from __future__ import annotations

from dataclasses import dataclass, field

from xsdata.models.datatype import XmlDate

from xjustiz.model_gen.xjustiz_0000_grunddatensatz_3_6 import (
    TypeGdsDauer,
    TypeGdsGeldbetrag,
    TypeGdsGrunddaten,
    TypeGdsNachrichtenkopf,
    TypeGdsRefRollennummer,
    TypeGdsRefSgo,
    TypeGdsSchriftgutobjekte,
)
from xjustiz.model_gen.xjustiz_0010_cl_allgemein_3_7 import (
    CodeGdsAstralTyp3,
    CodeGdsOwilTyp3,
)
from xjustiz.model_gen.xjustiz_1310_cl_aussonderung_3_0 import (
    CodeAussAussonderungsartTyp3,
    CodeAussBewertungsvorschlagTyp3,
)

__NAMESPACE__ = "http://www.xjustiz.de"


@dataclass(kw_only=True)
class TypeAussAufbewahrungsdauer:
    """
    Die Aufbewahrungsdauer legt fest, wie viele Jahre eine Akte oder ein
    Vorgang nach der Verfügung zur Akte (zdA-Verfügung) innerhalb der
    aktenführenden Stelle aufzubewahren ist oder ob die Aufbewahrung
    unbefristet erfolgen soll.
    """

    class Meta:
        name = "Type.AUSS.Aufbewahrungsdauer"

    auswahl_aufbewahrungsdauer: TypeAussAufbewahrungsdauer.AuswahlAufbewahrungsdauer = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class AuswahlAufbewahrungsdauer:
        """
        :ivar anzahl_jahre: Anzahl der Jahre, die eine Akte oder ein
            Vorgang nach der Verfügung zur Akte (zdA-Verfügung)
            innerhalb der aktenführenden Stelle aufzubewahren ist.
        :ivar unbefristet: Eine Akte oder ein Vorgang ist nach der
            Verfügung zur Akte (zdA-Verfügung) innerhalb der
            aktenführenden Stelle unbefristet aufzubewahren.
        """

        anzahl_jahre: None | int = field(
            default=None,
            metadata={
                "name": "anzahlJahre",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        unbefristet: None | bool = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )


@dataclass(kw_only=True)
class TypeAussErfolgOderMisserfolgAussonderung:
    """
    Die Information zum erfolgreichen oder nicht erfolgreichen Import eines
    auszusondernden Schriftgutobjekts.

    :ivar idsgo: Die ID des Schriftgutobjekts, das ausgesondert werden
        sollte.
    :ivar erfolgreich: Die Kennzeichnung des erfolgreichen oder nicht
        erfolgreichen Imports der Aussonderung zu einem
        Schriftgutobjekt. Der erfolgreiche Import wird mit 1 und der
        nicht erfolgreiche Import mit 0 gekennzeichnet.
    :ivar fehlermeldung: Erläuterung des Grundes für den nicht
        erfolgreichen Import einer Aussonderung zu einem
        Schriftgutobjekt.
    :ivar archivkennung: Die Archivsignatur, das heißt ID, unter der das
        auszusondernde Schriftgutobjekt im Archiv verwahrt wird. Für den
        Fall, dass "Erfolgreich" positiv belegt ist, können durch das
        archivierende System die Archivkennungen zu den einzelnen
        Schriftgutobjekten übergeben werden.
    """

    class Meta:
        name = "Type.AUSS.ErfolgOderMisserfolgAussonderung"

    idsgo: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"[0-9|A-F|a-f]{8}-[0-9|A-F|a-f]{4}-[0-9|A-F|a-f]{4}-[0-9|A-F|a-f]{4}-[0-9|A-F|a-f]{12}",
        }
    )
    erfolgreich: bool = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    fehlermeldung: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        },
    )
    archivkennung: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        },
    )


@dataclass(kw_only=True)
class TypeAussFachlicheDaten:
    """
    :ivar erledigungsgrund: In diesem Element wird der Erledigungsgrund,
        der für statistische Zwecke erfasst wurde, übermittelt
    :ivar anzahl_termine: Angabe der Anzahl der stattgefundenen
        gerichtlichen und staatsanwaltschaftlichen Termine.
    :ivar auswahl_fachgebiet:
    """

    class Meta:
        name = "Type.AUSS.FachlicheDaten"

    erledigungsgrund: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        },
    )
    anzahl_termine: None | int = field(
        default=None,
        metadata={
            "name": "anzahlTermine",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    auswahl_fachgebiet: None | TypeAussFachlicheDaten.AuswahlFachgebiet = (
        field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
    )

    @dataclass(kw_only=True)
    class AuswahlFachgebiet:
        register: None | TypeAussFachlicheDaten.AuswahlFachgebiet.Register = (
            field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
        )
        straf: None | TypeAussFachlicheDaten.AuswahlFachgebiet.Straf = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        bussgeldsachen: (
            None | TypeAussFachlicheDaten.AuswahlFachgebiet.Bussgeldsachen
        ) = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )

        @dataclass(kw_only=True)
        class Register:
            """
            :ivar referenz_organisation: Hier wird auf auf die Daten der
                Organisation referenziert.
            :ivar eintragungsdatum:
            :ivar gruendungsdatum:
            :ivar geschaeftszweck:
            :ivar kapital:
            :ivar loeschungsdatum:
            :ivar vorgaenger:
            :ivar nachfolger:
            """

            referenz_organisation: TypeGdsRefRollennummer = field(
                metadata={
                    "name": "referenz.organisation",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            eintragungsdatum: None | XmlDate = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            gruendungsdatum: None | XmlDate = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            geschaeftszweck: None | str = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            kapital: None | TypeGdsGeldbetrag = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            loeschungsdatum: None | XmlDate = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            vorgaenger: None | str = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([ -~]|[¡-¬]|[®-ž]|[Ƈ-ƈ]|Ə|ƒ|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|ʰ|ʳ|[ʹ-ʺ]|[ʾ-ʿ]|ˆ|ˈ|ˌ|˜|ˢ|Ά|[Έ-Ί]|Ό|[Ύ-Ρ]|[Σ-ώ]|ᵈ|ᵗ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|[‘-‚]|[“-„]|[†-‡]|…|‰|[′-″]|[‹-›]|⁰|[⁴-⁹]|[ⁿ-₉]|€|™|∞|[≤-≥]|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            nachfolger: None | str = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([ -~]|[¡-¬]|[®-ž]|[Ƈ-ƈ]|Ə|ƒ|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|ʰ|ʳ|[ʹ-ʺ]|[ʾ-ʿ]|ˆ|ˈ|ˌ|˜|ˢ|Ά|[Έ-Ί]|Ό|[Ύ-Ρ]|[Σ-ώ]|ᵈ|ᵗ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|[‘-‚]|[“-„]|[†-‡]|…|‰|[′-″]|[‹-›]|⁰|[⁴-⁹]|[ⁿ-₉]|€|™|∞|[≤-≥]|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )

        @dataclass(kw_only=True)
        class Straf:
            """
            :ivar astral_id:
            :ivar strafdauer: Sofern der Angeklagte zu einer
                Freiheitsstrafe verurteilt wurde, kann in diesem Element
                die Dauer einer Freiheitsstrafe mitgeteilt werden.
            """

            astral_id: CodeGdsAstralTyp3 = field(
                metadata={
                    "name": "astralID",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            strafdauer: None | TypeGdsDauer = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )

        @dataclass(kw_only=True)
        class Bussgeldsachen:
            """
            :ivar owil_id: Ordnungswidrigkeitentatbestandsliste
            """

            owil_id: CodeGdsOwilTyp3 = field(
                metadata={
                    "name": "owilID",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )


@dataclass(kw_only=True)
class TypeAussMetadatenAussonderung:
    """
    MetadatenAussonderung fasst die Informationen zu einem abschließend
    bearbeiteten Schriftgutobjekt (Vorgang oder Akte) zusammen, die für
    seine Aufbewahrung und Aussonderung relevant sind.

    :ivar aufbewahrungsdauer: Die Aufbewahrungsdauer legt fest, wie
        viele Jahre eine Akte oder ein Vorgang nach der Verfügung zur
        Akte (zdAVerfügung) durch die aktenführende Stelle aufzubewahren
        ist oder ob die Aufbewahrung unbefristet erfolgen soll. Nach
        Ablauf der Aufbewahrungsfrist erfolgt die Aussonderung in
        Abhängigkeit von der Aussonderungsart.
    :ivar aussonderungsart: Die Aussonderungsart gibt das Ergebnis der
        archivischen Bewertung an. Damit eine automatische Selektion der
        auszusondernden Vorgänge erfolgen kann, muss in
        Vorgangsbearbeitungssystemen für Akten und Vorgänge ein
        Metadatum "Aussonderungsart" vorgegeben werden. Die
        Metainformation enthält den Status „archivwürdig“, „bewerten“
        oder „vernichten“. Die Aussonderungsart wird vom Aktenplan
        (zweistufiges Aussonderungsverfahren) oder von der Akte
        (vierstufiges Aussonderungsverfahren) auf zugehörige Vorgänge
        und Dokumente vererbt.
    :ivar bewertungsvorschlag: Der Bewertungsvorschlag ist ein Hinweis
        des Bearbeiters eines Schriftgutobjekts an das zuständige
        Archiv. Er kann die Werte „archivwürdig“ oder „vernichten“
        annehmen.
    :ivar bewertungsvorschlag_grund:
    :ivar bundesarchivspezifische_daten: Dieses Element wird nur für den
        Datenaustausch mit dem Bundesarchiv verwendet
    """

    class Meta:
        name = "Type.AUSS.MetadatenAussonderung"

    aufbewahrungsdauer: TypeAussAufbewahrungsdauer = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    aussonderungsart: None | CodeAussAussonderungsartTyp3 = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    bewertungsvorschlag: None | CodeAussBewertungsvorschlagTyp3 = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    bewertungsvorschlag_grund: None | str = field(
        default=None,
        metadata={
            "name": "bewertungsvorschlagGrund",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        },
    )
    bundesarchivspezifische_daten: (
        None | TypeAussMetadatenAussonderung.BundesarchivspezifischeDaten
    ) = field(
        default=None,
        metadata={
            "name": "bundesarchivspezifischeDaten",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )

    @dataclass(kw_only=True)
    class BundesarchivspezifischeDaten:
        """
        :ivar auswahl_aussonderung: Gem. JAktAV können die Unterlagen in
            Verfahrensakten zwei unterschiedlichen Aufbewahrungsfristen
            zugeordnet sein. Daraus ergibt sich die Notwendigkeit,
            solche Akten mit entsprechendem zeitlichen Abstand
            aufgeteilt in zwei Nachrichten auszusondern, der
            "Teilaussonderung" und der "Restaussonderung". Liegt keine
            Aufteilung in zwei Aufbewahrungsfristen vor, handelt es sich
            um eine "Vollaussonderung". Die Auswahl des entsprechenden
            Unterelements richtet sich nach dem vorliegenden Datenpaket.
        :ivar aufbewahrungsende:
        :ivar erledigungsdatum:
        :ivar weglegungsdatum:
        """

        auswahl_aussonderung: TypeAussMetadatenAussonderung.BundesarchivspezifischeDaten.AuswahlAussonderung = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        aufbewahrungsende: XmlDate = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        erledigungsdatum: None | XmlDate = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        weglegungsdatum: None | XmlDate = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )

        @dataclass(kw_only=True)
        class AuswahlAussonderung:
            """
            :ivar teilaussonderung: Bei der Teilaussonderung werden die
                Unterlagen ausgesondert, die der ersten der beiden
                Aufbewahrungsfristen unterliegen.
            :ivar restaussonderung: Bei der Restaussonderung werden die
                noch ausstehenden Unterlagen einer bereits
                teilausgesonderten Akte übertragen. Hier ist anzugeben,
                dass es sich um eine Restaussonderung handelt.
            :ivar vollaussonderung: Bei der Vollaussonderung werden alle
                Unterlagen einer Akte zum gleichen Zeitpunkt in einem
                Datenpaket ausgesondert. Hier ist anzugeben, dass es
                sich um eine Vollaussonderung handelt.
            """

            teilaussonderung: (
                None
                | TypeAussMetadatenAussonderung.BundesarchivspezifischeDaten.AuswahlAussonderung.Teilaussonderung
            ) = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            restaussonderung: None | bool = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            vollaussonderung: None | bool = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )

            @dataclass(kw_only=True)
            class Teilaussonderung:
                """
                :ivar teilaussonderung: Hier ist anzugeben, dass es sich
                    um eine Teilaussonderung handelt.
                :ivar ablaufdatum: Hier wird das Datum der
                    Restaussonderung eingetragen.
                """

                teilaussonderung: bool = field(
                    init=False,
                    default=True,
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "required": True,
                    },
                )
                ablaufdatum: XmlDate = field(
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "required": True,
                    }
                )


@dataclass(kw_only=True)
class TypeAussRueckgabeparameterAnbietung:
    """
    Die Rückmeldung des Archivs zu einem zur Bewertung übergegebenen
    Schriftgutobjekt zur Steuerung des weiteren Aussonderungsprozesses.

    :ivar id: Die UUID des angebotenen Schriftgutobjektes, in der Regel
        die eines Vorgangs.
    :ivar aussonderungsart: Die Beschreibung des Bewertungsergebnisses
        für ein angebotenes Schriftgutobjekt.
    """

    class Meta:
        name = "Type.AUSS.RueckgabeparameterAnbietung"

    id: TypeGdsRefSgo = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    aussonderungsart: CodeAussAussonderungsartTyp3 = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class NachrichtAussAussonderungImportBestaetigen1300006:
    class Meta:
        name = "nachricht.auss.aussonderungImportBestaetigen.1300006"
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    fachdaten: NachrichtAussAussonderungImportBestaetigen1300006.Fachdaten = (
        field(
            metadata={
                "type": "Element",
                "required": True,
            }
        )
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        ausgesondertes_sgo: list[TypeAussErfolgOderMisserfolgAussonderung] = (
            field(
                default_factory=list,
                metadata={
                    "name": "ausgesondertesSGO",
                    "type": "Element",
                    "min_occurs": 1,
                },
            )
        )


@dataclass(kw_only=True)
class TypeAussFachdaten:
    """
    Archivspezifische Fachdaten zum Aussonderungsobjekt.

    :ivar archivspezifische_metadaten:
    :ivar allgemeine_daten: Das spezielle Konzept des Fachmoduls
        Aussonderung erfordert diese Darstellung. Deshalb stimmt das
        Projektbüro der BLK-AG IT-Standards dieser Abweichung als
        Ausnahme zu. Die grundsätzlichen Konventionen von XJustiz
        bleiben davon unberührt.
    :ivar fachliche_daten:
    """

    class Meta:
        name = "Type.AUSS.Fachdaten"

    archivspezifische_metadaten: TypeAussMetadatenAussonderung = field(
        metadata={
            "name": "archivspezifischeMetadaten",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    allgemeine_daten: None | TypeGdsGrunddaten = field(
        default=None,
        metadata={
            "name": "allgemeineDaten",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    fachliche_daten: None | TypeAussFachlicheDaten = field(
        default=None,
        metadata={
            "name": "fachlicheDaten",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )


@dataclass(kw_only=True)
class NachrichtAussBewertungsverzeichnis1300003:
    class Meta:
        name = "nachricht.auss.bewertungsverzeichnis.1300003"
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    fachdaten: NachrichtAussBewertungsverzeichnis1300003.Fachdaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        bewertetes_objekt: list[TypeAussRueckgabeparameterAnbietung] = field(
            default_factory=list,
            metadata={
                "name": "bewertetesObjekt",
                "type": "Element",
                "min_occurs": 1,
            },
        )


@dataclass(kw_only=True)
class NachrichtAussArchivJustizZuArchiv1300001:
    """
    Ein Objekt Aussonderungsobjekt muss unter dem Objekt Schriftgutobjekt
    (SGO) genau ein Aktenobjekt (ggf. mit Teilakten) führen.

    Jede weitere Akte muss mit einem neuen Aussonderungsobjekt aufgeführt
    werden.
    """

    class Meta:
        name = "nachricht.auss.archiv.justizZuArchiv.1300001"
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    fachdaten: NachrichtAussArchivJustizZuArchiv1300001.Fachdaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        aussonderungsobjekt: list[
            NachrichtAussArchivJustizZuArchiv1300001.Fachdaten.Aussonderungsobjekt
        ] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "min_occurs": 1,
            },
        )

        @dataclass(kw_only=True)
        class Aussonderungsobjekt:
            schriftgutobjekte: TypeGdsSchriftgutobjekte = field(
                metadata={
                    "type": "Element",
                    "required": True,
                }
            )
            fachdaten_aussonderung: TypeAussFachdaten = field(
                metadata={
                    "name": "fachdatenAussonderung",
                    "type": "Element",
                    "required": True,
                }
            )
