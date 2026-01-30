from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

from xsdata.models.datatype import XmlDate

from xjustiz.model_gen.xjustiz_0000_grunddatensatz_3_6 import (
    TypeGdsGrunddaten,
    TypeGdsNachrichtenkopf,
    TypeGdsRefRollennummer,
    TypeGdsSchriftgutobjekte,
    TypeGdsXdomeaZeitraumType,
)
from xjustiz.model_gen.xjustiz_0020_cl_gerichte_3_3 import CodeGdsGerichteTyp3
from xjustiz.model_gen.xjustiz_0240_cl_versorgungsauskunft_3_0 import (
    CodeVagAusgleich,
    CodeVagBezugsgroesse,
    CodeVagFehler,
    CodeVagLeistungsform,
    CodeVagSachstandsmitteilungKurzmitteilungVersorgungstraegerZuGericht,
    CodeVagTeilungsart,
    CodeVagTeilungsartEntscheidung,
    CodeVagVersorgungsart,
)

__NAMESPACE__ = "http://www.xjustiz.de"


class TypeVagFamilieFamilienart(Enum):
    EHEPAAR = "Ehepaar"
    LEBENSPARTNER = "Lebenspartner"


@dataclass(kw_only=True)
class TypeVagKurzmitteilung:
    """
    :ivar anfrage_id: Referenz auf Auskunftsersuchen des Gerichts
    :ivar auskunft_id: Referenz auf Auskunft des Versorgungsträgers
    :ivar ordnungskriterium: Hier ist das Ordnungskriterium des
        Versorgungsträgers anzugeben. Im Falle der Rentenversicherung
        soll die Versicherungsnummer angegeben werden (z.B.
        69010160H519). Ist das Ordnungskriterium nicht bekannt, wird das
        Element ohne Inhalt übermittelt.
    """

    class Meta:
        name = "Type.VAG.Kurzmitteilung"

    anfrage_id: str = field(
        metadata={
            "name": "anfrage.ID",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )
    auskunft_id: None | str = field(
        default=None,
        metadata={
            "name": "auskunft.ID",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        },
    )
    ordnungskriterium: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )


