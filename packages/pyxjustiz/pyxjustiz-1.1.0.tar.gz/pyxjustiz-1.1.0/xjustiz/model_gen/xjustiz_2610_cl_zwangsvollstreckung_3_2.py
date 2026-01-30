from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from xjustiz.model_gen.xoev_code import Code

__NAMESPACE__ = "http://www.xjustiz.de"


class ZvstrAltersstufenUnterhalt(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"


class ZvstrAnlage(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"
    VALUE_004 = "004"
    VALUE_005 = "005"
    VALUE_006 = "006"
    VALUE_007 = "007"
    VALUE_009 = "009"
    VALUE_010 = "010"
    VALUE_011 = "011"
    VALUE_012 = "012"
    VALUE_013 = "013"
    VALUE_014 = "014"
    VALUE_015 = "015"
    VALUE_016 = "016"
    VALUE_017 = "017"
    VALUE_019 = "019"
    VALUE_020 = "020"
    VALUE_021 = "021"
    VALUE_022 = "022"
    VALUE_023 = "023"
    VALUE_024 = "024"
    VALUE_025 = "025"
    VALUE_026 = "026"
    VALUE_027 = "027"


class ZvstrAntragZustellung(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"


class ZvstrEntscheidungsumfangPfueb(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"


class ZvstrTitelart(Enum):
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


class ZvstrUnterhaltsberechtigter(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"
    VALUE_004 = "004"
    VALUE_005 = "005"


class ZvstrZeitraumUnterhaltsforderung(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"
    VALUE_004 = "004"
    VALUE_005 = "005"


@dataclass(kw_only=True)
class CodeZvstrAltersstufenUnterhalt(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.ZVSTR.Altersstufen.Unterhalt"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:zvstr.altersstufen.unterhalt",
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
class CodeZvstrAnlage(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.ZVSTR.Anlage"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:zvstr.anlage",
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
class CodeZvstrAntragZustellung(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.ZVSTR.Antrag.Zustellung"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:zvstr.antrag.zustellung",
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
class CodeZvstrEntscheidungsumfangPfUeb(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.ZVSTR.Entscheidungsumfang.PfUEB"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:zvstr.entscheidungsumfang.pfueb",
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
class CodeZvstrTitelart(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.ZVSTR.Titelart"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:zvstr.titelart",
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
class CodeZvstrUnterhaltsberechtigter(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.ZVSTR.Unterhaltsberechtigter"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:zvstr.unterhaltsberechtigter",
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
class CodeZvstrZeitraumUnterhaltsforderung(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.ZVSTR.Zeitraum.Unterhaltsforderung"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:zvstr.zeitraum.unterhaltsforderung",
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
class CodeZvstrZinsmethodeTyp3(Code):
    """
    Diese Codeliste verweist auf die im XRepository veröffentlichte
    Codeliste GVZ.Zinsmethode.

    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.ZVSTR.Zinsmethode.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gvz.zinsmethode",
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
