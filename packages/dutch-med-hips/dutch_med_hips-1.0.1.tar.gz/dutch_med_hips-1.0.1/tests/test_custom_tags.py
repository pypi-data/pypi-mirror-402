import copy
import re

from dutch_med_hips import HideInPlainSight, schema, settings, surrogates
from dutch_med_hips.schema import PHIType


def test_extend_existing_phi_type_with_additional_pattern():
    """
    Extend an existing PHI type (e.g. GENERIC_ID) with an extra regex pattern
    and ensure it is detected and replaced using the standard ID template mechanism.
    """
    original_patterns = copy.deepcopy(schema.DEFAULT_PATTERNS)
    original_templates = dict(settings.ID_TEMPLATES_BY_TAG)

    try:
        # We assume PHIType.GENERIC_ID already exists and has some patterns.
        # Here we add a new variant of a Z-number tag.
        extra_tag_regex = r"<Z_NUMMER_EXTRA>"
        schema.DEFAULT_PATTERNS.setdefault(PHIType.GENERIC_ID, []).append(
            extra_tag_regex
        )

        # Bind a template specifically for this literal tag text
        settings.ID_TEMPLATES_BY_TAG["<Z_NUMMER_EXTRA>"] = "Z-###-###"

        text = "Extra Z-nummer: <Z_NUMMER_EXTRA>."
        hips = HideInPlainSight(default_seed=123)
        res = hips.run(text=text)

        anon = res["text"]
        mapping = res["mapping"]

        # Tag should be gone from output
        assert "<Z_NUMMER_EXTRA>" not in anon

        # Mapping should contain our new tag
        m = next(m for m in mapping if m["original"] == "<Z_NUMMER_EXTRA>")
        surr = m["surrogate"]

        # Surrogate should follow our Z-###-### format
        assert re.fullmatch(r"Z-\d{3}-\d{3}", surr)

    finally:
        # Restore original config to avoid leaking state into other tests
        schema.DEFAULT_PATTERNS.clear()
        schema.DEFAULT_PATTERNS.update(original_patterns)

        settings.ID_TEMPLATES_BY_TAG.clear()
        settings.ID_TEMPLATES_BY_TAG.update(original_templates)


def test_custom_id_tag_with_template():
    """
    Define a custom ID tag <CENTER_ID> and map it to CEN-######,
    then verify it is detected and replaced correctly.
    """
    # --- arrange: backup and extend config ---
    original_patterns = copy.deepcopy(schema.DEFAULT_PATTERNS)
    original_templates = dict(settings.ID_TEMPLATES_BY_TAG)

    try:
        # 1) add custom tag regex to a known PHI type
        schema.DEFAULT_PATTERNS.setdefault(PHIType.GENERIC_ID, []).append(
            r"<CENTER_ID>"
        )

        # 2) bind a surrogate template
        settings.ID_TEMPLATES_BY_TAG["<CENTER_ID>"] = "CEN-######"

        text = "Center: <CENTER_ID>."

        hips = HideInPlainSight(default_seed=1)
        res = hips.run(text=text)

        anon = res["text"]
        mapping = res["mapping"]

        # tag should be gone from text
        assert "<CENTER_ID>" not in anon

        # mapping should contain our tag
        m = next(m for m in mapping if m["original"] == "<CENTER_ID>")
        surr = m["surrogate"]

        # surrogate should match our template
        assert re.fullmatch(r"CEN-\d{6}", surr)

    finally:
        # restore config
        schema.DEFAULT_PATTERNS.clear()
        schema.DEFAULT_PATTERNS.update(original_patterns)

        settings.ID_TEMPLATES_BY_TAG.clear()
        settings.ID_TEMPLATES_BY_TAG.update(original_templates)


def test_custom_phi_type_with_generator():
    """
    Define a completely custom PHI type and generator for <CENTER_SPECIAL>.
    """
    # --- arrange: backup and extend config ---
    original_patterns = copy.deepcopy(schema.DEFAULT_PATTERNS)
    original_generators = dict(surrogates.DEFAULT_GENERATORS)

    CUSTOM_TYPE = "center"

    def generate_center(match: re.Match) -> str:
        return "CENTER-123456"

    try:
        # 1) register new PHI type & pattern
        schema.DEFAULT_PATTERNS[CUSTOM_TYPE] = [r"<CENTER_SPECIAL>"]

        # 2) register custom generator
        surrogates.DEFAULT_GENERATORS[CUSTOM_TYPE] = generate_center

        text = "Speciaal: <CENTER_SPECIAL>."
        hips = HideInPlainSight(default_seed=1)
        res = hips.run(text=text)

        anon = res["text"]
        mapping = res["mapping"]

        # tag should be gone
        assert "<CENTER_SPECIAL>" not in anon

        # mapping should contain our custom type and surrogate
        m = next(m for m in mapping if m["original"] == "<CENTER_SPECIAL>")
        assert m["phi_type"] == CUSTOM_TYPE
        assert m["surrogate"] == "CENTER-123456"

    finally:
        # restore config
        schema.DEFAULT_PATTERNS.clear()
        schema.DEFAULT_PATTERNS.update(original_patterns)

        surrogates.DEFAULT_GENERATORS.clear()
        surrogates.DEFAULT_GENERATORS.update(original_generators)