@dataclass(kw_only=True)
class TypeVagRechtskraftmitteilung:
    """
    :ivar mitteilung_id:
    :ivar entscheidung_id: Referenz auf Entscheidung des Gerichts
    :ivar anfrage_id: Referenz auf Anfrage des Gerichts
    :ivar entscheidungsdatum: Entscheidungsdatum ist das Datum der
        Entscheidung.
    :ivar zum_anrecht: Anrechtsbezogene Daten.
    """

    class Meta:
        name = "Type.VAG.Rechtskraftmitteilung"

    mitteilung_id: str = field(
        metadata={
            "name": "mitteilung.ID",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )
    entscheidung_id: str = field(
        metadata={
            "name": "entscheidung.ID",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )
    anfrage_id: None | str = field(
        default=None,
        metadata={
            "name": "anfrage.ID",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        },
    )
    entscheidungsdatum: None | XmlDate = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    zum_anrecht: list[TypeVagRechtskraftmitteilung.ZumAnrecht] = field(
        default_factory=list,
        metadata={
            "name": "zumAnrecht",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )

    @dataclass(kw_only=True)
    class ZumAnrecht:
        """
        :ivar anrecht_id: Referenz auf das Anrecht, das ausgeglichen
            wird. Dies ist grundsätzlich die Anrechts-ID aus der
            Auskunft des Versorgungsträgers. Sofern eine Entscheidung
            ohne vorherige Auskunft erteilt wurde, ist die vom Gericht
            in der Entscheidung vergebene Anrechts-ID einzutragen.
        :ivar rechtskraftdatum: Rechtskraftdatum ist das Datum der
            Rechtskraft.
        :ivar ordnungskriterium: Hier ist das Ordnungskriterium des
            Versorgungsträgers anzugeben. Im Falle der
            Rentenversicherung soll die Versicherungsnummer angegeben
            werden (z.B. 69010160H519). Ist das Ordnungskriterium nicht
            bekannt, wird das Element ohne Inhalt übermittelt.
        """

        anrecht_id: str = field(
            metadata={
                "name": "anrecht.ID",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            }
        )
        rechtskraftdatum: XmlDate = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        ordnungskriterium: str = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            }
        )


@dataclass(kw_only=True)
class TypeVagEmpfangsbestaetigung:
    """
    :ivar anfrage_id: Referenz auf Auskunftsersuchen des Gerichts
    :ivar auskunft_id: Die Empfangsbestätigung zur Entscheidung muss
        auch die Auskunfts-ID enthalten, weil die Entscheidungs-ID bei
        verschiedenen Versorgungsträgern gleich sein kann (eine
        Entscheidung wird an mehrere Versorgungsträger übermittelt).
    :ivar entscheidung_id: Dies ist in der Regel die ID der
        gerichtlichen Entscheidung im Fachsystem des Gerichts. Da diese
        Entscheidung mit derselben Entscheidungs-ID an verschiedene
        Versorgungsträger übersandt wird, muss die Empfangsbestätigung
        zur Entscheidung die Auskunfts-ID enthalten.
    :ivar versicherungstraeger: Referenz auf den tatsächlich zuständigen
        Versorgungsträger im Grunddatensatz. (Bei Empfangsbestätigung
        der Kontoführer, der die Antwort schickt; beim Prüffall
        derjenige, der prüft.)
    :ivar schluesselnummer_versorgungstraeger:
    """

    class Meta:
        name = "Type.VAG.Empfangsbestaetigung"

    anfrage_id: str = field(
        metadata={
            "name": "anfrage.ID",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )
    auskunft_id: None | str = field(
        default=None,
        metadata={
            "name": "auskunft.ID",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        },
    )
    entscheidung_id: None | str = field(
        default=None,
        metadata={
            "name": "entscheidung.ID",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        },
    )
    versicherungstraeger: TypeGdsRefRollennummer = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    schluesselnummer_versorgungstraeger: None | str = field(
        default=None,
        metadata={
            "name": "schluesselnummer.versorgungstraeger",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        },
    )


@dataclass(kw_only=True)
class TypeVagFamilie:
    """
    :ivar familienart: Ehepaar oder Lebenspartner
    :ivar ehezeit: Im Feld 'beginn' wird der Beginn der Ehezeit
        mitgeteilt. Im Feld 'ende' wird das Ende der Ehezeit mitgeteilt.
    """

    class Meta:
        name = "Type.VAG.Familie"

    familienart: TypeVagFamilieFamilienart = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    ehezeit: TypeGdsXdomeaZeitraumType = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class TypeVagFehler:
    """
    :ivar anfrage_id: Referenz auf Auskunftsersuchen des Gerichts
    :ivar fehler:
    """

    class Meta:
        name = "Type.VAG.Fehler"

    anfrage_id: str = field(
        metadata={
            "name": "anfrage.ID",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )
    fehler: list[TypeVagFehler.Fehler] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "min_occurs": 1,
        },
    )

    @dataclass(kw_only=True)
    class Fehler:
        """
        :ivar fehlercode: Hier kann ein Fehlercode übergeben werden.
            (Hierfür kann nicht das Ereignis im Nachrichtenkopf
            verwendet werden, weil eine Fehlernachricht mehrere
            Fehlermeldungen enthalten kann.) Der Text zum jeweiligen
            Fehlercode findet sich als Dokumentation mit in der
            Codeliste.
        :ivar zusatzinformationen: Dies kann zum Beispiel bei einem
            Validierungsfehler die Meldung vom Parser sein oder bei dem
            Fehler "Sonstiger Fehler." die Fehlerbeschreibung.
        """

        fehlercode: CodeVagFehler = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        zusatzinformationen: None | str = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            },
        )


@dataclass(kw_only=True)
class NachrichtVagKurzmitteilungGerichtZuVersorgungstraeger0250007:
    class Meta:
        name = (
            "nachricht.vag.kurzmitteilung.gerichtZuVersorgungstraeger.0250007"
        )
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    grunddaten: TypeGdsGrunddaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    schriftgutobjekte: None | TypeGdsSchriftgutobjekte = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    fachdaten: TypeVagKurzmitteilung = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class NachrichtVagKurzmitteilungVersorgungstraegerZuGericht0250008:
    class Meta:
        name = (
            "nachricht.vag.kurzmitteilung.versorgungstraegerZuGericht.0250008"
        )
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    grunddaten: TypeGdsGrunddaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    schriftgutobjekte: None | TypeGdsSchriftgutobjekte = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    fachdaten: NachrichtVagKurzmitteilungVersorgungstraegerZuGericht0250008.Fachdaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Fachdaten(TypeVagKurzmitteilung):
        sachstandsmitteilung: list[
            CodeVagSachstandsmitteilungKurzmitteilungVersorgungstraegerZuGericht
        ] = field(
            default_factory=list,
            metadata={
                "type": "Element",
            },
        )


