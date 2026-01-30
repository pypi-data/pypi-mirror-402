from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from xjustiz.model_gen.xoev_code import Code

__NAMESPACE__ = "http://www.xjustiz.de"


@dataclass(kw_only=True)
class CodeKlaverAnspruchsartTyp3(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.KLAVER.Anspruchsart.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:klaver.anspruchsart",
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
class CodeKlaverAntragTyp3(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.KLAVER.Antrag.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:klaver.antrag",
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
class CodeKlaverFgrAnspruchshoeheTyp3(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.KLAVER.FGR.Anspruchshoehe.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:klaver.fgr.anspruchshoehe",
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
class CodeKlaverKfvAnlassTyp3(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.KLAVER.KFV.Anlass.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:klaver.anlass",
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
class CodeKlaverKfvKostentatbestandTyp3(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.KLAVER.KFV.Kostentatbestand.Typ3"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:klaver.kfv.kostentatbestand",
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
