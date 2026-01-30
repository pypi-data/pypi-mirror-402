# 🇳🇱 dutch-med-hips

A robust, highly configurable **PHI anonymization and surrogate generation** toolkit designed for **Dutch medical and radiology reports**.  
It replaces PHI tokens (e.g. `<PERSOON>`, `<Z-NUMMER>`, `<DATUM>`) with realistic surrogate values such as names, ages, dates, hospitals, study names, IDs, BSNs, IBANs, phone numbers, URLs, emails, and more.

`dutch-med-hips` uses:

- [**Faker**](https://faker.readthedocs.io/en/master/) for Dutch-language surrogate generation  
- **Configurable templates** for ID-like fields  
- **Locale dictionaries** for hospitals, months, cities, study names  
- **A combined regex engine** for fast and safe substitution  
- **Document-level deterministic seeding** (optional)

---

## Installation

You can install `dutch-med-hips` via pip:

```bash
pip install dutch-med-hips
```

or from source:

```bash
git clone https://github.com/DIAGNijmegen/dutch-med-hips.git
cd dutch-med-hips
pip install -e .
```

---

## Quickstart

### Python API

Running HideInPlainSight in your Python code is straightforward:

```python
from dutch_med_hips import HideInPlainSight

text = """
Patiënt <PERSOON> werd opgenomen in <HOSPITAL_NAME> op <DATUM>.
Z-nummer: <Z-NUMMER>, BSN: <BSN>, Email: <EMAIL>.
Rapport ID: <RAPPORT_ID.T_NUMMER>.
""" 

hips = HideInPlainSight()
result = hips.run(text)

print(result["text"])
print(result["mapping"])  # Shows original -> surrogate mapping
```

### Command-Line Interface

You can also use `dutch-med-hips` directly from the command line:

```bash
dutch-med-hips [OPTIONS]
```

#### Common Options

| Option | Meaning |
|--------|---------|
| `-i, --input PATH` | Input file (UTF-8). Use `-` or omit to read from **stdin**. |
| `-o, --output PATH` | Output file (UTF-8). Use `-` or omit to write to **stdout**. |
| `--mapping-out PATH` | Write the JSON mapping (original → surrogate) to a file. |
| `--seed N` | Use a fixed seed for deterministic surrogate generation. |
| `--no-document-hash-seed` | Disable automatic seeding based on the document hash. |
| `--no-header` | Disable the anonymization disclaimer header. |
| `--disable-typos` | Disable random typo injection in surrogates. |

---

## Features

### 🔐 PHI Surrogates

#### 👤 People & Demographics

- **Person names**
  - Dutch-style names (first/last), tussenvoegsels (`van`, `de`, …)
  - Variants: first-only, last-only, full, initials (`J. Jansen`, `J.S. Jansen`)
  - Randomized casing (`jan jansen`, `JAN JANSEN`, `Jansen, Jan`)
- **Person initials**
  - Derived from full fake names: `Jan Steen` → `JS`, `Vincent van Gogh` → `VvG`
- **Age**
  - Sampled from a hospital-like Gaussian mixture model (more 40–85 year olds)

#### 🧾 Identifiers & Numbers

- **Patient IDs / Z-numbers / generic PHI numbers**
  - All driven by simple templates per tag (e.g. `<Z-NUMMER>` → `Z######`)
  - Template mini-language (`#` = digit, etc.)
- **Document IDs & sub-IDs**
  - Main report IDs from templates
  - Sub-IDs like `<RAPPORT_ID.T_NUMMER>` → `T123456`
- **BSN**
  - Dutch BSN-like numbers via Faker `ssn()`
- **IBAN**
  - Dutch IBANs via Faker, compact or grouped (`NL91ABNA0417164300`, `NL91 ABNA 0417 1643 00`)
- **Accreditation number**
  - Always `M` + 3 digits (e.g. `M007`, `M123`)

#### 🏥 Hospitals, Locations & Studies

- **Hospital names**
  - Realistic Dutch hospital pool with full names and abbreviations  
    e.g. `Amsterdam UMC locatie AMC`, `AMC`, `Radboudumc`, `LUMC`, `ADRZ`
  - Sometimes uses only the city as shorthand (e.g. `Amsterdam`, `Nijmegen`)
- **Locations**
  - Dutch cities and place names drawn from hospital/location data
- **Study names**
  - Curated list of real-looking study labels and variants
    e.g. `LEMA`, `Donan`, `M-SPECT`/`mSPECT`, `Alpe d'Huzes MRI`, `TULIP`, `PRIAS`
- **Company names**
  - Dutch company names via Faker (`nl_NL`)
    e.g. `Van der Berg BV`, `Jansen en Zonen`, `De Vries Holding`

#### 📅 Dates & Times

- **Dates**
  - Dutch-style formats:
    - Numeric: `D-M`, `DD-MM`, with/without year (`03-02-2025`, `3-2-12`)
    - Named months: `3 februari`, `3 feb 2025`
  - Mix of year/no-year, numeric vs month-name
  - Start/end date range configuration (e.g. last 10 years)
- **Times**
  - 24h clock formats: `13:45`, `13:45 uur`, `13.45`, `13u45`
  - Natural Dutch phrases: `kwart voor zes`, `kwart over drie`, `half vier`

#### 📞 Contact & Online

- **Phone numbers**
  - Dutch mobile numbers (`06-12345678`, `+31 6 12345678`)
  - Landlines / hospital numbers (`020-5669111`, `088-…`)
  - Internal SEIN/pager numbers (4–5 digit codes)
- **Email addresses**
  - Fake but valid emails via Faker (customizable domains)
- **URLs**
  - Fake but valid http(s) URLs via Faker (can be styled to look like portals/EPD endpoints)

#### 🏠 Addresses & Misc

- **Addresses**
  - Dutch-style street + number + postcode + city via Faker (`nl_NL`)
- **Other PHI**
  - Any additional tag-based IDs or tokens configured via templates can be mapped to surrogates in the same way.

### 🔧 Flexible Configuration

All defaults live in `settings.py` and can be overridden at runtime:

```python
from dutch_med_hips import settings

settings.ID_TEMPLATES_BY_TAG["<Z-NUMMER>"] = "Z-###-###"
settings.PERSON_NAME_REUSE_PROB = 0.15
settings.ENABLE_TYPOS = True
```

### 🧪 Deterministic Output

The system automatically hashes the document to generate a seed to stabilize output. This can be turned off, or you can provide your own fixed seed:

```python
hips = HideInPlainSight(default_seed=123)
```

!!! Note
    Using a fixed seed means the **same input document** will always yield the **same output document** and **same surrogate mappings**.  
    Different documents will still produce different outputs.

### ✏️ Optional Typo Injection

Using the [`typo`](https://github.com/ranvijaykumar/typo) Python package, some surrogates can receive:

- Adjacent-key typos
- Insertions
- Deletions  
You can enable/disable this globally.

### ⚠️ Automatic Disclaimer Header

Every anonymized document can automatically receive an anonymization disclaimer at the top.  
You may customize or disable it.

---

## Defining Custom PHI Tags

`dutch-med-hips` allows users to extend PHI detection and surrogate generation without modifying the library.  
Below are the **three most common customization patterns**, with clear examples:

1. **Add a new regex to an existing PHI category** (easiest)  
2. **Create a new ID-style tag with its own format** (advanced)  
3. **Extend surrogate pools** (e.g. add a new study name)

---

### 1️⃣ Adding a New Regex to Person Names (Simple Example)

If your reports use additional person‑name markers such as `<NM>` or `<PERSOON_NAAM>`, you can plug them into the existing system.

Just add them to the existing PHI type:

```python
from dutch_med_hips import schema
from dutch_med_hips.schema import PHIType

schema.DEFAULT_PATTERNS[PHIType.PERSON_NAME].extend([
    r"<NM>",
    r"<PERSOON_NAAM>",
])
```

These new tags will:

✔ Be recognized as person names  
✔ Use the existing name surrogate logic  
✔ Appear in the mapping as `phi_type="person_name"`  

**Example:**

```python
text = "Patiënt <NM> en begeleider <PERSOON_NAAM> kwamen binnen."
print(HideInPlainSight(seed=1).run(text)["text"])
```

---

### 2️⃣ Creating a New ID Tag with a Custom Format (Advanced)

Suppose your system uses `<CENTER_ID>` and you want outputs like:

```bash
CEN-123456
```

#### Step 1 — Add a detection pattern

```python
from dutch_med_hips import schema
from dutch_med_hips.schema import PHIType

schema.DEFAULT_PATTERNS.setdefault(PHIType.GENERIC_ID, []).append(
    r"<CENTER_ID>"
)
```

#### Step 2 — Assign a surrogate template

Use the template mini‑language (`#` = digit):

```python
from dutch_med_hips import settings

settings.ID_TEMPLATES_BY_TAG["<CENTER_ID>"] = "CEN-######"
```

#### Step 3 — Use it

```python
from dutch_med_hips import HideInPlainSight

text = "Centrum: <CENTER_ID>."
print(HideInPlainSight(seed=42).run(text)["text"])
# Centrum: CEN-123456.
```

---

### 3️⃣ Adding New Items to Surrogate Pools (e.g., Study Names)

Some surrogate categories use **pools**, such as the curated list of Dutch medical study names in `locale.py`:

```python
STUDY_NAME_POOL = [
    "LEMA",
    "Donan",
    ["M-SPECT", "mSPECT"],
    ...
]
```

To add your own study:

```python
from dutch_med_hips import settings

settings.STUDY_NAME_POOL.append("MY-NEW-STUDY")
```

Or add multiple variants:

```python
settings.STUDY_NAME_POOL.append([
    "CUSTOMTRIAL",
    "Custom Trial",
    "CT-Study"
])
```

The generator will randomly pick one of the variants.

#### Example

```python
text = "Onderzoek: <STUDY_NAME>."
hips = HideInPlainSight(seed=123)
print(hips.run(text)["text"])
# Onderzoek: MY-NEW-STUDY.
```

---

### Optional: Full Custom Generator

For more complex surrogate rules, you can define your own PHI type and generator:

```python
import re
from dutch_med_hips import schema, surrogates

def generate_center(match: re.Match) -> str:
    return "CENTER-" + "123456"

schema.DEFAULT_PATTERNS["center"] = [r"<CENTER_SPECIAL>"]
surrogates.DEFAULT_GENERATORS["center"] = generate_center
```

Now `<CENTER_SPECIAL>` maps through your custom function.

---

### Summary

| Task | Best Method |
|------|-------------|
| Add a new tag to an existing PHI category | Add regex to `schema.DEFAULT_PATTERNS[...]` |
| Create a new ID-like tag | Add regex + assign template via `settings.ID_TEMPLATES_BY_TAG` |
| Add new study/hospital/name variants | Append to the appropriate pool in `settings` |
| Create fully custom surrogate logic | Register generator in `surrogates.DEFAULT_GENERATORS` |

Customizing `dutch-med-hips` is:  
**Add regex → (optional) assign template or generator → done.**

---

## NER Label Position Tracking

When working with NER (Named Entity Recognition) pipelines, you often have label positions that need to stay aligned after surrogate substitution. `dutch-med-hips` can automatically update these positions for you.

### Usage

Pass your NER labels as a list of `(start, end, label)` tuples:

```python
from dutch_med_hips import HideInPlainSight

text = "Patient <PERSOON> geboren op <DATUM> in Amsterdam."
ner_labels = [
    (8, 17, "<PERSOON>"),   # Position of <PERSOON> tag
    (29, 36, "<DATUM>"),    # Position of <DATUM> tag
    (40, 49, "LOCATION"),   # Position of "Amsterdam" (non-PHI)
]

hips = HideInPlainSight(enable_header=False)
result = hips.run(text, ner_labels=ner_labels)

print(result["text"])
# "Patient Jan de Vries geboren op 15-03-1985 in Amsterdam."

print(result["updated_labels"])
# [(8, 20, "<PERSOON>"), (32, 42, "<DATUM>"), (46, 55, "LOCATION")]
```

### How It Works

- Labels **before** a replacement remain unchanged
- Labels **after** a replacement are shifted by the length difference (surrogate length - original length)
- Labels that **overlap** with a replacement have their end position adjusted
- When the header is enabled, all label positions are shifted by the header length

This is useful when you need to:
- Preserve NER annotations through anonymization
- Track entity positions for downstream processing
- Maintain alignment between original and anonymized text annotations

---

## Mapping Output Structure

`result = hips.run(text)` returns:

```python
{
    "text": "anonymized text...",
    "mapping": [
        {
            "original": "<PERSOON>",
            "surrogate": "Jan Steen",
            "phi_type": "person_name",
            "start": 10,
            "end": 18
        },
        ...
    ],
    "updated_labels": [...]  # Only present if ner_labels was provided
}
```

---