@dataclass(kw_only=True)
class NachrichtVagRechtskraftmitteilung0250009:
    class Meta:
        name = "nachricht.vag.rechtskraftmitteilung.0250009"
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    grunddaten: TypeGdsGrunddaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    schriftgutobjekte: None | TypeGdsSchriftgutobjekte = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    fachdaten: TypeVagRechtskraftmitteilung = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class TypeVagAuskunft:
    """
    :ivar auskunft_id: Die Auskunfts-ID ist das Zuordnungsmerkmal der
        Auskunft beim Versorgungsträger. Diese ist vom Gericht bei allen
        Folgenachrichten mitzuteilen.
    :ivar anfrage_id: Referenz auf das Auskunftsersuchen des Gerichts
        (siehe Element anfrage.ID des Typs Type.VAG.Auskunftsersuchen).
    :ivar familie:
    :ivar versorgungsart:
    :ivar anrecht: Hier sind die Anrechte anzugeben. Ist als Ereignis
        "keine Anrechte" angegeben, ist dieser Block nicht zu
        übermitteln.
    :ivar auskunft_aus_ungeklaertem_konto: Dieses Feld soll den Wert
        "true" haben, wenn es sich um eine Auskunft aus einem unklärten
        Versicherungskonto handelt (ausschließlich als Reaktion auf eine
        entsprechende Kurznachricht vom Gericht).
    """

    class Meta:
        name = "Type.VAG.Auskunft"

    auskunft_id: str = field(
        metadata={
            "name": "auskunft.ID",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )
    anfrage_id: str = field(
        metadata={
            "name": "anfrage.ID",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )
    familie: TypeVagFamilie = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    versorgungsart: CodeVagVersorgungsart = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    anrecht: list[TypeVagAuskunft.Anrecht] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    auskunft_aus_ungeklaertem_konto: None | bool = field(
        default=None,
        metadata={
            "name": "auskunftAusUngeklaertemKonto",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )

    @dataclass(kw_only=True)
    class Anrecht:
        """
        :ivar anrecht_id: Durch die Anrechts-ID wird das auszugleichende
            Anrecht identifiziert.
        :ivar berechnungszeitpunkt: Als Berechnungszeitpunkt ist der vom
            Versorgungsträger festgelegte Stichtag für die Berechnung
            anzugeben. Dies ist nicht das Datum der Erteilung der
            Auskunft. Als frühester Berechnungszeitpunkt kann das Ende
            der Ehezeit angegeben werden.
        :ivar versorgungstraeger: In diesem Feld wird der für dieses
            Anrecht zuständige Versorgungsträger aus den Grunddaten
            referenziert, falls der Auskunftserteilende nicht der
            zuständige Versorgungsträger ist (dabei ist davon
            auszugehen, dass dieser dem Gericht erstmalig mit der
            Auskunft bekannt wird). Beispiel: Ein Dienstleister oder
            Dachverband erteilt die Auskunft/Auskünfte für die
            zuständigen Versorgungsträger.
        :ivar ordnungskriterium: Hier ist das Ordnungskriterium des
            Versorgungsträgers anzugeben. Im Falle der
            Rentenversicherung soll die Versicherungsnummer angegeben
            werden (z.B. 69010160H519). Ist das Ordnungskriterium nicht
            bekannt, wird das Element ohne Inhalt übermittelt.
        :ivar leistungsform:
        :ivar unverfallbarkeit: Zeitpunkt, bis zu dem das
            Arbeits-/Versicherungsverhältnis fortbestehen muss, damit
            Unverfallbarkeit eintritt. null = Unverfallbarkeit ist
            bereits eingetreten [Noch verfallbare Rechte müssen NICHT
            betragsmäßig mitgeteilt werden. Teilweise verfallbare Rechte
            sind Sonderfälle und außerhalb des Datensatzes mitzuteilen
            (Papier!).]
        :ivar endgehaltsbezogenheit: Versorgung ist endgehaltsbezogen?
            (Z.B. Beamtenversorgung)
        :ivar bezugsgroesse: Die Bezugsgröße spezifiziert den
            Ehezeitanteil und Ausgleichswert.
        :ivar andere_bezugsgroesse: wenn in Bezugsgröße "andere" gewählt
        :ivar wert_ehezeitanteil: Entgeltpunkte auf 4 Nachkommastellen,
            Geldbeträge auf zwei Nachstellen.
        :ivar ausgleichswert: [übermittelt wird der "Nettowert", also
            der verbleibende Wert nach Abzug der Teilungskosten]
        :ivar garantiewert: [nur bei fondsgebundenen Versicherungen]
        :ivar teilungskosten_par13_vers_ausgl_g: Betrag in Euro.
            [gefragt ist nach dem Gesamtbetrag für beide Ehegatten.
            Anzugeben ist ein einmaliger Kapitalabzug, sonst Leereingabe
            im Datensatz; die Details ergeben sich aus dem Text der
            Auskunft]
        :ivar korrespondierender_kapitalwert: Betrag in Euro
        :ivar bu_versicherung:
        :ivar teilungsart: Art der Teilung
        :ivar teilungsregelung: Grundlage der internen Teilung
            [Kurzbezeichnung in Textform wie z.B. "Satzung", "Satzung
            vom 23.12.2008" oder "Tarif 3122"; kann vom
            Versorgungsträger frei eingegeben werden]
        :ivar fundstelle_der_teilungsregelung: Fundstelle der Satzung
            oder des Versicherungstarifes, z.B. Link auf eine
            Veröffentlichung im Internet oder Aktenzeichen eines
            Verfahrens beim gleichen Gericht, zu dem der Text bereits
            übermittelt worden ist.
        """

        anrecht_id: str = field(
            metadata={
                "name": "anrecht.ID",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            }
        )
        berechnungszeitpunkt: XmlDate = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        versorgungstraeger: None | TypeGdsRefRollennummer = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        ordnungskriterium: str = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            }
        )
        leistungsform: CodeVagLeistungsform = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        unverfallbarkeit: None | XmlDate = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        endgehaltsbezogenheit: bool = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        bezugsgroesse: CodeVagBezugsgroesse = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        andere_bezugsgroesse: None | str = field(
            default=None,
            metadata={
                "name": "andereBezugsgroesse",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            },
        )
        wert_ehezeitanteil: Decimal = field(
            metadata={
                "name": "wert.ehezeitanteil",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        ausgleichswert: Decimal = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        garantiewert: None | Decimal = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        teilungskosten_par13_vers_ausgl_g: None | Decimal = field(
            default=None,
            metadata={
                "name": "teilungskosten.par13.versAusglG",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        korrespondierender_kapitalwert: None | Decimal = field(
            default=None,
            metadata={
                "name": "korrespondierenderKapitalwert",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "total_digits": 9,
                "fraction_digits": 2,
            },
        )
        bu_versicherung: None | TypeVagAuskunft.Anrecht.BuVersicherung = field(
            default=None,
            metadata={
                "name": "bu.versicherung",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        teilungsart: CodeVagTeilungsart = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        teilungsregelung: None | str = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            },
        )
        fundstelle_der_teilungsregelung: None | str = field(
            default=None,
            metadata={
                "name": "fundstelleDerTeilungsregelung",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            },
        )

        @dataclass(kw_only=True)
        class BuVersicherung:
            """
            :ivar eintritt_waehrend_ehezeit: Ist der Versorgungsfall
                während der Ehezeit eingetreten?
            :ivar aktuelle_monatsrente: aktuelle Höhe einer (bei
                Jahresleistung ggf. umzurechnenden) Monatsrente in Euro
            :ivar erhoehungszeitpunkt: Nächster Erhöhungszeitpunkt der
                Monatsrente
            """

            eintritt_waehrend_ehezeit: bool = field(
                metadata={
                    "name": "eintrittWaehrendEhezeit",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            aktuelle_monatsrente: Decimal = field(
                metadata={
                    "name": "aktuelleMonatsrente",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            erhoehungszeitpunkt: str = field(
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                }
            )


@dataclass(kw_only=True)
class TypeVagAuskunftsersuchen:
    """
    :ivar anfrage_id: Die Anfrage-ID ist die Grundlage zur
        Identifikation des Vorgangs. Sie wird durch das Gericht gebildet
        und ist in allen Nachrichten zum gleichen Vorgang zu verwenden.
    :ivar datum_des_auskunftsersuchens: Das Datum wird vom Gericht
        erstellt.
    :ivar familie:
    :ivar versicherter: Referenz auf den Beteiligten im Grunddatensatz,
        für den die Auskunft benötigt wird.
    :ivar anderer_ehegatte: Referenz auf den anderen Ehegatten
    :ivar empfaenger_des_auskunftsersuchens: Referenz auf den
        Beteiligten im Grunddatensatz, an den das Auskunftsersuchen
        übermittelt wird (Versorgungsträger, Arbeitgeber).
    :ivar frist: In diesem Feld ist die Anzahl der Wochen als Frist für
        die Erteilung der Auskunft anzugeben.
    :ivar betriebsnummer: Bei der Betriebsnummer (BBNR) handelt es sich
        um eine achtstellige numerische Kennzahl, die zentral durch die
        Bundesagentur für Arbeit vergeben wird. Sofern für ein Gericht
        mehrere Betriebsnummern existieren, ist hier die BBNR für das
        Gericht und nicht der Personalstelle anzugeben. Die
        Betriebsnummer darf maximal 15 Zeichen umfassen.
    :ivar ausschlusszeitraum: Hier werden Zeiträume während der Ehe
        angegeben, die bei der Berechnung des Ehezeitanteils nicht
        berücksichtigt werden sollen.
    :ivar auskunft_mit_ergaenzenden_anlagen: false = Kurzauskunft
        (Standardfall); true = Auskunft mit allen Berechnungsanlagen
    """

    class Meta:
        name = "Type.VAG.Auskunftsersuchen"

    anfrage_id: str = field(
        metadata={
            "name": "anfrage.ID",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )
    datum_des_auskunftsersuchens: XmlDate = field(
        metadata={
            "name": "datumDesAuskunftsersuchens",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    familie: TypeVagFamilie = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    versicherter: TypeGdsRefRollennummer = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    anderer_ehegatte: TypeGdsRefRollennummer = field(
        metadata={
            "name": "andererEhegatte",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    empfaenger_des_auskunftsersuchens: TypeGdsRefRollennummer = field(
        metadata={
            "name": "empfaengerDesAuskunftsersuchens",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    frist: int = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    betriebsnummer: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "min_length": 1,
            "max_length": 15,
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )
    ausschlusszeitraum: list[TypeGdsXdomeaZeitraumType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    auskunft_mit_ergaenzenden_anlagen: None | bool = field(
        default=None,
        metadata={
            "name": "auskunftMitErgaenzendenAnlagen",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )


@dataclass(kw_only=True)
class TypeVagGerichtlicheEntscheidung:
    """
    :ivar entscheidung_id: Dies ist in der Regel die ID der
        gerichtlichen Entscheidung im Fachsystem des Gerichts. Die
        Rechtskraftmitteilung verweist auf diese Entscheidungs-ID. Da
        eine Entscheidung mit derselben Entscheidungs-ID an verschiedene
        Versorgungsträger übersandt wird, muss die Empfangsbestätigung
        zur Entscheidung die Auskunfts-ID enthalten.
    :ivar entscheidung_id_erstinstanz: Dies ist in der Regel die ID der
        gerichtlichen Entscheidung im Fachsystem des Gerichts. Da diese
        Entscheidung mit derselben Entscheidungs-ID an verschiedene
        Versorgungsträger übersandt wird, muss die Empfangsbestätigung
        zur Entscheidung die Auskunfts-ID enthalten.
    :ivar auskunft_id: Referenz auf die Auskunft des Versorgungsträgers.
        Muss angegeben werden, da die Empfangsbestätigung diese mit
        zurücksendet (vgl. auch Kommentar zur Entscheidungs-ID). Wenn
        von dem Versorgungsträger, der Empfänger der Nachricht ist,
        keine Auskunft zu der betreffenden Person erteilt wurde, muss
        das Gericht eine Auskunfts-ID zur Unterscheidung generieren.
    :ivar entscheidungsdatum:
    :ivar datum_antrag_abaenderung: Nur bei Abänderungsentscheidung.
        [Von der gesetzliche Rentenversicherung wegen §§ 76, 187 SGB VI
        gefordert.]
    :ivar datum_antrag_isolierte_erstentscheidung: Nur bei isolierter
        Erstentscheidung [Von der gesetzliche Rentenversicherung wegen
        §§ 76, 187 SGB VI gefordert.]
    :ivar datum_wiederaufnahme: Nur bei Entscheidung nach Wiederaufnahme
        des Verfahrens [Von der gesetzliche Rentenversicherung wegen §§
        76, 187 SGB VI gefordert.]
    :ivar datum_urspruengliche_entscheidung: Urspruenglich bedeutet
        abgeändert (bei rechtskräftigen oder auch nicht rechtskräftigen
        Entscheidungen) oder berichtigt
    :ivar datum_parteienvereinbarung:
    :ivar gericht_urspruengliche_entscheidung: Urspruenglich bedeutet
        abgeändert (bei rechtskräftigen oder auch nicht rechtskräftigen
        Entscheidungen) oder berichtigt. Hier ist die Gerichtskennzahl
        anzugeben.
    :ivar aktenzeichen_urspruengliche_entscheidung: Urspruenglich
        bedeutet abgeändert (bei rechtskräftigen oder auch nicht
        rechtskräftigen Entscheidungen) oder berichtigt.
    :ivar entscheidung_id_urspruengliche_entscheidung: Urspruenglich
        bedeutet abgeändert (bei rechtskräftigen oder auch nicht
        rechtskräftigen Entscheidungen) oder berichtigt.
    :ivar familie:
    :ivar versicherter: Referenz auf den Beteiligten im Grunddatensatz,
        für den die Auskunft benötigt wird.
    :ivar anderer_ehegatte: Referenz auf den anderen Ehegatten
    :ivar ist_teilentscheidung: Wird grundsätzlich mit false beschickt.
        Derzeit erfolgt keine technische Umsetzung in den Fachverfahren.
    :ivar ausgleich:
    :ivar zum_anrecht:
    """

    class Meta:
        name = "Type.VAG.GerichtlicheEntscheidung"

    entscheidung_id: str = field(
        metadata={
            "name": "entscheidung.ID",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )
    entscheidung_id_erstinstanz: None | str = field(
        default=None,
        metadata={
            "name": "entscheidung.ID.erstinstanz",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        },
    )
    auskunft_id: str = field(
        metadata={
            "name": "auskunft.ID",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )
    entscheidungsdatum: XmlDate = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    datum_antrag_abaenderung: None | XmlDate = field(
        default=None,
        metadata={
            "name": "datum.antrag.abaenderung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    datum_antrag_isolierte_erstentscheidung: None | XmlDate = field(
        default=None,
        metadata={
            "name": "datum.antrag.isolierteErstentscheidung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    datum_wiederaufnahme: None | XmlDate = field(
        default=None,
        metadata={
            "name": "datum.wiederaufnahme",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    datum_urspruengliche_entscheidung: None | XmlDate = field(
        default=None,
        metadata={
            "name": "datum.urspruenglicheEntscheidung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    datum_parteienvereinbarung: None | XmlDate = field(
        default=None,
        metadata={
            "name": "datum.parteienvereinbarung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    gericht_urspruengliche_entscheidung: None | CodeGdsGerichteTyp3 = field(
        default=None,
        metadata={
            "name": "gericht.urspruenglicheEntscheidung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    aktenzeichen_urspruengliche_entscheidung: None | str = field(
        default=None,
        metadata={
            "name": "aktenzeichen.urspruenglicheEntscheidung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        },
    )
    entscheidung_id_urspruengliche_entscheidung: None | str = field(
        default=None,
        metadata={
            "name": "entscheidung.ID.urspruenglicheEntscheidung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        },
    )
    familie: TypeVagFamilie = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    versicherter: TypeGdsRefRollennummer = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    anderer_ehegatte: TypeGdsRefRollennummer = field(
        metadata={
            "name": "andererEhegatte",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    ist_teilentscheidung: bool = field(
        init=False,
        default=False,
        metadata={
            "name": "istTeilentscheidung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        },
    )
    ausgleich: CodeVagAusgleich = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    zum_anrecht: list[TypeVagGerichtlicheEntscheidung.ZumAnrecht] = field(
        default_factory=list,
        metadata={
            "name": "zumAnrecht",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )

    @dataclass(kw_only=True)
    class ZumAnrecht:
        """
        :ivar anrecht_id: Referenz auf das Anrecht, das ausgeglichen
            wird. Diese muss immer übermittelt werden, da die
            Rechtskraft unter Bezug auf diese Anrechts-ID mitgeteilt
            wird. Dabei kann es sein, dass das betreffende Anrecht nicht
            von demselben Versorgungsträger übermittelt wurde, der
            Empfänger dieses Entscheidungsdatensatzes ist. Der
            Versorgungsträger muss also ggf. intern zusätzlich zur
            Anrechts-ID auch den jeweiligen Versorgungsträger mit
            abspeichern, da sonst die Anrechts-ID evtl. nicht eindeutig
            ist. Ggf. kann der Versorgungsträger auch an der Teilungsart
            die eigenen von fremden Anrechten unterscheiden.
        :ivar ordnungskriterium: Hier ist das Ordnungskriterium des
            Versorgungsträgers anzugeben. Im Falle der
            Rentenversicherung soll die Versicherungsnummer angegeben
            werden (z.B. 69010160H519). Ist das Ordnungskriterium nicht
            bekannt, wird das Element ohne Inhalt übermittelt.
        :ivar ausgleichswert: In diesem Feld ist der auszugleichende
            Wert in Abhängigkeit von der Bezugsgröße vorzugeben.
        :ivar bezugsgroesse: Die Bezugsgröße spezifiziert den
            Ehezeitanteil und Ausgleichswert.
        :ivar andere_bezugsgroesse: Für Sonstiges
        :ivar mindestkapitalbetrag: Wird neben der Anordnung über die
            Begründung von Fondsanteilen vom Familiengericht zusätzlich
            ein Mindestkapitalbetrag festgelegt, ist dieser in diesem
            Feld in Euro vorzugeben.
        :ivar teilungsart:
        :ivar verzinsung:
        :ivar tarif: Bezeichnung des Tarifes etc. des
            Zielversorgungsträgers
        :ivar ausgleichspflichtiger: Referenz auf die Beteiligtendaten
            des Ausgleichspflichtigen
        :ivar ausgleichsberechtigter: Referenz auf die Beteiligtendaten
            des Ausgleichsberechtigen
        :ivar zielversorgungstraeger_ausgleichsberechtigter: Referenz
            auf die Beteiligtendaten des Versorgungsträgers des
            Ausgleichsberechtigten bei externer Teilung.
        :ivar versorgungstraeger_ausgleichpflichtiger: Referenz auf die
            Beteiligtendaten des Versorgungsträgers des
            Ausgleichspflichtigen bei externer Teilung.
        :ivar internationale_wertpapierkennnummer: "International
            Securities Identification Number" (ISIN) gemäß Norm ISO 6166
            (zwölfstellige Buchstaben-Zahlen-Kombination)
        """

        anrecht_id: str = field(
            metadata={
                "name": "anrecht.ID",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            }
        )
        ordnungskriterium: str = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            }
        )
        ausgleichswert: Decimal = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        bezugsgroesse: CodeVagBezugsgroesse = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        andere_bezugsgroesse: None | str = field(
            default=None,
            metadata={
                "name": "andereBezugsgroesse",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            },
        )
        mindestkapitalbetrag: None | Decimal = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        teilungsart: CodeVagTeilungsartEntscheidung = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        verzinsung: list[
            TypeVagGerichtlicheEntscheidung.ZumAnrecht.Verzinsung
        ] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        tarif: None | str = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            },
        )
        ausgleichspflichtiger: TypeGdsRefRollennummer = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        ausgleichsberechtigter: TypeGdsRefRollennummer = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        zielversorgungstraeger_ausgleichsberechtigter: (
            None | TypeGdsRefRollennummer
        ) = field(
            default=None,
            metadata={
                "name": "zielversorgungstraeger.ausgleichsberechtigter",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        versorgungstraeger_ausgleichpflichtiger: (
            None | TypeGdsRefRollennummer
        ) = field(
            default=None,
            metadata={
                "name": "versorgungstraeger.ausgleichpflichtiger",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        internationale_wertpapierkennnummer: None | str = field(
            default=None,
            metadata={
                "name": "internationaleWertpapierkennnummer",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "pattern": r"[a-z|A-Z]{2}[a-z|A-Z|0-9]{9}\d",
            },
        )

        @dataclass(kw_only=True)
        class Verzinsung:
            """
            :ivar auswahl_zinssatz:
            :ivar kapitalbetrag: Hier wird ein Betrag für die
                Zinsberechnung eingegeben, wenn dieser abweichend vom
                Ausgleichsbetrag ist.
            :ivar auswahl_zinsbeginn:
            :ivar auswahl_zinsende:
            """

            auswahl_zinssatz: TypeVagGerichtlicheEntscheidung.ZumAnrecht.Verzinsung.AuswahlZinssatz = field(
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            kapitalbetrag: None | Decimal = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "total_digits": 9,
                    "fraction_digits": 2,
                },
            )
            auswahl_zinsbeginn: TypeVagGerichtlicheEntscheidung.ZumAnrecht.Verzinsung.AuswahlZinsbeginn = field(
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            auswahl_zinsende: TypeVagGerichtlicheEntscheidung.ZumAnrecht.Verzinsung.AuswahlZinsende = field(
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )

            @dataclass(kw_only=True)
            class AuswahlZinssatz:
                """
                :ivar zinssatz_in_prozent: Zinsatz in %
                :ivar prozent_ueber_basiszinssatz: % über Basiszinssatz
                """

                zinssatz_in_prozent: None | Decimal = field(
                    default=None,
                    metadata={
                        "name": "zinssatzInProzent",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "total_digits": 4,
                        "fraction_digits": 2,
                    },
                )
                prozent_ueber_basiszinssatz: None | Decimal = field(
                    default=None,
                    metadata={
                        "name": "prozentUeberBasiszinssatz",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "total_digits": 4,
                        "fraction_digits": 2,
                    },
                )

            @dataclass(kw_only=True)
            class AuswahlZinsbeginn:
                datum: None | XmlDate = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                    },
                )
                sonstiger_zeitpunkt: None | str = field(
                    default=None,
                    metadata={
                        "name": "sonstigerZeitpunkt",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )

            @dataclass(kw_only=True)
            class AuswahlZinsende:
                """
                :ivar zinsende_rechtskraft: Das Datum des Zinsendes ist
                    das Datum der Rechtskraft.
                :ivar bis_zum:
                """

                zinsende_rechtskraft: None | bool = field(
                    default=None,
                    metadata={
                        "name": "zinsende.rechtskraft",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                    },
                )
                bis_zum: None | XmlDate = field(
                    default=None,
                    metadata={
                        "name": "bisZum",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                    },
                )


@dataclass(kw_only=True)
class NachrichtVagEmpfangsbestaetigung0250003:
    class Meta:
        name = "nachricht.vag.empfangsbestaetigung.0250003"
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    grunddaten: TypeGdsGrunddaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    schriftgutobjekte: None | TypeGdsSchriftgutobjekte = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    fachdaten: TypeVagEmpfangsbestaetigung = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class NachrichtVagFehlerGerichtZuVersorgungstraeger0250004:
    class Meta:
        name = "nachricht.vag.fehler.gerichtZuVersorgungstraeger.0250004"
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    grunddaten: TypeGdsGrunddaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    schriftgutobjekte: None | TypeGdsSchriftgutobjekte = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    fachdaten: TypeVagFehler = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class NachrichtVagFehlerVersorgungstraegerZuGericht0250005:
    class Meta:
        name = "nachricht.vag.fehler.versorgungstraegerZuGericht.0250005"
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    grunddaten: TypeGdsGrunddaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    schriftgutobjekte: None | TypeGdsSchriftgutobjekte = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    fachdaten: TypeVagFehler = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class NachrichtVagAuskunft0250001:
    class Meta:
        name = "nachricht.vag.auskunft.0250001"
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    grunddaten: TypeGdsGrunddaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    schriftgutobjekte: None | TypeGdsSchriftgutobjekte = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    fachdaten: TypeVagAuskunft = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class NachrichtVagAuskunftsersuchen0250002:
    class Meta:
        name = "nachricht.vag.auskunftsersuchen.0250002"
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    grunddaten: TypeGdsGrunddaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    schriftgutobjekte: None | TypeGdsSchriftgutobjekte = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    fachdaten: TypeVagAuskunftsersuchen = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class NachrichtVagGerichtlicheEntscheidung0250006:
    """
    Zustellungsnachweis ist die technische Eingangsbestätigung.

    Wenn beide Ehepartner bei demselben Versorgungsträger sind, werden zwei
    Entscheidungsdatensätze übermittelt.
    """

    class Meta:
        name = "nachricht.vag.gerichtlicheEntscheidung.0250006"
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    grunddaten: TypeGdsGrunddaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    schriftgutobjekte: None | TypeGdsSchriftgutobjekte = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    fachdaten: TypeVagGerichtlicheEntscheidung = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
