from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from xjustiz.model_gen.xoev_code import Code

__NAMESPACE__ = "http://www.xjustiz.de"


class MahnKostenbefreiung(Enum):
    GB = "GB"
    KB = "KB"
    VZ = "VZ"


class MahnWiderspruchsart(Enum):
    GW = "GW"
    TW = "TW"


@dataclass(kw_only=True)
class CodeMahnKostenbefreiung(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.MAHN.Kostenbefreiung"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:mahn.kostenbefreiung",
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
class CodeMahnWiderspruchsart(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.MAHN.Widerspruchsart"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:mahn.widerspruchsart",
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
