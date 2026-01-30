# tests/test_full_pipeline.py

import json
from pathlib import Path

from dutch_med_hips import HideInPlainSight, schema


def test_full_pipeline_smoke():
    """
    Full-pipeline smoke test on a curated sample file that contains
    many occurrences of all supported PHI tags.

    - Runs HideInPlainSight end-to-end
    - Asserts that no known tags remain in the anonymized text
    - Writes anonymized text + mapping to test_artifacts/ for humans.
    """
    # 1. Load the sample input
    data_dir = Path(__file__).parent / "data"
    sample_path = data_dir / "hips_debug_input.txt"
    assert sample_path.exists(), f"Missing sample file: {sample_path}"

    original_text = sample_path.read_text(encoding="utf-8")

    # 2. Run the full pipeline
    hips = HideInPlainSight(default_seed=123, enable_header=True)
    result = hips.run(text=original_text)

    anon_text = result["text"]
    mapping = result["mapping"]

    # 3. Basic invariants
    all_tags = {
        tag
        for tags in schema.DEFAULT_PATTERNS.values()
        for tag in tags
        if tag.startswith("<") and tag.endswith(">")
    }

    for tag in all_tags:
        assert tag not in anon_text, f"Tag {tag!r} still present in output"

    assert mapping
    phi_types = {m["phi_type"] for m in mapping if "phi_type" in m}
    assert len(phi_types) > 3

    # 4. Write artifacts into repo (for local + CI)
    project_root = Path(__file__).resolve().parents[1]
    out_dir = project_root / "test_artifacts"
    out_dir.mkdir(exist_ok=True)

    out_text_path = out_dir / "full_pipeline_output.txt"
    out_map_path = out_dir / "full_pipeline_mapping.json"

    out_text_path.write_text(anon_text, encoding="utf-8")
    out_map_path.write_text(
        json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"\n[full-pipeline] Anonymized text written to: {out_text_path}")
    print(f"[full-pipeline] Mapping written to:       {out_map_path}")
