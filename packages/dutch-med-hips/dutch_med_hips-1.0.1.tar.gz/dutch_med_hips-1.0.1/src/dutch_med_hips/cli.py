# src/dutch_med_hips/cli.py

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from . import __version__  # if you expose a version constant; else hardcode
from .core import HideInPlainSight


def _read_text(input_path: Optional[str]) -> str:
    if input_path and input_path != "-":
        return Path(input_path).read_text(encoding="utf-8")
    # "-" or None => stdin
    return sys.stdin.read()


def _write_text(output_path: Optional[str], text: str) -> None:
    if output_path and output_path != "-":
        Path(output_path).write_text(text, encoding="utf-8")
    else:
        # stdout
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")


def _write_mapping(mapping_path: str, mapping: list[dict]) -> None:
    Path(mapping_path).write_text(
        json.dumps(mapping, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dutch-med-hips",
        description="Anonymize Dutch medical reports by replacing PHI tags with realistic surrogates.",
    )

    parser.add_argument(
        "-i",
        "--input",
        metavar="PATH",
        help="Input file (UTF-8). Use '-' or omit for stdin.",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="PATH",
        help="Output file (UTF-8). Use '-' or omit for stdout.",
    )
    parser.add_argument(
        "--mapping-out",
        metavar="PATH",
        help="Write JSON mapping (original -> surrogate) to this file.",
    )

    # seeding / randomness
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Fixed seed for deterministic surrogates. "
        "If omitted, can fall back to document-hash seeding.",
    )
    parser.add_argument(
        "--no-document-hash-seed",
        action="store_true",
        help="Disable automatic document-hash-based seeding.",
    )

    # header & typos
    parser.add_argument(
        "--no-header",
        action="store_true",
        help="Disable the anonymization disclaimer header.",
    )
    parser.add_argument(
        "--disable-typos",
        action="store_true",
        help="Disable random typo injection in surrogates.",
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"dutch-med-hips {__version__}",
    )

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    text = _read_text(args.input)

    hips = HideInPlainSight(
        default_seed=args.seed,
        use_document_hash_seed=not args.no_document_hash_seed,
        enable_header=not args.no_header,
        enable_random_typos=not args.disable_typos,
    )

    result = hips.run(text=text)

    _write_text(args.output, result["text"])

    if args.mapping_out:
        _write_mapping(args.mapping_out, result["mapping"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
