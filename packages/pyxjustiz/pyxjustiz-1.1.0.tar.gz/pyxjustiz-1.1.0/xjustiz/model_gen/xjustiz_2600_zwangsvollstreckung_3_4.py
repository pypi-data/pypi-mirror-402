from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from xsdata.models.datatype import XmlDate, XmlPeriod, XmlTime

from xjustiz.model_gen.xjustiz_0000_grunddatensatz_3_6 import (
    TypeGdsGrunddaten,
    TypeGdsNachrichtenkopf,
    TypeGdsRefBankverbindung,
    TypeGdsRefRollennummer,
    TypeGdsSchriftgutobjekte,
    TypeGdsXdomeaZeitraumType,
)
from xjustiz.model_gen.xjustiz_0010_cl_allgemein_3_7 import (
    CodeGdsAnschriftstyp,
    CodeGdsFamilienstand,
    CodeGdsIntervall,
)
from xjustiz.model_gen.xjustiz_0020_cl_gerichte_3_3 import CodeGdsGerichteTyp3
from xjustiz.model_gen.xjustiz_2610_cl_zwangsvollstreckung_3_2 import (
    CodeZvstrAltersstufenUnterhalt,
    CodeZvstrAnlage,
    CodeZvstrAntragZustellung,
    CodeZvstrEntscheidungsumfangPfUeb,
    CodeZvstrTitelart,
    CodeZvstrUnterhaltsberechtigter,
    CodeZvstrZeitraumUnterhaltsforderung,
    CodeZvstrZinsmethodeTyp3,
)

__NAMESPACE__ = "http://www.xjustiz.de"


