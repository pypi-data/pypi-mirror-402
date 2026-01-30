# locale.py

DUTCH_MONTHS_FULL = [
    "januari",
    "februari",
    "maart",
    "april",
    "mei",
    "juni",
    "juli",
    "augustus",
    "september",
    "oktober",
    "november",
    "december",
]

DUTCH_MONTHS_ABBR = [
    "jan",
    "feb",
    "mrt",
    "apr",
    "mei",
    "jun",
    "jul",
    "aug",
    "sep",
    "okt",
    "nov",
    "dec",
]

DUTCH_HOUR_WORDS = [
    "twaalf",
    "één",
    "twee",
    "drie",
    "vier",
    "vijf",
    "zes",
    "zeven",
    "acht",
    "negen",
    "tien",
    "elf",
]

DUTCH_AREA_CODES = [
    "010",
    "0111",
    "0113",
    "0114",
    "0115",
    "0117",
    "0118",
    "013",
    "015",
    "0161",
    "0162",
    "0164",
    "0165",
    "0166",
    "0167",
    "0168",
    "0172",
    "0174",
    "0180",
    "0181",
    "0182",
    "0183",
    "0184",
    "0186",
    "0187",
    "020",
    "0222",
    "0223",
    "0224",
    "0226",
    "0227",
    "0228",
    "0229",
    "023",
    "024",
    "0251",
    "0252",
    "0255",
    "026",
    "0294",
    "0297",
    "0299",
    "030",
    "0313",
    "0314",
    "0315",
    "0316",
    "0317",
    "0318",
    "0320",
    "0321",
    "033",
    "0341",
    "0342",
    "0343",
    "0344",
    "0345",
    "0346",
    "0347",
    "0348",
    "035",
    "036",
    "038",
    "040",
    "0411",
    "0412",
    "0413",
    "0416",
    "0418",
    "043",
    "045",
    "046",
    "0475",
    "0478",
    "0481",
    "0485",
    "0486",
    "0487",
    "0488",
    "0492",
    "0493",
    "0495",
    "0497",
    "0499",
    "050",
    "0511",
    "0512",
    "0513",
    "0514",
    "0515",
    "0516",
    "0517",
    "0518",
    "0519",
    "0521",
    "0522",
    "0523",
    "0524",
    "0525",
    "0527",
    "0528",
    "0529",
    "053",
    "0541",
    "0543",
    "0544",
    "0545",
    "0546",
    "0547",
    "0548",
    "055",
    "0561",
    "0562",
    "0566",
    "0570",
    "0571",
    "0572",
    "0573",
    "0575",
    "0577",
    "0578",
    "058",
    "0591",
    "0592",
    "0593",
    "0594",
    "0595",
    "0596",
    "0597",
    "0598",
    "0599",
    "070",
    "071",
    "072",
    "073",
    "074",
    "075",
    "076",
    "077",
    "078",
    "079",
    "088",
]

