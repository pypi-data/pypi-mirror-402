"""
Default surrogate generators for PHI types, using Faker.

All generators take a `re.Match` object and return a surrogate string.
"""

import math
import random
import re
import string
from datetime import date, datetime, timedelta
from typing import Callable, Dict, List, Tuple

from faker import Faker

from .locale import (
    DUTCH_AREA_CODES,
    DUTCH_HOUR_WORDS,
    DUTCH_MONTHS_ABBR,
    DUTCH_MONTHS_FULL,
    HOSPITAL_CITY_POOL,
    HOSPITAL_NAME_POOL,
)
from .schema import PHIType
from .settings import (
    AGE_GMM_MEANS,
    AGE_GMM_VARS,
    AGE_GMM_WEIGHTS,
    AGE_MAX,
    AGE_MIN,
    DATE_EARLIEST,
    DATE_LATEST,
    DATE_MONTH_AS_NAME_PROB,
    DATE_MONTH_NAME_ABBR_PROB,
    DATE_NUMERIC_PADDED_PROB,
    DATE_WITH_YEAR_PROB,
    DATE_YEAR_FULL_PROB,
    HOSPITAL_NAME_CITY_ONLY_PROB,
    ID_TEMPLATE_DEFAULT,
    ID_TEMPLATES_BY_TAG,
    PERSON_NAME_FIRST_ONLY_PROB,
    PERSON_NAME_INITIALS_PROB,
    PERSON_NAME_LAST_ONLY_PROB,
    PERSON_NAME_LOWERCASE_PROB,
    PERSON_NAME_MAX_INITIALS,
    PERSON_NAME_REVERSE_ORDER_PROB,
    PERSON_NAME_UPPERCASE_PROB,
    PHONE_TYPE_LANDLINE_PROB,
    PHONE_TYPE_MOBILE_PROB,
    PHONE_TYPE_SEIN_PROB,
    STUDY_NAME_POOL,
    TIME_ADD_HOUR,
    TIME_FMT_HH_DOT_MM_PROB,
    TIME_FMT_HH_MM_PROB,
    TIME_FMT_HH_U_MM_PROB,
    TIME_FMT_NATURAL_DUTCH_PROB,
)

# Single Faker instance for the whole module (Dutch locale)
_fake = Faker("nl_NL")

# -- Seeder ------------------------------------------------------


def seed_surrogates(seed: int) -> None:
    """
    Seed the Faker instance used by the surrogate generators.
    """
    _fake.seed_instance(seed)


# --- Helper functions ---------------------------------------


def _choose_weighted_index(weights: List[float]) -> int:
    """
    Return an index 0..len(weights)-1 chosen according to the given weights.
    """
    total = sum(weights)
    if total <= 0:
        # fallback: uniform
        return random.randrange(len(weights))

    r = random.random() * total
    acc = 0.0
    for i, w in enumerate(weights):
        acc += w
        if r <= acc:
            return i
    return len(weights) - 1


def _chance(p: float) -> bool:
    return random.random() < p


# --- People ------------------------------------------------------


def _first_name_to_initials(first_name: str, extra_count: int) -> str:
    """
    Convert a first name into a compact initials string.

    - First initial always based on the given first_name.
    - extra_count additional initials are based on extra random first names.
    - Example outputs: "J.", "J.S.", "J.S.T."
    """
    initials = []

    first_name = first_name.strip()
    if first_name:
        initials.append(first_name[0].upper() + ".")

    for _ in range(extra_count):
        extra = _fake.first_name().strip()
        if extra:
            initials.append(extra[0].upper() + ".")

    # Join without spaces so you get "J.S.T." as a single token
    return "".join(initials)


TUSSENVOEGSELS = {"van", "de", "der", "den", "van de", "van der", "van den"}


def _full_name_to_compact_initials(full_name: str) -> str:
    """
    Convert a full Dutch name into compact initials without dots, e.g.:

    - "Jan Steen" -> "JS"
    - "Bram van Ginneken" -> "BvG"
    - "Anna de Jong" -> "AdJ"

    Logic:
    - Split on whitespace.
    - Take the first character of each token that starts with a letter.
    - For typical Dutch tussenvoegsels (van, de, der, den) we use lowercase,
      all other parts uppercase.
    """
    tokens = full_name.strip().split()
    initials = []

    for idx, token in enumerate(tokens):
        if not token:
            continue
        # Normalize the word for tussenvoegsel detection
        base = token.lower().strip(",.")
        if not base:
            continue

        first_char = base[0]
        if not first_char.isalpha():
            continue

        # Tussenvoegsels (van, de, der, den) as lowercase, everything else uppercase
        if base in {"van", "de", "der", "den"} and idx > 0:
            initials.append(first_char.lower())
        else:
            initials.append(first_char.upper())

    return "".join(initials)


