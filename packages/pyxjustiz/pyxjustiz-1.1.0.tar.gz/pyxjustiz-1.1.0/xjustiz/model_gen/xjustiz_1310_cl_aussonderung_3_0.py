from __future__ import annotations

from dataclasses import dataclass, field

from xjustiz.model_gen.xoev_code import Code

__NAMESPACE__ = "http://www.xjustiz.de"


@dataclass(kw_only=True)
class CodeAussAussonderungsartTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.
    """

    class Meta:
        name = "Code.AUSS.Aussonderungsart.Typ3"

    name: str = field(
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        }
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xdomea:codeliste:aussonderungsart",
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
class CodeAussBewertungsvorschlagTyp3(Code):
    """
    Die Werte einer Codeliste vom Code-Typ 3 können im XRepository
    eingesehen werden.

    Nähere Details sind im Kapitel "Codelisten vom Code-Typ 3" beschrieben.
    """

    class Meta:
        name = "Code.AUSS.Bewertungsvorschlag.Typ3"

    name: str = field(
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        }
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xdomea:codeliste:bewertungsvorschlag",
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
