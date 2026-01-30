from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from xjustiz.model_gen.xoev_code import Code

__NAMESPACE__ = "http://www.xjustiz.de"


class VstrAnredePartei(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"
    VALUE_004 = "004"
    VALUE_005 = "005"
    VALUE_006 = "006"
    VALUE_007 = "007"
    VALUE_008 = "008"
    VALUE_009 = "009"
    VALUE_010 = "010"
    VALUE_011 = "011"
    VALUE_012 = "012"


class VstrEintragungsgruendeGerichtsvollzieherVollstreckungsbehoerde(Enum):
    GL_UBIGERBEFRIEDIGUNG_AUSGESCHLOSSEN = (
        "Gläubigerbefriedigung ausgeschlossen"
    )
    GL_UBIGERBEFRIEDIGUNG_NICHT_NACHGEWIESEN = (
        "Gläubigerbefriedigung nicht nachgewiesen"
    )
    NICHTABGABE_DER_VERM_GENSAUSKUNFT = "Nichtabgabe der Vermögensauskunft"


class VstrEintragungsgruendeInsolvenzgericht(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"
    VALUE_004 = "004"
    VALUE_005 = "005"
    VALUE_006 = "006"
    VALUE_007 = "007"
    VALUE_008 = "008"


class VstrEntscheidungsinhaltSchuldnerwiderspruch(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"


class VstrGerichtsvollzieherDienstbezeichnung(Enum):
    VALUE_001 = "001"
    VALUE_002 = "002"
    VALUE_003 = "003"
    VALUE_004 = "004"
    VALUE_005 = "005"


class VstrKorrekturLoeschung(Enum):
    KORREKTUR = "Korrektur"
    KORREKTUR_IRRIGER_EINTRAG = "Korrektur irriger Eintrag"
    L_SCHUNG = "Löschung"
    L_SCHUNG_IRRIGER_EINTRAG = "Löschung irriger Eintrag"
    VORZEITIGE_ERSETZUNG_EINER_VERM_GENSAUSKUNFT = (
        "Vorzeitige Ersetzung einer Vermögensauskunft"
    )


class VstrSchuldnerverzeichnisLoeschungsgruende(Enum):
    KORREKTUR = "Korrektur"
    KORREKTUR_IRRIGER_EINTRAG = "Korrektur irriger Eintrag"
    L_SCHUNG = "Löschung"
    L_SCHUNG_DER_EINTRAGUNG_WEGEN_FRISTABLAUFS = (
        "Löschung der Eintragung wegen Fristablaufs"
    )
    L_SCHUNG_IRRIGER_EINTRAG = "Löschung irriger Eintrag"
    VORZEITIGE_L_SCHUNG_DER_EINTRAGUNG_IM_SCHULDNERVERZEICHNIS = (
        "vorzeitige Löschung der Eintragung im Schuldnerverzeichnis"
    )


class VstrVerarbeitungsergebnisSchuldnerverzeichnis(Enum):
    VALUE_001_EINTRAGUNG_ERFOLGT = "001 Eintragung erfolgt"
    VALUE_002_SONSTIGER_FEHLER = "002 Sonstiger Fehler"
    VALUE_003_VERFAHRENSNUMMER_NICHT_VORHANDEN = (
        "003 Verfahrensnummer nicht vorhanden"
    )
    VALUE_004_ELEMENT_KORREKTUR_LOESCHUNG_FEHLT = (
        "004 Element 'korrekturLoeschung' fehlt"
    )
    VALUE_005_VERFAHRENSNUMMER_FEHLT = "005 Verfahrensnummer fehlt"
    VALUE_006_FALSCHE_ART_DES_VERM_GENSVERZEICHNISSES = (
        "006 Falsche Art des Vermögensverzeichnisses"
    )
    VALUE_007_DATENSATZ_BEREITS_VORHANDEN = "007 Datensatz bereits vorhanden"
    VALUE_008_EINTRAGUNGSHEMMNIS_VORHANDEN = "008 Eintragungshemmnis vorhanden"
    VALUE_009_KEINE_KORREKTUR_L_SCHUNG = "009 keine Korrektur / Löschung"
    VALUE_010_EINGANG_ZUR_CKWEISUNG_SCHULDNERWIDERSPRUCH = (
        "010 Eingang Zurückweisung Schuldnerwiderspruch"
    )
    VALUE_020_AKTENZEICHEN_INKONSISTENT = "020 Aktenzeichen inkonsistent"
    VALUE_021_VERFAHRENSNUMMER_UNG_LTIG = "021 Verfahrensnummer ungültig"
    VALUE_022_FALSCHES_ZEN_VG_IN_VERFAHRENSNUMMER = (
        "022 Falsches ZenVG in Verfahrensnummer"
    )
    VALUE_023_XJUSTIZ_KODE_ZEN_VG_UNG_LTIG = "023 XJustiz Kode ZenVG ungültig"
    VALUE_024_EREIGNIS_UNG_LTIG = "024 Ereignis ungültig"
    VALUE_025_INSTANZDATEN_UNG_LTIG = "025 Instanzdaten ungültig"
    VALUE_026_ROLLENNUMMER_UNG_LTIG = "026 Rollennummer ungültig"
    VALUE_027_FALSCHES_SACHGEBIET = "027 Falsches Sachgebiet"
    VALUE_028_VORNAME_VORKOMMEN_UNG_LTIG = "028 Vorname, Vorkommen ungültig"
    VALUE_029_WEITERER_NAME_VORKOMMEN_UNG_LTIG = (
        "029 'weitererName', Vorkommen ungültig"
    )
    VALUE_030_RUFNAME_UNG_LTIG = "030 Rufname ungültig"
    VALUE_031_BEZEICHNUNG_ALT_VORKOMMEN_UNG_LTIG = (
        "031 'bezeichnung.alt', Vorkommen ungültig"
    )
    VALUE_032_VERFAHRENS_ZUSTELLANSCHRIFT_VORKOMMEN_UNG_LTIG = (
        "032 Verfahrens-/Zustellanschrift, Vorkommen ungültig"
    )
    VALUE_033_EINTRAGUNGSANORDNUNG_UNG_LTIG = (
        "033 Eintragungsanordnung ungültig"
    )
    VALUE_035_KORREKTUR_LOESCHUNG_UNG_LTIG = "035 Korrektur_Loeschung ungültig"
    VALUE_037_SITZ_VORKOMMEN_UNG_LTIG = "037 Sitz, Vorkommen ungültig"
    VALUE_038_HANDELND_UNTER_VORKOMMEN_UNG_LTIG = (
        "038 'handelndUnter', Vorkommen ungültig"
    )
    VALUE_039_VERM_GENSVERZEICHNIS_FEHLT = "039 Vermögensverzeichnis fehlt"
    VALUE_040_FALSCHER_DOKUMENTENTYP_IM_ANHANG = (
        "040 Falscher Dokumententyp im Anhang"
    )
    VALUE_041_MEHR_ALS_EIN_DOKUMENT_BERSANDT = (
        "041 Mehr als ein Dokument übersandt"
    )
    VALUE_042_ABSENDER_INSO_FALSCH = "042 Absender INSO falsch"
    VALUE_043_KEIN_AKTENZEICHEN_ANGEGEBEN = "043 Kein Aktenzeichen angegeben"
    VALUE_044_ANORDNUNGSBEH_RDE_FEHLENDE_FALSCHE_BERECHTIGUNG_EINLIEFERER = (
        "044 Anordnungsbehörde, fehlende / falsche Berechtigung Einlieferer"
    )
    VALUE_045_KEIN_NAME_ANGEGEBEN = "045 Kein Name angegeben"
    VALUE_046_UNG_LTIGE_ZEITZONE_DATUM = "046 Ungültige Zeitzone Datum"
    VALUE_047_REGISTEREINTRAGUNG_VORKOMMEN_UNG_LTIG = (
        "047 Registereintragung, Vorkommen ungültig"
    )
    VALUE_048_KORREKTUR_L_SCHUNG_WERT_UNG_LTIG = (
        "048 Korrektur / Löschung, Wert ungültig"
    )
    VALUE_049_KEINE_AUSREICHENDE_DATEN_BEREINSTIMMUNG = (
        "049 Keine ausreichende Datenübereinstimmung"
    )
    VALUE_501_EINTRAGUNG_ERFOLGT = "501 Eintragung erfolgt"
    VALUE_502_SONSTIGER_FEHLER = "502 Sonstiger Fehler"
    VALUE_503_SYNTAKTISCHER_FEHLER_IM_DATENSATZ = (
        "503 Syntaktischer Fehler im Datensatz"
    )
    VALUE_504_VERFAHRENSNUMMER_NICHT_VORHANDEN = (
        "504 Verfahrensnummer nicht vorhanden"
    )
    VALUE_505_KEINE_EINTRAGUNG_VOLLSTRECKUNGPORTAL_INTERNER_FEHLER = (
        "505 Keine Eintragung (Vollstreckungportal-interner Fehler)"
    )
    VALUE_506_KEINE_KORREKTUR_VOLLSTRECKUNGPORTAL_INTERNER_FEHLER = (
        "506 Keine Korrektur (Vollstreckungportal-interner Fehler)"
    )
    VALUE_507_KEINE_L_SCHUNG_VOLLSTRECKUNGPORTAL_INTERNER_FEHLER = (
        "507 Keine Löschung (Vollstreckungportal-interner Fehler)"
    )
    VALUE_508_AUTHENTISIERUNG_AUFRUFER_FEHLGESCHLAGEN = (
        "508 Authentisierung Aufrufer fehlgeschlagen"
    )
    VALUE_509_AUFRUFER_F_R_DIE_NUTZUNG_DES_WEB_SERVICE_NICHT_AUTORISIERT = (
        "509 Aufrufer für die Nutzung des Web-Service nicht autorisiert"
    )
    VALUE_510_PORTAL_EINLIEFERUNG_FACHDATEN_ABGESCHALTET = (
        "510 Portal: Einlieferung Fachdaten abgeschaltet"
    )


class VstrVermoegensverzeichnisArt(Enum):
    ERNEUTE_VERM_GENSAUSKUNFT = "Erneute Vermögensauskunft"
    NACHBESSERUNG_DER_VERM_GENSAUSKUNFT = "Nachbesserung der Vermögensauskunft"
    NEUE_VERM_GENSAUSKUNFT = "Neue Vermögensauskunft"


@dataclass(kw_only=True)
class CodeVstrAnredePartei(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.VSTR.Anrede.Partei"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:vstr.anrede.partei",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="1.0",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeVstrEintragungsgruendeGerichtsvollzieherVollstreckungsbehoerde(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.VSTR.Eintragungsgruende.Gerichtsvollzieher.Vollstreckungsbehoerde"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:vstr.eintragungsgruende.gerichtsvollzieher.vollstreckungsbehoerde",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="2.0",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeVstrEintragungsgruendeInsolvenzgericht(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.VSTR.Eintragungsgruende.Insolvenzgericht"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:vstr.eintragungsgruende.insolvenzgericht",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="2.1",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeVstrEntscheidungsinhaltSchuldnerwiderspruch(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.VSTR.Entscheidungsinhalt.Schuldnerwiderspruch"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:vstr.entscheidungsinhalt.schuldnerwiderspruch",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="2.0",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeVstrGerichtsvollzieherDienstbezeichnung(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.VSTR.Gerichtsvollzieher.Dienstbezeichnung"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:vstr.gerichtsvollzieher.dienstbezeichnung",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="2.0",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeVstrKorrekturLoeschung(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.VSTR.KorrekturLoeschung"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:vstr.korrektur-loeschung",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="2.1",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeVstrSchuldnerverzeichnisLoeschungsgruende(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.VSTR.Schuldnerverzeichnis.Loeschungsgruende"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:vstr.schuldnerverzeichnis.loeschungsgruende",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="2.1",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeVstrVerarbeitungsergebnisSchuldnerverzeichnis(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.VSTR.Verarbeitungsergebnis.Schuldnerverzeichnis"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:vstr.verarbeitungsergebnis.schuldnerverzeichnis",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="2.2",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class CodeVstrVermoegensverzeichnisArt(Code):
    """
    :ivar name: Mit diesem optionalen XML-Element kann die Beschreibung
        des Codes, wie in der jeweiligen Beschreibungsspalte der
        Codeliste vorgegeben, übermittelt werden.
    :ivar list_uri:
    :ivar list_version_id:
    """

    class Meta:
        name = "Code.VSTR.Vermoegensverzeichnis.Art"

    name: Any = field(
        init=False,
        default=None,
        metadata={
            "type": "Ignore",
        },
    )
    list_uri: str = field(
        init=False,
        default="urn:xoev-de:xjustiz:codeliste:vstr.vermoegensverzeichnis.art",
        metadata={
            "name": "listURI",
            "type": "Attribute",
        },
    )
    list_version_id: str = field(
        init=False,
        default="2.1",
        metadata={
            "name": "listVersionID",
            "type": "Attribute",
        },
    )
