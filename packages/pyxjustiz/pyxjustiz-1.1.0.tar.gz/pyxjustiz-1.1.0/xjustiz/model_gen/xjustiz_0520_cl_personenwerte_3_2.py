from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from xjustiz.model_gen.xoev_code import Code

__NAMESPACE__ = "http://www.xjustiz.de"


@dataclass(kw_only=True)
class CodeStrafFahrerlaubnisartTyp3(Code):
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
        name = "Code.STRAF.Fahrerlaubnisart.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:straf.fahrerlaubnisart",
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
class CodeStrafFahrzeugantriebTyp3(Code):
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
        name = "Code.STRAF.Fahrzeugantrieb.Typ3"

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
class CodeStrafFahrzeugartTyp3(Code):
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
        name = "Code.STRAF.Fahrzeugart.Typ3"

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
class CodeStrafFuehrerscheinklasseTyp3(Code):
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
        name = "Code.STRAF.Fuehrerscheinklasse.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:straf.fuehrerscheinklasse",
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
class CodeStrafPersonenbezugTyp3(Code):
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
        name = "Code.STRAF.Personenbezug.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:straf.personenbezug",
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
class CodeStrafStrafverfolgungshindernisTyp3(Code):
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
        name = "Code.STRAF.Strafverfolgungshindernis.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:straf.strafverfolgungshindernis",
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