@dataclass(kw_only=True)
class TypeZvstrAnspruchPfUeb:
    class Meta:
        name = "Type.ZVSTR.Anspruch.PfUEB"

    auswahl_forderung_aus_anspruch: TypeZvstrAnspruchPfUeb.AuswahlForderungAusAnspruch = field(
        metadata={
            "name": "auswahl_forderungAusAnspruch",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class AuswahlForderungAusAnspruch:
        """
        :ivar anspruch_modul_e: Forderungen gegenüber Arbeitgebern
        :ivar anspruch_modul_f: Forderungen gegenüber Agentur für
            Arbeit, Versicherungsträger oder Versorgungseinrichtung
        :ivar anspruch_modul_g: Forderungen gegenüber dem Finanzamt
        :ivar anspruch_modul_h: Forderungen und sonstige Rechte
            gegenüber Kreditinstituten
        :ivar anspruch_modul_i: Forderungen und sonstige Rechte
            gegenüber Bausparkassen
        :ivar anspruch_modul_j: Forderungen und sonstige Rechte
            gegenüber Versicherungsgesellschaften
        :ivar anspruch_modul_k: Weitere Forderungen, Ansprüche und
            Vermögensrechte
        """

        anspruch_modul_e: (
            None
            | TypeZvstrAnspruchPfUeb.AuswahlForderungAusAnspruch.AnspruchModulE
        ) = field(
            default=None,
            metadata={
                "name": "anspruch.modulE",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        anspruch_modul_f: (
            None
            | TypeZvstrAnspruchPfUeb.AuswahlForderungAusAnspruch.AnspruchModulF
        ) = field(
            default=None,
            metadata={
                "name": "anspruch.modulF",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        anspruch_modul_g: (
            None
            | TypeZvstrAnspruchPfUeb.AuswahlForderungAusAnspruch.AnspruchModulG
        ) = field(
            default=None,
            metadata={
                "name": "anspruch.modulG",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        anspruch_modul_h: (
            None
            | TypeZvstrAnspruchPfUeb.AuswahlForderungAusAnspruch.AnspruchModulH
        ) = field(
            default=None,
            metadata={
                "name": "anspruch.modulH",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        anspruch_modul_i: (
            None
            | TypeZvstrAnspruchPfUeb.AuswahlForderungAusAnspruch.AnspruchModulI
        ) = field(
            default=None,
            metadata={
                "name": "anspruch.modulI",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        anspruch_modul_j: (
            None
            | TypeZvstrAnspruchPfUeb.AuswahlForderungAusAnspruch.AnspruchModulJ
        ) = field(
            default=None,
            metadata={
                "name": "anspruch.modulJ",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        anspruch_modul_k: (
            None
            | TypeZvstrAnspruchPfUeb.AuswahlForderungAusAnspruch.AnspruchModulK
        ) = field(
            default=None,
            metadata={
                "name": "anspruch.modulK",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )

        @dataclass(kw_only=True)
        class AnspruchModulE:
            """
            :ivar modul_nr: Eindeutige Nummer des Moduls zur
                Referenzierung
            :ivar arbeitseinkommen_und_sachbezuege:
            :ivar erstattungsanspruch_jahresausgleich:
            :ivar kurzarbeitergeld:
            :ivar beschreibung_sonstige_ansprueche:
            """

            modul_nr: int = field(
                metadata={
                    "name": "modulNr",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            arbeitseinkommen_und_sachbezuege: None | str = field(
                default=None,
                metadata={
                    "name": "arbeitseinkommenUndSachbezuege",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            erstattungsanspruch_jahresausgleich: (
                None
                | TypeZvstrAnspruchPfUeb.AuswahlForderungAusAnspruch.AnspruchModulE.ErstattungsanspruchJahresausgleich
            ) = field(
                default=None,
                metadata={
                    "name": "erstattungsanspruch.jahresausgleich",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            kurzarbeitergeld: None | str = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            beschreibung_sonstige_ansprueche: list[str] = field(
                default_factory=list,
                metadata={
                    "name": "beschreibung.sonstigeAnsprueche",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )

            @dataclass(kw_only=True)
            class ErstattungsanspruchJahresausgleich:
                erstattungsanspruch_bezeichnung: str = field(
                    init=False,
                    default="2. Forderung auf Auszahlung des als Überzahlung jeweils auszugleichenden Erstattungsbetrages aus dem durchgeführten Lohnsteuer-Jahresausgleich sowie aus dem Kirchenlohnsteuer-Jahresausgleich für das Kalenderjahr (siehe Folgeelement 'erstattungsanspruch.abKalenderjahr') und für alle folgenden Kalenderjahre",
                    metadata={
                        "name": "erstattungsanspruch.bezeichnung",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "required": True,
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )
                erstattungsanspruch_ab_kalenderjahr: XmlPeriod = field(
                    metadata={
                        "name": "erstattungsanspruch.abKalenderjahr",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "required": True,
                    }
                )

        @dataclass(kw_only=True)
        class AnspruchModulF:
            """
            :ivar modul_nr: Eindeutige Nummer des Moduls zur
                Referenzierung
            :ivar auswahl_sozialtraeger:
            :ivar bezeichnung_der_geldleistung:
            :ivar konto_oder_versicherungs_oder_mitglieds_nummer:
            :ivar beschreibung_sonstige_ansprueche:
            """

            modul_nr: int = field(
                metadata={
                    "name": "modulNr",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            auswahl_sozialtraeger: TypeZvstrAnspruchPfUeb.AuswahlForderungAusAnspruch.AnspruchModulF.AuswahlSozialtraeger = field(
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            bezeichnung_der_geldleistung: None | str = field(
                default=None,
                metadata={
                    "name": "bezeichnungDerGeldleistung",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            konto_oder_versicherungs_oder_mitglieds_nummer: None | str = field(
                default=None,
                metadata={
                    "name": "kontoOderVersicherungsOderMitgliedsNummer",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            beschreibung_sonstige_ansprueche: list[str] = field(
                default_factory=list,
                metadata={
                    "name": "beschreibung.sonstigeAnsprueche",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )

            @dataclass(kw_only=True)
            class AuswahlSozialtraeger:
                agentur_fuer_arbeit: None | bool = field(
                    default=None,
                    metadata={
                        "name": "agenturFuerArbeit",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                    },
                )
                versicherungstraeger: None | bool = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                    },
                )
                versorgungseinrichtung: None | bool = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                    },
                )

        @dataclass(kw_only=True)
        class AnspruchModulG:
            """
            :ivar modul_nr: Eindeutige Nummer des Moduls zur
                Referenzierung
            :ivar kalenderjahr_erstattung_einkommen_st:
            :ivar alle_frueheren_kalenderjahre:
            :ivar beschreibung_sonstige_ansprueche:
            """

            modul_nr: int = field(
                metadata={
                    "name": "modulNr",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            kalenderjahr_erstattung_einkommen_st: None | XmlPeriod = field(
                default=None,
                metadata={
                    "name": "kalenderjahr.erstattungEinkommenSt",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            alle_frueheren_kalenderjahre: None | bool = field(
                default=None,
                metadata={
                    "name": "alleFrueherenKalenderjahre",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            beschreibung_sonstige_ansprueche: list[str] = field(
                default_factory=list,
                metadata={
                    "name": "beschreibung.sonstigeAnsprueche",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )

        @dataclass(kw_only=True)
        class AnspruchModulH:
            """
            :ivar modul_nr: Eindeutige Nummer des Moduls zur
                Referenzierung
            :ivar pfaendung_girokonto:
            :ivar pfaendung_sparguthaben_festgeldkonto:
            :ivar darlehensvaluta:
            :ivar pfaendung_wertpapierkonto_gegenkonto:
            :ivar bankschliessfach:
            :ivar herausgabe_wertpapiere:
            :ivar beschreibung_sonstige_ansprueche:
            """

            modul_nr: int = field(
                metadata={
                    "name": "modulNr",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            pfaendung_girokonto: None | str = field(
                default=None,
                metadata={
                    "name": "pfaendungGirokonto",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            pfaendung_sparguthaben_festgeldkonto: None | str = field(
                default=None,
                metadata={
                    "name": "pfaendungSparguthabenFestgeldkonto",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            darlehensvaluta: None | str = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            pfaendung_wertpapierkonto_gegenkonto: None | str = field(
                default=None,
                metadata={
                    "name": "pfaendungWertpapierkonto.gegenkonto",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            bankschliessfach: None | bool = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            herausgabe_wertpapiere: None | bool = field(
                default=None,
                metadata={
                    "name": "herausgabeWertpapiere",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            beschreibung_sonstige_ansprueche: list[str] = field(
                default_factory=list,
                metadata={
                    "name": "beschreibung.sonstigeAnsprueche",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )

        @dataclass(kw_only=True)
        class AnspruchModulI:
            """
            :ivar modul_nr: Eindeutige Nummer des Moduls zur
                Referenzierung
            :ivar bausparsumme_in_euro:
            :ivar bausparvertrag_nr:
            :ivar auszahlung_bausparguthaben:
            :ivar auszahlung_sparbeitraege:
            :ivar rueckzahlung_sparguthaben:
            :ivar recht_zur_kuendigung_und_aenderung_des_vertrages:
            :ivar beschreibung_sonstige_ansprueche:
            """

            modul_nr: int = field(
                metadata={
                    "name": "modulNr",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            bausparsumme_in_euro: None | Decimal = field(
                default=None,
                metadata={
                    "name": "bausparsumme.inEuro",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            bausparvertrag_nr: None | str = field(
                default=None,
                metadata={
                    "name": "bausparvertrag.nr",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            auszahlung_bausparguthaben: None | str = field(
                default=None,
                metadata={
                    "name": "auszahlungBausparguthaben",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            auszahlung_sparbeitraege: None | str = field(
                default=None,
                metadata={
                    "name": "auszahlungSparbeitraege",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            rueckzahlung_sparguthaben: None | str = field(
                default=None,
                metadata={
                    "name": "rueckzahlungSparguthaben",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            recht_zur_kuendigung_und_aenderung_des_vertrages: None | str = (
                field(
                    default=None,
                    metadata={
                        "name": "rechtZurKuendigungUndAenderungDesVertrages",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )
            )
            beschreibung_sonstige_ansprueche: list[str] = field(
                default_factory=list,
                metadata={
                    "name": "beschreibung.sonstigeAnsprueche",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )

        @dataclass(kw_only=True)
        class AnspruchModulJ:
            """
            :ivar modul_nr: Eindeutige Nummer des Moduls zur
                Referenzierung
            :ivar zahlung_versicherungssumme:
            :ivar bestimmung_auszahlung:
            :ivar kuendigung_lebens_oder_rentenversicherungsvertrag:
            :ivar beschreibung_sonstige_ansprueche:
            """

            modul_nr: int = field(
                metadata={
                    "name": "modulNr",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            zahlung_versicherungssumme: None | str = field(
                default=None,
                metadata={
                    "name": "zahlungVersicherungssumme",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            bestimmung_auszahlung: None | str = field(
                default=None,
                metadata={
                    "name": "bestimmungAuszahlung",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            kuendigung_lebens_oder_rentenversicherungsvertrag: None | str = (
                field(
                    default=None,
                    metadata={
                        "name": "kuendigung.lebensOderRentenversicherungsvertrag",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )
            )
            beschreibung_sonstige_ansprueche: list[str] = field(
                default_factory=list,
                metadata={
                    "name": "beschreibung.sonstigeAnsprueche",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )

        @dataclass(kw_only=True)
        class AnspruchModulK:
            """
            :ivar modul_nr: Eindeutige Nummer des Moduls zur
                Referenzierung
            :ivar beschreibung_weitere_forderungen:
            """

            modul_nr: int = field(
                metadata={
                    "name": "modulNr",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            beschreibung_weitere_forderungen: str = field(
                metadata={
                    "name": "beschreibung.weitereForderungen",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                }
            )


@dataclass(kw_only=True)
class TypeZvstrElektronischUebermittelteAntraege:
    """
    :ivar uebersendung_ausfertigung_nach_mitteilung_aktenzeichen:
    :ivar uebersendung_ausfertigung_gleichzeitig: Hierüber kann
        mitgeteilt werden, ob die Ausfertigungen der Vollstreckungstitel
        gleichzeitig auf dem Postweg übersandt werden sollen.
    :ivar beigefuegt_abschrift_vollstreckungsbescheid: Hierüber kann
        mitgeteilt werden, ob eine Abschrift des
        Vollstreckungsbescheides nebst Zustellungsbescheinigung als
        elektronisches Dokument beigefügt wurde.
    """

    class Meta:
        name = "Type.ZVSTR.ElektronischUebermittelteAntraege"

    uebersendung_ausfertigung_nach_mitteilung_aktenzeichen: None | bool = (
        field(
            default=None,
            metadata={
                "name": "uebersendungAusfertigung.nachMitteilungAktenzeichen",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
    )
    uebersendung_ausfertigung_gleichzeitig: None | bool = field(
        default=None,
        metadata={
            "name": "uebersendungAusfertigung.gleichzeitig",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    beigefuegt_abschrift_vollstreckungsbescheid: None | bool = field(
        default=None,
        metadata={
            "name": "beigefuegtAbschriftVollstreckungsbescheid",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )


@dataclass(kw_only=True)
class TypeZvstrFreieEingabe:
    class Meta:
        name = "Type.ZVSTR.FreieEingabe"

    freie_eingabe_bezeichnung: str = field(
        metadata={
            "name": "freieEingabe.bezeichnung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )
    freie_eingabe_wert: Decimal = field(
        metadata={
            "name": "freieEingabe.wert",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )


@dataclass(kw_only=True)
class TypeZvstrGesamtkosten:
    class Meta:
        name = "Type.ZVSTR.Gesamtkosten"

    gesamtkosten: None | TypeZvstrGesamtkosten.Gesamtkosten = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    restkosten_aus_gesamtkosten: (
        None | TypeZvstrGesamtkosten.RestkostenAusGesamtkosten
    ) = field(
        default=None,
        metadata={
            "name": "restkostenAusGesamtkosten",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    teilkosten_aus_gesamtkosten: (
        None | TypeZvstrGesamtkosten.TeilkostenAusGesamtkosten
    ) = field(
        default=None,
        metadata={
            "name": "teilkostenAusGesamtkosten",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )

    @dataclass(kw_only=True)
    class Gesamtkosten:
        gesamtkosten_in_euro: Decimal = field(
            metadata={
                "name": "gesamtkosten.inEuro",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )

    @dataclass(kw_only=True)
    class RestkostenAusGesamtkosten:
        gesamtkosten_in_euro: Decimal = field(
            metadata={
                "name": "gesamtkosten.inEuro",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        restkosten_in_euro: Decimal = field(
            metadata={
                "name": "restkosten.inEuro",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )

    @dataclass(kw_only=True)
    class TeilkostenAusGesamtkosten:
        gesamtkosten_in_euro: Decimal = field(
            metadata={
                "name": "gesamtkosten.inEuro",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        teilkosten_in_euro: Decimal = field(
            metadata={
                "name": "teilkosten.inEuro",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )


@dataclass(kw_only=True)
class TypeZvstrHauptforderung:
    class Meta:
        name = "Type.ZVSTR.Hauptforderung"

    hauptforderung: None | TypeZvstrHauptforderung.Hauptforderung = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    restforderung_aus_hauptforderung: (
        None | TypeZvstrHauptforderung.RestforderungAusHauptforderung
    ) = field(
        default=None,
        metadata={
            "name": "restforderungAusHauptforderung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    teilforderung_aus_hauptforderung: (
        None | TypeZvstrHauptforderung.TeilforderungAusHauptforderung
    ) = field(
        default=None,
        metadata={
            "name": "teilforderungAusHauptforderung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )

    @dataclass(kw_only=True)
    class Hauptforderung:
        hauptforderung_in_euro: Decimal = field(
            metadata={
                "name": "hauptforderung.inEuro",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )

    @dataclass(kw_only=True)
    class RestforderungAusHauptforderung:
        hauptforderung_in_euro: Decimal = field(
            metadata={
                "name": "hauptforderung.inEuro",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        restforderung_in_euro: Decimal = field(
            metadata={
                "name": "restforderung.inEuro",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )

    @dataclass(kw_only=True)
    class TeilforderungAusHauptforderung:
        hauptforderung_in_euro: Decimal = field(
            metadata={
                "name": "hauptforderung.inEuro",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        teilforderung_in_euro: Decimal = field(
            metadata={
                "name": "teilforderung.inEuro",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )


@dataclass(kw_only=True)
class TypeZvstrRefTitelnummer:
    """
    :ivar ref_titelnummer: Hier wird auf die Titelnummer eines
        Vollstreckungstitels referenziert.
    """

    class Meta:
        name = "Type.ZVSTR.Ref.Titelnummer"

    ref_titelnummer: str = field(
        metadata={
            "name": "ref.titelnummer",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )


@dataclass(kw_only=True)
class TypeZvstrSaeumniszuschlag:
    class Meta:
        name = "Type.ZVSTR.Saeumniszuschlag"

    gesetzliche_grundlage: str = field(
        metadata={
            "name": "gesetzlicheGrundlage",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )
    zugrundeliegender_betrag: Decimal = field(
        metadata={
            "name": "zugrundeliegenderBetrag",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    beginn: XmlDate = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    ende: None | XmlDate = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    saeumniszuschlag_betrag: None | Decimal = field(
        default=None,
        metadata={
            "name": "saeumniszuschlag.betrag",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )


@dataclass(kw_only=True)
class TypeZvstrAnlagen:
    """
    :ivar art_der_anlage:
    :ivar bezeichnung: Auszufüllen, falls in Codeliste der Wert
        "sonstige" gewählt wurde
    """

    class Meta:
        name = "Type.ZVSTR.Anlagen"

    art_der_anlage: CodeZvstrAnlage = field(
        metadata={
            "name": "artDerAnlage",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    bezeichnung: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        },
    )


@dataclass(kw_only=True)
class TypeZvstrAnordnungenGegenueberSchuldner:
    class Meta:
        name = "Type.ZVSTR.Anordnungen.GegenueberSchuldner"

    auswahl_anordnungen_gegenueber_schuldner: TypeZvstrAnordnungenGegenueberSchuldner.AuswahlAnordnungenGegenueberSchuldner = field(
        metadata={
            "name": "auswahl_anordnungen.gegenueberSchuldner",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    ref_schuldner: None | TypeGdsRefRollennummer = field(
        default=None,
        metadata={
            "name": "ref.schuldner",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    ref_drittschuldner: None | TypeGdsRefRollennummer = field(
        default=None,
        metadata={
            "name": "ref.drittschuldner",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )

    @dataclass(kw_only=True)
    class AuswahlAnordnungenGegenueberSchuldner:
        lohn_oder_gehaltsabrechnungen_herausgabe: None | bool = field(
            default=None,
            metadata={
                "name": "lohnOderGehaltsabrechnungen.herausgabe",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        sparurkunden_herausgabe: None | bool = field(
            default=None,
            metadata={
                "name": "sparurkunden.herausgabe",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        kontoauszuege_herausgabe: None | bool = field(
            default=None,
            metadata={
                "name": "kontoauszuege.herausgabe",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        zugang_schliessfach: None | bool = field(
            default=None,
            metadata={
                "name": "zugang.schliessfach",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        wertpapier_herausgabe: None | bool = field(
            default=None,
            metadata={
                "name": "wertpapier.herausgabe",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        versicherungspolice_herausgabe: None | bool = field(
            default=None,
            metadata={
                "name": "versicherungspolice.herausgabe",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        abschrift_bescheinigung_nach903_abs1_satz2_zpo_herausgabe: (
            None | bool
        ) = field(
            default=None,
            metadata={
                "name": "abschriftBescheinigungNach903Abs1Satz2ZPO.herausgabe",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        anordnungen_weitere: None | str = field(
            default=None,
            metadata={
                "name": "anordnungen.weitere",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            },
        )


@dataclass(kw_only=True)
class TypeZvstrBeteiligterZusatz:
    """
    Für den im Grunddatensatz angegebenen Beteiligten werden weitergehende
    Informationen übergeben.

    :ivar ref_beteiligter: Referenz auf die Rollennummer des im
        Grunddatensatz angegebenen Beteiligten
    :ivar anrede_freitext:
    :ivar glaeubiger_nicht_vorsteuerabzugsberechtigt:
    :ivar betreuer_mit_ausschliesslichkeitserklaerung: Mit diesem
        Element kann angegeben werden, ob der gerichtlich bestellte
        Betreuer eine Ausschließlichkeitserklärung abgegeben hat (§ 53
        Absatz 2 ZPO).
    """

    class Meta:
        name = "Type.ZVSTR.Beteiligter.Zusatz"

    ref_beteiligter: TypeGdsRefRollennummer = field(
        metadata={
            "name": "ref.beteiligter",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    anrede_freitext: None | str = field(
        default=None,
        metadata={
            "name": "anrede.freitext",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        },
    )
    glaeubiger_nicht_vorsteuerabzugsberechtigt: None | bool = field(
        default=None,
        metadata={
            "name": "glaeubigerNichtVorsteuerabzugsberechtigt",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    betreuer_mit_ausschliesslichkeitserklaerung: None | bool = field(
        default=None,
        metadata={
            "name": "betreuerMitAusschliesslichkeitserklaerung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )


@dataclass(kw_only=True)
class TypeZvstrErmittlungSchuldneranschrift:
    """
    :ivar traeger_gesetzliche_rentenversicherung: Erhebung des Namens
        und der Vornamen oder der Firma sowie der Anschrift der
        derzeitigen Arbeitgeber des Schuldners bei den Trägern der
        gesetzlichen Rentenversicherung.
    :ivar berufsstaendische_versorgungseinrichtung: Erhebung des Namens
        und der Vornamen oder der Firma sowie der Anschrift der
        derzeitigen Arbeitgeber des Schuldners bei der folgenden
        berufsständischen Versorgungseinrichtung im Sinne des § 6 Absatz
        1 Satz 1 Nummer 1 SGB VI.
    """

    class Meta:
        name = "Type.ZVSTR.ErmittlungSchuldneranschrift"

    traeger_gesetzliche_rentenversicherung: None | bool = field(
        default=None,
        metadata={
            "name": "traegerGesetzlicheRentenversicherung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    berufsstaendische_versorgungseinrichtung: (
        None
        | TypeZvstrErmittlungSchuldneranschrift.BerufsstaendischeVersorgungseinrichtung
    ) = field(
        default=None,
        metadata={
            "name": "berufsstaendischeVersorgungseinrichtung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )

    @dataclass(kw_only=True)
    class BerufsstaendischeVersorgungseinrichtung:
        """
        :ivar ref_berufsstaendische_versorgungseinrichtung:
        :ivar anhaltspunkte: Tatsächliche Anhaltspunkte dafür, dass der
            Schuldner Mitglied dieser berufsständischen
            Versorgungseinrichtung ist.
        """

        ref_berufsstaendische_versorgungseinrichtung: TypeGdsRefRollennummer = field(
            metadata={
                "name": "ref.berufsstaendischeVersorgungseinrichtung",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        anhaltspunkte: str = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            }
        )


@dataclass(kw_only=True)
class TypeZvstrRenten:
    class Meta:
        name = "Type.ZVSTR.Renten"

    rente_in_hoehe_von: Decimal = field(
        metadata={
            "name": "rente.inHoeheVon",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    zahlungsintervall: CodeGdsIntervall = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    laufend_ab: str = field(
        metadata={
            "name": "laufendAb",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )
    zahlbar_am: str = field(
        metadata={
            "name": "zahlbarAm",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )
    auswahl_zahlungszeitraum: TypeZvstrRenten.AuswahlZahlungszeitraum = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class AuswahlZahlungszeitraum:
        zahlungszeitraum: None | CodeGdsIntervall = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        zahlung_bis: None | str = field(
            default=None,
            metadata={
                "name": "zahlungBis",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            },
        )


@dataclass(kw_only=True)
class TypeZvstrVollstreckungstitel:
    """
    :ivar titelnummer: Wird aus mehr als einem Vollstreckungstitel
        vollstreckt, ist jeweils die laufende Nummer anzugeben.
    :ivar titelart:
    :ivar sonstiger_titel: Dieses Feld ist z.B. zu füllen, wenn im Feld
        Titelart 'Sonstiger' ausgewählt worden ist.
    :ivar aktenzeichen:
    :ivar auswahl_ausstellende_behoerde: Wer hat den Vollstreckungstitel
        ausgestellt / erlassen?
    :ivar titeldatum:
    """

    class Meta:
        name = "Type.ZVSTR.Vollstreckungstitel"

    titelnummer: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        },
    )
    titelart: CodeZvstrTitelart = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    sonstiger_titel: None | str = field(
        default=None,
        metadata={
            "name": "sonstigerTitel",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        },
    )
    aktenzeichen: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
        }
    )
    auswahl_ausstellende_behoerde: TypeZvstrVollstreckungstitel.AuswahlAusstellendeBehoerde = field(
        metadata={
            "name": "auswahl_ausstellendeBehoerde",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    titeldatum: XmlDate = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class AuswahlAusstellendeBehoerde:
        gericht: None | CodeGdsGerichteTyp3 = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        sonstige: None | str = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "pattern": r"([ -~]|[¡-¬]|[®-ž]|[Ƈ-ƈ]|Ə|ƒ|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|ʰ|ʳ|[ʹ-ʺ]|[ʾ-ʿ]|ˆ|ˈ|ˌ|˜|ˢ|Ά|[Έ-Ί]|Ό|[Ύ-Ρ]|[Σ-ώ]|ᵈ|ᵗ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|[‘-‚]|[“-„]|[†-‡]|…|‰|[′-″]|[‹-›]|⁰|[⁴-⁹]|[ⁿ-₉]|€|™|∞|[≤-≥]|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            },
        )


@dataclass(kw_only=True)
class TypeZvstrZinsen:
    class Meta:
        name = "Type.ZVSTR.Zinsen"

    zu_verzinsender_betrag: Decimal = field(
        metadata={
            "name": "zuVerzinsenderBetrag",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    zinsangaben: TypeZvstrZinsen.Zinsangaben = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    zinsbetrag_in_euro: None | Decimal = field(
        default=None,
        metadata={
            "name": "zinsbetrag.inEuro",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )

    @dataclass(kw_only=True)
    class Zinsangaben:
        """
        :ivar zinssatz: Erforderlich bei Zinsenberechung
        :ivar zinsmethode: Wenn ein Zinssatz angegeben wird, so muss
            auch die Zinssatzmethode angegegen werden.
        :ivar zinsbeginndatum: Erforderlich bei Zinsenberechung
        :ivar zinsendedatum:
        """

        zinssatz: None | Decimal = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        zinsmethode: None | CodeZvstrZinsmethodeTyp3 = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        zinsbeginndatum: None | XmlDate = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        zinsendedatum: None | XmlDate = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )


@dataclass(kw_only=True)
class TypeZvstrForderungshoehe:
    """
    :ivar auswahl_forderung:
    :ivar zinsen_vollstreckungstitel: Hier können die (Teil-/Rest-)
        Zinsen wie im Vollstreckungstitel ausgerechnet eingetragen
        werden.
    :ivar zinsen:
    :ivar saeumniszuschlaege:
    :ivar freie_eingabe:
    """

    class Meta:
        name = "Type.ZVSTR.Forderungshoehe"

    auswahl_forderung: None | TypeZvstrHauptforderung = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    zinsen_vollstreckungstitel: None | Decimal = field(
        default=None,
        metadata={
            "name": "zinsen.vollstreckungstitel",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    zinsen: list[TypeZvstrZinsen] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    saeumniszuschlaege: list[TypeZvstrSaeumniszuschlag] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    freie_eingabe: list[TypeZvstrFreieEingabe] = field(
        default_factory=list,
        metadata={
            "name": "freieEingabe",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )


@dataclass(kw_only=True)
class TypeZvstrKostenforderung:
    """
    :ivar auswahl_kosten:
    :ivar zinsen_wie_titel: Hier können die (Teil-/Rest-) Zinsen wie im
        Vollstreckungsbescheid, Vollstreckungstitel oder
        Kostenfestsetzungsbeschluss ausgerechnet eingetragen werden.
    :ivar zinsen:
    """

    class Meta:
        name = "Type.ZVSTR.Kostenforderung"

    auswahl_kosten: TypeZvstrGesamtkosten = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    zinsen_wie_titel: None | Decimal = field(
        default=None,
        metadata={
            "name": "zinsenWieTitel",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    zinsen: list[TypeZvstrZinsen] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )


@dataclass(kw_only=True)
class NachrichtZvstrDurchsuchungsanordnung2600001:
    class Meta:
        name = "nachricht.zvstr.durchsuchungsanordnung.2600001"
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
    fachdaten: NachrichtZvstrDurchsuchungsanordnung2600001.Fachdaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        """
        :ivar beteiligter_zusatz: Für den im Grunddatensatz angegebenen
            Beteiligten werden weitergehende Informationen übergeben.
        :ivar antragsdaten:
        :ivar beschlussdaten:
        """

        beteiligter_zusatz: list[TypeZvstrBeteiligterZusatz] = field(
            default_factory=list,
            metadata={
                "name": "beteiligter.zusatz",
                "type": "Element",
            },
        )
        antragsdaten: (
            None
            | NachrichtZvstrDurchsuchungsanordnung2600001.Fachdaten.Antragsdaten
        ) = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )
        beschlussdaten: NachrichtZvstrDurchsuchungsanordnung2600001.Fachdaten.Beschlussdaten = field(
            metadata={
                "type": "Element",
                "required": True,
            }
        )

        @dataclass(kw_only=True)
        class Antragsdaten:
            antragsort: str = field(
                metadata={
                    "type": "Element",
                    "required": True,
                    "pattern": r"([ -~]|[¡-£]|¥|[§-¬]|[®-·]|[¹-»]|[¿-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                }
            )
            antragsdatum: XmlDate = field(
                metadata={
                    "type": "Element",
                    "required": True,
                }
            )
            angaben_zum_schuldner: TypeGdsRefRollennummer = field(
                metadata={
                    "name": "angabenZumSchuldner",
                    "type": "Element",
                    "required": True,
                }
            )
            kontaktdaten_antragsteller: list[TypeGdsRefRollennummer] = field(
                default_factory=list,
                metadata={
                    "name": "kontaktdaten.antragsteller",
                    "type": "Element",
                },
            )
            auswahl_erlass_beschluss_antrags_begruendung: NachrichtZvstrDurchsuchungsanordnung2600001.Fachdaten.Antragsdaten.AuswahlErlassBeschlussAntragsBegruendung = field(
                metadata={
                    "name": "auswahl_erlassBeschluss.antragsBegruendung",
                    "type": "Element",
                    "required": True,
                }
            )
            zusaetzliche_antraege: (
                None
                | NachrichtZvstrDurchsuchungsanordnung2600001.Fachdaten.Antragsdaten.ZusaetzlicheAntraege
            ) = field(
                default=None,
                metadata={
                    "name": "zusaetzlicheAntraege",
                    "type": "Element",
                },
            )
            vollstreckungshandlungen_anzahl: int = field(
                metadata={
                    "name": "vollstreckungshandlungen.anzahl",
                    "type": "Element",
                    "required": True,
                }
            )
            sendungsdaten_weitere_anlagen: list[TypeZvstrAnlagen] = field(
                default_factory=list,
                metadata={
                    "name": "sendungsdaten.weitereAnlagen",
                    "type": "Element",
                },
            )
            versicherung: (
                None
                | NachrichtZvstrDurchsuchungsanordnung2600001.Fachdaten.Antragsdaten.Versicherung
            ) = field(
                default=None,
                metadata={
                    "type": "Element",
                },
            )

            @dataclass(kw_only=True)
            class AuswahlErlassBeschlussAntragsBegruendung:
                antrags_begruendung_758a_abs_1_zpo: None | str = field(
                    default=None,
                    metadata={
                        "name": "antragsBegruendung.758aAbs.1ZPO",
                        "type": "Element",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )
                antrags_begruendung_758a_abs_4_zpo: None | str = field(
                    default=None,
                    metadata={
                        "name": "antragsBegruendung.758aAbs.4ZPO",
                        "type": "Element",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )
                antrags_begruendung_758a_abs_1_und_abs_4_zpo: (
                    None
                    | NachrichtZvstrDurchsuchungsanordnung2600001.Fachdaten.Antragsdaten.AuswahlErlassBeschlussAntragsBegruendung.AntragsBegruendung758AAbs1UndAbs4Zpo
                ) = field(
                    default=None,
                    metadata={
                        "name": "antragsBegruendung.758aAbs.1UndAbs.4ZPO",
                        "type": "Element",
                    },
                )

                @dataclass(kw_only=True)
                class AntragsBegruendung758AAbs1UndAbs4Zpo:
                    antrags_begruendung_758a_abs_1_zpo: str = field(
                        metadata={
                            "name": "antragsBegruendung.758aAbs.1ZPO",
                            "type": "Element",
                            "required": True,
                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                        }
                    )
                    antrags_begruendung_758a_abs_4_zpo: str = field(
                        metadata={
                            "name": "antragsBegruendung.758aAbs.4ZPO",
                            "type": "Element",
                            "required": True,
                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                        }
                    )

            @dataclass(kw_only=True)
            class ZusaetzlicheAntraege:
                antrag_erteilung_einer_ausfertigung: None | bool = field(
                    default=None,
                    metadata={
                        "name": "antrag.erteilungEinerAusfertigung",
                        "type": "Element",
                    },
                )
                antrag_direktweiterleitung_an_gv: None | bool = field(
                    default=None,
                    metadata={
                        "name": "antrag.direktweiterleitungAnGV",
                        "type": "Element",
                    },
                )
                antrag_absehen_anhoerung_schuldner: (
                    None
                    | NachrichtZvstrDurchsuchungsanordnung2600001.Fachdaten.Antragsdaten.ZusaetzlicheAntraege.AntragAbsehenAnhoerungSchuldner
                ) = field(
                    default=None,
                    metadata={
                        "name": "antrag.absehen.anhoerungSchuldner",
                        "type": "Element",
                    },
                )
                weiterer_antrag: list[str] = field(
                    default_factory=list,
                    metadata={
                        "name": "weitererAntrag",
                        "type": "Element",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )

                @dataclass(kw_only=True)
                class AntragAbsehenAnhoerungSchuldner:
                    antrag_begruendung: str = field(
                        metadata={
                            "name": "antrag.begruendung",
                            "type": "Element",
                            "required": True,
                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                        }
                    )

            @dataclass(kw_only=True)
            class Versicherung:
                versicherung_753a_satz1_zpo: None | bool = field(
                    default=None,
                    metadata={
                        "name": "versicherung.753aSatz1ZPO",
                        "type": "Element",
                    },
                )
                versicherung_weitere: list[str] = field(
                    default_factory=list,
                    metadata={
                        "name": "versicherung.weitere",
                        "type": "Element",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )

        @dataclass(kw_only=True)
        class Beschlussdaten:
            weitere_glaeubiger_gemaess_anlage: None | bool = field(
                default=None,
                metadata={
                    "name": "weitereGlaeubigerGemaessAnlage",
                    "type": "Element",
                },
            )
            weitere_schuldner_gemaess_anlage: None | bool = field(
                default=None,
                metadata={
                    "name": "weitereSchuldnerGemaessAnlage",
                    "type": "Element",
                },
            )
            auswahl_beschluss: NachrichtZvstrDurchsuchungsanordnung2600001.Fachdaten.Beschlussdaten.AuswahlBeschluss = field(
                metadata={
                    "type": "Element",
                    "required": True,
                }
            )
            vollstreckungstitel: list[TypeZvstrVollstreckungstitel] = field(
                default_factory=list,
                metadata={
                    "type": "Element",
                },
            )
            weitere_vollstreckungstitel_gemaess_anlage: None | bool = field(
                default=None,
                metadata={
                    "name": "weitereVollstreckungstitelGemaessAnlage",
                    "type": "Element",
                },
            )
            forderung: NachrichtZvstrDurchsuchungsanordnung2600001.Fachdaten.Beschlussdaten.Forderung = field(
                metadata={
                    "type": "Element",
                    "required": True,
                }
            )
            auswahl_ermaechtigungen_gerichtsvollzieher: list[
                NachrichtZvstrDurchsuchungsanordnung2600001.Fachdaten.Beschlussdaten.AuswahlErmaechtigungenGerichtsvollzieher
            ] = field(
                default_factory=list,
                metadata={
                    "name": "auswahl_ermaechtigungen.gerichtsvollzieher",
                    "type": "Element",
                    "min_occurs": 1,
                },
            )
            vom_gericht_auszufuellen: (
                None
                | NachrichtZvstrDurchsuchungsanordnung2600001.Fachdaten.Beschlussdaten.VomGerichtAuszufuellen
            ) = field(
                default=None,
                metadata={
                    "name": "vomGerichtAuszufuellen",
                    "type": "Element",
                },
            )

            @dataclass(kw_only=True)
            class AuswahlBeschluss:
                """
                :ivar durchsuchungsbeschluss:
                :ivar
                    beschluss_anordnung_der_vollstreckung_zur_nachtzeit_sonn_und_feiertage:
                    Beschluss über die Anordnung der Vollstreckung zur
                    Nachtzeit und an Sonn- und Feiertagen
                :ivar
                    durchsuchungsbeschluss_beschluss_anordnung_der_vollstreckung_zur_nachtzeit_sonn_und_feiertage:
                """

                durchsuchungsbeschluss: None | bool = field(
                    default=None,
                    metadata={
                        "type": "Element",
                    },
                )
                beschluss_anordnung_der_vollstreckung_zur_nachtzeit_sonn_und_feiertage: (
                    None | bool
                ) = field(
                    default=None,
                    metadata={
                        "name": "beschluss.anordnungDerVollstreckungZurNachtzeitSonnUndFeiertage",
                        "type": "Element",
                    },
                )
                durchsuchungsbeschluss_beschluss_anordnung_der_vollstreckung_zur_nachtzeit_sonn_und_feiertage: (
                    None | bool
                ) = field(
                    default=None,
                    metadata={
                        "name": "durchsuchungsbeschluss.beschlussAnordnungDerVollstreckungZurNachtzeitSonnUndFeiertage",
                        "type": "Element",
                    },
                )

            @dataclass(kw_only=True)
            class Forderung:
                anteilsart_hauptforderungen: (
                    None
                    | NachrichtZvstrDurchsuchungsanordnung2600001.Fachdaten.Beschlussdaten.Forderung.AnteilsartHauptforderungen
                ) = field(
                    default=None,
                    metadata={
                        "name": "anteilsart.hauptforderungen",
                        "type": "Element",
                    },
                )
                anteilsart_teilforderungen: (
                    None
                    | NachrichtZvstrDurchsuchungsanordnung2600001.Fachdaten.Beschlussdaten.Forderung.AnteilsartTeilforderungen
                ) = field(
                    default=None,
                    metadata={
                        "name": "anteilsart.teilforderungen",
                        "type": "Element",
                    },
                )
                anteilsart_restforderungen: (
                    None
                    | NachrichtZvstrDurchsuchungsanordnung2600001.Fachdaten.Beschlussdaten.Forderung.AnteilsartRestforderungen
                ) = field(
                    default=None,
                    metadata={
                        "name": "anteilsart.restforderungen",
                        "type": "Element",
                    },
                )

                @dataclass(kw_only=True)
                class AnteilsartHauptforderungen:
                    hoehe_in_euro: Decimal = field(
                        metadata={
                            "name": "hoehe.inEuro",
                            "type": "Element",
                            "required": True,
                        }
                    )
                    hauptforderungen: str = field(
                        init=False,
                        default="Hauptforderungen",
                        metadata={
                            "type": "Element",
                            "required": True,
                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                        },
                    )

                @dataclass(kw_only=True)
                class AnteilsartTeilforderungen:
                    hoehe_in_euro: Decimal = field(
                        metadata={
                            "name": "hoehe.inEuro",
                            "type": "Element",
                            "required": True,
                        }
                    )
                    teilforderungen: str = field(
                        init=False,
                        default="Teilforderungen",
                        metadata={
                            "type": "Element",
                            "required": True,
                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                        },
                    )

                @dataclass(kw_only=True)
                class AnteilsartRestforderungen:
                    hoehe_in_euro: Decimal = field(
                        metadata={
                            "name": "hoehe.inEuro",
                            "type": "Element",
                            "required": True,
                        }
                    )
                    restforderungen: str = field(
                        init=False,
                        default="Restforderungen",
                        metadata={
                            "type": "Element",
                            "required": True,
                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                        },
                    )

            @dataclass(kw_only=True)
            class AuswahlErmaechtigungenGerichtsvollzieher:
                zu_durchsuchendes_objekt: (
                    None
                    | NachrichtZvstrDurchsuchungsanordnung2600001.Fachdaten.Beschlussdaten.AuswahlErmaechtigungenGerichtsvollzieher.ZuDurchsuchendesObjekt
                ) = field(
                    default=None,
                    metadata={
                        "name": "zuDurchsuchendesObjekt",
                        "type": "Element",
                    },
                )
                durchfuehrung_der_zwangsvollstreckungsmassnahme: (
                    None
                    | NachrichtZvstrDurchsuchungsanordnung2600001.Fachdaten.Beschlussdaten.AuswahlErmaechtigungenGerichtsvollzieher.DurchfuehrungDerZwangsvollstreckungsmassnahme
                ) = field(
                    default=None,
                    metadata={
                        "name": "durchfuehrungDerZwangsvollstreckungsmassnahme",
                        "type": "Element",
                    },
                )

                @dataclass(kw_only=True)
                class ZuDurchsuchendesObjekt:
                    """
                    :ivar ermaechtigung_gerichtsvollzieher: Der
                        zuständige Gerichtsvollzieher wird ermächtigt,
                        zum Zweck der Zwangsvollstreckung das Objekt zu
                        durchsuchen.
                    :ivar zu_durchsuchendes_objekt_oertlichkeit:
                    :ivar betroffene_person:
                    :ivar anordnung_durchfuehrung_gemaess758a_abs4_zpo:
                        Es wird gleichzeitig angeordnet, dass die
                        Durchsuchung des oben bezeichneten Objektes zur
                        Nachtzeit und an Sonn- und Feiertagen (§ 758a
                        Absatz 4 ZPO) durchgeführt werden kann.
                    """

                    ermaechtigung_gerichtsvollzieher: bool = field(
                        init=False,
                        default=True,
                        metadata={
                            "name": "ermaechtigung.gerichtsvollzieher",
                            "type": "Element",
                            "required": True,
                        },
                    )
                    zu_durchsuchendes_objekt_oertlichkeit: CodeGdsAnschriftstyp = field(
                        metadata={
                            "name": "zuDurchsuchendesObjekt.oertlichkeit",
                            "type": "Element",
                            "required": True,
                        }
                    )
                    betroffene_person: TypeGdsRefRollennummer = field(
                        metadata={
                            "name": "betroffenePerson",
                            "type": "Element",
                            "required": True,
                        }
                    )
                    anordnung_durchfuehrung_gemaess758a_abs4_zpo: (
                        None | bool
                    ) = field(
                        default=None,
                        metadata={
                            "name": "anordnung.durchfuehrungGemaess758aAbs4ZPO",
                            "type": "Element",
                        },
                    )

                @dataclass(kw_only=True)
                class DurchfuehrungDerZwangsvollstreckungsmassnahme:
                    """
                    :ivar ermaechtigung_gerichtsvollzieher: Der
                        zuständige Gerichtsvollzieher wird ermächtigt,
                        die bezeichnete Zwangsvollstreckungsmaßnahme zur
                        Nachtzeit und an Sonn- und Feiertagen
                        durchzuführen (§ 758a Absatz 4 ZPO).
                    :ivar zwangsvollstreckungsmassnahme:
                    :ivar
                        durchfuehrung_der_zwangsvollstreckungsmassnahme_oertlichkeit:
                    :ivar betroffene_person:
                    """

                    ermaechtigung_gerichtsvollzieher: bool = field(
                        init=False,
                        default=True,
                        metadata={
                            "name": "ermaechtigung.gerichtsvollzieher",
                            "type": "Element",
                            "required": True,
                        },
                    )
                    zwangsvollstreckungsmassnahme: str = field(
                        metadata={
                            "type": "Element",
                            "required": True,
                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                        }
                    )
                    durchfuehrung_der_zwangsvollstreckungsmassnahme_oertlichkeit: CodeGdsAnschriftstyp = field(
                        metadata={
                            "name": "durchfuehrungDerZwangsvollstreckungsmassnahme.oertlichkeit",
                            "type": "Element",
                            "required": True,
                        }
                    )
                    betroffene_person: TypeGdsRefRollennummer = field(
                        metadata={
                            "name": "betroffenePerson",
                            "type": "Element",
                            "required": True,
                        }
                    )

            @dataclass(kw_only=True)
            class VomGerichtAuszufuellen:
                """
                :ivar anordnung_ermaechtigung_dauer:
                :ivar
                    befugnis_oeffnungen_und_beschlagnahme_pfandstuecke:
                    Im Rahmen der angeordneten Durchsuchung umfasst sie
                    die Befugnis, verschlossene Haustüren, Zimmertüren
                    und Behältnisse öffnen zu lassen und Pfandstücke zum
                    Zweck ihrer Verwertung an sich zu nehmen (Artikel 13
                    Absatz 2 GG, § 758a Absatz 1 ZPO). Die Ermächtigung
                    gilt zugleich für das Abholen der Pfandstücke.
                :ivar auswahl_weitere_anordnungen:
                :ivar gruende:
                :ivar sonstige_gruende_oder_weitere_anordnungen: Hier
                    können sonstige Gründe oder auch weitere Anordnungen
                    angegeben werden.
                """

                anordnung_ermaechtigung_dauer: (
                    None
                    | NachrichtZvstrDurchsuchungsanordnung2600001.Fachdaten.Beschlussdaten.VomGerichtAuszufuellen.AnordnungErmaechtigungDauer
                ) = field(
                    default=None,
                    metadata={
                        "name": "anordnung.ermaechtigung.dauer",
                        "type": "Element",
                    },
                )
                befugnis_oeffnungen_und_beschlagnahme_pfandstuecke: (
                    None | bool
                ) = field(
                    default=None,
                    metadata={
                        "name": "befugnis.oeffnungenUndBeschlagnahmePfandstuecke",
                        "type": "Element",
                    },
                )
                auswahl_weitere_anordnungen: (
                    None
                    | NachrichtZvstrDurchsuchungsanordnung2600001.Fachdaten.Beschlussdaten.VomGerichtAuszufuellen.AuswahlWeitereAnordnungen
                ) = field(
                    default=None,
                    metadata={
                        "name": "auswahl_weitereAnordnungen",
                        "type": "Element",
                    },
                )
                gruende: NachrichtZvstrDurchsuchungsanordnung2600001.Fachdaten.Beschlussdaten.VomGerichtAuszufuellen.Gruende = field(
                    metadata={
                        "type": "Element",
                        "required": True,
                    }
                )
                sonstige_gruende_oder_weitere_anordnungen: list[str] = field(
                    default_factory=list,
                    metadata={
                        "name": "sonstigeGruendeOderWeitereAnordnungen",
                        "type": "Element",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )

                @dataclass(kw_only=True)
                class AnordnungErmaechtigungDauer:
                    bezeichnung_der_ermaechtigung: str = field(
                        metadata={
                            "name": "bezeichnungDerErmaechtigung",
                            "type": "Element",
                            "required": True,
                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                        }
                    )
                    dauer_ermaechtigung_in_monaten: int = field(
                        metadata={
                            "name": "dauer.ermaechtigungInMonaten",
                            "type": "Element",
                            "required": True,
                        }
                    )

                @dataclass(kw_only=True)
                class AuswahlWeitereAnordnungen:
                    zeitliche_beschraenkung: (
                        None
                        | NachrichtZvstrDurchsuchungsanordnung2600001.Fachdaten.Beschlussdaten.VomGerichtAuszufuellen.AuswahlWeitereAnordnungen.ZeitlicheBeschraenkung
                    ) = field(
                        default=None,
                        metadata={
                            "name": "zeitlicheBeschraenkung",
                            "type": "Element",
                        },
                    )
                    keine_zeitliche_beschraenkung: None | bool = field(
                        default=None,
                        metadata={
                            "name": "keineZeitlicheBeschraenkung",
                            "type": "Element",
                        },
                    )

                    @dataclass(kw_only=True)
                    class ZeitlicheBeschraenkung:
                        uhrzeit_von: XmlTime = field(
                            metadata={
                                "name": "uhrzeit.von",
                                "type": "Element",
                                "required": True,
                            }
                        )
                        uhrzeit_bis: XmlTime = field(
                            metadata={
                                "name": "uhrzeit.bis",
                                "type": "Element",
                                "required": True,
                            }
                        )

                @dataclass(kw_only=True)
                class Gruende:
                    """
                    :ivar schuldner_wiederholt_nicht_angetroffen:
                    :ivar verweigerung_durchsuchung:
                    :ivar verzicht_anhoerung_schuldner: Auf eine
                        Anhörung der Schuldner vor Erlass des
                        Beschlusses wurde im Hinblick auf den bisherigen
                        Verfahrensgang verzichtet, um den
                        Vollstreckungserfolg nicht zu gefährden.
                    """

                    schuldner_wiederholt_nicht_angetroffen: None | bool = (
                        field(
                            default=None,
                            metadata={
                                "name": "schuldnerWiederholtNichtAngetroffen",
                                "type": "Element",
                            },
                        )
                    )
                    verweigerung_durchsuchung: None | bool = field(
                        default=None,
                        metadata={
                            "name": "verweigerungDurchsuchung",
                            "type": "Element",
                        },
                    )
                    verzicht_anhoerung_schuldner: None | bool = field(
                        default=None,
                        metadata={
                            "name": "verzicht.anhoerungSchuldner",
                            "type": "Element",
                        },
                    )


@dataclass(kw_only=True)
class TypeZvstrForderungsaufstellungGewoehnlicheForderung:
    """
    :ivar lfd_nr_forderungsaufstellung:
    :ivar ref_vollstreckungstitel:
    :ivar i_hauptforderung_zinsen_saeumniszuschlaege:
    :ivar ii_renten:
    :ivar iii_titulierte_kosten_nebenforderungen:
    :ivar iv_kosten_zwangsvollstreckung:
    :ivar summe_i_iv: Hier ist die Summe der Punkte I. bis IV.
        anzugeben. Zinsen und Säumniszuschläge nur, soweit nicht
        laufend.
    """

    class Meta:
        name = "Type.ZVSTR.Forderungsaufstellung.GewoehnlicheForderung"

    lfd_nr_forderungsaufstellung: int = field(
        metadata={
            "name": "lfdNr.forderungsaufstellung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    ref_vollstreckungstitel: TypeZvstrRefTitelnummer = field(
        metadata={
            "name": "ref.vollstreckungstitel",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    i_hauptforderung_zinsen_saeumniszuschlaege: list[
        TypeZvstrForderungshoehe
    ] = field(
        default_factory=list,
        metadata={
            "name": "i.hauptforderung.zinsenSaeumniszuschlaege",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    ii_renten: list[TypeZvstrRenten] = field(
        default_factory=list,
        metadata={
            "name": "ii.renten",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    iii_titulierte_kosten_nebenforderungen: (
        None
        | TypeZvstrForderungsaufstellungGewoehnlicheForderung.IiiTitulierteKostenNebenforderungen
    ) = field(
        default=None,
        metadata={
            "name": "iii.titulierteKostenNebenforderungen",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    iv_kosten_zwangsvollstreckung: (
        None
        | TypeZvstrForderungsaufstellungGewoehnlicheForderung.IvKostenZwangsvollstreckung
    ) = field(
        default=None,
        metadata={
            "name": "iv.kostenZwangsvollstreckung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    summe_i_iv: Decimal = field(
        metadata={
            "name": "summe.i-iv",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class IiiTitulierteKostenNebenforderungen:
        auswahl_art_der_kostenforderung: list[
            TypeZvstrForderungsaufstellungGewoehnlicheForderung.IiiTitulierteKostenNebenforderungen.AuswahlArtDerKostenforderung
        ] = field(
            default_factory=list,
            metadata={
                "name": "auswahl_artDerKostenforderung",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        freie_eingabe: list[TypeZvstrFreieEingabe] = field(
            default_factory=list,
            metadata={
                "name": "freieEingabe",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )

        @dataclass(kw_only=True)
        class AuswahlArtDerKostenforderung:
            kosten_des_mahnverfahrens_vollstreckungsbescheid: (
                None | TypeZvstrKostenforderung
            ) = field(
                default=None,
                metadata={
                    "name": "kostenDesMahnverfahrens.vollstreckungsbescheid",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            titulierte_vorgerichtliche_kosten: (
                None | TypeZvstrKostenforderung
            ) = field(
                default=None,
                metadata={
                    "name": "titulierteVorgerichtlicheKosten",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            festgesetzte_kosten: None | TypeZvstrKostenforderung = field(
                default=None,
                metadata={
                    "name": "festgesetzteKosten",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )

    @dataclass(kw_only=True)
    class IvKostenZwangsvollstreckung:
        """
        :ivar bisherige_vollstreckungskosten_anlage: Hier können die
            bisherigen Vollstreckungskosten gemäß Aufstellung in
            weiterer Anlage eingetragen werden.
        :ivar kosten_des_verfahrens:
        :ivar sonstige_kosten:
        """

        bisherige_vollstreckungskosten_anlage: None | Decimal = field(
            default=None,
            metadata={
                "name": "bisherigeVollstreckungskosten.anlage",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        kosten_des_verfahrens: list[
            TypeZvstrForderungsaufstellungGewoehnlicheForderung.IvKostenZwangsvollstreckung.KostenDesVerfahrens
        ] = field(
            default_factory=list,
            metadata={
                "name": "kostenDesVerfahrens",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        sonstige_kosten: list[
            TypeZvstrForderungsaufstellungGewoehnlicheForderung.IvKostenZwangsvollstreckung.SonstigeKosten
        ] = field(
            default_factory=list,
            metadata={
                "name": "sonstigeKosten",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )

        @dataclass(kw_only=True)
        class KostenDesVerfahrens:
            """
            :ivar gerichtskosten: Gerichtskosten nach GKG (Gebühr nach
                KV Nr. 2111)
            :ivar anwaltskosten_gemaess_rvg:
            :ivar inkassokosten_anlage: Kosten von Inkassodienstleistern
                nach § 13e RDG gemäß Aufstellung in weiterer Anlage
            """

            gerichtskosten: None | Decimal = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            anwaltskosten_gemaess_rvg: (
                None
                | TypeZvstrForderungsaufstellungGewoehnlicheForderung.IvKostenZwangsvollstreckung.KostenDesVerfahrens.AnwaltskostenGemaessRvg
            ) = field(
                default=None,
                metadata={
                    "name": "anwaltskosten.gemaessRVG",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            inkassokosten_anlage: None | Decimal = field(
                default=None,
                metadata={
                    "name": "inkassokosten.anlage",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )

            @dataclass(kw_only=True)
            class AnwaltskostenGemaessRvg:
                """
                :ivar anwaltskosten_gegenstandswert: Gegenstandswert
                    gemäß § 25 RVG
                :ivar verfahrensgebuehr: Verfahrensgebühr (VV Nr. 3309,
                    ggf. i. V. m. VV Nr. 1008)
                :ivar auslagenpauschale: Entgelte für Post- und
                    Telekommunikationsdienstleistungen, ggf. Pauschale
                    (VV Nr. 7001 oder 7002)
                :ivar weitere_auslagen:
                :ivar umsatzsteuer:
                :ivar zwischensumme_rechtsanwaltskosten_in_euro:
                """

                anwaltskosten_gegenstandswert: Decimal = field(
                    metadata={
                        "name": "anwaltskosten.gegenstandswert",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "required": True,
                    }
                )
                verfahrensgebuehr: Decimal = field(
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "required": True,
                    }
                )
                auslagenpauschale: None | Decimal = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                    },
                )
                weitere_auslagen: list[
                    TypeZvstrForderungsaufstellungGewoehnlicheForderung.IvKostenZwangsvollstreckung.KostenDesVerfahrens.AnwaltskostenGemaessRvg.WeitereAuslagen
                ] = field(
                    default_factory=list,
                    metadata={
                        "name": "weitereAuslagen",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                    },
                )
                umsatzsteuer: None | Decimal = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                    },
                )
                zwischensumme_rechtsanwaltskosten_in_euro: Decimal = field(
                    metadata={
                        "name": "zwischensummeRechtsanwaltskostenInEuro",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "required": True,
                    }
                )

                @dataclass(kw_only=True)
                class WeitereAuslagen:
                    bezeichnung: str = field(
                        metadata={
                            "type": "Element",
                            "namespace": "http://www.xjustiz.de",
                            "required": True,
                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                        }
                    )
                    betrag: Decimal = field(
                        metadata={
                            "type": "Element",
                            "namespace": "http://www.xjustiz.de",
                            "required": True,
                        }
                    )

        @dataclass(kw_only=True)
        class SonstigeKosten:
            bezeichnung: str = field(
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                }
            )
            betrag_in_euro: Decimal = field(
                metadata={
                    "name": "betragInEuro",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )


@dataclass(kw_only=True)
class TypeZvstrForderungsaufstellungUnterhaltsforderung:
    """
    :ivar lfd_nr_forderungsaufstellung:
    :ivar unterhaltsberechtigter:
    :ivar ref_schuldner:
    :ivar ref_vollstreckungstitel:
    :ivar i_rueckstand_unterhalt:
    :ivar ii_titulierte_kosten_nebenforderungen:
    :ivar iii_kosten_zwangsvollstreckung:
    :ivar iv_statische_unterhaltsrente:
    :ivar v_dynamisierte_unterhaltsrente:
    :ivar summe_i_v: Hier ist die Summe der Punkte I. bis V. anzugeben.
        Zinsen, Säumniszuschläge und Unterhaltsrenten nur, soweit nicht
        laufend.
    """

    class Meta:
        name = "Type.ZVSTR.Forderungsaufstellung.Unterhaltsforderung"

    lfd_nr_forderungsaufstellung: int = field(
        metadata={
            "name": "lfdNr.forderungsaufstellung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    unterhaltsberechtigter: TypeGdsRefRollennummer = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    ref_schuldner: TypeGdsRefRollennummer = field(
        metadata={
            "name": "ref.schuldner",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    ref_vollstreckungstitel: TypeZvstrRefTitelnummer = field(
        metadata={
            "name": "ref.vollstreckungstitel",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    i_rueckstand_unterhalt: list[
        TypeZvstrForderungsaufstellungUnterhaltsforderung.IRueckstandUnterhalt
    ] = field(
        default_factory=list,
        metadata={
            "name": "i.rueckstand.unterhalt",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    ii_titulierte_kosten_nebenforderungen: (
        None
        | TypeZvstrForderungsaufstellungUnterhaltsforderung.IiTitulierteKostenNebenforderungen
    ) = field(
        default=None,
        metadata={
            "name": "ii.titulierteKostenNebenforderungen",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    iii_kosten_zwangsvollstreckung: (
        None
        | TypeZvstrForderungsaufstellungUnterhaltsforderung.IiiKostenZwangsvollstreckung
    ) = field(
        default=None,
        metadata={
            "name": "iii.kostenZwangsvollstreckung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    iv_statische_unterhaltsrente: (
        None
        | TypeZvstrForderungsaufstellungUnterhaltsforderung.IvStatischeUnterhaltsrente
    ) = field(
        default=None,
        metadata={
            "name": "iv.statischeUnterhaltsrente",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    v_dynamisierte_unterhaltsrente: (
        None
        | TypeZvstrForderungsaufstellungUnterhaltsforderung.VDynamisierteUnterhaltsrente
    ) = field(
        default=None,
        metadata={
            "name": "v.dynamisierteUnterhaltsrente",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    summe_i_v: Decimal = field(
        metadata={
            "name": "summe.i-v",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class IRueckstandUnterhalt:
        unterhaltsrueckstand: (
            None
            | TypeZvstrForderungsaufstellungUnterhaltsforderung.IRueckstandUnterhalt.Unterhaltsrueckstand
        ) = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        forderung: (
            None
            | TypeZvstrForderungsaufstellungUnterhaltsforderung.IRueckstandUnterhalt.Forderung
        ) = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        freie_eingabe: list[TypeZvstrFreieEingabe] = field(
            default_factory=list,
            metadata={
                "name": "freieEingabe",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )

        @dataclass(kw_only=True)
        class Unterhaltsrueckstand:
            """
            :ivar hoehe_konkreter_unterhaltsrueckstand:
            :ivar zinsen_vollstreckungstitel: Hier können die
                (Teil-/Rest-) Zinsen wie im Vollstreckungstitel
                ausgerechnet eingetragen werden.
            :ivar zinsen_unterhaltsrueckstand:
            """

            hoehe_konkreter_unterhaltsrueckstand: (
                None
                | TypeZvstrForderungsaufstellungUnterhaltsforderung.IRueckstandUnterhalt.Unterhaltsrueckstand.HoeheKonkreterUnterhaltsrueckstand
            ) = field(
                default=None,
                metadata={
                    "name": "hoehe.konkreterUnterhaltsrueckstand",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            zinsen_vollstreckungstitel: None | Decimal = field(
                default=None,
                metadata={
                    "name": "zinsen.vollstreckungstitel",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            zinsen_unterhaltsrueckstand: list[TypeZvstrZinsen] = field(
                default_factory=list,
                metadata={
                    "name": "zinsen.unterhaltsrueckstand",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )

            @dataclass(kw_only=True)
            class HoeheKonkreterUnterhaltsrueckstand:
                beginn_zeitraum: XmlDate = field(
                    metadata={
                        "name": "beginn.zeitraum",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "required": True,
                    }
                )
                ende_zeitraum: XmlDate = field(
                    metadata={
                        "name": "ende.zeitraum",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "required": True,
                    }
                )
                betrag_in_euro: Decimal = field(
                    metadata={
                        "name": "betrag.inEuro",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "required": True,
                    }
                )

        @dataclass(kw_only=True)
        class Forderung:
            auswahl_forderung: None | TypeZvstrHauptforderung = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            saeumniszuschlag: TypeZvstrSaeumniszuschlag = field(
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )

    @dataclass(kw_only=True)
    class IiTitulierteKostenNebenforderungen:
        auswahl_art_der_kostenforderung: list[
            TypeZvstrForderungsaufstellungUnterhaltsforderung.IiTitulierteKostenNebenforderungen.AuswahlArtDerKostenforderung
        ] = field(
            default_factory=list,
            metadata={
                "name": "auswahl_artDerKostenforderung",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        freie_eingabe: list[TypeZvstrFreieEingabe] = field(
            default_factory=list,
            metadata={
                "name": "freieEingabe",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )

        @dataclass(kw_only=True)
        class AuswahlArtDerKostenforderung:
            kosten_des_mahnverfahrens_vollstreckungsbescheid: (
                None | TypeZvstrKostenforderung
            ) = field(
                default=None,
                metadata={
                    "name": "kostenDesMahnverfahrens.vollstreckungsbescheid",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            titulierte_vorgerichtliche_kosten: (
                None | TypeZvstrKostenforderung
            ) = field(
                default=None,
                metadata={
                    "name": "titulierteVorgerichtlicheKosten",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            festgesetzte_kosten: None | TypeZvstrKostenforderung = field(
                default=None,
                metadata={
                    "name": "festgesetzteKosten",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )

    @dataclass(kw_only=True)
    class IiiKostenZwangsvollstreckung:
        """
        :ivar bisherige_vollstreckungskosten_anlage: Hier können die
            bisherigen Vollstreckungskosten gemäß Aufstellung in
            weiterer Anlage eingetragen werden.
        :ivar kosten_des_verfahrens:
        :ivar sonstige_kosten:
        """

        bisherige_vollstreckungskosten_anlage: None | Decimal = field(
            default=None,
            metadata={
                "name": "bisherigeVollstreckungskosten.anlage",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        kosten_des_verfahrens: list[
            TypeZvstrForderungsaufstellungUnterhaltsforderung.IiiKostenZwangsvollstreckung.KostenDesVerfahrens
        ] = field(
            default_factory=list,
            metadata={
                "name": "kostenDesVerfahrens",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        sonstige_kosten: list[
            TypeZvstrForderungsaufstellungUnterhaltsforderung.IiiKostenZwangsvollstreckung.SonstigeKosten
        ] = field(
            default_factory=list,
            metadata={
                "name": "sonstigeKosten",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )

        @dataclass(kw_only=True)
        class KostenDesVerfahrens:
            """
            :ivar gerichtskosten: Gerichtskosten nach GKG (Gebühr nach
                KV Nr. 2111)
            :ivar anwaltskosten_gemaess_rvg:
            :ivar inkassokosten_anlage: Kosten von Inkassodienstleistern
                nach § 13e RDG gemäß Aufstellung in weiterer Anlage
            """

            gerichtskosten: None | Decimal = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            anwaltskosten_gemaess_rvg: (
                None
                | TypeZvstrForderungsaufstellungUnterhaltsforderung.IiiKostenZwangsvollstreckung.KostenDesVerfahrens.AnwaltskostenGemaessRvg
            ) = field(
                default=None,
                metadata={
                    "name": "anwaltskosten.gemaessRVG",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            inkassokosten_anlage: None | Decimal = field(
                default=None,
                metadata={
                    "name": "inkassokosten.anlage",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )

            @dataclass(kw_only=True)
            class AnwaltskostenGemaessRvg:
                """
                :ivar anwaltskosten_gegenstandswert: Gegenstandswert
                    gemäß § 25 RVG
                :ivar verfahrensgebuehr: Verfahrensgebühr (VV Nr. 3309,
                    ggf. i. V. m. VV Nr. 1008)
                :ivar auslagenpauschale: Entgelte für Post- und
                    Telekommunikationsdienstleistungen, ggf. Pauschale
                    (VV Nr. 7001 oder 7002)
                :ivar weitere_auslagen:
                :ivar umsatzsteuer:
                :ivar zwischensumme_rechtsanwaltskosten_in_euro:
                """

                anwaltskosten_gegenstandswert: Decimal = field(
                    metadata={
                        "name": "anwaltskosten.gegenstandswert",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "required": True,
                    }
                )
                verfahrensgebuehr: Decimal = field(
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "required": True,
                    }
                )
                auslagenpauschale: None | Decimal = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                    },
                )
                weitere_auslagen: list[
                    TypeZvstrForderungsaufstellungUnterhaltsforderung.IiiKostenZwangsvollstreckung.KostenDesVerfahrens.AnwaltskostenGemaessRvg.WeitereAuslagen
                ] = field(
                    default_factory=list,
                    metadata={
                        "name": "weitereAuslagen",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                    },
                )
                umsatzsteuer: None | Decimal = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                    },
                )
                zwischensumme_rechtsanwaltskosten_in_euro: Decimal = field(
                    metadata={
                        "name": "zwischensummeRechtsanwaltskostenInEuro",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "required": True,
                    }
                )

                @dataclass(kw_only=True)
                class WeitereAuslagen:
                    bezeichnung: str = field(
                        metadata={
                            "type": "Element",
                            "namespace": "http://www.xjustiz.de",
                            "required": True,
                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                        }
                    )
                    betrag: Decimal = field(
                        metadata={
                            "type": "Element",
                            "namespace": "http://www.xjustiz.de",
                            "required": True,
                        }
                    )

        @dataclass(kw_only=True)
        class SonstigeKosten:
            bezeichnung: str = field(
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                }
            )
            betrag_in_euro: Decimal = field(
                metadata={
                    "name": "betragInEuro",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )

    @dataclass(kw_only=True)
    class IvStatischeUnterhaltsrente:
        unterhaltsberechtigter: CodeZvstrUnterhaltsberechtigter = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        zahlungsintervall: CodeGdsIntervall = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        beginn_zahlungszeitraum: XmlDate = field(
            metadata={
                "name": "beginn.zahlungszeitraum",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        zahlbar_am: str = field(
            metadata={
                "name": "zahlbarAm",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            }
        )
        ende_zahlungszeitraum: None | XmlDate = field(
            default=None,
            metadata={
                "name": "ende.zahlungszeitraum",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        bezifferung_statischer_unterhalt: list[
            TypeZvstrForderungsaufstellungUnterhaltsforderung.IvStatischeUnterhaltsrente.BezifferungStatischerUnterhalt
        ] = field(
            default_factory=list,
            metadata={
                "name": "bezifferung.statischerUnterhalt",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "min_occurs": 1,
            },
        )

        @dataclass(kw_only=True)
        class BezifferungStatischerUnterhalt:
            betrag_in_euro: None | Decimal = field(
                default=None,
                metadata={
                    "name": "betrag.inEuro",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            zeitraum_unterhaltsforderung: TypeZvstrForderungsaufstellungUnterhaltsforderung.IvStatischeUnterhaltsrente.BezifferungStatischerUnterhalt.ZeitraumUnterhaltsforderung = field(
                metadata={
                    "name": "zeitraum.unterhaltsforderung",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )

            @dataclass(kw_only=True)
            class ZeitraumUnterhaltsforderung:
                zeitraum_definiert: CodeZvstrZeitraumUnterhaltsforderung = (
                    field(
                        metadata={
                            "name": "zeitraum.definiert",
                            "type": "Element",
                            "namespace": "http://www.xjustiz.de",
                            "required": True,
                        }
                    )
                )
                sonstiger_zeitraum: (
                    None
                    | TypeZvstrForderungsaufstellungUnterhaltsforderung.IvStatischeUnterhaltsrente.BezifferungStatischerUnterhalt.ZeitraumUnterhaltsforderung.SonstigerZeitraum
                ) = field(
                    default=None,
                    metadata={
                        "name": "sonstigerZeitraum",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                    },
                )

                @dataclass(kw_only=True)
                class SonstigerZeitraum:
                    beginn_zeitraum: XmlDate = field(
                        metadata={
                            "name": "beginn.zeitraum",
                            "type": "Element",
                            "namespace": "http://www.xjustiz.de",
                            "required": True,
                        }
                    )
                    ende_zeitraum: None | XmlDate = field(
                        default=None,
                        metadata={
                            "name": "ende.zeitraum",
                            "type": "Element",
                            "namespace": "http://www.xjustiz.de",
                        },
                    )

    @dataclass(kw_only=True)
    class VDynamisierteUnterhaltsrente:
        zeitraum: TypeGdsXdomeaZeitraumType = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        abschnitt_unterhalt_nach_altersstufe: list[
            TypeZvstrForderungsaufstellungUnterhaltsforderung.VDynamisierteUnterhaltsrente.AbschnittUnterhaltNachAltersstufe
        ] = field(
            default_factory=list,
            metadata={
                "name": "abschnitt.unterhaltNachAltersstufe",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "min_occurs": 1,
                "max_occurs": 3,
            },
        )

        @dataclass(kw_only=True)
        class AbschnittUnterhaltNachAltersstufe:
            altersstufe: CodeZvstrAltersstufenUnterhalt = field(
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            prozentsatz_mindestunterhalt: Decimal = field(
                metadata={
                    "name": "prozentsatz.mindestunterhalt",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            abzug_kindergeld_anteilig: (
                None
                | TypeZvstrForderungsaufstellungUnterhaltsforderung.VDynamisierteUnterhaltsrente.AbschnittUnterhaltNachAltersstufe.AbzugKindergeldAnteilig
            ) = field(
                default=None,
                metadata={
                    "name": "abzug.kindergeld.anteilig",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            abzug_betrag_kindergeld_in_euro: None | Decimal = field(
                default=None,
                metadata={
                    "name": "abzug.betrag.kindergeld.inEuro",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            abzug_sonstige_kindbezogene_leistung: (
                None
                | TypeZvstrForderungsaufstellungUnterhaltsforderung.VDynamisierteUnterhaltsrente.AbschnittUnterhaltNachAltersstufe.AbzugSonstigeKindbezogeneLeistung
            ) = field(
                default=None,
                metadata={
                    "name": "abzug.sonstigeKindbezogeneLeistung",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )

            @dataclass(kw_only=True)
            class AbzugKindergeldAnteilig:
                auswahl_anteil_kindergeld: TypeZvstrForderungsaufstellungUnterhaltsforderung.VDynamisierteUnterhaltsrente.AbschnittUnterhaltNachAltersstufe.AbzugKindergeldAnteilig.AuswahlAnteilKindergeld = field(
                    metadata={
                        "name": "auswahl_anteil.kindergeld",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "required": True,
                    }
                )

                @dataclass(kw_only=True)
                class AuswahlAnteilKindergeld:
                    haelftig: None | str = field(
                        default=None,
                        metadata={
                            "type": "Element",
                            "namespace": "http://www.xjustiz.de",
                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                        },
                    )
                    voll: None | str = field(
                        default=None,
                        metadata={
                            "type": "Element",
                            "namespace": "http://www.xjustiz.de",
                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                        },
                    )

            @dataclass(kw_only=True)
            class AbzugSonstigeKindbezogeneLeistung:
                """
                :ivar betrag_sonstige_leistung_in_euro:
                :ivar derzeitiger_zahlbetrag_in_euro: Hier kann der
                    derzeitige monatliche Zahlbetrag des Unterhalts
                    eingetragen werden.
                :ivar zeitraum:
                """

                betrag_sonstige_leistung_in_euro: Decimal = field(
                    metadata={
                        "name": "betrag.sonstigeLeistung.inEuro",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "required": True,
                    }
                )
                derzeitiger_zahlbetrag_in_euro: None | Decimal = field(
                    default=None,
                    metadata={
                        "name": "derzeitigerZahlbetrag.inEuro",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                    },
                )
                zeitraum: None | TypeGdsXdomeaZeitraumType = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                    },
                )


@dataclass(kw_only=True)
class TypeZvstrForderungsaufstellungVollstreckungsauftrag:
    """
    :ivar lfd_nr_forderungsaufstellung:
    :ivar ref_vollstreckungstitel:
    :ivar i_hauptforderung_zinsen_saeumniszuschlaege:
    :ivar ii_rueckstand_unterhalt_oder_rente:
    :ivar iii_titulierte_kosten_nebenforderungen:
    :ivar iv_kosten_zwangsvollstreckung:
    :ivar summe_i_iv: Hier ist die Summe der Punkte I. bis IV.
        anzugeben. Zinsen und Säumniszuschläge nur, soweit nicht
        laufend.
    """

    class Meta:
        name = "Type.ZVSTR.Forderungsaufstellung.Vollstreckungsauftrag"

    lfd_nr_forderungsaufstellung: int = field(
        metadata={
            "name": "lfdNr.forderungsaufstellung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    ref_vollstreckungstitel: TypeZvstrRefTitelnummer = field(
        metadata={
            "name": "ref.vollstreckungstitel",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )
    i_hauptforderung_zinsen_saeumniszuschlaege: list[
        TypeZvstrForderungshoehe
    ] = field(
        default_factory=list,
        metadata={
            "name": "i.hauptforderung.zinsenSaeumniszuschlaege",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    ii_rueckstand_unterhalt_oder_rente: list[
        TypeZvstrForderungsaufstellungVollstreckungsauftrag.IiRueckstandUnterhaltOderRente
    ] = field(
        default_factory=list,
        metadata={
            "name": "ii.rueckstand.unterhaltOderRente",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    iii_titulierte_kosten_nebenforderungen: (
        None
        | TypeZvstrForderungsaufstellungVollstreckungsauftrag.IiiTitulierteKostenNebenforderungen
    ) = field(
        default=None,
        metadata={
            "name": "iii.titulierteKostenNebenforderungen",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    iv_kosten_zwangsvollstreckung: (
        None
        | TypeZvstrForderungsaufstellungVollstreckungsauftrag.IvKostenZwangsvollstreckung
    ) = field(
        default=None,
        metadata={
            "name": "iv.kostenZwangsvollstreckung",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    summe_i_iv: Decimal = field(
        metadata={
            "name": "summe.i-iv",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class IiRueckstandUnterhaltOderRente:
        berechtigter: TypeGdsRefRollennummer = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        rueckstand: TypeZvstrForderungsaufstellungVollstreckungsauftrag.IiRueckstandUnterhaltOderRente.Rueckstand = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )

        @dataclass(kw_only=True)
        class Rueckstand:
            """
            :ivar rueckstand_hoehe_und_zeitraum:
            :ivar zinsen_vollstreckungstitel: Hier können die
                (Teil-/Rest-) Zinsen wie im Vollstreckungstitel
                ausgerechnet eingetragen werden.
            :ivar zinsen:
            """

            rueckstand_hoehe_und_zeitraum: TypeZvstrForderungsaufstellungVollstreckungsauftrag.IiRueckstandUnterhaltOderRente.Rueckstand.RueckstandHoeheUndZeitraum = field(
                metadata={
                    "name": "rueckstand.hoeheUndZeitraum",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )
            zinsen_vollstreckungstitel: None | Decimal = field(
                default=None,
                metadata={
                    "name": "zinsen.vollstreckungstitel",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            zinsen: list[TypeZvstrZinsen] = field(
                default_factory=list,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )

            @dataclass(kw_only=True)
            class RueckstandHoeheUndZeitraum:
                beginn_zeitraum: XmlDate = field(
                    metadata={
                        "name": "beginn.zeitraum",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "required": True,
                    }
                )
                ende_zeitraum: XmlDate = field(
                    metadata={
                        "name": "ende.zeitraum",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "required": True,
                    }
                )
                betrag_in_euro: Decimal = field(
                    metadata={
                        "name": "betrag.inEuro",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "required": True,
                    }
                )

    @dataclass(kw_only=True)
    class IiiTitulierteKostenNebenforderungen:
        auswahl_art_der_kostenforderung: list[
            TypeZvstrForderungsaufstellungVollstreckungsauftrag.IiiTitulierteKostenNebenforderungen.AuswahlArtDerKostenforderung
        ] = field(
            default_factory=list,
            metadata={
                "name": "auswahl_artDerKostenforderung",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        freie_eingabe: list[TypeZvstrFreieEingabe] = field(
            default_factory=list,
            metadata={
                "name": "freieEingabe",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )

        @dataclass(kw_only=True)
        class AuswahlArtDerKostenforderung:
            kosten_des_mahnverfahrens_vollstreckungsbescheid: (
                None | TypeZvstrKostenforderung
            ) = field(
                default=None,
                metadata={
                    "name": "kostenDesMahnverfahrens.vollstreckungsbescheid",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            titulierte_vorgerichtliche_kosten: (
                None | TypeZvstrKostenforderung
            ) = field(
                default=None,
                metadata={
                    "name": "titulierteVorgerichtlicheKosten",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            festgesetzte_kosten: None | TypeZvstrKostenforderung = field(
                default=None,
                metadata={
                    "name": "festgesetzteKosten",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )

    @dataclass(kw_only=True)
    class IvKostenZwangsvollstreckung:
        """
        :ivar bisherige_vollstreckungskosten_anlage: Hier können die
            bisherigen Vollstreckungskosten gemäß Aufstellung in
            weiterer Anlage eingetragen werden.
        :ivar kosten_des_verfahrens:
        :ivar sonstige_kosten:
        """

        bisherige_vollstreckungskosten_anlage: None | Decimal = field(
            default=None,
            metadata={
                "name": "bisherigeVollstreckungskosten.anlage",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        kosten_des_verfahrens: list[
            TypeZvstrForderungsaufstellungVollstreckungsauftrag.IvKostenZwangsvollstreckung.KostenDesVerfahrens
        ] = field(
            default_factory=list,
            metadata={
                "name": "kostenDesVerfahrens",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )
        sonstige_kosten: list[
            TypeZvstrForderungsaufstellungVollstreckungsauftrag.IvKostenZwangsvollstreckung.SonstigeKosten
        ] = field(
            default_factory=list,
            metadata={
                "name": "sonstigeKosten",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
            },
        )

        @dataclass(kw_only=True)
        class KostenDesVerfahrens:
            """
            :ivar anwaltskosten_gemaess_rvg:
            :ivar inkassokosten_anlage: Kosten von Inkassodienstleistern
                nach § 13e RDG gemäß Aufstellung in weiterer Anlage
            """

            anwaltskosten_gemaess_rvg: list[
                TypeZvstrForderungsaufstellungVollstreckungsauftrag.IvKostenZwangsvollstreckung.KostenDesVerfahrens.AnwaltskostenGemaessRvg
            ] = field(
                default_factory=list,
                metadata={
                    "name": "anwaltskosten.gemaessRVG",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )
            inkassokosten_anlage: None | Decimal = field(
                default=None,
                metadata={
                    "name": "inkassokosten.anlage",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                },
            )

            @dataclass(kw_only=True)
            class AnwaltskostenGemaessRvg:
                """
                :ivar vollstreckungsmassnahme: Bezeichnung der
                    Vollstreckungsmaßnahme
                :ivar anwaltskosten_gegenstandswert: Gegenstandswert
                    gemäß § 25 RVG
                :ivar verfahrensgebuehr: Verfahrensgebühr (VV Nr. 3309,
                    ggf. i. V. m. VV Nr. 1008)
                :ivar auslagenpauschale: Entgelte für Post- und
                    Telekommunikationsdienstleistungen, ggf. Pauschale
                    (VV Nr. 7001 oder 7002)
                :ivar weitere_auslagen:
                :ivar umsatzsteuer:
                :ivar zwischensumme_rechtsanwaltskosten_in_euro:
                """

                vollstreckungsmassnahme: str = field(
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "required": True,
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    }
                )
                anwaltskosten_gegenstandswert: Decimal = field(
                    metadata={
                        "name": "anwaltskosten.gegenstandswert",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "required": True,
                    }
                )
                verfahrensgebuehr: Decimal = field(
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "required": True,
                    }
                )
                auslagenpauschale: None | Decimal = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                    },
                )
                weitere_auslagen: list[
                    TypeZvstrForderungsaufstellungVollstreckungsauftrag.IvKostenZwangsvollstreckung.KostenDesVerfahrens.AnwaltskostenGemaessRvg.WeitereAuslagen
                ] = field(
                    default_factory=list,
                    metadata={
                        "name": "weitereAuslagen",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                    },
                )
                umsatzsteuer: None | Decimal = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                    },
                )
                zwischensumme_rechtsanwaltskosten_in_euro: Decimal = field(
                    metadata={
                        "name": "zwischensummeRechtsanwaltskostenInEuro",
                        "type": "Element",
                        "namespace": "http://www.xjustiz.de",
                        "required": True,
                    }
                )

                @dataclass(kw_only=True)
                class WeitereAuslagen:
                    bezeichnung: str = field(
                        metadata={
                            "type": "Element",
                            "namespace": "http://www.xjustiz.de",
                            "required": True,
                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                        }
                    )
                    betrag: Decimal = field(
                        metadata={
                            "type": "Element",
                            "namespace": "http://www.xjustiz.de",
                            "required": True,
                        }
                    )

        @dataclass(kw_only=True)
        class SonstigeKosten:
            bezeichnung: str = field(
                metadata={
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                }
            )
            betrag_in_euro: Decimal = field(
                metadata={
                    "name": "betragInEuro",
                    "type": "Element",
                    "namespace": "http://www.xjustiz.de",
                    "required": True,
                }
            )


@dataclass(kw_only=True)
class NachrichtZvstrForderungspfaendung2600002:
    class Meta:
        name = "nachricht.zvstr.forderungspfaendung.2600002"
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
    fachdaten: NachrichtZvstrForderungspfaendung2600002.Fachdaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        """
        :ivar beteiligter_zusatz: Für den im Grunddatensatz angegebenen
            Beteiligten werden weitergehende Informationen übergeben.
        :ivar antragsdaten:
        :ivar beschlussdaten:
        """

        beteiligter_zusatz: list[TypeZvstrBeteiligterZusatz] = field(
            default_factory=list,
            metadata={
                "name": "beteiligter.zusatz",
                "type": "Element",
            },
        )
        antragsdaten: (
            None
            | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Antragsdaten
        ) = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )
        beschlussdaten: NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten = field(
            metadata={
                "type": "Element",
                "required": True,
            }
        )

        @dataclass(kw_only=True)
        class Antragsdaten:
            """
            :ivar antragsort:
            :ivar antragsdatum:
            :ivar auswahl_gerichtskosten_vollstreckung:
            :ivar angaben_zum_schuldner:
            :ivar vorpfaendung: Es besteht bereits ein vorläufiges
                Zahlungsverbot nach § 845 ZPO (Vorpfändung).
            :ivar kontaktdaten_antragsteller:
            :ivar zusaetzliche_antraege:
            :ivar forderungsaufstellungen:
            :ivar auswahl_elektronisch_uebermittelte_antraege:
            :ivar sendungsdaten_weitere_anlagen:
            :ivar versicherung:
            """

            antragsort: str = field(
                metadata={
                    "type": "Element",
                    "required": True,
                    "pattern": r"([ -~]|[¡-£]|¥|[§-¬]|[®-·]|[¹-»]|[¿-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                }
            )
            antragsdatum: XmlDate = field(
                metadata={
                    "type": "Element",
                    "required": True,
                }
            )
            auswahl_gerichtskosten_vollstreckung: (
                None
                | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Antragsdaten.AuswahlGerichtskostenVollstreckung
            ) = field(
                default=None,
                metadata={
                    "name": "auswahl_gerichtskostenVollstreckung",
                    "type": "Element",
                },
            )
            angaben_zum_schuldner: TypeGdsRefRollennummer = field(
                metadata={
                    "name": "angabenZumSchuldner",
                    "type": "Element",
                    "required": True,
                }
            )
            vorpfaendung: None | bool = field(
                default=None,
                metadata={
                    "type": "Element",
                },
            )
            kontaktdaten_antragsteller: list[TypeGdsRefRollennummer] = field(
                default_factory=list,
                metadata={
                    "name": "kontaktdaten.antragsteller",
                    "type": "Element",
                },
            )
            zusaetzliche_antraege: list[
                NachrichtZvstrForderungspfaendung2600002.Fachdaten.Antragsdaten.ZusaetzlicheAntraege
            ] = field(
                default_factory=list,
                metadata={
                    "name": "zusaetzlicheAntraege",
                    "type": "Element",
                },
            )
            forderungsaufstellungen: NachrichtZvstrForderungspfaendung2600002.Fachdaten.Antragsdaten.Forderungsaufstellungen = field(
                metadata={
                    "type": "Element",
                    "required": True,
                }
            )
            auswahl_elektronisch_uebermittelte_antraege: (
                None | TypeZvstrElektronischUebermittelteAntraege
            ) = field(
                default=None,
                metadata={
                    "name": "auswahl_elektronischUebermittelteAntraege",
                    "type": "Element",
                },
            )
            sendungsdaten_weitere_anlagen: list[TypeZvstrAnlagen] = field(
                default_factory=list,
                metadata={
                    "name": "sendungsdaten.weitereAnlagen",
                    "type": "Element",
                    "min_occurs": 1,
                },
            )
            versicherung: (
                None
                | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Antragsdaten.Versicherung
            ) = field(
                default=None,
                metadata={
                    "type": "Element",
                },
            )

            @dataclass(kw_only=True)
            class AuswahlGerichtskostenVollstreckung:
                elektronische_kostenmarke: (
                    None
                    | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Antragsdaten.AuswahlGerichtskostenVollstreckung.ElektronischeKostenmarke
                ) = field(
                    default=None,
                    metadata={
                        "name": "elektronischeKostenmarke",
                        "type": "Element",
                    },
                )
                sepa_mandat: None | bool = field(
                    default=None,
                    metadata={
                        "name": "sepa-mandat",
                        "type": "Element",
                    },
                )
                gerichtskostenbefreiung_gemaess: None | str = field(
                    default=None,
                    metadata={
                        "name": "gerichtskostenbefreiungGemaess",
                        "type": "Element",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )

                @dataclass(kw_only=True)
                class ElektronischeKostenmarke:
                    nummer: str = field(
                        metadata={
                            "type": "Element",
                            "required": True,
                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                        }
                    )
                    wert_in_euro: Decimal = field(
                        metadata={
                            "name": "wert.inEuro",
                            "type": "Element",
                            "required": True,
                        }
                    )
                    datum: XmlDate = field(
                        metadata={
                            "type": "Element",
                            "required": True,
                        }
                    )

            @dataclass(kw_only=True)
            class ZusaetzlicheAntraege:
                antrag_erteilung_einer_ausfertigung: None | bool = field(
                    default=None,
                    metadata={
                        "name": "antrag.erteilungEinerAusfertigung",
                        "type": "Element",
                    },
                )
                antrag_zustellung: None | CodeZvstrAntragZustellung = field(
                    default=None,
                    metadata={
                        "name": "antrag.zustellung",
                        "type": "Element",
                    },
                )
                pkh: (
                    None
                    | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Antragsdaten.ZusaetzlicheAntraege.Pkh
                ) = field(
                    default=None,
                    metadata={
                        "type": "Element",
                    },
                )
                antrag_weiterer: None | str = field(
                    default=None,
                    metadata={
                        "name": "antrag.weiterer",
                        "type": "Element",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )

                @dataclass(kw_only=True)
                class Pkh:
                    glaeubiger: TypeGdsRefRollennummer = field(
                        metadata={
                            "type": "Element",
                            "required": True,
                        }
                    )
                    pkh_bewilligen: bool = field(
                        default=False,
                        metadata={
                            "name": "pkh.bewilligen",
                            "type": "Element",
                            "required": True,
                        },
                    )
                    ra_beiordnung: (
                        None
                        | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Antragsdaten.ZusaetzlicheAntraege.Pkh.RaBeiordnung
                    ) = field(
                        default=None,
                        metadata={
                            "name": "ra.beiordnung",
                            "type": "Element",
                        },
                    )

                    @dataclass(kw_only=True)
                    class RaBeiordnung:
                        ra_beiordnen: bool = field(
                            init=False,
                            default=True,
                            metadata={
                                "name": "ra.beiordnen",
                                "type": "Element",
                                "required": True,
                            },
                        )
                        begruendung: NachrichtZvstrForderungspfaendung2600002.Fachdaten.Antragsdaten.ZusaetzlicheAntraege.Pkh.RaBeiordnung.Begruendung = field(
                            metadata={
                                "type": "Element",
                                "required": True,
                            }
                        )
                        beizuordnender_rechtsanwalt: (
                            None | TypeGdsRefRollennummer
                        ) = field(
                            default=None,
                            metadata={
                                "name": "beizuordnenderRechtsanwalt",
                                "type": "Element",
                            },
                        )

                        @dataclass(kw_only=True)
                        class Begruendung:
                            schuldnerseite_rechtsanwaltlich_vertreten: (
                                None | bool
                            ) = field(
                                default=None,
                                metadata={
                                    "name": "schuldnerseiteRechtsanwaltlichVertreten",
                                    "type": "Element",
                                },
                            )
                            vertretung_erforderlich_gruende: None | str = (
                                field(
                                    default=None,
                                    metadata={
                                        "name": "vertretungErforderlich.gruende",
                                        "type": "Element",
                                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                                    },
                                )
                            )

            @dataclass(kw_only=True)
            class Forderungsaufstellungen:
                forderungsaufstellung_gewoehnliche_forderung: list[
                    TypeZvstrForderungsaufstellungGewoehnlicheForderung
                ] = field(
                    default_factory=list,
                    metadata={
                        "name": "forderungsaufstellung.gewoehnlicheForderung",
                        "type": "Element",
                    },
                )
                forderungsaufstellung_unterhaltsforderung: list[
                    TypeZvstrForderungsaufstellungUnterhaltsforderung
                ] = field(
                    default_factory=list,
                    metadata={
                        "name": "forderungsaufstellung.unterhaltsforderung",
                        "type": "Element",
                    },
                )
                forderungsaufstellungen_anzahl: int = field(
                    metadata={
                        "name": "forderungsaufstellungen.anzahl",
                        "type": "Element",
                        "required": True,
                    }
                )

            @dataclass(kw_only=True)
            class Versicherung:
                versicherung_753a_satz1_zpo: None | bool = field(
                    default=None,
                    metadata={
                        "name": "versicherung.753aSatz1ZPO",
                        "type": "Element",
                    },
                )
                versicherung_829a_abs1_nr4_zpo: None | bool = field(
                    default=None,
                    metadata={
                        "name": "versicherung.829aAbs1Nr4ZPO",
                        "type": "Element",
                    },
                )
                versicherung_weitere: list[str] = field(
                    default_factory=list,
                    metadata={
                        "name": "versicherung.weitere",
                        "type": "Element",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )

        @dataclass(kw_only=True)
        class Beschlussdaten:
            weitere_glaeubiger_gemaess_anlage: None | bool = field(
                default=None,
                metadata={
                    "name": "weitereGlaeubigerGemaessAnlage",
                    "type": "Element",
                },
            )
            bankverbindung_zum_glaeubiger: (
                None
                | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.BankverbindungZumGlaeubiger
            ) = field(
                default=None,
                metadata={
                    "name": "bankverbindungZumGlaeubiger",
                    "type": "Element",
                },
            )
            weitere_schuldner_gemaess_anlage: None | bool = field(
                default=None,
                metadata={
                    "name": "weitereSchuldnerGemaessAnlage",
                    "type": "Element",
                },
            )
            entscheidungsumfang: CodeZvstrEntscheidungsumfangPfUeb = field(
                metadata={
                    "type": "Element",
                    "required": True,
                }
            )
            vollstreckungstitel: list[TypeZvstrVollstreckungstitel] = field(
                default_factory=list,
                metadata={
                    "type": "Element",
                },
            )
            weitere_vollstreckungstitel_gemaess_anlage: None | bool = field(
                default=None,
                metadata={
                    "name": "weitereVollstreckungstitelGemaessAnlage",
                    "type": "Element",
                },
            )
            vom_gericht_auszufuellen: (
                None
                | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.VomGerichtAuszufuellen
            ) = field(
                default=None,
                metadata={
                    "name": "vomGerichtAuszufuellen",
                    "type": "Element",
                },
            )
            weitere_angaben_drittschuldner: list[
                NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.WeitereAngabenDrittschuldner
            ] = field(
                default_factory=list,
                metadata={
                    "name": "weitereAngaben.drittschuldner",
                    "type": "Element",
                },
            )
            weitere_drittschuldner_gemaess_anlage: None | bool = field(
                default=None,
                metadata={
                    "name": "weitereDrittschuldnerGemaessAnlage",
                    "type": "Element",
                },
            )
            anspruch: list[TypeZvstrAnspruchPfUeb] = field(
                default_factory=list,
                metadata={
                    "type": "Element",
                    "min_occurs": 1,
                },
            )
            anordnung_nach829_abs1_und835_abs1_zpo: str = field(
                init=False,
                default="Die Drittschuldner dürfen, soweit die Forderungen gepfändet sind, an die Schuldner nicht mehr zahlen; die Schuldner dürfen insoweit nicht über die Forderungen verfügen, sie insbesondere nicht einziehen. Im Anwendungsbereich des § 850c ZPO wird auf die Pfändungsfreigrenzenbekanntmachung in der jeweils geltenden Fassung Bezug genommen (§ 850c Absatz 5 Satz 3 ZPO)",
                metadata={
                    "name": "anordnungNach829Abs1Und835Abs1ZPO",
                    "type": "Element",
                    "required": True,
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            auswahl_anordnung_drittschuldner: (
                None
                | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.AuswahlAnordnungDrittschuldner
            ) = field(
                default=None,
                metadata={
                    "name": "auswahl_anordnung.drittschuldner",
                    "type": "Element",
                },
            )
            anordnungen_gegenueber_schuldner: list[
                TypeZvstrAnordnungenGegenueberSchuldner
            ] = field(
                default_factory=list,
                metadata={
                    "name": "anordnungen.gegenueberSchuldner",
                    "type": "Element",
                },
            )
            ergaenzende_antraege: list[
                NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.ErgaenzendeAntraege
            ] = field(
                default_factory=list,
                metadata={
                    "name": "ergaenzendeAntraege",
                    "type": "Element",
                },
            )
            angaben_schuldner_persoenliche_wirtschaftliche_verhaeltnisse: list[
                NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.AngabenSchuldnerPersoenlicheWirtschaftlicheVerhaeltnisse
            ] = field(
                default_factory=list,
                metadata={
                    "name": "angabenSchuldner.persoenlicheWirtschaftlicheVerhaeltnisse",
                    "type": "Element",
                },
            )
            zusaetzliche_angaben_fuer_pfaendung850d_zpo: (
                None
                | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.ZusaetzlicheAngabenFuerPfaendung850DZpo
            ) = field(
                default=None,
                metadata={
                    "name": "zusaetzlicheAngabenFuerPfaendung850dZPO",
                    "type": "Element",
                },
            )
            unterhaltsberechtige_personen_eigenes_einkommen: list[
                NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.UnterhaltsberechtigePersonenEigenesEinkommen
            ] = field(
                default_factory=list,
                metadata={
                    "name": "unterhaltsberechtigePersonen.eigenesEinkommen",
                    "type": "Element",
                },
            )
            anordnung_nach850d_zpo: (
                None
                | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.AnordnungNach850DZpo
            ) = field(
                default=None,
                metadata={
                    "name": "anordnungNach850dZPO",
                    "type": "Element",
                },
            )
            anordnung_nach850c_absatz6_zpo: (
                None
                | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.AnordnungNach850CAbsatz6Zpo
            ) = field(
                default=None,
                metadata={
                    "name": "anordnungNach850cAbsatz6ZPO",
                    "type": "Element",
                },
            )
            anordnung_nach850f_absatz2_zpo: (
                None
                | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.AnordnungNach850FAbsatz2Zpo
            ) = field(
                default=None,
                metadata={
                    "name": "anordnungNach850fAbsatz2ZPO",
                    "type": "Element",
                },
            )
            vom_gericht_auszufuellen_modul_t: (
                None
                | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.VomGerichtAuszufuellenModulT
            ) = field(
                default=None,
                metadata={
                    "name": "vomGerichtAuszufuellen.modulT",
                    "type": "Element",
                },
            )

            @dataclass(kw_only=True)
            class BankverbindungZumGlaeubiger:
                ref_kontoinhaber: TypeGdsRefRollennummer = field(
                    metadata={
                        "name": "ref.kontoinhaber",
                        "type": "Element",
                        "required": True,
                    }
                )
                ref_bankverbindung: TypeGdsRefBankverbindung = field(
                    metadata={
                        "name": "ref.bankverbindung",
                        "type": "Element",
                        "required": True,
                    }
                )

            @dataclass(kw_only=True)
            class VomGerichtAuszufuellen:
                zustellungskosten_pfueb: bool = field(
                    init=False,
                    default=True,
                    metadata={
                        "name": "zustellungskosten.pfueb",
                        "type": "Element",
                        "required": True,
                    },
                )

            @dataclass(kw_only=True)
            class WeitereAngabenDrittschuldner:
                ref_drittschuldner: TypeGdsRefRollennummer = field(
                    metadata={
                        "name": "ref.drittschuldner",
                        "type": "Element",
                        "required": True,
                    }
                )
                ref_schuldner: TypeGdsRefRollennummer = field(
                    metadata={
                        "name": "ref.schuldner",
                        "type": "Element",
                        "required": True,
                    }
                )
                ref_modul_nr: list[int] = field(
                    default_factory=list,
                    metadata={
                        "name": "ref.modulNr",
                        "type": "Element",
                        "min_occurs": 1,
                    },
                )

            @dataclass(kw_only=True)
            class AuswahlAnordnungDrittschuldner:
                zur_einziehung_ueberwiesen: None | str = field(
                    default=None,
                    metadata={
                        "name": "zurEinziehungUeberwiesen",
                        "type": "Element",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )
                an_zahlungs_statt_ueberwiesen: None | str = field(
                    default=None,
                    metadata={
                        "name": "anZahlungsStattUeberwiesen",
                        "type": "Element",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )

            @dataclass(kw_only=True)
            class ErgaenzendeAntraege:
                ref_schuldner: TypeGdsRefRollennummer = field(
                    metadata={
                        "name": "ref.schuldner",
                        "type": "Element",
                        "required": True,
                    }
                )
                arbeitseinkommen_und_arbeitseinkommen: (
                    None
                    | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.ErgaenzendeAntraege.ArbeitseinkommenUndArbeitseinkommen
                ) = field(
                    default=None,
                    metadata={
                        "name": "arbeitseinkommenUndArbeitseinkommen",
                        "type": "Element",
                    },
                )
                geldleistung_und_arbeitseinkommen: (
                    None
                    | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.ErgaenzendeAntraege.GeldleistungUndArbeitseinkommen
                ) = field(
                    default=None,
                    metadata={
                        "name": "geldleistungUndArbeitseinkommen",
                        "type": "Element",
                    },
                )
                geldleistung_und_geldleistung: (
                    None
                    | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.ErgaenzendeAntraege.GeldleistungUndGeldleistung
                ) = field(
                    default=None,
                    metadata={
                        "name": "geldleistungUndGeldleistung",
                        "type": "Element",
                    },
                )

                @dataclass(kw_only=True)
                class ArbeitseinkommenUndArbeitseinkommen:
                    arbeitseinkommen: list[
                        NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.ErgaenzendeAntraege.ArbeitseinkommenUndArbeitseinkommen.Arbeitseinkommen
                    ] = field(
                        default_factory=list,
                        metadata={
                            "type": "Element",
                            "min_occurs": 2,
                        },
                    )
                    unpfaendbarer_grundbetrag_drittschuldner: TypeGdsRefRollennummer = field(
                        metadata={
                            "name": "unpfaendbarerGrundbetrag.drittschuldner",
                            "type": "Element",
                            "required": True,
                        }
                    )

                    @dataclass(kw_only=True)
                    class Arbeitseinkommen:
                        ref_drittschuldner: TypeGdsRefRollennummer = field(
                            metadata={
                                "name": "ref.drittschuldner",
                                "type": "Element",
                                "required": True,
                            }
                        )
                        betrag_in_euro: Decimal = field(
                            metadata={
                                "name": "betrag.inEuro",
                                "type": "Element",
                                "required": True,
                            }
                        )

                @dataclass(kw_only=True)
                class GeldleistungUndArbeitseinkommen:
                    geldleistung: list[
                        NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.ErgaenzendeAntraege.GeldleistungUndArbeitseinkommen.Geldleistung
                    ] = field(
                        default_factory=list,
                        metadata={
                            "type": "Element",
                            "min_occurs": 1,
                        },
                    )
                    arbeitseinkommen: list[
                        NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.ErgaenzendeAntraege.GeldleistungUndArbeitseinkommen.Arbeitseinkommen
                    ] = field(
                        default_factory=list,
                        metadata={
                            "type": "Element",
                            "min_occurs": 1,
                        },
                    )
                    auswahl_unpfaendbarer_grundbetrag_drittschuldner: NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.ErgaenzendeAntraege.GeldleistungUndArbeitseinkommen.AuswahlUnpfaendbarerGrundbetragDrittschuldner = field(
                        metadata={
                            "name": "auswahl_unpfaendbarerGrundbetrag.drittschuldner",
                            "type": "Element",
                            "required": True,
                        }
                    )

                    @dataclass(kw_only=True)
                    class Geldleistung:
                        geldleistung_bezeichnung: str = field(
                            metadata={
                                "name": "geldleistung.bezeichnung",
                                "type": "Element",
                                "required": True,
                                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                            }
                        )
                        ref_drittschuldner: TypeGdsRefRollennummer = field(
                            metadata={
                                "name": "ref.drittschuldner",
                                "type": "Element",
                                "required": True,
                            }
                        )

                    @dataclass(kw_only=True)
                    class Arbeitseinkommen:
                        ref_drittschuldner: TypeGdsRefRollennummer = field(
                            metadata={
                                "name": "ref.drittschuldner",
                                "type": "Element",
                                "required": True,
                            }
                        )

                    @dataclass(kw_only=True)
                    class AuswahlUnpfaendbarerGrundbetragDrittschuldner:
                        entnahme_arbeitseinkommen: None | bool = field(
                            default=None,
                            metadata={
                                "name": "entnahme.arbeitseinkommen",
                                "type": "Element",
                            },
                        )
                        entnahme_geldleistung: None | bool = field(
                            default=None,
                            metadata={
                                "name": "entnahme.geldleistung",
                                "type": "Element",
                            },
                        )

                @dataclass(kw_only=True)
                class GeldleistungUndGeldleistung:
                    geldleistung: list[
                        NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.ErgaenzendeAntraege.GeldleistungUndGeldleistung.Geldleistung
                    ] = field(
                        default_factory=list,
                        metadata={
                            "type": "Element",
                            "min_occurs": 2,
                        },
                    )
                    unpfaendbarer_grundbetrag_drittschuldner: TypeGdsRefRollennummer = field(
                        metadata={
                            "name": "unpfaendbarerGrundbetrag.drittschuldner",
                            "type": "Element",
                            "required": True,
                        }
                    )

                    @dataclass(kw_only=True)
                    class Geldleistung:
                        geldleistung_bezeichnung: str = field(
                            metadata={
                                "name": "geldleistung.bezeichnung",
                                "type": "Element",
                                "required": True,
                                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                            }
                        )
                        ref_drittschuldner: TypeGdsRefRollennummer = field(
                            metadata={
                                "name": "ref.drittschuldner",
                                "type": "Element",
                                "required": True,
                            }
                        )
                        betrag_in_euro: Decimal = field(
                            metadata={
                                "name": "betrag.inEuro",
                                "type": "Element",
                                "required": True,
                            }
                        )

            @dataclass(kw_only=True)
            class AngabenSchuldnerPersoenlicheWirtschaftlicheVerhaeltnisse:
                ref_schuldner: TypeGdsRefRollennummer = field(
                    metadata={
                        "name": "ref.schuldner",
                        "type": "Element",
                        "required": True,
                    }
                )
                unterhaltspflichten: list[
                    NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.AngabenSchuldnerPersoenlicheWirtschaftlicheVerhaeltnisse.Unterhaltspflichten
                ] = field(
                    default_factory=list,
                    metadata={
                        "type": "Element",
                        "min_occurs": 1,
                    },
                )
                teilweise_erfuellung_unterhaltspflicht: None | str = field(
                    default=None,
                    metadata={
                        "name": "teilweiseErfuellungUnterhaltspflicht",
                        "type": "Element",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )
                sonstige_angaben: None | str = field(
                    default=None,
                    metadata={
                        "name": "sonstigeAngaben",
                        "type": "Element",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )
                auswahl_erwerbstaetigkeit_schuldner: (
                    None
                    | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.AngabenSchuldnerPersoenlicheWirtschaftlicheVerhaeltnisse.AuswahlErwerbstaetigkeitSchuldner
                ) = field(
                    default=None,
                    metadata={
                        "name": "auswahl_erwerbstaetigkeitSchuldner",
                        "type": "Element",
                    },
                )
                auswahl_familienstand: (
                    None
                    | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.AngabenSchuldnerPersoenlicheWirtschaftlicheVerhaeltnisse.AuswahlFamilienstand
                ) = field(
                    default=None,
                    metadata={
                        "type": "Element",
                    },
                )

                @dataclass(kw_only=True)
                class Unterhaltspflichten:
                    unterhaltsberechtigte_person: NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.AngabenSchuldnerPersoenlicheWirtschaftlicheVerhaeltnisse.Unterhaltspflichten.UnterhaltsberechtigtePerson = field(
                        metadata={
                            "name": "unterhaltsberechtigtePerson",
                            "type": "Element",
                            "required": True,
                        }
                    )
                    auswahl_umfang_unterhaltspflicht: NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.AngabenSchuldnerPersoenlicheWirtschaftlicheVerhaeltnisse.Unterhaltspflichten.AuswahlUmfangUnterhaltspflicht = field(
                        metadata={
                            "name": "auswahl_umfangUnterhaltspflicht",
                            "type": "Element",
                            "required": True,
                        }
                    )

                    @dataclass(kw_only=True)
                    class UnterhaltsberechtigtePerson:
                        ref_unterhaltsberechtigte_person: TypeGdsRefRollennummer = field(
                            metadata={
                                "name": "ref.unterhaltsberechtigtePerson",
                                "type": "Element",
                                "required": True,
                            }
                        )
                        verwandtschaftsverhaeltnis_zum_schuldner: CodeZvstrUnterhaltsberechtigter = field(
                            metadata={
                                "name": "verwandtschaftsverhaeltnisZumSchuldner",
                                "type": "Element",
                                "required": True,
                            }
                        )

                    @dataclass(kw_only=True)
                    class AuswahlUmfangUnterhaltspflicht:
                        vollstaendig: None | bool = field(
                            default=None,
                            metadata={
                                "type": "Element",
                            },
                        )
                        teilweise: None | bool = field(
                            default=None,
                            metadata={
                                "type": "Element",
                            },
                        )
                        nicht: None | bool = field(
                            default=None,
                            metadata={
                                "type": "Element",
                            },
                        )

                @dataclass(kw_only=True)
                class AuswahlErwerbstaetigkeitSchuldner:
                    erwerbstaetig: None | bool = field(
                        default=None,
                        metadata={
                            "type": "Element",
                        },
                    )
                    nicht_erwerbstaetig: None | bool = field(
                        default=None,
                        metadata={
                            "name": "nichtErwerbstaetig",
                            "type": "Element",
                        },
                    )

                @dataclass(kw_only=True)
                class AuswahlFamilienstand:
                    familienstand: None | CodeGdsFamilienstand = field(
                        default=None,
                        metadata={
                            "type": "Element",
                        },
                    )
                    verheiratet_oder_lebenspartnerschaft_mit_glaeubiger: (
                        None | bool
                    ) = field(
                        default=None,
                        metadata={
                            "name": "verheiratetOderLebenspartnerschaftMitGlaeubiger",
                            "type": "Element",
                        },
                    )

            @dataclass(kw_only=True)
            class ZusaetzlicheAngabenFuerPfaendung850DZpo:
                zahlungspflicht_nicht_absichtlich_entzogen: bool = field(
                    metadata={
                        "name": "zahlungspflichtNichtAbsichtlichEntzogen",
                        "type": "Element",
                        "required": True,
                    }
                )

            @dataclass(kw_only=True)
            class UnterhaltsberechtigePersonenEigenesEinkommen:
                ref_schuldner: TypeGdsRefRollennummer = field(
                    metadata={
                        "name": "ref.schuldner",
                        "type": "Element",
                        "required": True,
                    }
                )
                unterhaltsberechtige_personen: NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.UnterhaltsberechtigePersonenEigenesEinkommen.UnterhaltsberechtigePersonen = field(
                    metadata={
                        "name": "unterhaltsberechtigePersonen",
                        "type": "Element",
                        "required": True,
                    }
                )
                weitere_angaben: None | str = field(
                    default=None,
                    metadata={
                        "name": "weitereAngaben",
                        "type": "Element",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )

                @dataclass(kw_only=True)
                class UnterhaltsberechtigePersonen:
                    ehegatte_oder_eingetragener_lebenspartner: (
                        None
                        | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.UnterhaltsberechtigePersonenEigenesEinkommen.UnterhaltsberechtigePersonen.EhegatteOderEingetragenerLebenspartner
                    ) = field(
                        default=None,
                        metadata={
                            "name": "ehegatteOderEingetragenerLebenspartner",
                            "type": "Element",
                        },
                    )
                    kinder: list[
                        NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.UnterhaltsberechtigePersonenEigenesEinkommen.UnterhaltsberechtigePersonen.Kinder
                    ] = field(
                        default_factory=list,
                        metadata={
                            "type": "Element",
                        },
                    )

                    @dataclass(kw_only=True)
                    class EhegatteOderEingetragenerLebenspartner:
                        ref_ehegatte_oder_eingetragener_lebenspartner: TypeGdsRefRollennummer = field(
                            metadata={
                                "name": "ref.ehegatteOderEingetragenerLebenspartner",
                                "type": "Element",
                                "required": True,
                            }
                        )
                        einkommen_art_und_hoehe: str = field(
                            metadata={
                                "name": "einkommen.artUndHoehe",
                                "type": "Element",
                                "required": True,
                                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                            }
                        )

                    @dataclass(kw_only=True)
                    class Kinder:
                        ref_kinder: TypeGdsRefRollennummer = field(
                            metadata={
                                "name": "ref.kinder",
                                "type": "Element",
                                "required": True,
                            }
                        )
                        einkommen_art_und_hoehe: str = field(
                            metadata={
                                "name": "einkommen.artUndHoehe",
                                "type": "Element",
                                "required": True,
                                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                            }
                        )

            @dataclass(kw_only=True)
            class AnordnungNach850DZpo:
                """
                :ivar
                    anordnung_pfaendbarkeit_bei_unterhaltsanspruechen_850d_zpo:
                :ivar ref_schuldner:
                :ivar vom_gericht_auszufuellen: Wenn die Pfändbarkeit
                    bei Unterhaltsansprüchen nach § 850d ZPO angeordnet
                    wird, so sind die hier aufgeführten Elemente vom
                    Gericht auszufüllen.
                """

                anordnung_pfaendbarkeit_bei_unterhaltsanspruechen_850d_zpo: (
                    None | bool
                ) = field(
                    default=None,
                    metadata={
                        "name": "anordnung.pfaendbarkeitBeiUnterhaltsanspruechen.850dZPO",
                        "type": "Element",
                    },
                )
                ref_schuldner: None | TypeGdsRefRollennummer = field(
                    default=None,
                    metadata={
                        "name": "ref.schuldner",
                        "type": "Element",
                    },
                )
                vom_gericht_auszufuellen: (
                    None
                    | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.AnordnungNach850DZpo.VomGerichtAuszufuellen
                ) = field(
                    default=None,
                    metadata={
                        "name": "vomGerichtAuszufuellen",
                        "type": "Element",
                    },
                )

                @dataclass(kw_only=True)
                class VomGerichtAuszufuellen:
                    """
                    :ivar unterhalts_rueckstaende:
                    :ivar schuldner_unpfaendbarer_betrag_in_euro:
                        Hierüber kann mitgeteilt werden, wieviel dem
                        Schuldner bis zur Deckung des Gläubigeranspruchs
                        für seinen eigenen notwendigen Unterhalt in Euro
                        als unpfändbarer Betrag monatlich zu belassen
                        ist.
                    :ivar monatlich_unpfaendbarer_betrag:
                    :ivar monatlich_unpfaendbarer_betrag_weiterer:
                    :ivar sonstige_anordnungen:
                    :ivar gruende:
                    """

                    unterhalts_rueckstaende: (
                        None
                        | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.AnordnungNach850DZpo.VomGerichtAuszufuellen.UnterhaltsRueckstaende
                    ) = field(
                        default=None,
                        metadata={
                            "name": "unterhaltsRueckstaende",
                            "type": "Element",
                        },
                    )
                    schuldner_unpfaendbarer_betrag_in_euro: None | Decimal = (
                        field(
                            default=None,
                            metadata={
                                "name": "schuldner.unpfaendbarerBetrag.inEuro",
                                "type": "Element",
                            },
                        )
                    )
                    monatlich_unpfaendbarer_betrag: (
                        None
                        | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.AnordnungNach850DZpo.VomGerichtAuszufuellen.MonatlichUnpfaendbarerBetrag
                    ) = field(
                        default=None,
                        metadata={
                            "name": "monatlichUnpfaendbarerBetrag",
                            "type": "Element",
                        },
                    )
                    monatlich_unpfaendbarer_betrag_weiterer: (
                        None
                        | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.AnordnungNach850DZpo.VomGerichtAuszufuellen.MonatlichUnpfaendbarerBetragWeiterer
                    ) = field(
                        default=None,
                        metadata={
                            "name": "monatlichUnpfaendbarerBetrag.weiterer",
                            "type": "Element",
                        },
                    )
                    sonstige_anordnungen: list[str] = field(
                        default_factory=list,
                        metadata={
                            "name": "sonstigeAnordnungen",
                            "type": "Element",
                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                        },
                    )
                    gruende: None | str = field(
                        default=None,
                        metadata={
                            "type": "Element",
                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                        },
                    )

                    @dataclass(kw_only=True)
                    class UnterhaltsRueckstaende:
                        """
                        :ivar nichtgeltung_850d_abs1_satz1bis3_zpo: Für
                            die Pfändung wegen der Rückstände, die
                            länger als ein Jahr vor dem Antrag auf
                            Erlass des Pfändungsbeschlusses, bei Gericht
                            eingegangen, siehe Element
                            "pfuebEingangBeiGericht", fällig geworden
                            sind, gilt § 850d Absatz 1 Satz 1 bis 3 ZPO
                            nicht.
                        :ivar pfueb_eingang_bei_gericht:
                        """

                        nichtgeltung_850d_abs1_satz1bis3_zpo: bool = field(
                            init=False,
                            default=True,
                            metadata={
                                "name": "nichtgeltung.850dAbs1Satz1bis3ZPO",
                                "type": "Element",
                                "required": True,
                            },
                        )
                        pfueb_eingang_bei_gericht: XmlDate = field(
                            metadata={
                                "name": "pfuebEingangBeiGericht",
                                "type": "Element",
                                "required": True,
                            }
                        )

                    @dataclass(kw_only=True)
                    class MonatlichUnpfaendbarerBetrag:
                        erfuellung_laufende_unterhaltspflichten_in_euro: (
                            None | Decimal
                        ) = field(
                            default=None,
                            metadata={
                                "name": "erfuellungLaufendeUnterhaltspflichten.inEuro",
                                "type": "Element",
                            },
                        )
                        verbleibender_betrag_unterhaltsberechtige_person_wie_glaeubiger: (
                            None
                            | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.AnordnungNach850DZpo.VomGerichtAuszufuellen.MonatlichUnpfaendbarerBetrag.VerbleibenderBetragUnterhaltsberechtigePersonWieGlaeubiger
                        ) = field(
                            default=None,
                            metadata={
                                "name": "verbleibenderBetrag.unterhaltsberechtigePersonWieGlaeubiger",
                                "type": "Element",
                            },
                        )

                        @dataclass(kw_only=True)
                        class VerbleibenderBetragUnterhaltsberechtigePersonWieGlaeubiger:
                            zaehler: int = field(
                                metadata={
                                    "type": "Element",
                                    "required": True,
                                }
                            )
                            nenner: int = field(
                                metadata={
                                    "type": "Element",
                                    "required": True,
                                }
                            )

                    @dataclass(kw_only=True)
                    class MonatlichUnpfaendbarerBetragWeiterer:
                        arbeitseinkommen_ohne_beschraenkungen: None | bool = (
                            field(
                                default=None,
                                metadata={
                                    "name": "arbeitseinkommen.ohneBeschraenkungen",
                                    "type": "Element",
                                },
                            )
                        )

            @dataclass(kw_only=True)
            class AnordnungNach850CAbsatz6Zpo:
                """
                :ivar
                    nicht_beruecksichtigung_von_unterhaltsberechtigten:
                    Es wird die (teilweise) Nichtberücksichtigung von
                    Unterhaltsberechtigten des Schuldners nach § 850c
                    Absatz 6 ZPO angeordnet.
                :ivar ref_schuldner:
                :ivar vom_gericht_auszufuellen: Vom Gericht zu befüllen
                    für die Berechnung des unpfändbaren Teils
                """

                nicht_beruecksichtigung_von_unterhaltsberechtigten: (
                    None | bool
                ) = field(
                    default=None,
                    metadata={
                        "name": "nichtBeruecksichtigungVonUnterhaltsberechtigten",
                        "type": "Element",
                    },
                )
                ref_schuldner: None | TypeGdsRefRollennummer = field(
                    default=None,
                    metadata={
                        "name": "ref.schuldner",
                        "type": "Element",
                    },
                )
                vom_gericht_auszufuellen: (
                    None
                    | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.AnordnungNach850CAbsatz6Zpo.VomGerichtAuszufuellen
                ) = field(
                    default=None,
                    metadata={
                        "name": "vomGerichtAuszufuellen",
                        "type": "Element",
                    },
                )

                @dataclass(kw_only=True)
                class VomGerichtAuszufuellen:
                    arbeitseinkommen_schuldner: None | bool = field(
                        default=None,
                        metadata={
                            "name": "arbeitseinkommen.schuldner",
                            "type": "Element",
                        },
                    )
                    guthaben_pfaendungsschutzkonto_schuldner: None | bool = (
                        field(
                            default=None,
                            metadata={
                                "name": "guthaben.pfaendungsschutzkontoSchuldner",
                                "type": "Element",
                            },
                        )
                    )
                    unberuecksichtigte_personen: list[
                        NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.AnordnungNach850CAbsatz6Zpo.VomGerichtAuszufuellen.UnberuecksichtigtePersonen
                    ] = field(
                        default_factory=list,
                        metadata={
                            "name": "unberuecksichtigtePersonen",
                            "type": "Element",
                            "min_occurs": 1,
                        },
                    )
                    gruende: None | str = field(
                        default=None,
                        metadata={
                            "type": "Element",
                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                        },
                    )

                    @dataclass(kw_only=True)
                    class UnberuecksichtigtePersonen:
                        ref_unberuecksichtigte_person: TypeGdsRefRollennummer = field(
                            metadata={
                                "name": "ref.unberuecksichtigtePerson",
                                "type": "Element",
                                "required": True,
                            }
                        )
                        auswahl_hoehe_nichtberuecksichtigung: NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.AnordnungNach850CAbsatz6Zpo.VomGerichtAuszufuellen.UnberuecksichtigtePersonen.AuswahlHoeheNichtberuecksichtigung = field(
                            metadata={
                                "name": "auswahl_hoeheNichtberuecksichtigung",
                                "type": "Element",
                                "required": True,
                            }
                        )

                        @dataclass(kw_only=True)
                        class AuswahlHoeheNichtberuecksichtigung:
                            ganz: None | bool = field(
                                default=None,
                                metadata={
                                    "type": "Element",
                                },
                            )
                            in_hoehe_von_betrag_in_euro: None | Decimal = (
                                field(
                                    default=None,
                                    metadata={
                                        "name": "inHoeheVonBetrag.inEuro",
                                        "type": "Element",
                                    },
                                )
                            )
                            in_hoehe_von_prozent: None | Decimal = field(
                                default=None,
                                metadata={
                                    "name": "inHoeheVonProzent",
                                    "type": "Element",
                                },
                            )

            @dataclass(kw_only=True)
            class AnordnungNach850FAbsatz2Zpo:
                anordnung_pfaendbarkeit_forderung_aus_unerlaubter_handlung: (
                    None | bool
                ) = field(
                    default=None,
                    metadata={
                        "name": "anordnungPfaendbarkeit.forderungAusUnerlaubterHandlung",
                        "type": "Element",
                    },
                )
                ref_schuldner: None | TypeGdsRefRollennummer = field(
                    default=None,
                    metadata={
                        "name": "ref.schuldner",
                        "type": "Element",
                    },
                )
                vom_gericht_auszufuellen: (
                    None
                    | NachrichtZvstrForderungspfaendung2600002.Fachdaten.Beschlussdaten.AnordnungNach850FAbsatz2Zpo.VomGerichtAuszufuellen
                ) = field(
                    default=None,
                    metadata={
                        "name": "vomGerichtAuszufuellen",
                        "type": "Element",
                    },
                )

                @dataclass(kw_only=True)
                class VomGerichtAuszufuellen:
                    pfaendungsgrenzen_arbeitseinkommen_keine_ruecksicht_auf850c_zpo: (
                        None | str
                    ) = field(
                        default=None,
                        metadata={
                            "name": "pfaendungsgrenzenArbeitseinkommen.keineRuecksichtAuf850cZPO",
                            "type": "Element",
                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                        },
                    )
                    arbeitseinkommen_schuldner: None | bool = field(
                        default=None,
                        metadata={
                            "name": "arbeitseinkommenSchuldner",
                            "type": "Element",
                        },
                    )
                    guthaben_pfaendungsschutzkonto_schuldner: None | bool = (
                        field(
                            default=None,
                            metadata={
                                "name": "guthabenPfaendungsschutzkontoSchuldner",
                                "type": "Element",
                            },
                        )
                    )
                    notwendiger_unterhalt: Decimal = field(
                        metadata={
                            "name": "notwendigerUnterhalt",
                            "type": "Element",
                            "required": True,
                        }
                    )
                    erfuellung_gesetzlicher_unterhaltspflichten: (
                        None | Decimal
                    ) = field(
                        default=None,
                        metadata={
                            "name": "erfuellungGesetzlicherUnterhaltspflichten",
                            "type": "Element",
                        },
                    )
                    gruende: None | str = field(
                        default=None,
                        metadata={
                            "type": "Element",
                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                        },
                    )

            @dataclass(kw_only=True)
            class VomGerichtAuszufuellenModulT:
                """
                :ivar freitextfeld_beschluss: Dieser Bereich ist vom
                    Gericht auszufüllen.
                """

                freitextfeld_beschluss: str = field(
                    metadata={
                        "name": "freitextfeld.beschluss",
                        "type": "Element",
                        "required": True,
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    }
                )


@dataclass(kw_only=True)
class NachrichtZvstrVollstreckungsauftrag2600003:
    class Meta:
        name = "nachricht.zvstr.vollstreckungsauftrag.2600003"
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
    fachdaten: NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass(kw_only=True)
    class Fachdaten:
        """
        :ivar beteiligter_zusatz: Für den im Grunddatensatz angegebenen
            Beteiligten werden weitergehende Informationen übergeben.
        :ivar antragsort:
        :ivar antragsdatum:
        :ivar angaben_zum_schuldner:
        :ivar kontaktdaten_auftraggeber:
        :ivar angaben_bankverbindung:
        :ivar weitere_glaeubiger_gemaess_anlage:
        :ivar weitere_schuldner_gemaess_anlage:
        :ivar vollstreckungstitel:
        :ivar weitere_vollstreckungstitel_gemaess_anlage:
        :ivar forderungsaufstellung:
        :ivar auswahl_elektronisch_uebermittelte_antraege:
        :ivar sendungsdaten_weitere_anlagen:
        :ivar versicherung:
        :ivar auftraege: Wegen der aus den Forderungsaufstellungen
            ersichtlichen Forderungen und der für dieses Verfahren
            entstehenden Kosten werden folgende Aufträge erteilt.
        :ivar reihenfolge_der_auftraege:
        :ivar hinweise_vorgaben_an_gerichtsvollzieher:
        """

        beteiligter_zusatz: list[TypeZvstrBeteiligterZusatz] = field(
            default_factory=list,
            metadata={
                "name": "beteiligter.zusatz",
                "type": "Element",
            },
        )
        antragsort: str = field(
            metadata={
                "type": "Element",
                "required": True,
                "pattern": r"([ -~]|[¡-£]|¥|[§-¬]|[®-·]|[¹-»]|[¿-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            }
        )
        antragsdatum: XmlDate = field(
            metadata={
                "type": "Element",
                "required": True,
            }
        )
        angaben_zum_schuldner: TypeGdsRefRollennummer = field(
            metadata={
                "name": "angabenZumSchuldner",
                "type": "Element",
                "required": True,
            }
        )
        kontaktdaten_auftraggeber: list[TypeGdsRefRollennummer] = field(
            default_factory=list,
            metadata={
                "name": "kontaktdaten.auftraggeber",
                "type": "Element",
            },
        )
        angaben_bankverbindung: (
            None
            | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.AngabenBankverbindung
        ) = field(
            default=None,
            metadata={
                "name": "angabenBankverbindung",
                "type": "Element",
            },
        )
        weitere_glaeubiger_gemaess_anlage: None | bool = field(
            default=None,
            metadata={
                "name": "weitereGlaeubigerGemaessAnlage",
                "type": "Element",
            },
        )
        weitere_schuldner_gemaess_anlage: None | bool = field(
            default=None,
            metadata={
                "name": "weitereSchuldnerGemaessAnlage",
                "type": "Element",
            },
        )
        vollstreckungstitel: list[
            NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Vollstreckungstitel
        ] = field(
            default_factory=list,
            metadata={
                "type": "Element",
            },
        )
        weitere_vollstreckungstitel_gemaess_anlage: None | bool = field(
            default=None,
            metadata={
                "name": "weitereVollstreckungstitelGemaessAnlage",
                "type": "Element",
            },
        )
        forderungsaufstellung: (
            None
            | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Forderungsaufstellung
        ) = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )
        auswahl_elektronisch_uebermittelte_antraege: (
            None | TypeZvstrElektronischUebermittelteAntraege
        ) = field(
            default=None,
            metadata={
                "name": "auswahl_elektronischUebermittelteAntraege",
                "type": "Element",
            },
        )
        sendungsdaten_weitere_anlagen: list[TypeZvstrAnlagen] = field(
            default_factory=list,
            metadata={
                "name": "sendungsdaten.weitereAnlagen",
                "type": "Element",
            },
        )
        versicherung: (
            None
            | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Versicherung
        ) = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )
        auftraege: NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege = field(
            metadata={
                "type": "Element",
                "required": True,
            }
        )
        reihenfolge_der_auftraege: (
            None
            | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.ReihenfolgeDerAuftraege
        ) = field(
            default=None,
            metadata={
                "name": "reihenfolgeDerAuftraege",
                "type": "Element",
            },
        )
        hinweise_vorgaben_an_gerichtsvollzieher: (
            None
            | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.HinweiseVorgabenAnGerichtsvollzieher
        ) = field(
            default=None,
            metadata={
                "name": "hinweiseVorgabenAnGerichtsvollzieher",
                "type": "Element",
            },
        )

        @dataclass(kw_only=True)
        class AngabenBankverbindung:
            auswahl_sepa_lastschriftmandat_befreiung_gerichtsvollzieherkosten: (
                None
                | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.AngabenBankverbindung.AuswahlSepaLastschriftmandatBefreiungGerichtsvollzieherkosten
            ) = field(
                default=None,
                metadata={
                    "name": "auswahl_sepaLastschriftmandat.befreiungGerichtsvollzieherkosten",
                    "type": "Element",
                },
            )
            bankverbindung: (
                None
                | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.AngabenBankverbindung.Bankverbindung
            ) = field(
                default=None,
                metadata={
                    "type": "Element",
                },
            )

            @dataclass(kw_only=True)
            class AuswahlSepaLastschriftmandatBefreiungGerichtsvollzieherkosten:
                sepa_lastschriftmandat: None | bool = field(
                    default=None,
                    metadata={
                        "name": "sepaLastschriftmandat",
                        "type": "Element",
                    },
                )
                befreiung_gerichtsvollzieherkosten_gemaess: None | str = field(
                    default=None,
                    metadata={
                        "name": "befreiungGerichtsvollzieherkostenGemaess",
                        "type": "Element",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )

            @dataclass(kw_only=True)
            class Bankverbindung:
                ref_kontoinhaber: TypeGdsRefRollennummer = field(
                    metadata={
                        "name": "ref.kontoinhaber",
                        "type": "Element",
                        "required": True,
                    }
                )
                ref_bankverbindung: TypeGdsRefBankverbindung = field(
                    metadata={
                        "name": "ref.bankverbindung",
                        "type": "Element",
                        "required": True,
                    }
                )

        @dataclass(kw_only=True)
        class Vollstreckungstitel(TypeZvstrVollstreckungstitel):
            zuzueglich_zustellungsnachweis: None | bool = field(
                default=None,
                metadata={
                    "name": "zuzueglichZustellungsnachweis",
                    "type": "Element",
                },
            )

        @dataclass(kw_only=True)
        class Forderungsaufstellung:
            forderungsaufstellung_angaben: list[
                TypeZvstrForderungsaufstellungVollstreckungsauftrag
            ] = field(
                default_factory=list,
                metadata={
                    "name": "forderungsaufstellung.angaben",
                    "type": "Element",
                    "min_occurs": 1,
                },
            )
            forderungsaufstellung_anzahl: int = field(
                metadata={
                    "name": "forderungsaufstellung.anzahl",
                    "type": "Element",
                    "required": True,
                }
            )

        @dataclass(kw_only=True)
        class Versicherung:
            """
            :ivar versicherung_753a_satz1_zpo:
            :ivar versicherung_754a_abs1_s1_nr4_zpo: Es wird gemäß §
                754a Absatz 1 Satz 1 Nummer 4 ZPO versichert, dass
                Ausfertigungen der als elektronische Dokumente
                übermittelten Vollstreckungsbescheide mit den jeweiligen
                Zustellungsnachweisen vorliegen und die Forderungen in
                Höhe des Vollstreckungsauftrags noch bestehen.
            :ivar versicherung_weitere:
            """

            versicherung_753a_satz1_zpo: None | bool = field(
                default=None,
                metadata={
                    "name": "versicherung.753aSatz1ZPO",
                    "type": "Element",
                },
            )
            versicherung_754a_abs1_s1_nr4_zpo: None | bool = field(
                default=None,
                metadata={
                    "name": "versicherung.754aAbs1S1Nr4ZPO",
                    "type": "Element",
                },
            )
            versicherung_weitere: list[str] = field(
                default_factory=list,
                metadata={
                    "name": "versicherung.weitere",
                    "type": "Element",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )

        @dataclass(kw_only=True)
        class Auftraege:
            """
            :ivar antrag_zustellung:
            :ivar guetliche_erledigung_802b_zpo:
            :ivar abnahme_vermoegensauskunft:
            :ivar erlass_haftbefehl: Für den Fall, dass ein Schuldner
                dem Termin zur Abgabe der Vermögensauskunft
                unentschuldigt fernbleibt oder sich ohne Grund weigert,
                die Vermögensauskunft zu erteilen, wird der
                Gerichtsvollzieher beauftragt, beim zuständigen
                Amtsgericht den Erlass eines Haftbefehls nach § 802g
                Absatz 1 ZPO zu beantragen.
            :ivar verhaftung_schuldner:
            :ivar vorpfaendung: Mit diesem Element kann die Zustellung
                der Benachrichtigung über eine bevorstehende Pfändung
                aller oder bestimmter Forderungen gemäß § 845 ZPO
                beauftragt werden.
            :ivar pfaendung_und_verwertung:
            :ivar aufenthaltsermittlung:
            :ivar einholung_drittauskuenfte: Einholung von Auskünften
                Dritter (§ 802l ZPO) über den Schuldner
            :ivar weitere_auftraege:
            """

            antrag_zustellung: (
                None
                | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.AntragZustellung
            ) = field(
                default=None,
                metadata={
                    "name": "antrag.zustellung",
                    "type": "Element",
                },
            )
            guetliche_erledigung_802b_zpo: (
                None
                | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.GuetlicheErledigung802BZpo
            ) = field(
                default=None,
                metadata={
                    "name": "guetlicheErledigung.802bZPO",
                    "type": "Element",
                },
            )
            abnahme_vermoegensauskunft: list[
                NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.AbnahmeVermoegensauskunft
            ] = field(
                default_factory=list,
                metadata={
                    "name": "abnahmeVermoegensauskunft",
                    "type": "Element",
                },
            )
            erlass_haftbefehl: list[
                NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.ErlassHaftbefehl
            ] = field(
                default_factory=list,
                metadata={
                    "name": "erlassHaftbefehl",
                    "type": "Element",
                },
            )
            verhaftung_schuldner: list[
                NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.VerhaftungSchuldner
            ] = field(
                default_factory=list,
                metadata={
                    "name": "verhaftung.schuldner",
                    "type": "Element",
                },
            )
            vorpfaendung: (
                None
                | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.Vorpfaendung
            ) = field(
                default=None,
                metadata={
                    "type": "Element",
                },
            )
            pfaendung_und_verwertung: (
                None
                | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.PfaendungUndVerwertung
            ) = field(
                default=None,
                metadata={
                    "name": "pfaendungUndVerwertung",
                    "type": "Element",
                },
            )
            aufenthaltsermittlung: list[
                NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.Aufenthaltsermittlung
            ] = field(
                default_factory=list,
                metadata={
                    "type": "Element",
                },
            )
            einholung_drittauskuenfte: list[
                NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.EinholungDrittauskuenfte
            ] = field(
                default_factory=list,
                metadata={
                    "name": "einholungDrittauskuenfte",
                    "type": "Element",
                },
            )
            weitere_auftraege: list[str] = field(
                default_factory=list,
                metadata={
                    "name": "weitereAuftraege",
                    "type": "Element",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )

            @dataclass(kw_only=True)
            class AntragZustellung:
                """
                :ivar zustellung_aller_titel: sämtlicher beigefügter
                    Vollstreckungstitel
                :ivar zustellung_einzeltitel:
                :ivar zustellung_vorpfaendungsbenachrichtigung:
                :ivar zustellung_sonstiges:
                """

                zustellung_aller_titel: None | bool = field(
                    default=None,
                    metadata={
                        "name": "zustellung.allerTitel",
                        "type": "Element",
                    },
                )
                zustellung_einzeltitel: None | TypeZvstrRefTitelnummer = field(
                    default=None,
                    metadata={
                        "name": "zustellung.einzeltitel",
                        "type": "Element",
                    },
                )
                zustellung_vorpfaendungsbenachrichtigung: None | bool = field(
                    default=None,
                    metadata={
                        "name": "zustellung.vorpfaendungsbenachrichtigung",
                        "type": "Element",
                    },
                )
                zustellung_sonstiges: list[str] = field(
                    default_factory=list,
                    metadata={
                        "name": "zustellung.sonstiges",
                        "type": "Element",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )

            @dataclass(kw_only=True)
            class GuetlicheErledigung802BZpo:
                beschraenkung_auf_guetliche_erledigung: None | bool = field(
                    default=None,
                    metadata={
                        "name": "beschraenkungAufGuetlicheErledigung",
                        "type": "Element",
                    },
                )
                zahlungsvereinbarung: (
                    None
                    | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.GuetlicheErledigung802BZpo.Zahlungsvereinbarung
                ) = field(
                    default=None,
                    metadata={
                        "type": "Element",
                    },
                )
                sonstige_weisungen: list[str] = field(
                    default_factory=list,
                    metadata={
                        "name": "sonstigeWeisungen",
                        "type": "Element",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )

                @dataclass(kw_only=True)
                class Zahlungsvereinbarung:
                    auswahl_einverstaendnis: NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.GuetlicheErledigung802BZpo.Zahlungsvereinbarung.AuswahlEinverstaendnis = field(
                        metadata={
                            "type": "Element",
                            "required": True,
                        }
                    )

                    @dataclass(kw_only=True)
                    class AuswahlEinverstaendnis:
                        kein_einverstaendnis: None | bool = field(
                            default=None,
                            metadata={
                                "name": "keinEinverstaendnis",
                                "type": "Element",
                            },
                        )
                        einverstaendnis_wie_folgt: (
                            None
                            | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.GuetlicheErledigung802BZpo.Zahlungsvereinbarung.AuswahlEinverstaendnis.EinverstaendnisWieFolgt
                        ) = field(
                            default=None,
                            metadata={
                                "name": "einverstaendnisWieFolgt",
                                "type": "Element",
                            },
                        )

                        @dataclass(kw_only=True)
                        class EinverstaendnisWieFolgt:
                            zahlungsfrist: None | str = field(
                                default=None,
                                metadata={
                                    "type": "Element",
                                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                                },
                            )
                            teilbetraege: (
                                None
                                | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.GuetlicheErledigung802BZpo.Zahlungsvereinbarung.AuswahlEinverstaendnis.EinverstaendnisWieFolgt.Teilbetraege
                            ) = field(
                                default=None,
                                metadata={
                                    "type": "Element",
                                },
                            )
                            abweichen_nach_ermessen: None | bool = field(
                                default=None,
                                metadata={
                                    "name": "abweichenNachErmessen",
                                    "type": "Element",
                                },
                            )

                            @dataclass(kw_only=True)
                            class Teilbetraege:
                                mindest_ratenhoehe: None | Decimal = field(
                                    default=None,
                                    metadata={
                                        "name": "mindestRatenhoehe",
                                        "type": "Element",
                                    },
                                )
                                auswahl_turnus: NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.GuetlicheErledigung802BZpo.Zahlungsvereinbarung.AuswahlEinverstaendnis.EinverstaendnisWieFolgt.Teilbetraege.AuswahlTurnus = field(
                                    metadata={
                                        "type": "Element",
                                        "required": True,
                                    }
                                )

                                @dataclass(kw_only=True)
                                class AuswahlTurnus:
                                    monatlich: None | bool = field(
                                        default=None,
                                        metadata={
                                            "type": "Element",
                                        },
                                    )
                                    sonstiger: None | str = field(
                                        default=None,
                                        metadata={
                                            "type": "Element",
                                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                                        },
                                    )

            @dataclass(kw_only=True)
            class AbnahmeVermoegensauskunft:
                ref_schuldner: TypeGdsRefRollennummer = field(
                    metadata={
                        "name": "ref.schuldner",
                        "type": "Element",
                        "required": True,
                    }
                )
                auswahl_vermoegensauskunft: NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.AbnahmeVermoegensauskunft.AuswahlVermoegensauskunft = field(
                    metadata={
                        "type": "Element",
                        "required": True,
                    }
                )
                auswahl_ohne_oder_nach_pfaendungsversuch: (
                    None
                    | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.AbnahmeVermoegensauskunft.AuswahlOhneOderNachPfaendungsversuch
                ) = field(
                    default=None,
                    metadata={
                        "name": "auswahl_ohneOderNachPfaendungsversuch",
                        "type": "Element",
                    },
                )
                verzicht_mitteilung_terminsbestimmung: None | bool = field(
                    default=None,
                    metadata={
                        "name": "verzicht.mitteilungTerminsbestimmung",
                        "type": "Element",
                    },
                )
                teilnahme_abnahme_vermoegensauskunft: None | bool = field(
                    default=None,
                    metadata={
                        "name": "teilnahme.abnahmeVermoegensauskunft",
                        "type": "Element",
                    },
                )
                sonstiges: list[str] = field(
                    default_factory=list,
                    metadata={
                        "type": "Element",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )

                @dataclass(kw_only=True)
                class AuswahlVermoegensauskunft:
                    auskunft_802c_zpo: None | bool = field(
                        default=None,
                        metadata={
                            "name": "auskunft.802cZPO",
                            "type": "Element",
                        },
                    )
                    weitere_auskunft_802d_zpo: (
                        None
                        | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.AbnahmeVermoegensauskunft.AuswahlVermoegensauskunft.WeitereAuskunft802DZpo
                    ) = field(
                        default=None,
                        metadata={
                            "name": "weitereAuskunft.802dZPO",
                            "type": "Element",
                        },
                    )

                    @dataclass(kw_only=True)
                    class WeitereAuskunft802DZpo:
                        gruende: str = field(
                            metadata={
                                "type": "Element",
                                "required": True,
                                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                            }
                        )
                        glaubhaftmachung: str = field(
                            metadata={
                                "type": "Element",
                                "required": True,
                                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                            }
                        )

                @dataclass(kw_only=True)
                class AuswahlOhneOderNachPfaendungsversuch:
                    ohne_vorherigen_pfaendungsversuch: None | bool = field(
                        default=None,
                        metadata={
                            "name": "ohneVorherigenPfaendungsversuch",
                            "type": "Element",
                        },
                    )
                    nach_vorherigem_pfaendungsversuch: (
                        None
                        | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.AbnahmeVermoegensauskunft.AuswahlOhneOderNachPfaendungsversuch.NachVorherigemPfaendungsversuch
                    ) = field(
                        default=None,
                        metadata={
                            "name": "nachVorherigemPfaendungsversuch",
                            "type": "Element",
                        },
                    )

                    @dataclass(kw_only=True)
                    class NachVorherigemPfaendungsversuch:
                        nach_vorherigem_pfaendungsversuch: bool = field(
                            init=False,
                            default=True,
                            metadata={
                                "name": "nachVorherigemPfaendungsversuch",
                                "type": "Element",
                                "required": True,
                            },
                        )
                        schuldner_wiederholt_nicht_angetroffen: (
                            None
                            | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.AbnahmeVermoegensauskunft.AuswahlOhneOderNachPfaendungsversuch.NachVorherigemPfaendungsversuch.SchuldnerWiederholtNichtAngetroffen
                        ) = field(
                            default=None,
                            metadata={
                                "name": "schuldnerWiederholtNichtAngetroffen",
                                "type": "Element",
                            },
                        )

                        @dataclass(kw_only=True)
                        class SchuldnerWiederholtNichtAngetroffen:
                            auswahl_abnahme_vermoegensauskunft_oder_ruecksendung_vollstreckungsunterlagen: (
                                None
                                | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.AbnahmeVermoegensauskunft.AuswahlOhneOderNachPfaendungsversuch.NachVorherigemPfaendungsversuch.SchuldnerWiederholtNichtAngetroffen.AuswahlAbnahmeVermoegensauskunftOderRuecksendungVollstreckungsunterlagen
                            ) = field(
                                default=None,
                                metadata={
                                    "name": "auswahl_abnahmeVermoegensauskunftOderRuecksendungVollstreckungsunterlagen",
                                    "type": "Element",
                                },
                            )
                            sonstiges: list[str] = field(
                                default_factory=list,
                                metadata={
                                    "type": "Element",
                                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                                },
                            )

                            @dataclass(kw_only=True)
                            class AuswahlAbnahmeVermoegensauskunftOderRuecksendungVollstreckungsunterlagen:
                                abnahme_vermoegensauskunft: None | bool = (
                                    field(
                                        default=None,
                                        metadata={
                                            "name": "abnahmeVermoegensauskunft",
                                            "type": "Element",
                                        },
                                    )
                                )
                                ruecksendung_vollstreckungsunterlagen: (
                                    None | bool
                                ) = field(
                                    default=None,
                                    metadata={
                                        "name": "ruecksendungVollstreckungsunterlagen",
                                        "type": "Element",
                                    },
                                )

            @dataclass(kw_only=True)
            class ErlassHaftbefehl:
                """
                :ivar ref_schuldner: In diesem Element kann angegeben
                    werden, für welchen Schuldner der Erlass eines
                    Haftbefehls beantragt wird.
                :ivar auswahl_weiterleitung: In diesem Element wird
                    mitgeteilt, an wen das zuständige Amtsgericht den
                    Haftbefehl nach Erlass übersenden soll.
                """

                ref_schuldner: TypeGdsRefRollennummer = field(
                    metadata={
                        "name": "ref.schuldner",
                        "type": "Element",
                        "required": True,
                    }
                )
                auswahl_weiterleitung: NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.ErlassHaftbefehl.AuswahlWeiterleitung = field(
                    metadata={
                        "type": "Element",
                        "required": True,
                    }
                )

                @dataclass(kw_only=True)
                class AuswahlWeiterleitung:
                    weiterleitung_an_glauebiger: None | bool = field(
                        default=None,
                        metadata={
                            "name": "weiterleitungAnGlauebiger",
                            "type": "Element",
                        },
                    )
                    weiterleitung_an_bevollmaechtigten: None | bool = field(
                        default=None,
                        metadata={
                            "name": "weiterleitungAnBevollmaechtigten",
                            "type": "Element",
                        },
                    )
                    weiterleitung_an_zustaendigen_gv: None | bool = field(
                        default=None,
                        metadata={
                            "name": "weiterleitungAnZustaendigenGV",
                            "type": "Element",
                        },
                    )

            @dataclass(kw_only=True)
            class VerhaftungSchuldner:
                ref_schuldner: TypeGdsRefRollennummer = field(
                    metadata={
                        "name": "ref.schuldner",
                        "type": "Element",
                        "required": True,
                    }
                )
                haftbefehl_amtsgericht: CodeGdsGerichteTyp3 = field(
                    metadata={
                        "name": "haftbefehl.amtsgericht",
                        "type": "Element",
                        "required": True,
                    }
                )
                haftbefehl_datum_des_haftbefehls: XmlDate = field(
                    metadata={
                        "name": "haftbefehl.datumDesHaftbefehls",
                        "type": "Element",
                        "required": True,
                    }
                )
                geschaeftszeichen_des_haftbefehls: str = field(
                    metadata={
                        "name": "geschaeftszeichenDesHaftbefehls",
                        "type": "Element",
                        "required": True,
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    }
                )

            @dataclass(kw_only=True)
            class Vorpfaendung:
                bekannte_pfaendbare_forderung: (
                    None
                    | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.Vorpfaendung.BekanntePfaendbareForderung
                ) = field(
                    default=None,
                    metadata={
                        "name": "bekanntePfaendbareForderung",
                        "type": "Element",
                    },
                )
                folgende_forderungen: None | str = field(
                    default=None,
                    metadata={
                        "name": "folgendeForderungen",
                        "type": "Element",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )

                @dataclass(kw_only=True)
                class BekanntePfaendbareForderung:
                    bekannte_pfaendbare_forderungen: bool = field(
                        init=False,
                        default=True,
                        metadata={
                            "name": "bekanntePfaendbareForderungen",
                            "type": "Element",
                            "required": True,
                        },
                    )
                    ausnahme_folgender_forderungen: None | str = field(
                        default=None,
                        metadata={
                            "name": "ausnahmeFolgenderForderungen",
                            "type": "Element",
                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                        },
                    )

            @dataclass(kw_only=True)
            class PfaendungUndVerwertung:
                """
                :ivar durchfuehrung_sachpfaendung:
                :ivar pfaendung_von_wertpapieren: Es soll eine Pfändung
                    von Forderungen aus Wechseln und anderen Papieren,
                    die durch Indossament übertragen werden können,
                    durchgeführt werden.
                :ivar keine_fruchtlosigkeitsbescheinigung: Mit der
                    Erteilung einer Fruchtlosigkeitsbescheinigung nach §
                    32 GVGA besteht kein Einverständnis.
                :ivar pfaendbare_gegenstaende_im_vermoegensverzeichnis:
                    Der Pfändungsauftrag steht unter der Bedingung, dass
                    sich aus dem Vermögensverzeichnis pfändbare
                    Gegenstände ergeben.
                :ivar sonstiges:
                """

                durchfuehrung_sachpfaendung: (
                    None
                    | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.PfaendungUndVerwertung.DurchfuehrungSachpfaendung
                ) = field(
                    default=None,
                    metadata={
                        "name": "durchfuehrungSachpfaendung",
                        "type": "Element",
                    },
                )
                pfaendung_von_wertpapieren: None | bool = field(
                    default=None,
                    metadata={
                        "name": "pfaendungVonWertpapieren",
                        "type": "Element",
                    },
                )
                keine_fruchtlosigkeitsbescheinigung: None | bool = field(
                    default=None,
                    metadata={
                        "name": "keineFruchtlosigkeitsbescheinigung",
                        "type": "Element",
                    },
                )
                pfaendbare_gegenstaende_im_vermoegensverzeichnis: (
                    None | bool
                ) = field(
                    default=None,
                    metadata={
                        "name": "pfaendbareGegenstaendeImVermoegensverzeichnis",
                        "type": "Element",
                    },
                )
                sonstiges: list[str] = field(
                    default_factory=list,
                    metadata={
                        "type": "Element",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )

                @dataclass(kw_only=True)
                class DurchfuehrungSachpfaendung:
                    durchfuehrung_sachpfaendung: bool = field(
                        init=False,
                        default=True,
                        metadata={
                            "name": "durchfuehrungSachpfaendung",
                            "type": "Element",
                            "required": True,
                        },
                    )
                    auswahl_einschliesslich_oder_beschraenkt_auf: (
                        None
                        | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.PfaendungUndVerwertung.DurchfuehrungSachpfaendung.AuswahlEinschliesslichOderBeschraenktAuf
                    ) = field(
                        default=None,
                        metadata={
                            "name": "auswahl_einschliesslichOderBeschraenktAuf",
                            "type": "Element",
                        },
                    )
                    taschenpfaendungen: None | bool = field(
                        default=None,
                        metadata={
                            "type": "Element",
                        },
                    )
                    kassenpfaendungen: None | bool = field(
                        default=None,
                        metadata={
                            "type": "Element",
                        },
                    )
                    sonstige_pfaendungen: list[str] = field(
                        default_factory=list,
                        metadata={
                            "name": "sonstigePfaendungen",
                            "type": "Element",
                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                        },
                    )

                    @dataclass(kw_only=True)
                    class AuswahlEinschliesslichOderBeschraenktAuf:
                        einschliesslich: None | bool = field(
                            default=None,
                            metadata={
                                "type": "Element",
                            },
                        )
                        beschraenkt_auf: None | bool = field(
                            default=None,
                            metadata={
                                "name": "beschraenktAuf",
                                "type": "Element",
                            },
                        )

            @dataclass(kw_only=True)
            class Aufenthaltsermittlung:
                ref_schuldner: TypeGdsRefRollennummer = field(
                    metadata={
                        "name": "ref.schuldner",
                        "type": "Element",
                        "required": True,
                    }
                )
                ermittlung_aufenthaltsort_schuldner: (
                    None
                    | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.Aufenthaltsermittlung.ErmittlungAufenthaltsortSchuldner
                ) = field(
                    default=None,
                    metadata={
                        "name": "ermittlung.aufenthaltsortSchuldner",
                        "type": "Element",
                    },
                )
                ermittlung_nach755_absatz1_zpo: (
                    None
                    | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.Aufenthaltsermittlung.ErmittlungNach755Absatz1Zpo
                ) = field(
                    default=None,
                    metadata={
                        "name": "ermittlung.nach755Absatz1ZPO",
                        "type": "Element",
                    },
                )
                ermittlung_nach755_absatz2_zpo: (
                    None
                    | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.Aufenthaltsermittlung.ErmittlungNach755Absatz2Zpo
                ) = field(
                    default=None,
                    metadata={
                        "name": "ermittlung.nach755Absatz2ZPO",
                        "type": "Element",
                    },
                )
                sonstiges: list[str] = field(
                    default_factory=list,
                    metadata={
                        "type": "Element",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )

                @dataclass(kw_only=True)
                class ErmittlungAufenthaltsortSchuldner:
                    """
                    :ivar keine_zustellungsfaehige_anschrift: Ermittlung
                        des Aufenthaltsorts des Schuldners für den Fall,
                        dass sich im Verfahren herausstellt, dass keine
                        zustellungsfähige Anschrift des Schuldners
                        vorliegt.
                    """

                    keine_zustellungsfaehige_anschrift: bool = field(
                        init=False,
                        default=True,
                        metadata={
                            "name": "keineZustellungsfaehigeAnschrift",
                            "type": "Element",
                            "required": True,
                        },
                    )

                @dataclass(kw_only=True)
                class ErmittlungNach755Absatz1Zpo:
                    """
                    :ivar nachfrage_meldebehoerde: Ermittlung nach § 755
                        Absatz 1 ZPO der gegenwärtigen Anschriften sowie
                        der Angaben zur Haupt- und Nebenwohnung des
                        Schuldners durch Nachfrage bei der Meldebehörde
                    :ivar einsicht_in_register: Ermittlung nach § 755
                        Absatz 1 ZPO der gegenwärtigen Anschriften, des
                        Ortes der Hauptniederlassung oder des Sitzes des
                        Schuldners durch Einsicht in das Handels-,
                        Genossenschafts-, Partnerschafts-, Unternehmens-
                        oder Vereinsregister
                    :ivar auskunft_durch_zustaendige_behoerden:
                        Ermittlung nach § 755 Absatz 1 ZPO der
                        gegenwärtigen Anschriften, des Ortes der
                        Hauptniederlassung oder des Sitzes des
                        Schuldners durch Einholung einer Auskunft bei
                        den nach Landesrecht für die Durchführung der
                        Aufgaben nach § 14 Absatz 1 GewO zuständigen
                        Behörden
                    """

                    nachfrage_meldebehoerde: None | bool = field(
                        default=None,
                        metadata={
                            "name": "nachfrageMeldebehoerde",
                            "type": "Element",
                        },
                    )
                    einsicht_in_register: None | bool = field(
                        default=None,
                        metadata={
                            "name": "einsichtInRegister",
                            "type": "Element",
                        },
                    )
                    auskunft_durch_zustaendige_behoerden: None | bool = field(
                        default=None,
                        metadata={
                            "name": "auskunftDurchZustaendigeBehoerden",
                            "type": "Element",
                        },
                    )

                @dataclass(kw_only=True)
                class ErmittlungNach755Absatz2Zpo:
                    """
                    :ivar auslaenderzentralregister: Ermittlung nach §
                        755 Absatz 2 ZPO des Aufenthaltsorts durch
                        Nachfragen beim Ausländerzentralregister und bei
                        der aktenführenden Ausländerbehörde
                    :ivar
                        anschrift_rentenversicherung_oder_versorgungseinrichtung:
                        Ermittlung nach § 755 Absatz 2 ZPO der bekannten
                        derzeitigen Anschrift sowie des derzeitigen oder
                        zukünftigen Aufenthaltsorts des Schuldners bei
                    :ivar halterdaten_kraftfahrtbundesamt: Ermittlung
                        nach § 755 Absatz 2 ZPO der Halterdaten nach §
                        33 Absatz 1 Satz 1 Nummer 2 StVG des Schuldners
                        beim Kraftfahrt-Bundesamt
                    """

                    auslaenderzentralregister: None | bool = field(
                        default=None,
                        metadata={
                            "type": "Element",
                        },
                    )
                    anschrift_rentenversicherung_oder_versorgungseinrichtung: (
                        None | TypeZvstrErmittlungSchuldneranschrift
                    ) = field(
                        default=None,
                        metadata={
                            "name": "anschrift.rentenversicherungOderVersorgungseinrichtung",
                            "type": "Element",
                        },
                    )
                    halterdaten_kraftfahrtbundesamt: None | bool = field(
                        default=None,
                        metadata={
                            "name": "halterdaten.kraftfahrtbundesamt",
                            "type": "Element",
                        },
                    )

            @dataclass(kw_only=True)
            class EinholungDrittauskuenfte:
                ref_schuldner: TypeGdsRefRollennummer = field(
                    metadata={
                        "name": "ref.schuldner",
                        "type": "Element",
                        "required": True,
                    }
                )
                erhebung_rentenversicherung_versorgungseinrichtung: (
                    None | TypeZvstrErmittlungSchuldneranschrift
                ) = field(
                    default=None,
                    metadata={
                        "name": "erhebung.rentenversicherungVersorgungseinrichtung",
                        "type": "Element",
                    },
                )
                ersuchen_bundeszentralamt_steuern: None | bool = field(
                    default=None,
                    metadata={
                        "name": "ersuchen.bundeszentralamtSteuern",
                        "type": "Element",
                    },
                )
                erhebung_kraftfahrtbundesamt: None | bool = field(
                    default=None,
                    metadata={
                        "name": "erhebung.kraftfahrtbundesamt",
                        "type": "Element",
                    },
                )
                antrag_einholung_aktuelle_auskuenfte: (
                    None
                    | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.Auftraege.EinholungDrittauskuenfte.AntragEinholungAktuelleAuskuenfte
                ) = field(
                    default=None,
                    metadata={
                        "name": "antrag.einholungAktuelleAuskuenfte",
                        "type": "Element",
                    },
                )
                sonstiges: list[str] = field(
                    default_factory=list,
                    metadata={
                        "type": "Element",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )

                @dataclass(kw_only=True)
                class AntragEinholungAktuelleAuskuenfte:
                    aenderung_vermoegensverhaeltnisse_schuldner: str = field(
                        metadata={
                            "name": "aenderungVermoegensverhaeltnisse.schuldner",
                            "type": "Element",
                            "required": True,
                            "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                        }
                    )

        @dataclass(kw_only=True)
        class ReihenfolgeDerAuftraege:
            """
            :ivar reihenfolge_1: Hier kann der entsprechende
                Modulbuchstabe eingetragen werden.
            :ivar reihenfolge_2: Hier kann der entsprechende
                Modulbuchstabe eingetragen werden.
            :ivar reihenfolge_3: Hier kann der entsprechende
                Modulbuchstabe eingetragen werden.
            :ivar weitere_reihenfolge:
            """

            reihenfolge_1: str = field(
                metadata={
                    "name": "reihenfolge.1",
                    "type": "Element",
                    "required": True,
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                }
            )
            reihenfolge_2: None | str = field(
                default=None,
                metadata={
                    "name": "reihenfolge.2",
                    "type": "Element",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            reihenfolge_3: None | str = field(
                default=None,
                metadata={
                    "name": "reihenfolge.3",
                    "type": "Element",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )
            weitere_reihenfolge: list[str] = field(
                default_factory=list,
                metadata={
                    "name": "weitereReihenfolge",
                    "type": "Element",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )

        @dataclass(kw_only=True)
        class HinweiseVorgabenAnGerichtsvollzieher:
            """
            :ivar auswahl_uebersendung:
            :ivar nichtzustaendigkeit_weiterleitung: Im Fall der
                Nichtzuständigkeit wird um Weiterleitung des
                Vollstreckungsauftrags an den zuständigen
                Gerichtsvollzieher gebeten, wenn nicht bereits eine
                Weiterleitung von Amts wegen erfolgt.
            :ivar ruecksendung_vollstreckungsunterlagen_beschreibung:
            :ivar weitere_hinweise_und_vorgaben:
            """

            auswahl_uebersendung: (
                None
                | NachrichtZvstrVollstreckungsauftrag2600003.Fachdaten.HinweiseVorgabenAnGerichtsvollzieher.AuswahlUebersendung
            ) = field(
                default=None,
                metadata={
                    "type": "Element",
                },
            )
            nichtzustaendigkeit_weiterleitung: None | bool = field(
                default=None,
                metadata={
                    "name": "nichtzustaendigkeit.weiterleitung",
                    "type": "Element",
                },
            )
            ruecksendung_vollstreckungsunterlagen_beschreibung: None | str = (
                field(
                    default=None,
                    metadata={
                        "name": "ruecksendungVollstreckungsunterlagen.beschreibung",
                        "type": "Element",
                        "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                    },
                )
            )
            weitere_hinweise_und_vorgaben: list[str] = field(
                default_factory=list,
                metadata={
                    "name": "weitereHinweiseUndVorgaben",
                    "type": "Element",
                    "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
                },
            )

            @dataclass(kw_only=True)
            class AuswahlUebersendung:
                protokoll: None | bool = field(
                    default=None,
                    metadata={
                        "type": "Element",
                    },
                )
                gesamtprotokoll: None | bool = field(
                    default=None,
                    metadata={
                        "type": "Element",
                    },
                )
