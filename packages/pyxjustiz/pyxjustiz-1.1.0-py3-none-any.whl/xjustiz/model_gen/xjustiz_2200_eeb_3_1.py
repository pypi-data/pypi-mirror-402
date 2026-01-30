from __future__ import annotations

from dataclasses import dataclass, field

from xsdata.models.datatype import XmlDate

from xjustiz.model_gen.xjustiz_0000_grunddatensatz_3_6 import (
    TypeGdsNachrichtenkopf,
)
from xjustiz.model_gen.xjustiz_2210_cl_eeb_3_1 import CodeEebStoerungsId

__NAMESPACE__ = "http://www.xjustiz.de"


@dataclass(kw_only=True)
class TypeEebZuruecklaufend:
    """
    :ivar empfangsbestaetigung:
    :ivar stoerungsmeldung:
    :ivar zustellungsempfaenger_abweichend: Sollte ein legitimierter
        Vertreter das eEB zurückleiten, ist hier der Wert 'true'
        einzutragen.
    """

    class Meta:
        name = "Type.EEB.Zuruecklaufend"

    empfangsbestaetigung: None | XmlDate = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    stoerungsmeldung: None | TypeEebZuruecklaufend.Stoerungsmeldung = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )
    zustellungsempfaenger_abweichend: None | bool = field(
        default=None,
        metadata={
            "name": "zustellungsempfaenger.abweichend",
            "type": "Element",
            "namespace": "http://www.xjustiz.de",
        },
    )

    @dataclass(kw_only=True)
    class Stoerungsmeldung:
        """
        :ivar stoerungs_id:
        :ivar stoerungs_grund: Freitextfeld zur Erläuterung der Störung.
        """

        stoerungs_id: CodeEebStoerungsId = field(
            metadata={
                "name": "stoerungsID",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "required": True,
            }
        )
        stoerungs_grund: None | str = field(
            default=None,
            metadata={
                "name": "stoerungsGrund",
                "type": "Element",
                "namespace": "http://www.xjustiz.de",
                "pattern": r"([\t-\n]|\r|[ -~]|[\xa0-¬]|[®-ž]|[Ƈ-ƈ]|Ə|Ɨ|[Ơ-ơ]|[Ư-ư]|Ʒ|[Ǎ-ǜ]|[Ǟ-ǟ]|[Ǣ-ǰ]|[Ǵ-ǵ]|[Ǹ-ǿ]|[Ȓ-ȓ]|[Ș-ț]|[Ȟ-ȟ]|[ȧ-ȳ]|ə|ɨ|ʒ|[ʹ-ʺ]|[ʾ-ʿ]|ˈ|ˌ|[Ḃ-ḃ]|[Ḇ-ḇ]|[Ḋ-ḑ]|ḗ|[Ḝ-ḫ]|[ḯ-ḷ]|[Ḻ-ḻ]|[Ṁ-ṉ]|[Ṓ-ṛ]|[Ṟ-ṣ]|[Ṫ-ṯ]|[Ẁ-ẇ]|[Ẍ-ẗ]|ẞ|[Ạ-ỹ]|’|‡|€|A̋|C(̀|̄|̆|̈|̕|̣|̦|̨̆)|D̂|F(̀|̄)|G̀|H(̄|̦|̱)|J(́|̌)|K(̀|̂|̄|̇|̕|̛|̦|͟H|͟h)|L(̂|̥|̥̄|̦)|M(̀|̂|̆|̐)|N(̂|̄|̆|̦)|P(̀|̄|̕|̣)|R(̆|̥|̥̄)|S(̀|̄|̛̄|̱)|T(̀|̄|̈|̕|̛)|U̇|Z(̀|̄|̆|̈|̧)|a̋|c(̀|̄|̆|̈|̕|̣|̦|̨̆)|d̂|f(̀|̄)|g̀|h(̄|̦)|j́|k(̀|̂|̄|̇|̕|̛|̦|͟h)|l(̂|̥|̥̄|̦)|m(̀|̂|̆|̐)|n(̂|̄|̆|̦)|p(̀|̄|̕|̣)|r(̆|̥|̥̄)|s(̀|̄|̛̄|̱)|t(̀|̄|̕|̛)|u̇|z(̀|̄|̆|̈|̧)|Ç̆|Û̄|ç̆|û̄|ÿ́|Č(̕|̣)|č(̕|̣)|ē̍|Ī́|ī́|ō̍|Ž(̦|̧)|ž(̦|̧)|Ḳ̄|ḳ̄|Ṣ̄|ṣ̄|Ṭ̄|ṭ̄|Ạ̈|ạ̈|Ọ̈|ọ̈|Ụ(̄|̈)|ụ(̄|̈))*",
            },
        )


@dataclass(kw_only=True)
class NachrichtEebZuruecklaufend2200007:
    class Meta:
        name = "nachricht.eeb.zuruecklaufend.2200007"
        namespace = "http://www.xjustiz.de"

    nachrichtenkopf: TypeGdsNachrichtenkopf = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    fachdaten: TypeEebZuruecklaufend = field(
        metadata={
            "type": "Element",
            "required": True,
        }
    )