def generate_fake_person_name(match: re.Match) -> str:
    """
    Generate a fake person name with:
    - First / last / full name variants
    - Initials only allowed when a last name is present (never lone initial)
    - Multi-initials (J., J.S., J.S.T.) using up to PERSON_NAME_MAX_INITIALS
    - Random capitalization
    - Optional 'Lastname, First' format
    """
    first = _fake.first_name()
    last = _fake.last_name()

    # Decide basic structure: first-only, last-only, or full
    r = random.random()
    if r < PERSON_NAME_FIRST_ONLY_PROB:
        structure = "first_only"
    elif r < PERSON_NAME_FIRST_ONLY_PROB + PERSON_NAME_LAST_ONLY_PROB:
        structure = "last_only"
    else:
        structure = "full"

    # Decide whether to use initials.
    # RULE 1: never a lone initial -> only allow initials when a last name is present.
    use_initials = structure == "full" and random.random() < PERSON_NAME_INITIALS_PROB

    if use_initials:
        # Decide how many initials (1..PERSON_NAME_MAX_INITIALS)
        max_n = max(1, PERSON_NAME_MAX_INITIALS)
        extra_count = random.randint(0, max_n - 1)  # 0 extra -> 1 initial total
        first_part = _first_name_to_initials(first, extra_count)
    else:
        first_part = first

    # Build the parts according to the structure
    if structure == "first_only":
        parts = [first_part]
    elif structure == "last_only":
        parts = [last]
    else:  # "full"
        parts = [first_part, last]

    # Maybe reverse order as "Lastname, First"
    if len(parts) == 2 and random.random() < PERSON_NAME_REVERSE_ORDER_PROB:
        parts = [parts[1] + ",", parts[0]]

    name = " ".join(parts)

    # Apply capitalization style
    c = random.random()
    if c < PERSON_NAME_LOWERCASE_PROB:
        name = name.lower()
    elif c < PERSON_NAME_LOWERCASE_PROB + PERSON_NAME_UPPERCASE_PROB:
        name = name.upper()
    else:
        # Keep as-is (Faker returns Title Case by default,
        # initials are already uppercase)
        pass

    return name


def generate_fake_person_initials(match: re.Match) -> str:
    """
    Generate fake initials based on a full Faker name, e.g.:

    - "Jan Steen" -> "JS"
    - "Bram van Ginneken" -> "BvG"
    """
    full_name = f"{_fake.first_name()} {_fake.last_name()}"
    return _full_name_to_compact_initials(full_name)


# --- Dates / times / age -----------------------------------------


def parse_date_string(s: str) -> date | str:
    """
    Parse user input into something usable by faker.date_between:
    - absolute dates -> datetime.date
    - 'today'/'now'/'yesterday'/'tomorrow' -> concrete dates
    - faker-style relative offsets ('-30d', '+2y', etc.) -> passed through as string
    - empty/None -> None
    """

    POSSIBLE_FORMATS = [
        "%d-%m-%Y",  # 1-1-2024 / 01-01-2024
        "%Y-%m-%d",  # 2024-01-01
        "%d/%m/%Y",  # 1/1/2024
    ]

    RELATIVE_PATTERN = re.compile(r"[+-]\d+[dmy]$", re.IGNORECASE)

    if s is None:
        return None

    s = s.strip()
    if not s:
        return None

    lower = s.lower()

    # Special keywords -> concrete dates
    if lower in {"today", "now"}:
        return date.today()
    if lower == "yesterday":
        return date.today() - timedelta(days=1)
    if lower == "tomorrow":
        return date.today() + timedelta(days=1)

    # Faker-style relative strings: '-30d', '+2y', '+10m', etc.
    if RELATIVE_PATTERN.fullmatch(lower):
        # let Faker handle these natively
        return lower

    # Try absolute date formats
    for fmt in POSSIBLE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue

    raise ValueError(f"Invalid date format: {s!r}")


