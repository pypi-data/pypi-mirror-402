from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from xjustiz.model_gen.xoev_code import Code

__NAMESPACE__ = "http://www.xjustiz.de"


class FamBetragsart(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"
    VALUE_004 = "004"
    VALUE_005 = "005"


class FamFamilienart(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"
    VALUE_004 = "004"


class FamGegenstandsbezeichnung(Enum):
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
    VALUE_044 = "044"
    VALUE_045 = "045"
    VALUE_046 = "046"
    VALUE_047 = "047"
    VALUE_048 = "048"
    VALUE_049 = "049"
    VALUE_050 = "050"
    VALUE_051 = "051"
    VALUE_052 = "052"
    VALUE_053 = "053"
    VALUE_054 = "054"
    VALUE_055 = "055"
    VALUE_056 = "056"
    VALUE_057 = "057"
    VALUE_058 = "058"
    VALUE_059 = "059"
    VALUE_060 = "060"
    VALUE_061 = "061"
    VALUE_062 = "062"
    VALUE_063 = "063"
    VALUE_064 = "064"
    VALUE_065 = "065"
    VALUE_066 = "066"
    VALUE_067 = "067"
    VALUE_068 = "068"
    VALUE_069 = "069"
    VALUE_070 = "070"
    VALUE_071 = "071"
    VALUE_072 = "072"
    VALUE_073 = "073"
    VALUE_074 = "074"
    VALUE_075 = "075"
    VALUE_076 = "076"
    VALUE_077 = "077"
    VALUE_078 = "078"
    VALUE_079 = "079"
    VALUE_080 = "080"
    VALUE_081 = "081"
    VALUE_082 = "082"
    VALUE_083 = "083"
    VALUE_084 = "084"
    VALUE_085 = "085"
    VALUE_086 = "086"
    VALUE_087 = "087"
    VALUE_088 = "088"
    VALUE_089 = "089"
    VALUE_090 = "090"
    VALUE_091 = "091"
    VALUE_092 = "092"
    VALUE_093 = "093"
    VALUE_094 = "094"
    VALUE_095 = "095"
    VALUE_096 = "096"
    VALUE_097 = "097"
    VALUE_098 = "098"
    VALUE_099 = "099"
    VALUE_100 = "100"
    VALUE_101 = "101"
    VALUE_102 = "102"
    VALUE_103 = "103"
    VALUE_104 = "104"
    VALUE_105 = "105"
    VALUE_106 = "106"
    VALUE_107 = "107"
    VALUE_108 = "108"
    VALUE_109 = "109"
    VALUE_110 = "110"
    VALUE_111 = "111"
    VALUE_112 = "112"
    VALUE_113 = "113"
    VALUE_114 = "114"
    VALUE_115 = "115"
    VALUE_116 = "116"
    VALUE_117 = "117"
    VALUE_118 = "118"
    VALUE_119 = "119"
    VALUE_120 = "120"
    VALUE_121 = "121"
    VALUE_122 = "122"
    VALUE_123 = "123"
    VALUE_124 = "124"
    VALUE_125 = "125"
    VALUE_126 = "126"
    VALUE_127 = "127"
    VALUE_128 = "128"


class FamVermoegenstyp(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"
    VALUE_004 = "004"


@dataclass(kw_only=True)
class CodeFamBetragsart(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.FAM.Betragsart"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:fam.betragsart",
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
class CodeFamFamilienart(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.FAM.Familienart"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:fam.familienart",
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
class CodeFamGegenstandsbezeichnung(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.FAM.Gegenstandsbezeichnung"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:fam.gegenstandsbezeichnung",
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
class CodeFamVermoegenstyp(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.FAM.Vermoegenstyp"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:fam.vermoegenstyp",
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
