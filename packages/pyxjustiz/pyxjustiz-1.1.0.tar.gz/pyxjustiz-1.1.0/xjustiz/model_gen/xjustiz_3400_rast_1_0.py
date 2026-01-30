from __future__ import annotations

from dataclasses import dataclass, field

from xsdata.models.datatype import XmlDate

from xjustiz.model_gen.xjustiz_0000_grunddatensatz_3_6 import (
    TypeGdsFahrzeug,
    TypeGdsGrunddaten,
    TypeGdsNachrichtenkopf,
    TypeGdsRefRollennummer,
    TypeGdsSchriftgutobjekte,
)
from xjustiz.model_gen.xjustiz_3410_cl_rast_1_0 import (
    CodeRastBelastungsartTyp3,
    CodeRastInhaberEigentumsVerhaeltnisTyp3,
)

__NAMESPACE__ = "http://www.xjustiz.de"


@dataclass(kw_only=True)
class NachrichtRastAntragBeratungshilfe3400001:
    class Meta:
        name = "nachricht.rast.antragBeratungshilfe.3400001"
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
    fachdaten: NachrichtRastAntragBeratungshilfe3400001.Fachdaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        """
        :ivar sachverhalt:
        :ivar voraussetzungen_erfuellt: Die nachfolgend aufgeführten
            Voraussetzungen müssen erfüllt sein. Sofern eine der
            genannten Voraussetzungen nicht erfüllt ist, kann
            Beratungshilfe nicht bewilligt werden. Auf die Übermittlung
            des Antrags soll in diesem Fall verzichtet werden.
        :ivar auswahl_sozialhilfe_bewilligt:
        :ivar beratung_vertretung_stattgefunden: In diesem Element kann
            der Antragsteller angeben, dass er sich an eine
            Beratungsperson gewandt hat.
        :ivar versicherungen: In diesem Element ist folgender fixed-Wert
            zu übertragen, wenn der Antragsteller folgende
            Versicherungen abgibt: "Ich versichere, dass mir in
            derselben Angelegenheit Beratungshilfe weder gewährt noch
            durch das Gericht versagt worden ist und dass in derselben
            Angelegenheit kein gerichtliches Verfahren anhängig ist oder
            war. Ich versichere, dass meine Angaben vollständig und wahr
            sind. Die Allgemeinen Hinweise und die Ausfüllhinweise zu
            diesem Formular habe ich erhalten. Mir ist bekannt, dass das
            Gericht verlangen kann, dass ich meine Angaben glaubhaft
            mache und insbesondere auch die Abgabe einer Versicherung an
            Eides statt fordern kann. Mir ist bekannt, dass
            unvollständige oder unrichtige Angaben die Aufhebung der
            Bewilligung von Beratungshilfe und ggf. auch eine
            Strafverfolgung nach sich ziehen können." (fixed-Wert)
        """

        sachverhalt: str = field(
            metadata={
                "type": "Element",
                "required": True,
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            }
        )
        voraussetzungen_erfuellt: NachrichtRastAntragBeratungshilfe3400001.Fachdaten.VoraussetzungenErfuellt = field(
            metadata={
                "name": "voraussetzungenErfuellt",
                "type": "Element",
                "required": True,
            }
        )
        auswahl_sozialhilfe_bewilligt: NachrichtRastAntragBeratungshilfe3400001.Fachdaten.AuswahlSozialhilfeBewilligt = field(
            metadata={
                "name": "auswahl_sozialhilfeBewilligt",
                "type": "Element",
                "required": True,
            }
        )
        beratung_vertretung_stattgefunden: (
            None
            | NachrichtRastAntragBeratungshilfe3400001.Fachdaten.BeratungVertretungStattgefunden
        ) = field(
            default=None,
            metadata={
                "name": "beratung.vertretungStattgefunden",
                "type": "Element",
            },
        )
        versicherungen: str = field(
            metadata={
                "type": "Element",
                "required": True,
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            }
        )

        @dataclass(kw_only=True)
        class VoraussetzungenErfuellt:
            """
            :ivar keine_rechtsschutzversicherung: In diesem Wert ist der
                Wert "true" anzugeben, wenn der Antragsteller folgende
                Erklärung abgibt: "In der vorliegenden Angelegenheit
                tritt keine Rechtsschutzversicherung ein."
            :ivar keine_andere_kostenlose_beratung: In diesem Wert ist
                der Wert "true" anzugeben, wenn der Antragsteller
                folgende Erklärung abgibt: "In dieser Angelegenheit
                besteht für mich nach meiner Kenntnis keine andere
                Möglichkeit, kostenlose Beratung und Vertretung in
                Anspruch zu nehmen."
            :ivar keine_beratungshilfe_diese_angelegenheit: In diesem
                Wert ist der Wert "true" anzugeben, wenn der
                Antragsteller folgende Erklärung abgibt: "In dieser
                Angelegenheit ist mir bisher Beratungshilfe weder
                bewilligt noch versagt worden."
            :ivar kein_gerichtliches_verfahren: In diesem Wert ist der
                Wert "true" anzugeben, wenn der Antragsteller folgende
                Erklärung abgibt: "In dieser Angelegenheit wird oder
                wurde von mir bisher kein gerichtliches Verfahren
                geführt."
            """

            keine_rechtsschutzversicherung: bool = field(
                metadata={
                    "name": "keineRechtsschutzversicherung",
                    "type": "Element",
                    "required": True,
                }
            )
            keine_andere_kostenlose_beratung: bool = field(
                metadata={
                    "name": "keineAndereKostenloseBeratung",
                    "type": "Element",
                    "required": True,
                }
            )
            keine_beratungshilfe_diese_angelegenheit: bool = field(
                metadata={
                    "name": "keineBeratungshilfeDieseAngelegenheit",
                    "type": "Element",
                    "required": True,
                }
            )
            kein_gerichtliches_verfahren: bool = field(
                metadata={
                    "name": "keinGerichtlichesVerfahren",
                    "type": "Element",
                    "required": True,
                }
            )

        @dataclass(kw_only=True)
        class AuswahlSozialhilfeBewilligt:
            ja: None | bool = field(
                default=None,
                metadata={
                    "type": "Element",
                },
            )
            nein: (
                None
                | NachrichtRastAntragBeratungshilfe3400001.Fachdaten.AuswahlSozialhilfeBewilligt.Nein
            ) = field(
                default=None,
                metadata={
                    "type": "Element",
                },
            )

            @dataclass(kw_only=True)
            class Nein:
                """
                :ivar erwerbstaetig: In diesem Wert ist "true"
                    anzugeben, wenn der Antragsteller erwerbstätig ist,
                    also einen Beruf ausübt und dafür Lohn erhält.
                :ivar monatliche_einkuenfte_in_euro:
                :ivar wohnung:
                :ivar unterhalts_gewaehrung: Diese Sequenz ist
                    auszufüllen, wenn der Antragsteller einer anderen
                    Person Unterhalt gewährt. Unterhalt kann in Form von
                    Geldzahlungen, aber auch durch Gewährung von
                    Unterkunft, Verpflegung etc. erfolgen.
                :ivar vermoegen:
                :ivar zahlungsverpflichtungen_sonstige_belastungen:
                """

                erwerbstaetig: bool = field(
                    default=False,
                    metadata={
                        "type": "Element",
                        "required": True,
                    },
                )
                monatliche_einkuenfte_in_euro: NachrichtRastAntragBeratungshilfe3400001.Fachdaten.AuswahlSozialhilfeBewilligt.Nein.MonatlicheEinkuenfteInEuro = field(
                    metadata={
                        "name": "monatlicheEinkuenfteInEuro",
                        "type": "Element",
                        "required": True,
                    }
                )
                wohnung: NachrichtRastAntragBeratungshilfe3400001.Fachdaten.AuswahlSozialhilfeBewilligt.Nein.Wohnung = field(
                    metadata={
                        "type": "Element",
                        "required": True,
                    }
                )
                unterhalts_gewaehrung: list[
                    NachrichtRastAntragBeratungshilfe3400001.Fachdaten.AuswahlSozialhilfeBewilligt.Nein.UnterhaltsGewaehrung
                ] = field(
                    default_factory=list,
                    metadata={
                        "name": "unterhaltsGewaehrung",
                        "type": "Element",
                    },
                )
                vermoegen: NachrichtRastAntragBeratungshilfe3400001.Fachdaten.AuswahlSozialhilfeBewilligt.Nein.Vermoegen = field(
                    metadata={
                        "type": "Element",
                        "required": True,
                    }
                )
                zahlungsverpflichtungen_sonstige_belastungen: (
                    None
                    | NachrichtRastAntragBeratungshilfe3400001.Fachdaten.AuswahlSozialhilfeBewilligt.Nein.ZahlungsverpflichtungenSonstigeBelastungen
                ) = field(
                    default=None,
                    metadata={
                        "name": "zahlungsverpflichtungenSonstigeBelastungen",
                        "type": "Element",
                    },
                )

                @dataclass(kw_only=True)
                class MonatlicheEinkuenfteInEuro:
                    """
                    :ivar einkuenfte_antragsteller:
                    :ivar einkuenfte_ehegatte_netto: In diesem Element
                        sind die monatlichen netto Einkünfte des
                        Ehegatten/der Ehegattin bzw. des eingetragenen
                        Lebenspartners/der eingetragenen Lebenspartnerin
                        des Antragstellers/der Antragstellerin
                        anzugeben.
                    """

                    einkuenfte_antragsteller: NachrichtRastAntragBeratungshilfe3400001.Fachdaten.AuswahlSozialhilfeBewilligt.Nein.MonatlicheEinkuenfteInEuro.EinkuenfteAntragsteller = field(
                        metadata={
                            "name": "einkuenfteAntragsteller",
                            "type": "Element",
                            "required": True,
                        }
                    )
                    einkuenfte_ehegatte_netto: None | float = field(
                        default=None,
                        metadata={
                            "name": "einkuenfteEhegatteNetto",
                            "type": "Element",
                        },
                    )

                    @dataclass(kw_only=True)
                    class EinkuenfteAntragsteller:
                        brutto: None | float = field(
                            default=None,
                            metadata={
                                "type": "Element",
                            },
                        )
                        netto: float = field(
                            metadata={
                                "type": "Element",
                                "required": True,
                            }
                        )

                @dataclass(kw_only=True)
                class Wohnung:
                    """
                    :ivar groesse:
                    :ivar wohnkosten_monatlich_in_euro:
                    :ivar kosten_anteil_antragsteller_in_euro: In diesem
                        Element ist immer der Anteil der Wohnkosten des
                        Antragstellers anzugeben.
                    :ivar auswahl_personenanzahl_haushalt: Hier ist
                        anzugeben, ob der Antragssteller die Wohnung
                        alleine oder mit weiteren Personen bewohnt.
                    """

                    groesse: int = field(
                        metadata={
                            "type": "Element",
                            "required": True,
                        }
                    )
                    wohnkosten_monatlich_in_euro: float = field(
                        metadata={
                            "name": "wohnkostenMonatlichInEuro",
                            "type": "Element",
                            "required": True,
                        }
                    )
                    kosten_anteil_antragsteller_in_euro: float = field(
                        metadata={
                            "name": "kostenAnteilAntragstellerInEuro",
                            "type": "Element",
                            "required": True,
                        }
                    )
                    auswahl_personenanzahl_haushalt: (
                        None
                        | NachrichtRastAntragBeratungshilfe3400001.Fachdaten.AuswahlSozialhilfeBewilligt.Nein.Wohnung.AuswahlPersonenanzahlHaushalt
                    ) = field(
                        default=None,
                        metadata={
                            "name": "auswahl_personenanzahlHaushalt",
                            "type": "Element",
                        },
                    )

                    @dataclass(kw_only=True)
                    class AuswahlPersonenanzahlHaushalt:
                        """
                        :ivar alleine:
                        :ivar weitere_personen_haushalt: Wenn der
                            Antragsteller die Wohnung gemeinsam mit
                            weiteren Personen bewohnt, ist die in diesem
                            Element die Anzahl der Personen anzugeben.
                        """

                        alleine: None | bool = field(
                            default=None,
                            metadata={
                                "type": "Element",
                            },
                        )
                        weitere_personen_haushalt: None | int = field(
                            default=None,
                            metadata={
                                "name": "weiterePersonenHaushalt",
                                "type": "Element",
                            },
                        )

                @dataclass(kw_only=True)
                class UnterhaltsGewaehrung:
                    """
                    :ivar unterhaltsempfaenger: Der Unterhaltsempfänger
                        wird in den Grunddaten aufgeführt und über die
                        Rollennummer verknüpft. Sofern der
                        Unterhaltsempfänger einen anderen Wohnsitz als
                        der Antragsteller inne hat, so ist dieser
                        Wohnsitz in den Grunddaten anzugeben.
                    :ivar monatlicher_betrag_in_euro: Ist nur zu
                        befüllen, wenn Unterhalt ausschließlich in Form
                        von Geldzahlungen geleistet wird. (Nicht zu
                        befüllen z.B. bei im Haushalt lebenden Kindern)
                    :ivar auswahl_eigene_einnahmen_netto_in_euro: Hier
                        kann angegeben werden, ob und in welcher Höhe
                        der Angehörige eigene Einnahmen hat.
                    """

                    unterhaltsempfaenger: TypeGdsRefRollennummer = field(
                        metadata={
                            "type": "Element",
                            "required": True,
                        }
                    )
                    monatlicher_betrag_in_euro: None | float = field(
                        default=None,
                        metadata={
                            "name": "monatlicherBetragInEuro",
                            "type": "Element",
                        },
                    )
                    auswahl_eigene_einnahmen_netto_in_euro: (
                        None
                        | NachrichtRastAntragBeratungshilfe3400001.Fachdaten.AuswahlSozialhilfeBewilligt.Nein.UnterhaltsGewaehrung.AuswahlEigeneEinnahmenNettoInEuro
                    ) = field(
                        default=None,
                        metadata={
                            "name": "auswahl_eigeneEinnahmenNettoInEuro",
                            "type": "Element",
                        },
                    )

                    @dataclass(kw_only=True)
                    class AuswahlEigeneEinnahmenNettoInEuro:
                        """
                        :ivar keine_einnahmen:
                        :ivar hoehe_der_einahmen_netto_in_euro: Wenn der
                            Angehörige eigene Einnahmen hat, ist der
                            Betrag in diesem Element anzugeben.
                        """

                        keine_einnahmen: None | bool = field(
                            default=None,
                            metadata={
                                "name": "keineEinnahmen",
                                "type": "Element",
                            },
                        )
                        hoehe_der_einahmen_netto_in_euro: None | float = field(
                            default=None,
                            metadata={
                                "name": "hoeheDerEinahmenNettoInEuro",
                                "type": "Element",
                            },
                        )

                @dataclass(kw_only=True)
                class Vermoegen:
                    """
                    :ivar auswahl_bankkonten_wertpapiere: In den
                        Elementen dieser Auswahl werden Angaben zu
                        Giro-, Sparkonten und andere Bankkonten,
                        Bausparkonten, Wertpapiere übermittelt.
                    :ivar auswahl_grundeigentum: In den Elementen dieser
                        Auswahl werden Angaben zu Grundeigentum (zum
                        Beispiel Grundstück, Familienheim,
                        Wohnungseigentum, Erbbaurecht) übermittelt.
                    :ivar auswahl_kraftfahrzeuge: In den Elementen
                        dieser Auswahl werden Angaben zu Kraftfahrzeugen
                        übermittelt.
                    :ivar auswahl_sonstige_vermoegenswerte: Sonstige
                        Vermögenswerte können zum Beispiel
                        Kapitallebensversicherung, Bargeld,
                        Wertgegenstände, Forderungen, Anspruch aus
                        Zugewinnausgleich sein.
                    """

                    auswahl_bankkonten_wertpapiere: list[
                        NachrichtRastAntragBeratungshilfe3400001.Fachdaten.AuswahlSozialhilfeBewilligt.Nein.Vermoegen.AuswahlBankkontenWertpapiere
                    ] = field(
                        default_factory=list,
                        metadata={
                            "name": "auswahl_bankkontenWertpapiere",
                            "type": "Element",
                            "min_occurs": 1,
                        },
                    )
                    auswahl_grundeigentum: list[
                        NachrichtRastAntragBeratungshilfe3400001.Fachdaten.AuswahlSozialhilfeBewilligt.Nein.Vermoegen.AuswahlGrundeigentum
                    ] = field(
                        default_factory=list,
                        metadata={
                            "type": "Element",
                            "min_occurs": 1,
                        },
                    )
                    auswahl_kraftfahrzeuge: list[
                        NachrichtRastAntragBeratungshilfe3400001.Fachdaten.AuswahlSozialhilfeBewilligt.Nein.Vermoegen.AuswahlKraftfahrzeuge
                    ] = field(
                        default_factory=list,
                        metadata={
                            "type": "Element",
                            "min_occurs": 1,
                        },
                    )
                    auswahl_sonstige_vermoegenswerte: list[
                        NachrichtRastAntragBeratungshilfe3400001.Fachdaten.AuswahlSozialhilfeBewilligt.Nein.Vermoegen.AuswahlSonstigeVermoegenswerte
                    ] = field(
                        default_factory=list,
                        metadata={
                            "name": "auswahl_sonstigeVermoegenswerte",
                            "type": "Element",
                            "min_occurs": 1,
                        },
                    )

                    @dataclass(kw_only=True)
                    class AuswahlBankkontenWertpapiere:
                        keinebankkonten_wertpapiere: None | bool = field(
                            default=None,
                            metadata={
                                "name": "keinebankkontenWertpapiere",
                                "type": "Element",
                            },
                        )
                        bankkonten_wertpapiere_vorhanden: (
                            None
                            | NachrichtRastAntragBeratungshilfe3400001.Fachdaten.AuswahlSozialhilfeBewilligt.Nein.Vermoegen.AuswahlBankkontenWertpapiere.BankkontenWertpapiereVorhanden
                        ) = field(
                            default=None,
                            metadata={
                                "name": "bankkontenWertpapiereVorhanden",
                                "type": "Element",
                            },
                        )

                        @dataclass(kw_only=True)
                        class BankkontenWertpapiereVorhanden:
                            """
                            :ivar bezeichnung: Hier muss die Bezeichnung
                                der Bank/der Sparkasse/des sonstigen
                                Kreditinstuts angegeben werden.
                            :ivar inhaber: Mit diesem Element wird
                                angegeben ob der Antragsteller alleine,
                                oder der Ehegatte/Lebenspartner alleine
                                oder der Antragsteller gemeinsam mit
                                Ehegatten/Lebenspartner Inhaber des
                                Kontos/Wertpapiers ist.
                            :ivar auszahlungstermin: Nur anzugeben bei
                                Bausparkonten
                            :ivar verwendungszweck: Nur anzugeben bei
                                Bausparkonten
                            :ivar kontostand_in_euro:
                            """

                            bezeichnung: str = field(
                                metadata={
                                    "type": "Element",
                                    "required": True,
                                    "pattern": r"([ -~]|[¡-¬]|[®-ž]|[Ƈ-ƈ]|Ə|ƒ|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|ʰ|ʳ|[ʹ-ʺ]|[ʾ-ʿ]|ˆ|ˈ|ˌ|˜|ˢ|Ά|[Έ-Ί]|Ό|[Ύ-Ρ]|[Σ-ώ]|ᵈ|ᵗ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|[‘-‚]|[“-„]|[†-‡]|…|‰|[′-″]|[‹-›]|⁰|[⁴-⁹]|[ⁿ-₉]|€|™|∞|[≤-≥]|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                                }
                            )
                            inhaber: CodeRastInhaberEigentumsVerhaeltnisTyp3 = field(
                                metadata={
                                    "type": "Element",
                                    "required": True,
                                }
                            )
                            auszahlungstermin: None | XmlDate = field(
                                default=None,
                                metadata={
                                    "type": "Element",
                                },
                            )
                            verwendungszweck: None | str = field(
                                default=None,
                                metadata={
                                    "type": "Element",
                                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                                },
                            )
                            kontostand_in_euro: float = field(
                                metadata={
                                    "name": "kontostandInEuro",
                                    "type": "Element",
                                    "required": True,
                                }
                            )

                    @dataclass(kw_only=True)
                    class AuswahlGrundeigentum:
                        kein_grundeigentum: None | bool = field(
                            default=None,
                            metadata={
                                "name": "keinGrundeigentum",
                                "type": "Element",
                            },
                        )
                        grundeigentum_vorhanden: (
                            None
                            | NachrichtRastAntragBeratungshilfe3400001.Fachdaten.AuswahlSozialhilfeBewilligt.Nein.Vermoegen.AuswahlGrundeigentum.GrundeigentumVorhanden
                        ) = field(
                            default=None,
                            metadata={
                                "name": "grundeigentumVorhanden",
                                "type": "Element",
                            },
                        )

                        @dataclass(kw_only=True)
                        class GrundeigentumVorhanden:
                            eigentuemer: CodeRastInhaberEigentumsVerhaeltnisTyp3 = field(
                                metadata={
                                    "type": "Element",
                                    "required": True,
                                }
                            )
                            bezeichnung: NachrichtRastAntragBeratungshilfe3400001.Fachdaten.AuswahlSozialhilfeBewilligt.Nein.Vermoegen.AuswahlGrundeigentum.GrundeigentumVorhanden.Bezeichnung = field(
                                metadata={
                                    "type": "Element",
                                    "required": True,
                                }
                            )
                            verkehrswert_in_euro: float = field(
                                metadata={
                                    "name": "verkehrswertInEuro",
                                    "type": "Element",
                                    "required": True,
                                }
                            )

                            @dataclass(kw_only=True)
                            class Bezeichnung:
                                lage: None | str = field(
                                    default=None,
                                    metadata={
                                        "type": "Element",
                                        "pattern": r"([ -~]|[¡-£]|¥|[§-¬]|[®-·]|[¹-»]|[¿-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                                    },
                                )
                                groesse: str = field(
                                    metadata={
                                        "type": "Element",
                                        "required": True,
                                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                                    }
                                )
                                nutzungsart: str = field(
                                    metadata={
                                        "type": "Element",
                                        "required": True,
                                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                                    }
                                )

                    @dataclass(kw_only=True)
                    class AuswahlKraftfahrzeuge:
                        keine_kraftfahrzeuge: None | bool = field(
                            default=None,
                            metadata={
                                "name": "keineKraftfahrzeuge",
                                "type": "Element",
                            },
                        )
                        kraftfahrzeuge_vorhanden: (
                            None
                            | NachrichtRastAntragBeratungshilfe3400001.Fachdaten.AuswahlSozialhilfeBewilligt.Nein.Vermoegen.AuswahlKraftfahrzeuge.KraftfahrzeugeVorhanden
                        ) = field(
                            default=None,
                            metadata={
                                "name": "kraftfahrzeugeVorhanden",
                                "type": "Element",
                            },
                        )

                        @dataclass(kw_only=True)
                        class KraftfahrzeugeVorhanden:
                            eigentuemer: CodeRastInhaberEigentumsVerhaeltnisTyp3 = field(
                                metadata={
                                    "type": "Element",
                                    "required": True,
                                }
                            )
                            fahrzeug: TypeGdsFahrzeug = field(
                                metadata={
                                    "type": "Element",
                                    "required": True,
                                }
                            )

                    @dataclass(kw_only=True)
                    class AuswahlSonstigeVermoegenswerte:
                        keine_sonstige_vermoegenswerte: None | bool = field(
                            default=None,
                            metadata={
                                "name": "keineSonstigeVermoegenswerte",
                                "type": "Element",
                            },
                        )
                        sonstige_vermoegenswerte: (
                            None
                            | NachrichtRastAntragBeratungshilfe3400001.Fachdaten.AuswahlSozialhilfeBewilligt.Nein.Vermoegen.AuswahlSonstigeVermoegenswerte.SonstigeVermoegenswerte
                        ) = field(
                            default=None,
                            metadata={
                                "name": "sonstigeVermoegenswerte",
                                "type": "Element",
                            },
                        )

                        @dataclass(kw_only=True)
                        class SonstigeVermoegenswerte:
                            eigentuemer: CodeRastInhaberEigentumsVerhaeltnisTyp3 = field(
                                metadata={
                                    "type": "Element",
                                    "required": True,
                                }
                            )
                            bezeichnung_gegenstand: str = field(
                                metadata={
                                    "name": "bezeichnungGegenstand",
                                    "type": "Element",
                                    "required": True,
                                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                                }
                            )
                            rueckkaufswert_verkehrswert_in_euro: float = field(
                                metadata={
                                    "name": "rueckkaufswert.verkehrswertInEuro",
                                    "type": "Element",
                                    "required": True,
                                }
                            )

                @dataclass(kw_only=True)
                class ZahlungsverpflichtungenSonstigeBelastungen:
                    zahlungsverpflichtungen: list[
                        NachrichtRastAntragBeratungshilfe3400001.Fachdaten.AuswahlSozialhilfeBewilligt.Nein.ZahlungsverpflichtungenSonstigeBelastungen.Zahlungsverpflichtungen
                    ] = field(
                        default_factory=list,
                        metadata={
                            "type": "Element",
                        },
                    )
                    sonstige_belastungen: list[
                        NachrichtRastAntragBeratungshilfe3400001.Fachdaten.AuswahlSozialhilfeBewilligt.Nein.ZahlungsverpflichtungenSonstigeBelastungen.SonstigeBelastungen
                    ] = field(
                        default_factory=list,
                        metadata={
                            "name": "sonstigeBelastungen",
                            "type": "Element",
                        },
                    )

                    @dataclass(kw_only=True)
                    class Zahlungsverpflichtungen:
                        verbindlichkeit: str = field(
                            metadata={
                                "type": "Element",
                                "required": True,
                                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                            }
                        )
                        glaeubiger: str = field(
                            metadata={
                                "type": "Element",
                                "required": True,
                                "pattern": r"([ -~]|[¡-¬]|[®-ž]|[Ƈ-ƈ]|Ə|ƒ|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|ʰ|ʳ|[ʹ-ʺ]|[ʾ-ʿ]|ˆ|ˈ|ˌ|˜|ˢ|Ά|[Έ-Ί]|Ό|[Ύ-Ρ]|[Σ-ώ]|ᵈ|ᵗ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|[‘-‚]|[“-„]|[†-‡]|…|‰|[′-″]|[‹-›]|⁰|[⁴-⁹]|[ⁿ-₉]|€|™|∞|[≤-≥]|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                            }
                        )
                        verwendungszweck: str = field(
                            metadata={
                                "type": "Element",
                                "required": True,
                                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                            }
                        )
                        raten_bis: None | XmlDate = field(
                            default=None,
                            metadata={
                                "name": "ratenBis",
                                "type": "Element",
                            },
                        )
                        restschuld_in_euro: None | float = field(
                            default=None,
                            metadata={
                                "name": "restschuldInEuro",
                                "type": "Element",
                            },
                        )
                        monatlicher_betrag_antragsteller_in_euro: (
                            None | float
                        ) = field(
                            default=None,
                            metadata={
                                "name": "monatlicherBetragAntragstellerInEuro",
                                "type": "Element",
                            },
                        )
                        monatlicher_betrag_ehegatte_lebenspartner_in_euro: (
                            None | float
                        ) = field(
                            default=None,
                            metadata={
                                "name": "monatlicherBetragEhegatte.LebenspartnerInEuro",
                                "type": "Element",
                            },
                        )

                    @dataclass(kw_only=True)
                    class SonstigeBelastungen:
                        """
                        :ivar art: Hier kann aus der Codeliste der
                            Umstand ausgewählt werden, der auf den
                            Antragsteller oder den
                            Ehegatte/eingetragener Lebenspartner bzw.
                            seiner Ehegattin/eingetragenen
                            Lebenspartnerin zutrifft. Sofern der Wert
                            "Sonstiges" ausgewählt wird, muss immer das
                            Element "begruendung" befüllt werden.
                        :ivar begruendung: Hier kann eine Begründung für
                            die sonstigen Belastungen eingetragen
                            werden. Das Element ist zwingend zu füllen,
                            wenn der Wert "Sonstiges" aus der Codeliste
                            RAST.Belastungsart ausgewählt wurde.
                        :ivar monatlicher_betrag_antragsteller_in_euro:
                        :ivar
                            monatlicher_betrag_ehegatte_lebenspartner_in_euro:
                        """

                        art: CodeRastBelastungsartTyp3 = field(
                            metadata={
                                "type": "Element",
                                "required": True,
                            }
                        )
                        begruendung: None | str = field(
                            default=None,
                            metadata={
                                "type": "Element",
                                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                            },
                        )
                        monatlicher_betrag_antragsteller_in_euro: (
                            None | float
                        ) = field(
                            default=None,
                            metadata={
                                "name": "monatlicherBetragAntragstellerInEuro",
                                "type": "Element",
                            },
                        )
                        monatlicher_betrag_ehegatte_lebenspartner_in_euro: (
                            None | float
                        ) = field(
                            default=None,
                            metadata={
                                "name": "monatlicherBetragEhegatte.LebenspartnerInEuro",
                                "type": "Element",
                            },
                        )

        @dataclass(kw_only=True)
        class BeratungVertretungStattgefunden:
            """
            :ivar datum_der_ersten_beratung_vertretung: Hier muss das
                Datum der ersten Beratung bzw. Vertretung angegeben
                werden.
            :ivar beratungs_vertretungs_person: Name und Anschrift der
                Person, die die Beratung bzw. die Vertretung
                durchgeführt hat, werden in den Grunddaten aufgeführt.
                In diesem Element ist der Verweis auf die Angaben dieser
                Person in den Grunddaten anzugeben.
            """

            datum_der_ersten_beratung_vertretung: XmlDate = field(
                metadata={
                    "name": "datumDerErstenBeratung.vertretung",
                    "type": "Element",
                    "required": True,
                }
            )
            beratungs_vertretungs_person: TypeGdsRefRollennummer = field(
                metadata={
                    "name": "beratungs.vertretungs.person",
                    "type": "Element",
                    "required": True,
                }
            )
