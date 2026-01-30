"""
Configuration constants for random 'chances' and other defaults in the
anonymization pipeline.
"""

# --- Chance / probability knobs -----------------------------------

# Very small chance to add a spelling error / typo to a surrogate.
# Example: 0.002 = 0.2% per surrogate.
TYPO_IN_SURROGATE_PROB: float = 0.002

# Default behaviour flags
DEFAULT_ENABLE_RANDOM_TYPOS: bool = True

# --- Person name formatting knobs --------------------------------

# Probability that we output ONLY a first name
PERSON_NAME_FIRST_ONLY_PROB: float = 0.05

# Probability that we output ONLY a last name
PERSON_NAME_LAST_ONLY_PROB: float = 0.6
# Remaining probability (1 - above) is for full "first last"

# Probability that the *first name* is rendered as initials
# (only when a last name is present)
PERSON_NAME_INITIALS_PROB: float = 0.25

# Max number of initials (e.g. 3 -> J., J.S., J.S.T.)
PERSON_NAME_MAX_INITIALS: int = 3

# Capitalization probabilities
PERSON_NAME_LOWERCASE_PROB: float = 0.05
PERSON_NAME_UPPERCASE_PROB: float = 0.005

# Probability for "Lastname, First" ordering (when both parts present)
PERSON_NAME_REVERSE_ORDER_PROB: float = 0.01

# Probability to reuse a previous person name in the same document
PERSON_NAME_REUSE_PROB: float = 0.1

# --- Date formatting knobs ---------------------------------------

# Options for date range sampling consist of:
#   "today" = today
#   "-Ny" = N years ago from today
#   "-Nm" = N months ago from today
#   "-Nd" = N days ago from today
#   "dd-mm-yyyy" = fixed date
DATE_EARLIEST = "-10y"
DATE_LATEST = "today"

# Step 1: with or without year
DATE_WITH_YEAR_PROB: float = (
    0.75  # e.g. "03-02-2025", "3 feb 2025 instead of "03-02", "3 feb"
)

# Step 2: month as name or number
DATE_MONTH_AS_NAME_PROB: float = (
    0.40  # e.g. "3 februari", "3 feb 2025 instead of "3-2", "03-02-2025"
)

# Step 2: year format (if year present)
DATE_YEAR_FULL_PROB: float = 0.60  # e.g. "2025 instead of "25"

# Step 3 (numeric): either D-M or DD-MM (both day & month same style)
DATE_NUMERIC_PADDED_PROB: float = 0.60  # "03-02" vs "3-2"

# Step 3 (named month): full vs abbreviated month name
DATE_MONTH_NAME_ABBR_PROB: float = 0.40  # "feb" vs "februari"


# --- Time formatting knobs ---------------------------------------

# Relative frequencies for time formats:
#  - "13:45"
#  - "13:45 uur"
#  - "13.45"
#  - "13u45"
#  - natural Dutch phrases ("kwart voor zes", "half vier", ...)
TIME_FMT_HH_MM_PROB: float = 0.70  # "13:45"
TIME_FMT_HH_DOT_MM_PROB: float = 0.1  # "13.45"
TIME_FMT_HH_U_MM_PROB: float = 0.1  # "13u45"
TIME_FMT_NATURAL_DUTCH_PROB: float = 0.1  # "kwart voor zes", "half vier"
TIME_ADD_HOUR: float = 0.2  # add "uur" suffix


# --- Age distribution knobs (Gaussian Mixture Model) --------------

# Parameters of a 3-component 1D Gaussian Mixture for age, based on
# hospital-like data. Age is in years.
AGE_GMM_MEANS = [
    71.22211106,
    32.77964968,
    56.70935326,
]

AGE_GMM_VARS = [
    46.83038289,
    135.5549187,
    57.88157936,
]

AGE_GMM_WEIGHTS = [
    0.46571202,
    0.15135840,
    0.38292958,
]

# Hard bounds for ages (inclusive); used for truncating/rejecting samples.
AGE_MIN: int = 0
AGE_MAX: int = 105


# --- Phone / SEIN formatting knobs --------------------------------

# Relative frequency of different phone-like outputs
# - mobile phone numbers (06-...)
# - landline / hospital main numbers (0xx-...)
# - internal SEIN/pager numbers (4–5 digits)
PHONE_TYPE_MOBILE_PROB: float = 0.50  # e.g. "06-12345678"
PHONE_TYPE_LANDLINE_PROB: float = 0.35  # e.g. "020-5669111"
PHONE_TYPE_SEIN_PROB: float = 0.15  # e.g. "59319", "2000"

