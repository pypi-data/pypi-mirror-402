# tests/test_hips_core.py

import re

import pytest

from dutch_med_hips import HideInPlainSight, settings
from dutch_med_hips.locale import HOSPITAL_CITY_POOL, HOSPITAL_NAME_POOL


@pytest.fixture(autouse=True)
def reset_settings(monkeypatch):
    """
    Best-effort reset of a few settings that tests mutate.
    Adjust if you have a more formal settings reset.
    """
    # copy original dict so we can mutate safely
    original_id_templates = dict(settings.ID_TEMPLATES_BY_TAG)

    yield

    # restore
    settings.ID_TEMPLATES_BY_TAG.clear()
    settings.ID_TEMPLATES_BY_TAG.update(original_id_templates)


def test_basic_anonymization_replaces_tags():
    text = (
        "Patiënt <PERSOON> werd gezien in <HOSPITAL_NAME> op <DATUM>.\n"
        "Z-nummer: <Z-NUMMER>. BSN: <BSN>. IBAN: <IBAN>.\n"
        "Contact: <EMAIL> of via <URL>."
    )

    hips = HideInPlainSight(default_seed=123)
    result = hips.run(text=text)

    anon = result["text"]

    # Tags should be gone
    for tag in [
        "<PERSOON>",
        "<HOSPITAL_NAME>",
        "<DATUM>",
        "<Z-NUMMER>",
        "<BSN>",
        "<IBAN>",
        "<EMAIL>",
        "<URL>",
    ]:
        assert tag not in anon

    # There should be some mapping entries
    assert result["mapping"]
    assert any(m["original"] == "<PERSOON>" for m in result["mapping"])


def test_deterministic_with_same_seed():
    text = "Patiënt <PERSOON> met Z-nummer <Z-NUMMER>."

    hips1 = HideInPlainSight(default_seed=42)
    hips2 = HideInPlainSight(default_seed=42)

    res1 = hips1.run(text=text)
    res2 = hips2.run(text=text)

    assert res1["text"] == res2["text"]
    assert res1["mapping"] == res2["mapping"]


def test_different_seed_gives_different_output():
    text = "Patiënt <PERSOON> met Z-nummer <Z-NUMMER>."

    hips1 = HideInPlainSight(default_seed=1)
    hips2 = HideInPlainSight(default_seed=2)

    res1 = hips1.run(text=text)
    res2 = hips2.run(text=text)

    # Not guaranteed, but extremely likely different
    assert res1["text"] != res2["text"]


def test_z_number_template_overridden():
    """
    Check that ID_TEMPLATES_BY_TAG is honored for Z-numbers.
    """
    settings.ID_TEMPLATES_BY_TAG["<Z-NUMMER>"] = "Z-###-###"

    text = "Z-nummer: <Z-NUMMER>."
    hips = HideInPlainSight(default_seed=7)
    res = hips.run(text=text)

    # Extract the surrogate from mapping
    m = next(m for m in res["mapping"] if m["original"] == "<Z-NUMMER>")
    z = m["surrogate"]

    assert re.fullmatch(r"Z-\d{3}-\d{3}", z)


def test_bsn_is_nine_digits():
    text = "BSN: <BSN>."
    hips = HideInPlainSight(default_seed=7)
    res = hips.run(text=text)

    m = next(m for m in res["mapping"] if m["original"] == "<BSN>")
    bsn = m["surrogate"]
    assert len(bsn) == 9
    assert bsn.isdigit()


def test_iban_has_nl_prefix():
    text = "IBAN: <IBAN>."
    hips = HideInPlainSight(default_seed=7)
    res = hips.run(text=text)

    m = next(m for m in res["mapping"] if m["original"] == "<IBAN>")
    iban = m["surrogate"].replace(" ", "")
    assert iban.startswith("NL")
    # length for NL IBAN is usually 18 characters
    assert 16 <= len(iban) <= 20  # be a bit lenient


def test_email_and_url_look_reasonable():
    text = "Email: <EMAIL>, website: <URL>."
    hips = HideInPlainSight(default_seed=123)
    res = hips.run(text=text)

    email = next(m["surrogate"] for m in res["mapping"] if m["original"] == "<EMAIL>")
    url = next(m["surrogate"] for m in res["mapping"] if m["original"] == "<URL>")

    assert "@" in email and "." in email.split("@")[-1]
    assert url.startswith("http://") or url.startswith("https://")