# Each inner list = variants for one hospital (names + abbreviations)
HOSPITAL_NAME_POOL = [
    ["Admiraal de Ruijter", "Admiraal de Ruyter", "ADRZ"],
    ["Albert Schweitzer", "ASz"],
    ["Alrijne"],
    ["Amphia"],
    ["Amsterdam UMC locatie AMC", "Amsterdam UMC", "AUMC-AMC", "AMC"],
    ["Amsterdam UMC locatie VUmc", "AUMC-Vumc", "Vumc", "VUMC"],
    ["Anna Zorggroep"],
    ["Antonius", "AZS"],
    ["Bernhoven"],
    ["BovenIJ"],
    ["Bravis"],
    ["Canisius-Wilhelmina", "CWZ"],
    ["Catharina", "CZE"],
    ["Deventer", "DZ"],
    ["Diakonessenhuis", "diak"],
    ["Dijklander", "DLZ"],
    ["Elisabeth-TweeSteden", "ETZ"],
    ["Elkerliek"],
    ["Erasmus MC"],
    ["Flevo"],
    ["Franciscus Gasthuis & Vlietland"],
    ["Gelre ziekenhuizen"],
    ["Groene Hart", "GHZ"],
    ["Haga"],
    ["HagaZiekenhuis Zoetermeer", "HagaZiekenhuis"],
    ["Haaglanden Medisch Centrum", "HMC"],
    ["IJsselland", "YSL"],
    ["Ikazia"],
    ["Isala"],
    ["Jeroen Bosch", "JBZ"],
    ["Laurentius", "LZR"],
    ["Leids Universitair Medisch Centrum", "LUMC"],
    ["Maasstad"],
    [
        "Maastricht UMC",
        "Maastricht UMC+",
        "Academisch Ziekenhuis Maastricht",
        "MUMC",
        "azM",
    ],
    ["Maasziekenhuis Pantein"],
    ["Martini"],
    ["Máxima MC", "MMC"],
    ["Meander Medisch Centrum"],
    ["Medisch Centrum Leeuwarden", "MCL"],
    ["Medisch Spectrum Twente", "MST"],
    ["Nij Smellinghe"],
    ["Noordwest Ziekenhuisgroep", "Medisch Centrum Alkmaar", "NWZ", "MCA"],
    ["OLVG", "OLVG Oost", "OLVG West"],
    ["Ommelander Ziekenhuis Groningen", "OZG"],
    [
        "Radboud UMC",
        "Radboudumc",
        "UMC St. Radboud",
        "RadboudMC",
        "Radboud",
        "RUMC",
        "UMCN",
    ],
    ["Reinier de Graaf Gasthuis"],
    ["Rijnstate"],
    ["Rivas Zorggroep", "Beatrix"],
    ["Rode Kruis", "RKZ"],
    ["Saxenburgh Medisch Centrum"],
    ["Sint Antonius"],
    ["Slingeland"],
    ["Spaarne Gasthuis"],
    ["Spijkenisse Medisch Centrum"],
    ["St Jansdal", "Jansdal"],
    ["St. Antonius", "Antonius"],
    ["St. Jans Gasthuis"],
    ["Streekziekenhuis Koningin Beatrix", "SKB"],
    ["Tergooi MC"],
    ["Tjongerschans"],
    ["Treant Zorggroep"],
    ["UMC Utrecht", "UMCU"],
    ["Universitair Medisch Centrum Groningen", "UMCG"],
    ["Van Weel-Bethesda"],
    ["VieCuri Medisch Centrum"],
    ["Wilhelmina", "WZA"],
    ["Zaans Medisch Centrum", "ZMC"],
    ["Amstelland"],
    ["Gelderse Vallei", "ZGV"],
    ["Groep Twente", "ZGT"],
    ["Rivierenland"],
    ["ZorgSaam"],
    ["Zuyderland Medisch Centrum"],
    ["Gemini"],
    [
        "Antoni van Leeuwenhoek",
        "A. van Leeuwenhoek",
        "NKI-A. v. Leeuwenhoek",
        "A. v. Leeuwenhoek",
        "AVL",
        "AvL",
        "NKI",
    ],
    ["PAMM Eindhoven", "PAMM"],
    ["Symbiant"],
]

