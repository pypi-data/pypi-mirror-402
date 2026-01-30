from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from xjustiz.model_gen.xoev_code import Code

__NAMESPACE__ = "http://www.xjustiz.de"


class InsoIriFehlerart(Enum):
    INTERNAL_SERVICE_EXCEPTION = "InternalServiceException"
    NOT_IMPLEMENTED_EXCEPTION = "NotImplementedException"


class InsoIriFehlercode(Enum):
    VALUE_0 = "0"
    VALUE_100 = "100"
    VALUE_101 = "101"
    VALUE_102 = "102"
    VALUE_103 = "103"
    VALUE_500 = "500"
    VALUE_501 = "501"
    VALUE_502 = "502"
    VALUE_503 = "503"
    VALUE_504 = "504"
    VALUE_505 = "505"
    VALUE_506 = "506"
    VALUE_507 = "507"


class InsoIriFeldtyp(Enum):
    AMOUNT = "AMOUNT"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    DATETIME = "DATETIME"
    ID = "ID"
    LIST = "LIST"
    LOV = "LOV"
    NUMBER = "NUMBER"
    PERIOD = "PERIOD"
    TABLE = "TABLE"
    TEXT = "TEXT"
    TIME = "TIME"
    URL = "URL"


class InsoIriStatus(Enum):
    ERROR = "ERROR"
    OK = "OK"
    WARNING = "WARNING"


@dataclass(kw_only=True)
class CodeInsoIriFehlerart(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.INSO.IRI.Fehlerart"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:inso.iri.fehlerart",
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
class CodeInsoIriFehlercode(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.INSO.IRI.Fehlercode"

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
        init=False,
        default="1.0",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeInsoIriFeldtyp(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.INSO.IRI.Feldtyp"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:inso.iri.feldtyp",
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
class CodeInsoIriStatus(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.INSO.IRI.Status"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:inso.iri.status",
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
