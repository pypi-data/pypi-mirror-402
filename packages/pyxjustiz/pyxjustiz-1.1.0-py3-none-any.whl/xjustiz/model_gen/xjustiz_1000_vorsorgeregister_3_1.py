from __future__ import annotations

from dataclasses import dataclass, field

from xsdata.models.datatype import XmlDate, XmlDateTime

from xjustiz.model_gen.xjustiz_0000_grunddatensatz_3_6 import (
    TypeGdsAktenzeichen,
    TypeGdsGrunddaten,
    TypeGdsNachrichtenkopf,
    TypeGdsRefRollennummer,
    TypeGdsRefSgo,
    TypeGdsSchriftgutobjekte,
)
from xjustiz.model_gen.xjustiz_0020_cl_gerichte_3_3 import CodeGdsGerichteTyp3
from xjustiz.model_gen.xjustiz_1010_cl_vorsorgeregister_3_0 import (
    CodeZvrAntwortart,
    CodeZvrEintragungsart,
)

__NAMESPACE__ = "http://www.xjustiz.de"


@dataclass(kw_only=True)
class TypeZvrVollmachtdatenBasis:
    """
    :ivar registernummer: ZVR-Registernummer
    :ivar datum_eintragung: Datum der letzten Eintragung
    :ivar datum_vollmacht: Datum der Vorsorgevollmacht
    :ivar urkundenrollennummer: Angabe nur bei notarieller Registrierung
    :ivar aktenzeichen: Angabe nur bei nicht-notarieller Registrierung
    """

    class Meta:
        name = "Type.ZVR.VollmachtdatenBasis"

    registernummer: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )
    datum_eintragung: XmlDate = field(
        metadata={
            "name": "datum.eintragung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    datum_vollmacht: XmlDate = field(
        metadata={
            "name": "datum.vollmacht",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    urkundenrollennummer: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        },
    )
    aktenzeichen: None | TypeGdsAktenzeichen = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )


@dataclass(kw_only=True)
class NachrichtZvrErstelleAbfrageProtokollInput1000004:
    class Meta:
        name = "nachricht.zvr.erstelleAbfrageProtokoll.input.1000004"
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
    fachdaten: NachrichtZvrErstelleAbfrageProtokollInput1000004.Fachdaten = (
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
        :ivar gericht_id: GvzGerichtId des Gerichts für welches ein
            Protokoll angefragt wird.
        :ivar abfragen_von:
        :ivar abfragen_bis:
        """

        gericht_id: CodeGdsGerichteTyp3 = field(
            metadata={
                "name": "gerichtID",
                "type": "Element",
                "required": True,
            }
        )
        abfragen_von: None | XmlDate = field(
            default=None,
            metadata={
                "name": "abfragen.von",
                "type": "Element",
            },
        )
        abfragen_bis: None | XmlDate = field(
            default=None,
            metadata={
                "name": "abfragen.bis",
                "type": "Element",
            },
        )


@dataclass(kw_only=True)
class NachrichtZvrErstelleAbfrageProtokollOutput1000005:
    class Meta:
        name = "nachricht.zvr.erstelleAbfrageProtokoll.output.1000005"
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
    schriftgutobjekte: TypeGdsSchriftgutobjekte = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    fachdaten: NachrichtZvrErstelleAbfrageProtokollOutput1000005.Fachdaten = (
        field(
            metadata={
                "type": "Element",
                "required": True,
            }
        )
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        protokoll: (
            None
            | NachrichtZvrErstelleAbfrageProtokollOutput1000005.Fachdaten.Protokoll
        ) = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )
        abfrageeintrag: list[
            NachrichtZvrErstelleAbfrageProtokollOutput1000005.Fachdaten.Abfrageeintrag
        ] = field(
            default_factory=list,
            metadata={
                "type": "Element",
            },
        )

        @dataclass(kw_only=True)
        class Protokoll:
            """
            :ivar erstellzeitpunkt_protokoll:
            :ivar username_abfragender: Nur wenn der Username im SAML
                Token vorhanden sein wird
            :ivar name_betreuungsgericht:
            :ivar suchfelder:
            :ivar dokument:
            """

            erstellzeitpunkt_protokoll: XmlDateTime = field(
                metadata={
                    "name": "erstellzeitpunktProtokoll",
                    "type": "Element",
                    "required": True,
                }
            )
            username_abfragender: None | str = field(
                default=None,
                metadata={
                    "name": "usernameAbfragender",
                    "type": "Element",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            name_betreuungsgericht: str = field(
                metadata={
                    "name": "nameBetreuungsgericht",
                    "type": "Element",
                    "required": True,
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                }
            )
            suchfelder: NachrichtZvrErstelleAbfrageProtokollOutput1000005.Fachdaten.Protokoll.Suchfelder = field(
                metadata={
                    "type": "Element",
                    "required": True,
                }
            )
            dokument: TypeGdsRefSgo = field(
                metadata={
                    "type": "Element",
                    "required": True,
                }
            )

            @dataclass(kw_only=True)
            class Suchfelder:
                abfragen_von: XmlDate = field(
                    metadata={
                        "name": "abfragen.von",
                        "type": "Element",
                        "required": True,
                    }
                )
                abfragen_bis: XmlDate = field(
                    metadata={
                        "name": "abfragen.bis",
                        "type": "Element",
                        "required": True,
                    }
                )

        @dataclass(kw_only=True)
        class Abfrageeintrag:
            """
            :ivar abfrage_id: Vom ZVR erzeugte Id der Abfrage.
            :ivar gericht_id: XJustizId des Gerichts, für welches ein
                Prokoll angefragt wird.
            :ivar abfragezeitpunkt:
            :ivar username_abfragender:
            :ivar geschaeftszeichen:
            :ivar suchfelder:
            :ivar antwortart:
            :ivar zeitpunkt_des_egvp_versands: Zeitpunkt des Versands
                der Auskunft an das sichere Postfach
            :ivar aehnlichkeitssuche: Gibt an, ob die Ähnlichkeitssuche
                in der Anfrage für ein oder mehrere Suchfelder genutzt
                wurde.
            :ivar registereintrag:
            """

            abfrage_id: str = field(
                metadata={
                    "name": "abfrageID",
                    "type": "Element",
                    "required": True,
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                }
            )
            gericht_id: CodeGdsGerichteTyp3 = field(
                metadata={
                    "name": "gerichtID",
                    "type": "Element",
                    "required": True,
                }
            )
            abfragezeitpunkt: XmlDateTime = field(
                metadata={
                    "type": "Element",
                    "required": True,
                }
            )
            username_abfragender: str = field(
                metadata={
                    "name": "usernameAbfragender",
                    "type": "Element",
                    "required": True,
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                }
            )
            geschaeftszeichen: str = field(
                metadata={
                    "type": "Element",
                    "required": True,
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                }
            )
            suchfelder: NachrichtZvrErstelleAbfrageProtokollOutput1000005.Fachdaten.Abfrageeintrag.Suchfelder = field(
                metadata={
                    "type": "Element",
                    "required": True,
                }
            )
            antwortart: CodeZvrAntwortart = field(
                metadata={
                    "type": "Element",
                    "required": True,
                }
            )
            zeitpunkt_des_egvp_versands: None | XmlDateTime = field(
                default=None,
                metadata={
                    "name": "zeitpunktDesEGVP_Versands",
                    "type": "Element",
                },
            )
            aehnlichkeitssuche: bool = field(
                metadata={
                    "type": "Element",
                    "required": True,
                }
            )
            registereintrag: list[
                NachrichtZvrErstelleAbfrageProtokollOutput1000005.Fachdaten.Abfrageeintrag.Registereintrag
            ] = field(
                default_factory=list,
                metadata={
                    "type": "Element",
                },
            )

            @dataclass(kw_only=True)
            class Suchfelder:
                nachname: None | str = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "pattern": r"( |'|[,-\.]|[A-Z]|[`-z]|~|¨|´|·|[À-Ö]|[Ø-ö]|[ø-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )
                vorname: None | str = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "pattern": r"( |'|[,-\.]|[A-Z]|[`-z]|~|¨|´|·|[À-Ö]|[Ø-ö]|[ø-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )
                geburtsname: None | str = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "pattern": r"( |'|[,-\.]|[A-Z]|[`-z]|~|¨|´|·|[À-Ö]|[Ø-ö]|[ø-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )
                geburtsdatum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "pattern": r"\d{4}((-\d{2}){0,1}-\d{2}){0,1}",
                    },
                )

            @dataclass(kw_only=True)
            class Registereintrag:
                """
                :ivar registernummer:
                :ivar treffer_id: Eindeutige Id des Abfragetreffers.
                :ivar vollmachtgeber:
                :ivar bevollmaechtigter:
                :ivar vielmelder:
                :ivar in_detail_geladen: gibt an, ob Meldung nur in
                    Trefferliste angezeigt oder Meldung im Detail
                    geöffnet wurde
                """

                registernummer: str = field(
                    metadata={
                        "type": "Element",
                        "required": True,
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    }
                )
                treffer_id: str = field(
                    metadata={
                        "name": "trefferID",
                        "type": "Element",
                        "required": True,
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    }
                )
                vollmachtgeber: TypeGdsRefRollennummer = field(
                    metadata={
                        "type": "Element",
                        "required": True,
                    }
                )
                bevollmaechtigter: list[TypeGdsRefRollennummer] = field(
                    default_factory=list,
                    metadata={
                        "type": "Element",
                        "max_occurs": 12,
                    },
                )
                vielmelder: None | TypeGdsRefRollennummer = field(
                    default=None,
                    metadata={
                        "type": "Element",
                    },
                )
                in_detail_geladen: bool = field(
                    metadata={
                        "name": "inDetailGeladen",
                        "type": "Attribute",
                        "required": True,
                    }
                )


@dataclass(kw_only=True)
class NachrichtZvrErstelleAuskunftInput1000010:
    class Meta:
        name = "nachricht.zvr.erstelleAuskunft.input.1000010"
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
    fachdaten: NachrichtZvrErstelleAuskunftInput1000010.Fachdaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        """
        :ivar abfrage_id: Vom ZVR erzeugte Id der Abfrage.
        :ivar auswahl_auskunfttyp:
        :ivar versandart: Legt fest, auf welchem Weg ZVR die Auskunft
            versendet. Es dürfen nur die Werte: "EGVP" oder "Download"
            genutzt werden.
        """

        abfrage_id: str = field(
            metadata={
                "name": "abfrageID",
                "type": "Element",
                "required": True,
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            }
        )
        auswahl_auskunfttyp: NachrichtZvrErstelleAuskunftInput1000010.Fachdaten.AuswahlAuskunfttyp = field(
            metadata={
                "type": "Element",
                "required": True,
            }
        )
        versandart: CodeZvrAntwortart = field(
            metadata={
                "type": "Element",
                "required": True,
            }
        )

        @dataclass(kw_only=True)
        class AuswahlAuskunfttyp:
            """
            :ivar registernummer: ZVR-Registernummer
            :ivar in_detail_geladen: Gibt an, ob Service Consumer
                Details zu Registrierung abgerufen hat.
            :ivar auskunfttyp: Legt fest, ob ZVR eine Positiv- oder
                Negativauskunft erstellt.
            """

            registernummer: None | str = field(
                default=None,
                metadata={
                    "type": "Element",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            in_detail_geladen: None | bool = field(
                default=None,
                metadata={
                    "name": "inDetailGeladen",
                    "type": "Element",
                },
            )
            auskunfttyp: list[str] = field(
                default_factory=list,
                metadata={
                    "type": "Element",
                    "max_occurs": 2,
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    "sequence": 1,
                },
            )


@dataclass(kw_only=True)
class NachrichtZvrErstelleAuskunftOutput1000011:
    class Meta:
        name = "nachricht.zvr.erstelleAuskunft.output.1000011"
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
    fachdaten: NachrichtZvrErstelleAuskunftOutput1000011.Fachdaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        auswahl_versandart: NachrichtZvrErstelleAuskunftOutput1000011.Fachdaten.AuswahlVersandart = field(
            metadata={
                "type": "Element",
                "required": True,
            }
        )

        @dataclass(kw_only=True)
        class AuswahlVersandart:
            """
            :ivar download: Auskunftsdokument als pdf
            :ivar egvp_versand_eingeleitet: Gibt an, ob der EGVP Versand
                eingeleitet wurde.
            """

            download: None | TypeGdsRefSgo = field(
                default=None,
                metadata={
                    "type": "Element",
                },
            )
            egvp_versand_eingeleitet: None | bool = field(
                default=None,
                metadata={
                    "name": "egvpVersandEingeleitet",
                    "type": "Element",
                },
            )


@dataclass(kw_only=True)
class NachrichtZvrLadeRegistrierungInput1000006:
    class Meta:
        name = "nachricht.zvr.ladeRegistrierung.input.1000006"
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
    fachdaten: NachrichtZvrLadeRegistrierungInput1000006.Fachdaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        """
        :ivar abfrage_id: Vom ZVR erzeugte Id einer früheren Abfrage.
        :ivar registernummer:
        """

        abfrage_id: str = field(
            metadata={
                "name": "abfrageID",
                "type": "Element",
                "required": True,
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            }
        )
        registernummer: str = field(
            metadata={
                "type": "Element",
                "required": True,
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            }
        )


@dataclass(kw_only=True)
class NachrichtZvrSucheRegistrierungInput1000008:
    class Meta:
        name = "nachricht.zvr.sucheRegistrierung.input.1000008"
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
    fachdaten: NachrichtZvrSucheRegistrierungInput1000008.Fachdaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        """
        :ivar geschaeftszeichen: Gerichtliches Geschäftszeichen
        :ivar suche:
        """

        geschaeftszeichen: str = field(
            metadata={
                "type": "Element",
                "required": True,
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            }
        )
        suche: NachrichtZvrSucheRegistrierungInput1000008.Fachdaten.Suche = (
            field(
                metadata={
                    "type": "Element",
                    "required": True,
                }
            )
        )

        @dataclass(kw_only=True)
        class Suche:
            """
            :ivar nachname:
            :ivar nachname_fehlertolerant: Gibt an, ob Ähnlichkeitssuche
                für den Nachnamen verwendet wird.
            :ivar vorname:
            :ivar vorname_fehlertolerant: Gibt an, ob Ähnlichkeitssuche
                für den Vornamen verwendet wird.
            :ivar geburtsname:
            :ivar geburtsname_fehlertolerant: Gibt an, ob
                Ähnlichkeitssuche für den Geburtsnamen verwendet wird.
            :ivar geburtsdatum:
            :ivar geburtsdatum_fehlertolerant: Gibt an, ob
                Ähnlichkeitssuche für das Geburtsdatum verwendet wird.
            :ivar menge:
            :ivar versatz:
            """

            nachname: None | str = field(
                default=None,
                metadata={
                    "type": "Element",
                    "pattern": r"( |'|[,-\.]|[A-Z]|[`-z]|~|¨|´|·|[À-Ö]|[Ø-ö]|[ø-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            nachname_fehlertolerant: None | bool = field(
                default=None,
                metadata={
                    "name": "nachname.fehlertolerant",
                    "type": "Element",
                },
            )
            vorname: None | str = field(
                default=None,
                metadata={
                    "type": "Element",
                    "pattern": r"( |'|[,-\.]|[A-Z]|[`-z]|~|¨|´|·|[À-Ö]|[Ø-ö]|[ø-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            vorname_fehlertolerant: None | bool = field(
                default=None,
                metadata={
                    "name": "vorname.fehlertolerant",
                    "type": "Element",
                },
            )
            geburtsname: None | str = field(
                default=None,
                metadata={
                    "type": "Element",
                    "pattern": r"( |'|[,-\.]|[A-Z]|[`-z]|~|¨|´|·|[À-Ö]|[Ø-ö]|[ø-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            geburtsname_fehlertolerant: None | bool = field(
                default=None,
                metadata={
                    "name": "geburtsname.fehlertolerant",
                    "type": "Element",
                },
            )
            geburtsdatum: None | XmlDate = field(
                default=None,
                metadata={
                    "type": "Element",
                },
            )
            geburtsdatum_fehlertolerant: None | bool = field(
                default=None,
                metadata={
                    "name": "geburtsdatum.fehlertolerant",
                    "type": "Element",
                },
            )
            menge: int = field(
                default=50,
                metadata={
                    "type": "Attribute",
                },
            )
            versatz: int = field(
                default=0,
                metadata={
                    "type": "Attribute",
                },
            )


@dataclass(kw_only=True)
class TypeZvrVollmachtdaten(TypeZvrVollmachtdatenBasis):
    """
    :ivar eintragungsart:
    :ivar kennzeichen_vollmacht: Vollmacht zur Erledigung von...
    :ivar weitere_angaben: z. B. Aufbewahrungsort der Vorsorgeurkunde -
        keine personenbezogenen Daten
    """

    class Meta:
        name = "Type.ZVR.Vollmachtdaten"

    eintragungsart: CodeZvrEintragungsart = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    kennzeichen_vollmacht: TypeZvrVollmachtdaten.KennzeichenVollmacht = field(
        metadata={
            "name": "kennzeichenVollmacht",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    weitere_angaben: None | str = field(
        default=None,
        metadata={
            "name": "weitereAngaben",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        },
    )

    @dataclass(kw_only=True)
    class KennzeichenVollmacht:
        """
        :ivar vermoegensangelegenheiten: Vermögensangelegenheiten
        :ivar gesundheitsvorsorge: Angelegenheit zur Gesundheitsvorsorge
        :ivar erklaerung_bgb1904: Maßnahmen nach § 1904 Abs. 1 S. 1 und
            Abs. 2 BGB ausdrücklich umfasst
        :ivar erklaerung_bgb1906a: Maßnahmen nach § 1906a Abs. 1 und 4
            BGB ausdrücklich umfasst
        :ivar aufenthaltsbestimmung: Angelegenheiten der
            Aufenthaltsbestimmung
        :ivar erklaerung_bgb1906: Maßnahmen nach § 1906 Abs. 1 und 4 BGB
            und bei Vorsorgeurkunden, die vor dem 22.07.2017 errichtet
            wurden auch Maßnahmen nach § 1906 Abs. 3 BGB a.F.
            ausdrücklich umfasst
        :ivar persoenliche_angelegenheiten: sonstige persönliche
            Angelegenheiten
        :ivar betreuungsverfuegung: für den Fall, dass das Gericht einen
            Betreuer bestellt (Betreuungsverfügung)
        :ivar patientenverfuegung: hinsichtlich Art und Umfang
            medizinischer Versorgung (Patientenverfügung)
        """

        vermoegensangelegenheiten: bool = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        gesundheitsvorsorge: bool = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        erklaerung_bgb1904: bool = field(
            metadata={
                "name": "erklaerung.BGB1904",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        erklaerung_bgb1906a: bool = field(
            metadata={
                "name": "erklaerung.BGB1906a",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        aufenthaltsbestimmung: bool = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        erklaerung_bgb1906: bool = field(
            metadata={
                "name": "erklaerung.BGB1906",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        persoenliche_angelegenheiten: bool = field(
            metadata={
                "name": "persoenlicheAngelegenheiten",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        betreuungsverfuegung: bool = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        patientenverfuegung: bool = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )


@dataclass(kw_only=True)
class NachrichtZvrSucheRegistrierungOutput1000009:
    class Meta:
        name = "nachricht.zvr.sucheRegistrierung.output.1000009"
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
    fachdaten: NachrichtZvrSucheRegistrierungOutput1000009.Fachdaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        """
        :ivar abfrage_id: Vom ZVR erzeugte Id der Abfrage, welche später
            beim Laden weiterer Daten und bei der Erstellung eines
            Protokolls genutzt wird.
        :ivar suchergebnis:
        """

        abfrage_id: str = field(
            metadata={
                "name": "abfrageID",
                "type": "Element",
                "required": True,
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            }
        )
        suchergebnis: NachrichtZvrSucheRegistrierungOutput1000009.Fachdaten.Suchergebnis = field(
            metadata={
                "type": "Element",
                "required": True,
            }
        )

        @dataclass(kw_only=True)
        class Suchergebnis:
            registereintrag: list[
                NachrichtZvrSucheRegistrierungOutput1000009.Fachdaten.Suchergebnis.Registereintrag
            ] = field(
                default_factory=list,
                metadata={
                    "type": "Element",
                },
            )
            menge: int = field(
                metadata={
                    "type": "Attribute",
                    "required": True,
                }
            )
            menge_insgesamt: int = field(
                metadata={
                    "name": "menge.insgesamt",
                    "type": "Attribute",
                    "required": True,
                }
            )
            versatz: int = field(
                metadata={
                    "type": "Attribute",
                    "required": True,
                }
            )

            @dataclass(kw_only=True)
            class Registereintrag:
                treffer_id: str = field(
                    metadata={
                        "name": "trefferID",
                        "type": "Element",
                        "required": True,
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    }
                )
                vollmachtdaten: TypeZvrVollmachtdatenBasis = field(
                    metadata={
                        "type": "Element",
                        "required": True,
                    }
                )
                vollmachtgeber: TypeGdsRefRollennummer = field(
                    metadata={
                        "type": "Element",
                        "required": True,
                    }
                )


@dataclass(kw_only=True)
class NachrichtZvrLadeRegistrierungOutput1000007:
    class Meta:
        name = "nachricht.zvr.ladeRegistrierung.output.1000007"
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
    fachdaten: NachrichtZvrLadeRegistrierungOutput1000007.Fachdaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        registerverlauf: NachrichtZvrLadeRegistrierungOutput1000007.Fachdaten.Registerverlauf = field(
            metadata={
                "type": "Element",
                "required": True,
            }
        )

        @dataclass(kw_only=True)
        class Registerverlauf:
            registereintrag: list[
                NachrichtZvrLadeRegistrierungOutput1000007.Fachdaten.Registerverlauf.Registereintrag
            ] = field(
                default_factory=list,
                metadata={
                    "type": "Element",
                    "min_occurs": 1,
                },
            )

            @dataclass(kw_only=True)
            class Registereintrag:
                """
                :ivar vollmachtdaten:
                :ivar vollmachtgeber:
                :ivar bevollmaechtigter:
                :ivar vielmelder:
                :ivar aktueller_eintrag: gibt an, ob der Eintrag der
                    aktuellste im Registverlauf ist
                """

                vollmachtdaten: TypeZvrVollmachtdaten = field(
                    metadata={
                        "type": "Element",
                        "required": True,
                    }
                )
                vollmachtgeber: TypeGdsRefRollennummer = field(
                    metadata={
                        "type": "Element",
                        "required": True,
                    }
                )
                bevollmaechtigter: list[
                    NachrichtZvrLadeRegistrierungOutput1000007.Fachdaten.Registerverlauf.Registereintrag.Bevollmaechtigter
                ] = field(
                    default_factory=list,
                    metadata={
                        "type": "Element",
                        "max_occurs": 12,
                    },
                )
                vielmelder: None | TypeGdsRefRollennummer = field(
                    default=None,
                    metadata={
                        "type": "Element",
                    },
                )
                aktueller_eintrag: bool = field(
                    init=False,
                    default=True,
                    metadata={
                        "name": "aktuellerEintrag",
                        "type": "Attribute",
                    },
                )

                @dataclass(kw_only=True)
                class Bevollmaechtigter:
                    referenzierung_bevollmaechtigter: TypeGdsRefRollennummer = field(
                        metadata={
                            "name": "referenzierungBevollmaechtigter",
                            "type": "Element",
                            "required": True,
                        }
                    )
                    weitere_angaben_bevollmaechtigter: None | str = field(
                        default=None,
                        metadata={
                            "name": "weitereAngabenBevollmaechtigter",
                            "type": "Element",
                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                        },
                    )