# Parallel list: each inner list = locations for the corresponding hospital
# Index i in HOSPITAL_CITY_POOL matches index i in HOSPITAL_NAME_POOL.
HOSPITAL_CITY_POOL = [
    ["Goes", "Vlissingen", "Zierikzee"],  # Admiraal de Ruijter
    ["Dordrecht", "Zwijndrecht", "Sliedrecht"],  # Albert Schweitzer
    ["Leiden"],  # Alrijne
    ["Breda"],  # Amphia
    ["Amsterdam", "Adam", "A'dam"],  # AUMC-AMC
    ["Amsterdam", "Adam", "A'dam"],  # AUMC-VUmc
    ["Geldrop"],  # Anna Zorggroep
    ["Sneek"],  # Antonius
    ["Uden"],  # Bernhoven
    ["Amsterdam", "Adam", "A'dam"],  # BovenIJ
    ["Roosendaal", "Bergen op Zoom"],  # Bravis
    ["Nijmegen"],  # Canisius-Wilhelmina
    ["Eindhoven"],  # Catharina
    ["Deventer"],  # Deventer
    ["Utrecht", "Zeist", "Doorn"],  # Diakonessenhuis
    ["Purmerend", "Hoorn"],  # Dijklander
    ["Tilburg", "Waalwijk"],  # ETZ
    ["Helmond", "Deurne"],  # Elkerliek
    ["Rotterdam"],  # Erasmus MC
    ["Almere"],  # Flevo
    ["Rotterdam", "Schiedam"],  # Franciscus
    ["Apeldoorn", "Zutphen"],  # Gelre
    ["Gouda"],  # Groene Hart
    ["Den Haag"],  # Haga
    ["Zoetermeer"],  # Haga Zoetermeer
    ["Den Haag"],  # HMC
    ["Capelle aan den IJssel"],  # IJsselland
    ["Rotterdam"],  # Ikazia
    ["Zwolle", "Meppel"],  # Isala
    ["'s-Hertogenbosch", "Den Bosch"],  # Jeroen Bosch
    ["Roermond"],  # Laurentius
    ["Leiden"],  # LUMC
    ["Rotterdam"],  # Maasstad
    ["Maastricht"],  # MUMC
    ["Beugen"],  # Maasziekenhuis Pantein
    ["Groningen"],  # Martini
    ["Eindhoven", "Veldhoven"],  # Máxima
    ["Amersfoort", "Baarn", "Barneveld", "Nijkerk", "Leusden"],  # Meander
    ["Leeuwarden", "Harlingen"],  # MCL
    ["Enschede"],  # MST
    ["Drachten"],  # Nij Smellinghe
    ["Alkmaar", "Den Helder"],  # Noordwest
    ["Amsterdam", "Adam", "A'dam"],  # OLVG
    ["Scheemda"],  # Ommelander
    ["Nijmegen"],  # Radboud
    ["Delft"],  # Reinier de Graaf
    ["Arnhem", "Elst", "Zevenaar"],  # Rijnstate
    ["Gorinchem"],  # Rivas/Beatrix
    ["Beverwijk"],  # Rode Kruis
    ["Hardenberg"],  # Saxenburgh
    ["Woerden"],  # Sint Antonius (Woerden)
    ["Doetinchem"],  # Slingeland
    ["Haarlem", "Hoofddorp", "Heemstede", "H'lem"],  # Spaarne
    ["Spijkenisse"],  # Spijkenisse MC
    ["Harderwijk", "Lelystad", "Dronten"],  # St Jansdal
    ["Nieuwegein", "Utrecht", "Houten", "De Meern", "Sneek"],  # St. Antonius
    ["Weert"],  # St. Jans Gasthuis
    ["Winterswijk"],  # SKB
    ["Blaricum", "Hilversum"],  # Tergooi
    ["Heerenveen"],  # Tjongerschans
    ["Hoogeveen", "Stadskanaal", "Emmen"],  # Treant
    ["Utrecht"],  # UMCU
    ["Groningen"],  # UMCG
    ["Dirksland"],  # Van Weel-Bethesda
    ["Venlo", "Venray"],  # VieCuri
    ["Assen"],  # Wilhelmina (WZA)
    ["Zaandam"],  # Zaans MC
    ["Amstelveen"],  # Amstelland
    ["Ede"],  # Gelderse Vallei
    ["Almelo", "Hengelo"],  # ZGT
    ["Tiel"],  # Rivierenland
    ["Terneuzen"],  # ZorgSaam
    ["Heerlen", "Sittard-Geleen"],  # Zuyderland
    ["Den Helder"],  # Gemini
    ["Amsterdam"],  # Antoni v. Leeuwenhoek
    ["Eindhoven"],  # PAMM
    ["Zaandam", "Hoorn", "Alkmaar"],  # Symbiant
]