def generate_fake_date(match: re.Match) -> str:
    """
    Generate a fake date using a 3-step scheme:

    1) pick with or without year
    2) pick month representation: name vs numeric
    3) pick exact format:
       - numeric: D-M or DD-MM (± year), never mixed padding
       - name: full vs abbreviated month (± year)
    """
    # Use a date between DATE_EARLIEST and DATE_LATEST
    start_date = parse_date_string(DATE_EARLIEST)
    end_date = parse_date_string(DATE_LATEST)
    d = _fake.date_between(start_date=start_date, end_date=end_date)
    year = d.year
    month = d.month
    day = d.day

    # Step 1: with or without year
    with_year = _chance(DATE_WITH_YEAR_PROB)
    if with_year:
        # Decide year format
        use_full_year = _chance(DATE_YEAR_FULL_PROB)
        if use_full_year:
            year_str = f"{year:04d}"
        else:
            year_str = f"{year % 100:02d}"

    # Step 2: month as name or number
    month_as_name = _chance(DATE_MONTH_AS_NAME_PROB)

    if month_as_name:
        # Named month
        use_abbr = _chance(DATE_MONTH_NAME_ABBR_PROB)
        month_str = (
            DUTCH_MONTHS_ABBR[month - 1] if use_abbr else DUTCH_MONTHS_FULL[month - 1]
        )
        # Always non-padded day here
        if with_year:
            # "3 februari 2025" / "3 feb 2025"
            return f"{day} {month_str} {year_str}"
        else:
            # "3 februari" / "3 feb"
            return f"{day} {month_str}"
    else:
        # Numeric month: either D-M or DD-MM (both parts same style)
        padded = _chance(DATE_NUMERIC_PADDED_PROB)
        if padded:
            day_str = f"{day:02d}"
            month_str = f"{month:02d}"
        else:
            day_str = str(day)
            month_str = str(month)

        if with_year:
            # "03-02-2025" or "3-2-2025"
            return f"{day_str}-{month_str}-{year_str}"
        else:
            # "03-02" or "3-2"
            return f"{day_str}-{month_str}"


def _natural_dutch_time() -> str:
    """
    Generate a simple natural-language Dutch time phrase, e.g.:
    - "kwart voor zes"
    - "kwart over drie"
    - "half vier"
    """
    # Use 1–11 as base hour; we'll map 0 -> "twaalf"
    base_hour = random.randint(0, 11)  # 0..11 -> 12,1,..11
    hour_word = DUTCH_HOUR_WORDS[base_hour]

    # "half vier" in Dutch means 3:30 (halfway to 4), so we need next hour word too
    next_hour_word = DUTCH_HOUR_WORDS[(base_hour + 1) % 12]

    kind = random.choice(["kwart_voor", "kwart_over", "half", "uur"])

    if kind == "kwart_voor":
        return f"kwart voor {next_hour_word}"
    elif kind == "kwart_over":
        return f"kwart over {hour_word}"
    elif kind == "half":
        return f"half {next_hour_word}"
    else:  # "uur"
        return f"{hour_word} uur"


def generate_fake_time(match: re.Match) -> str:
    """
    Generate a fake time in Dutch style.

    Formats:
    - "13:45"
    - "13:45 uur"
    - "13.45"
    - "13u45"
    - natural Dutch ("kwart voor zes", "half vier", ...)
    """
    # Base numeric time
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)

    idx = _choose_weighted_index(
        [
            TIME_FMT_HH_MM_PROB,
            TIME_FMT_HH_DOT_MM_PROB,
            TIME_FMT_HH_U_MM_PROB,
            TIME_FMT_NATURAL_DUTCH_PROB,
        ]
    )

    add_hour = _chance(TIME_ADD_HOUR)
    if add_hour:
        uur = " uur"
    else:
        uur = ""

    if idx == 0:
        return f"{hour:02d}:{minute:02d}{uur}"
    elif idx == 1:
        return f"{hour:02d}.{minute:02d}{uur}"
    elif idx == 2:
        # Belgian/Dutch style "12u23"
        return f"{hour}u{minute:02d}"
    else:
        # Natural phrase like "kwart voor zes"
        return _natural_dutch_time()


def generate_fake_age(match: re.Match) -> str:
    """
    Generate a fake age (years) using a 1D Gaussian Mixture Model defined in
    AGE_GMM_MEANS, AGE_GMM_VARS, AGE_GMM_WEIGHTS.

    We:
    - choose a component according to AGE_GMM_WEIGHTS
    - sample from N(mean, var) for that component
    - enforce integer age, truncated to [AGE_MIN, AGE_MAX]
      via simple rejection (with a fallback clamp)
    """
    if not (AGE_GMM_MEANS and AGE_GMM_VARS and AGE_GMM_WEIGHTS):
        # Fallback if misconfigured
        return str(random.randint(AGE_MIN, AGE_MAX))

    # Choose mixture component
    k = _choose_weighted_index(AGE_GMM_WEIGHTS)

    mean = AGE_GMM_MEANS[k]
    var = AGE_GMM_VARS[k]
    sigma = math.sqrt(var) if var > 0 else 1.0

    # Rejection sampling to stay within [AGE_MIN, AGE_MAX]
    for _ in range(10):
        sample = random.gauss(mean, sigma)
        age = int(round(sample))
        if AGE_MIN <= age <= AGE_MAX:
            return str(age)

    # Fallback: clamp a final sample
    sample = random.gauss(mean, sigma)
    age = int(round(sample))
    age = max(AGE_MIN, min(AGE_MAX, age))
    return str(age)


