from __future__ import annotations

from dataclasses import dataclass, field

from xsdata.models.datatype import XmlDate

from xjustiz.model_gen.xjustiz_0000_grunddatensatz_3_6 import (
    TypeGdsBeteiligung,
    TypeGdsGrunddaten,
    TypeGdsNachrichtenkopf,
    TypeGdsRefRollennummer,
    TypeGdsSchriftgutobjekte,
)
from xjustiz.model_gen.xjustiz_3110_cl_musterfeststellungsklagenregister_1_3 import (
    CodeMfkregArtDerOeffentlichenBekanntmachungTyp3,
    CodeMfkregBekanntmachungsartTyp3,
    CodeMfkregGliederungspunkteTyp3,
    CodeMfkregKlageartTyp3,
    CodeMfkregRegisterauszugsartTyp3,
)

__NAMESPACE__ = "http://www.xjustiz.de"


@dataclass(kw_only=True)
class TypeMfkregTextanpassung:
    """
    Dieser Typ wird für die Angabe von Textstreichungen und Textergänzungen
    verwendet.
    """

    class Meta:
        name = "Type.MFKREG.Textanpassung"

    angabe_textstelle: str = field(
        metadata={
            "name": "angabeTextstelle",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([ -~]|[¡-¬]|[®-ž]|[Ƈ-ƈ]|Ə|ƒ|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|ʰ|ʳ|[ʹ-ʺ]|[ʾ-ʿ]|ˆ|ˈ|ˌ|˜|ˢ|Ά|[Έ-Ί]|Ό|[Ύ-Ρ]|[Σ-ώ]|ᵈ|ᵗ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|[‘-‚]|[“-„]|[†-‡]|…|‰|[′-″]|[‹-›]|⁰|[⁴-⁹]|[ⁿ-₉]|€|™|∞|[≤-≥]|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )
    text: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([ -~]|[¡-¬]|[®-ž]|[Ƈ-ƈ]|Ə|ƒ|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|ʰ|ʳ|[ʹ-ʺ]|[ʾ-ʿ]|ˆ|ˈ|ˌ|˜|ˢ|Ά|[Έ-Ί]|Ό|[Ύ-Ρ]|[Σ-ώ]|ᵈ|ᵗ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|[‘-‚]|[“-„]|[†-‡]|…|‰|[′-″]|[‹-›]|⁰|[⁴-⁹]|[ⁿ-₉]|€|™|∞|[≤-≥]|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )


@dataclass(kw_only=True)
class TypeMfkregBekanntmachungstexte:
    """
    Je nach Kommunikationsszenario müssen bzw. können verschiedene
    Bekanntmachungen, Beschlüsse, Rechtsbelehrungen etc. zu einer
    Musterfeststellungsklage nach ZPO a.F., zu einer Verbandsklage, zu
    einer Unterlassungsklage oder zu einer einstweiligen Verfügung
    veröffentlicht werden.

    Das Szenario ergibt sich aus dem Ereignis, das im Nachrichtenkopf
    angegeben wird. Es ist dabei immer ein passender Gliederungspunkt zum
    Freitext anzugeben. Alle mehrseitigen Texte wie Urteile,
    Beschlussinhalte und andere Mitteilungen können auch als Schriftgut,
    d.h. als barrierefreie PDF-Dokumente übermittelt werden. Dann werden
    diese PDF-Dokumente im Klageregister öffentlich bekannt gemacht.

    :ivar ref_termins_id: Wenn die Bekanntmachung eines Termins zu einer
        Musterfeststellungsklage nach ZPO a.F. einen Hinweis zu diesem
        Termin enthält, dann wird dieser Hinweis als Bekanntmachungstext
        angegeben. Über diese ID kann der Hinweis auf den Termin
        referenzieren.
    :ivar textnummer: Die Texte innerhalb einer Bekanntmachung sind
        fortlaufend zu nummerieren.
    :ivar ueberschrift_bekanntmachung: Es ist zu jedem Text einer
        Bekanntmachung ein Gliederungspunkt als Überschrift gemäß
        Codeliste anzugeben.
    :ivar inhalt_bekanntmachung: Es ist der zum Gliederungspunkt
        passende Text der Bekanntmachung als Freitext anzugeben. Sofern
        es sich bei dem zu veröffentlichenden Text um eine
        Rechtsbelehrung handelt, wird ein Default-Text für die Gerichte
        vorgegeben (Codeliste Rechtsbelehrungen). Anderenfalls ist hier
        der, je nach Ereignis und Überschrift, zu veröffentlichende
        Inhalt der Bekanntmachung anzugeben.
    """

    class Meta:
        name = "Type.MFKREG.Bekanntmachungstexte"

    ref_termins_id: None | str = field(
        default=None,
        metadata={
            "name": "ref.terminsID",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        },
    )
    textnummer: int = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    ueberschrift_bekanntmachung: CodeMfkregGliederungspunkteTyp3 = field(
        metadata={
            "name": "ueberschrift.bekanntmachung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    inhalt_bekanntmachung: str = field(
        metadata={
            "name": "inhalt.bekanntmachung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([ -~]|[¡-¬]|[®-ž]|[Ƈ-ƈ]|Ə|ƒ|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|ʰ|ʳ|[ʹ-ʺ]|[ʾ-ʿ]|ˆ|ˈ|ˌ|˜|ˢ|Ά|[Έ-Ί]|Ό|[Ύ-Ρ]|[Σ-ώ]|ᵈ|ᵗ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|[‘-‚]|[“-„]|[†-‡]|…|‰|[′-″]|[‹-›]|⁰|[⁴-⁹]|[ⁿ-₉]|€|™|∞|[≤-≥]|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )


@dataclass(kw_only=True)
class NachrichtMfkregEntscheidungVergleich3100012:
    """
    Mit dieser Nachricht werden die Beschlüsse zu Entscheidungen und
    Urteilen oder einem gerichtlich genehmigten Vergleich dem Bundesamt für
    Justiz zur Bekanntmachung übersandt.
    """

    class Meta:
        name = "nachricht.mfkreg.entscheidung.vergleich.3100012"
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
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
    fachdaten: NachrichtMfkregEntscheidungVergleich3100012.Fachdaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        auswahl_entscheidung_vergleich: NachrichtMfkregEntscheidungVergleich3100012.Fachdaten.AuswahlEntscheidungVergleich = field(
            metadata={
                "name": "auswahl_entscheidung.vergleich",
                "type": "Element",
                "required": True,
            }
        )

        @dataclass(kw_only=True)
        class AuswahlEntscheidungVergleich:
            """
            :ivar entscheidung: Die Entscheidung(en) werden in Abschrift
                als barrierefreies PDF (Schriftgut) beigefügt.
            :ivar vergleich: Die Abschrift des gerichtlich genehmigten
                Vergleichs wird als barrierefreies PDF (Schriftgut)
                beigefügt.
            """

            entscheidung: (
                None
                | NachrichtMfkregEntscheidungVergleich3100012.Fachdaten.AuswahlEntscheidungVergleich.Entscheidung
            ) = field(
                default=None,
                metadata={
                    "type": "Element",
                },
            )
            vergleich: (
                None
                | NachrichtMfkregEntscheidungVergleich3100012.Fachdaten.AuswahlEntscheidungVergleich.Vergleich
            ) = field(
                default=None,
                metadata={
                    "type": "Element",
                },
            )

            @dataclass(kw_only=True)
            class Entscheidung:
                """
                :ivar datum:
                :ivar auswahl_entscheidung: Es können mehrere
                    Entscheidungen zusammen in der Nachricht übermittelt
                    werden.
                :ivar aufhebung_und_zurueckweisung: Hier kann bei Bedarf
                    der Umfang der vollständigen oder teilweisen
                    Aufhebung und Zurückweisung dargestellt werden.
                    Dabei sollte auch auf den Tenor der Entscheidung
                    Bezug genommen werden.
                """

                datum: XmlDate = field(
                    metadata={
                        "type": "Element",
                        "required": True,
                    }
                )
                auswahl_entscheidung: NachrichtMfkregEntscheidungVergleich3100012.Fachdaten.AuswahlEntscheidungVergleich.Entscheidung.AuswahlEntscheidung = field(
                    metadata={
                        "type": "Element",
                        "required": True,
                    }
                )
                aufhebung_und_zurueckweisung: None | str = field(
                    default=None,
                    metadata={
                        "name": "aufhebungUndZurueckweisung",
                        "type": "Element",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )

                @dataclass(kw_only=True)
                class AuswahlEntscheidung:
                    urteil: None | bool = field(
                        default=None,
                        metadata={
                            "type": "Element",
                        },
                    )
                    beschluss: None | bool = field(
                        default=None,
                        metadata={
                            "type": "Element",
                        },
                    )
                    sonstige_entscheidung: None | str = field(
                        default=None,
                        metadata={
                            "name": "sonstigeEntscheidung",
                            "type": "Element",
                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                        },
                    )

            @dataclass(kw_only=True)
            class Vergleich:
                datum: XmlDate = field(
                    metadata={
                        "type": "Element",
                        "required": True,
                    }
                )
                information_vergleich: str = field(
                    init=False,
                    default="Das Verbandsklageverfahren kann durch einen gerichtlichen Vergleich mit Wirkung für und gegen die Angemeldeten beendet werden. Der Vergleich bedarf der Genehmigung durch das Gericht. Das BfJ macht den genehmigten Vergleich im Verbandsklageregister öffentlich bekannt. Angemeldete zu der Verbandsklage können innerhalb eines Monats ab Bekanntgabe des Vergleichs den Austritt aus dem Vergleich erklären. Der Austritt muss gegenüber dem BfJ in Textform erklärt werden. Für den Vergleichsaustritt stellt das BfJ auf seiner Internetseite in dem Bereich 'Öffentliche Bekanntmachungen im Verbandsklageregister' unter der jeweiligen Klage ein Formular zur Verfügung. Das Formular kann auch postalisch beim Bundesamt für Justiz, Verbandsklageregister, 53094 Bonn angefordert werden. Wird der Vergleichsaustritt durch eine Rechtsanwältin oder einen Rechtsanwalt erklärt, muss für die Erklärung das vom BfJ hierfür elektronisch bereitgestellte Formular genutzt werden. Angemeldete, die ihren Austritt wirksam erklärt haben, werden durch den Vergleich nicht gebunden. Durch den Austritt wird die Wirksamkeit der Anmeldung zum Verbandsklageregister nicht berührt.",
                    metadata={
                        "name": "informationVergleich",
                        "type": "Element",
                        "required": True,
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )


@dataclass(kw_only=True)
class NachrichtMfkregRechtskraftVeroeffentlichungZustellung3100004:
    """
    Diese Nachricht wird für drei Kommunikationsszenarien genutzt.

    Erstens werden damit Bekanntmachungen zu rechtskräftigen Entscheidungen
    zu den Verfahren der Musterfeststellungsklagen nach ZPO a.F. von den
    Gerichten an das BfJ verschickt. Zweitens informiert so das BfJ die
    Gerichte über die Veröffentlichung einer Musterfeststellungsklage nach
    ZPO a.F. bzw. einer Verbandsklage. Und drittens übermitteln so die
    Prozessbevollmächtigten des Antragstellers auf Erlass einer
    einstweiligen Verfügung das Datum der Zustellung an den Antragsgegner,
    die Abschrift der einstweiligen Verfügung und den Zustellungsnachweis
    nach § 6a Absatz 1 Satz 3 bis 5 UKlaG (i.V.m. § 8 Absatz 1 und 5 Satz 2
    UWG).
    """

    class Meta:
        name = (
            "nachricht.mfkreg.rechtskraftVeroeffentlichungZustellung.3100004"
        )
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
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
    fachdaten: NachrichtMfkregRechtskraftVeroeffentlichungZustellung3100004.Fachdaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        """
        :ivar datum_ereignis: Je nach Ereignis ist entweder das Datum
            der Rechtskraft einer Rechtsprechung zu einer
            Musterfeststellungsklage, das Datum der Veröffentlichung der
            Bekanntmachung oder das Datum der erfolgten Zustellung des
            Erlasses einer einstweiligen Verfügung mitzuteilen. Das
            Gericht teilt die Rechtskraft einer Rechtsprechung dem BfJ
            mit. Das BfJ teilt das Datum der Veröffentlichung im
            Klageregister mit. Der Prozessbevollmächtigte des
            Antragstellers auf Erlass einer einstweiligen Verfügung
            verschickt das Datum der erfolgten Zustellung, die Abschrift
            der einstweiligen Verfügung sowie den Zustellungsnachweis
            nach § 6a Absatz 1 Satz 3 bis 5 UKlaG (i.V.m. § 8 Absatz 1
            und 5 Satz 2 UWG).
        """

        datum_ereignis: XmlDate = field(
            metadata={
                "name": "datum.ereignis",
                "type": "Element",
                "required": True,
            }
        )


@dataclass(kw_only=True)
class NachrichtMfkregRegisterauszug3100007:
    """
    Diese Nachricht wird für den Registerauszug von
    Musterfeststellungsklagen nach ZPO a.F. und von Verbandsklagen genutzt.
    """

    class Meta:
        name = "nachricht.mfkreg.registerauszug.3100007"
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    fachdaten: NachrichtMfkregRegisterauszug3100007.Fachdaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        """
        :ivar art_auszug: Es ist der jeweilige Anforderungsgrund
            anzugeben, der durch das Gericht angefordert wurde.
        :ivar stichtag_auszug: Hier ist das Datum des Stichtags
            angegeben, zu dem der Registerauszug erstellt wurde.
        :ivar richtigkeit_vollstaendigkeit: Mit diesem Element wird
            bestätigt, dass zu allen Anmeldungen deren Richtigkeit und
            Vollständigkeit vom Verbraucher oder dessen Vertreter
            versichert wurden.Es werden nur solche Anmeldungen durch das
            BfJ übermittelt.
        :ivar register_auszuege:
        """

        art_auszug: CodeMfkregRegisterauszugsartTyp3 = field(
            metadata={
                "name": "art.auszug",
                "type": "Element",
                "required": True,
            }
        )
        stichtag_auszug: XmlDate = field(
            metadata={
                "name": "stichtag.auszug",
                "type": "Element",
                "required": True,
            }
        )
        richtigkeit_vollstaendigkeit: bool = field(
            metadata={
                "type": "Element",
                "required": True,
            }
        )
        register_auszuege: list[
            NachrichtMfkregRegisterauszug3100007.Fachdaten.RegisterAuszuege
        ] = field(
            default_factory=list,
            metadata={
                "name": "registerAuszuege",
                "type": "Element",
                "min_occurs": 1,
            },
        )

        @dataclass(kw_only=True)
        class RegisterAuszuege:
            """
            :ivar geschaeftszeichen_bf_j: Zu jeder Anmeldung im Register
                für Musterfeststellungsklagen gehört ein
                Geschäftszeichen des BfJ, mit der die Anmeldung
                eindeutig identifiziert ist.
            :ivar gegenstand_und_grund: Bei jeder Anmeldung muss der
                Gegenstand und Grund des Anspruchs oder des
                Rechtsverhältnisses vom Verbraucher gegenüber dem
                beklagten Unternehmen angegeben werden.
            :ivar betrag: Die Höhe des Anspruchs ist optional und wird
                in Euro angegeben.
            :ivar datum_anmeldung: Hier wird das Datum angegeben, an dem
                die Anmeldung im BfJ eingegangen ist.
            :ivar datum_ruecknahme: Hier wird das Datum angegeben, an
                dem die Anmeldung zurückgenommen wurde.
            :ivar aenderungshistorie: Sofern sich die Angaben der
                Beteiligten im Laufe des Verfahrens geändert haben (z.B.
                Name geändert), sind hier die Änderungen einzutragen.
            :ivar anmeldung_beteiligung: Hier sind die zugehörigen
                Beteiligtendaten der Anmeldung anzugeben.
                Zurückgenommene Anmeldungen sind in den Registerauszügen
                von Verbandsklagen nicht enthalten. Für jede Anmeldung
                gibt es einen Beteiligten, den Verbraucher oder das
                Unternehmen. Im Fall einer Rechtsnachfolge können auch
                mehrere Verbraucher als Beteiligte zur selben Anmeldung
                aufgeführt werden. Jeder Verbraucher kann zudem
                vertreten werden durch einen Rechtsbeistand oder einen
                sonstigen Vertreter. Unternehmen können zudem durch
                einen Insolvenzverwalter vertreten werden, zudem können
                Unternehmen eine Kontaktperson angeben.
            """

            geschaeftszeichen_bf_j: str = field(
                metadata={
                    "name": "geschaeftszeichen.BfJ",
                    "type": "Element",
                    "required": True,
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                }
            )
            gegenstand_und_grund: str = field(
                metadata={
                    "name": "gegenstandUndGrund",
                    "type": "Element",
                    "required": True,
                    "pattern": r"([ -~]|[¡-¬]|[®-ž]|[Ƈ-ƈ]|Ə|ƒ|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|ʰ|ʳ|[ʹ-ʺ]|[ʾ-ʿ]|ˆ|ˈ|ˌ|˜|ˢ|Ά|[Έ-Ί]|Ό|[Ύ-Ρ]|[Σ-ώ]|ᵈ|ᵗ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|[‘-‚]|[“-„]|[†-‡]|…|‰|[′-″]|[‹-›]|⁰|[⁴-⁹]|[ⁿ-₉]|€|™|∞|[≤-≥]|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                }
            )
            betrag: None | str = field(
                default=None,
                metadata={
                    "type": "Element",
                    "pattern": r"([ -~]|[¡-¬]|[®-ž]|[Ƈ-ƈ]|Ə|ƒ|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|ʰ|ʳ|[ʹ-ʺ]|[ʾ-ʿ]|ˆ|ˈ|ˌ|˜|ˢ|Ά|[Έ-Ί]|Ό|[Ύ-Ρ]|[Σ-ώ]|ᵈ|ᵗ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|[‘-‚]|[“-„]|[†-‡]|…|‰|[′-″]|[‹-›]|⁰|[⁴-⁹]|[ⁿ-₉]|€|™|∞|[≤-≥]|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            datum_anmeldung: XmlDate = field(
                metadata={
                    "name": "datum.anmeldung",
                    "type": "Element",
                    "required": True,
                }
            )
            datum_ruecknahme: None | XmlDate = field(
                default=None,
                metadata={
                    "name": "datum.ruecknahme",
                    "type": "Element",
                },
            )
            aenderungshistorie: None | str = field(
                default=None,
                metadata={
                    "type": "Element",
                    "pattern": r"([ -~]|[¡-¬]|[®-ž]|[Ƈ-ƈ]|Ə|ƒ|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|ʰ|ʳ|[ʹ-ʺ]|[ʾ-ʿ]|ˆ|ˈ|ˌ|˜|ˢ|Ά|[Έ-Ί]|Ό|[Ύ-Ρ]|[Σ-ώ]|ᵈ|ᵗ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|[‘-‚]|[“-„]|[†-‡]|…|‰|[′-″]|[‹-›]|⁰|[⁴-⁹]|[ⁿ-₉]|€|™|∞|[≤-≥]|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            anmeldung_beteiligung: list[TypeGdsBeteiligung] = field(
                default_factory=list,
                metadata={
                    "name": "anmeldung.beteiligung",
                    "type": "Element",
                    "min_occurs": 1,
                },
            )


@dataclass(kw_only=True)
class NachrichtMfkregRevision3100005:
    """
    Diese Nachricht wird für Bekanntmachungen der Revision im Verfahren zu
    Musterfeststellungsklagen nach ZPO a.F. sowie für Bekanntmachungen der
    Revision im Verfahren zu Verbandsklagen genutzt.
    """

    class Meta:
        name = "nachricht.mfkreg.revision.3100005"
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
    fachdaten: NachrichtMfkregRevision3100005.Fachdaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        """
        :ivar datum_revision: Bei der Bekanntmachung einer Revision ist
            das Datum der Einlegung der Revision anzugeben.
        :ivar gegenstand_revision: Hier kann beispielsweise angegeben
            werden, ob gegen das Abhilfegrund- oder das Abhilfeendurteil
            Revision eingelegt wurde.
        """

        datum_revision: XmlDate = field(
            metadata={
                "name": "datum.revision",
                "type": "Element",
                "required": True,
            }
        )
        gegenstand_revision: None | str = field(
            default=None,
            metadata={
                "name": "gegenstand.revision",
                "type": "Element",
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            },
        )


@dataclass(kw_only=True)
class NachrichtMfkregVergleichsaustritte3100008:
    """
    Diese Nachricht wird nur für die Vergleichsaustritte bei Verfahren zu
    Musterfeststellungsklagen nach ZPO a.F. genutzt.

    Diese Nachricht wird bei Verbandsklagen nicht genutzt.
    """

    class Meta:
        name = "nachricht.mfkreg.vergleichsaustritte.3100008"
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    fachdaten: NachrichtMfkregVergleichsaustritte3100008.Fachdaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        """
        :ivar vergleich_austritt: Die Geschäftsstelle des Gerichts
            protokolliert die Austritte aus einem Vergleich. Dazu
            gehören je Austritt das Geschäftszeichen der Anmeldung des
            BfJ sowie das Datum der Austrittserklärung.
        """

        vergleich_austritt: list[
            NachrichtMfkregVergleichsaustritte3100008.Fachdaten.VergleichAustritt
        ] = field(
            default_factory=list,
            metadata={
                "name": "vergleichAustritt",
                "type": "Element",
                "min_occurs": 1,
            },
        )

        @dataclass(kw_only=True)
        class VergleichAustritt:
            """
            :ivar geschaeftszeichen_bf_j: Hier wird das BfJ-
                Geschäftzeichen des Beteiligten angegeben.
            :ivar austrittsdatum: Hier wird das Datum des Austritts aus
                dem Vergleich angegeben.
            """

            geschaeftszeichen_bf_j: str = field(
                metadata={
                    "name": "geschaeftszeichen.BfJ",
                    "type": "Element",
                    "required": True,
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                }
            )
            austrittsdatum: XmlDate = field(
                metadata={
                    "type": "Element",
                    "required": True,
                }
            )


@dataclass(kw_only=True)
class NachrichtMfkregVerhandlungRegisterauszugsanforderung3100006:
    """
    Diese Nachricht wird nur für Bekanntmachungen zu Verhandlungen und
    Registerauszugsanforderungen zu Verfahren von Musterfeststellungsklagen
    nach ZPO a.F. oder zu Registerauszugsanforderungen zu Verfahren von
    Verbandsklagen genutzt.
    """

    class Meta:
        name = "nachricht.mfkreg.verhandlungRegisterauszugsanforderung.3100006"
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    fachdaten: NachrichtMfkregVerhandlungRegisterauszugsanforderung3100006.Fachdaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        """
        :ivar verhandlung: Unter der Sequenz werden Mitteilungen zum
            Beginn der Verhandlung des Musterfeststellungsverfahrens
            angegeben werden.
        :ivar registerauszug: Unter der Sequenz kann angegeben werden,
            ob ein Auszug beim Register angefordert wird. Es ist der
            jeweilige Anforderungsgrund anzugeben.
        """

        verhandlung: (
            None
            | NachrichtMfkregVerhandlungRegisterauszugsanforderung3100006.Fachdaten.Verhandlung
        ) = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )
        registerauszug: (
            None
            | NachrichtMfkregVerhandlungRegisterauszugsanforderung3100006.Fachdaten.Registerauszug
        ) = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )

        @dataclass(kw_only=True)
        class Verhandlung:
            """
            :ivar termin_stattgefunden: Es wird angegeben, ob der erste
                Termin stattfgefunden hat.
            :ivar datum_termin: Sofern der erste Termin stattgefunden
                hat, ist hier das Datum des Termins anzugeben.
            :ivar verhandlung_stattgefunden: Es wird angegeben, ob die
                mündliche Verhandlung begonnen wurde.
            :ivar datum_verhandlung: Sofern die mündliche Verhandlung
                begonnen wurde, ist hier das Datum des Beginns der
                mündlichen Verhandlung anzugeben.
            """

            termin_stattgefunden: bool = field(
                metadata={
                    "name": "terminStattgefunden",
                    "type": "Element",
                    "required": True,
                }
            )
            datum_termin: None | XmlDate = field(
                default=None,
                metadata={
                    "name": "datum.termin",
                    "type": "Element",
                },
            )
            verhandlung_stattgefunden: bool = field(
                metadata={
                    "name": "verhandlungStattgefunden",
                    "type": "Element",
                    "required": True,
                }
            )
            datum_verhandlung: None | XmlDate = field(
                default=None,
                metadata={
                    "name": "datum.verhandlung",
                    "type": "Element",
                },
            )

        @dataclass(kw_only=True)
        class Registerauszug:
            auszug_anfordern: bool = field(
                metadata={
                    "name": "auszugAnfordern",
                    "type": "Element",
                    "required": True,
                }
            )
            art_auszug: CodeMfkregRegisterauszugsartTyp3 = field(
                metadata={
                    "name": "art.auszug",
                    "type": "Element",
                    "required": True,
                }
            )


@dataclass(kw_only=True)
class NachrichtMfkregZurueckweisungVeroeffentlichung3100009:
    """
    Diese Nachricht wird für die Zurückweisung von Veröffentlichungen zu
    Musterfeststellungsklagen nach ZPO a.F. und für die Zurückweisung von
    Veröffentlichungen zu Verbandsklagen genutzt.
    """

    class Meta:
        name = "nachricht.mfkreg.zurueckweisungVeroeffentlichung.3100009"
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    fachdaten: NachrichtMfkregZurueckweisungVeroeffentlichung3100009.Fachdaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        """
        :ivar grund_zurueckweisung: Es ist anzugeben, welche Daten, die
            für die Veröffentlichung im
            Musterfeststellungsklagenregister bzw. im Klageregister
            notwendig sind, nicht durch das zuständige Gericht
            übermittelt bzw. nicht schlüssig angegeben worden sind,
            sodass eine Veröffentlichung durch das BfJ zurückgewiesen
            werden muss.
        """

        grund_zurueckweisung: str = field(
            metadata={
                "name": "grund.zurueckweisung",
                "type": "Element",
                "required": True,
                "pattern": r"([ -~]|[¡-¬]|[®-ž]|[Ƈ-ƈ]|Ə|ƒ|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|ʰ|ʳ|[ʹ-ʺ]|[ʾ-ʿ]|ˆ|ˈ|ˌ|˜|ˢ|Ά|[Έ-Ί]|Ό|[Ύ-Ρ]|[Σ-ώ]|ᵈ|ᵗ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|[‘-‚]|[“-„]|[†-‡]|…|‰|[′-″]|[‹-›]|⁰|[⁴-⁹]|[ⁿ-₉]|€|™|∞|[≤-≥]|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            }
        )


@dataclass(kw_only=True)
class NachrichtMfkregBeendigungRechtskraft3100003:
    """
    Diese Nachricht wird sowohl für Bekanntmachungen der Beendigung der
    Verfahren von Musterfeststellungsklagen nach ZPO a.F. als auch für
    Bekanntmachungen der Beendigung der Verfahren von Unterlassungsklagen
    und einstweiligen Verfügungen nach § 6a UKlaG (i.V.m. § 8 Absatz 1 und
    5 Satz 2 UWG) genutzt.

    Nachricht zur Übermittlung des Formulars 5.
    """

    class Meta:
        name = "nachricht.mfkreg.beendigungRechtskraft.3100003"
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
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
    fachdaten: NachrichtMfkregBeendigungRechtskraft3100003.Fachdaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        """
        :ivar datum_verfahrensende: Hier ist das Datum der Beendigung
            des Verbandsklageverfahrens anzugeben. Das Datum ist
            ungleich zum Erstellungszeitpunkt der XJustiz-Nachricht.
        :ivar verfahrensende_art: Hier wird angegeben, durch welche Art
            das Verfahren beendet worden ist. Für
            Musterfeststellungsverfahren nach ZPO a.F., Verbandsklagen,
            Unterlassungsklagen und einstweilige Verfügungen sind alle
            sieben Optionen (auch mehrere miteinander kombiniert)
            möglich.
        :ivar datum_eintritt_rechtskraft:
        :ivar teilrechtskraft_entscheidung: Dieses Attribut betrifft nur
            Musterfeststellungsklagen nach ZPO a.F. Wenn eine BGH-
            Entscheidung Teilrechtskraft hat, kann das hier angegeben
            werden. Das Datum ist identisch mit dem Datum des
            Verfahrensendes (s.o.). Die Angabe der Teilrechtskraft
            entfällt bei Verbandsklagen.
        :ivar beschlussinhalt: Dieses Attribut betrifft nur
            Musterfeststellungsklagen nach ZPO a.F. Es sind die
            bekanntzumachenden Inhalte des Beschlusses, des Vergleichs
            etc., der/ die zur Beendigung des Verfahrens geführt hat,
            anzugeben. Diese Bekanntmachungstexte entfallen bei
            Verbandsklagen, weil sie da gesondert übertragen werden.
        """

        datum_verfahrensende: XmlDate = field(
            metadata={
                "name": "datum.verfahrensende",
                "type": "Element",
                "required": True,
            }
        )
        verfahrensende_art: NachrichtMfkregBeendigungRechtskraft3100003.Fachdaten.VerfahrensendeArt = field(
            metadata={
                "name": "verfahrensendeArt",
                "type": "Element",
                "required": True,
            }
        )
        datum_eintritt_rechtskraft: None | XmlDate = field(
            default=None,
            metadata={
                "name": "datumEintrittRechtskraft",
                "type": "Element",
            },
        )
        teilrechtskraft_entscheidung: None | str = field(
            default=None,
            metadata={
                "name": "teilrechtskraftEntscheidung",
                "type": "Element",
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            },
        )
        beschlussinhalt: list[TypeMfkregBekanntmachungstexte] = field(
            default_factory=list,
            metadata={
                "type": "Element",
            },
        )

        @dataclass(kw_only=True)
        class VerfahrensendeArt:
            beendigung_urteil: bool = field(
                metadata={
                    "name": "beendigungUrteil",
                    "type": "Element",
                    "required": True,
                }
            )
            beendigung_beschluss: bool = field(
                metadata={
                    "name": "beendigungBeschluss",
                    "type": "Element",
                    "required": True,
                }
            )
            beendigung_vergleichsbeschluss: bool = field(
                metadata={
                    "name": "beendigungVergleichsbeschluss",
                    "type": "Element",
                    "required": True,
                }
            )
            beendigung_klageruecknahme: bool = field(
                metadata={
                    "name": "beendigungKlageruecknahme",
                    "type": "Element",
                    "required": True,
                }
            )
            beendigung_rechtsmittelruecknahme: bool = field(
                metadata={
                    "name": "beendigungRechtsmittelruecknahme",
                    "type": "Element",
                    "required": True,
                }
            )
            beendigung_erledigung_rechtsstreit: bool = field(
                metadata={
                    "name": "beendigungErledigungRechtsstreit",
                    "type": "Element",
                    "required": True,
                }
            )
            sonstige_beendigung: bool = field(
                metadata={
                    "name": "sonstigeBeendigung",
                    "type": "Element",
                    "required": True,
                }
            )


@dataclass(kw_only=True)
class NachrichtMfkregBerichtigungsbeschluss3100010:
    """
    Diese Nachricht wird nur für Bekanntmachungen der
    Berichtigungsbeschlüsse von Musterfeststellungsklagen nach ZPO a.F., zu
    Verbandsklagen nach VDuG und zu einstweiligen Verfügungen und
    Unterlassungsklagen nach § 6a UKlaG (i.V.m. § 8 Absatz 1 und 5 Satz 2
    UWG) genutzt.
    """

    class Meta:
        name = "nachricht.mfkreg.berichtigungsbeschluss.3100010"
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
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
    fachdaten: NachrichtMfkregBerichtigungsbeschluss3100010.Fachdaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        """
        :ivar datum_bekanntmachung: Es ist das Datum der zu
            berichtigenden öffentlichen Bekanntmachung anzugeben.
        :ivar datum_berichtigungsbeschluss:
        :ivar art_der_oeffentlichen_bekanntmachung:
        :ivar beschlussinhalt: Ergeht ein Berichtigungsbeschluss, wird
            dieser Beschluss stets in der Form im Klageregister bekannt
            gemacht, in der er vom Gericht übermittelt wurde. Das
            Gericht kann den Berichtigungsbeschluss und/ oder einen
            konsolidierten Text, der die berichtigten Inhalte enthält,
            an das BfJ übermitteln.
        :ivar textstreichung:
        :ivar textersetzung:
        :ivar textergaenzung:
        :ivar geaenderte_fassung:
        """

        datum_bekanntmachung: XmlDate = field(
            metadata={
                "name": "datum.bekanntmachung",
                "type": "Element",
                "required": True,
            }
        )
        datum_berichtigungsbeschluss: XmlDate = field(
            metadata={
                "name": "datum.berichtigungsbeschluss",
                "type": "Element",
                "required": True,
            }
        )
        art_der_oeffentlichen_bekanntmachung: CodeMfkregArtDerOeffentlichenBekanntmachungTyp3 = field(
            metadata={
                "name": "artDerOeffentlichenBekanntmachung",
                "type": "Element",
                "required": True,
            }
        )
        beschlussinhalt: list[TypeMfkregBekanntmachungstexte] = field(
            default_factory=list,
            metadata={
                "type": "Element",
            },
        )
        textstreichung: None | TypeMfkregTextanpassung = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )
        textersetzung: None | str = field(
            default=None,
            metadata={
                "type": "Element",
                "pattern": r"([ -~]|[¡-¬]|[®-ž]|[Ƈ-ƈ]|Ə|ƒ|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|ʰ|ʳ|[ʹ-ʺ]|[ʾ-ʿ]|ˆ|ˈ|ˌ|˜|ˢ|Ά|[Έ-Ί]|Ό|[Ύ-Ρ]|[Σ-ώ]|ᵈ|ᵗ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|[‘-‚]|[“-„]|[†-‡]|…|‰|[′-″]|[‹-›]|⁰|[⁴-⁹]|[ⁿ-₉]|€|™|∞|[≤-≥]|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            },
        )
        textergaenzung: None | TypeMfkregTextanpassung = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )
        geaenderte_fassung: None | str = field(
            default=None,
            metadata={
                "name": "geaenderteFassung",
                "type": "Element",
                "pattern": r"([ -~]|[¡-¬]|[®-ž]|[Ƈ-ƈ]|Ə|ƒ|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|ʰ|ʳ|[ʹ-ʺ]|[ʾ-ʿ]|ˆ|ˈ|ˌ|˜|ˢ|Ά|[Έ-Ί]|Ό|[Ύ-Ρ]|[Σ-ώ]|ᵈ|ᵗ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|[‘-‚]|[“-„]|[†-‡]|…|‰|[′-″]|[‹-›]|⁰|[⁴-⁹]|[ⁿ-₉]|€|™|∞|[≤-≥]|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            },
        )


@dataclass(kw_only=True)
class NachrichtMfkregHinweiseZwischenentscheidung3100002:
    """
    Diese Nachricht wird nur für Bekanntmachungen von Hinweisen und
    Zwischenentscheidungen zu Musterfeststellungsklagen nach ZPO a.F.
    genutzt.

    Nachricht zur Übermittlung der Formulare 3 und 4.
    """

    class Meta:
        name = "nachricht.mfkreg.hinweiseZwischenentscheidung.3100002"
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
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
    fachdaten: NachrichtMfkregHinweiseZwischenentscheidung3100002.Fachdaten = (
        field(
            metadata={
                "type": "Element",
                "required": True,
            }
        )
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        """
        :ivar datum_ereignis: Bei der Bekanntmachung von Hinweisen oder
            Zwischenentscheidungen ist das Datum der jeweiligen
            Ereignisse anzugeben. Das Datum ist in der Regel ungleich
            zum Erstellungszeitpunkt der XJustiz-Nachricht.
        :ivar auswahl_verlinkung:
        :ivar feststellungsziele_verweis: Unter dieser Sequenz kann
            abgebildet werden, ob eine Verlinkung der bekanntzumachenden
            Hinweise oder Zwischenentscheidungen zum Abhilfeantrag bzw.
            zu den Feststellungszielen erwünscht ist und wie die
            Verlinkung platziert werden soll. Es ist anzugeben, ob der
            Abhilfeantrag bzw. die Feststellungsziele ergänzt,
            modifiziert oder ergänzt und modifiziert worden sind.
        :ivar beschlussinhalt: Bei der Bekanntmachung von Hinweisen oder
            Zwischenentscheidungen kann angegeben werden, ob die
            jeweiligen Zwischenstände mit einem Termin oder einem
            Feststellungsziel verknüpft werden soll.
        """

        datum_ereignis: XmlDate = field(
            metadata={
                "name": "datum.ereignis",
                "type": "Element",
                "required": True,
            }
        )
        auswahl_verlinkung: (
            None
            | NachrichtMfkregHinweiseZwischenentscheidung3100002.Fachdaten.AuswahlVerlinkung
        ) = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )
        feststellungsziele_verweis: (
            None
            | NachrichtMfkregHinweiseZwischenentscheidung3100002.Fachdaten.FeststellungszieleVerweis
        ) = field(
            default=None,
            metadata={
                "name": "feststellungszieleVerweis",
                "type": "Element",
            },
        )
        beschlussinhalt: list[
            NachrichtMfkregHinweiseZwischenentscheidung3100002.Fachdaten.Beschlussinhalt
        ] = field(
            default_factory=list,
            metadata={
                "type": "Element",
            },
        )

        @dataclass(kw_only=True)
        class AuswahlVerlinkung:
            keine_verlinkung: bool = field(
                init=False,
                default=True,
                metadata={
                    "name": "keineVerlinkung",
                    "type": "Element",
                    "required": True,
                },
            )
            verlinkung: XmlDate = field(
                metadata={
                    "type": "Element",
                    "required": True,
                }
            )

        @dataclass(kw_only=True)
        class FeststellungszieleVerweis:
            ergaenzt: bool = field(
                metadata={
                    "type": "Element",
                    "required": True,
                }
            )
            modifiziert: bool = field(
                metadata={
                    "type": "Element",
                    "required": True,
                }
            )

        @dataclass(kw_only=True)
        class Beschlussinhalt:
            """
            :ivar text_bekanntmachung: Es sind die bekanntzumachenden
                Inhalte als Freitext anzugeben. Bei der Bekanntmachung
                einer Musterfeststellungsklage nach ZPO a.F. sind hier
                zwingend die 'Feststellungsziele', die 'kurze
                Darstellung des Lebenssachverhalts' sowie vier
                Rechtsbelehrungen anzugeben. Bei der Bekanntmachung
                einer Verbandsklage sind hier zwingend Angaben zu
                'Abhilfeantrag / Feststellungsziele' zu erfassen sowie
                die 'kurze Darstellung des Lebenssachverhalts' und drei
                Rechtsbelehrungen anzugeben. Für die Rechtsbelehrungen
                stehen jeweils Default-Texte zur Verfügung, die bei
                Bedarf angepasst werden können. Bekanntmachungen von
                Unterlassungsklagen und von einstweiligen Verfügungen
                enthalten jeweils nur einen Bekanntmachungstext zu der
                behaupteten Zuwiderhandlung, die Anlass des Antrags auf
                Erlass einer einstweiligen Verfügung ist bzw. gegen die
                die Klage gerichtet ist. Es sind die passenden
                Gliederungspunkte der Bekanntmachung aus der Codeliste
                auszuwählen. Bei der Bekanntmachung des Antrags auf
                Erlass einer einstweiligen Verfügung, der dem
                Antragsgegner zugestellt worden ist, sind das Datum des
                Eingangs des Antrags bei Gericht und das Datum der
                Zustellung des Antrags beim Antragsgegner unverzüglich
                bekanntzumachen. Wurde die einstweilige Verfügung
                erlassen, ohne dass der Antrag auf Erlass der
                einstweiligen Verfügung dem Antragsgegner vorher
                zugestellt worden ist, tritt an die Stelle der
                Bekanntmachung des Datums der Zustellung des Antrags das
                Datum des Erlasses der einstweiligen Verfügung. Bei der
                Bekanntmachung der Unterlassungsklage müssen das Datum
                der Anhängigkeit der Klage (= Eingang der Klage bei
                Gericht) und das Datum der Rechtshängigkeit der Klage (=
                Zustellung der Klage an den Beklagten) übermittelt
                werden. Sowohl für Unterlassungsklagen als auch für
                einstweilige Verfügungen muss mindestens ein Grund für
                die Erhebung der Klage bzw. die Stellung des Antrags
                angegeben werden: Verstoß gegen Normen des Gesetzes
                gegen den unlauteren Wettbewerb oder Verstoß gegen
                Normen des Unterlassungsklagengesetzes (oder beides).
            """

            text_bekanntmachung: TypeMfkregBekanntmachungstexte = field(
                metadata={
                    "name": "text.bekanntmachung",
                    "type": "Element",
                    "required": True,
                }
            )


@dataclass(kw_only=True)
class NachrichtMfkregKlagebekanntmachungTerminbestimmung3100001:
    """
    Diese Nachricht wird sowohl für Bekanntmachungen und Terminbestimmungen
    von Musterfeststellungsklagen nach ZPO a.F. und von Verbandsklagen nach
    VDuG als auch für Bekanntmachungen von Unterlassungsklagen und
    einstweiligen Verfügungen nach § 6a UKlaG (i.V.m. § 8 Absatz 1 und 5
    Satz 2 UWG) genutzt.

    Nachricht zur Übermittlung der Formulare 1 und 2.
    """

    class Meta:
        name = "nachricht.mfkreg.klagebekanntmachungTerminbestimmung.3100001"
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
    fachdaten: (
        None
        | NachrichtMfkregKlagebekanntmachungTerminbestimmung3100001.Fachdaten
    ) = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        """
        :ivar auswahl_klage_verfuegung_terminsbestimmung:
        :ivar text_bekanntmachung: Es sind die bekanntzumachenden
            Inhalte als Freitext anzugeben. Bei der Bekanntmachung einer
            Musterfeststellungsklage nach ZPO a.F. sind hier zwingend
            die "Feststellungsziele", die "kurze Darstellung des
            Lebenssachverhalts" sowie vier Rechtsbelehrungen anzugeben.
            Bei der Bekanntmachung einer Verbandsklage sind hier
            zwingend Angaben zu "Abhilfeantrag / Feststellungsziele" zu
            erfassen sowie die "kurze Darstellung des
            Lebenssachverhalts" und drei Rechtsbelehrungen anzugeben.
            Für die Rechtsbelehrungen stehen jeweils Default-Texte zur
            Verfügung, die bei Bedarf angepasst werden können.
            Bekanntmachungen von Unterlassungsklagen und von
            einstweiligen Verfügungen enthalten jeweils nur einen
            Bekanntmachungstext zu der behaupteten Zuwiderhandlung, die
            Anlass des Antrags auf Erlass einer einstweiligen Verfügung
            ist bzw. gegen die die Klage gerichtet ist. Es sind die
            passenden Gliederungspunkte der Bekanntmachung aus der
            Codeliste auszuwählen. Bei der Bekanntmachung des Antrags
            auf Erlass einer einstweiligen Verfügung, der dem
            Antragsgegner zugestellt worden ist, sind das Datum des
            Eingangs des Antrags bei Gericht und das Datum der
            Zustellung des Antrags beim Antragsgegner unverzüglich
            bekanntzumachen. Wurde die einstweilige Verfügung erlassen,
            ohne dass der Antrag auf Erlass der einstweiligen Verfügung
            dem Antragsgegner vorher zugestellt worden ist, tritt an die
            Stelle der Bekanntmachung des Datums der Zustellung des
            Antrags das Datum des Erlasses der einstweiligen Verfügung.
            Bei der Bekanntmachung der Unterlassungsklage müssen das
            Datum der Anhängigkeit der Klage (= Eingang der Klage bei
            Gericht) und das Datum der Rechtshängigkeit der Klage (=
            Zustellung der Klage an den Beklagten) übermittelt werden.
            Sowohl für Unterlassungsklagen als auch für einstweilige
            Verfügungen muss mindestens ein Grund für die Erhebung der
            Klage bzw. die Stellung des Antrags angegeben werden:
            Verstoß gegen Normen des Gesetzes gegen den unlauteren
            Wettbewerb oder Verstoß gegen Normen des
            Unterlassungsklagengesetzes (oder beides).
        """

        auswahl_klage_verfuegung_terminsbestimmung: NachrichtMfkregKlagebekanntmachungTerminbestimmung3100001.Fachdaten.AuswahlKlageVerfuegungTerminsbestimmung = field(
            metadata={
                "name": "auswahl_klage.verfuegung.terminsbestimmung",
                "type": "Element",
                "required": True,
            }
        )
        text_bekanntmachung: list[TypeMfkregBekanntmachungstexte] = field(
            default_factory=list,
            metadata={
                "name": "text.bekanntmachung",
                "type": "Element",
            },
        )

        @dataclass(kw_only=True)
        class AuswahlKlageVerfuegungTerminsbestimmung:
            unterlassungsklage_einstweilige_verfuegung: (
                None
                | NachrichtMfkregKlagebekanntmachungTerminbestimmung3100001.Fachdaten.AuswahlKlageVerfuegungTerminsbestimmung.UnterlassungsklageEinstweiligeVerfuegung
            ) = field(
                default=None,
                metadata={
                    "name": "unterlassungsklage.einstweiligeVerfuegung",
                    "type": "Element",
                },
            )
            abhilfeklage_musterfeststellungsklage: (
                None
                | NachrichtMfkregKlagebekanntmachungTerminbestimmung3100001.Fachdaten.AuswahlKlageVerfuegungTerminsbestimmung.AbhilfeklageMusterfeststellungsklage
            ) = field(
                default=None,
                metadata={
                    "name": "abhilfeklage.musterfeststellungsklage",
                    "type": "Element",
                },
            )
            terminbestimmung: (
                None
                | NachrichtMfkregKlagebekanntmachungTerminbestimmung3100001.Fachdaten.AuswahlKlageVerfuegungTerminsbestimmung.Terminbestimmung
            ) = field(
                default=None,
                metadata={
                    "type": "Element",
                },
            )

            @dataclass(kw_only=True)
            class UnterlassungsklageEinstweiligeVerfuegung:
                datum_eingang: None | XmlDate = field(
                    default=None,
                    metadata={
                        "name": "datum.eingang",
                        "type": "Element",
                    },
                )
                datum_erlass: None | XmlDate = field(
                    default=None,
                    metadata={
                        "name": "datum.erlass",
                        "type": "Element",
                    },
                )
                datum_zustellung: None | XmlDate = field(
                    default=None,
                    metadata={
                        "name": "datum.zustellung",
                        "type": "Element",
                    },
                )
                rechtsgrundlage_uwg: None | bool = field(
                    default=None,
                    metadata={
                        "name": "rechtsgrundlage.UWG",
                        "type": "Element",
                    },
                )
                rechtsgrundlage_ukla_g: None | bool = field(
                    default=None,
                    metadata={
                        "name": "rechtsgrundlage.UKlaG",
                        "type": "Element",
                    },
                )

            @dataclass(kw_only=True)
            class AbhilfeklageMusterfeststellungsklage:
                klageart: CodeMfkregKlageartTyp3 = field(
                    metadata={
                        "type": "Element",
                        "required": True,
                    }
                )
                datum_anhaengigkeit: XmlDate = field(
                    metadata={
                        "name": "datum.anhaengigkeit",
                        "type": "Element",
                        "required": True,
                    }
                )
                rechtshaengigkeit: list[
                    NachrichtMfkregKlagebekanntmachungTerminbestimmung3100001.Fachdaten.AuswahlKlageVerfuegungTerminsbestimmung.AbhilfeklageMusterfeststellungsklage.Rechtshaengigkeit
                ] = field(
                    default_factory=list,
                    metadata={
                        "type": "Element",
                        "min_occurs": 1,
                    },
                )

                @dataclass(kw_only=True)
                class Rechtshaengigkeit:
                    """
                    :ivar datum:
                    :ivar ref_beteiligter: In diesem Element ist auf den
                        Beklagten oder Antragsgegner zu referenzieren.
                        Hierfür wird jeweils auf eine Person, die in den
                        Grunddaten angegeben wurde, referenziert.
                    """

                    datum: XmlDate = field(
                        metadata={
                            "type": "Element",
                            "required": True,
                        }
                    )
                    ref_beteiligter: TypeGdsRefRollennummer = field(
                        metadata={
                            "name": "ref.beteiligter",
                            "type": "Element",
                            "required": True,
                        }
                    )

            @dataclass(kw_only=True)
            class Terminbestimmung:
                bekanntmachung_entscheidung: CodeMfkregBekanntmachungsartTyp3 = field(
                    metadata={
                        "name": "bekanntmachungEntscheidung",
                        "type": "Element",
                        "required": True,
                    }
                )


@dataclass(kw_only=True)
class NachrichtMfkregUmsetzungInsolvenzverfahren3100011:
    """
    In dieser Nachricht werden sechs Bekanntmachungsarten kombiniert: der
    Beschluss über die Eröffnung eines Umsetzungsverfahrens der Beschluss
    über die Feststellung der Beendigung des Umsetzungsverfahrens die
    Bestellung des Sachwalters die für begründet erklärte Ablehnung des
    Sachwalters die Entlassung des Sachwalters der Beschluss über die
    Eröffnung eines Insolvenzverfahrens über das Vermögen des Unternehmers.
    """

    class Meta:
        name = "nachricht.mfkreg.umsetzung.insolvenzverfahren.3100011"
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
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
    fachdaten: NachrichtMfkregUmsetzungInsolvenzverfahren3100011.Fachdaten = (
        field(
            metadata={
                "type": "Element",
                "required": True,
            }
        )
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        auswahl_umsetzung_insolvenzverfahren: NachrichtMfkregUmsetzungInsolvenzverfahren3100011.Fachdaten.AuswahlUmsetzungInsolvenzverfahren = field(
            metadata={
                "name": "auswahl_umsetzung.insolvenzverfahren",
                "type": "Element",
                "required": True,
            }
        )
        beschlussinhalt: list[TypeMfkregBekanntmachungstexte] = field(
            default_factory=list,
            metadata={
                "type": "Element",
            },
        )

        @dataclass(kw_only=True)
        class AuswahlUmsetzungInsolvenzverfahren:
            umsetzungsverfahren: (
                None
                | NachrichtMfkregUmsetzungInsolvenzverfahren3100011.Fachdaten.AuswahlUmsetzungInsolvenzverfahren.Umsetzungsverfahren
            ) = field(
                default=None,
                metadata={
                    "type": "Element",
                },
            )
            bestellung_sachwalter: (
                None
                | NachrichtMfkregUmsetzungInsolvenzverfahren3100011.Fachdaten.AuswahlUmsetzungInsolvenzverfahren.BestellungSachwalter
            ) = field(
                default=None,
                metadata={
                    "name": "bestellungSachwalter",
                    "type": "Element",
                },
            )
            ablehnung_entlassung_sachwalter: (
                None
                | NachrichtMfkregUmsetzungInsolvenzverfahren3100011.Fachdaten.AuswahlUmsetzungInsolvenzverfahren.AblehnungEntlassungSachwalter
            ) = field(
                default=None,
                metadata={
                    "name": "ablehnungEntlassungSachwalter",
                    "type": "Element",
                },
            )
            insolvenzverfahren: (
                None
                | NachrichtMfkregUmsetzungInsolvenzverfahren3100011.Fachdaten.AuswahlUmsetzungInsolvenzverfahren.Insolvenzverfahren
            ) = field(
                default=None,
                metadata={
                    "type": "Element",
                },
            )

            @dataclass(kw_only=True)
            class Umsetzungsverfahren:
                datum_beschluss: XmlDate = field(
                    metadata={
                        "name": "datumBeschluss",
                        "type": "Element",
                        "required": True,
                    }
                )

            @dataclass(kw_only=True)
            class BestellungSachwalter:
                """
                :ivar datum_bestellung:
                :ivar name: Der Sachwalter bzw. die Sachwalterin wird
                    nicht als Beteiligte, sondern als Freitextfeld
                    modelliert, um alle Möglichkeiten berücksichtigen zu
                    können. Ein Sachwalter kann eine natürliche Person
                    sein, z.B. ein Jurist, ein Wirtschaftsprüfer oder
                    ein Steuerberater. Es ist aber nicht auszuschließen,
                    dass eine Kanzlei etc. zur Sachwalterin bestellt
                    wird.
                """

                datum_bestellung: XmlDate = field(
                    metadata={
                        "name": "datumBestellung",
                        "type": "Element",
                        "required": True,
                    }
                )
                name: str = field(
                    metadata={
                        "type": "Element",
                        "required": True,
                        "pattern": r"([ -~]|[¡-¬]|[®-ž]|[Ƈ-ƈ]|Ə|ƒ|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|ʰ|ʳ|[ʹ-ʺ]|[ʾ-ʿ]|ˆ|ˈ|ˌ|˜|ˢ|Ά|[Έ-Ί]|Ό|[Ύ-Ρ]|[Σ-ώ]|ᵈ|ᵗ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|[‘-‚]|[“-„]|[†-‡]|…|‰|[′-″]|[‹-›]|⁰|[⁴-⁹]|[ⁿ-₉]|€|™|∞|[≤-≥]|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    }
                )

            @dataclass(kw_only=True)
            class AblehnungEntlassungSachwalter:
                datum_beschluss: XmlDate = field(
                    metadata={
                        "name": "datumBeschluss",
                        "type": "Element",
                        "required": True,
                    }
                )

            @dataclass(kw_only=True)
            class Insolvenzverfahren:
                datum_eroeffnung: XmlDate = field(
                    metadata={
                        "name": "datumEroeffnung",
                        "type": "Element",
                        "required": True,
                    }
                )
                insolvenzgericht: str = field(
                    metadata={
                        "type": "Element",
                        "required": True,
                        "pattern": r"([ -~]|[¡-£]|¥|[§-¬]|[®-·]|[¹-»]|[¿-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    }
                )
                aktenzeichen_insolvenzverfahren: str = field(
                    metadata={
                        "name": "aktenzeichenInsolvenzverfahren",
                        "type": "Element",
                        "required": True,
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    }
                )
