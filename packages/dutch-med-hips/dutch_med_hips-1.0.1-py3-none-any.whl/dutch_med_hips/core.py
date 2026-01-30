"""
Core functionality for hiding PHI in plain sight.

Key public pieces:
- PatternConfig: dataclass for regex-based PHI patterns.
- build_pattern_configs: helper that merges defaults and user overrides,
  with a duplicate-pattern check.
- HideInPlainSight: main anonymizer class.
"""

import hashlib
import random
import re
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import Callable, Dict, List, Optional, Tuple

import typo

from .schema import DEFAULT_PATTERNS, PHIType
from .settings import (
    DEFAULT_ENABLE_HEADER,
    DEFAULT_ENABLE_RANDOM_TYPOS,
    DEFAULT_HEADER_TEMPLATE,
    PERSON_NAME_REUSE_PROB,
    TYPO_IN_SURROGATE_PROB,
)
from .surrogates import DEFAULT_GENERATORS, seed_surrogates


@dataclass
class PatternConfig:
    """
    Configuration for a PHI detection pattern.

    Attributes
    ----------
    phi_type:
        Logical PHI category (e.g. PHIType.PERSON_NAME).
    pattern:
        Regex string that matches the thing to be replaced, for example
        r"<PERSOON>" or r"<RAPPORT[_-]ID\.(T|R|C|DPA|RPA)[_-]NUMMER>".
    generator:
        Function that, given the regex match, returns a surrogate string.
        Signature: Callable[[re.Match], str]
    max_per_document:
        Optional cap on the number of replacements for this PHI type per
        document. If None, no limit.
    """

    phi_type: str
    pattern: str
    generator: Callable[[re.Match], str]
    max_per_document: Optional[int] = None


def _get_package_version() -> str:
    """Return installed version of dutch-med-hips, or 'unknown'."""
    try:
        return version("dutch-med-hips")
    except PackageNotFoundError:
        return "unknown"


def _seed_from_text(text: str) -> int:
    """
    Derive a deterministic integer seed from the document text.

    Uses SHA-256 and folds it into a 32-bit integer.
    """
    h = hashlib.sha256(text.encode("utf-8")).digest()
    return int.from_bytes(h[:4], byteorder="big", signed=False)


def _introduce_single_typo(text: str) -> str:
    """
    Introduce a single typo into `text` using the `typo` package.

    We randomly choose one of:
    - missing_char      (drop a character)
    - char_swap         (swap adjacent characters)
    - extra_char        (insert a keyboard-neighbor character)

    We also preserve first/last characters to avoid completely
    mangling short surrogates.
    """
    if not text or text.isspace():
        return text

    # pick an operation
    op = random.choice(["missing_char", "char_swap", "extra_char"])

    # tie typo's RNG to our own RNG by passing a seed derived from `random`
    err = typo.StrErrer(text, seed=random.randint(0, 2**32 - 1))

    if op == "missing_char":
        return err.missing_char(preservefirst=True, preservelast=True).result
    elif op == "char_swap":
        return err.char_swap(preservefirst=True, preservelast=True).result
    else:
        # extra_char uses keyboard-neighbor by design
        return err.extra_char(preservefirst=True, preservelast=True).result


def _maybe_add_typo(text: str, enabled: bool, probability: float) -> tuple[str, bool]:
    """
    With given probability, introduce a single typo into `text`.

    Returns (possibly_modified_text, typo_was_applied).
    """
    if not enabled or probability <= 0.0:
        return text, False

    if random.random() >= probability:
        return text, False

    return _introduce_single_typo(text), True


def build_pattern_configs(
    custom_patterns_per_type: Optional[Dict[str, List[str]]] = None,
    max_per_document: Optional[Dict[str, int]] = None,
) -> List[PatternConfig]:
    """
    Build PatternConfig objects starting from DEFAULT_PATTERNS,
    optionally overridden by the user.

    Parameters
    ----------
    custom_patterns_per_type:
        Optional dict mapping phi_type -> list of regex patterns.
        If provided for a phi_type, this *replaces* the default patterns
        for that phi_type.

        Example:
            {
                PHIType.PERSON_NAME: [r"<NAAM>", r"<NAME>"],
                PHIType.DATE: [r"<D>", r"<DATE>"],
            }

    max_per_document:
        Optional dict mapping phi_type -> max replacements per document.

    Returns
    -------
    List[PatternConfig]

    Raises
    ------
    ValueError
        If the same *pattern string* is assigned to more than one PHI type.
    KeyError
        If a PHI type has no default generator in DEFAULT_GENERATORS.
    """
    # 1) Merge defaults + custom overrides.
    final_patterns_per_type: Dict[str, List[str]] = {}

    for phi_type, default_patterns in DEFAULT_PATTERNS.items():
        if custom_patterns_per_type and phi_type in custom_patterns_per_type:
            # Use user-specified patterns, de-duplicated but order-preserving.
            patterns = list(dict.fromkeys(custom_patterns_per_type[phi_type]))
        else:
            patterns = list(dict.fromkeys(default_patterns))

        final_patterns_per_type[phi_type] = patterns

    # 2) Check for duplicate pattern strings across PHI types.
    seen: Dict[str, str] = {}
    conflicts: List[str] = []

    for phi_type, patterns in final_patterns_per_type.items():
        for pattern in patterns:
            if pattern in seen and seen[pattern] != phi_type:
                conflicts.append(
                    f"Pattern {pattern!r} used for both "
                    f"{seen[pattern]!r} and {phi_type!r}"
                )
            else:
                seen[pattern] = phi_type

    if conflicts:
        raise ValueError(
            "Duplicate regex pattern strings across PHI categories are not allowed:\n"
            + "\n".join(conflicts)
        )

    # 3) Build PatternConfig list.
    configs: List[PatternConfig] = []
    for phi_type, patterns in final_patterns_per_type.items():
        if phi_type not in DEFAULT_GENERATORS:
            raise KeyError(
                f"No default surrogate generator registered for PHI type {phi_type!r}"
            )

        generator = DEFAULT_GENERATORS[phi_type]
        max_doc = max_per_document.get(phi_type) if max_per_document else None

        for pattern in patterns:
            configs.append(
                PatternConfig(
                    phi_type=phi_type,
                    pattern=pattern,
                    generator=generator,
                    max_per_document=max_doc,
                )
            )

    return configs


