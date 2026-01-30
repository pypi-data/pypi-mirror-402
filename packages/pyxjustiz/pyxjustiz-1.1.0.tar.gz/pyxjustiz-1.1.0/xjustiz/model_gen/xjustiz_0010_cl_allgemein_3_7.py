from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from xjustiz.model_gen.xoev_code import Code

__NAMESPACE__ = "http://www.xjustiz.de"


class GdsAktenreferenzart(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"
    VALUE_004 = "004"
    VALUE_005 = "005"


class GdsAktentyp(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"
    VALUE_004 = "004"
    VALUE_005 = "005"
    VALUE_006 = "006"
    VALUE_007 = "007"
    VALUE_008 = "008"
    VALUE_009 = "009"
    VALUE_010 = "010"
    VALUE_011 = "011"
    VALUE_012 = "012"
    VALUE_013 = "013"
    VALUE_014 = "014"
    VALUE_015 = "015"
    VALUE_016 = "016"
    VALUE_017 = "017"
    VALUE_018 = "018"
    VALUE_019 = "019"
    VALUE_020 = "020"
    VALUE_021 = "021"
    VALUE_022 = "022"
    VALUE_023 = "023"
    VALUE_024 = "024"


class GdsAktenzeichenart(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"
    VALUE_004 = "004"
    VALUE_005 = "005"


class GdsAnschriftstyp(Enum):
    VALUE_002 = "002"
    VALUE_003 = "003"
    VALUE_004 = "004"
    VALUE_005 = "005"
    VALUE_006 = "006"
    VALUE_007 = "007"
    VALUE_008 = "008"
    VALUE_009 = "009"
    VALUE_010 = "010"
    VALUE_011 = "011"
    VALUE_012 = "012"
    VALUE_013 = "013"
    VALUE_014 = "014"
    VALUE_017 = "017"
    VALUE_018 = "018"
    VALUE_019 = "019"
    VALUE_020 = "020"
    VALUE_021 = "021"


class GdsBestandteiltyp(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"
    VALUE_004 = "004"
    VALUE_006 = "006"
    VALUE_010 = "010"
    VALUE_011 = "011"
    VALUE_012 = "012"
    VALUE_013 = "013"


class GdsFamilienstand(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"
    VALUE_004 = "004"
    VALUE_005 = "005"
    VALUE_006 = "006"
    VALUE_007 = "007"
    VALUE_008 = "008"
    VALUE_009 = "009"
    VALUE_010 = "010"


class GdsForderungsteil(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"
    VALUE_004 = "004"
    VALUE_005 = "005"


class GdsGeschlecht(Enum):
    VALUE_0 = "0"
    VALUE_1 = "1"
    VALUE_2 = "2"
    VALUE_3 = "3"
    VALUE_4 = "4"


class GdsIntervall(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"
    VALUE_004 = "004"
    VALUE_005 = "005"
    VALUE_006 = "006"
    VALUE_007 = "007"


class GdsKanzleiform(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"


class GdsLastschrifttyp(Enum):
    FNAL = "FNAL"
    FRST = "FRST"
    OOFF = "OOFF"
    RCUR = "RCUR"


class GdsRvtraeger(Enum):
    VALUE_02 = "02"
    VALUE_09 = "09"
    VALUE_10 = "10"
    VALUE_11 = "11"
    VALUE_12 = "12"
    VALUE_13 = "13"
    VALUE_15 = "15"
    VALUE_16 = "16"
    VALUE_17 = "17"
    VALUE_18 = "18"
    VALUE_21 = "21"
    VALUE_24 = "24"
    VALUE_25 = "25"
    VALUE_28 = "28"
    VALUE_70 = "70"
    VALUE_80 = "80"


class GdsSprachen(Enum):
    VALUE_00 = "00"
    VALUE_01 = "01"
    AA = "aa"
    AB = "ab"
    AE = "ae"
    AF = "af"
    AK = "ak"
    AM = "am"
    AN = "an"
    AR = "ar"
    AS = "as"
    AV = "av"
    AY = "ay"
    AZ = "az"
    BA = "ba"
    BE = "be"
    BG = "bg"
    BH = "bh"
    BI = "bi"
    BM = "bm"
    BN = "bn"
    BO = "bo"
    BR = "br"
    BS = "bs"
    CA = "ca"
    CE = "ce"
    CH = "ch"
    CN = "cn"
    CO = "co"
    CR = "cr"
    CS = "cs"
    CU = "cu"
    CV = "cv"
    CY = "cy"
    DA = "da"
    DE = "de"
    DV = "dv"
    DZ = "dz"
    EE = "ee"
    EL = "el"
    EN = "en"
    EO = "eo"
    ES = "es"
    ET = "et"
    EU = "eu"
    FA = "fa"
    FF = "ff"
    FI = "fi"
    FJ = "fj"
    FO = "fo"
    FR = "fr"
    FY = "fy"
    GA = "ga"
    GD = "gd"
    GL = "gl"
    GN = "gn"
    GU = "gu"
    GV = "gv"
    HA = "ha"
    HE = "he"
    HI = "hi"
    HO = "ho"
    HR = "hr"
    HT = "ht"
    HU = "hu"
    HY = "hy"
    HZ = "hz"
    IA = "ia"
    ID = "id"
    IE = "ie"
    IG = "ig"
    II = "ii"
    IK = "ik"
    IO = "io"
    IS = "is"
    IT = "it"
    IU = "iu"
    JA = "ja"
    JV = "jv"
    KA = "ka"
    KG = "kg"
    KI = "ki"
    KJ = "kj"
    KK = "kk"
    KL = "kl"
    KM = "km"
    KN = "kn"
    KO = "ko"
    KR = "kr"
    KS = "ks"
    KU = "ku"
    KV = "kv"
    KW = "kw"
    KY = "ky"
    LA = "la"
    LB = "lb"
    LG = "lg"
    LI = "li"
    LN = "ln"
    LO = "lo"
    LT = "lt"
    LU = "lu"
    LV = "lv"
    MG = "mg"
    MH = "mh"
    MI = "mi"
    MK = "mk"
    ML = "ml"
    MN = "mn"
    MR = "mr"
    MS = "ms"
    MT = "mt"
    MY = "my"
    NA = "na"
    NB = "nb"
    ND = "nd"
    NE = "ne"
    NG = "ng"
    NL = "nl"
    NN = "nn"
    NO = "no"
    NR = "nr"
    NV = "nv"
    NY = "ny"
    OC = "oc"
    OJ = "oj"
    OM = "om"
    OR = "or"
    OS = "os"
    PA = "pa"
    PI = "pi"
    PL = "pl"
    PS = "ps"
    PT = "pt"
    QU = "qu"
    RM = "rm"
    RN = "rn"
    RO = "ro"
    RU = "ru"
    RW = "rw"
    SA = "sa"
    SC = "sc"
    SD = "sd"
    SE = "se"
    SG = "sg"
    SI = "si"
    SK = "sk"
    SL = "sl"
    SM = "sm"
    SN = "sn"
    SO = "so"
    SQ = "sq"
    SR = "sr"
    SS = "ss"
    ST = "st"
    SU = "su"
    SV = "sv"
    SW = "sw"
    TA = "ta"
    TE = "te"
    TG = "tg"
    TH = "th"
    TI = "ti"
    TK = "tk"
    TL = "tl"
    TN = "tn"
    TO = "to"
    TR = "tr"
    TS = "ts"
    TT = "tt"
    TW = "tw"
    TY = "ty"
    UG = "ug"
    UK = "uk"
    UR = "ur"
    UZ = "uz"
    VE = "ve"
    VI = "vi"
    VO = "vo"
    WA = "wa"
    WO = "wo"
    XH = "xh"
    YI = "yi"
    YO = "yo"
    ZA = "za"
    ZH = "zh"
    ZU = "zu"


class GdsTeilaktentyp(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"
    VALUE_004 = "004"
    VALUE_005 = "005"
    VALUE_006 = "006"
    VALUE_007 = "007"
    VALUE_008 = "008"
    VALUE_009 = "009"
    VALUE_010 = "010"
    VALUE_011 = "011"
    VALUE_012 = "012"
    VALUE_013 = "013"
    VALUE_014 = "014"
    VALUE_015 = "015"
    VALUE_016 = "016"
    VALUE_017 = "017"
    VALUE_018 = "018"
    VALUE_019 = "019"
    VALUE_020 = "020"
    VALUE_021 = "021"
    VALUE_022 = "022"
    VALUE_023 = "023"
    VALUE_024 = "024"
    VALUE_025 = "025"
    VALUE_026 = "026"
    VALUE_027 = "027"
    VALUE_028 = "028"
    VALUE_029 = "029"
    VALUE_030 = "030"
    VALUE_031 = "031"
    VALUE_032 = "032"
    VALUE_033 = "033"
    VALUE_034 = "034"
    VALUE_035 = "035"
    VALUE_036 = "036"
    VALUE_037 = "037"
    VALUE_038 = "038"
    VALUE_039 = "039"
    VALUE_040 = "040"
    VALUE_041 = "041"
    VALUE_042 = "042"
    VALUE_043 = "043"


class GdsTerminsart(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"
    VALUE_004 = "004"
    VALUE_005 = "005"
    VALUE_006 = "006"
    VALUE_007 = "007"
    VALUE_008 = "008"
    VALUE_009 = "009"
    VALUE_010 = "010"
    VALUE_011 = "011"
    VALUE_012 = "012"
    VALUE_013 = "013"
    VALUE_014 = "014"
    VALUE_015 = "015"
    VALUE_016 = "016"
    VALUE_017 = "017"
    VALUE_018 = "018"
    VALUE_019 = "019"
    VALUE_020 = "020"
    VALUE_021 = "021"
    VALUE_022 = "022"
    VALUE_023 = "023"
    VALUE_024 = "024"
    VALUE_025 = "025"
    VALUE_026 = "026"
    VALUE_027 = "027"
    VALUE_028 = "028"
    VALUE_029 = "029"
    VALUE_030 = "030"
    VALUE_031 = "031"
    VALUE_032 = "032"
    VALUE_033 = "033"
    VALUE_034 = "034"
    VALUE_035 = "035"
    VALUE_036 = "036"
    VALUE_037 = "037"
    VALUE_038 = "038"


class GdsTerminskategorie(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"


class GdsVerweistyp(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"


class GdsZinsberechnung(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"


class GdsZinstyp(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"


@dataclass(kw_only=True)
class CodeFehlerTyp4(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.Fehler.Typ4"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        metadata={
            "name": "listURI",
            "type": "Attribute",
            "required": True,
        }
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsAstralTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.

    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.ASTRAL.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:straf.astral",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsAktenreferenzart(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Aktenreferenzart"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.aktenreferenzart",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="2.1",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeGdsAktentyp(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Aktentyp"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.aktentyp",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="2.2",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeGdsAktenzeichenart(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Aktenzeichenart"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.aktenzeichenart",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="2.0",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeGdsAnschriftstyp(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Anschriftstyp"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.anschriftstyp",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="3.0",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeGdsAuskunftVollstreckungssachenFehlerTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.

    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Auskunft.Vollstreckungssachen.Fehler.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.auskunft.vollstreckungssachen.fehler",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsAusweisartTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.

    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Ausweisart.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.ausweisart",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsBrisListOfRegistersTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.
    Neben dem Code im Element 'code' ist zusätzlich im zwingend
    nachfolgenden Element 'name' die Bezeichnung der ausländischen
    Registerbehörde anzugeben. Dabei werden die Einträge der Spalte
    'Original-language-name-of-register' genutzt.
    """

    class Meta:
        name = "Code.GDS.BRIS-ListOfRegisters.Typ3"

    name: str = field(
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        }
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.bris-listofregisters",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsBestandteiltyp(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Bestandteiltyp"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.bestandteiltyp",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="2.5",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeGdsBundeslandTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.

    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Bundesland.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:de:bund:destatis:bevoelkerungsstatistik:schluessel:bundesland",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsDatentypTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.

    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Datentyp.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xdomea:codeliste:datentyp",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsDienstbezeichnungTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.

    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Dienstbezeichnung.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.dienstbezeichnung",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsDokumentklasseTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.

    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Dokumentklasse.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.dokumentklasse",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsDokumenttypTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.

    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Dokumenttyp.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.dokumenttyp",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsEntscheidungsartTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.

    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Entscheidungsart.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.entscheidungsart",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsEreignisTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.

    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Ereignis.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.ereignis",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsFachlicherZusammenhangTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.

    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.FachlicherZusammenhang.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.fachlicher-zusammenhang",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsFahrzeugantriebTyp3(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Fahrzeugantrieb.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:straf.fahrzeugantrieb",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsFahrzeugartTyp3(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Fahrzeugart.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:straf.fahrzeugart",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsFamilienstand(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Familienstand"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.familienstand",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="2.0",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeGdsFehlercodesTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.

    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Fehlercodes.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.fehlercodes",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsFinanzbehoerdenTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.

    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Finanzbehoerden.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:ag-it-standards:codeliste:gds.finanzbehoerden",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsForderungsteil(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Forderungsteil"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.forderungsteil",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="1.0",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeGdsGeheimhaltungsgradTyp3(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Geheimhaltungsgrad.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.geheimhaltungsgrad",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsGeschlecht(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Geschlecht"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.geschlecht",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="2.1",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeGdsInsoIriFehlercodeTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.

    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.INSO.IRI.Fehlercode.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:inso.iri.fehlercode",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsIntervall(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Intervall"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.intervall",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="2.0",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeGdsKfzKennzeichenTyp3(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.KFZ.Kennzeichen.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:straf.kfz.kennzeichen",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsKanzleiform(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Kanzleiform"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.kanzleiform",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="2.0",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeGdsLastschrifttyp(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Lastschrifttyp"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.lastschrifttyp",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="1.0",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeGdsOwilTyp3(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.OWIL.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:straf.owil",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsPersonenbezugTyp3(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Personenbezug.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.personenbezug",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsPolizeibehoerdenTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.

    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Polizeibehoerden.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.polizeibehoerden",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsRvtraeger(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.RVTraeger"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.rvtraeger",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="2.0",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeGdsRechtsmittelartTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.

    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Rechtsmittelart.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.rechtsmittelart",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsStrafBzrVerarbeitungsbestaetigungTyp3(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.STRAF.BZR.Verarbeitungsbestaetigung.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.straf.bzr.verarbeitungsbestaetigung",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsSachgebietTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.

    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Sachgebiet.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.sachgebiet",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsSendungsprioritaetTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.

    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Sendungsprioritaet.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.sendungsprioritaet",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsSprachen(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Sprachen"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.sprachen",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="2.1",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeGdsTeilaktentyp(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Teilaktentyp"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.teilaktentyp",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="2.3",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeGdsTerminsart(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Terminsart"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.terminsart",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="2.2",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeGdsTerminskategorie(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Terminskategorie"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.terminskategorie",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="1.0",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeGdsUrkundentypTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.

    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Urkundentyp.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.urkundentyp",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsVagFehlerTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.

    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.VAG.Fehler.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:vag.fehler",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsVertraulichkeitsstufeTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.

    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Vertraulichkeitsstufe.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.vertraulichkeitsstufe",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsVerweistyp(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Verweistyp"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.verweistyp",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="2.0",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeGdsWaehrungTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.

    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Waehrung.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:bund:kba:codeliste:waehrung",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsZinsberechnung(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Zinsberechnung"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.zinsberechnung",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="2.0",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeGdsZinsmethodeTyp3(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Zinsmethode.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.zinsmethode",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class CodeGdsZinstyp(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Zinstyp"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.zinstyp",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="2.0",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )
