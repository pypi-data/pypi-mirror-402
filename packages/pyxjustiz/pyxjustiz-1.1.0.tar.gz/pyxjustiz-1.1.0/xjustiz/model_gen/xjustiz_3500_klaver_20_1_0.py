from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from xsdata.models.datatype import XmlDate, XmlDateTime

from xjustiz.model_gen.xjustiz_0000_grunddatensatz_3_6 import (
    TypeGdsDauer,
    TypeGdsGeldbetrag,
    TypeGdsGrunddaten,
    TypeGdsNachrichtenkopf,
    TypeGdsRefBankverbindung,
    TypeGdsRefRollennummer,
    TypeGdsRefSgo,
    TypeGdsSchriftgutobjekte,
    TypeGdsXdomeaZeitraumType,
    TypeGdsZinsen,
)
from xjustiz.model_gen.xjustiz_0010_cl_allgemein_3_7 import (
    CodeGdsEntscheidungsartTyp3,
)
from xjustiz.model_gen.xjustiz_0020_cl_gerichte_3_3 import CodeGdsGerichteTyp3
from xjustiz.model_gen.xjustiz_3510_cl_klaver_1_0 import (
    CodeKlaverAnspruchsartTyp3,
    CodeKlaverAntragTyp3,
    CodeKlaverFgrAnspruchshoeheTyp3,
    CodeKlaverKfvAnlassTyp3,
    CodeKlaverKfvKostentatbestandTyp3,
)

__NAMESPACE__ = "http://www.xjustiz.de"


@dataclass(kw_only=True)
class TypeKlaverFgrBefoerderung:
    class Meta:
        name = "Type.KLAVER.FGR.Befoerderung"

    zeitpunkt: XmlDateTime = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    auswahl_befoerderungsart: TypeKlaverFgrBefoerderung.AuswahlBefoerderungsart = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class AuswahlBefoerderungsart:
        """
        :ivar flugnummer:
        :ivar sonstige: Wenn die tatsächliche Verbindung nicht von einem
            Motorluftflugzeug mit festen Tragflächen im Sinne des Art. 3
            Abs. 4 Verordnung (EG) Nr. 261/2004 durchgeführt wurde, ist
            hier anzugeben, wie der Transport erfolgte (Bus, Bahn,
            alternative Verkehrsmittel).
        """

        flugnummer: None | str = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            },
        )
        sonstige: None | str = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            },
        )