class HideInPlainSight:
    """
    Main engine that replaces regex-based PHI patterns with surrogates.

    Seeding behaviour:
    - If `seed` is passed to anonymize(), that is used.
    - Else if `default_seed` (constructor) is set, that is used.
    - Else if `use_document_hash_seed` is True, a seed is derived
      from the document text.
    - Else: no seeding is performed (fully random).

    Noise behaviour:
    - If `enable_random_typos` is True, each surrogate has a small
      chance (TYPO_IN_SURROGATE_PROB) of receiving a single typo.

    Header behaviour:
    - If `enable_header` is True, `header_text` is prepended to the
      anonymized text. By default, this is a disclaimer about
      dutch-med-hips anonymization.
    """

    def __init__(
        self,
        pattern_configs: Optional[List[PatternConfig]] = None,
        *,
        default_seed: Optional[int] = None,
        use_document_hash_seed: bool = True,
        enable_random_typos: bool = DEFAULT_ENABLE_RANDOM_TYPOS,
        enable_header: bool = DEFAULT_ENABLE_HEADER,
        header_text: Optional[str] = None,
        custom_patterns_per_type: Optional[Dict[str, List[str]]] = None,
        max_per_document: Optional[Dict[str, int]] = None,
    ):
        # Build default pattern configs if none supplied
        if pattern_configs is None:
            pattern_configs = build_pattern_configs(
                custom_patterns_per_type=custom_patterns_per_type,
                max_per_document=max_per_document,
            )

        self._pattern_configs = pattern_configs
        self._default_seed = default_seed
        self._use_document_hash_seed = use_document_hash_seed
        self._enable_random_typos = enable_random_typos

        # header settings
        self._enable_header = enable_header
        if header_text is not None:
            self._header_text = header_text
        else:
            pkg_version = _get_package_version()
            self._header_text = DEFAULT_HEADER_TEMPLATE.format(version=pkg_version)

        # Defensive: ensure no identical pattern string is used for different PHI types.
        pattern_owner: Dict[str, str] = {}
        for cfg in pattern_configs:
            owner = pattern_owner.get(cfg.pattern)
            if owner is not None and owner != cfg.phi_type:
                raise ValueError(
                    f"Pattern {cfg.pattern!r} defined for multiple PHI types: "
                    f"{owner!r} and {cfg.phi_type!r}"
                )
            pattern_owner[cfg.pattern] = cfg.phi_type

        # Build combined regex with named groups
        group_parts: List[str] = []
        self._group_to_config: Dict[str, PatternConfig] = {}

        for idx, cfg in enumerate(pattern_configs):
            group_name = f"p{idx}"
            group_parts.append(f"(?P<{group_name}>{cfg.pattern})")
            self._group_to_config[group_name] = cfg

        if group_parts:
            combined_src = "|".join(group_parts)
            self._combined_pattern = re.compile(combined_src)
        else:
            self._combined_pattern = None

    def run(
        self,
        text: str,
        keep_mapping: bool = True,
        seed: Optional[int] = None,
        ner_labels: Optional[List[Tuple[int, int, str]]] = None,
    ) -> Dict[str, object]:
        """
        Replace all configured patterns in `text` with generated surrogates.

        Seeding priority:
        1. `seed` argument (per-call)
        2. `self._default_seed` (constructor)
        3. hash of `text` if `self._use_document_hash_seed` is True
        4. no seeding (random)

        Parameters
        ----------
        text:
            The input text containing PHI tags to be replaced.
        keep_mapping:
            If True, return a mapping of original -> surrogate replacements.
        seed:
            Optional seed for deterministic surrogate generation.
        ner_labels:
            Optional list of NER labels as (start, end, label) tuples.
            If provided, the returned dict will include 'updated_labels'
            with positions adjusted to account for length changes from
            surrogate substitutions.

        Returns
        -------
        dict with keys:
            - "text": the anonymized text
            - "mapping": list of replacement details (if keep_mapping=True)
            - "updated_labels": list of (start, end, label) with adjusted
              positions (if ner_labels was provided)
        """
        if self._combined_pattern is None:
            return {
                "text": text,
                "mapping": [] if keep_mapping else None,
                "updated_labels": list(ner_labels) if ner_labels else None,
            }

        # --- decide effective seed ---
        if seed is not None:
            effective_seed = seed
        elif self._default_seed is not None:
            effective_seed = self._default_seed
        elif self._use_document_hash_seed:
            effective_seed = _seed_from_text(text)
        else:
            effective_seed = None

        # --- apply seeding ---
        if effective_seed is not None:
            random.seed(effective_seed)
            seed_surrogates(effective_seed)

        per_type_counts: Dict[str, int] = {}
        per_type_surrogates: Dict[str, List[str]] = {}  # for reuse within the document
        mapping: List[Dict[str, object]] = []

        # Collect all matches first so we can track position shifts
        matches = list(self._combined_pattern.finditer(text))

        # Process matches and collect replacement info
        replacements: List[Tuple[int, int, str, str]] = []  # (start, end, original, surrogate)

        for match in matches:
            group_name = match.lastgroup
            cfg = self._group_to_config[group_name]
            phi_type = cfg.phi_type

            count = per_type_counts.get(phi_type, 0)
            if cfg.max_per_document is not None and count >= cfg.max_per_document:
                # Limit reached: leave original text unchanged.
                continue

            # Per-document surrogate cache (for reuse)
            cache = per_type_surrogates.setdefault(phi_type, [])
            reused = False

            if (
                phi_type == PHIType.PERSON_NAME
                and cache
                and random.random() < PERSON_NAME_REUSE_PROB
            ):
                surrogate = random.choice(cache)
                reused = True
            else:
                surrogate = cfg.generator(match)
                cache.append(surrogate)
                reused = False

            per_type_counts[phi_type] = count + 1

            # Maybe introduce a typo
            surrogate, typo_applied = _maybe_add_typo(
                surrogate,
                enabled=self._enable_random_typos,
                probability=TYPO_IN_SURROGATE_PROB,
            )

            replacements.append((match.start(), match.end(), match.group(0), surrogate))

            if keep_mapping:
                mapping.append(
                    {
                        "phi_type": phi_type,
                        "pattern": cfg.pattern,
                        "original": match.group(0),
                        "surrogate": surrogate,
                        "start": match.start(),
                        "end": match.end(),
                        "typo_applied": typo_applied,
                        "reused_surrogate": reused,
                    }
                )

        # Build the anonymized text by applying replacements in reverse order
        # (to preserve positions for earlier replacements)
        anonymized_text = text
        for start, end, original, surrogate in reversed(replacements):
            anonymized_text = anonymized_text[:start] + surrogate + anonymized_text[end:]

        # Update NER labels if provided
        updated_labels: Optional[List[Tuple[int, int, str]]] = None
        if ner_labels is not None:
            updated_labels = []
            for label_start, label_end, label_text in ner_labels:
                new_start = label_start
                new_end = label_end

                # Apply offset shifts from all replacements that affect this label
                for repl_start, repl_end, original, surrogate in replacements:
                    delta = len(surrogate) - len(original)

                    if repl_end <= label_start:
                        # Replacement is entirely before this label: shift both
                        new_start += delta
                        new_end += delta
                    elif repl_start < label_end:
                        # Replacement overlaps or is inside the label: adjust end
                        new_end += delta

                updated_labels.append((new_start, new_end, label_text))

        # Update mapping positions to reflect final positions in anonymized text
        if keep_mapping:
            for entry in mapping:
                orig_start = entry["start"]
                orig_end = entry["end"]
                new_start = orig_start
                new_end = orig_end

                # Apply offset shifts from earlier replacements
                for repl_start, repl_end, original, surrogate in replacements:
                    if repl_start >= orig_start:
                        # This replacement is at or after our position, skip
                        break
                    delta = len(surrogate) - len(original)
                    new_start += delta
                    new_end += delta

                # The end position should reflect the surrogate length
                new_end = new_start + len(entry["surrogate"])

                entry["start"] = new_start
                entry["end"] = new_end

        # Optionally prepend header disclaimer
        if self._enable_header and self._header_text:
            header = self._header_text
            offset = len(header)

            # Adjust mapping positions so they still refer to the final string
            if keep_mapping:
                for entry in mapping:
                    entry["start"] += offset
                    entry["end"] += offset

            # Adjust updated_labels positions
            if updated_labels is not None:
                updated_labels = [
                    (start + offset, end + offset, label)
                    for start, end, label in updated_labels
                ]

            anonymized_text = header + anonymized_text

        return {
            "text": anonymized_text,
            "mapping": mapping if keep_mapping else None,
            "updated_labels": updated_labels,
        }
