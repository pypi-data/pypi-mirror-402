from __future__ import annotations

from dataclasses import dataclass, field

__NAMESPACE__ = "http://xoev.de/schemata/code/1_0"


@dataclass(kw_only=True)
class Code:
    """
    Der XÖV-Datentyp Code ermöglicht die Übermittlung von Werten, so
    genannter Codes, aus vordefinierten Codelisten.

    Eine Codeliste ist eine Liste von Codes und der Beschreibung ihrer
    jeweiligen Bedeutung. Eine entscheidende Eigenschaft des Datentyps ist
    die Möglichkeit auf differenzierte Weise Bezug zu Codelisten zu nehmen
    (Code-Typ 1 bis 4). In jedem Fall erlauben die übermittelten Daten eine
    eindeutige Identifizierung der zugrundeliegenden Codeliste.

    :ivar code: In diesem XML-Element wird der Code einer Codeliste
        übermittelt.
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri: Mit diesem XML-Attribut wird die Kennung der
        Codeliste übermittelt, in deren Kontext der jeweilige Code zu
        interpretieren ist. Die Kennung identifiziert die Codeliste,
        nicht jedoch deren Version eindeutig. Wird bereits im Rahmen des
        XÖV-Standards eine Kennung vorgegeben (es handelt sich in diesem
        Fall um einen Code-Typ 1, 2 oder 3) darf auf eine nochmalige
        Angabe der Kennung bei der Übermittlung eines Codes verzichtet
        werden. Aus diesem Grund ist das XML-Attribut listURI zunächst
        als optional deklariert.
    :ivar list_version_id: Die konkrete Version der zu nutzenden
        Codeliste wird mit diesem XML-Attribut übertragen. Analog zum
        listURI ist die Bestimmung der Version einer Codeliste bei der
        Übertragung eines Codes zwingend. Die Version kann jedoch
        ebenfalls bereits im XÖV-Standard festgelegt werden (es handelt
        sich in diesem Fall um einen Code-Typ 1 oder 2).
    """

    code: str = field(
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        }
    )
    name: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )
    list_uri: None | str = field(
        default=None,
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: None | str = field(
        default=None,
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )
