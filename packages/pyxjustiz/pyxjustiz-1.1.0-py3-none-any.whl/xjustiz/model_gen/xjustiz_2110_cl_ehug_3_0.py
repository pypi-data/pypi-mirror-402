from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from xjustiz.model_gen.xoev_code import Code

__NAMESPACE__ = "http://www.xjustiz.de"


class EhugEbanzMeldungBfj(Enum):
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


class EhugInfoBfj(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"


class EhugPostZu(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"
    VALUE_004 = "004"
    VALUE_005 = "005"
    VALUE_006 = "006"
    VALUE_007 = "007"
    VALUE_008 = "008"


@dataclass(kw_only=True)
class CodeEhugEbanzMeldungBfj(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.EHUG.Ebanz.Meldung.BFJ"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:ehug.ebanz.meldung.bfj",
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
class CodeEhugInfoBfj(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.EHUG.Info.BFJ"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:ehug.info.bfj",
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
class CodeEhugPostZu(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.EHUG.Post.ZU"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:ehug.post.zu",
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