def test_hospital_name_comes_from_pool_or_city():
    text = "Patiënt werd opgenomen in <HOSPITAL_NAME>."
    hips = HideInPlainSight(default_seed=11)
    res = hips.run(text=text)

    hosp = next(
        m["surrogate"] for m in res["mapping"] if m["original"] == "<HOSPITAL_NAME>"
    )

    # Build a flat set of all known names & cities
    all_names = {v for variants in HOSPITAL_NAME_POOL for v in variants}
    all_cities = {v for variants in HOSPITAL_CITY_POOL for v in variants}

    assert hosp in all_names or hosp in all_cities


def test_header_is_added_and_mapping_offsets_are_adjusted():
    text = "Patiënt <PERSOON>."
    hips = HideInPlainSight(default_seed=1, enable_header=True)
    res = hips.run(text=text)

    anon_text = res["text"]
    mapping = res["mapping"]

    # Header should be at the top and contain "DISCLAIMER"
    assert anon_text.startswith("#")
    assert "DISCLAIMER" in anon_text.splitlines()[0] or "DISCLAIMER" in anon_text

    # The mapped surrogate should correspond to the substring at [start:end]
    m = next(m for m in mapping if m["original"] == "<PERSOON>")
    start, end = m["start"], m["end"]
    segment = anon_text[start:end]
    # The replaced span should start with the surrogate
    assert segment.startswith(m["surrogate"])
    # And only contain trailing punctuation/whitespace after it
    trailing = segment[len(m["surrogate"]) :]
    assert trailing.strip(" .,!?:;") == ""


def test_header_can_be_disabled():
    text = "Patiënt <PERSOON>."
    hips = HideInPlainSight(default_seed=1, enable_header=False)
    res = hips.run(text=text)

    anon_text = res["text"]

    # No big disclaimer block at the top
    assert not anon_text.startswith("##############################")
    # Text should start with something like "Patiënt"
    assert anon_text.lstrip().startswith("Patiënt")


def test_person_name_initials_are_compact():
    """
    For PERSON_NAME_ABBREV tags, we expect initials like 'JS', 'BvG'.
    """
    text = "Initialen: <PERSON_INITIALS>."
    hips = HideInPlainSight(default_seed=5)
    res = hips.run(text=text)

    m = next(m for m in res["mapping"] if m["original"] == "<PERSON_INITIALS>")
    initials = m["surrogate"]

    assert re.fullmatch(r"[A-Za-z]{2,4}", initials)


def test_document_sub_id_pattern():
    """
    For tags like <RAPPORT_ID.T_NUMMER>, ensure we get prefix + digits.
    This will work whether you use a dedicated generator or tag-based templates,
    as long as you follow the 'prefix + 6 digits' style.
    """
    text = (
        "T: <RAPPORT_ID.T_NUMMER>, "
        "R: <RAPPORT_ID.R_NUMMER>, "
        "C: <RAPPORT_ID.C_NUMMER>, "
        "DPA: <RAPPORT_ID.DPA_NUMMER>, "
        "RPA: <RAPPORT_ID.RPA_NUMMER>."
    )

    hips = HideInPlainSight(default_seed=99)
    res = hips.run(text=text)

    for tag, prefix in [
        ("<RAPPORT_ID.T_NUMMER>", "T"),
        ("<RAPPORT_ID.R_NUMMER>", "R"),
        ("<RAPPORT_ID.C_NUMMER>", "C"),
        ("<RAPPORT_ID.DPA_NUMMER>", "DPA"),
        ("<RAPPORT_ID.RPA_NUMMER>", "RPA"),
    ]:
        m = next(m for m in res["mapping"] if m["original"] == tag)
        surr = m["surrogate"]
        assert surr.startswith(prefix)
        # suffix should be (at least) digits
        pattern = re.escape(prefix) + r"[-\s]?\d{4,8}"
        assert re.fullmatch(pattern, surr)