# --- Contact / location ------------------------------------------


def _fake_mobile_number() -> str:
    """
    Generate a Dutch-looking mobile number.
    """
    suffix = random.randint(10_000_000, 99_999_999)  # 8 digits
    style = random.choice(["dash", "space", "intl", "intl_brackets"])

    if style == "dash":
        return f"06-{suffix:08d}"
    elif style == "space":
        return f"06 {suffix:08d}"
    elif style == "intl":
        return f"+31 6 {suffix:08d}"
    else:
        return f"+31 (0)6 {suffix:08d}"


def _fake_landline_number() -> str:
    """
    Generate a Dutch-looking landline / hospital main number.
    """
    area = random.choice(DUTCH_AREA_CODES)
    # 7-digit subscriber part
    rest = random.randint(1_000_000, 9_999_999)
    style = random.choice(["dash", "space"])

    if style == "dash":
        return f"{area}-{rest:07d}"
    else:
        return f"{area} {rest:07d}"


def _fake_sein_number() -> str:
    """
    Generate a hospital SEIN / pager number, usually 4 or 5 digits. If 4 numbers they can start with a *.
    Examples in the wild: 2000, 59319, 55064, *5018, etc.
    """
    length = 4 if random.random() < 0.7 else 5
    upper = 10**length - 1
    num = random.randint(0, upper)
    if length == 4 and random.random() < 0.5:
        return f"*{num:03d}"
    return f"{num:0{length}d}"


def generate_fake_phone(match: re.Match) -> str:
    """
    Generate a fake phone-like string that can be:
    - a mobile number (06-xxxx xxxx)
    - a landline/hospital number (0xx-xxxxxxx)
    - an internal hospital SEIN number (4–5 digits)
    """
    idx = _choose_weighted_index(
        [
            PHONE_TYPE_MOBILE_PROB,
            PHONE_TYPE_LANDLINE_PROB,
            PHONE_TYPE_SEIN_PROB,
        ]
    )

    if idx == 0:
        return _fake_mobile_number()
    elif idx == 1:
        return _fake_landline_number()
    else:
        return _fake_sein_number()


def generate_fake_address(match: re.Match) -> str:
    """Generate a fake address."""
    addr = _fake.address()
    return addr + "\n"


def generate_fake_location(match: re.Match) -> str:
    """Generate a fake city/location name."""
    return _fake.city()


# --- IDs / numbers -----------------------------------------------


def _generate_from_template(template: str) -> str:
    """
    Generate a random string from a tiny ID template language:

      # -> digit 0–9
      A -> uppercase letter
      a -> lowercase letter
      X -> uppercase letter or digit

      Any other char is literal.
    """
    chars = []
    for ch in template:
        if ch == "#":
            chars.append(random.choice(string.digits))
        else:
            chars.append(ch)
    return "".join(chars)


def generate_id_from_tag(match: re.Match) -> str:
    """
    Generic ID generator that looks at the matched *tag* and chooses an ID
    template from settings.ID_TEMPLATES_BY_TAG.

    Example:
      "<Z-NUMMER>" -> "Z######" -> "Z123456"
    """
    tag = match.group(0)  # the literal text that matched, e.g. "<Z-NUMMER>"
    template = ID_TEMPLATES_BY_TAG.get(tag, ID_TEMPLATE_DEFAULT)
    if isinstance(template, (list, tuple)):
        template = random.choice(template)
    return _generate_from_template(template)


def generate_fake_accreditation_number(match: re.Match) -> str:
    """
    Generate a fake accreditation number in the form 'M123'.
    Always 'M' + 3 digits.
    """
    return f"M{random.randint(0, 999):03d}"


def generate_fake_bsn(match: re.Match) -> str:
    """
    Generate a fake BSN-like number using Faker's ssn(), normalized to digits.

    For nl_NL, Faker.ssn() yields a Dutch-style citizen service number.
    We strip any non-digits just to be safe and ensure it's 9 digits if possible.
    """
    digits = _fake.ssn()

    # If Faker ever returns something not 9 digits, we pad/trim.
    if len(digits) < 9:
        digits = digits.ljust(9, "0")
    elif len(digits) > 9:
        digits = digits[:9]

    return digits