# --- Hospital name formatting knobs -------------------------------

# Probability to use only the city name instead of full hospital name
HOSPITAL_NAME_CITY_ONLY_PROB: float = 0.3

# --- Tag-based ID templates ---------------------------------------

# Map *tag text* (as it appears in the text) to ID templates.
# Users can override this dict in their own code.
ID_TEMPLATES_BY_TAG = {
    # Z-numbers
    "<Z_NUMMER>": "Z######",
    "<Z-NUMBER>": "Z######",
    "<ZNUMMER>": "Z######",
    "<ZNUMBER>": "Z######",
    "<Z-NUMMER>": "Z######",
    "<Z-NUMBER>": "Z######",
    # Patient IDs
    "<PATIENT_ID>": "#######",
    "<PATIENTID>": "#######",
    "<PATIENTNUMMER>": "#######",
    # Generic PHI numbers
    "<PHI_NUMMER>": "######",
    "<PHI_NUMBER>": "######",
    "<PHINUMMER>": "######",
    "<PHINUMBER>": "######",
    "<PHI-NUMMER>": "######",
    "<PHI-NUMBER>": "######",
    # Document IDs
    "<RAPPORT-ID.T-NUMMER>": ["T######", "T ######", "T-######"],
    "<RAPPORT_ID.T_NUMMER>": ["T######", "T ######", "T-######"],
    "<RAPPORT-ID.R-NUMMER>": ["R######", "R ######", "R-######"],
    "<RAPPORT_ID.R_NUMMER>": ["R######", "R ######", "R-######"],
    "<RAPPORT-ID.C-NUMMER>": ["C######", "C ######", "C-######"],
    "<RAPPORT_ID.C_NUMMER>": ["C######", "C ######", "C-######"],
    "<RAPPORT-ID.DPA-NUMMER>": ["DPA######", "DPA ######", "DPA-######"],
    "<RAPPORT_ID.DPA_NUMMER>": ["DPA######", "DPA ######", "DPA-######"],
    "<RAPPORT-ID.RPA-NUMMER>": ["RPA######", "RPA ######", "RPA-######"],
    "<RAPPORT_ID.RPA_NUMMER>": ["RPA######", "RPA ######", "RPA-######"],
}

# Fallback template if a tag is not in ID_TEMPLATES_BY_TAG but is handled
# by the generic ID generator.
ID_TEMPLATE_DEFAULT = "########"


# --- Study name pool ----------------------------------------------

STUDY_NAME_POOL = [
    "LEMA",
    "Donan",
    ["M-SPECT", "mSPECT"],
    "CAELC",
    "PINNACLE",
    "M18ICR",
    "4M",
    ["Alpe d'Huzes MRI", "Alpe d' Huzes MRI", "Alpe"],
    "N21SPL",
    "M21MUP",
    "M13PSN",
    "B18NCI",
    "CFMPB 293",
    "N18WGS - 2",
    "IRBm19-124",
    "DARANA",
    "M19OTE-1",
    "N14DAR",
    "PROMPT",
    "TULIP",
    "N18CLI",
    "BIA",
    ["MR-PRIAS", "MRPRIAS", "PRIAS"],
    "CFMPB484",
    "CLIPPS",
    "CFMPB283",
    "N13PSN",
    "N12IGP",
    "M11TOO",
    "M20FRM",
    "TOOKAD",
    "colopec",
    "DC vacc",
    "MDV-3800",
    "Keynote-199",
    "HOVON",
    "G250",
    "CAIRO",
    "M14CDP-1",
    "Luctas",
    "TARZAN",
]


# --- Header / disclaimer knobs ------------------------------------

DEFAULT_ENABLE_HEADER: bool = True

DEFAULT_HEADER_TEMPLATE: str = (
    "##############################\n"
    "DISCLAIMER  (dutch-med-hips v{version})\n"
    "\n"
    "THIS DOCUMENT HAS BEEN AUTOMATICALLY ANONYMIZED.\n"
    "IDENTIFIABLE PATIENT HEALTH INFORMATION HAS BEEN REPLACED WITH\n"
    "SYNTHETIC SURROGATES GENERATED BY DUTCH-MED-HIPS.\n"
    "\n"
    "ALL PERSONAL DETAILS ARE ARTIFICIAL. ANY RESEMBLANCE TO REAL\n"
    "PERSONS IS ENTIRELY COINCIDENTAL.\n"
    "##############################\n"
    "\n"
)
