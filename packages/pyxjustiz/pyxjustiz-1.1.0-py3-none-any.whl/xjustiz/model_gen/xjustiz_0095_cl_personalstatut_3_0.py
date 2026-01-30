from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from xjustiz.model_gen.xoev_code import Code

__NAMESPACE__ = "http://www.xjustiz.de"


class GdsPersonalstatut(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"
    VALUE_004 = "004"
    VALUE_005 = "005"
    VALUE_006 = "006"


@dataclass(kw_only=True)
class CodeGdsPersonalstatut(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.GDS.Personalstatut"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:gds.personalstatut",
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
