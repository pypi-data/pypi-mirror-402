from typing import Dict, List


class PHIType:
    PERSON_NAME = "person_name"
    PERSON_NAME_ABBREV = "person_name_abbrev"
    DATE = "date"
    TIME = "time"
    PHONE_NUMBER = "phone_number"
    ADDRESS = "address"
    LOCATION = "location"
    AGE = "age"
    HOSPITAL_NAME = "hospital_name"
    ACCREDITATION_NUMBER = "accreditation_number"
    STUDY_NAME = "study_name"
    BSN = "bsn"
    IBAN = "iban"
    GENERIC_ID = "generic_id"
    EMAIL = "email"
    URL = "url"
    COMPANY_NAME = "company_name"


# "Smart" regex patterns per PHI type
DEFAULT_PATTERNS: Dict[str, List[str]] = {
    # <PERSOON>, <PERSON_NAME>, <NAAM>, <NAME>
    PHIType.PERSON_NAME: [
        r"<(?:PERSOON|PERSON_NAME|NAAM|NAME)>",
    ],
    # <DATE>, <DATUM>
    PHIType.DATE: [
        r"<(?:DATE|DATUM)>",
    ],
    # <TIME>, <TIJD>
    PHIType.TIME: [
        r"<(?:TIME|TIJD)>",
    ],
    # <PHONE>, <PHONENUMBER>, <TELEFOON>, <TELEFOONNUMMER>
    PHIType.PHONE_NUMBER: [
        r"<(?:PHONE|PHONENUMBER|TELEFOON|TELEFOONNUMMER)>",
    ],
    # <ADRES>, <ADDRESS>
    PHIType.ADDRESS: [
        r"<(?:ADRES|ADDRESS)>",
    ],
    # <LOCATIE>, <LOCATION>, <PLAATS>, <PLACE>
    PHIType.LOCATION: [
        r"<(?:LOCATIE|LOCATION|PLAATS|PLACE)>",
    ],
    # <LEEFTIJD>, <AGE>
    PHIType.AGE: [
        r"<(?:LEEFTIJD|AGE)>",
    ],
    # <PERSON_INITIALS>, <PERSOONAFKORTING>
    PHIType.PERSON_NAME_ABBREV: [
        r"<(?:PERSON_INITIALS|PERSOONAFKORTING)>",
    ],
    # <HOSPITAL_NAME>, <ZIEKENHUIS>, <HOSPITAL>
    PHIType.HOSPITAL_NAME: [
        r"<(?:HOSPITAL_NAME|ZIEKENHUIS|HOSPITAL)>",
    ],
    # <ACCREDITATION_NUMBER>, <ACCREDITATIE_NUMMER>
    PHIType.ACCREDITATION_NUMBER: [
        r"<(?:ACCREDITATION_NUMBER|ACCREDITATIE_NUMMER|ACCREDATIE[-_]?NUMMER)>",
    ],
    # <STUDY_NAME>, <STUDYNAME>, <STUDY-NAME>,
    # <STUDIENAAM>, <STUDIE_NAAM>, <STUDIE-NAAM>
    PHIType.STUDY_NAME: [
        r"<(?:STUDY[-_]?NAME|STUDIE[-_]?NAAM)>",
    ],
    PHIType.BSN: [
        r"<BSN>",
        r"<BSNNUMMER>",
        r"<BSNNUMBER>",
        r"<BSN-NUMMER>",
        r"<BSN-NUMBER>",
    ],
    PHIType.IBAN: [
        r"<IBAN>",
        r"<IBANNUMMER>",
        r"<IBANNUMBER>",
        r"<IBAN-NUMMER>",
        r"<IBAN-NUMBER>",
    ],
    PHIType.GENERIC_ID: [
        r"<PATIENT(?:_ID|ID|NUMMER)>",
        r"<Z[-_]?(?:NUMMER|NUMBER)>",
        r"<RAPPORT[_-]ID\.(T|R|C|DPA|RPA)[_-]NUMMER>",
        r"<PHI[-_]?(?:NUMMER|NUMBER)>",
        r"<(?:DOCUMENT|RAPPORT)[-_]?ID>",
    ],
    PHIType.EMAIL: [
        r"<EMAIL>",
        r"<EMAILADRES>",
        r"<E[-_]?MAIL>",
        r"<MAILADRES>",
    ],
    PHIType.URL: [
        r"<URL>",
        r"<LINK>",
        r"<WEBSITE>",
        r"<WEBADRES>",
    ],
    PHIType.COMPANY_NAME: [
        r"<(?:COMPANY|BEDRIJF|BEDRIJFSNAAM|COMPANY_NAME)>",
    ],
}