class TestNerLabelUpdates:
    """Tests for NER label position tracking through surrogate substitution."""

    def test_ner_labels_updated_with_longer_surrogate(self):
        """When surrogate is longer than original tag, positions shift forward."""
        text = "Patient <PERSOON> geboren op <DATUM>."
        # <PERSOON> is at positions 8-17, <DATUM> is at positions 29-36
        ner_labels = [
            (8, 17, "<PERSOON>"),
            (29, 36, "<DATUM>"),
        ]

        hips = HideInPlainSight(default_seed=42, enable_header=False)
        result = hips.run(text, ner_labels=ner_labels)

        updated_labels = result["updated_labels"]
        anon_text = result["text"]

        assert updated_labels is not None
        assert len(updated_labels) == 2

        # Verify the updated positions point to the correct text
        for start, end, label in updated_labels:
            # The span should exist within the text bounds
            assert 0 <= start < end <= len(anon_text)
            # Extract what's at that position
            extracted = anon_text[start:end]
            # It should match the surrogate from the mapping
            mapping_entry = next(
                m for m in result["mapping"] if m["original"] == label
            )
            assert extracted == mapping_entry["surrogate"]

    def test_ner_labels_updated_with_shorter_surrogate(self):
        """When surrogate is shorter than original tag, positions shift backward."""
        # Use a tag that typically produces shorter output
        text = "Leeftijd: <LEEFTIJD> jaar."
        # <LEEFTIJD> at positions 10-20
        ner_labels = [(10, 20, "<LEEFTIJD>")]

        hips = HideInPlainSight(default_seed=42, enable_header=False)
        result = hips.run(text, ner_labels=ner_labels)

        updated_labels = result["updated_labels"]
        anon_text = result["text"]

        assert updated_labels is not None
        assert len(updated_labels) == 1

        start, end, label = updated_labels[0]
        extracted = anon_text[start:end]
        mapping_entry = next(m for m in result["mapping"] if m["original"] == label)
        assert extracted == mapping_entry["surrogate"]

    def test_ner_labels_with_multiple_replacements(self):
        """Multiple replacements accumulate offset shifts correctly."""
        text = "<PERSOON> en <PERSOON> op <DATUM>."
        # First <PERSOON> at 0-9, second at 13-22, <DATUM> at 26-33
        ner_labels = [
            (0, 9, "<PERSOON>"),
            (13, 22, "<PERSOON>"),
            (26, 33, "<DATUM>"),
        ]

        hips = HideInPlainSight(default_seed=123, enable_header=False)
        result = hips.run(text, ner_labels=ner_labels)

        updated_labels = result["updated_labels"]
        anon_text = result["text"]

        assert updated_labels is not None
        assert len(updated_labels) == 3

        # Each label should point to the correct surrogate in the final text
        for i, (start, end, label) in enumerate(updated_labels):
            assert 0 <= start < end <= len(anon_text)
            extracted = anon_text[start:end]
            # Find corresponding mapping entry (by index since same tag appears multiple times)
            mapping_entry = result["mapping"][i]
            assert extracted == mapping_entry["surrogate"]

    def test_ner_labels_none_returns_none(self):
        """When ner_labels is not provided, updated_labels is None."""
        text = "Patient <PERSOON>."
        hips = HideInPlainSight(default_seed=42, enable_header=False)
        result = hips.run(text)

        assert result["updated_labels"] is None

    def test_ner_labels_empty_list_returns_empty_list(self):
        """When ner_labels is empty list, updated_labels is empty list."""
        text = "Patient <PERSOON>."
        hips = HideInPlainSight(default_seed=42, enable_header=False)
        result = hips.run(text, ner_labels=[])

        assert result["updated_labels"] == []

    def test_ner_labels_with_header_includes_header_offset(self):
        """When header is enabled, label positions include header offset."""
        text = "Patient <PERSOON>."
        ner_labels = [(8, 17, "<PERSOON>")]

        hips = HideInPlainSight(default_seed=42, enable_header=True)
        result = hips.run(text, ner_labels=ner_labels)

        updated_labels = result["updated_labels"]
        anon_text = result["text"]

        assert updated_labels is not None
        start, end, label = updated_labels[0]

        # Position should account for header
        assert start > 8  # Original position was 8, now shifted by header
        extracted = anon_text[start:end]
        mapping_entry = next(m for m in result["mapping"] if m["original"] == label)
        assert extracted == mapping_entry["surrogate"]

    def test_ner_labels_for_non_replaced_spans(self):
        """Labels pointing to non-PHI text should shift correctly."""
        text = "Hello <PERSOON> world."
        # "Hello" at 0-5, "world" at 16-21 (after the tag)
        ner_labels = [
            (0, 5, "GREETING"),
            (16, 21, "NOUN"),
        ]

        hips = HideInPlainSight(default_seed=42, enable_header=False)
        result = hips.run(text, ner_labels=ner_labels)

        updated_labels = result["updated_labels"]
        anon_text = result["text"]

        # First label (before replacement) should be unchanged
        start1, end1, label1 = updated_labels[0]
        assert anon_text[start1:end1] == "Hello"

        # Second label (after replacement) should be shifted
        start2, end2, label2 = updated_labels[1]
        assert anon_text[start2:end2] == "world"
