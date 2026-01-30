from __future__ import annotations

from dataclasses import dataclass, field

from xsdata.models.datatype import XmlDate

from xjustiz.model_gen.xjustiz_0000_grunddatensatz_3_6 import (
    TypeGdsBasisnachricht,
    TypeGdsGrunddaten,
    TypeGdsNachrichtenkopf,
    TypeGdsSchriftgutobjekte,
)
from xjustiz.model_gen.xjustiz_0010_cl_allgemein_3_7 import (
    CodeFehlerTyp4,
    CodeGdsAuskunftVollstreckungssachenFehlerTyp3,
    CodeGdsFehlercodesTyp3,
    CodeGdsInsoIriFehlercodeTyp3,
    CodeGdsStrafBzrVerarbeitungsbestaetigungTyp3,
    CodeGdsVagFehlerTyp3,
)

__NAMESPACE__ = "http://www.xjustiz.de"


@dataclass(kw_only=True)
class NachrichtGdsBasisnachricht0005006:
    """
    Diese Nachricht kann für alle Kommunikationsszenarien, bei denen keine
    Schriftgutobjekte übermittelt werden und für die keine spezielle
    Fachnachricht bereitsteht, genutzt werden.
    """

    class Meta:
        name = "nachricht.gds.basisnachricht.0005006"
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    grunddaten: None | TypeGdsGrunddaten = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass(kw_only=True)
class NachrichtGdsFehler0005007:
    class Meta:
        name = "nachricht.gds.fehler.0005007"
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    grunddaten: None | TypeGdsGrunddaten = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    fachdaten: NachrichtGdsFehler0005007.Fachdaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        fehler: list[NachrichtGdsFehler0005007.Fachdaten.Fehler] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "min_occurs": 1,
            },
        )

        @dataclass(kw_only=True)
        class Fehler:
            """
            :ivar auswahl_fehlercode:
            :ivar zusatzinformation: In diesem Element können weitere
                Informationen zum Fehler angegeben werden. Dies kann zum
                Beispiel bei einem Validierungsfehler die Meldung vom
                Parser oder die Fehlerbeschreibung bei Auswahl des
                Wertes "Sonstiger Fehler" sein. Es dürfen nur maximal
                2000 Zeichen angegeben werden.
            :ivar auswahl_status_weiterverarbeitung: In diesem Element
                kann angegeben werden, ob die Nachricht trotz des
                Fehlers bearbeitet wird oder ob die Übermittlung einer
                fehlerfreien XJustiz-Nachricht erforderlich ist.
            """

            auswahl_fehlercode: NachrichtGdsFehler0005007.Fachdaten.Fehler.AuswahlFehlercode = field(
                metadata={
                    "type": "Element",
                    "required": True,
                }
            )
            zusatzinformation: None | str = field(
                default=None,
                metadata={
                    "type": "Element",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|ƒ|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|ʰ|ʳ|[ʹ-ʺ]|[ʾ-ʿ]|ˆ|ˈ|ˌ|˜|ˢ|Ά|[Έ-Ί]|Ό|[Ύ-Ρ]|[Σ-ώ]|Ѝ|[А-Ъ]|Ь|[Ю-ъ]|ь|[ю-я]|ѝ|ᵈ|ᵗ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|[‘-‚]|[“-„]|[†-‡]|…|‰|[′-″]|[‹-›]|⁰|[⁴-⁹]|[ⁿ-₉]|€|™|∞|[≤-≥]|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            auswahl_status_weiterverarbeitung: (
                None
                | NachrichtGdsFehler0005007.Fachdaten.Fehler.AuswahlStatusWeiterverarbeitung
            ) = field(
                default=None,
                metadata={
                    "name": "auswahl_statusWeiterverarbeitung",
                    "type": "Element",
                },
            )

            @dataclass(kw_only=True)
            class AuswahlFehlercode:
                """
                :ivar fehlercode: Dieses Element ist zu verwenden, wenn
                    keine fach- oder anwendungsspezifische Codeliste
                    abgestimmt ist.
                :ivar anwendungsspezifischer_fehler: Mit diesem Element
                    kann auf Codelisten zurückgegriffen werden, die für
                    bestimmte IT-Anwendungen abgestimmt wurden, jedoch
                    (noch) nicht in den XJustiz-Standards aufgenommen
                    werden konnten. In diesem Fall muss die Kennung und
                    Version der verwendeten Codeliste bei der
                    Nachrichtenübermittlung angegeben werden. Zudem muss
                    sichergestellt sein, dass der Empfänger Kenntnis von
                    der Codeliste hat und auf sie zugreifen kann.
                :ivar vag_fehler: Zu verwenden für
                    Kommunikationsszenarien des Fachmoduls
                    Versorgungsausgleich.
                :ivar inso_iri_fehler: Zu verwenden für
                    Kommunikationsszenarien des Fachmoduls Insolvenz.
                :ivar auskunft_vollstreckungssachen_fehler:
                    Fehlermeldung für die Kommunikation bei
                    Auskunftsersuchen im Rahmen von
                    Vollstreckungssachen. z.B. für Fachmodule eZoll und
                    ZPO Fremdauskunft
                """

                fehlercode: None | CodeGdsFehlercodesTyp3 = field(
                    default=None,
                    metadata={
                        "type": "Element",
                    },
                )
                anwendungsspezifischer_fehler: None | CodeFehlerTyp4 = field(
                    default=None,
                    metadata={
                        "name": "anwendungsspezifischerFehler",
                        "type": "Element",
                    },
                )
                vag_fehler: None | CodeGdsVagFehlerTyp3 = field(
                    default=None,
                    metadata={
                        "name": "vag.fehler",
                        "type": "Element",
                    },
                )
                inso_iri_fehler: None | CodeGdsInsoIriFehlercodeTyp3 = field(
                    default=None,
                    metadata={
                        "name": "inso.iri.fehler",
                        "type": "Element",
                    },
                )
                auskunft_vollstreckungssachen_fehler: (
                    None | CodeGdsAuskunftVollstreckungssachenFehlerTyp3
                ) = field(
                    default=None,
                    metadata={
                        "name": "auskunft.vollstreckungssachen.fehler",
                        "type": "Element",
                    },
                )

            @dataclass(kw_only=True)
            class AuswahlStatusWeiterverarbeitung:
                """
                :ivar erfolgt: Die Bearbeitung der Nachricht erfolgt
                    trotz des Fehlers. Eine bereinigte Version der
                    fehlerhaften Nachricht darf nicht übermittelt
                    werden, der Fehler soll vielmehr für künftige
                    Übermittlung bereinigt werden.
                :ivar abhaengig_von_fehlerbehebung: Die Nachricht wird
                    nicht bearbeitet. Die Übermittlung einer
                    fehlerbereinigten Nachricht ist zwingend
                    erforderlich.
                """

                erfolgt: None | bool = field(
                    default=None,
                    metadata={
                        "type": "Element",
                    },
                )
                abhaengig_von_fehlerbehebung: None | bool = field(
                    default=None,
                    metadata={
                        "name": "abhaengigVonFehlerbehebung",
                        "type": "Element",
                    },
                )


@dataclass(kw_only=True)
class NachrichtGdsUebermittlungSchriftgutobjekte0005005(TypeGdsBasisnachricht):
    """
    Diese Nachricht ist eine Erweiterung des Type.GDS.Basisnachricht.
    """

    class Meta:
        name = "nachricht.gds.uebermittlungSchriftgutobjekte.0005005"
        namespace = "http://www.xjustiz.de"

    schriftgutobjekte: TypeGdsSchriftgutobjekte = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class NachrichtGdsVerarbeitungsbestaetigung0005008:
    """
    Die XJustiz-Nachricht "nachricht.gds.verarbeitungsbestaetigung.0005008"
    wird verwendet, wenn die Verarbeitung einer eingegangenen
    XJustiz-Nachricht bestätigt werden soll.

    Sie nimmt auf eine eingegangene XJustiz-Nachricht Bezug. Dabei wird die
    ID, die in der eingegangen XJustiz-Nachricht als „eigeneNachrichtenID“
    im Nachrichtenkopf angegeben wurde, im Element „fremdeNachrichtenID“ im
    Nachrichtenkopf der Nachricht
    „nachricht.gds.verarbeitungsbestaetigung.0005008“ zurück übermittelt.
    Die XJustiz-Nachricht wird nicht verwendet, um den bloßen Eingang einer
    XJustiz-Nachricht zu bestätigen. Die Eingangsbestätigung erfolgt
    vielmehr auf der Transportebene durch die EGVP-Eingangsbestätigung, die
    beim Versand von EGVP-Nachrichten über die ERV-Infrastruktur erstellt
    wird. Nachfolgend sind die Einsatzszenarien für die XJustiz-Nachricht
    „nachricht.gds.verarbeitungsbestaetigung.0005008“ beschrieben:
    Wettbewerbsregister Die Verarbeitungsbestätigung wird versandt, wenn
    die Eintragungsmitteilungen (Erstmitteilung/Berichtigung) oder
    Löschmitteilungen im Wettbewerbsregister zur weiteren fachlichen
    Verarbeitung in das System übernommen wurden. Die Übernahme erfolgt nur
    dann, wenn die referenzierte Mitteilung die technischen
    Strukturvorgaben erfüllt. BZR/GZR Die Verarbeitungsbestätigung wird
    versandt, wenn das Register auf der Grundlage einer übermittelten
    XJustiz-Nachricht fortgeschrieben wurde. Falls das Register durch die
    Nachricht nicht fortgeschrieben wird, wird dies durch das Kindelement
    BZRGZR kenntlich gemacht. Im Falle einer Doppelmitteilung wird der
    Codeschlüssel 001 übermittelt, im Falle einer Berichtigungsmitteilung
    der Codeschlüssel 002. Fahndung Die Verarbeitungsbestätigung wird
    versandt, wenn die Erstausschreibung in Fahndungssachen von der Polizei
    in die dortigen Systeme übernommen wurde. Dabei wird das
    Ausschreibungsende, das im System der Polizei erfasst wurde,
    mitgeteilt.

    :ivar nachrichtenkopf:
    :ivar fachdaten: Die Verwendung der Fachdaten kommt für die
        Kommunikation zwischen Polizei und Justiz in Fahndungssachen
        oder für die Kommunikation zwischen Justiz und BfJ (BZR/GZR-
        Sachen) in Betracht.
    """

    class Meta:
        name = "nachricht.gds.verarbeitungsbestaetigung.0005008"
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    fachdaten: (
        None | NachrichtGdsVerarbeitungsbestaetigung0005008.Fachdaten
    ) = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        """
        :ivar fahndung_ausschreibungsende: Mit diesem Element wird das
            Datum, bis zu dem die Fahndung im System der Polizei erfasst
            bleibt, übermittelt.
        :ivar bzrgzr: Mit diesem Element können bei der Kommunikation
            zwischen der Justiz und dem BZR/GZR zusätzliche
            Informationen (falls einschlägig) zur
            Verarbeitungsbestätigung übermittelt werden.
        """

        fahndung_ausschreibungsende: None | XmlDate = field(
            default=None,
            metadata={
                "name": "fahndung.ausschreibungsende",
                "type": "Element",
            },
        )
        bzrgzr: None | CodeGdsStrafBzrVerarbeitungsbestaetigungTyp3 = field(
            default=None,
            metadata={
                "name": "BZRGZR",
                "type": "Element",
            },
        )