def generate_fake_iban(match: re.Match) -> str:
    """
    Generate a fake Dutch IBAN using Faker, with realistic formatting.

    Examples:
      - "NL91ABNA0417164300"
      - "NL91 ABNA 0417 1643 00"
    """
    raw = _fake.iban()

    # Normalize to "compact" form first (no spaces)
    compact = raw.replace(" ", "")

    # Randomly choose formatting style
    style = random.choice(["compact", "spaced"])

    if style == "compact":
        return compact

    # grouped as "NL91 ABNA 0417 1643 00"
    groups = [compact[i : i + 4] for i in range(0, len(compact), 4)]
    return " ".join(groups)


# --- Other text fields -------------------------------------------


def generate_fake_hospital_name(match: re.Match) -> str:
    """
    Generate a fake hospital mention that can be:
      - a hospital name or abbreviation (ADRZ, LUMC, Radboudumc)
      - OR just a location ("Amsterdam") that implicitly refers to the hospital
    """
    if not HOSPITAL_NAME_POOL:
        return _fake.company()

    idx = random.randrange(len(HOSPITAL_NAME_POOL))

    name_variants = HOSPITAL_NAME_POOL[idx] or []
    city_variants = HOSPITAL_CITY_POOL[idx] if idx < len(HOSPITAL_CITY_POOL) else []
    city_variants = city_variants or []

    # If both are empty (shouldn't happen), fall back
    if not name_variants and not city_variants:
        return _fake.company()

    # Chance to use location-only instead of hospital name
    # e.g. "overgeplaatst naar Amsterdam" instead of "overgeplaatst naar AMC"
    use_city = bool(city_variants) and random.random() < HOSPITAL_NAME_CITY_ONLY_PROB

    if use_city:
        return random.choice(city_variants)

    # Fall back to names/abbrevs
    if name_variants:
        return random.choice(name_variants)

    # If we somehow have cities but no names
    return random.choice(city_variants)


def generate_fake_study_name(match: re.Match) -> str:
    """
    Generate a fake study name from a predefined pool.

    Some entries in STUDY_NAME_POOL are lists, which represent
    multiple textual variants of the same study; in that case
    we pick one variant at random.

    Examples:
      - "LEMA"
      - "Donan"
      - "M-SPECT" / "mSPECT"
      - "Alpe d'Huzes MRI" / "Alpe d' Huzes MRI" / "Alpe"
      - "MR-PRIAS" / "MRPRIAS" / "PRIAS"
    """
    choice = random.choice(STUDY_NAME_POOL)

    # If this pool entry has multiple variants, pick one
    if isinstance(choice, (list, tuple)):
        if not choice:
            return ""
        return random.choice(choice)

    return choice


def generate_fake_email(match: re.Match) -> str:
    """
    Generate a fake email address.

    Uses Faker's email, but you could later customize the pattern to
    match your hospital style (e.g. initials + lastname).
    """
    return _fake.free_email()


def generate_fake_url(match: re.Match) -> str:
    """
    Generate a fake URL.

    Uses Faker's url(), which gives plausible http(s) URLs.
    """
    return _fake.uri()


def generate_fake_company_name(match: re.Match) -> str:
    """
    Generate a fake company name.

    Uses Faker's company(), which gives plausible Dutch company names.
    """
    return _fake.company()


# --- Mapping from PHI type -> generator --------------------------


DEFAULT_GENERATORS: Dict[str, Callable[[re.Match], str]] = {
    PHIType.PERSON_NAME: generate_fake_person_name,
    PHIType.PERSON_NAME_ABBREV: generate_fake_person_initials,
    PHIType.DATE: generate_fake_date,
    PHIType.TIME: generate_fake_time,
    PHIType.PHONE_NUMBER: generate_fake_phone,
    PHIType.ADDRESS: generate_fake_address,
    PHIType.LOCATION: generate_fake_location,
    PHIType.GENERIC_ID: generate_id_from_tag,
    PHIType.AGE: generate_fake_age,
    PHIType.HOSPITAL_NAME: generate_fake_hospital_name,
    PHIType.ACCREDITATION_NUMBER: generate_fake_accreditation_number,
    PHIType.STUDY_NAME: generate_fake_study_name,
    PHIType.BSN: generate_fake_bsn,
    PHIType.IBAN: generate_fake_iban,
    PHIType.EMAIL: generate_fake_email,
    PHIType.URL: generate_fake_url,
    PHIType.COMPANY_NAME: generate_fake_company_name,
}