@dataclass(kw_only=True)
class TypeKlaverFgrBetroffenerFlug:
    """
    :ivar flugnummer: Die Flugnummer des betroffenen Fluges
    :ivar abflug_flughafen: Abflughafen des betroffenen Fluges.
        Anzugeben als IATA Flughafen Code.
    :ivar ankunft_flughafen: Ankunftsflughafen des betroffenen Fluges.
        Anzugeben als IATA Flughafen Code.
    """

    class Meta:
        name = "Type.KLAVER.FGR.BetroffenerFlug"

    flugnummer: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )
    abflug_flughafen: str = field(
        metadata={
            "name": "abflugFlughafen",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )
    ankunft_flughafen: str = field(
        metadata={
            "name": "ankunftFlughafen",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )


@dataclass(kw_only=True)
class TypeKlaverFgrPuenktlichkeit:
    """
    :ivar vorgeschriebene_check_in_zeit: Wenn auf der
        Buchungsbestätigung eine vereinbarte Check-In Zeit steht, ist
        diese hier anzugeben.
    :ivar tatsaechliche_check_in_zeit: Der Zeitpunkt der Ankunft beim
        Check-In Schalter des verspäteten (Teil-)Fluges.
    """

    class Meta:
        name = "Type.KLAVER.FGR.Puenktlichkeit"

    vorgeschriebene_check_in_zeit: None | XmlDateTime = field(
        default=None,
        metadata={
            "name": "vorgeschriebeneCheckInZeit",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    tatsaechliche_check_in_zeit: None | XmlDateTime = field(
        default=None,
        metadata={
            "name": "tatsaechlicheCheckInZeit",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )


@dataclass(kw_only=True)
class TypeKlaverAnspruch:
    """
    :ivar fortlaufende_nummer: Die fortlaufende Nummer wird als
        eindeutige Kennziffer innerhalb dieser XJustiz-Nachricht
        verwendet, um andere Elemente dieser XJustiz-Nachricht mit
        diesem Anspruch zu verknüpfen. Die Nummern dürfen nicht doppelt
        vergeben werden.
    :ivar anspruchssteller: Sofern der Anspruch bei mehreren Klägern nur
        für einen Teil der Kläger geltend gemacht wird, können diese
        Kläger in diesem Element referenziert werden.
    :ivar anspruchsgegner: Sofern der Anspruch bei mehreren Beklagten
        nur gegen einen Teil der Beklagten geltend gemacht wird, können
        diese Beklagten in diesem Element referenziert werden.
    :ivar anspruchsart: In diesem Element wird die Art des Anspruchs
        unter Verwendung einer Codeliste übermittelt.
    :ivar wert_anspruch: In diesem Element wird der Betrag des
        Anspruchs, der mit der Klage geltend gemacht werden soll,
        übermittelt. Bei Klagen auf Handlung/Unterlassung/Duldung,
        Feststellung, Gestaltung und Auskunft ist hier der Wert gemäß
        der einschlägigen Wertvorschriften anzugeben.
    :ivar anspruchsgegenstand: In diesem Element wird der Anspruch näher
        bezeichnet. (z.B. 'Kaufpreis gem. Vertrag vom' oder
        'Schmerzensgeld aus Vorfall vom ...')
    """

    class Meta:
        name = "Type.KLAVER.Anspruch"

    fortlaufende_nummer: None | int = field(
        default=None,
        metadata={
            "name": "fortlaufendeNummer",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    anspruchssteller: list[TypeGdsRefRollennummer] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    anspruchsgegner: list[TypeGdsRefRollennummer] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    anspruchsart: None | CodeKlaverAnspruchsartTyp3 = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    wert_anspruch: None | TypeGdsGeldbetrag = field(
        default=None,
        metadata={
            "name": "wertAnspruch",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    anspruchsgegenstand: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        },
    )


@dataclass(kw_only=True)
class TypeKlaverAusfuehrungen:
    """
    Mit diesem Datentyp können Tatsachen, Ausführungen und eine rechtliche
    Würdigung zum Gerichtsstand (§§ 12 ff.

    ZPO) in Textform übermittelt werden. Zudem können Beweise und Anlagen
    verknüpft werden. Dabei kann ein- und dasselbe Dokument sowohl als
    Beweismittel als auch als (vortragsergänzende) Anlage verknüpft werden.

    :ivar inhalt:
    :ivar ref_beweis_nummer: In diesem Element kann ein Beweis angeboten
        werden. Hierzu wird die Nummer, die im Element 'beweis' für das
        hier einschlägige Beweismittel verwendet wurde, angegeben.
    :ivar ref_glaubhaftmachung_nummer: In diesem Element kann auf ein
        Mittel zur Glaubhaftmachung referenziert werden. Hierzu wird die
        Nummer, die im Element "glaubhaftmachung" für das hier
        einschlägige Mittel zur Glaubhaftmachung verwendet wurde,
        angegeben.
    :ivar parteianhoerung: In diesem Element kann auf eine Partei, die
        informell angehört werden soll, referenziert werden. Hierfür
        wird jeweils auf eine Person, die in den Grunddaten angegeben
        wurde, referenziert.
    :ivar anlage: In diesem Element können (vortragsergänzende) Anlagen,
        die in dem Knoten Schriftgutobjekte aufgeführt sind, mit den
        Ausführungen verknüpft werden.
    """

    class Meta:
        name = "Type.KLAVER.Ausfuehrungen"

    inhalt: None | TypeKlaverAusfuehrungen.Inhalt = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    ref_beweis_nummer: list[int] = field(
        default_factory=list,
        metadata={
            "name": "ref.beweisNummer",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    ref_glaubhaftmachung_nummer: list[int] = field(
        default_factory=list,
        metadata={
            "name": "ref.glaubhaftmachungNummer",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    parteianhoerung: list[TypeGdsRefRollennummer] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    anlage: list[TypeGdsRefSgo] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )

    @dataclass(kw_only=True)
    class Inhalt:
        """
        :ivar tatsachenvortrag_sachverhaltsbeschreibung: Dieses Element
            dient dem Vortrag von Tatsachen und Sachverhalten in
            Textform.
        :ivar rechtliche_wuerdigung: Mit diesem Element kann eine
            rechtliche Würdigung in Textform übermittelt werden.
        """

        tatsachenvortrag_sachverhaltsbeschreibung: None | str = field(
            default=None,
            metadata={
                "name": "tatsachenvortrag.sachverhaltsbeschreibung",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            },
        )
        rechtliche_wuerdigung: None | str = field(
            default=None,
            metadata={
                "name": "rechtlicheWuerdigung",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            },
        )


@dataclass(kw_only=True)
class TypeKlaverBeweis:
    """
    Dieser Datentyp wird verwendet, um sämtliche Beweismittel, die im
    Klageverfahren relevant sind, aufzuführen.

    Dabei erhält jedes Beweismittel eine BeweisID. Diese BeweisID wird bei
    den Ausführungen, für die das Beweismittel einschlägig ist, angegeben.

    :ivar beweis_nummer: Diese Nummer wird verwendet, um den Beweis
        innerhalb einer XJustiz-Nachricht.mit einer oder mehreren
        Ausführungen (Type.KLAVER.Ausfuehrungen) zu verknüpfen.
    :ivar auswahl_beweismittel: In diesem Element kann die Art des
        Beweismittels ausgewählt werden.
    """

    class Meta:
        name = "Type.KLAVER.Beweis"

    beweis_nummer: int = field(
        metadata={
            "name": "beweisNummer",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    auswahl_beweismittel: TypeKlaverBeweis.AuswahlBeweismittel = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class AuswahlBeweismittel:
        """
        :ivar sachverstaendigengutachten: Mit dieser Auswahl kann die
            Erstellung eines Sachverständigengutachten als Beweis
            aufgeführt werden.
        :ivar zeugen: Mit dieser Auswahl kann ein Zeuge aufgeführt
            werden. Hierfür wird auf eine Person, die in den Grunddaten
            angegeben wurde, referenziert.
        :ivar auswahl_augenschein: Mit dieser Auswahl kann die
            Inaugenscheinnahme als Beweismittel aufgeführt werden.
        :ivar urkunde: Mit diesem Element kann eine Urkunde als Beweis
            aufgeführt werden. Hierfür wird auf ein Dokument, das in den
            Schriftgutobjekten angegeben ist, referenziert.
        :ivar parteivernehmung: Mit diesem Element kann die Partei für
            das Beweismittel Parteivernehmung aufgeführt werden. Hierfür
            wird auf eine Person, die in den Grunddaten angegeben wurde,
            referenziert.
        """

        sachverstaendigengutachten: None | bool = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        zeugen: None | TypeGdsRefRollennummer = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        auswahl_augenschein: (
            None | TypeKlaverBeweis.AuswahlBeweismittel.AuswahlAugenschein
        ) = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        urkunde: None | TypeGdsRefSgo = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        parteivernehmung: None | TypeGdsRefRollennummer = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )

        @dataclass(kw_only=True)
        class AuswahlAugenschein:
            """
            :ivar dokument: Sofern sich die Inaugenscheinnahme auf ein
                elektronisches Dokument, eine Akte oder eine Teilakte
                bezieht, die in den Schriftgutobjekten angegeben ist,
                kann auf sie referenziert werden.
            :ivar sonstige: Diese Auswahl ist zu treffen, sofern sich
                die Inaugenscheinnahme auf einen anderen Gegenstand
                bezieht.
            """

            dokument: None | TypeGdsRefSgo = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            sonstige: None | bool = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )


@dataclass(kw_only=True)
class TypeKlaverFgrErsatzangebot:
    """
    :ivar abreise: In diesem Element kann die Abreisezeit des
        Ersatzangebotes angegeben werden. Zusätzlich kann die Art der
        Beförderung angegeben werden.
    :ivar ankunft: In diesem Element kann die Ankunftszeit des
        Ersatzangebotes angegeben werden. Zusätzlich kann die Art der
        Beförderung angegeben werden.
    """

    class Meta:
        name = "Type.KLAVER.FGR.Ersatzangebot"

    abreise: None | TypeKlaverFgrBefoerderung = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    ankunft: None | TypeKlaverFgrBefoerderung = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )


@dataclass(kw_only=True)
class TypeKlaverFgrFluggast:
    """
    :ivar fluggast: Person, die an einem der Flüge teilgenommen hat
    :ivar buchungscode: Angabe des Buchungscodes der Buchung
    :ivar ref_beweis_nummer:
    """

    class Meta:
        name = "Type.KLAVER.FGR.Fluggast"

    fluggast: TypeGdsRefRollennummer = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    buchungscode: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        },
    )
    ref_beweis_nummer: list[int] = field(
        default_factory=list,
        metadata={
            "name": "ref.beweisNummer",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )


@dataclass(kw_only=True)
class TypeKlaverGlaubhaftmachung:
    """
    Dieser Datentyp wird verwendet, um sämtliche Mittel zur
    Glaubhaftmachung, die im Klageverfahren relevant sind, aufzuführen.

    Dabei erhält jedes Mittel zur Glaubhaftmachung eine
    GlaubhaftmachungNummer. Diese GlaubhaftmachungNummer wird bei den
    Ausführungen, für die das Mittel zur Glaubhaftmachung einschlägig ist,
    angegeben.

    :ivar glaubhaftmachung_nummer: Diese Nummer wird verwendet, um das
        Mittel zur Glaubhaftmachung innerhalb einer XJustiz-Nachricht
        mit einer oder mehreren Ausführungen (Type.KLAVER.Ausfuehrungen)
        zu verknüpfen.
    :ivar auswahl_mittel_glaubhaftmachung: In diesem Element kann die
        Art des Mittels zur Glaubhaftmachung ausgewählt werden.
    """

    class Meta:
        name = "Type.KLAVER.Glaubhaftmachung"

    glaubhaftmachung_nummer: int = field(
        metadata={
            "name": "glaubhaftmachungNummer",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    auswahl_mittel_glaubhaftmachung: TypeKlaverGlaubhaftmachung.AuswahlMittelGlaubhaftmachung = field(
        metadata={
            "name": "auswahl_mittelGlaubhaftmachung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class AuswahlMittelGlaubhaftmachung:
        """
        :ivar eidesstattliche_versicherung: Sofern die Glaubhaftmachung
            durch eidesstattliche Versicherung erfolgt, wird in diesem
            Element auf das Dokument, das die eidesstattliche
            Versicherung enthält und im Knoten Schriftgutobjekte
            aufgeführt ist, referenziert.
        :ivar ref_beweis_nummer: In diesem Element kann das
            Beweismittel, das für die Glaubhaftmachung verwendet werden
            soll, aufgeführt werden. Hierzu wird die Nummer, die im
            Element 'beweis' für das hier einschlägige Beweismittel
            verwendet wurde, angegeben.
        """

        eidesstattliche_versicherung: None | TypeGdsRefSgo = field(
            default=None,
            metadata={
                "name": "eidesstattlicheVersicherung",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        ref_beweis_nummer: None | int = field(
            default=None,
            metadata={
                "name": "ref.beweisNummer",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )


@dataclass(kw_only=True)
class TypeKlaverAntrag:
    """
    :ivar sachantraege:
    :ivar nebenantraege_zinsen: Wenn mit der Klage ein oder mehrere
        Nebenanträge auf Zinsen geltend gemacht werden, werden die
        erforderlichen Daten in dieser Sequenz übermittelt.
    :ivar auswahl_sonstige_antraege: In diesem Element können sonstige
        Anträge, wie z.B. Prozessanträge oder Kostenanträge, die mit der
        Klage geltend gemacht werden sollen, übermittelt werden.
    :ivar prozesskostenhilfe_beantragt: Mit diesem Element kann
        Prozesskostenhilfe beantragt werden.
    """

    class Meta:
        name = "Type.KLAVER.Antrag"

    sachantraege: None | TypeKlaverAntrag.Sachantraege = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    nebenantraege_zinsen: None | TypeKlaverAntrag.NebenantraegeZinsen = field(
        default=None,
        metadata={
            "name": "nebenantraege.zinsen",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    auswahl_sonstige_antraege: list[
        TypeKlaverAntrag.AuswahlSonstigeAntraege
    ] = field(
        default_factory=list,
        metadata={
            "name": "auswahl_sonstigeAntraege",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    prozesskostenhilfe_beantragt: list[
        TypeKlaverAntrag.ProzesskostenhilfeBeantragt
    ] = field(
        default_factory=list,
        metadata={
            "name": "prozesskostenhilfeBeantragt",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )

    @dataclass(kw_only=True)
    class Sachantraege:
        """
        :ivar inhalt: In diesem Element wird der bzw. die mit der Klage
            geltend gemachten Sachanträge in Textform übermittelt.
        :ivar anspruch: In diesem Element werden Angaben zur Höhe, Art
            und Gegenstand des mit der Klage geltend gemachten Ansprüche
            übermittelt. Sofern mit dem Sachantrag mehrere Ansprüche
            geltend gemacht werden, muss das Element "anspruch" mehrfach
            übermittelt werden.
        """

        inhalt: str = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|ƒ|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|ʰ|ʳ|[ʹ-ʺ]|[ʾ-ʿ]|ˆ|ˈ|ˌ|˜|ˢ|Ά|[Έ-Ί]|Ό|[Ύ-Ρ]|[Σ-ώ]|Ѝ|[А-Ъ]|Ь|[Ю-ъ]|ь|[ю-я]|ѝ|ᵈ|ᵗ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|[‘-‚]|[“-„]|[†-‡]|…|‰|[′-″]|[‹-›]|⁰|[⁴-⁹]|[ⁿ-₉]|€|™|∞|[≤-≥]|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            }
        )
        anspruch: list[TypeKlaverAnspruch] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )

    @dataclass(kw_only=True)
    class NebenantraegeZinsen:
        """
        :ivar inhalt: In diesem Element wird der mit der Klage geltend
            gemachte Nebenantrag auf Zinsen in Textform übermittelt.
        :ivar zinsanspruch:
        """

        inhalt: str = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|ƒ|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|ʰ|ʳ|[ʹ-ʺ]|[ʾ-ʿ]|ˆ|ˈ|ˌ|˜|ˢ|Ά|[Έ-Ί]|Ό|[Ύ-Ρ]|[Σ-ώ]|Ѝ|[А-Ъ]|Ь|[Ю-ъ]|ь|[ю-я]|ѝ|ᵈ|ᵗ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|[‘-‚]|[“-„]|[†-‡]|…|‰|[′-″]|[‹-›]|⁰|[⁴-⁹]|[ⁿ-₉]|€|™|∞|[≤-≥]|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            }
        )
        zinsanspruch: list[
            TypeKlaverAntrag.NebenantraegeZinsen.Zinsanspruch
        ] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )

        @dataclass(kw_only=True)
        class Zinsanspruch:
            """
            :ivar fortlaufende_nummer: Die fortlaufende Nummer wird als
                eindeutige Kennziffer innerhalb dieser XJustiz-Nachricht
                verwendet, um andere Elemente dieser XJustiz-Nachricht,
                insbesondere einen Vortrag in der Begründetheit, mit den
                jeweiligen Zinsansprüchen verknüpfen zu können. Die
                Nummern dürfen nicht doppelt vergeben werden.
            :ivar ref_fortlaufende_nummer: In diesem Element wird die
                fortlaufende Nummer des Anspruchs, für den die Zinsen
                geltend gemacht werden, angegeben.
            :ivar zinsen: Mit diesem Element können die
                Zinsinformationen für den angegeben Anspruch, ggf. auch
                für verschiedene Zeiträume, übermittelt werden.
            """

            fortlaufende_nummer: None | int = field(
                default=None,
                metadata={
                    "name": "fortlaufendeNummer",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            ref_fortlaufende_nummer: None | int = field(
                default=None,
                metadata={
                    "name": "ref.fortlaufendeNummer",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            zinsen: list[TypeGdsZinsen] = field(
                default_factory=list,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "min_occurs": 1,
                },
            )

    @dataclass(kw_only=True)
    class AuswahlSonstigeAntraege:
        """
        :ivar antrag_sonstige:
        :ivar fristen: Mit diesem Element kann die Verkürzung oder
            Verlängerung von Fristen beantragt werden.
        """

        antrag_sonstige: (
            None | TypeKlaverAntrag.AuswahlSonstigeAntraege.AntragSonstige
        ) = field(
            default=None,
            metadata={
                "name": "antrag.sonstige",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        fristen: None | TypeKlaverAntrag.AuswahlSonstigeAntraege.Fristen = (
            field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
        )

        @dataclass(kw_only=True)
        class AntragSonstige:
            """
            :ivar auswahl_antrag_sonstige:
            :ivar anspruch: In diesem Element werden Angaben zur Höhe,
                Art und Gegenstand des mit der Klage geltend gemachten
                Ansprüche übermittelt. Sofern mit dem Sachantrag mehrere
                Ansprüche geltend gemacht werden, muss das Element
                "anspruch" mehrfach übermittelt werden.
            """

            auswahl_antrag_sonstige: TypeKlaverAntrag.AuswahlSonstigeAntraege.AntragSonstige.AuswahlAntragSonstige = field(
                metadata={
                    "name": "auswahl_antrag.sonstige",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            anspruch: list[TypeKlaverAnspruch] = field(
                default_factory=list,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )

            @dataclass(kw_only=True)
            class AuswahlAntragSonstige:
                """
                :ivar antrag_werteliste: Mit diesem Auswahl-Element kann
                    ein Antrag aus dieser Codeliste gestellt werden. Die
                    zusätzliche Übermittlung in Textform ist nicht
                    vorgesehen.
                :ivar sonstiger_antrag_textform: Mit diesem Auswahl-
                    Element werden sonstige mit der Klage geltend
                    gemachte Anträge übermittelt. Dieses Element darf
                    nur verwendet werden, wenn in der Codeliste
                    Code.KLAVER.Antrag.Typ3 kein Wert für diesen Antrag
                    vorhanden ist.
                """

                antrag_werteliste: None | CodeKlaverAntragTyp3 = field(
                    default=None,
                    metadata={
                        "name": "antragWerteliste",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                    },
                )
                sonstiger_antrag_textform: None | str = field(
                    default=None,
                    metadata={
                        "name": "sonstigerAntragTextform",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|ƒ|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|ʰ|ʳ|[ʹ-ʺ]|[ʾ-ʿ]|ˆ|ˈ|ˌ|˜|ˢ|Ά|[Έ-Ί]|Ό|[Ύ-Ρ]|[Σ-ώ]|Ѝ|[А-Ъ]|Ь|[Ю-ъ]|ь|[ю-я]|ѝ|ᵈ|ᵗ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|[‘-‚]|[“-„]|[†-‡]|…|‰|[′-″]|[‹-›]|⁰|[⁴-⁹]|[ⁿ-₉]|€|™|∞|[≤-≥]|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )

        @dataclass(kw_only=True)
        class Fristen:
            """
            :ivar antragsteller:
            :ivar fortlaufende_nummer: Die fortlaufende Nummer wird als
                eindeutige Kennziffer innerhalb dieser XJustiz-Nachricht
                verwendet, um andere Elemente dieser XJustiz-Nachricht
                mit diesem Antrag auf Verkürzung oder Verlängerung von
                Fristen zu verknüpfen.
            :ivar betroffene_frist: In diesem Element muss die Frist,
                auf die sich der Antrag bezieht, benannt werden.
            :ivar auswahl_fristaenderung:
            """

            antragsteller: list[TypeGdsRefRollennummer] = field(
                default_factory=list,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            fortlaufende_nummer: None | int = field(
                default=None,
                metadata={
                    "name": "fortlaufendeNummer",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            betroffene_frist: str = field(
                metadata={
                    "name": "betroffeneFrist",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                }
            )
            auswahl_fristaenderung: TypeKlaverAntrag.AuswahlSonstigeAntraege.Fristen.AuswahlFristaenderung = field(
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )

            @dataclass(kw_only=True)
            class AuswahlFristaenderung:
                """
                :ivar fristende: Mit diesem Auswahl-Element kann das
                    Datum, an dem die Frist enden soll, angegeben
                    werden. Das Datum kann vor (Fristverkürzung) oder
                    nach (Fristverlängerung) der betroffenen Frist
                    liegen.
                :ivar fristverkuerzung: Mit diesem Auswahl-Element kann
                    der Zeitraum, um den die Frist verkürzt werden soll,
                    angegeben werden.
                :ivar fristverlaengerung: Mit diesem Auswahl-Element
                    kann der Zeitraum, um den die Frist verlängert
                    werden soll, angegeben werden.
                """

                fristende: None | XmlDate = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                    },
                )
                fristverkuerzung: None | TypeGdsDauer = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                    },
                )
                fristverlaengerung: None | TypeGdsDauer = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                    },
                )

    @dataclass(kw_only=True)
    class ProzesskostenhilfeBeantragt:
        """
        :ivar antragsteller:
        :ivar fortlaufende_nummer: Die fortlaufende Nummer wird als
            eindeutige Kennziffer innerhalb dieser XJustiz-Nachricht
            verwendet, um andere Elemente dieser XJustiz-Nachricht mit
            diesem Antrag auf Prozesskostenhilfe zu verknüpfen.
        :ivar beantragt: Falls Prozesskostenhilfe beantragt wird, wird
            der Antrag gestellt, indem in diesem Feld, der Wert 'true'
            angegeben wird.
        :ivar abhaengigkeit_klageerhebung: In diesem Element wird
            mitgeteilt, ob die Klageerhebung von der
            Prozesskostenhilfebewilligung abhängig gemacht wird (= true)
            oder nicht (=false).
        """

        antragsteller: list[TypeGdsRefRollennummer] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        fortlaufende_nummer: None | int = field(
            default=None,
            metadata={
                "name": "fortlaufendeNummer",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        beantragt: bool = field(
            init=False,
            default=True,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            },
        )
        abhaengigkeit_klageerhebung: bool = field(
            metadata={
                "name": "abhaengigkeitKlageerhebung",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )


@dataclass(kw_only=True)
class TypeKlaverKfvKostentatbestand:
    """
    :ivar kostentatbestands_id: Die eindeutige ID wird systemseitig
        vergeben und ermöglicht beim Datenaustausch die Bezugnahme auf
        einen bestimmten eigenen oder fremden Kostentatbestand.
    :ivar fremde_kostentatbestands_id: Sofern sich der Kostentatbestand
        auf einen Kostentatbestand eines anderen Verfahrensbeteiligten
        oder einen eigenen Kostentatbestand bezieht, kann dieser
        Kostentatbestand mit diesem Element verknüpft werden. Hierfür
        wird die ID, die für den zu verknüpfenden Kostentatbestand im
        Element 'kostentatbestandsID' angegeben wurde, verwendet.
    :ivar reihenfolge: In diesem Element kann eine Nummer angegeben
        werden, wenn die Kostentatbestände in einer bestimmten
        Reihenfolge verarbeitet werden sollen. Auf diese Weise können
        die verschiedenen Kostentatbestände eines Schriftsatzes im
        XJustiz-Format dem Leser in der vom Verfasser gewünschten
        Reihenfolge angezeigt werden. Die Nummern dürfen nicht doppelt
        vergeben werden. Die Nummerierung muss in dem Element mit 1
        beginnen.
    :ivar gegenstandswert: Hier ist der Gegenstandswert, nach dem sich
        die Gebühr richtet, anzugeben. Er ist nur anzugeben, wenn eine
        Wertgebühr geltend gemacht wird.
    :ivar auswahl_kostentatbestand: In diesem Element ist der Gebühren-
        bzw. Auslagentatbestand anzugeben. Dabei ist grundsätzlich ein
        Tatbestand aus der Codeliste
        Code.KLAVER.KFV.Kostentatbestand.Typ3 auszuwählen. Sollte in der
        Codeliste kein einschlägiger Code enthalten sein, ist das
        Auswahl-Element 'auffangtatbestand' zu verwenden.
    :ivar berechnungsfaktor: Anzugeben, sofern sich der
        Berechnungsfaktor nicht bereits aus dem Tatbestand ergibt.
    :ivar betrag: Anzugeben, sofern sich der Betrag der Gebühr oder der
        Auslage nicht bereits aus dem Tatbestand ergibt.
    :ivar begruendung: In diesem Element können Begründungen zum Antrag,
        zum Folgeantrag, wie z.B. Korrekturen und zur Erwiderung, wie
        z.B. Beanstandung, übermittelt werden.
    :ivar versicherung_post_tk: Anwaltliche Versicherung, dass die
        geltend gemachten Post- und Telekommunikationsdienstleistungen
        entstanden sind. Das Element ist nur für den Kostentatbestand
        Nr. 7002 VV RVG zu verwenden.
    """

    class Meta:
        name = "Type.KLAVER.KFV.Kostentatbestand"

    kostentatbestands_id: str = field(
        metadata={
            "name": "kostentatbestandsID",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"[0-9|A-F|a-f]{8}-[0-9|A-F|a-f]{4}-[0-9|A-F|a-f]{4}-[0-9|A-F|a-f]{4}-[0-9|A-F|a-f]{12}",
        }
    )
    fremde_kostentatbestands_id: None | str = field(
        default=None,
        metadata={
            "name": "fremdeKostentatbestandsID",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "pattern": r"[0-9|A-F|a-f]{8}-[0-9|A-F|a-f]{4}-[0-9|A-F|a-f]{4}-[0-9|A-F|a-f]{4}-[0-9|A-F|a-f]{12}",
        },
    )
    reihenfolge: None | int = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    gegenstandswert: None | Decimal = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    auswahl_kostentatbestand: (
        None | TypeKlaverKfvKostentatbestand.AuswahlKostentatbestand
    ) = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    berechnungsfaktor: None | float = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    betrag: None | TypeGdsGeldbetrag = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    begruendung: list[TypeKlaverAusfuehrungen] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    versicherung_post_tk: None | bool = field(
        default=None,
        metadata={
            "name": "versicherung_Post_TK",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )

    @dataclass(kw_only=True)
    class AuswahlKostentatbestand:
        """
        :ivar kostentatbestand: In diesem Element ist die einschlägige
            Nummer des Kostentatbestandes und ggf. eines modifizierenden
            Kostentatbestandes aus den Kosten- und
            Vergütungsverzeichnissen der Kostengesetzen anzugeben.
        :ivar auffangtatbestand: Sofern ein Kostentatbestand
            zugrundegelegt wird, der nicht in der Codeliste
            Code.KLAVER.KFV.Kostentatbestand.Typ3 enthalten ist (z.B.
            Kosten eines vorgerichtlichen Gutachtens oder
            Detektivkosten), kann dieser hier in Textform benannt
            werden.
        """

        kostentatbestand: (
            None
            | TypeKlaverKfvKostentatbestand.AuswahlKostentatbestand.Kostentatbestand
        ) = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        auffangtatbestand: None | str = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            },
        )

        @dataclass(kw_only=True)
        class Kostentatbestand:
            tatbestand: CodeKlaverKfvKostentatbestandTyp3 = field(
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            modifizierender_tatbestand: list[
                CodeKlaverKfvKostentatbestandTyp3
            ] = field(
                default_factory=list,
                metadata={
                    "name": "modifizierenderTatbestand",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )


@dataclass(kw_only=True)
class TypeKlaverVortrag:
    """
    :ivar schlagwort: In diesem Element soll dem Vortrag ein
        einschlägiges Schlagwort zugeordnet werden. z.B. in
        Verkehrsunfallsachen 'Unfallhergang' oder 'Schadenshöhe' oder
        weitere.
    :ivar reihenfolge: In diesem Element kann eine Nummer angegeben
        werden, wenn die Vorträge in einer bestimmten Reihenfolge
        verarbeitet werden sollen. Auf diese Weise können die
        verschiedenen Vorträge eines Schriftsatzes im XJustiz-Format dem
        Leser in der vom Verfasser gewünschten Reihenfolge angezeigt
        werden. In Verkehrsunfallsachen z.B. zuerst der Vortrag zum
        Unfallhergang und dann der Vortrag zur Schadenshöhe. Die Nummern
        dürfen nicht doppelt vergeben werden. Die Nummerierung muss in
        dem Element mit 1 beginnen.
    :ivar ref_fortlaufende_nummer: In diesem Element kann angegeben
        werden, auf welchen Antrag oder Anspruch sich der Vortrag
        bezieht. Hierfür wird die fortlaufende Nummer, die für den
        Antrag oder Anspruch im Element 'fortlaufendeNummer' angegeben
        wurde, verwendet.
    :ivar datum: Mit diesem Element kann, falls fachlich einschlägig,
        das Datum des Ereignisses auf das sich der Vortrag bezieht,
        angegeben werden. Auf diese Weise kann automatisiert ein
        Zeitstrahl der Geschehnisse erzeugt werden.
    :ivar vortrags_id: Die eindeutige ID wird systemseitig vergeben und
        ermöglicht beim Datenaustausch die Bezugnahme auf einen
        bestimmten eigenen oder fremden Vortrag.
    :ivar fremde_vortrags_id: Sofern sich der Vortrag auf einen Vortrag
        eines anderen Verfahrensbeteiligten oder einen eigenen Vortrag
        bezieht, kann dieser Vortrag mit diesem Element verknüpft
        werden. Hierfür wird die ID, die für den zu verknüpfenden
        Vortrag im Element "vortragsID" angegeben wurde, verwendet.
    :ivar ausfuehrungen: Mit diesem Element können Tatsachen,
        Ausführungen und eine rechtliche Würdigung in Textform
        übermittelt werden. Zudem können Beweise und Anlagen verknüpft
        werden. Dabei kann ein- und dasselbe Dokument sowohl als
        Beweismittel als auch als (vortragsergänzende) Anlage verknüpft
        werden.
    """

    class Meta:
        name = "Type.KLAVER.Vortrag"

    schlagwort: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )
    reihenfolge: None | int = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    ref_fortlaufende_nummer: list[int] = field(
        default_factory=list,
        metadata={
            "name": "ref.fortlaufendeNummer",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    datum: None | TypeGdsXdomeaZeitraumType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    vortrags_id: str = field(
        metadata={
            "name": "vortragsID",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"[0-9|A-F|a-f]{8}-[0-9|A-F|a-f]{4}-[0-9|A-F|a-f]{4}-[0-9|A-F|a-f]{4}-[0-9|A-F|a-f]{12}",
        }
    )
    fremde_vortrags_id: list[str] = field(
        default_factory=list,
        metadata={
            "name": "fremdeVortragsID",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "pattern": r"[0-9|A-F|a-f]{8}-[0-9|A-F|a-f]{4}-[0-9|A-F|a-f]{4}-[0-9|A-F|a-f]{4}-[0-9|A-F|a-f]{12}",
        },
    )
    ausfuehrungen: TypeKlaverAusfuehrungen = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class TypeKlaverFgrAusgleichsansprueche:
    """
    :ivar geltungsbereich:
    :ivar fluggast:
    :ivar geplante_reise: Beschreibung der laut Buchungsbestätigung
        ursprünglich geplanten Reise.
    :ivar auswahl_leistungsstoerung:
    :ivar anspruchshoehe:
    :ivar sonstiger_vortrag: Dieses Element wird verwendet, um etwaige
        zusätzliche Erklärungen und Ausführungen, auch zu anderen
        Ansprüchen, in strukturierter Form zu übermitteln.
    """

    class Meta:
        name = "Type.KLAVER.FGR.Ausgleichsansprueche"

    geltungsbereich: (
        None | TypeKlaverFgrAusgleichsansprueche.Geltungsbereich
    ) = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    fluggast: list[TypeKlaverFgrFluggast] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "min_occurs": 1,
        },
    )
    geplante_reise: None | TypeKlaverFgrAusgleichsansprueche.GeplanteReise = (
        field(
            default=None,
            metadata={
                "name": "geplanteReise",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
    )
    auswahl_leistungsstoerung: list[
        TypeKlaverFgrAusgleichsansprueche.AuswahlLeistungsstoerung
    ] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    anspruchshoehe: None | TypeKlaverFgrAusgleichsansprueche.Anspruchshoehe = (
        field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
    )
    sonstiger_vortrag: list[TypeKlaverVortrag] = field(
        default_factory=list,
        metadata={
            "name": "sonstigerVortrag",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )

    @dataclass(kw_only=True)
    class Geltungsbereich:
        voraussetzungen_flugtyp: (
            None
            | TypeKlaverFgrAusgleichsansprueche.Geltungsbereich.VoraussetzungenFlugtyp
        ) = field(
            default=None,
            metadata={
                "name": "voraussetzungenFlugtyp",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        kosten_flugticket: (
            None
            | TypeKlaverFgrAusgleichsansprueche.Geltungsbereich.KostenFlugticket
        ) = field(
            default=None,
            metadata={
                "name": "kostenFlugticket",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )

        @dataclass(kw_only=True)
        class VoraussetzungenFlugtyp:
            """
            :ivar feste_tragflaechen_und_motorisiert: In diesem Element
                wird angegeben, dass der Flug mit einem
                Motorluftflugzeug mit festen Tragflächen im Sinne des
                Art. 3 Abs. 4 Verordnung (EG) Nr. 261/2004 durchgeführt
                (keine Ballonfahrten, keine Hubschrauberfluege) wurde.
            :ivar ref_beweis_nummer:
            """

            feste_tragflaechen_und_motorisiert: bool = field(
                init=False,
                default=True,
                metadata={
                    "name": "festeTragflaechenUndMotorisiert",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                },
            )
            ref_beweis_nummer: list[int] = field(
                default_factory=list,
                metadata={
                    "name": "ref.beweisNummer",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )

        @dataclass(kw_only=True)
        class KostenFlugticket:
            """
            :ivar nicht_kostenlos: Versicherung, dass die Reise nicht
                kostenlos war und damit Art. 3 Abs. 2 Verordnung (EG)
                Nr. 261/2004 nicht zutrifft.
            :ivar kein_reduzierter_tarif: Versicherung, dass die Reise
                nicht zu einem reduzierten Tarif stattgefunden hat und
                damit Art. 3 Abs. 2 Verordnung (EG) Nr. 261/2004 nicht
                zutrifft.
            :ivar ref_beweis_nummer:
            """

            nicht_kostenlos: bool = field(
                metadata={
                    "name": "nichtKostenlos",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            kein_reduzierter_tarif: bool = field(
                metadata={
                    "name": "keinReduzierterTarif",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            ref_beweis_nummer: list[int] = field(
                default_factory=list,
                metadata={
                    "name": "ref.beweisNummer",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )

    @dataclass(kw_only=True)
    class GeplanteReise:
        """
        :ivar start:
        :ivar zwischenstopp: Hier können die Flughäfen, an denen ein
            Zwischenstopp geplant war, angegeben werden. Anzugeben als
            IATA Flughafen Code.
        :ivar ankunft:
        :ivar ref_beweis_nummer:
        """

        start: None | TypeKlaverFgrAusgleichsansprueche.GeplanteReise.Start = (
            field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
        )
        zwischenstopp: list[str] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            },
        )
        ankunft: (
            None | TypeKlaverFgrAusgleichsansprueche.GeplanteReise.Ankunft
        ) = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        ref_beweis_nummer: list[int] = field(
            default_factory=list,
            metadata={
                "name": "ref.beweisNummer",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )

        @dataclass(kw_only=True)
        class Start:
            """
            :ivar flughafen: Der Flughafen an dem das Flugzeug starten
                sollte. Anzugeben als IATA Flughafen Code.
            :ivar zeitpunkt: Der Zeitpunkt zu dem das Flugzeug abfliegen
                sollte.
            """

            flughafen: str = field(
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                }
            )
            zeitpunkt: XmlDateTime = field(
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )

        @dataclass(kw_only=True)
        class Ankunft:
            """
            :ivar flughafen: Der Flughafen an dem das Flugzeug landen
                sollte. Anzugeben als IATA Flughafen Code.
            :ivar zeitpunkt: Der Zeitpunkt zu dem das Flugzeug ankommen
                sollte.
            """

            flughafen: str = field(
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                }
            )
            zeitpunkt: XmlDateTime = field(
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )

    @dataclass(kw_only=True)
    class AuswahlLeistungsstoerung:
        """
        :ivar verspaetung: Eine Verspätung liegt vor, wenn die Ankunft
            am letzten Zielort mindestens drei Stunden nach der
            geplanten Ankunftszeit erfolgte.
        :ivar nichtbefoerderung: Die Weigerung gem. Art. 2 j) Verordnung
            (EG) Nr. 261/2004 rechtzeitig am Gate anwesende Fluggäste zu
            befoerdern, ohne dass ihnen gegenüber vertretbare Gründe
            vorliegen.
        :ivar annullierung: Die Nichtdurchführung eines geplanten
            Fluges, für den ein Platz reserviert war nach Art. 2 l)
            Verordnung (EG) Nr. 261/2004
        """

        verspaetung: (
            None
            | TypeKlaverFgrAusgleichsansprueche.AuswahlLeistungsstoerung.Verspaetung
        ) = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        nichtbefoerderung: (
            None
            | TypeKlaverFgrAusgleichsansprueche.AuswahlLeistungsstoerung.Nichtbefoerderung
        ) = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        annullierung: (
            None
            | TypeKlaverFgrAusgleichsansprueche.AuswahlLeistungsstoerung.Annullierung
        ) = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )

        @dataclass(kw_only=True)
        class Verspaetung:
            """
            :ivar betroffener_flug: Der Flug, der verspätet war
            :ivar anschlussflug_verpasst: Dieses Element ist anzugeben,
                wenn ein oder mehrere Anschlussflüge verpasst wurden.
            :ivar ankunft: In diesem Element kann die Ankunftszeit, zu
                der tatsächlich die Ankunft am Zielort stattgefunden
                hat, angegeben werden. Diese kann von der geplanten
                Ankunftszeit abweichen. Daraus errechnet sich die
                Verspätung des Fluges. Zusätzlich kann die Art der
                Beförderung angegeben werden.
            :ivar aussergewoehnliche_umstaende:
            :ivar puenktlichkeit:
            :ivar ref_beweis_nummer:
            """

            betroffener_flug: TypeKlaverFgrBetroffenerFlug = field(
                metadata={
                    "name": "betroffenerFlug",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            anschlussflug_verpasst: None | bool = field(
                default=None,
                metadata={
                    "name": "anschlussflugVerpasst",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            ankunft: None | TypeKlaverFgrBefoerderung = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            aussergewoehnliche_umstaende: (
                None
                | TypeKlaverFgrAusgleichsansprueche.AuswahlLeistungsstoerung.Verspaetung.AussergewoehnlicheUmstaende
            ) = field(
                default=None,
                metadata={
                    "name": "aussergewoehnlicheUmstaende",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            puenktlichkeit: None | TypeKlaverFgrPuenktlichkeit = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            ref_beweis_nummer: list[int] = field(
                default_factory=list,
                metadata={
                    "name": "ref.beweisNummer",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )

            @dataclass(kw_only=True)
            class AussergewoehnlicheUmstaende:
                """
                :ivar angegebene_umstaende: Vom Flugunternehmen
                    angegebene außergewöhnliche Umstände gem. Art. 5
                    Abs. 3 der Verordnung (EG) Nr. 261/2004
                :ivar ergriffene_massnahmen: Vom Flugunternehmen
                    ergriffene Maßnahmen
                """

                angegebene_umstaende: None | str = field(
                    default=None,
                    metadata={
                        "name": "angegebeneUmstaende",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )
                ergriffene_massnahmen: None | str = field(
                    default=None,
                    metadata={
                        "name": "ergriffeneMassnahmen",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )

        @dataclass(kw_only=True)
        class Nichtbefoerderung:
            """
            :ivar betroffener_flug: Der Flug, der nicht durchgeführt
                wurde
            :ivar anschlussflug_verpasst: Dieses Element ist anzugeben,
                wenn ein oder mehrere Anschlussflüge verpasst wurden.
            :ivar ankunft: In diesem Element kann die Ankunftszeit, zu
                der tatsächlich die Ankunft am Zielort stattgefunden
                hat, angegeben werden. Diese kann von der geplanten
                Ankunftszeit abweichen. Daraus errechnet sich die
                Verspätung des Fluges. Zusätzlich kann die Art der
                Beförderung angegeben werden.
            :ivar vertretbare_gruende: Vom Flugunternehmen angegebene
                vertretbare Gründe gem. Art. 5 Abs. 3 der Verordnung
                (EG) Nr. 261/2004
            :ivar puenktlichkeit:
            :ivar ref_beweis_nummer:
            """

            betroffener_flug: TypeKlaverFgrBetroffenerFlug = field(
                metadata={
                    "name": "betroffenerFlug",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            anschlussflug_verpasst: None | bool = field(
                default=None,
                metadata={
                    "name": "anschlussflugVerpasst",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            ankunft: None | TypeKlaverFgrBefoerderung = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            vertretbare_gruende: None | str = field(
                default=None,
                metadata={
                    "name": "vertretbareGruende",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            puenktlichkeit: None | TypeKlaverFgrPuenktlichkeit = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            ref_beweis_nummer: list[int] = field(
                default_factory=list,
                metadata={
                    "name": "ref.beweisNummer",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )

        @dataclass(kw_only=True)
        class Annullierung:
            """
            :ivar mitteilung_annullierung: Das Datum zu dem eine
                Annullierung durch das Flugunternehmen mitgeteilt wurde.
            :ivar betroffener_flug: Der Flug, der annulliert wurde
            :ivar anschlussflug_verpasst: Dieses Element ist anzugeben,
                wenn ein oder mehrere Anschlussflüge verpasst wurden.
            :ivar ersatzangebot: Diese Sequenz ist nur zu befüllen, wenn
                ein Ersatzangebot unterbreitet wurde.
            :ivar ref_beweis_nummer:
            """

            mitteilung_annullierung: None | XmlDate = field(
                default=None,
                metadata={
                    "name": "mitteilungAnnullierung",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            betroffener_flug: TypeKlaverFgrBetroffenerFlug = field(
                metadata={
                    "name": "betroffenerFlug",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            anschlussflug_verpasst: None | bool = field(
                default=None,
                metadata={
                    "name": "anschlussflugVerpasst",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            ersatzangebot: None | TypeKlaverFgrErsatzangebot = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            ref_beweis_nummer: list[int] = field(
                default_factory=list,
                metadata={
                    "name": "ref.beweisNummer",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )

    @dataclass(kw_only=True)
    class Anspruchshoehe:
        """
        :ivar anspruchshoehe:
        :ivar anspruchskuerzungen_um50_prozent:
        :ivar ersatzangebot: Diese Sequenz ist nur zu befüllen, wenn ein
            Ersatzangebot unterbreitet wurde.
        :ivar ref_beweis_nummer:
        """

        anspruchshoehe: CodeKlaverFgrAnspruchshoeheTyp3 = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        anspruchskuerzungen_um50_prozent: None | bool = field(
            default=None,
            metadata={
                "name": "anspruchskuerzungenUm50Prozent",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        ersatzangebot: None | TypeKlaverFgrErsatzangebot = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        ref_beweis_nummer: list[int] = field(
            default_factory=list,
            metadata={
                "name": "ref.beweisNummer",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )


@dataclass(kw_only=True)
class TypeKlaverKfvKostenfestsetzungsverfahren:
    """
    :ivar anlass: Mit diesem Element muss angegeben werden, ob ein
        Erstantrag, ein Folgeantrag, eine Erwiderung oder eine
        Beanstandung übermittelt werden soll.
    :ivar zu_verwendende_bankverbindung: Sofern der Antrag auf
        Auszahlung an den Antragsteller (z.B. PKH-Vergütung) gerichtet
        ist, ist hier auf die in den Grunddaten angegebene
        Bankverbindung des Antragstellers, die für die Auszahlung
        verwendet werden soll, zu referenzieren.
    :ivar grundentscheidung: Hier ist die Kostengrundentscheidung
        anzugeben.
    :ivar instanzrechnungsdaten: Sofern das Kostenfestsetzungsverfahren
        mehrere Gerichtsinstanzen betrifft, können mit diesem Element
        die Gebühren und Auslagen für jede Instanz gesondert angegeben
        werden.
    :ivar sonstiger_vortrag: Dieses Element wird verwendet, um etwaige
        zusätzliche Erklärungen und Ausführungen im
        Kostenfestsetzungsverfahren strukturierter Form zu übermitteln.
    """

    class Meta:
        name = "Type.KLAVER.KFV.Kostenfestsetzungsverfahren"

    anlass: CodeKlaverKfvAnlassTyp3 = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    zu_verwendende_bankverbindung: None | TypeGdsRefBankverbindung = field(
        default=None,
        metadata={
            "name": "zuVerwendendeBankverbindung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    grundentscheidung: list[
        TypeKlaverKfvKostenfestsetzungsverfahren.Grundentscheidung
    ] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    instanzrechnungsdaten: list[
        TypeKlaverKfvKostenfestsetzungsverfahren.Instanzrechnungsdaten
    ] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "min_occurs": 1,
        },
    )
    sonstiger_vortrag: list[TypeKlaverVortrag] = field(
        default_factory=list,
        metadata={
            "name": "sonstigerVortrag",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )

    @dataclass(kw_only=True)
    class Grundentscheidung:
        """
        :ivar auswahl_gericht_titelersteller:
        :ivar entscheidungsart:
        :ivar entscheidungsdatum:
        :ivar aktenzeichen: Nur erforderlich wenn Entscheidungen aus
            verschiedenen Verfahren zu berücksichtigen sind (z.B.
            mehrere Beschwerden). Andernfalls genügt das Aktenzeichen im
            Nachrichtenkopf.
        """

        auswahl_gericht_titelersteller: (
            None
            | TypeKlaverKfvKostenfestsetzungsverfahren.Grundentscheidung.AuswahlGerichtTitelersteller
        ) = field(
            default=None,
            metadata={
                "name": "auswahl_gericht.titelersteller",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        entscheidungsart: None | CodeGdsEntscheidungsartTyp3 = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        entscheidungsdatum: XmlDate = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        aktenzeichen: None | str = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            },
        )

        @dataclass(kw_only=True)
        class AuswahlGerichtTitelersteller:
            erkennendes_gericht: None | CodeGdsGerichteTyp3 = field(
                default=None,
                metadata={
                    "name": "erkennendesGericht",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            sonstiger_titelersteller: None | str = field(
                default=None,
                metadata={
                    "name": "sonstigerTitelersteller",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )

    @dataclass(kw_only=True)
    class Instanzrechnungsdaten:
        """
        :ivar ref_instanznummer: In diesem Element kann, mittels
            Referenz auf die Instanznummer, auf die entsprechende
            Instanz referenziert werden.
        :ivar kostentatbestand: In diesem Element können die
            Kostentatbestände für Gebühren und Auslagen, einschließlich
            der Parteikosten, angegeben werden.
        :ivar erhaltene_zahlungen: Hier sind Zahlungen anzugeben, die,
            z.B. aus der Staatskasse, an den Anspruchsteller geleistet
            wurden.
        """

        ref_instanznummer: None | str = field(
            default=None,
            metadata={
                "name": "ref.instanznummer",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            },
        )
        kostentatbestand: list[TypeKlaverKfvKostentatbestand] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        erhaltene_zahlungen: list[
            TypeKlaverKfvKostenfestsetzungsverfahren.Instanzrechnungsdaten.ErhalteneZahlungen
        ] = field(
            default_factory=list,
            metadata={
                "name": "erhalteneZahlungen",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )

        @dataclass(kw_only=True)
        class ErhalteneZahlungen:
            """
            :ivar zahler: Zahler kann z.B. die Staatskasse oder eine
                Partei sein.
            :ivar betrag: Hier sind die Beträge, die gezahlt wurden,
                anzugeben. Sofern mehrere Auszahlungen durch ein und den
                selben Zahler erfolgten, sollen die Beträge jeweils
                angegeben werden.
            :ivar begruendung: In diesem Element können Ausführungen zu
                den erhaltenen Zahlungen übermittelt werden.
            """

            zahler: TypeGdsRefRollennummer = field(
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            betrag: list[TypeGdsGeldbetrag] = field(
                default_factory=list,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "min_occurs": 1,
                },
            )
            begruendung: list[TypeKlaverAusfuehrungen] = field(
                default_factory=list,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )


@dataclass(kw_only=True)
class NachrichtKlaverKlageverfahren3500001:
    class Meta:
        name = "nachricht.klaver.klageverfahren.3500001"
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
    inhaltsdaten: NachrichtKlaverKlageverfahren3500001.Inhaltsdaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Inhaltsdaten:
        """
        :ivar antraege: Wenn mit dieser XJustiz-Nachricht Anträge
            gestellt werden sollen, ist dieses Element zu verwenden.
            Dabei sind für die Sachanträge, die Nebenanträge und die
            sonstigen Anträge gesonderte Elemente vorgesehen.
        :ivar beweis: Dieses Element wird verwendet, um sämtliche
            Beweismittel, die im Klageverfahren relevant sind,
            aufzuführen. Dabei erhält jedes Beweismittel eine BeweisID.
            Diese BeweisID wird bei den Ausführungen, für die das
            Beweismittel einschlägig ist, angegeben.
        :ivar glaubhaftmachung: Dieses Element wird verwendet, um
            sämtliche Mittel zur Glaubhaftmachung, die im Klageverfahren
            relevant sind, aufzuführen. Dabei erhält jedes Mittel zur
            Glaubhaftmachung eine GlaubhaftmachungNummer. Diese
            GlaubhaftmachungNummer wird bei den Ausführungen, für die
            das Mittel zur Glaubhaftmachung einschlägig ist, angegeben.
        :ivar gerichtsstand: Mit diesem Element können Tatsachen,
            Ausführungen und eine rechtliche Würdigung zum Gerichtsstand
            (§§ 12 ff. ZPO) in Textform übermittelt werden. Zudem können
            Beweise und Anlagen verknüpft werden. Dabei kann ein- und
            dasselbe Dokument sowohl als Beweismittel als auch als
            (vortragsergänzende) Anlage verknüpft werden.
        :ivar parteifaehigkeit: In diesem Element können Tatsachen,
            Ausführungen und eine rechtliche Würdigung zur
            Parteifähigkeit (§ 50 ZPO) in Textform übermittelt werden.
        :ivar prozessfaehigkeit: In diesem Element können Tatsachen,
            Ausführungen und eine rechtliche Würdigung zur
            Prozessfähigkeit (§§ 51 ff. ZPO) in Textform übermittelt
            werden.
        :ivar streitgenossenschaft: Wenn bei mehreren Klägern oder
            Beklagten Tatsachen und Ausführungen zur
            Streitgenossenschaft (§ 59 ff. ZPO) übermittelt werden
            sollen, wird diese Sequenz verwendet.
        :ivar beteiligung_dritter: Wenn an dem Rechtsstreit Dritte
            beteiligt werden sollen (§ 64 ff. ZPO), können die
            erforderlichen Daten in dieser Sequenz übermittelt werden.
        :ivar prozessvertretung: Tatsachen und Ausführungen, welche die
            Prozessvollmacht und die weiteren Voraussetzungen der
            Prozessvertretung gem. §§ 78 ff. ZPO betreffen.
        :ivar sonstige_prozessuale_ausfuehrungen: Erklärungen, welche
            die Vorschriften zur mündlichen Verhandlung (§§ 128 ff - 165
            ZPO) betreffen. Denkbar ist insbesondere eine Mitteilung, ob
            einer Entscheidung ohne mündliche Verhandlung nach § 128
            Abs. 2 ZPO zugestimmt wird; zudem eine Erklärung, ob
            Einwände/Bedenken (§ 253 Abs. 3 Nr. 4 ZPO) gegen die
            Durchführung eines Termins zur Güteverhandlung und zur
            mündlichen Verhandlung als Videoverhandlung nach § 128a ZPO
            bestehen. Mit diesem Datentyp können Tatsachen, Ausführungen
            und eine rechtliche Würdigung in Textform übermittelt
            werden. Zudem können Beweise und Anlagen verknüpft werden.
            Dabei kann ein- und dasselbe Dokument sowohl als
            Beweismittel als auch als (vortragsergänzende) Anlage
            verknüpft werden.
        :ivar zustellungen_und_ladungen: In diesem Element können
            Tatsachen, Ausführungen und Anordungen, welche die
            Vorschriften zur Zustellung, Ladung und zu Fristen (§§ 166
            ff - 229 ZPO) betreffen, übermittelt werden. Mit diesem
            Datentyp können Tatsachen, Ausführungen und eine rechtliche
            Würdigung in Textform übermittelt werden. Zudem können
            Beweise und Anlagen verknüpft werden. Dabei kann ein- und
            dasselbe Dokument sowohl als Beweismittel als auch als
            (vortragsergänzende) Anlage verknüpft werden.
        :ivar sonstige_sachentscheidungsvoraussetzungen: Hier können
            Ausführungen zu sonstigen Sachentscheidungsvoraussetzungen
            und Sollangaben (z.B. § 253 Abs. 2 ZPO) sowie rechtliche
            Würdigungen übermittelt werden. Zudem können Beweise
            verknüpft werden.
        :ivar gerichtskostenvorschuss_gezahlt: Sofern der
            Gerichtskostenvorschuss bereits eingezahlt wurde, kann in
            diesem Element auf den entsprechenden Nachweis, der als
            Dokument im Knoten Schriftgutobjekte angegeben ist,
            referenziert werden.
        :ivar auswahl_begruendetheit:
        """

        antraege: None | TypeKlaverAntrag = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )
        beweis: list[TypeKlaverBeweis] = field(
            default_factory=list,
            metadata={
                "type": "Element",
            },
        )
        glaubhaftmachung: list[TypeKlaverGlaubhaftmachung] = field(
            default_factory=list,
            metadata={
                "type": "Element",
            },
        )
        gerichtsstand: None | TypeKlaverAusfuehrungen = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )
        parteifaehigkeit: list[
            NachrichtKlaverKlageverfahren3500001.Inhaltsdaten.Parteifaehigkeit
        ] = field(
            default_factory=list,
            metadata={
                "type": "Element",
            },
        )
        prozessfaehigkeit: list[
            NachrichtKlaverKlageverfahren3500001.Inhaltsdaten.Prozessfaehigkeit
        ] = field(
            default_factory=list,
            metadata={
                "type": "Element",
            },
        )
        streitgenossenschaft: list[
            NachrichtKlaverKlageverfahren3500001.Inhaltsdaten.Streitgenossenschaft
        ] = field(
            default_factory=list,
            metadata={
                "type": "Element",
            },
        )
        beteiligung_dritter: list[
            NachrichtKlaverKlageverfahren3500001.Inhaltsdaten.BeteiligungDritter
        ] = field(
            default_factory=list,
            metadata={
                "name": "beteiligungDritter",
                "type": "Element",
            },
        )
        prozessvertretung: list[
            NachrichtKlaverKlageverfahren3500001.Inhaltsdaten.Prozessvertretung
        ] = field(
            default_factory=list,
            metadata={
                "type": "Element",
            },
        )
        sonstige_prozessuale_ausfuehrungen: None | TypeKlaverAusfuehrungen = (
            field(
                default=None,
                metadata={
                    "name": "sonstigeProzessualeAusfuehrungen",
                    "type": "Element",
                },
            )
        )
        zustellungen_und_ladungen: None | TypeKlaverAusfuehrungen = field(
            default=None,
            metadata={
                "name": "zustellungenUndLadungen",
                "type": "Element",
            },
        )
        sonstige_sachentscheidungsvoraussetzungen: list[TypeKlaverVortrag] = (
            field(
                default_factory=list,
                metadata={
                    "name": "sonstigeSachentscheidungsvoraussetzungen",
                    "type": "Element",
                },
            )
        )
        gerichtskostenvorschuss_gezahlt: None | TypeGdsRefSgo = field(
            default=None,
            metadata={
                "name": "gerichtskostenvorschussGezahlt",
                "type": "Element",
            },
        )
        auswahl_begruendetheit: NachrichtKlaverKlageverfahren3500001.Inhaltsdaten.AuswahlBegruendetheit = field(
            metadata={
                "type": "Element",
                "required": True,
            }
        )

        @dataclass(kw_only=True)
        class Parteifaehigkeit:
            """
            :ivar prozessbeteiligter: In diesem Element wird auf den
                Prozessbeteiligten/die Prozessbeteiligte, zu dem/denen
                Tatsachen und Ausführugen übermittelt werden sollen,
                referenziert. Hierfür wird die Rollennummer, die für den
                Beteiligten in den Grunddaten angegeben wurde,
                verwendet.
            :ivar ausfuehrungen:
            """

            prozessbeteiligter: list[TypeGdsRefRollennummer] = field(
                default_factory=list,
                metadata={
                    "type": "Element",
                    "min_occurs": 1,
                },
            )
            ausfuehrungen: TypeKlaverAusfuehrungen = field(
                metadata={
                    "type": "Element",
                    "required": True,
                }
            )

        @dataclass(kw_only=True)
        class Prozessfaehigkeit:
            """
            :ivar prozessbeteiligter: In diesem Element wird auf den
                Prozessbeteiligten/die Prozessbeteiligte, zu dem/denen
                Tatsachen und Ausführugen übermittelt werden sollen,
                referenziert. Hierfür wird die Rollennummer, die für den
                Beteiligten in den Grunddaten angegeben wurde,
                verwendet.
            :ivar ausfuehrungen:
            """

            prozessbeteiligter: list[TypeGdsRefRollennummer] = field(
                default_factory=list,
                metadata={
                    "type": "Element",
                    "min_occurs": 1,
                },
            )
            ausfuehrungen: TypeKlaverAusfuehrungen = field(
                metadata={
                    "type": "Element",
                    "required": True,
                }
            )

        @dataclass(kw_only=True)
        class Streitgenossenschaft:
            """
            :ivar streitgenosse: In diesem Element wird auf den
                Streitgenossen/die Streitgenossen, zu dem/denen
                Tatsachen und Ausführungen übermittelt werden sollen,
                referenziert. Hierfür wird die Rollennummer, die für den
                Beteiligten in den Grunddaten angegeben wurde,
                verwendet.
            :ivar ausfuehrungen:
            """

            streitgenosse: list[TypeGdsRefRollennummer] = field(
                default_factory=list,
                metadata={
                    "type": "Element",
                    "min_occurs": 1,
                },
            )
            ausfuehrungen: None | TypeKlaverAusfuehrungen = field(
                default=None,
                metadata={
                    "type": "Element",
                },
            )

        @dataclass(kw_only=True)
        class BeteiligungDritter:
            """
            :ivar beteiligter: In diesem Element wird auf den Dritten
                der am Rechtsstreit teilnimmt, zu dem/denen Tatsachen
                und Ausführungen übermittelt werden sollen,
                referenziert. Hierfür wird die Rollennummer, die für den
                Beteiligten in den Grunddaten angegeben wurde,
                verwendet.
            :ivar ausfuehrungen:
            """

            beteiligter: list[TypeGdsRefRollennummer] = field(
                default_factory=list,
                metadata={
                    "type": "Element",
                    "min_occurs": 1,
                },
            )
            ausfuehrungen: None | TypeKlaverAusfuehrungen = field(
                default=None,
                metadata={
                    "type": "Element",
                },
            )

        @dataclass(kw_only=True)
        class Prozessvertretung:
            """
            :ivar vollmachtgeber: In diesem Element wird auf den
                Prozessbeteiligten (Kläger oder Beklagter), der die
                Prozessvollmacht erteilt hat, referenziert. Hierfür wird
                die Rollennummer, die für den Beteiligten in den
                Grunddaten angegeben wurde, verwendet.
            :ivar vollmacht: In diesem Element sind die Ausführungen zur
                Bevollmächtigung in Textform zu übermitteln.
            :ivar vollmacht_nachweis: In diesem Element kann auf ein
                beigefügtes Dokument (i. d. R. die Vollmacht) verwiesen
                werden.
            """

            vollmachtgeber: TypeGdsRefRollennummer = field(
                metadata={
                    "type": "Element",
                    "required": True,
                }
            )
            vollmacht: str = field(
                metadata={
                    "type": "Element",
                    "required": True,
                    "pattern": r"([ -~]|[¡-¬]|[®-ž]|[Ƈ-ƈ]|Ə|ƒ|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|ʰ|ʳ|[ʹ-ʺ]|[ʾ-ʿ]|ˆ|ˈ|ˌ|˜|ˢ|Ά|[Έ-Ί]|Ό|[Ύ-Ρ]|[Σ-ώ]|ᵈ|ᵗ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|[‘-‚]|[“-„]|[†-‡]|…|‰|[′-″]|[‹-›]|⁰|[⁴-⁹]|[ⁿ-₉]|€|™|∞|[≤-≥]|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                }
            )
            vollmacht_nachweis: list[TypeGdsRefSgo] = field(
                default_factory=list,
                metadata={
                    "name": "vollmachtNachweis",
                    "type": "Element",
                },
            )

        @dataclass(kw_only=True)
        class AuswahlBegruendetheit:
            """
            :ivar fluggastrechte_ausgleichsansprueche: In diesem Element
                sind Ausgleichsansprüche nach Art. 7 der europäischen
                Fluggastrechte-Verordnung (261/2004) abgebildet.
            :ivar anderes_klageverfahren: Ist für das Klageverfahren
                kein gesondertes Auswahl-Element vorhanden, wird dieses
                Auswahl-Element für die Übermittlung der Begründetheit
                in strukturierter Form verwendet.
            :ivar kostenfestsetzungsverfahren: Mit diesem Element können
                Daten im Kostenfestsetzungsverfahren ausgetauscht
                werden. Hierzu gehören insbesondere Anträge auf
                Kostenfestsetzung, sowie Festlegung von Gebühren und
                Festsetzungen gegen die Staatskasse, sowie Folgeanträge,
                Erwiderungen und Beanstandungen.
            """

            fluggastrechte_ausgleichsansprueche: (
                None | TypeKlaverFgrAusgleichsansprueche
            ) = field(
                default=None,
                metadata={
                    "name": "fluggastrechte.ausgleichsansprueche",
                    "type": "Element",
                },
            )
            anderes_klageverfahren: (
                None
                | NachrichtKlaverKlageverfahren3500001.Inhaltsdaten.AuswahlBegruendetheit.AnderesKlageverfahren
            ) = field(
                default=None,
                metadata={
                    "name": "anderesKlageverfahren",
                    "type": "Element",
                },
            )
            kostenfestsetzungsverfahren: (
                None | TypeKlaverKfvKostenfestsetzungsverfahren
            ) = field(
                default=None,
                metadata={
                    "type": "Element",
                },
            )

            @dataclass(kw_only=True)
            class AnderesKlageverfahren:
                """
                :ivar vortrag: Dieses Element wird verwendet, um die
                    Inhalte der Begründetheit in strukturierter Form zu
                    übermitteln. Um den Vortrag inhaltlich gliedern zu
                    können, soll der Datentyp mehrfach verwendet werden.
                    So sollen einzelne Sachverhalte jeweils gesondert
                    angegeben werden. In Verkehrsunfallsachen soll z.B.
                    der Vortrag zum Unfallhergang und der Vortrag zur
                    Schadenshöhe jeweils gesondert erfolgen.
                """

                vortrag: list[TypeKlaverVortrag] = field(
                    default_factory=list,
                    metadata={
                        "type": "Element",
                        "min_occurs": 1,
                    },
                )
