# generated from JSON Schema


from __future__ import annotations

from datetime import date as date_aliased
from typing import Annotated, Any, ClassVar, Literal
from uuid import UUID

from pydantic import AnyUrl, Field, RootModel

from ..base import BaseFeature
from . import definitions


class Model(RootModel[Any]):
    root: Annotated[
        Any,
        Field(
            description="Applikationsschema für die Modellierung von Leitungsnetzen",
            json_schema_extra={
                "full_name": "XTrasse",
                "prefix": "xtrasse",
                "full_version": "2.0",
                "namespace_uri": "http://www.xtrasse.de/2.0",
            },
        ),
    ]


class BRABaugrubeTyp(RootModel[Literal["1000", "2000"]]):
    root: Annotated[
        Literal["1000", "2000"],
        Field(
            description="Auswahl von Start- und Zielgrube.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Startgrube",
                        "alias": "Startgrube",
                        "description": "Startgrube für alternative Verlegemethoden",
                    },
                    "2000": {
                        "name": "Zielgrube",
                        "alias": "Zielgrube",
                        "description": "Zielgrube für alternative Verlegemethoden",
                    },
                }
            },
        ),
    ]


class IGPVersion(BaseFeature):
    """Versionierung der Variante des Plans"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "DataType"
    versionName: Annotated[
        str,
        Field(
            description="Name der Version",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    datum: Annotated[
        date_aliased,
        Field(
            description="Datum der Version",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "1",
            },
        ),
    ]


class IGPVorgaengerVersion(BaseFeature):
    """Referenz auf die voherige Version des Plans"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "DataType"
    refUuid: Annotated[
        str | None,
        Field(
            description="UUID des vorherigen Plans",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    versionName: Annotated[
        str | None,
        Field(
            description="Name des vorherigen Plans",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class IPEinAusspeisung(BaseFeature):
    """Angaben zur Ein- oder Ausspeisung von Gas in Leitungsnetzen"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "DataType"
    einspeiseleistung: Annotated[
        definitions.GenericMeasure | None,
        Field(
            description="Einspeiseleistung in MWh/hth",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "MW",
            },
        ),
    ] = None
    einspeisemengeProJahr: Annotated[
        definitions.GenericMeasure | None,
        Field(
            description="Einspeisemenge pro Jahr in MWhth",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "MWh",
            },
        ),
    ] = None
    ausspeiseleistung: Annotated[
        definitions.GenericMeasure | None,
        Field(
            description="Ausspeiseleistung in",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "MW",
            },
        ),
    ] = None
    ausspeisemengeProJahr: Annotated[
        definitions.GenericMeasure | None,
        Field(
            description="Ausspeiseleistung pro Jahr in MWhth",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "MWh",
            },
        ),
    ] = None


class ISAAnsprechpartner(BaseFeature):
    """Ansprechpartner für einen gelieferten XTrasse Datensatz"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "DataType"
    anrede: Annotated[
        str | None,
        Field(
            description="Anrede",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    vorUndZuname: Annotated[
        str,
        Field(
            description="Vor- und Zuname",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    telefon: Annotated[
        str,
        Field(
            description="Telefonnummer",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    eMail: Annotated[
        str,
        Field(
            description="Email Adresse",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]


class PFSArbeitsstreifenData(BaseFeature):
    """Temporäre Einschränkungen und Eingriffe entlang der Trasse"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "DataType"
    arbeitsstreifenFlur: Annotated[
        definitions.Length | None,
        Field(
            description="Zur Bauausführung wird ein Regelarbeitsstreifen auf freier Feldflur in Anspruch genommen, Gesamtbreite in m (zur Darstellung im Web-GIS kann auch die Klasse PFS_Baustelle genutzt werden)",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    arbeitsstreifenWald: Annotated[
        definitions.Length | None,
        Field(
            description="Im Wald wird ein schmalerer Arbeitsstreifen beansprucht, Gesamtbreite in m (zur Darstellung im Web-GIS kann auch die Klasse PFS_Baustelle genutzt werden)",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    arbeitsstreifenWiese: Annotated[
        definitions.Length | None,
        Field(
            description="Auf feuchten Wiesen wird ein schmalerer Arbeitsstreifen beansprucht, Gesamtbreite in m (zur Darstellung im Web-GIS kann auch die Klasse PFS_Baustelle genutzt werden)",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None


class PFSErdkabel(BaseFeature):
    """Daten zu Erdkabeln einer Hochspannungsleitung"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "DataType"
    regelueberdeckung: Annotated[
        definitions.Length | None,
        Field(
            description="Mindestabstand zwischen Oberkante des Weges und Oberkante des Rohres in m.\r\n(gml:LengthType: uom=“m“ oder uom=“urn:adv:uom:m“)",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    aussendurchmesser: Annotated[
        definitions.Length | None,
        Field(
            description="Aussendurchmesser (DA) der Kabel in m",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    anzahl: Annotated[
        int | None,
        Field(
            description="Anzahl der Erdkabel",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    leitungszoneBreite: Annotated[
        definitions.Length | None,
        Field(
            description="Gesamtbreite des Streifens der Erdkabel in m",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None


class PFSRohrgraben(BaseFeature):
    """Dimension des Rohrgrabens bei offener Bauweise"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "DataType"
    breiteKrone: Annotated[
        definitions.Length | None,
        Field(
            description="Ungefähre Breite der Grabenkrone in m",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    breiteSohle: Annotated[
        definitions.Length | None,
        Field(
            description="Ungefähre Breite der Grabensohle in m",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    tiefe: Annotated[
        definitions.Length | None,
        Field(
            description="Ungefähre Tiefe des Grabens bis zur Grabensohle in m",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None


class PFSSchutzstreifenData(BaseFeature):
    """Dauerhafte Einschränkungen und Eingriffe entlang der Trasse"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "DataType"
    schutzstreifen: Annotated[
        definitions.Length | None,
        Field(
            description="Dinglich zu sichernder Schutzstreifen einer (Frei-)Leitung. Angabe der Gesamtbreite in m. Bei Hochspannungsleitungen erfolgt für die parabolische Form die Angabe der maximalen Breite. (Zur Darstellung im Web-GIS kann auch der FeatureType PFS_Schutzstreifen genutzt werden)",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    SchutzstreifenGehoelzfrei: Annotated[
        definitions.Length | None,
        Field(
            description="Breite des Schutzstreifens, der dauerhaft von Gehölzen freizuhalten ist, in m",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    schutzstreifenWald: Annotated[
        definitions.Length | None,
        Field(
            description="Nur für Hochspannungsleitungen: In bewaldeten Leitungsabschnitten verläuft der Schutzstreifen parallel zur Leitungsachse und nicht in parabolischer Form. Maßgebend für die Gesamtbreite ist eine sog. Baumfallkurve, welche zur Sicherung der äußeren Leiterseile vor umstürzenden Bäumen dient.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None


class PFSVersionRVP(BaseFeature):
    """Referenz auf die zugehörige Raumverträglichkeitsprüfung"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "DataType"
    refUuid: Annotated[
        str | None,
        Field(
            description="UUID des Plans",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    versionName: Annotated[
        str | None,
        Field(
            description="Name des Plans",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    datum: Annotated[
        date_aliased | None,
        Field(
            description="Datum der (landesplanerischen) Feststellung/Festlegung, raumodnerische Beurteilung,  Entscheid der Bundesfachplanung",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class RVPVersion(BaseFeature):
    """Versionierung der Variante des Plans"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "DataType"
    versionName: Annotated[
        str,
        Field(
            description="Name der Version",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    datum: Annotated[
        date_aliased,
        Field(
            description="Datum der Version",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "1",
            },
        ),
    ]


class RVPVorgaengerVersion(BaseFeature):
    """Referenz auf die voherige Version des Plans"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "DataType"
    refUuid: Annotated[
        str | None,
        Field(
            description="UUID des vorherigen Plans",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    versionName: Annotated[
        str | None,
        Field(
            description="Name des vorherigen Plans",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class XPAuslegung(BaseFeature):
    """Angaben zur Auslegung von Planunterlagen in den betroffenen Gemeinden"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "DataType"
    gemeinde: Annotated[
        str | None,
        Field(
            description="Name der betroffenen Gemeinde",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    auslegungStartDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum der Auslegung",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    auslegungEndDatum: Annotated[
        date_aliased | None,
        Field(
            description="Ende der Auslegung",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class XPGesetzlicheGrundlage(BaseFeature):
    """Spezifikation der gesetzlichen Grundlage eines Planinhalts"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "DataType"
    name: Annotated[
        str | None,
        Field(
            description="Name / Titel des Gesetzes",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detail: Annotated[
        str | None,
        Field(
            description="Detaillierte Spezifikation der gesetzlichen Grundlage mit Angabe einer Paragraphennummer",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ausfertigungDatum: Annotated[
        date_aliased | None,
        Field(
            description="Die Datumsangabe bezieht sich in der Regel auf das Datum der Ausfertigung des Gesetzes oder der Rechtsverordnung",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    letzteBekanntmDatum: Annotated[
        date_aliased | None,
        Field(
            description="Ist das Gesetz oder die Verordnung nach mehreren Änderungen neu bekannt gemacht worden, kann anstelle des Ausfertigungsdatums das Datum der Bekanntmachung der Neufassung angegeben werden",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    letzteAenderungDatum: Annotated[
        date_aliased | None,
        Field(
            description="Ist ein Gesetz oder eine Rechtsverordnung nach der Veröffentlichung des amtlichen Volltextes geändert worden, kann hierauf hingewiesen werden",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class XPNetzExterneReferenz(BaseFeature):
    """Verweis auf ein extern gespeichertes Dokument, einen extern gespeicherten Plan oder einen Datenbank-Eintrag"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "DataType"
    referenzName: Annotated[
        str,
        Field(
            description="Name des referierten Dokument innerhalb des Informationssystems",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    referenzURL: Annotated[
        AnyUrl,
        Field(
            description="URI des referierten Dokuments, bzw. Datenbank-Schlüssel. Wenn der XTrasseGML Datensatz und das referierte Dokument in einem hierarchischen Ordnersystem gespeichert sind, kann die URI auch einen relativen Pfad vom XPlanGML-Datensatz zum Dokument enthalten.",
            json_schema_extra={
                "typename": "URI",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    beschreibung: Annotated[
        str | None,
        Field(
            description="Beschreibung des referierten Dokuments",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    datum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des referierten Dokuments",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class XPNetzObjekt(BaseFeature):
    """Abstrakte Oberklasse für alle Fachobjekte des Leitungsplans. Die Attribute dieser Klasse werden über den Vererbungs-Mechanismus an alle Fachobjekte weitergegeben."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    id: str | None = None
    uuid: Annotated[
        str | None,
        Field(
            description="Eindeutiger Identifier des Objektes",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    title: Annotated[
        str,
        Field(
            description="Textliche Bezeichnung des Objekts (Anmerkung: Ldproxy nutzt das Attribut für die Kodierung der Objektreferenzierung in HTML, GML und JSON)",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    beschreibung: Annotated[
        str | None,
        Field(
            description="Kommentierende Beschreibung von Planinhalten/-objekten",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    aufschrift: Annotated[
        str | None,
        Field(
            description="Spezifischer Text zur Beschriftung von Planinhalten",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    netzbetreiber: Annotated[
        str | None,
        Field(
            description="Angabe des Leitungsbetreibers",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class XPNetzPlan(BaseFeature):
    """Abstrakte Oberklasse für alle Klassen raumbezogener Leitungspläne"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    id: str | None = None
    uuid: Annotated[
        str | None,
        Field(
            description="Eindeutiger Identifier des Objektes",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    name: Annotated[
        str,
        Field(
            description="Name des Plans  (Anmerkung: Ldproxy nutzt das Attribut für die Kodierung der Objektreferenzierung in HTML und GML)",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    nummer: Annotated[
        str | None,
        Field(
            description="Nummer des Plans",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    internalId: Annotated[
        str | None,
        Field(
            description="Interner Identifikator des Plans",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    beschreibung: Annotated[
        str | None,
        Field(
            description="Kommentierende Beschreibung des Leitungsplans",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gesetzlicheGrundlage: Annotated[
        list[XPGesetzlicheGrundlage] | None,
        Field(
            description="Angabe der gesetzlichen Grundlage des Planinhalts",
            json_schema_extra={
                "typename": "XP_GesetzlicheGrundlage",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    technischePlanerstellung: Annotated[
        str | None,
        Field(
            description="Bezeichnung der Institution oder Firma, die den Plan technisch erstellt hat",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    technHerstellDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum, an dem der Plan technisch ausgefertigt wurde",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    erstellungsMassstab: Annotated[
        int | None,
        Field(
            description="Der bei der Erstellung des Plans benutzte Kartenmaßstab",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    externeReferenz: Annotated[
        list[XPNetzExterneReferenz] | None,
        Field(
            description="Referenz auf ein Dokument oder einen Plan",
            json_schema_extra={
                "typename": "XP_NetzExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    position: Annotated[
        definitions.Polygon,
        Field(
            description="Flächenhafter Raumbezug des Plans",
            json_schema_extra={
                "typename": "GM_Surface",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]
    hatObjekt: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            description="Referenz auf ein Objekt des Netzplans",
            json_schema_extra={
                "typename": ["XP_Planreferenz", "XP_Trassenquerschnitt"],
                "stereotype": "Association",
                "reverseProperty": "gehoertZuPlan",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    hatBSTObjekt: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            description="Referenz auf ein spezifisches Objekt des Netzplans",
            json_schema_extra={
                "typename": [
                    "BST_Abwasserleitung",
                    "BST_Armatur",
                    "BST_Baum",
                    "BST_Energiespeicher",
                    "BST_Gasleitung",
                    "BST_Hausanschluss",
                    "BST_Kraftwerk",
                    "BST_Mast",
                    "BST_Richtfunkstrecke",
                    "BST_Schacht",
                    "BST_SonstigeInfrastruktur",
                    "BST_SonstigeInfrastrukturFlaeche",
                    "BST_SonstigeLeitung",
                    "BST_Station",
                    "BST_StationFlaeche",
                    "BST_Strassenablauf",
                    "BST_Strassenbeleuchtung",
                    "BST_Stromleitung",
                    "BST_Telekommunikationsleitung",
                    "BST_Umspannwerk",
                    "BST_Verteiler",
                    "BST_Waermeleitung",
                    "BST_Wasserleitung",
                    "BST_Wegekante",
                ],
                "stereotype": "Association",
                "reverseProperty": "gehoertZuPlan",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            },
        ),
    ] = None


class XPObjekt(XPNetzObjekt):
    """Abstrakte Oberklasse für Teilmodell-übergreifende Fachobjekte"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    gehoertZuPlan: Annotated[
        AnyUrl | UUID,
        Field(
            description="Referenz auf den Netzplan, zu dem das Objekt gehört",
            json_schema_extra={
                "typename": [
                    "BRA_AusbauPlan",
                    "BST_NetzPlan",
                    "IGP_Plan",
                    "ISA_Plan",
                    "PFS_Plan",
                    "RVP_Plan",
                ],
                "stereotype": "Association",
                "reverseProperty": "hatObjekt",
                "sourceOrTarget": "source",
                "multiplicity": "1",
            },
        ),
    ]


class XPPlanreferenz(XPObjekt):
    """Kartenausschnitt eines extern referenzierten Planwerkes"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Polygon,
        Field(
            description="Raumbezug des Plans",
            json_schema_extra={
                "typename": "GM_Surface",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]
    referenz: Annotated[
        XPNetzExterneReferenz,
        Field(
            description="Referenz auf einen Plan, der sich auf das markierte Polygon bezieht",
            json_schema_extra={
                "typename": "XP_NetzExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "1",
            },
        ),
    ]


class XPTrassenquerschnitt(XPObjekt):
    """Linie eines Querschnitts, der durch ein externes Dokument dargestellt wird"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Line,
        Field(
            description="Verlauf des Trassenquerschnitts",
            json_schema_extra={
                "typename": "GM_Curve",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]
    trassenquerschnitt: Annotated[
        XPNetzExterneReferenz,
        Field(
            description="Referenz auf ein Dokument/Bild, das den Trassenquerschnitt an der markierten Position zeigt",
            json_schema_extra={
                "typename": "XP_NetzExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "1",
            },
        ),
    ]


class BRAObjekt(XPNetzObjekt):
    """Basisklasse für alle raumbezogenen Objekte des Fachschemas Breitbandausbau"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    gehoertZuBRA: Annotated[
        AnyUrl | UUID,
        Field(
            description="Referenz auf den Breitband-Ausbauplan, zu dem das Objekt gehört",
            json_schema_extra={
                "typename": "BRA_AusbauPlan",
                "stereotype": "Association",
                "reverseProperty": "hatBRAObjekt",
                "sourceOrTarget": "source",
                "multiplicity": "1",
            },
        ),
    ]


class BSTNetzPlan(XPNetzPlan):
    """Klasse zur Modellierung von Bestandsplänen"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    netzSparte: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000", "6000", "9999"]],
        Field(
            description="Auswahl der Leitungssparte(n).",
            json_schema_extra={
                "typename": "BST_NetzSparte",
                "stereotype": "Enumeration",
                "multiplicity": "1..*",
                "enumDescription": {
                    "1000": {
                        "name": "Telekommunikation",
                        "alias": "Telekommunikation",
                        "description": "Telekommunikation",
                    },
                    "2000": {
                        "name": "Gas",
                        "alias": "Gas",
                        "description": "Gasversorgung",
                    },
                    "3000": {
                        "name": "Elektrizitaet",
                        "alias": "Elektrizität",
                        "description": "Stromversorgung",
                    },
                    "4000": {
                        "name": "Waermeversorgung",
                        "alias": "Wärmeversorgung",
                        "description": "Versorgung mit Fern- oder Nahwärme",
                    },
                    "5000": {
                        "name": "Abwasserentsorgung",
                        "alias": "Abwasserentsorgung",
                        "description": "Abwasserentsorgung",
                    },
                    "6000": {
                        "name": "Wasserversorgung",
                        "alias": "Wasserversorgung",
                        "description": "Trinkwasserversorgung",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "Sonstiges Netz",
                        "description": "Sonstiges Ver- bzw. Entsorgungsnetz",
                    },
                },
            },
            min_length=1,
        ),
    ]


class BSTObjekt(XPNetzObjekt):
    """Abstrakte Oberklasse für alle Klassen des Fachschemas Bestandsnetze"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    gehoertZuPlan: Annotated[
        AnyUrl | UUID,
        Field(
            description="Referenz auf einen Netzplan, zu dem das Objekt gehört",
            json_schema_extra={
                "typename": [
                    "BRA_AusbauPlan",
                    "BST_NetzPlan",
                    "IGP_Plan",
                    "ISA_Plan",
                    "PFS_Plan",
                    "RVP_Plan",
                ],
                "stereotype": "Association",
                "reverseProperty": "hatBSTObjekt",
                "sourceOrTarget": "source",
                "multiplicity": "1",
            },
        ),
    ]


class IGPObjekt(XPNetzObjekt):
    """Basisklasse für alle raumbezogenen Objekte des Fachschemas Infrastrukturgebieteplan. Abgeleitete Fachobjekte können neben IGP_Plan auch von PFS_Plan (und RVP_Plan) referiert werden."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    gehoertZuIP: Annotated[
        AnyUrl | UUID,
        Field(
            description="Referenz auf den Infrastrukturplan, zu dem das Objekt gehört",
            json_schema_extra={
                "typename": ["IGP_Plan", "PFS_Plan", "RVP_Plan"],
                "stereotype": "Association",
                "reverseProperty": "hatIGPObjekt",
                "sourceOrTarget": "source",
                "multiplicity": "1",
            },
        ),
    ]


class IPObjekt(XPNetzObjekt):
    """Abstrakte Oberklasse für gemeinsame Fachobjekte der drei Teilmodelle"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    gehoertZuIP: Annotated[
        AnyUrl | UUID,
        Field(
            description="Referenz auf den Infrastrukturplan, zu dem das Objekt gehört",
            json_schema_extra={
                "typename": ["IGP_Plan", "PFS_Plan", "RVP_Plan"],
                "stereotype": "Association",
                "reverseProperty": "hatIPObjekt",
                "sourceOrTarget": "source",
                "multiplicity": "1",
            },
        ),
    ]


class IPStationierungspunkt(IPObjekt):
    """Stationierungspunkte sind Vermessungspunkte entlang einer Trasse. Sie können in regelmäßigen Abständen Längenangaben liefern oder sonstige spezifische Punkte auf der Trasse kennzeichnen."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Point,
        Field(
            description="Raumbezug des Objektes",
            json_schema_extra={
                "typename": "GM_Point",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]
    laenge: Annotated[
        definitions.Length | None,
        Field(
            description="Angabe der Streckenkilometer in m",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None


class IPWebservice(BaseFeature):
    """Referenzierung von Webservices. Die Dienste liefern raumbezogene Daten, die für die Darstellung von Plänen der Raumverträglichkeitsprüfungen, Infrastrukturgebiete und Planfeststellungsverfahren relevant sind."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "DataType"
    name: Annotated[
        str,
        Field(
            description="Name des Dienstes",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    beschreibung: Annotated[
        str | None,
        Field(
            description="Beschreibung der Daten",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    typ: Annotated[
        Literal["1000", "2000", "3000", "9999"],
        Field(
            description="Typ des Webservice",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "WMS",
                        "alias": "Web Map Service",
                        "description": "Web Map Service",
                    },
                    "2000": {
                        "name": "WFS",
                        "alias": "Web Feature Service",
                        "description": "Web Feature Service",
                    },
                    "3000": {
                        "name": "OAF",
                        "alias": "OGC API Features",
                        "description": "OGC API Features",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiger Dienst",
                        "description": "Sonstiger Dienst",
                    },
                },
                "typename": "IP_WebserviceTyp",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    url: Annotated[
        AnyUrl,
        Field(
            description="Internetadresse des Diensteservers",
            json_schema_extra={
                "typename": "URI",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    filterausdruck: Annotated[
        str | None,
        Field(
            description="Filterausdruck, der die url erweitert (um z.B. einzelne Features abzufragen)",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ressourcenidentifikatorGDI: Annotated[
        str | None,
        Field(
            description="Eindeutige Kennung des Datensatzes im Geodatenkatalog der GDI-DE (https://registry.gdi-de.org/id/...)",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class ISAObjekt(XPNetzObjekt):
    """Basisklasse für alle Objekte des Infrastrukturatlas-Schemas"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    foerderung: Annotated[
        Literal["1000", "2000", "3000"],
        Field(
            description="Das Kriterium der Förderung kennzeichnet einzelne Infrastrukturen, Leitungsabschnitte oder auch ganze Netzbereiche, die im Rahmen der Breitbandförderung finanziert wurden.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Gefoerdert",
                        "alias": "gefördert",
                        "description": "gefördert im Rahmen des Breitbandausbaus",
                    },
                    "2000": {
                        "name": "TeilweiseGefoerdert",
                        "alias": "teilweise gefördert",
                        "description": "teilweise gefördert im Rahmen des Breitbandausbaus",
                    },
                    "3000": {
                        "name": "NichtGefoerdert",
                        "alias": "nicht gefördert",
                        "description": "nicht gefördert",
                    },
                },
                "typename": "ISA_Foerderung",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    verfuegbarkeit: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000"],
        Field(
            description="Die tatsächliche Verfügbarkeit wird als Kapazitäts- bzw. Auslastungsangabe zu den Einrichtungen verstanden. Über vorgegebene Kategorien werden die tatsächlich vorhandenen Kapazitäten erfasst (ein Leer-/Schutzrohrabschnitt ist bspw. nur teilweise befüllt oder ein Bauwerk bietet als Technikraum noch Platz für TK-Infrastruktur und ist daher auf Anfrage verfügbar etc.).",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "NichtVerfuegbar_Belegt",
                        "alias": "nicht verfügbar - belegt",
                        "description": "belegt",
                    },
                    "2000": {
                        "name": "NichtVerfuegbar_Reserviert",
                        "alias": "nicht verfügbar - für eigene Planung reserviert",
                        "description": "für eigene Planung reserviert - nicht verfügbar",
                    },
                    "3000": {
                        "name": "Verfuegbar_Teilweise",
                        "alias": "verfügbar - verfügbar",
                        "description": "teilweise verfügbar",
                    },
                    "4000": {
                        "name": "Verfuegbar_AufAnfrage",
                        "alias": "verfügbar - auf Anfrage",
                        "description": "auf Anfrage verfügbar",
                    },
                    "5000": {
                        "name": "Verfuegbar_ZurMitnutzungAngeboten",
                        "alias": "verfuegbar - zur Mitnutzung angeboten",
                        "description": "Kapazitäten werden zur Mitnutzung angeboten",
                    },
                },
                "typename": "ISA_VerfuegbarkeitTyp",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    nutzung: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000", "6000", "9999"]],
        Field(
            description="Die Angabe zur gegenwärtigen Nutzung enthält die Information, für welchen Zweck die gelieferten Einrichtungen tatsächlich genutzt werden (z. B. Nutzung des Schutz-/Leerrohrs für TK-Zwecke oder als Schutz-/Leerrohr für die Elektrizitätsversorgung oder Leitungen für Fernwärme etc.). Eine Zuordnung der vorgegebenen Kategorien soll möglichst bezogen auf jede einzelne Infrastruktureinrichtung vorgenommen werden.\r\nEine Mehrfacheinordnung ist auch weiterhin möglich, damit Einrichtungen, die aktuell für mehrere Zwecke genutzt werden, entsprechend erfasst werden können.",
            json_schema_extra={
                "typename": "ISA_NutzungTyp",
                "stereotype": "Enumeration",
                "multiplicity": "1..*",
                "enumDescription": {
                    "1000": {
                        "name": "Telekommunikation",
                        "alias": "Telekommunikation",
                        "description": "Telekommunikation",
                    },
                    "2000": {
                        "name": "Gas",
                        "alias": "Gas",
                        "description": "Gasversorgung",
                    },
                    "3000": {
                        "name": "Elektrizitaet",
                        "alias": "Elektrizität",
                        "description": "Stromversorgung",
                    },
                    "4000": {
                        "name": "Fernwaerme",
                        "alias": "Fernwärme",
                        "description": "Versorgung mit Fernwärme",
                    },
                    "5000": {
                        "name": "Wasser_Abwasser",
                        "alias": "Trinkwasserversorgung und Abwasserentsorgung",
                        "description": "Trinkwasserversorgung  und Abwasserentsorgung",
                    },
                    "6000": {
                        "name": "Verkehr",
                        "alias": "Verkehr",
                        "description": "Verkehr",
                    },
                    "9999": {
                        "name": "Sonstige",
                        "alias": "Sonstiges Netz",
                        "description": "Die Kategorie „Sonstige“ dient der Aufnahme von Einrichtungen, die zum Zeitpunkt der Datenlieferung (noch) keiner gegenwärtigen Nutzung zugeordnet werden können. Darunter fallen z.B. öffentliche Gebäude/Grundstücke oder Leerrohre, die nur als Reserve mitverlegt wurden.",
                    },
                },
            },
            min_length=1,
        ),
    ]
    lagegenauigkeit: Annotated[
        Literal["1000", "2000", "3000", "4000"] | None,
        Field(
            description="Lagegenauigkeit des Raumbezugs",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "bis_10_CM",
                        "alias": "bis 10 cm",
                        "description": "Lagegenauigkeit bis 10 cm",
                    },
                    "2000": {
                        "name": "bis_1_M",
                        "alias": "bis 1 m",
                        "description": "Lagegenauigkeit bis zu 1 m",
                    },
                    "3000": {
                        "name": "bis_10_M",
                        "alias": "bis 10 m",
                        "description": "Lagegenauigkeit bis zu 10 m",
                    },
                    "4000": {
                        "name": "ueber_10_M",
                        "alias": "über 10 m",
                        "description": "Lagegenauigkeit schlechter als 10 m",
                    },
                },
                "typename": "ISA_Lagegenauigkeit",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    lagegenauigkeitText: Annotated[
        str | None,
        Field(
            description="Textlich formulierte Lagegenauigkeit des Raumbezugs",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    typ: Annotated[
        str | None,
        Field(
            description='Es besteht die Möglichkeit zusätzlich nähere Spezifikationen zu den Infrastrukturen als TYP-Angaben in den ISA aufzunehmen. Diese sollten möglichst eindeutig benannt und den einzelnen Geometrien zugeordnet sein (s. Beispiele "TYP" in den einzelnen Objektarten).',
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ausnahmeISA: Annotated[
        bool | None,
        Field(
            description="Das Objekt soll gemäß § 79  Abs. 3 TKG nicht im Infrastrukturatlas veröffentlicht werden. \r\nDas Objekt wird in einem separaten Datensatz „Ausnahme nach § 79 Abs. 3 TKG_Geodaten“ an die BNetzA geliefert.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gehoertZuISA: Annotated[
        AnyUrl | UUID,
        Field(
            description="Referenz auf den Infrastrukturatlas. zu dem das Objekt gehört",
            json_schema_extra={
                "typename": "ISA_Plan",
                "stereotype": "Association",
                "reverseProperty": "hatISAObjekt",
                "sourceOrTarget": "source",
                "multiplicity": "1",
            },
        ),
    ]


class ISAPlan(XPNetzPlan):
    """Die zentrale Informationsstelle des Bundes verlangt gemäß § 79 TKG von Eigentümern oder Betreibern öffentlicher Versorgungsnetze sowie Betreibern sonstiger physischer Infrastrukturen Informationen zu allen passiven Netzinfrastrukturen und sonstigen physischen Infrastrukturen. Ausgeführt  werden diese gesetzlichen Verpflichtungen in den "Datenlieferungsbedingungen für den Infrastrukturatlas der Zentralen Informationsstelle des Bundes".
    ISA_Plan modelliert auf Basis der Datenlieferungsbedingungen einen Datensatz für die Zulieferung zum Infrastrukturatlas (Stand: August 2022).
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    inhaberTyp: Annotated[
        Literal["1000", "2000"],
        Field(
            description="Es ist anzugeben, ob der Infrastrukturinhaber Eigentümer oder Betreiber der gelieferten Infrastrukturen ist. Eine Darstellung dieser Eigenschaft im Infrastrukturatlas erfolgt nicht. Die Erhebung erfolgt zur internen Verifizierung des Datenlieferanten.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Eigentuemer",
                        "alias": "Eigentümer",
                        "description": "Eigentümer",
                    },
                    "2000": {
                        "name": "Betreiber",
                        "alias": "Betreiber",
                        "description": "Betreiber",
                    },
                },
                "typename": "ISA_InhaberTyp",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    kontaktMitnutzung: Annotated[
        ISAAnsprechpartner,
        Field(
            description="Ansprechperson, die für Mitnutzungsanfragen verantwortlich ist.",
            json_schema_extra={
                "typename": "ISA_Ansprechpartner",
                "stereotype": "DataType",
                "multiplicity": "1",
            },
        ),
    ]
    kontaktGIS: Annotated[
        ISAAnsprechpartner,
        Field(
            description="Ansprechperson, die für Rückfragen zur Verarbeitung der Geodaten verantwortlich ist.",
            json_schema_extra={
                "typename": "ISA_Ansprechpartner",
                "stereotype": "DataType",
                "multiplicity": "1",
            },
        ),
    ]
    hatISAObjekt: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            description="Referenz auf ein spezifisches Objekt des Infrastrukturatlas",
            json_schema_extra={
                "typename": [
                    "ISA_Abwasserleitung",
                    "ISA_Ampel",
                    "ISA_Bauwerk",
                    "ISA_Funkmast",
                    "ISA_Glasfaser",
                    "ISA_Grundstueck_Liegenschaft",
                    "ISA_Haltestelle",
                    "ISA_Hauptverteiler",
                    "ISA_Holz_Mast",
                    "ISA_Kabelverzweiger",
                    "ISA_Lehrrohr",
                    "ISA_PointOfPresence",
                    "ISA_Reklametafel_Litfasssauele",
                    "ISA_Richtfunkstrecke",
                    "ISA_Strassenlaterne",
                    "ISA_Strassenmobiliar",
                    "ISA_Verkehrsschild",
                    "ISA_Zugangspunkt",
                ],
                "stereotype": "Association",
                "reverseProperty": "gehoertZuISA",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            },
        ),
    ] = None


class PFSObjekt(XPNetzObjekt):
    """Basisklasse für alle raumbezogenen Objekte des Fachschemas Planfeststellung"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    gehoertZuPFS: Annotated[
        AnyUrl | UUID,
        Field(
            description="Referenz auf den Plan, zu dem das Objekt gehört",
            json_schema_extra={
                "typename": "PFS_Plan",
                "stereotype": "Association",
                "reverseProperty": "hatPFSObjekt",
                "sourceOrTarget": "source",
                "multiplicity": "1",
            },
        ),
    ]
    nachrichtlUebernahme: Annotated[
        bool | None,
        Field(
            description="Nachrichtliche Übernahme = true: Objekt ist nicht Bestandteil dieses Planfeststellungsverfahrens. Default = false.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False
    planErgaenzAenderung: Annotated[
        bool | None,
        Field(
            description="Objekt ist Bestandtteil eines Planergänzungs- oder -äenderungsverfahrens = true (s. PFS_PlanStatus). Default = false.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False


class PFSSchutzrohr(BaseFeature):
    """Daten zu Kabelschutzrohren in einem Leitungsabschnitt"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "DataType"
    regelueberdeckung: Annotated[
        definitions.Length | None,
        Field(
            description="Mindestabstand zwischen Oberkante des Weges und Oberkante des Rohres in m.\r\n(gml:LengthType: uom=“m“ oder uom=“urn:adv:uom:m“)",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    nennweite: Annotated[
        str | None,
        Field(
            description="Nennweite (DN)",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    aussendurchmesser: Annotated[
        definitions.Length | None,
        Field(
            description="Aussendurchmesser (DA) in m",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    anzahl: Annotated[
        int | None,
        Field(
            description="Anzahl der Schutzrohre",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    werkstoff: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "2000",
            "20001",
            "20002",
            "20003",
            "2500",
            "25001",
            "25002",
            "25003",
            "25004",
            "25005",
            "3000",
            "30001",
            "30002",
            "4000",
            "5000",
            "9999",
        ]
        | None,
        Field(
            description="Werkstoff des Rohres",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Kunststoff",
                        "alias": "Kunststoff",
                        "description": "Kunststoff",
                    },
                    "10001": {
                        "name": "Polyethylen_PE",
                        "alias": "Polyethylen ( PE)",
                        "description": "Polyethylen (PE)",
                    },
                    "10002": {
                        "name": "Polyethylen_PE_HD",
                        "alias": "High-Density Polyethylen",
                        "description": "High-Density Polyethylen",
                    },
                    "10003": {
                        "name": "Polypropylen_PP",
                        "alias": "Polypropylen ( PP)",
                        "description": "Polypropylen (PP)",
                    },
                    "10004": {
                        "name": "Polycarbonat_PC",
                        "alias": "Polycarbonat ( PC)",
                        "description": "Polycarbonat (PC)",
                    },
                    "10005": {
                        "name": "Polyvinylchlorid_PVC_U",
                        "alias": "Polyvinylchlorid ( PVC- U)",
                        "description": "Polyvinylchlorid (PVC-U)",
                    },
                    "2000": {"name": "Stahl", "alias": "Stahl", "description": "Stahl"},
                    "20001": {
                        "name": "StahlVerzinkt",
                        "alias": "Stahl verzinkt",
                        "description": "Stahl verzinkt",
                    },
                    "20002": {
                        "name": "Stahlgitter",
                        "alias": "Stahlgitter",
                        "description": "Stahlfachwerkskonstruktion (z.B. Freileitungsmast als Gittermast)",
                    },
                    "20003": {
                        "name": "Stahlrohr",
                        "alias": "Stahlrohr",
                        "description": "Rohrförmiger Profilstahl, dessen Wand aus Stahl besteht. Stahlrohre dienen der Durchleitung von flüssigen, gasförmigen oder festen Stoffen, oder werden als statische oder konstruktive Elemente verwendet (z.B. Freileitungsmast als Stahlrohrmast)",
                    },
                    "2500": {
                        "name": "Stahlverbundrohr",
                        "alias": "Stahlverbundrohr",
                        "description": "Stahlverbundrohre im Rohrleitungsbau",
                    },
                    "25001": {
                        "name": "St_PE",
                        "alias": "Stahlrohr mit Standard-Kunststoffumhüllung (PE)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PE-Basis",
                    },
                    "25002": {
                        "name": "St_PP",
                        "alias": "Stahlrohr mit Kunstoffumhüllung (PP)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PP-Basis für höhere Temperatur- und Härte-Anforderungen",
                    },
                    "25003": {
                        "name": "St_FZM",
                        "alias": "Stahlrohr mit FZM-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz durch Faserzementmörtel-Ummantelung (FZM)",
                    },
                    "25004": {
                        "name": "St_GFK",
                        "alias": "Stahlrohr mit GFK-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz aus glasfaserverstärktem Kunststoff (GFK) für höchste mechanische Abriebfestigkeit bei grabenlosem Rohrvortrieb",
                    },
                    "25005": {
                        "name": "St_ZM_PE",
                        "alias": "Stahl-Verbundrohr (ZM-PE)",
                        "description": "Stahlrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserohr)",
                    },
                    "3000": {
                        "name": "Gusseisen",
                        "alias": "Gusseisen",
                        "description": "Gusseisen",
                    },
                    "30001": {
                        "name": "GGG_ZM",
                        "alias": "duktiles Gussrohr mit ZM-Auskleidung",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung (z.B Abwasserrohr)",
                    },
                    "30002": {
                        "name": "GGG_ZM_PE",
                        "alias": "duktiles Guss-Verbundrohr (ZM-PE)",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserrohr)",
                    },
                    "4000": {
                        "name": "Beton",
                        "alias": "Beton",
                        "description": "Beton (z.B. Schacht)",
                    },
                    "5000": {
                        "name": "Holz",
                        "alias": "Holz",
                        "description": "Holz (z.B. Holzmast)",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiger Werkstoff",
                        "description": "Sonstiger Werkstoff",
                    },
                },
                "typename": "XP_Werkstoff",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    zweck: Annotated[
        str | None,
        Field(
            description="Zweck der Verlegung (z.B. Mitverlegung Leerrohr, Steuerungskabel)",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class PFSTrasse(PFSObjekt):
    """Basisklasse für PFS-Trassenobjekte mit Liniengeometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Line,
        Field(
            description="Raumbezug des Objektes",
            json_schema_extra={
                "typename": "GM_Curve",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]
    leitungstyp: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "10006",
            "2000",
            "20001",
            "20002",
            "20003",
        ]
        | None,
        Field(
            description="Geplanter Leitungstyp",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Erdverlegt",
                        "alias": "erdverlegte (Rohr-)Leitungen",
                        "description": "Oberkategorie für erdverlegte (Rohr-)Leitungen",
                    },
                    "10001": {
                        "name": "Erdkabel",
                        "alias": "Erdkabel",
                        "description": "Ein Erdkabel ist ein im Erdboden verlegtes elektrisch genutztes Kabel mit einer besonders robusten Isolierung nach außen, dem Kabelmantel, der eine Zerstörung derselben durch chemische Einflüsse im Erdreich bzw. im Boden lebender Kleintiere verhindert.",
                    },
                    "10002": {
                        "name": "Seekabel",
                        "alias": "Seekabel",
                        "description": "Ein Seekabel (auch Unterseekabel, Unterwasserkabel) ist ein im Wesentlichen in einem Gewässer verlegtes Kabel zur Datenübertragung oder die Übertragung elektrischer Energie.",
                    },
                    "10003": {
                        "name": "Schutzrohr",
                        "alias": "Schutzrohr",
                        "description": "Im Schutzrohr verlegte oder zu verlegende Kabel/Leitungen. - Schutzrohre schützen erdverlegte Leitungen vor mechanischen Einflüssen und Feuchtigkeit.",
                    },
                    "10004": {
                        "name": "Leerrohr",
                        "alias": "Leerrohr (unbelegtes Schutzrohr)",
                        "description": "Über die Baumaßnahme hinaus unbelegtes Schutzrohr",
                    },
                    "10005": {
                        "name": "Leitungsbuendel",
                        "alias": "Leitungsbündel",
                        "description": "Bündel von Kabeln und/oder Schutzrohren in den Sparten Sparten Strom und Telekommunikation im Bestand",
                    },
                    "10006": {
                        "name": "Dueker",
                        "alias": "Düker",
                        "description": "Druckleitung zur Unterquerung von Straßen, Flüssen, Bahngleisen etc. Im Düker kann die Flüssigkeit das Hindernis überwinden, ohne dass Pumpen eingesetzt werden müssen.",
                    },
                    "2000": {
                        "name": "Oberirdisch",
                        "alias": "oberirdischer Verlauf",
                        "description": "Oberirdisch verlegte Leitungen und Rohre",
                    },
                    "20001": {
                        "name": "Freileitung",
                        "alias": "Freileitung",
                        "description": "Elektrische Leitung, deren spannungsführende Leiter im Freien durch die Luft geführt und meist auch nur durch die umgebende Luft voneinander und vom Erdboden isoliert sind. In der Regel werden die Leiterseile von Freileitungsmasten getragen, an denen sie mit Isolatoren befestigt sind.",
                    },
                    "20002": {
                        "name": "Heberleitung",
                        "alias": "Heberleitung",
                        "description": "Leitung zur Überquerung von Straßen oder zur Verbindung von Behältern (Gegenstück zu einem Düker)",
                    },
                    "20003": {
                        "name": "Rohrbruecke",
                        "alias": "Rohrbrücke",
                        "description": "Eine Rohrbrücke oder Rohrleitungsbrücke dient dazu, einzelne oder mehrere Rohrleitungen oberirdisch über größere Entfernungen zu führen.",
                    },
                },
                "typename": "XP_LeitungTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class RVPObjekt(XPNetzObjekt):
    """Basisklasse für alle raumbezogenen Objekte des Fachschemas Raumvertraeglichkeit. Abgeleitete Fachobjekte können neben RVP_Plan auch von PFS_Plan (und IGP_Plan) referiert werden."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    gehoertZuIP: Annotated[
        AnyUrl | UUID,
        Field(
            description="Referenz auf den Infrastrukturplan, zu dem das Objekt gehört",
            json_schema_extra={
                "typename": ["IGP_Plan", "PFS_Plan", "RVP_Plan"],
                "stereotype": "Association",
                "reverseProperty": "hatRVPObjekt",
                "sourceOrTarget": "source",
                "multiplicity": "1",
            },
        ),
    ]


class RVPTrassenkorridor(RVPObjekt):
    """Trassenkorridore werden im Rahmen der Raumverträglichkeitsprüfung oder der Bundesfachplanung als Gebietsstreifen ausgewiesen, innerhalb derer die Trasse einer Leitung verläuft.
    Der Trassenkorridor wird entweder a) mit einer Postion versehen,  b) ohne eigene Position über die Referenz auf RVP_TrassenkorridorSegmente gebildet oder c) alternativ dazu nur über die Klasse RVP_TrassenkorridorSegment dargestellt.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiPolygon | None,
        Field(
            description="Raumbezug des Korridors",
            json_schema_extra={
                "typename": "GM_MultiSurface",
                "stereotype": "Geometry",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    art: Annotated[
        Literal["1000", "10001", "10002", "10003", "2000", "20001", "20002", "9999"],
        Field(
            description="Variante des Trassenkorridors",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Antragskorridor",
                        "alias": "Antragskorridor",
                        "description": "Trassenkorridor als Ergebnis des Verfahrens (auch Antragsvariante). Der Antragskorridor kann sich aus mehreren Segmenten zusammensetzen.",
                    },
                    "10001": {
                        "name": "FestgelegterTrassenkorridor",
                        "alias": "festgelegter Trassenkorridor",
                        "description": "Festgelegter Trassenkorridor",
                    },
                    "10002": {
                        "name": "BevorzugterTrassenkorridor",
                        "alias": "präferierter Trassenkorridor",
                        "description": "Bevorzugter Trassenkorridor (auch präferierter oder Vorschlagstrassenkorridor)",
                    },
                    "10003": {
                        "name": "VorgeschlagenerTrassenkorridor",
                        "alias": "vorgeschlagener Trassenkorridor",
                        "description": "Vorgeschlagener Trassenkorridor / Vorschlags(trassen)korridor / Trassenkorridorvorschlag",
                    },
                    "2000": {
                        "name": "Variantenkorridor",
                        "alias": "Variantenkorridor",
                        "description": "Variante eines Trassenkorridors bei mehreren möglichen Trassenverläufen. Die jeweilige Varianten kann aus mehreren Segmenten bestehen.",
                    },
                    "20001": {
                        "name": "AlternativerTrassenkorridor",
                        "alias": "Alternativer Trassenkorridor",
                        "description": "Ernsthaft zu berücksichtigende bzw. in Frage kommende Alternative (im Vergleich zum Antragskorridor)",
                    },
                    "20002": {
                        "name": "PotenziellerTrassenkorridor",
                        "alias": "potenzieller Trassenkorridor",
                        "description": "Potenzieller Trassenkorridor",
                    },
                    "9999": {
                        "name": "SonstigerKorridor",
                        "alias": "sonstiger Korridor",
                        "description": "sonstiger Korridor",
                    },
                },
                "typename": "RVP_KorridorTyp",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    status: Annotated[
        Literal["1000", "2000", "3000", "4000"],
        Field(
            description="Planungsstatus des Korridors",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "InBearbeitung",
                        "alias": "in Bearbeitung",
                        "description": "Trassenkorridor ist Bestandteil einer laufenden Raumverträglichkeitsprüfung oder einer Rauwiderstandsanalyse",
                    },
                    "2000": {
                        "name": "ErgebnisRVP",
                        "alias": "Ergebnis der Raumverträglichkeitsprüfung",
                        "description": "Trassenkorridor ist das Ergebnis der Räumverträglichkeitsprüfung",
                    },
                    "3000": {
                        "name": "LandesplanerischeFeststellung",
                        "alias": "Landesplanerische Festlegung",
                        "description": "Abschluss der Raumverträglichkeitsprüfung durch landesplanerische Feststellung",
                    },
                    "4000": {
                        "name": "Bestand",
                        "alias": "Bestandskorridor",
                        "description": "Trassenkorrior um Bestandsleitungen",
                    },
                },
                "typename": "RVP_KorridorStatus",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    breite: Annotated[
        definitions.Length | None,
        Field(
            description="Breite des Trassenkorridors in Metern.\r\n(gml:LengthType: uom=“m“ oder uom=“urn:adv:uom:m“)",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    bewertung: Annotated[
        str | None,
        Field(
            description="Gesamtbewertung der Variante",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    bestehtAus: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            description="Verweis auf die Segmente, aus denen sich der Trassenkorridor zusammensetzt",
            json_schema_extra={
                "typename": "RVP_TrassenkorridorSegment",
                "stereotype": "Association",
                "multiplicity": "0..*",
            },
        ),
    ] = None


class XPAkteur(BaseFeature):
    """An der Baumaßnahme beteiligte Akteure"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "DataType"
    nameOrganisation: Annotated[
        str | None,
        Field(
            description="Name der Organisation",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    namePerson: Annotated[
        str | None,
        Field(
            description="Name der Person",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    strasseHausnr: Annotated[
        str | None,
        Field(
            description="Straße und Hausnummer",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    postfach: Annotated[
        str | None,
        Field(
            description="Postfach",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    postleitzahl: Annotated[
        str | None,
        Field(
            description="Postleitzahl",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ort: Annotated[
        str | None,
        Field(
            description="Ort",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    telefon: Annotated[
        str | None,
        Field(
            description="Telefonnummer",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    mail: Annotated[
        str | None,
        Field(
            description="Mail-Adresse",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    rolle: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "6000", "7100", "7200", "8000"]
        | None,
        Field(
            description="Rolle der Person/Organisation",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Antragstellung",
                        "alias": "Antragstellung",
                        "description": "Antragsteller",
                    },
                    "2000": {
                        "name": "BevollmaechtigtPlanung",
                        "alias": "Bevollmächtigt für Planung",
                        "description": "Bevollmächtigt und Ersteller der Planung",
                    },
                    "3000": {
                        "name": "Bevollmaechtigt",
                        "alias": "Bevollmächtigt",
                        "description": "Bevollmächtigtes Unternehmen",
                    },
                    "4000": {
                        "name": "Planung",
                        "alias": "Planung",
                        "description": "Planendes Büro",
                    },
                    "5000": {
                        "name": "Bauunternehmen",
                        "alias": "Bauunternehmen",
                        "description": "Unternehmen, das Tiefbaumaßnahmen durchführt",
                    },
                    "6000": {
                        "name": "Vorhabentraeger",
                        "alias": "Vorhabenträger",
                        "description": "Träger eines Vorhabens im Planfeststellungs- oder Raumordnungsverfahren",
                    },
                    "7100": {
                        "name": "Planfeststellungsbehoerde",
                        "alias": "Planfeststellungsbehörde",
                        "description": "Zuständige Behörde eines Planfeststellungsverfahrens",
                    },
                    "7200": {
                        "name": "Anhoerungsbehoerde",
                        "alias": "Anhörungsbehörde",
                        "description": "Behörde, die Anhörungsverfahren im Rahmen eines Planfeststellungsverfahrens durchführt",
                    },
                    "8000": {
                        "name": "Raumordnungsbehoerde",
                        "alias": "Zuständig für Raumverträglichkeitsprüfung",
                        "description": "Zuständige Behörde einer Raumverträglichkeitsprüfung",
                    },
                },
                "typename": "XP_Rolle",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BRAAusbauPlan(XPNetzPlan):
    """Die Klasse umfasst die übergreifenden Attribute einer TK-Planung, die im Geltungsbereich des TKG erstellt wird"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    hatBRAObjekt: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            description="Referenz auf ein spezifisches Objekt des BRA-Ausbauplans",
            json_schema_extra={
                "typename": [
                    "BRA_Baugrube",
                    "BRA_Baustelle",
                    "BRA_BreitbandtrasseAbschnitt",
                    "BRA_Hausanschluss",
                    "BRA_Kabel",
                    "BRA_Kompaktstation",
                    "BRA_Mast",
                    "BRA_Mikrorohr",
                    "BRA_Mikrorohrverbund",
                    "BRA_Rohrmuffe",
                    "BRA_Schacht",
                    "BRA_Schutzrohr",
                    "BRA_Umfeld",
                    "BRA_Verteiler",
                ],
                "stereotype": "Association",
                "reverseProperty": "gehoertZuBRA",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    beteiligte: Annotated[
        list[XPAkteur] | None,
        Field(
            description="Beteiligte Akteure der Baumaßnahme",
            json_schema_extra={
                "typename": "XP_Akteur",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    bauBeginn: Annotated[
        date_aliased | None,
        Field(
            description="Datum des geplanten Baubeginns",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    bauEnde: Annotated[
        date_aliased | None,
        Field(
            description="Datum des geplanten Abschlusses der Baumaßnahme",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    status: Annotated[
        Literal["1000", "2000", "3000", "4000"] | None,
        Field(
            description="Angabe zum Status des Plans im Kontext des TKG und der behördlichen Verfahren",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "VerlegungTKG",
                        "alias": "Verlegung TK-Linie nach TKG",
                        "description": "Verlegung einer neuen Trasse/TK-Linie gemäß § 127 Abs. 1 TKG",
                    },
                    "2000": {
                        "name": "AenderungTKG",
                        "alias": "Änderung TK-Linie nach TKG",
                        "description": "Änderung einer bestehenden Trasse/TK-Linie gemäß § 127 Abs. 1 TKG",
                    },
                    "3000": {
                        "name": "AnzeigeTKG",
                        "alias": "Anzeige gemäß TKG",
                        "description": "Geringfügige bauliche Maßnahme gemäß § 127 Abs. 4 TKG",
                    },
                    "4000": {
                        "name": "AnzeigeRahmenvertrag",
                        "alias": "Anzeige gemäß Rahmenvertrag",
                        "description": "Anzuzeigende Maßnahme gemäß Rahmenvertrag",
                    },
                },
                "typename": "BRA_PlanStatus",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BRALinienobjekt(BRAObjekt):
    """Oberklasse der Objekte eines Breitband-Ausbauplans mit Liniengeometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Line,
        Field(
            description="Raumbezug des Objektes",
            json_schema_extra={
                "typename": "GM_Curve",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]
    leitungstyp: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "10006",
            "2000",
            "20001",
            "20002",
            "20003",
        ]
        | None,
        Field(
            description="Auswahl des Leitungstyps",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Erdverlegt",
                        "alias": "erdverlegte (Rohr-)Leitungen",
                        "description": "Oberkategorie für erdverlegte (Rohr-)Leitungen",
                    },
                    "10001": {
                        "name": "Erdkabel",
                        "alias": "Erdkabel",
                        "description": "Ein Erdkabel ist ein im Erdboden verlegtes elektrisch genutztes Kabel mit einer besonders robusten Isolierung nach außen, dem Kabelmantel, der eine Zerstörung derselben durch chemische Einflüsse im Erdreich bzw. im Boden lebender Kleintiere verhindert.",
                    },
                    "10002": {
                        "name": "Seekabel",
                        "alias": "Seekabel",
                        "description": "Ein Seekabel (auch Unterseekabel, Unterwasserkabel) ist ein im Wesentlichen in einem Gewässer verlegtes Kabel zur Datenübertragung oder die Übertragung elektrischer Energie.",
                    },
                    "10003": {
                        "name": "Schutzrohr",
                        "alias": "Schutzrohr",
                        "description": "Im Schutzrohr verlegte oder zu verlegende Kabel/Leitungen. - Schutzrohre schützen erdverlegte Leitungen vor mechanischen Einflüssen und Feuchtigkeit.",
                    },
                    "10004": {
                        "name": "Leerrohr",
                        "alias": "Leerrohr (unbelegtes Schutzrohr)",
                        "description": "Über die Baumaßnahme hinaus unbelegtes Schutzrohr",
                    },
                    "10005": {
                        "name": "Leitungsbuendel",
                        "alias": "Leitungsbündel",
                        "description": "Bündel von Kabeln und/oder Schutzrohren in den Sparten Sparten Strom und Telekommunikation im Bestand",
                    },
                    "10006": {
                        "name": "Dueker",
                        "alias": "Düker",
                        "description": "Druckleitung zur Unterquerung von Straßen, Flüssen, Bahngleisen etc. Im Düker kann die Flüssigkeit das Hindernis überwinden, ohne dass Pumpen eingesetzt werden müssen.",
                    },
                    "2000": {
                        "name": "Oberirdisch",
                        "alias": "oberirdischer Verlauf",
                        "description": "Oberirdisch verlegte Leitungen und Rohre",
                    },
                    "20001": {
                        "name": "Freileitung",
                        "alias": "Freileitung",
                        "description": "Elektrische Leitung, deren spannungsführende Leiter im Freien durch die Luft geführt und meist auch nur durch die umgebende Luft voneinander und vom Erdboden isoliert sind. In der Regel werden die Leiterseile von Freileitungsmasten getragen, an denen sie mit Isolatoren befestigt sind.",
                    },
                    "20002": {
                        "name": "Heberleitung",
                        "alias": "Heberleitung",
                        "description": "Leitung zur Überquerung von Straßen oder zur Verbindung von Behältern (Gegenstück zu einem Düker)",
                    },
                    "20003": {
                        "name": "Rohrbruecke",
                        "alias": "Rohrbrücke",
                        "description": "Eine Rohrbrücke oder Rohrleitungsbrücke dient dazu, einzelne oder mehrere Rohrleitungen oberirdisch über größere Entfernungen zu führen.",
                    },
                },
                "typename": "XP_LeitungTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    nennweite: Annotated[
        str | None,
        Field(
            description='Die Nennweite DN ("diamètre nominal", "Durchmesser nach Norm") ist eine numerische Bezeichnung der ungefähren Durchmesser von Bauteilen in einem Rohrleitungssystem, die laut EN ISO 6708 "für Referenzzwecke verwendet wird".',
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    aussendurchmesser: Annotated[
        definitions.Length | None,
        Field(
            description="Außendurchmesser in m.\r\n(gml:LengthType: uom=“m“ oder uom=“urn:adv:uom:m“)",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    ueberdeckung: Annotated[
        definitions.Length | None,
        Field(
            description='Mindestüberdeckung (DIN) ist Abstand zwischen Oberkante der Verkehrsfläche und Oberkante des Rohres/Kabels in m. Die "Verlegetiefe" wird dagegen bis zur Grabensohle gemessen (s. Attribut grabentiefe). \r\nGilt nur für erdverlegte Linienobjekte.\r\n(gml:LengthType: uom=“m“ oder uom=“urn:adv:uom:m“)',
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    pufferzone3D: Annotated[
        definitions.Length | None,
        Field(
            description="Die Pufferzone definiert in einem 3D Modell einen rechteckigen Körper, in dem die Höhenlage einer Leitung variieren kann. Die obere Grenze des Puffers wird durch das Attribut Überdeckung definiert. Das hier einzutragende Maß ist die Distanz zur unteren Grenze des Puffers. Die Breite ergibt sich aus dem Attribut Nennweite oder Außendurchmesser.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    schutzzone3D: Annotated[
        definitions.Length | None,
        Field(
            description="Die Schutzzone definiert in einem 3D Modell einen quadratischen Körper um die Leitung. Der hier einzutragende Wert ist die Länge, die von vier Kreistangenten ausgehend den Abstand zu den waage- und senkrechten Kanten des Quadrats darstellt.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None


class BRAMikrorohr(BRALinienobjekt):
    """Mikrorohre (micro-ducts) nehmen Glasfaserkabel auf. Sie lassen sich (ergänzend) einem BRA_Mikrorohrverbund zuordnen oder können in ihrer Summe einen eigenständigen Verbund bilden."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    farbe: Annotated[
        Literal[
            "1000",
            "1100",
            "1200",
            "1300",
            "1400",
            "1500",
            "1600",
            "1700",
            "1800",
            "1900",
            "2000",
            "2100",
        ]
        | None,
        Field(
            description="Auswahl der Farbe",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Rot", "alias": "Rot", "description": "Rot"},
                    "1100": {"name": "Gruen", "alias": "Grün", "description": "Grün"},
                    "1200": {"name": "Blau", "alias": "Blau", "description": "Blau"},
                    "1300": {"name": "Gelb", "alias": "Gelb", "description": "Gelb"},
                    "1400": {"name": "Weiss", "alias": "Weiß", "description": "Weiß"},
                    "1500": {"name": "Grau", "alias": "Grau", "description": "Grau"},
                    "1600": {"name": "Braun", "alias": "Braun", "description": "Braun"},
                    "1700": {
                        "name": "Violett",
                        "alias": "Violett",
                        "description": "Violett",
                    },
                    "1800": {
                        "name": "Tuerkis",
                        "alias": "Türkis",
                        "description": "Türkis",
                    },
                    "1900": {
                        "name": "Schwarz",
                        "alias": "Schwarz",
                        "description": "Schwarz",
                    },
                    "2000": {
                        "name": "Orange",
                        "alias": "Orange",
                        "description": "Orange",
                    },
                    "2100": {"name": "Pink", "alias": "Pink", "description": "Pink"},
                },
                "typename": "BRA_Farbe",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    istReserveRohr: Annotated[
        bool | None,
        Field(
            description="Rohr ist ein Reserverohr und bleibt nach der Baumaßnahme unbelegt = true",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    werkstoff: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "2000",
            "20001",
            "20002",
            "20003",
            "2500",
            "25001",
            "25002",
            "25003",
            "25004",
            "25005",
            "3000",
            "30001",
            "30002",
            "4000",
            "5000",
            "9999",
        ]
        | None,
        Field(
            description="Werkstoff des Mikrorohrs",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Kunststoff",
                        "alias": "Kunststoff",
                        "description": "Kunststoff",
                    },
                    "10001": {
                        "name": "Polyethylen_PE",
                        "alias": "Polyethylen ( PE)",
                        "description": "Polyethylen (PE)",
                    },
                    "10002": {
                        "name": "Polyethylen_PE_HD",
                        "alias": "High-Density Polyethylen",
                        "description": "High-Density Polyethylen",
                    },
                    "10003": {
                        "name": "Polypropylen_PP",
                        "alias": "Polypropylen ( PP)",
                        "description": "Polypropylen (PP)",
                    },
                    "10004": {
                        "name": "Polycarbonat_PC",
                        "alias": "Polycarbonat ( PC)",
                        "description": "Polycarbonat (PC)",
                    },
                    "10005": {
                        "name": "Polyvinylchlorid_PVC_U",
                        "alias": "Polyvinylchlorid ( PVC- U)",
                        "description": "Polyvinylchlorid (PVC-U)",
                    },
                    "2000": {"name": "Stahl", "alias": "Stahl", "description": "Stahl"},
                    "20001": {
                        "name": "StahlVerzinkt",
                        "alias": "Stahl verzinkt",
                        "description": "Stahl verzinkt",
                    },
                    "20002": {
                        "name": "Stahlgitter",
                        "alias": "Stahlgitter",
                        "description": "Stahlfachwerkskonstruktion (z.B. Freileitungsmast als Gittermast)",
                    },
                    "20003": {
                        "name": "Stahlrohr",
                        "alias": "Stahlrohr",
                        "description": "Rohrförmiger Profilstahl, dessen Wand aus Stahl besteht. Stahlrohre dienen der Durchleitung von flüssigen, gasförmigen oder festen Stoffen, oder werden als statische oder konstruktive Elemente verwendet (z.B. Freileitungsmast als Stahlrohrmast)",
                    },
                    "2500": {
                        "name": "Stahlverbundrohr",
                        "alias": "Stahlverbundrohr",
                        "description": "Stahlverbundrohre im Rohrleitungsbau",
                    },
                    "25001": {
                        "name": "St_PE",
                        "alias": "Stahlrohr mit Standard-Kunststoffumhüllung (PE)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PE-Basis",
                    },
                    "25002": {
                        "name": "St_PP",
                        "alias": "Stahlrohr mit Kunstoffumhüllung (PP)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PP-Basis für höhere Temperatur- und Härte-Anforderungen",
                    },
                    "25003": {
                        "name": "St_FZM",
                        "alias": "Stahlrohr mit FZM-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz durch Faserzementmörtel-Ummantelung (FZM)",
                    },
                    "25004": {
                        "name": "St_GFK",
                        "alias": "Stahlrohr mit GFK-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz aus glasfaserverstärktem Kunststoff (GFK) für höchste mechanische Abriebfestigkeit bei grabenlosem Rohrvortrieb",
                    },
                    "25005": {
                        "name": "St_ZM_PE",
                        "alias": "Stahl-Verbundrohr (ZM-PE)",
                        "description": "Stahlrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserohr)",
                    },
                    "3000": {
                        "name": "Gusseisen",
                        "alias": "Gusseisen",
                        "description": "Gusseisen",
                    },
                    "30001": {
                        "name": "GGG_ZM",
                        "alias": "duktiles Gussrohr mit ZM-Auskleidung",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung (z.B Abwasserrohr)",
                    },
                    "30002": {
                        "name": "GGG_ZM_PE",
                        "alias": "duktiles Guss-Verbundrohr (ZM-PE)",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserrohr)",
                    },
                    "4000": {
                        "name": "Beton",
                        "alias": "Beton",
                        "description": "Beton (z.B. Schacht)",
                    },
                    "5000": {
                        "name": "Holz",
                        "alias": "Holz",
                        "description": "Holz (z.B. Holzmast)",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiger Werkstoff",
                        "description": "Sonstiger Werkstoff",
                    },
                },
                "typename": "XP_Werkstoff",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    rohrtyp: Annotated[
        Literal[
            "1100",
            "1200",
            "2100",
            "2200",
            "3100",
            "3200",
            "4100",
            "4200",
            "5100",
            "5200",
            "6100",
            "6200",
            "9999",
        ]
        | None,
        Field(
            description="Art des Mikrorohrs in Bezug auf Durchmesser (DN) und Wandstärke",
            json_schema_extra={
                "enumDescription": {
                    "1100": {
                        "name": "7x0,75",
                        "alias": "7x0,75",
                        "description": "7x0,75",
                    },
                    "1200": {"name": "7x1,5", "alias": "7x1,5", "description": "7x1,5"},
                    "2100": {
                        "name": "10x1,0",
                        "alias": "10x1,0",
                        "description": "10x1,0",
                    },
                    "2200": {
                        "name": "10x2,0",
                        "alias": "10x2,0",
                        "description": "10x2,0",
                    },
                    "3100": {
                        "name": "12x1,1",
                        "alias": "12x1,1",
                        "description": "12x1,1",
                    },
                    "3200": {
                        "name": "12x2,0",
                        "alias": "12x2,0",
                        "description": "12x2,0",
                    },
                    "4100": {
                        "name": "14x1,3",
                        "alias": "14x1,3",
                        "description": "14x1,3",
                    },
                    "4200": {
                        "name": "14x2,0",
                        "alias": "14x2,0",
                        "description": "14x2,0",
                    },
                    "5100": {
                        "name": "16x1,5",
                        "alias": "16x1,5",
                        "description": "16x1,5",
                    },
                    "5200": {
                        "name": "16x2,0",
                        "alias": "16x2,0",
                        "description": "16x2,0",
                    },
                    "6100": {
                        "name": "20x2.0",
                        "alias": "20x2.0",
                        "description": "20x2.0",
                    },
                    "6200": {
                        "name": "20x2,5",
                        "alias": "20x2,5",
                        "description": "20x2,5",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "Sonstiges",
                        "description": "Sonstiges",
                    },
                },
                "typename": "BRA_MikrorohrTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    mikrorohrverbund: Annotated[
        AnyUrl | UUID | None,
        Field(
            description="Referenz auf den Verbund, zu dem das Mikrorohr gehört",
            json_schema_extra={
                "typename": "BRA_Mikrorohrverbund",
                "stereotype": "Association",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    schutzrohr: Annotated[
        AnyUrl | UUID | None,
        Field(
            description="Referenz auf das Schutzrohr, in dem sich das Mikrorohr befindet bzw. verlegt wird",
            json_schema_extra={
                "typename": "BRA_Schutzrohr",
                "stereotype": "Association",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BRAMikrorohrverbund(BRALinienobjekt):
    """Verbund von Mikrorohren in einer oder zwei Größen, der von einem Hüllrohr umschlossen ist.  Die einzelnen Mikrorohre (micro-ducts) nehmen Glasfaserkabel auf, was über BRA_Kabel im Ausbauplan dargestellt werden kann. Bleiben die Mirkorohre ohne Belegung, heißt dies in der Regel, dass nach Abschluss der Baumaßnahme Glasfaserkabel "eingeblasen" werden.  Ein Mikrorohrverbund wird in ein BRA_Schutzrohr gelegt."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    anzahlMikrorohr1: Annotated[
        int | None,
        Field(
            description="Anzahl der Mikrorohre im Rohrverbund (gleicher Größe)",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    anzahlMikrorohr2: Annotated[
        int | None,
        Field(
            description="Anzahl der Mikrorohre im Rohrverbund (gleicher Größe), wenn der Verbund zwei unterschiedliche Größen umfasst.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    davonReserveRohre: Annotated[
        int | None,
        Field(
            description="Anzahl der Rohre, die als Reserve eingeplant werden. (Nach der Verlegung werden keine Kabel eingeblasen).",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    artMikrorohr1: Annotated[
        Literal[
            "1100",
            "1200",
            "2100",
            "2200",
            "3100",
            "3200",
            "4100",
            "4200",
            "5100",
            "5200",
            "6100",
            "6200",
            "9999",
        ]
        | None,
        Field(
            description="Auswahl Mikrorohr1 in Bezug auf Außendurchmesser und Wandstärke",
            json_schema_extra={
                "enumDescription": {
                    "1100": {
                        "name": "7x0,75",
                        "alias": "7x0,75",
                        "description": "7x0,75",
                    },
                    "1200": {"name": "7x1,5", "alias": "7x1,5", "description": "7x1,5"},
                    "2100": {
                        "name": "10x1,0",
                        "alias": "10x1,0",
                        "description": "10x1,0",
                    },
                    "2200": {
                        "name": "10x2,0",
                        "alias": "10x2,0",
                        "description": "10x2,0",
                    },
                    "3100": {
                        "name": "12x1,1",
                        "alias": "12x1,1",
                        "description": "12x1,1",
                    },
                    "3200": {
                        "name": "12x2,0",
                        "alias": "12x2,0",
                        "description": "12x2,0",
                    },
                    "4100": {
                        "name": "14x1,3",
                        "alias": "14x1,3",
                        "description": "14x1,3",
                    },
                    "4200": {
                        "name": "14x2,0",
                        "alias": "14x2,0",
                        "description": "14x2,0",
                    },
                    "5100": {
                        "name": "16x1,5",
                        "alias": "16x1,5",
                        "description": "16x1,5",
                    },
                    "5200": {
                        "name": "16x2,0",
                        "alias": "16x2,0",
                        "description": "16x2,0",
                    },
                    "6100": {
                        "name": "20x2.0",
                        "alias": "20x2.0",
                        "description": "20x2.0",
                    },
                    "6200": {
                        "name": "20x2,5",
                        "alias": "20x2,5",
                        "description": "20x2,5",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "Sonstiges",
                        "description": "Sonstiges",
                    },
                },
                "typename": "BRA_MikrorohrTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    artMikrorohr2: Annotated[
        Literal[
            "1100",
            "1200",
            "2100",
            "2200",
            "3100",
            "3200",
            "4100",
            "4200",
            "5100",
            "5200",
            "6100",
            "6200",
            "9999",
        ]
        | None,
        Field(
            description="Auswahl Mikrorohr2 in Bezug auf Außendurchmesser und Wandstärke",
            json_schema_extra={
                "enumDescription": {
                    "1100": {
                        "name": "7x0,75",
                        "alias": "7x0,75",
                        "description": "7x0,75",
                    },
                    "1200": {"name": "7x1,5", "alias": "7x1,5", "description": "7x1,5"},
                    "2100": {
                        "name": "10x1,0",
                        "alias": "10x1,0",
                        "description": "10x1,0",
                    },
                    "2200": {
                        "name": "10x2,0",
                        "alias": "10x2,0",
                        "description": "10x2,0",
                    },
                    "3100": {
                        "name": "12x1,1",
                        "alias": "12x1,1",
                        "description": "12x1,1",
                    },
                    "3200": {
                        "name": "12x2,0",
                        "alias": "12x2,0",
                        "description": "12x2,0",
                    },
                    "4100": {
                        "name": "14x1,3",
                        "alias": "14x1,3",
                        "description": "14x1,3",
                    },
                    "4200": {
                        "name": "14x2,0",
                        "alias": "14x2,0",
                        "description": "14x2,0",
                    },
                    "5100": {
                        "name": "16x1,5",
                        "alias": "16x1,5",
                        "description": "16x1,5",
                    },
                    "5200": {
                        "name": "16x2,0",
                        "alias": "16x2,0",
                        "description": "16x2,0",
                    },
                    "6100": {
                        "name": "20x2.0",
                        "alias": "20x2.0",
                        "description": "20x2.0",
                    },
                    "6200": {
                        "name": "20x2,5",
                        "alias": "20x2,5",
                        "description": "20x2,5",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "Sonstiges",
                        "description": "Sonstiges",
                    },
                },
                "typename": "BRA_MikrorohrTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    farbe: Annotated[
        Literal[
            "1000",
            "1100",
            "1200",
            "1300",
            "1400",
            "1500",
            "1600",
            "1700",
            "1800",
            "1900",
            "2000",
            "2100",
        ]
        | None,
        Field(
            description="Auswahl der Farbe des äußeren Hüllrohrs",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Rot", "alias": "Rot", "description": "Rot"},
                    "1100": {"name": "Gruen", "alias": "Grün", "description": "Grün"},
                    "1200": {"name": "Blau", "alias": "Blau", "description": "Blau"},
                    "1300": {"name": "Gelb", "alias": "Gelb", "description": "Gelb"},
                    "1400": {"name": "Weiss", "alias": "Weiß", "description": "Weiß"},
                    "1500": {"name": "Grau", "alias": "Grau", "description": "Grau"},
                    "1600": {"name": "Braun", "alias": "Braun", "description": "Braun"},
                    "1700": {
                        "name": "Violett",
                        "alias": "Violett",
                        "description": "Violett",
                    },
                    "1800": {
                        "name": "Tuerkis",
                        "alias": "Türkis",
                        "description": "Türkis",
                    },
                    "1900": {
                        "name": "Schwarz",
                        "alias": "Schwarz",
                        "description": "Schwarz",
                    },
                    "2000": {
                        "name": "Orange",
                        "alias": "Orange",
                        "description": "Orange",
                    },
                    "2100": {"name": "Pink", "alias": "Pink", "description": "Pink"},
                },
                "typename": "BRA_Farbe",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    werkstoff: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "2000",
            "20001",
            "20002",
            "20003",
            "2500",
            "25001",
            "25002",
            "25003",
            "25004",
            "25005",
            "3000",
            "30001",
            "30002",
            "4000",
            "5000",
            "9999",
        ]
        | None,
        Field(
            description="Werkstoff des Mikrorohrverbunds",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Kunststoff",
                        "alias": "Kunststoff",
                        "description": "Kunststoff",
                    },
                    "10001": {
                        "name": "Polyethylen_PE",
                        "alias": "Polyethylen ( PE)",
                        "description": "Polyethylen (PE)",
                    },
                    "10002": {
                        "name": "Polyethylen_PE_HD",
                        "alias": "High-Density Polyethylen",
                        "description": "High-Density Polyethylen",
                    },
                    "10003": {
                        "name": "Polypropylen_PP",
                        "alias": "Polypropylen ( PP)",
                        "description": "Polypropylen (PP)",
                    },
                    "10004": {
                        "name": "Polycarbonat_PC",
                        "alias": "Polycarbonat ( PC)",
                        "description": "Polycarbonat (PC)",
                    },
                    "10005": {
                        "name": "Polyvinylchlorid_PVC_U",
                        "alias": "Polyvinylchlorid ( PVC- U)",
                        "description": "Polyvinylchlorid (PVC-U)",
                    },
                    "2000": {"name": "Stahl", "alias": "Stahl", "description": "Stahl"},
                    "20001": {
                        "name": "StahlVerzinkt",
                        "alias": "Stahl verzinkt",
                        "description": "Stahl verzinkt",
                    },
                    "20002": {
                        "name": "Stahlgitter",
                        "alias": "Stahlgitter",
                        "description": "Stahlfachwerkskonstruktion (z.B. Freileitungsmast als Gittermast)",
                    },
                    "20003": {
                        "name": "Stahlrohr",
                        "alias": "Stahlrohr",
                        "description": "Rohrförmiger Profilstahl, dessen Wand aus Stahl besteht. Stahlrohre dienen der Durchleitung von flüssigen, gasförmigen oder festen Stoffen, oder werden als statische oder konstruktive Elemente verwendet (z.B. Freileitungsmast als Stahlrohrmast)",
                    },
                    "2500": {
                        "name": "Stahlverbundrohr",
                        "alias": "Stahlverbundrohr",
                        "description": "Stahlverbundrohre im Rohrleitungsbau",
                    },
                    "25001": {
                        "name": "St_PE",
                        "alias": "Stahlrohr mit Standard-Kunststoffumhüllung (PE)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PE-Basis",
                    },
                    "25002": {
                        "name": "St_PP",
                        "alias": "Stahlrohr mit Kunstoffumhüllung (PP)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PP-Basis für höhere Temperatur- und Härte-Anforderungen",
                    },
                    "25003": {
                        "name": "St_FZM",
                        "alias": "Stahlrohr mit FZM-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz durch Faserzementmörtel-Ummantelung (FZM)",
                    },
                    "25004": {
                        "name": "St_GFK",
                        "alias": "Stahlrohr mit GFK-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz aus glasfaserverstärktem Kunststoff (GFK) für höchste mechanische Abriebfestigkeit bei grabenlosem Rohrvortrieb",
                    },
                    "25005": {
                        "name": "St_ZM_PE",
                        "alias": "Stahl-Verbundrohr (ZM-PE)",
                        "description": "Stahlrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserohr)",
                    },
                    "3000": {
                        "name": "Gusseisen",
                        "alias": "Gusseisen",
                        "description": "Gusseisen",
                    },
                    "30001": {
                        "name": "GGG_ZM",
                        "alias": "duktiles Gussrohr mit ZM-Auskleidung",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung (z.B Abwasserrohr)",
                    },
                    "30002": {
                        "name": "GGG_ZM_PE",
                        "alias": "duktiles Guss-Verbundrohr (ZM-PE)",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserrohr)",
                    },
                    "4000": {
                        "name": "Beton",
                        "alias": "Beton",
                        "description": "Beton (z.B. Schacht)",
                    },
                    "5000": {
                        "name": "Holz",
                        "alias": "Holz",
                        "description": "Holz (z.B. Holzmast)",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiger Werkstoff",
                        "description": "Sonstiger Werkstoff",
                    },
                },
                "typename": "XP_Werkstoff",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    master: Annotated[
        bool | None,
        Field(
            description="Verbund ist äußeres Rohr = true (wird nicht im Schutzrohr verlegt)",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    schutzrohr: Annotated[
        AnyUrl | UUID | None,
        Field(
            description="Referenz auf das Schutzrohr, in dem sich der Mikrorohrverbund befindet bzw. verlegt wird",
            json_schema_extra={
                "typename": "BRA_Schutzrohr",
                "stereotype": "Association",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BRAMultiFlaechenobjekt(BRAObjekt):
    """Oberklasse der Objekte eines Breitband-Ausbauplans mit Flächengeometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiPolygon,
        Field(
            description="Raumbezug des Objektes",
            json_schema_extra={
                "typename": "GM_MultiSurface",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class BRAMultiPunktobjekt(BRAObjekt):
    """Oberklasse der Objekte eines Breitband-Ausbauplans mit Punktgeometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiPoint,
        Field(
            description="Raumbezug des Objektes",
            json_schema_extra={
                "typename": "GM_MultiPoint",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class BRARohrmuffe(BRAMultiPunktobjekt):
    """Rohrmuffe im Breitband-Netz"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Auswahl der Rohrverbindung",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Abzweigemuffe",
                        "alias": "Abzweigemuffe",
                        "description": "Abzweigemuffe",
                    },
                    "2000": {
                        "name": "Verbindungsmuffe",
                        "alias": "Verbindungsmuffe",
                        "description": "Verbindungsmuffe",
                    },
                    "3000": {
                        "name": "Endmuffe",
                        "alias": "Endmuffe",
                        "description": "Endmuffe",
                    },
                },
                "typename": "BRA_RohrmuffeTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BRASchacht(BRAMultiPunktobjekt):
    """Schacht eines Breitband-Netzes"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class BRASchutzrohr(BRALinienobjekt):
    """Kabelschutzrohre dienen in der Erdverlegung als drucklose Leitungen, die Kabel oder Mikrorohre gegen mechanische Beschädigungen schützen. In einem BRA_Ausbauplan wird der räumliche Verlauf der Schutzrohre durch den Verlauf der BRA_BreitbandtrasseAbschnitte vorgegeben. Eine Aufteilung der Schutzrohre in Abschnitte ist nicht erforderlich."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    istReserveRohr: Annotated[
        bool | None,
        Field(
            description="Rohr ist ein Reserverohr und bleibt nach der Baumaßnahme unbelegt = true",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    master: Annotated[
        bool | None,
        Field(
            description="Schutzrohr ist äußerstes Rohr im Rohrsystem = true",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    werkstoff: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "2000",
            "20001",
            "20002",
            "20003",
            "2500",
            "25001",
            "25002",
            "25003",
            "25004",
            "25005",
            "3000",
            "30001",
            "30002",
            "4000",
            "5000",
            "9999",
        ]
        | None,
        Field(
            description="Werkstoff des Schutzrohres",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Kunststoff",
                        "alias": "Kunststoff",
                        "description": "Kunststoff",
                    },
                    "10001": {
                        "name": "Polyethylen_PE",
                        "alias": "Polyethylen ( PE)",
                        "description": "Polyethylen (PE)",
                    },
                    "10002": {
                        "name": "Polyethylen_PE_HD",
                        "alias": "High-Density Polyethylen",
                        "description": "High-Density Polyethylen",
                    },
                    "10003": {
                        "name": "Polypropylen_PP",
                        "alias": "Polypropylen ( PP)",
                        "description": "Polypropylen (PP)",
                    },
                    "10004": {
                        "name": "Polycarbonat_PC",
                        "alias": "Polycarbonat ( PC)",
                        "description": "Polycarbonat (PC)",
                    },
                    "10005": {
                        "name": "Polyvinylchlorid_PVC_U",
                        "alias": "Polyvinylchlorid ( PVC- U)",
                        "description": "Polyvinylchlorid (PVC-U)",
                    },
                    "2000": {"name": "Stahl", "alias": "Stahl", "description": "Stahl"},
                    "20001": {
                        "name": "StahlVerzinkt",
                        "alias": "Stahl verzinkt",
                        "description": "Stahl verzinkt",
                    },
                    "20002": {
                        "name": "Stahlgitter",
                        "alias": "Stahlgitter",
                        "description": "Stahlfachwerkskonstruktion (z.B. Freileitungsmast als Gittermast)",
                    },
                    "20003": {
                        "name": "Stahlrohr",
                        "alias": "Stahlrohr",
                        "description": "Rohrförmiger Profilstahl, dessen Wand aus Stahl besteht. Stahlrohre dienen der Durchleitung von flüssigen, gasförmigen oder festen Stoffen, oder werden als statische oder konstruktive Elemente verwendet (z.B. Freileitungsmast als Stahlrohrmast)",
                    },
                    "2500": {
                        "name": "Stahlverbundrohr",
                        "alias": "Stahlverbundrohr",
                        "description": "Stahlverbundrohre im Rohrleitungsbau",
                    },
                    "25001": {
                        "name": "St_PE",
                        "alias": "Stahlrohr mit Standard-Kunststoffumhüllung (PE)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PE-Basis",
                    },
                    "25002": {
                        "name": "St_PP",
                        "alias": "Stahlrohr mit Kunstoffumhüllung (PP)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PP-Basis für höhere Temperatur- und Härte-Anforderungen",
                    },
                    "25003": {
                        "name": "St_FZM",
                        "alias": "Stahlrohr mit FZM-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz durch Faserzementmörtel-Ummantelung (FZM)",
                    },
                    "25004": {
                        "name": "St_GFK",
                        "alias": "Stahlrohr mit GFK-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz aus glasfaserverstärktem Kunststoff (GFK) für höchste mechanische Abriebfestigkeit bei grabenlosem Rohrvortrieb",
                    },
                    "25005": {
                        "name": "St_ZM_PE",
                        "alias": "Stahl-Verbundrohr (ZM-PE)",
                        "description": "Stahlrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserohr)",
                    },
                    "3000": {
                        "name": "Gusseisen",
                        "alias": "Gusseisen",
                        "description": "Gusseisen",
                    },
                    "30001": {
                        "name": "GGG_ZM",
                        "alias": "duktiles Gussrohr mit ZM-Auskleidung",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung (z.B Abwasserrohr)",
                    },
                    "30002": {
                        "name": "GGG_ZM_PE",
                        "alias": "duktiles Guss-Verbundrohr (ZM-PE)",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserrohr)",
                    },
                    "4000": {
                        "name": "Beton",
                        "alias": "Beton",
                        "description": "Beton (z.B. Schacht)",
                    },
                    "5000": {
                        "name": "Holz",
                        "alias": "Holz",
                        "description": "Holz (z.B. Holzmast)",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiger Werkstoff",
                        "description": "Sonstiger Werkstoff",
                    },
                },
                "typename": "XP_Werkstoff",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    rohrtyp: Annotated[
        Literal[
            "03218",
            "03229",
            "03240",
            "04019",
            "04037",
            "04040",
            "05018",
            "05024",
            "05040",
            "05046",
            "06319",
            "06330",
            "06347",
            "07522",
            "07536",
            "08525",
            "09027",
            "09043",
            "11032",
            "11034",
            "11037",
            "11042",
            "11053",
            "11063",
            "12537",
            "12539",
            "12548",
            "12560",
            "12571",
            "14041",
            "14067",
            "16047",
            "16049",
            "16062",
            "16077",
            "16091",
            "99999",
        ]
        | None,
        Field(
            description="Rohrtyp in Bezug auf Durchmesser (DN) und Wandstärke",
            json_schema_extra={
                "enumDescription": {
                    "03218": {
                        "name": "32x1,8",
                        "alias": "32x1,8",
                        "description": "32x1,8",
                    },
                    "03229": {
                        "name": "32x2,9",
                        "alias": "32x2,9",
                        "description": "32x2,9",
                    },
                    "03240": {
                        "name": "32x4,0",
                        "alias": "32x4,0",
                        "description": "32x4,0",
                    },
                    "04019": {
                        "name": "40x1,9",
                        "alias": "40x1,9",
                        "description": "40x1,9",
                    },
                    "04037": {
                        "name": "40x3,7",
                        "alias": "40x3,7",
                        "description": "40x3,7",
                    },
                    "04040": {
                        "name": "40x4,0",
                        "alias": "40x4,0",
                        "description": "40x4,0",
                    },
                    "05018": {
                        "name": "50x1,8",
                        "alias": "50x1,8",
                        "description": "50x1,8",
                    },
                    "05024": {
                        "name": "50x2,4",
                        "alias": "50x2,4",
                        "description": "50x2,4",
                    },
                    "05040": {
                        "name": "50x4,0",
                        "alias": "50x4,0",
                        "description": "50x4,0",
                    },
                    "05046": {
                        "name": "50x4,6",
                        "alias": "50x4,6",
                        "description": "50x4,6",
                    },
                    "06319": {
                        "name": "63x1,9",
                        "alias": "63x1,9",
                        "description": "63x1,9",
                    },
                    "06330": {
                        "name": "63x3,0",
                        "alias": "63x3,0",
                        "description": "63x3,0",
                    },
                    "06347": {
                        "name": "63x4,7",
                        "alias": "63x4,7",
                        "description": "63x4,7",
                    },
                    "07522": {
                        "name": "75x2,2",
                        "alias": "75x2,2",
                        "description": "75x2,2",
                    },
                    "07536": {
                        "name": "75x3,6",
                        "alias": "75x3,6",
                        "description": "75x3,6",
                    },
                    "08525": {
                        "name": "85x2,5",
                        "alias": "85x2,5",
                        "description": "85x2,5",
                    },
                    "09027": {
                        "name": "90x2,7",
                        "alias": "90x2,7",
                        "description": "90x2,7",
                    },
                    "09043": {
                        "name": "90x4,3",
                        "alias": "90x4,3",
                        "description": "90x4,3",
                    },
                    "11032": {
                        "name": "110x3,2",
                        "alias": "110x3,2",
                        "description": "110x3,2",
                    },
                    "11034": {
                        "name": "110x3,4",
                        "alias": "110x3,4",
                        "description": "110x3,4",
                    },
                    "11037": {
                        "name": "110x3,7",
                        "alias": "110x3,7",
                        "description": "110x3,7",
                    },
                    "11042": {
                        "name": "110x4,2",
                        "alias": "110x4,2",
                        "description": "110x4,2",
                    },
                    "11053": {
                        "name": "110x5,3",
                        "alias": "110x5,3",
                        "description": "110x5,3",
                    },
                    "11063": {
                        "name": "110x6,3",
                        "alias": "110x6,3",
                        "description": "110x6,3",
                    },
                    "12537": {
                        "name": "125x3,7",
                        "alias": "125x3,7",
                        "description": "125x3,7",
                    },
                    "12539": {
                        "name": "125x3,9",
                        "alias": "125x3,9",
                        "description": "125x3,9",
                    },
                    "12548": {
                        "name": "125x4,8",
                        "alias": "125x4,8",
                        "description": "125x4,8",
                    },
                    "12560": {
                        "name": "125x6,0",
                        "alias": "125x6,0",
                        "description": "125x6,0",
                    },
                    "12571": {
                        "name": "125x7,1",
                        "alias": "125x7,1",
                        "description": "125x7,1",
                    },
                    "14041": {
                        "name": "140x4,1",
                        "alias": "140x4,1",
                        "description": "140x4,1",
                    },
                    "14067": {
                        "name": "140x6,7",
                        "alias": "140x6,7",
                        "description": "140x6,7",
                    },
                    "16047": {
                        "name": "160x4,7",
                        "alias": "160x4,7",
                        "description": "160x4,7",
                    },
                    "16049": {
                        "name": "160x4,9",
                        "alias": "160x4,9",
                        "description": "160x4,9",
                    },
                    "16062": {
                        "name": "160x6,2",
                        "alias": "160x6,2",
                        "description": "160x6,2",
                    },
                    "16077": {
                        "name": "160x7,7",
                        "alias": "160x7,7",
                        "description": "160x7,7",
                    },
                    "16091": {
                        "name": "160x9,1",
                        "alias": "160x9,1",
                        "description": "160x9,1",
                    },
                    "99999": {
                        "name": "Sonstiges",
                        "alias": "Sonstiges",
                        "description": "Sonstiges",
                    },
                },
                "typename": "BRA_SchutzrohrTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    farbe: Annotated[
        Literal[
            "1000",
            "1100",
            "1200",
            "1300",
            "1400",
            "1500",
            "1600",
            "1700",
            "1800",
            "1900",
            "2000",
            "2100",
        ]
        | None,
        Field(
            description="Auswahl der Farbe",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Rot", "alias": "Rot", "description": "Rot"},
                    "1100": {"name": "Gruen", "alias": "Grün", "description": "Grün"},
                    "1200": {"name": "Blau", "alias": "Blau", "description": "Blau"},
                    "1300": {"name": "Gelb", "alias": "Gelb", "description": "Gelb"},
                    "1400": {"name": "Weiss", "alias": "Weiß", "description": "Weiß"},
                    "1500": {"name": "Grau", "alias": "Grau", "description": "Grau"},
                    "1600": {"name": "Braun", "alias": "Braun", "description": "Braun"},
                    "1700": {
                        "name": "Violett",
                        "alias": "Violett",
                        "description": "Violett",
                    },
                    "1800": {
                        "name": "Tuerkis",
                        "alias": "Türkis",
                        "description": "Türkis",
                    },
                    "1900": {
                        "name": "Schwarz",
                        "alias": "Schwarz",
                        "description": "Schwarz",
                    },
                    "2000": {
                        "name": "Orange",
                        "alias": "Orange",
                        "description": "Orange",
                    },
                    "2100": {"name": "Pink", "alias": "Pink", "description": "Pink"},
                },
                "typename": "BRA_Farbe",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BRAUmfeld(BRAMultiFlaechenobjekt):
    """Hervorzuhebende Flächenobjekte im Straßenraum"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal["1000", "2000", "9999"],
        Field(
            description="Auswahl der darzustellenden Flächenart",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Abstandsflaeche",
                        "alias": "Abstandsfläche",
                        "description": "Fläche zur Markierung von Abständen zwischen bestimmten Objekten",
                    },
                    "2000": {
                        "name": "Verkehsflaeche",
                        "alias": "Verkehsfläche",
                        "description": "Fläche zur Markierung einer vorhandenen Verkehrsfläche",
                    },
                    "9999": {
                        "name": "sonstigeFlaeche",
                        "alias": "sonstige Fläche",
                        "description": "Markierung einer sonstigen Fläche",
                    },
                },
                "typename": "BRA_UmfeldTyp",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]


class BRAVerteiler(BRAMultiPunktobjekt):
    """Verteiler des Breitband-Netzes"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "10003",
            "2000",
            "20001",
            "20002",
            "20003",
            "20004",
            "9999",
        ]
        | None,
        Field(
            description="Auswahl der Gehäuse und Bauten",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "TK_Verteiler",
                        "alias": "TK-Verteiler",
                        "description": "Verteilerschränke der Telekommunikation",
                    },
                    "10001": {
                        "name": "Multifunktionsgehaeuse",
                        "alias": "Multifunktionsgehäuse",
                        "description": "Multifunktionsgehäuse",
                    },
                    "10002": {
                        "name": "GlasfaserNetzverteiler",
                        "alias": "Glasfaser-Netzverteiler (Gf- NVt)",
                        "description": "Glasfaser-Netzverteiler (Gf-NVt)",
                    },
                    "10003": {
                        "name": "Kabelverzweiger_KVz",
                        "alias": "Kabelverzweiger ( KVz) - (Telekom  AG)",
                        "description": "Kabelverzweiger (KVz) - (Telekom AG)",
                    },
                    "2000": {
                        "name": "Strom_Schrank",
                        "alias": "Strom-Schrank",
                        "description": "Schränke für die Stromversorgung, öffentliche Beleuchtung, Verkehrstechnik u.a.",
                    },
                    "20001": {
                        "name": "Schaltschrank",
                        "alias": "Schaltschrank",
                        "description": "Schaltschrank",
                    },
                    "20002": {
                        "name": "Kabelverteilerschrank",
                        "alias": "Kabelverteilerschrank",
                        "description": "Kabelverteilerschrank",
                    },
                    "20003": {
                        "name": "Steuerschrank",
                        "alias": "Steuerschrank",
                        "description": "Steuerschrank",
                    },
                    "20004": {
                        "name": "Trennschrank",
                        "alias": "Trennschrank",
                        "description": "Trennschrank",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiger Schrank",
                        "description": "sonstiger Schrank",
                    },
                },
                "typename": "XP_GehaeuseTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    technik: Annotated[
        Literal[
            "1000",
            "2000",
            "3000",
            "4000",
            "5000",
            "6000",
            "7000",
            "8000",
            "9000",
            "9999",
        ]
        | None,
        Field(
            description="Auswahl der aktiven oder passiven Netztechnik",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Hauptverteiler_HVt",
                        "alias": "Hauptverteiler ( HVt) - konventionell",
                        "description": "Hauptverteiler (HVt) - konventionell",
                    },
                    "2000": {
                        "name": "GlasfaserHVt_PoP",
                        "alias": "Glasfaser-HVt/ PoP",
                        "description": "Glasfaser-HVt/ PoP",
                    },
                    "3000": {
                        "name": "DSLAM_MSAN",
                        "alias": "DSLAM/ MSAN",
                        "description": "DSLAM/MSAN",
                    },
                    "4000": {
                        "name": "GlasfaserVerteiler",
                        "alias": "Glasfaser-Verteiler",
                        "description": "Glasfaser-Verteiler",
                    },
                    "5000": {
                        "name": "Kabelmuffe",
                        "alias": "Kabelmuffe",
                        "description": "Kabelmuffe",
                    },
                    "6000": {
                        "name": "Hausuebergabepunkt_APL",
                        "alias": "Hausübergabepunkt/ APL",
                        "description": "Hausübergabepunkt/ APL",
                    },
                    "7000": {
                        "name": "UebergabepunktBackbone",
                        "alias": "Übergabepunkt Backbone",
                        "description": "Übergabepunkt Backbone",
                    },
                    "8000": {
                        "name": "OpticalLineTermination_OLT",
                        "alias": "Optical Line Termination (OLT)",
                        "description": "Optical Line Termination (OLT)",
                    },
                    "9000": {
                        "name": "OptischerSplitter",
                        "alias": "Optischer  Splitter",
                        "description": "Optischer Splitter",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "Sonstiges",
                        "description": "Sonstiges",
                    },
                },
                "typename": "BRA_Netztechnik",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    werkstoff: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "2000",
            "20001",
            "20002",
            "20003",
            "2500",
            "25001",
            "25002",
            "25003",
            "25004",
            "25005",
            "3000",
            "30001",
            "30002",
            "4000",
            "5000",
            "9999",
        ]
        | None,
        Field(
            description="Werkstoff des Verteilers",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Kunststoff",
                        "alias": "Kunststoff",
                        "description": "Kunststoff",
                    },
                    "10001": {
                        "name": "Polyethylen_PE",
                        "alias": "Polyethylen ( PE)",
                        "description": "Polyethylen (PE)",
                    },
                    "10002": {
                        "name": "Polyethylen_PE_HD",
                        "alias": "High-Density Polyethylen",
                        "description": "High-Density Polyethylen",
                    },
                    "10003": {
                        "name": "Polypropylen_PP",
                        "alias": "Polypropylen ( PP)",
                        "description": "Polypropylen (PP)",
                    },
                    "10004": {
                        "name": "Polycarbonat_PC",
                        "alias": "Polycarbonat ( PC)",
                        "description": "Polycarbonat (PC)",
                    },
                    "10005": {
                        "name": "Polyvinylchlorid_PVC_U",
                        "alias": "Polyvinylchlorid ( PVC- U)",
                        "description": "Polyvinylchlorid (PVC-U)",
                    },
                    "2000": {"name": "Stahl", "alias": "Stahl", "description": "Stahl"},
                    "20001": {
                        "name": "StahlVerzinkt",
                        "alias": "Stahl verzinkt",
                        "description": "Stahl verzinkt",
                    },
                    "20002": {
                        "name": "Stahlgitter",
                        "alias": "Stahlgitter",
                        "description": "Stahlfachwerkskonstruktion (z.B. Freileitungsmast als Gittermast)",
                    },
                    "20003": {
                        "name": "Stahlrohr",
                        "alias": "Stahlrohr",
                        "description": "Rohrförmiger Profilstahl, dessen Wand aus Stahl besteht. Stahlrohre dienen der Durchleitung von flüssigen, gasförmigen oder festen Stoffen, oder werden als statische oder konstruktive Elemente verwendet (z.B. Freileitungsmast als Stahlrohrmast)",
                    },
                    "2500": {
                        "name": "Stahlverbundrohr",
                        "alias": "Stahlverbundrohr",
                        "description": "Stahlverbundrohre im Rohrleitungsbau",
                    },
                    "25001": {
                        "name": "St_PE",
                        "alias": "Stahlrohr mit Standard-Kunststoffumhüllung (PE)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PE-Basis",
                    },
                    "25002": {
                        "name": "St_PP",
                        "alias": "Stahlrohr mit Kunstoffumhüllung (PP)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PP-Basis für höhere Temperatur- und Härte-Anforderungen",
                    },
                    "25003": {
                        "name": "St_FZM",
                        "alias": "Stahlrohr mit FZM-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz durch Faserzementmörtel-Ummantelung (FZM)",
                    },
                    "25004": {
                        "name": "St_GFK",
                        "alias": "Stahlrohr mit GFK-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz aus glasfaserverstärktem Kunststoff (GFK) für höchste mechanische Abriebfestigkeit bei grabenlosem Rohrvortrieb",
                    },
                    "25005": {
                        "name": "St_ZM_PE",
                        "alias": "Stahl-Verbundrohr (ZM-PE)",
                        "description": "Stahlrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserohr)",
                    },
                    "3000": {
                        "name": "Gusseisen",
                        "alias": "Gusseisen",
                        "description": "Gusseisen",
                    },
                    "30001": {
                        "name": "GGG_ZM",
                        "alias": "duktiles Gussrohr mit ZM-Auskleidung",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung (z.B Abwasserrohr)",
                    },
                    "30002": {
                        "name": "GGG_ZM_PE",
                        "alias": "duktiles Guss-Verbundrohr (ZM-PE)",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserrohr)",
                    },
                    "4000": {
                        "name": "Beton",
                        "alias": "Beton",
                        "description": "Beton (z.B. Schacht)",
                    },
                    "5000": {
                        "name": "Holz",
                        "alias": "Holz",
                        "description": "Holz (z.B. Holzmast)",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiger Werkstoff",
                        "description": "Sonstiger Werkstoff",
                    },
                },
                "typename": "XP_Werkstoff",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BSTLinienobjekt(BSTObjekt):
    """Oberklasse der Objekte eines Bestandsplans mit Liniengeometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Line,
        Field(
            description="Raumbezug des Objektes",
            json_schema_extra={
                "typename": "GM_Curve",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class BSTMultiFlaechenobjekt(BSTObjekt):
    """Oberklasse der Objekte eines Bestandsplans mit Multi-Punktgeometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiPolygon,
        Field(
            description="Raumbezug des Objektes",
            json_schema_extra={
                "typename": "GM_MultiSurface",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]
    netzSparte: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "6000", "9999"] | None,
        Field(
            description="Leitungssparte eines Punktobjektes",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Telekommunikation",
                        "alias": "Telekommunikation",
                        "description": "Telekommunikation",
                    },
                    "2000": {
                        "name": "Gas",
                        "alias": "Gas",
                        "description": "Gasversorgung",
                    },
                    "3000": {
                        "name": "Elektrizitaet",
                        "alias": "Elektrizität",
                        "description": "Stromversorgung",
                    },
                    "4000": {
                        "name": "Waermeversorgung",
                        "alias": "Wärmeversorgung",
                        "description": "Versorgung mit Fern- oder Nahwärme",
                    },
                    "5000": {
                        "name": "Abwasserentsorgung",
                        "alias": "Abwasserentsorgung",
                        "description": "Abwasserentsorgung",
                    },
                    "6000": {
                        "name": "Wasserversorgung",
                        "alias": "Wasserversorgung",
                        "description": "Trinkwasserversorgung",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "Sonstiges Netz",
                        "description": "Sonstiges Ver- bzw. Entsorgungsnetz",
                    },
                },
                "typename": "BST_NetzSparte",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    statusAktuell: Annotated[
        Literal["1000", "2100", "2200", "3000", "4000", "5000", "6000", "9999"] | None,
        Field(
            description="aktueller Status",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "InBetrieb",
                        "alias": "in Betrieb",
                        "description": "Bestandsobjekt ist in Betrieb",
                    },
                    "2100": {
                        "name": "AusserBetriebGenommen",
                        "alias": "außer Betrieb genommen",
                        "description": "Bestandsobjekt ist temporär oder dauerhaft außer Betrieb genommen aber nicht stillgelegt",
                    },
                    "2200": {
                        "name": "Stillgelegt",
                        "alias": "stillgelegt",
                        "description": "Bestandsobjekt ist dauerhaft stillgelegt und steht nicht mehr für eine Wiederinbetriebnahme zur Verfügung",
                    },
                    "3000": {
                        "name": "ImRueckbau",
                        "alias": "im Rückbau",
                        "description": "Bestandsobjekt ist aktuell im Rückbau",
                    },
                    "4000": {
                        "name": "InSanierung",
                        "alias": "in Sanierung",
                        "description": "Bestandsobjekt ist nicht in Betrieb, da Instandsetzungs- oder Sanierungsarbeiten erfolgen",
                    },
                    "5000": {
                        "name": "InAenderung",
                        "alias": "in Änderung/Erweiterung",
                        "description": "Bestandsobjekt wird zurzeit geändert oder erweitertert (gemäß NABEG § 3, Nr.1)",
                    },
                    "6000": {
                        "name": "InErsetzung",
                        "alias": "in Ersetzung",
                        "description": "Bestandsobjekt wird zurzeit durch einen Neubau ersetzt (Ersatzneubau nach NABEG § 3, Nr. 4)",
                    },
                    "9999": {
                        "name": "UnbekannterStatus",
                        "alias": "unbekannter Status",
                        "description": "aktueller Status des Bestandsobjektes ist unbekannt",
                    },
                },
                "typename": "BST_StatusAktuell",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    statusAenderung: Annotated[
        Literal["1000", "2100", "2200", "3000", "4000", "40001", "5000", "6100", "6200"]
        | None,
        Field(
            description="Statusveränderung im Rahmen einer Baumaßnahme",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Wiederinbetriebnahme",
                        "alias": "Wiederinbetriebnahme",
                        "description": "Wiederinbetriebnahme einer Leitung; Wiederinbetriebnahme eines Infrastrukturobjektes",
                    },
                    "2100": {
                        "name": "Ausserbetriebnahme",
                        "alias": "Außerbetriebnahme",
                        "description": "Betriebszustand einer Leitung, in der aktuell kein Medientransport erfolgt, die Anlage jedoch für diesen Zweck weiterhin vorgehalten wird (Eine Gasleitung wird weiterhin überwacht und betriebsbereit instandgehalten, sie ist ebenso in den Korrosionsschutz eingebunden)",
                    },
                    "2200": {
                        "name": "Stilllegung",
                        "alias": "Stilllegung",
                        "description": "Endgültige Einstellung des Betriebs ohne dass ein vollständiger Rückbau der Leitung vorgesehen ist. Die Anlage wird nach endgültiger Stilllegung so gesichert, dass von ihr keine Gefahr ausgeht.",
                    },
                    "3000": {
                        "name": "Rueckbau",
                        "alias": "Rückbau",
                        "description": "Rückbau einer Leitung nach endgültiger Stilllegung; Rückbau eines Infrastrukturobjektes",
                    },
                    "4000": {
                        "name": "Sanierung",
                        "alias": "Sanierung",
                        "description": "Sanierung oder Instandsetzung bestehender Leitungen",
                    },
                    "40001": {
                        "name": "Umstellung_H2",
                        "alias": "Umstellung H2",
                        "description": "Umstellung von Leitungen und Speichern für Transport und Speicherung von Wasserstoff",
                    },
                    "5000": {
                        "name": "AenderungErweiterung",
                        "alias": "Änderung/Erweiterung",
                        "description": "NABEG § 3, Nr.1: Änderung oder  Ausbau einer Leitung in einer Bestandstrasse, wobei die bestehende Leitung grundsätzlich fortbestehen soll",
                    },
                    "6100": {
                        "name": "Ersatzneubau",
                        "alias": "Ersatzneubau",
                        "description": "NABEG § 3, Nr. 4: Errichtung einer neuen Leitung in oder unmittelbar neben einer Bestandstrasse, wobei die bestehende Leitung innerhalb von drei Jahren ersetzt wird; die Errichtung erfolgt in der Bestandstrasse, wenn sich bei Freileitungen die Mastfundamente und bei Erdkabeln die Kabel in der Bestandstrasse befinden; die Errichtung erfolgt unmittelbar neben der Bestandstrasse, wenn ein Abstand von 200 Metern zwischen den Trassenachsen nicht überschritten wird.",
                    },
                    "6200": {
                        "name": "Parallelneubau",
                        "alias": "Parallelneubau",
                        "description": "NABEG § 3, Nr.5: Errichtung einer neuen Leitung unmittelbar neben einer Bestandstrasse, wobei die bestehende Leitung fortbestehen soll; die Errichtung erfolgt unmittelbar neben der Bestandstrasse, wenn ein Abstand von 200 Metern zwischen den Trassenachsen nicht überschritten wird.",
                    },
                },
                "typename": "BST_StatusAenderung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    begrenzung: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Bestimmung der dargestellten Fläche",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Betriebsgelaende",
                        "alias": "Betriebsgelände",
                        "description": "gesamtes Betriebsgelände bzw. Grundstücksfläche",
                    },
                    "2000": {
                        "name": "EingezaeunteFlaeche",
                        "alias": "eingezäunte Fläche",
                        "description": "eingezäuntes Gelände der Infrastrukturgebäude (ohne Parkplätze und Nebengebäude)",
                    },
                    "3000": {
                        "name": "Gebaeudeflaeche",
                        "alias": "Gebäudefläche",
                        "description": "Fläche eines Gebäudes, das technische Anlagen enthält",
                    },
                },
                "typename": "XP_InfrastrukturFlaeche",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BSTMultiLinienobjekt(BSTObjekt):
    """Oberklasse der Objekte eines Bestandsplans mit Multi-Liniengeometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiLine,
        Field(
            description="Raumbezug des Objektes",
            json_schema_extra={
                "typename": "GM_MultiCurve",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]
    leitungstyp: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "10006",
            "2000",
            "20001",
            "20002",
            "20003",
        ]
        | None,
        Field(
            description="Auswahl des Leitungstyps",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Erdverlegt",
                        "alias": "erdverlegte (Rohr-)Leitungen",
                        "description": "Oberkategorie für erdverlegte (Rohr-)Leitungen",
                    },
                    "10001": {
                        "name": "Erdkabel",
                        "alias": "Erdkabel",
                        "description": "Ein Erdkabel ist ein im Erdboden verlegtes elektrisch genutztes Kabel mit einer besonders robusten Isolierung nach außen, dem Kabelmantel, der eine Zerstörung derselben durch chemische Einflüsse im Erdreich bzw. im Boden lebender Kleintiere verhindert.",
                    },
                    "10002": {
                        "name": "Seekabel",
                        "alias": "Seekabel",
                        "description": "Ein Seekabel (auch Unterseekabel, Unterwasserkabel) ist ein im Wesentlichen in einem Gewässer verlegtes Kabel zur Datenübertragung oder die Übertragung elektrischer Energie.",
                    },
                    "10003": {
                        "name": "Schutzrohr",
                        "alias": "Schutzrohr",
                        "description": "Im Schutzrohr verlegte oder zu verlegende Kabel/Leitungen. - Schutzrohre schützen erdverlegte Leitungen vor mechanischen Einflüssen und Feuchtigkeit.",
                    },
                    "10004": {
                        "name": "Leerrohr",
                        "alias": "Leerrohr (unbelegtes Schutzrohr)",
                        "description": "Über die Baumaßnahme hinaus unbelegtes Schutzrohr",
                    },
                    "10005": {
                        "name": "Leitungsbuendel",
                        "alias": "Leitungsbündel",
                        "description": "Bündel von Kabeln und/oder Schutzrohren in den Sparten Sparten Strom und Telekommunikation im Bestand",
                    },
                    "10006": {
                        "name": "Dueker",
                        "alias": "Düker",
                        "description": "Druckleitung zur Unterquerung von Straßen, Flüssen, Bahngleisen etc. Im Düker kann die Flüssigkeit das Hindernis überwinden, ohne dass Pumpen eingesetzt werden müssen.",
                    },
                    "2000": {
                        "name": "Oberirdisch",
                        "alias": "oberirdischer Verlauf",
                        "description": "Oberirdisch verlegte Leitungen und Rohre",
                    },
                    "20001": {
                        "name": "Freileitung",
                        "alias": "Freileitung",
                        "description": "Elektrische Leitung, deren spannungsführende Leiter im Freien durch die Luft geführt und meist auch nur durch die umgebende Luft voneinander und vom Erdboden isoliert sind. In der Regel werden die Leiterseile von Freileitungsmasten getragen, an denen sie mit Isolatoren befestigt sind.",
                    },
                    "20002": {
                        "name": "Heberleitung",
                        "alias": "Heberleitung",
                        "description": "Leitung zur Überquerung von Straßen oder zur Verbindung von Behältern (Gegenstück zu einem Düker)",
                    },
                    "20003": {
                        "name": "Rohrbruecke",
                        "alias": "Rohrbrücke",
                        "description": "Eine Rohrbrücke oder Rohrleitungsbrücke dient dazu, einzelne oder mehrere Rohrleitungen oberirdisch über größere Entfernungen zu führen.",
                    },
                },
                "typename": "XP_LeitungTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    statusAktuell: Annotated[
        Literal["1000", "2100", "2200", "3000", "4000", "5000", "6000", "9999"] | None,
        Field(
            description="aktueller Status",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "InBetrieb",
                        "alias": "in Betrieb",
                        "description": "Bestandsobjekt ist in Betrieb",
                    },
                    "2100": {
                        "name": "AusserBetriebGenommen",
                        "alias": "außer Betrieb genommen",
                        "description": "Bestandsobjekt ist temporär oder dauerhaft außer Betrieb genommen aber nicht stillgelegt",
                    },
                    "2200": {
                        "name": "Stillgelegt",
                        "alias": "stillgelegt",
                        "description": "Bestandsobjekt ist dauerhaft stillgelegt und steht nicht mehr für eine Wiederinbetriebnahme zur Verfügung",
                    },
                    "3000": {
                        "name": "ImRueckbau",
                        "alias": "im Rückbau",
                        "description": "Bestandsobjekt ist aktuell im Rückbau",
                    },
                    "4000": {
                        "name": "InSanierung",
                        "alias": "in Sanierung",
                        "description": "Bestandsobjekt ist nicht in Betrieb, da Instandsetzungs- oder Sanierungsarbeiten erfolgen",
                    },
                    "5000": {
                        "name": "InAenderung",
                        "alias": "in Änderung/Erweiterung",
                        "description": "Bestandsobjekt wird zurzeit geändert oder erweitertert (gemäß NABEG § 3, Nr.1)",
                    },
                    "6000": {
                        "name": "InErsetzung",
                        "alias": "in Ersetzung",
                        "description": "Bestandsobjekt wird zurzeit durch einen Neubau ersetzt (Ersatzneubau nach NABEG § 3, Nr. 4)",
                    },
                    "9999": {
                        "name": "UnbekannterStatus",
                        "alias": "unbekannter Status",
                        "description": "aktueller Status des Bestandsobjektes ist unbekannt",
                    },
                },
                "typename": "BST_StatusAktuell",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    statusAenderung: Annotated[
        Literal["1000", "2100", "2200", "3000", "4000", "40001", "5000", "6100", "6200"]
        | None,
        Field(
            description="Statusveränderung im Rahmen einer Baumaßnahme",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Wiederinbetriebnahme",
                        "alias": "Wiederinbetriebnahme",
                        "description": "Wiederinbetriebnahme einer Leitung; Wiederinbetriebnahme eines Infrastrukturobjektes",
                    },
                    "2100": {
                        "name": "Ausserbetriebnahme",
                        "alias": "Außerbetriebnahme",
                        "description": "Betriebszustand einer Leitung, in der aktuell kein Medientransport erfolgt, die Anlage jedoch für diesen Zweck weiterhin vorgehalten wird (Eine Gasleitung wird weiterhin überwacht und betriebsbereit instandgehalten, sie ist ebenso in den Korrosionsschutz eingebunden)",
                    },
                    "2200": {
                        "name": "Stilllegung",
                        "alias": "Stilllegung",
                        "description": "Endgültige Einstellung des Betriebs ohne dass ein vollständiger Rückbau der Leitung vorgesehen ist. Die Anlage wird nach endgültiger Stilllegung so gesichert, dass von ihr keine Gefahr ausgeht.",
                    },
                    "3000": {
                        "name": "Rueckbau",
                        "alias": "Rückbau",
                        "description": "Rückbau einer Leitung nach endgültiger Stilllegung; Rückbau eines Infrastrukturobjektes",
                    },
                    "4000": {
                        "name": "Sanierung",
                        "alias": "Sanierung",
                        "description": "Sanierung oder Instandsetzung bestehender Leitungen",
                    },
                    "40001": {
                        "name": "Umstellung_H2",
                        "alias": "Umstellung H2",
                        "description": "Umstellung von Leitungen und Speichern für Transport und Speicherung von Wasserstoff",
                    },
                    "5000": {
                        "name": "AenderungErweiterung",
                        "alias": "Änderung/Erweiterung",
                        "description": "NABEG § 3, Nr.1: Änderung oder  Ausbau einer Leitung in einer Bestandstrasse, wobei die bestehende Leitung grundsätzlich fortbestehen soll",
                    },
                    "6100": {
                        "name": "Ersatzneubau",
                        "alias": "Ersatzneubau",
                        "description": "NABEG § 3, Nr. 4: Errichtung einer neuen Leitung in oder unmittelbar neben einer Bestandstrasse, wobei die bestehende Leitung innerhalb von drei Jahren ersetzt wird; die Errichtung erfolgt in der Bestandstrasse, wenn sich bei Freileitungen die Mastfundamente und bei Erdkabeln die Kabel in der Bestandstrasse befinden; die Errichtung erfolgt unmittelbar neben der Bestandstrasse, wenn ein Abstand von 200 Metern zwischen den Trassenachsen nicht überschritten wird.",
                    },
                    "6200": {
                        "name": "Parallelneubau",
                        "alias": "Parallelneubau",
                        "description": "NABEG § 3, Nr.5: Errichtung einer neuen Leitung unmittelbar neben einer Bestandstrasse, wobei die bestehende Leitung fortbestehen soll; die Errichtung erfolgt unmittelbar neben der Bestandstrasse, wenn ein Abstand von 200 Metern zwischen den Trassenachsen nicht überschritten wird.",
                    },
                },
                "typename": "BST_StatusAenderung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    nennweite: Annotated[
        str | None,
        Field(
            description='Nennweite einer einzelnen Leitung. Die Nennweite DN ("diamètre nominal", "Durchmesser nach Norm") ist eine numerische Bezeichnung der ungefähren Durchmesser von Bauteilen in einem Rohrleitungssystem, die laut EN ISO 6708 "für Referenzzwecke verwendet wird".',
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    aussendurchmesser: Annotated[
        definitions.Length | None,
        Field(
            description="Außendurchmesser einer einzelnen Leitung in m\r\n(gml:LengthType: uom=“m“ oder uom=“urn:adv:uom:m“)",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    ueberdeckung: Annotated[
        definitions.Length | None,
        Field(
            description='Mindestüberdeckung (DIN): Mindestabstand zwischen Oberkante der Verkehrsfläche und Oberkante der Leitung  in m. Bei Leitungsbündeln bezieht sich der Wert auf die oberste Leitung bzw. die Oberkante des Bündels. \r\nDie "Verlegetiefe" einer Leitung wird dagegen bis zur Grabensohle gemessen.\r\nGilt nur für erdverlegte Linienobjekte.\r\n(gml:LengthType: uom=“m“ oder uom=“urn:adv:uom:m“)',
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    lagegenauigkeit: Annotated[
        definitions.Length | None,
        Field(
            description="Statistisches Maß der maximalen Abweichung des realen Verlaufs der Leitung von der Liniengeometrie in m\r\n(gml:LengthType: uom=“m“ oder uom=“urn:adv:uom:m“)",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    pufferzone3D: Annotated[
        definitions.Length | None,
        Field(
            description="Die Pufferzone definiert in einem 3D Modell einen rechteckigen Körper, in dem die Höhenlage einer Leitung (oder eines Leitungsbündels) variieren kann. Die obere Grenze des Puffers wird durch das Attribut Überdeckung definiert. Das hier einzutragende Maß ist die Distanz zur unteren Grenze des Puffers. Die Breite ergibt sich bei einzelnen Leitungen aus dem Attribut Nennweite oder Außendurchmesser, bei Leitungsbündeln aus der Breite der Leitungszone.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    schutzzone3D: Annotated[
        definitions.Length | None,
        Field(
            description="Die Schutzzone definiert in einem 3D Modell einen quadratischen Körper um die Leitung. Der hier einzutragende Wert ist die Länge, die von vier Kreistangenten ausgehend den Abstand zu den waage- und senkrechten Kanten des Quadrats darstellt.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None


class BSTMultiPunktobjekt(BSTObjekt):
    """Oberklasse der Objekte eines Bestandsplans mit Multi-Punktgeometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiPoint,
        Field(
            description="Raumbezug des Objektes",
            json_schema_extra={
                "typename": "GM_MultiPoint",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]
    netzSparte: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "6000", "9999"] | None,
        Field(
            description="Leitungssparte eines Punktobjektes",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Telekommunikation",
                        "alias": "Telekommunikation",
                        "description": "Telekommunikation",
                    },
                    "2000": {
                        "name": "Gas",
                        "alias": "Gas",
                        "description": "Gasversorgung",
                    },
                    "3000": {
                        "name": "Elektrizitaet",
                        "alias": "Elektrizität",
                        "description": "Stromversorgung",
                    },
                    "4000": {
                        "name": "Waermeversorgung",
                        "alias": "Wärmeversorgung",
                        "description": "Versorgung mit Fern- oder Nahwärme",
                    },
                    "5000": {
                        "name": "Abwasserentsorgung",
                        "alias": "Abwasserentsorgung",
                        "description": "Abwasserentsorgung",
                    },
                    "6000": {
                        "name": "Wasserversorgung",
                        "alias": "Wasserversorgung",
                        "description": "Trinkwasserversorgung",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "Sonstiges Netz",
                        "description": "Sonstiges Ver- bzw. Entsorgungsnetz",
                    },
                },
                "typename": "BST_NetzSparte",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    statusAktuell: Annotated[
        Literal["1000", "2100", "2200", "3000", "4000", "5000", "6000", "9999"] | None,
        Field(
            description="aktueller Status",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "InBetrieb",
                        "alias": "in Betrieb",
                        "description": "Bestandsobjekt ist in Betrieb",
                    },
                    "2100": {
                        "name": "AusserBetriebGenommen",
                        "alias": "außer Betrieb genommen",
                        "description": "Bestandsobjekt ist temporär oder dauerhaft außer Betrieb genommen aber nicht stillgelegt",
                    },
                    "2200": {
                        "name": "Stillgelegt",
                        "alias": "stillgelegt",
                        "description": "Bestandsobjekt ist dauerhaft stillgelegt und steht nicht mehr für eine Wiederinbetriebnahme zur Verfügung",
                    },
                    "3000": {
                        "name": "ImRueckbau",
                        "alias": "im Rückbau",
                        "description": "Bestandsobjekt ist aktuell im Rückbau",
                    },
                    "4000": {
                        "name": "InSanierung",
                        "alias": "in Sanierung",
                        "description": "Bestandsobjekt ist nicht in Betrieb, da Instandsetzungs- oder Sanierungsarbeiten erfolgen",
                    },
                    "5000": {
                        "name": "InAenderung",
                        "alias": "in Änderung/Erweiterung",
                        "description": "Bestandsobjekt wird zurzeit geändert oder erweitertert (gemäß NABEG § 3, Nr.1)",
                    },
                    "6000": {
                        "name": "InErsetzung",
                        "alias": "in Ersetzung",
                        "description": "Bestandsobjekt wird zurzeit durch einen Neubau ersetzt (Ersatzneubau nach NABEG § 3, Nr. 4)",
                    },
                    "9999": {
                        "name": "UnbekannterStatus",
                        "alias": "unbekannter Status",
                        "description": "aktueller Status des Bestandsobjektes ist unbekannt",
                    },
                },
                "typename": "BST_StatusAktuell",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    statusAenderung: Annotated[
        Literal["1000", "2100", "2200", "3000", "4000", "40001", "5000", "6100", "6200"]
        | None,
        Field(
            description="Statusveränderung im Rahmen einer Baumaßnahme",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Wiederinbetriebnahme",
                        "alias": "Wiederinbetriebnahme",
                        "description": "Wiederinbetriebnahme einer Leitung; Wiederinbetriebnahme eines Infrastrukturobjektes",
                    },
                    "2100": {
                        "name": "Ausserbetriebnahme",
                        "alias": "Außerbetriebnahme",
                        "description": "Betriebszustand einer Leitung, in der aktuell kein Medientransport erfolgt, die Anlage jedoch für diesen Zweck weiterhin vorgehalten wird (Eine Gasleitung wird weiterhin überwacht und betriebsbereit instandgehalten, sie ist ebenso in den Korrosionsschutz eingebunden)",
                    },
                    "2200": {
                        "name": "Stilllegung",
                        "alias": "Stilllegung",
                        "description": "Endgültige Einstellung des Betriebs ohne dass ein vollständiger Rückbau der Leitung vorgesehen ist. Die Anlage wird nach endgültiger Stilllegung so gesichert, dass von ihr keine Gefahr ausgeht.",
                    },
                    "3000": {
                        "name": "Rueckbau",
                        "alias": "Rückbau",
                        "description": "Rückbau einer Leitung nach endgültiger Stilllegung; Rückbau eines Infrastrukturobjektes",
                    },
                    "4000": {
                        "name": "Sanierung",
                        "alias": "Sanierung",
                        "description": "Sanierung oder Instandsetzung bestehender Leitungen",
                    },
                    "40001": {
                        "name": "Umstellung_H2",
                        "alias": "Umstellung H2",
                        "description": "Umstellung von Leitungen und Speichern für Transport und Speicherung von Wasserstoff",
                    },
                    "5000": {
                        "name": "AenderungErweiterung",
                        "alias": "Änderung/Erweiterung",
                        "description": "NABEG § 3, Nr.1: Änderung oder  Ausbau einer Leitung in einer Bestandstrasse, wobei die bestehende Leitung grundsätzlich fortbestehen soll",
                    },
                    "6100": {
                        "name": "Ersatzneubau",
                        "alias": "Ersatzneubau",
                        "description": "NABEG § 3, Nr. 4: Errichtung einer neuen Leitung in oder unmittelbar neben einer Bestandstrasse, wobei die bestehende Leitung innerhalb von drei Jahren ersetzt wird; die Errichtung erfolgt in der Bestandstrasse, wenn sich bei Freileitungen die Mastfundamente und bei Erdkabeln die Kabel in der Bestandstrasse befinden; die Errichtung erfolgt unmittelbar neben der Bestandstrasse, wenn ein Abstand von 200 Metern zwischen den Trassenachsen nicht überschritten wird.",
                    },
                    "6200": {
                        "name": "Parallelneubau",
                        "alias": "Parallelneubau",
                        "description": "NABEG § 3, Nr.5: Errichtung einer neuen Leitung unmittelbar neben einer Bestandstrasse, wobei die bestehende Leitung fortbestehen soll; die Errichtung erfolgt unmittelbar neben der Bestandstrasse, wenn ein Abstand von 200 Metern zwischen den Trassenachsen nicht überschritten wird.",
                    },
                },
                "typename": "BST_StatusAenderung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BSTRichtfunkstrecke(BSTMultiLinienobjekt):
    """Drahtlose Datenübertragung mittels Radiowellen, die von einem Ausgangspunkt auf einen definierten Zielpunkt gerichtet ist"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class BSTSchacht(BSTMultiPunktobjekt):
    """Unterirdisches Bauwerk eines Infrastrukturnetzes"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    schachttiefe: Annotated[
        definitions.Length | None,
        Field(
            description="Schachttiefe (= Deckelhöhe - Sohlhöhe)",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None


class BSTSonstigeInfrastruktur(BSTMultiPunktobjekt):
    """Punktförmige Infrastruktur, die sich nicht durch eine der expliziten Klassen darstellen lässt. Sie muss textlich näher gekennzeichnet werden (Attribut beschreibung der Oberklasse XP_NetzObjekt)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class BSTSonstigeInfrastrukturFlaeche(BSTMultiFlaechenobjekt):
    """Als Fläche dargestellte Infrastruktur, die sich nicht durch eine der expliziten Klassen erfassen lässt. Sie muss textlich näher gekennzeichnet werden (Attribut beschreibung der Oberklasse XP_NetzObjekt)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class BSTSonstigeLeitung(BSTMultiLinienobjekt):
    """Leitungsförmige Infrastruktur, die sich nicht durch eine der expliziten Klassen darstellen lässt. Sie muss textlich näher gekennzeichnet werden (Attribut beschreibung der Oberklasse XP_NetzObjekt)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class BSTStation(BSTMultiPunktobjekt):
    """Knoten eines Infrastrukturnetzes oder zwischen Infrastrukturnetzen mit identischem Transportmedium"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "10006",
            "10007",
            "2000",
            "20001",
            "20002",
            "20003",
            "3000",
            "9999",
        ]
        | None,
        Field(
            description="Art der Station",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "StationGas",
                        "alias": "Station Gas",
                        "description": "Station für Medium Gas (Wasserstoff/Erdgas)",
                    },
                    "10001": {
                        "name": "Schieberstation",
                        "alias": "Schieberstation",
                        "description": "Über eine Schieberstation (Abzweigstation?)  kann mit Hilfe der dort installierten Kugelhähne der Gasfluss gestoppt bzw. umgelenkt werden",
                    },
                    "10002": {
                        "name": "Verdichterstation",
                        "alias": "Verdichterstation",
                        "description": "Eine Verdichterstation (Kompressorstation) ist eine Anlage in einer Transportleitung, bei der ein Kompressor das Gas wieder komprimiert, um Rohr-Druckverluste auszugleichen und den Volumenstrom zu regeln",
                    },
                    "10003": {
                        "name": "Regel_Messstation",
                        "alias": "Regel- und Messstation",
                        "description": "Eine Gas-Druckregelanlage (GDRA) ist eine Anlage zur ein- oder mehrstufigen Gas-Druckreduzierung. Bei einer Gas-Druckregel- und Messanlage (GDRMA) wird zusätzlich noch die Gas-Mengenmessung vorgenommen. (Anmerkung: Einspeise- und Übergabestationen können separat erfasst werden)",
                    },
                    "10004": {
                        "name": "Armaturstation",
                        "alias": "Armaturstation",
                        "description": "Kombination von Armaturengruppen wie Absperr- und und Abgangsarmaturengruppen",
                    },
                    "10005": {
                        "name": "Einspeisestation",
                        "alias": "Einspeisestation",
                        "description": "Die Einspeisungs- oder Empfangsstation leitet Erdgas oder Wasserstoff in ein Transportleitungsnetz. Die Einspeisung erfolgt z.B. aus einer Produktions- oder Speicheranlage oder über ein LNG-Terminal nach der Regasifizierung.",
                    },
                    "10006": {
                        "name": "Uebergabestation",
                        "alias": "Übergabe-/Entnahmestation",
                        "description": "Gas-Übergabestationen (auch Übernahme- oder Entnahmestation) dienen i.d.R. der Verteilung von Gas aus Transportleitungen in die Verbrauchernetze. Dafür muss das ankommende Gas heruntergeregelt werden. Wird Wasserstoff in ein Erdgasleitungsnetz übergeben, muss zusätzlich ein Mischer an der Übernahmestelle gewährleisten, dass sich Wasserstoff und Erdgas gleichmäßig durchmischen. \r\nEine weitere Variante ist die Übergabe von Gas an ein Kraftwerk.",
                    },
                    "10007": {
                        "name": "Molchstation",
                        "alias": "Molchstation",
                        "description": "Station um Molchungen zur Prüfung der Integrität der Fernleitung während der Betriebsphase durchzuführen.  \r\nDer Molch füllt den Leitungsquerschnitt aus und wandert entweder einfach mit dem Produktstrom durch die Leitung (meist bei Öl) oder wird durch Druck durch die Leitung gepresst. Im Rahmen der Molchtechnik werden neben dem Molch noch ins System eingebaute Schleusen benötigt, durch die der Molch in die Leitungen eingesetzt bzw. herausgenommen und von hinten mit Druck belegt werden kann.",
                    },
                    "2000": {
                        "name": "StationStrom",
                        "alias": "Station Strom",
                        "description": "Station für Medium Strom",
                    },
                    "20001": {
                        "name": "Transformatorenstation",
                        "alias": "Transformatorenstation",
                        "description": "In einer Transformatorenstation (Umspannstation, Netzstation, Ortsnetzstation oder kurz Trafostation) wird die elektrische Energie aus dem Mittelspannungsnetz mit einer elektrischen Spannung von 10 kV bis 36 kV auf die in Niederspannungsnetzen (Ortsnetzen) verwendeten 400/230 V zur allgemeinen Versorgung transformiert",
                    },
                    "20002": {
                        "name": "Konverterstation",
                        "alias": "Konverterstation",
                        "description": "Ein Konverter steht an den Verbindungspunkten von Gleich- und Wechselstromleitungen. Er verwandelt Wechsel- in Gleichstrom und kann ebenso Gleichstrom wieder zurück in Wechselstrom umwandeln und diesen ins Übertragungsnetz einspeisen.",
                    },
                    "20003": {
                        "name": "Phasenschieber",
                        "alias": "Phasenschieber",
                        "description": "Phasenschiebertransformatoren (PST), auch Querregler genannt, werden zur Steuerung der Stromflüsse zwischen Übertragungsnetzen eingesetzt. Der Phasenschiebertransformator speist einen Ausgleichsstrom in das System ein, der den Laststrom in der Leitung entweder verringert oder erhöht. Sinkt der Stromfluss in einer Leitung, werden die Stromflüsse im gesamten Verbundsystem neu verteilt.",
                    },
                    "3000": {
                        "name": "StationWaerme",
                        "alias": "Station (Fern-)Wärme",
                        "description": "Station im (Fern-)Wärmenetz",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstige Station",
                        "description": "Sonstige Station",
                    },
                },
                "typename": "XP_StationTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BSTStationFlaeche(BSTMultiFlaechenobjekt):
    """Knoten eines Infrastrukturnetzes oder zwischen Infrastrukturnetzen mit identischem Transportmedium (Alternative Spezifizieurng zu BST_Station)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "10006",
            "10007",
            "2000",
            "20001",
            "20002",
            "20003",
            "3000",
            "9999",
        ]
        | None,
        Field(
            description="Art der Station",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "StationGas",
                        "alias": "Station Gas",
                        "description": "Station für Medium Gas (Wasserstoff/Erdgas)",
                    },
                    "10001": {
                        "name": "Schieberstation",
                        "alias": "Schieberstation",
                        "description": "Über eine Schieberstation (Abzweigstation?)  kann mit Hilfe der dort installierten Kugelhähne der Gasfluss gestoppt bzw. umgelenkt werden",
                    },
                    "10002": {
                        "name": "Verdichterstation",
                        "alias": "Verdichterstation",
                        "description": "Eine Verdichterstation (Kompressorstation) ist eine Anlage in einer Transportleitung, bei der ein Kompressor das Gas wieder komprimiert, um Rohr-Druckverluste auszugleichen und den Volumenstrom zu regeln",
                    },
                    "10003": {
                        "name": "Regel_Messstation",
                        "alias": "Regel- und Messstation",
                        "description": "Eine Gas-Druckregelanlage (GDRA) ist eine Anlage zur ein- oder mehrstufigen Gas-Druckreduzierung. Bei einer Gas-Druckregel- und Messanlage (GDRMA) wird zusätzlich noch die Gas-Mengenmessung vorgenommen. (Anmerkung: Einspeise- und Übergabestationen können separat erfasst werden)",
                    },
                    "10004": {
                        "name": "Armaturstation",
                        "alias": "Armaturstation",
                        "description": "Kombination von Armaturengruppen wie Absperr- und und Abgangsarmaturengruppen",
                    },
                    "10005": {
                        "name": "Einspeisestation",
                        "alias": "Einspeisestation",
                        "description": "Die Einspeisungs- oder Empfangsstation leitet Erdgas oder Wasserstoff in ein Transportleitungsnetz. Die Einspeisung erfolgt z.B. aus einer Produktions- oder Speicheranlage oder über ein LNG-Terminal nach der Regasifizierung.",
                    },
                    "10006": {
                        "name": "Uebergabestation",
                        "alias": "Übergabe-/Entnahmestation",
                        "description": "Gas-Übergabestationen (auch Übernahme- oder Entnahmestation) dienen i.d.R. der Verteilung von Gas aus Transportleitungen in die Verbrauchernetze. Dafür muss das ankommende Gas heruntergeregelt werden. Wird Wasserstoff in ein Erdgasleitungsnetz übergeben, muss zusätzlich ein Mischer an der Übernahmestelle gewährleisten, dass sich Wasserstoff und Erdgas gleichmäßig durchmischen. \r\nEine weitere Variante ist die Übergabe von Gas an ein Kraftwerk.",
                    },
                    "10007": {
                        "name": "Molchstation",
                        "alias": "Molchstation",
                        "description": "Station um Molchungen zur Prüfung der Integrität der Fernleitung während der Betriebsphase durchzuführen.  \r\nDer Molch füllt den Leitungsquerschnitt aus und wandert entweder einfach mit dem Produktstrom durch die Leitung (meist bei Öl) oder wird durch Druck durch die Leitung gepresst. Im Rahmen der Molchtechnik werden neben dem Molch noch ins System eingebaute Schleusen benötigt, durch die der Molch in die Leitungen eingesetzt bzw. herausgenommen und von hinten mit Druck belegt werden kann.",
                    },
                    "2000": {
                        "name": "StationStrom",
                        "alias": "Station Strom",
                        "description": "Station für Medium Strom",
                    },
                    "20001": {
                        "name": "Transformatorenstation",
                        "alias": "Transformatorenstation",
                        "description": "In einer Transformatorenstation (Umspannstation, Netzstation, Ortsnetzstation oder kurz Trafostation) wird die elektrische Energie aus dem Mittelspannungsnetz mit einer elektrischen Spannung von 10 kV bis 36 kV auf die in Niederspannungsnetzen (Ortsnetzen) verwendeten 400/230 V zur allgemeinen Versorgung transformiert",
                    },
                    "20002": {
                        "name": "Konverterstation",
                        "alias": "Konverterstation",
                        "description": "Ein Konverter steht an den Verbindungspunkten von Gleich- und Wechselstromleitungen. Er verwandelt Wechsel- in Gleichstrom und kann ebenso Gleichstrom wieder zurück in Wechselstrom umwandeln und diesen ins Übertragungsnetz einspeisen.",
                    },
                    "20003": {
                        "name": "Phasenschieber",
                        "alias": "Phasenschieber",
                        "description": "Phasenschiebertransformatoren (PST), auch Querregler genannt, werden zur Steuerung der Stromflüsse zwischen Übertragungsnetzen eingesetzt. Der Phasenschiebertransformator speist einen Ausgleichsstrom in das System ein, der den Laststrom in der Leitung entweder verringert oder erhöht. Sinkt der Stromfluss in einer Leitung, werden die Stromflüsse im gesamten Verbundsystem neu verteilt.",
                    },
                    "3000": {
                        "name": "StationWaerme",
                        "alias": "Station (Fern-)Wärme",
                        "description": "Station im (Fern-)Wärmenetz",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstige Station",
                        "description": "Sonstige Station",
                    },
                },
                "typename": "XP_StationTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BSTStrassenablauf(BSTMultiPunktobjekt):
    """Ein Straßenablauf (Einlaufgitter, Gully, Trumme) ist ein Bauteil zur Straßenentwässerung. Es dient der Aufnahme von Oberflächenwasser auf befestigten Flächen und leitet dieses durch einen unterirdischen Abwasserkanal ab."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class BSTStromleitung(BSTMultiLinienobjekt):
    """Stromleitung oder Bündel von Stromleitungen (s.a. BST_Leitungstyp)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    spannung: Annotated[
        Literal["1000", "2000", "3000", "30001", "30002", "30003", "9999"] | None,
        Field(
            description='Angabe der Spannung einer Leitung. \r\nBei Leitungsbündeln kann das Textattribut "beschreibung" zur Differenzierung der Spannungsarten genutzt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Niedrigspannung",
                        "alias": "Niedrigspannung",
                        "description": "Niedrigspannung (< 1 kV)",
                    },
                    "2000": {
                        "name": "Mittelspannung",
                        "alias": "Mittelspannung",
                        "description": "Der Begriff Mittelspannung ist nicht genormt bzw. in den Grenzen nicht exakt definiert. Die oberen Grenze wird häufig  mit 30 oder 50 kV angegeben.",
                    },
                    "3000": {
                        "name": "Hochspannung",
                        "alias": "Hochspannung",
                        "description": "Hochspannung",
                    },
                    "30001": {
                        "name": "Hochspannung_110 kV",
                        "alias": "Hochspannung 110 kV",
                        "description": "Hochspannung 110 kV",
                    },
                    "30002": {
                        "name": "Hoechstspannung_220 kV",
                        "alias": "Höchstspannung 220 kV",
                        "description": "Höchstspannung 220 kV",
                    },
                    "30003": {
                        "name": "Hoechstspannung_380 kV",
                        "alias": "Höchstspannung 380 kV",
                        "description": "Höchstspannung 380 kV",
                    },
                    "9999": {
                        "name": "UnbekannteSpannung",
                        "alias": "Unbekannte Spannung",
                        "description": "Unbekannte Spannung",
                    },
                },
                "typename": "BST_Spannung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    leitungszoneBreite: Annotated[
        definitions.Length | None,
        Field(
            description="Ein Bündel an Leitungen wird über deren Gesamtbreite und -tiefe in Metern spezifiziert. \r\nEine weitere Differenzierung zwischen Kabeln mit und ohne Schutzrohr sowie deren jeweiligem Durchmesser erfolgt nicht.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    leitungszoneTiefe: Annotated[
        definitions.Length | None,
        Field(
            description="Ein Bündel an Leitungen wird über deren Gesamtbreite und -tiefe in Metern spezifiziert. \r\nDie Tiefe bezieht sich auf den Abstand zwischen der Oberkante der obersten und der Unterkante der untersten Lage der Leitungen.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None


class BSTTelekommunikationsleitung(BSTMultiLinienobjekt):
    """Telekommunikationsleitung oder Bündel an Telekommunikationsleitungen (s.a. BST_Leitungstyp)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal["1000", "2000", "3000", "4000"] | None,
        Field(
            description='Auswahl des Kabeltyps. \r\nBei Leitungsbündeln kann das Textattribut "beschreibung" zur Differenzierung der Kabel genutzt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Glasfaserkabel",
                        "alias": "Glasfaserkabel",
                        "description": "Glasfaserkabel",
                    },
                    "2000": {
                        "name": "Kupferkabel",
                        "alias": "Kupferkabel",
                        "description": "Kupferkabel",
                    },
                    "3000": {
                        "name": "Hybridkabel",
                        "alias": "Hybridkabel",
                        "description": "Hybridkabel",
                    },
                    "4000": {
                        "name": "Koaxialkabel",
                        "alias": "Koaxial-(TV)-Kabel",
                        "description": "Koaxial-(TV)-Kabel",
                    },
                },
                "typename": "XP_KabelTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    leitungszoneBreite: Annotated[
        definitions.Length | None,
        Field(
            description="Ein Bündel an Leitungen wird über deren Gesamtbreite und -tiefe in Metern spezifiziert. \r\nEine weitere Differenzierung zwischen Kabeln mit und ohne Schutzrohr sowie deren jeweiligem Durchmesser erfolgt nicht.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    leitungszoneTiefe: Annotated[
        definitions.Length | None,
        Field(
            description="Ein Bündel an Leitungen wird über deren Gesamtbreite und -tiefe in Metern spezifiziert. \r\nDie Tiefe bezieht sich auf den Abstand zwischen der Oberkante der obersten und der Unterkante der untersten Lage der Leitungen.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None


class BSTUmspannwerk(BSTMultiFlaechenobjekt):
    """Knoten eines elektrischen Versorgungsnetzes, um Netze mit verschiedenen Spannungsebenen (z. B. 380 kV und 110 kV) durch Transformatoren zu verbinden. Ebenso können Teile des Netzes gleicher Spannung in Schaltanlagen miteinander verbunden oder abgeschaltet werden. Kleinere Umspannanlagen, in denen Mittel- auf Niederspannung transformiert wird, gehören zu den Stationen (s. BST_Station und BST_StationFlaeche)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class BSTVerteiler(BSTMultiPunktobjekt):
    """Verteilerschränke/-kästen in Niederspannungs- und TK-Netzen"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "10003",
            "2000",
            "20001",
            "20002",
            "20003",
            "20004",
            "9999",
        ]
        | None,
        Field(
            description="Typ des Gehäuses bzw. der Funktion",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "TK_Verteiler",
                        "alias": "TK-Verteiler",
                        "description": "Verteilerschränke der Telekommunikation",
                    },
                    "10001": {
                        "name": "Multifunktionsgehaeuse",
                        "alias": "Multifunktionsgehäuse",
                        "description": "Multifunktionsgehäuse",
                    },
                    "10002": {
                        "name": "GlasfaserNetzverteiler",
                        "alias": "Glasfaser-Netzverteiler (Gf- NVt)",
                        "description": "Glasfaser-Netzverteiler (Gf-NVt)",
                    },
                    "10003": {
                        "name": "Kabelverzweiger_KVz",
                        "alias": "Kabelverzweiger ( KVz) - (Telekom  AG)",
                        "description": "Kabelverzweiger (KVz) - (Telekom AG)",
                    },
                    "2000": {
                        "name": "Strom_Schrank",
                        "alias": "Strom-Schrank",
                        "description": "Schränke für die Stromversorgung, öffentliche Beleuchtung, Verkehrstechnik u.a.",
                    },
                    "20001": {
                        "name": "Schaltschrank",
                        "alias": "Schaltschrank",
                        "description": "Schaltschrank",
                    },
                    "20002": {
                        "name": "Kabelverteilerschrank",
                        "alias": "Kabelverteilerschrank",
                        "description": "Kabelverteilerschrank",
                    },
                    "20003": {
                        "name": "Steuerschrank",
                        "alias": "Steuerschrank",
                        "description": "Steuerschrank",
                    },
                    "20004": {
                        "name": "Trennschrank",
                        "alias": "Trennschrank",
                        "description": "Trennschrank",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiger Schrank",
                        "description": "sonstiger Schrank",
                    },
                },
                "typename": "XP_GehaeuseTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BSTWaermeleitung(BSTMultiLinienobjekt):
    """Wärmeleitung eines Nah- oder Fernwärmenetzes"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"] | None,
        Field(
            description="Art der Wärmeleitung",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Strang",
                        "alias": "Strang",
                        "description": "Schematische Darstellung als Strang (mit Vor- und Rücklauf)",
                    },
                    "2000": {
                        "name": "Vorlauf",
                        "alias": "Vorlauf",
                        "description": "Vorlaufrohr",
                    },
                    "3000": {
                        "name": "Ruecklauf",
                        "alias": "Rücklauf",
                        "description": "Rücklaufrohr",
                    },
                    "4000": {
                        "name": "Doppelrohr",
                        "alias": "Doppelrohr",
                        "description": "Vor- und Rücklauf in einem Doppelrohr",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiger Typ",
                        "description": "Sonstiger Typ",
                    },
                },
                "typename": "XP_WaermeleitungTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    netzEbene: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "6000", "7000", "8000", "9999"]
        | None,
        Field(
            description="Leitungsart innerhalb des Wärmenetzes",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Fernleitung",
                        "alias": "Fernleitung",
                        "description": "Fernleitung gemäß Umweltverträglichkeitsprüfung (UVPG), Anlage 1 und ENWG § 3, Nr. 19d/20; Leitungen der Fernleitungsnetzbetreiber",
                    },
                    "2000": {
                        "name": "Verteilnetzleitung",
                        "alias": "Verteilnetzleitung",
                        "description": "Leitung eines Verteil(er)netzes; Leitungen der Versorgungsunternehmen",
                    },
                    "3000": {
                        "name": "Hauptleitung",
                        "alias": "Hauptleitung",
                        "description": "Hauptleitung, oberste Leitungskategorie in einem Trinkwasser und Wärmenetz",
                    },
                    "4000": {
                        "name": "Versorgungsleitung",
                        "alias": "Versorgungsleitung",
                        "description": "Versorgungsleitung, auch Ortsleitung (z.B Wasserleitungen innerhalb des Versorgungsgebietes im bebauten Bereich)",
                    },
                    "5000": {
                        "name": "Zubringerleitung",
                        "alias": "Zubringerleitung",
                        "description": "Zubringerleitung (z.B. Wasserleitungen zwischen Wassergewinnungs- und Versorgungsgebieten)",
                    },
                    "6000": {
                        "name": "Anschlussleitung",
                        "alias": "Hausanschlussleitung",
                        "description": "Anschlussleitung, Hausanschluss (z.B. Wasserleitungen von der Abzweigstelle der Versorgungsleitung bis zur Übergabestelle/Hauptabsperreinrichtung)",
                    },
                    "7000": {
                        "name": "Verbindungsleitung",
                        "alias": "Verbindungsleitung",
                        "description": "Verbindungsleitung (z.B. Wasserleitungen außerhalb der Versorgungsgebiete, die Versorgungsgebiete (Orte) miteinander verbinden), in der Wärmeversorung auch Transportleitung genannt (die eine Wärmeerzeuugungsinfrastruktur mit einem entfernten Versorgungsgebiet verbindet)",
                    },
                    "8000": {
                        "name": "Strassenablaufleitung",
                        "alias": "Straßenablaufleitung",
                        "description": "Straßenablaufleitung (in der Abwasserentsorgung)",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstige Leitung",
                        "description": "Sonstige Leitung",
                    },
                },
                "typename": "XP_RohrleitungNetz",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    werkstoff: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "2000",
            "20001",
            "20002",
            "20003",
            "2500",
            "25001",
            "25002",
            "25003",
            "25004",
            "25005",
            "3000",
            "30001",
            "30002",
            "4000",
            "5000",
            "9999",
        ]
        | None,
        Field(
            description="Werkstoff der Leitung",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Kunststoff",
                        "alias": "Kunststoff",
                        "description": "Kunststoff",
                    },
                    "10001": {
                        "name": "Polyethylen_PE",
                        "alias": "Polyethylen ( PE)",
                        "description": "Polyethylen (PE)",
                    },
                    "10002": {
                        "name": "Polyethylen_PE_HD",
                        "alias": "High-Density Polyethylen",
                        "description": "High-Density Polyethylen",
                    },
                    "10003": {
                        "name": "Polypropylen_PP",
                        "alias": "Polypropylen ( PP)",
                        "description": "Polypropylen (PP)",
                    },
                    "10004": {
                        "name": "Polycarbonat_PC",
                        "alias": "Polycarbonat ( PC)",
                        "description": "Polycarbonat (PC)",
                    },
                    "10005": {
                        "name": "Polyvinylchlorid_PVC_U",
                        "alias": "Polyvinylchlorid ( PVC- U)",
                        "description": "Polyvinylchlorid (PVC-U)",
                    },
                    "2000": {"name": "Stahl", "alias": "Stahl", "description": "Stahl"},
                    "20001": {
                        "name": "StahlVerzinkt",
                        "alias": "Stahl verzinkt",
                        "description": "Stahl verzinkt",
                    },
                    "20002": {
                        "name": "Stahlgitter",
                        "alias": "Stahlgitter",
                        "description": "Stahlfachwerkskonstruktion (z.B. Freileitungsmast als Gittermast)",
                    },
                    "20003": {
                        "name": "Stahlrohr",
                        "alias": "Stahlrohr",
                        "description": "Rohrförmiger Profilstahl, dessen Wand aus Stahl besteht. Stahlrohre dienen der Durchleitung von flüssigen, gasförmigen oder festen Stoffen, oder werden als statische oder konstruktive Elemente verwendet (z.B. Freileitungsmast als Stahlrohrmast)",
                    },
                    "2500": {
                        "name": "Stahlverbundrohr",
                        "alias": "Stahlverbundrohr",
                        "description": "Stahlverbundrohre im Rohrleitungsbau",
                    },
                    "25001": {
                        "name": "St_PE",
                        "alias": "Stahlrohr mit Standard-Kunststoffumhüllung (PE)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PE-Basis",
                    },
                    "25002": {
                        "name": "St_PP",
                        "alias": "Stahlrohr mit Kunstoffumhüllung (PP)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PP-Basis für höhere Temperatur- und Härte-Anforderungen",
                    },
                    "25003": {
                        "name": "St_FZM",
                        "alias": "Stahlrohr mit FZM-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz durch Faserzementmörtel-Ummantelung (FZM)",
                    },
                    "25004": {
                        "name": "St_GFK",
                        "alias": "Stahlrohr mit GFK-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz aus glasfaserverstärktem Kunststoff (GFK) für höchste mechanische Abriebfestigkeit bei grabenlosem Rohrvortrieb",
                    },
                    "25005": {
                        "name": "St_ZM_PE",
                        "alias": "Stahl-Verbundrohr (ZM-PE)",
                        "description": "Stahlrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserohr)",
                    },
                    "3000": {
                        "name": "Gusseisen",
                        "alias": "Gusseisen",
                        "description": "Gusseisen",
                    },
                    "30001": {
                        "name": "GGG_ZM",
                        "alias": "duktiles Gussrohr mit ZM-Auskleidung",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung (z.B Abwasserrohr)",
                    },
                    "30002": {
                        "name": "GGG_ZM_PE",
                        "alias": "duktiles Guss-Verbundrohr (ZM-PE)",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserrohr)",
                    },
                    "4000": {
                        "name": "Beton",
                        "alias": "Beton",
                        "description": "Beton (z.B. Schacht)",
                    },
                    "5000": {
                        "name": "Holz",
                        "alias": "Holz",
                        "description": "Holz (z.B. Holzmast)",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiger Werkstoff",
                        "description": "Sonstiger Werkstoff",
                    },
                },
                "typename": "XP_Werkstoff",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BSTWasserleitung(BSTMultiLinienobjekt):
    """Trinkwasserleitung"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    netzEbene: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "6000", "7000", "8000", "9999"]
        | None,
        Field(
            description="Leitungsart innerhalb des Wassernetzes",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Fernleitung",
                        "alias": "Fernleitung",
                        "description": "Fernleitung gemäß Umweltverträglichkeitsprüfung (UVPG), Anlage 1 und ENWG § 3, Nr. 19d/20; Leitungen der Fernleitungsnetzbetreiber",
                    },
                    "2000": {
                        "name": "Verteilnetzleitung",
                        "alias": "Verteilnetzleitung",
                        "description": "Leitung eines Verteil(er)netzes; Leitungen der Versorgungsunternehmen",
                    },
                    "3000": {
                        "name": "Hauptleitung",
                        "alias": "Hauptleitung",
                        "description": "Hauptleitung, oberste Leitungskategorie in einem Trinkwasser und Wärmenetz",
                    },
                    "4000": {
                        "name": "Versorgungsleitung",
                        "alias": "Versorgungsleitung",
                        "description": "Versorgungsleitung, auch Ortsleitung (z.B Wasserleitungen innerhalb des Versorgungsgebietes im bebauten Bereich)",
                    },
                    "5000": {
                        "name": "Zubringerleitung",
                        "alias": "Zubringerleitung",
                        "description": "Zubringerleitung (z.B. Wasserleitungen zwischen Wassergewinnungs- und Versorgungsgebieten)",
                    },
                    "6000": {
                        "name": "Anschlussleitung",
                        "alias": "Hausanschlussleitung",
                        "description": "Anschlussleitung, Hausanschluss (z.B. Wasserleitungen von der Abzweigstelle der Versorgungsleitung bis zur Übergabestelle/Hauptabsperreinrichtung)",
                    },
                    "7000": {
                        "name": "Verbindungsleitung",
                        "alias": "Verbindungsleitung",
                        "description": "Verbindungsleitung (z.B. Wasserleitungen außerhalb der Versorgungsgebiete, die Versorgungsgebiete (Orte) miteinander verbinden), in der Wärmeversorung auch Transportleitung genannt (die eine Wärmeerzeuugungsinfrastruktur mit einem entfernten Versorgungsgebiet verbindet)",
                    },
                    "8000": {
                        "name": "Strassenablaufleitung",
                        "alias": "Straßenablaufleitung",
                        "description": "Straßenablaufleitung (in der Abwasserentsorgung)",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstige Leitung",
                        "description": "Sonstige Leitung",
                    },
                },
                "typename": "XP_RohrleitungNetz",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    werkstoff: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "2000",
            "20001",
            "20002",
            "20003",
            "2500",
            "25001",
            "25002",
            "25003",
            "25004",
            "25005",
            "3000",
            "30001",
            "30002",
            "4000",
            "5000",
            "9999",
        ]
        | None,
        Field(
            description="Werkstoff der Leitung",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Kunststoff",
                        "alias": "Kunststoff",
                        "description": "Kunststoff",
                    },
                    "10001": {
                        "name": "Polyethylen_PE",
                        "alias": "Polyethylen ( PE)",
                        "description": "Polyethylen (PE)",
                    },
                    "10002": {
                        "name": "Polyethylen_PE_HD",
                        "alias": "High-Density Polyethylen",
                        "description": "High-Density Polyethylen",
                    },
                    "10003": {
                        "name": "Polypropylen_PP",
                        "alias": "Polypropylen ( PP)",
                        "description": "Polypropylen (PP)",
                    },
                    "10004": {
                        "name": "Polycarbonat_PC",
                        "alias": "Polycarbonat ( PC)",
                        "description": "Polycarbonat (PC)",
                    },
                    "10005": {
                        "name": "Polyvinylchlorid_PVC_U",
                        "alias": "Polyvinylchlorid ( PVC- U)",
                        "description": "Polyvinylchlorid (PVC-U)",
                    },
                    "2000": {"name": "Stahl", "alias": "Stahl", "description": "Stahl"},
                    "20001": {
                        "name": "StahlVerzinkt",
                        "alias": "Stahl verzinkt",
                        "description": "Stahl verzinkt",
                    },
                    "20002": {
                        "name": "Stahlgitter",
                        "alias": "Stahlgitter",
                        "description": "Stahlfachwerkskonstruktion (z.B. Freileitungsmast als Gittermast)",
                    },
                    "20003": {
                        "name": "Stahlrohr",
                        "alias": "Stahlrohr",
                        "description": "Rohrförmiger Profilstahl, dessen Wand aus Stahl besteht. Stahlrohre dienen der Durchleitung von flüssigen, gasförmigen oder festen Stoffen, oder werden als statische oder konstruktive Elemente verwendet (z.B. Freileitungsmast als Stahlrohrmast)",
                    },
                    "2500": {
                        "name": "Stahlverbundrohr",
                        "alias": "Stahlverbundrohr",
                        "description": "Stahlverbundrohre im Rohrleitungsbau",
                    },
                    "25001": {
                        "name": "St_PE",
                        "alias": "Stahlrohr mit Standard-Kunststoffumhüllung (PE)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PE-Basis",
                    },
                    "25002": {
                        "name": "St_PP",
                        "alias": "Stahlrohr mit Kunstoffumhüllung (PP)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PP-Basis für höhere Temperatur- und Härte-Anforderungen",
                    },
                    "25003": {
                        "name": "St_FZM",
                        "alias": "Stahlrohr mit FZM-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz durch Faserzementmörtel-Ummantelung (FZM)",
                    },
                    "25004": {
                        "name": "St_GFK",
                        "alias": "Stahlrohr mit GFK-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz aus glasfaserverstärktem Kunststoff (GFK) für höchste mechanische Abriebfestigkeit bei grabenlosem Rohrvortrieb",
                    },
                    "25005": {
                        "name": "St_ZM_PE",
                        "alias": "Stahl-Verbundrohr (ZM-PE)",
                        "description": "Stahlrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserohr)",
                    },
                    "3000": {
                        "name": "Gusseisen",
                        "alias": "Gusseisen",
                        "description": "Gusseisen",
                    },
                    "30001": {
                        "name": "GGG_ZM",
                        "alias": "duktiles Gussrohr mit ZM-Auskleidung",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung (z.B Abwasserrohr)",
                    },
                    "30002": {
                        "name": "GGG_ZM_PE",
                        "alias": "duktiles Guss-Verbundrohr (ZM-PE)",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserrohr)",
                    },
                    "4000": {
                        "name": "Beton",
                        "alias": "Beton",
                        "description": "Beton (z.B. Schacht)",
                    },
                    "5000": {
                        "name": "Holz",
                        "alias": "Holz",
                        "description": "Holz (z.B. Holzmast)",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiger Werkstoff",
                        "description": "Sonstiger Werkstoff",
                    },
                },
                "typename": "XP_Werkstoff",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BSTWegekante(BSTLinienobjekt):
    """Hervorzuhebende Wegekante im Umfeld einer Baumaßnahme"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Art der Wegekante",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Strassenkante",
                        "alias": "Straßenkante",
                        "description": "Straßenkante",
                    },
                    "2000": {
                        "name": "KanteFahrradweg",
                        "alias": "Kante Fahrradweg",
                        "description": "Kante Fahrradweg",
                    },
                    "3000": {
                        "name": "KanteGehweg",
                        "alias": "Kante Gehweg",
                        "description": "Kante Gehweg",
                    },
                },
                "typename": "BST_WegekanteTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class IGPMultiFlaechenobjekt(IGPObjekt):
    """Basisklasse für IGP-Objekte mit Multi-Flächengeometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiPolygon,
        Field(
            description="Raumbezug des Objektes",
            json_schema_extra={
                "typename": "GM_MultiSurface",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class IGPMultiLinienobjekt(IGPObjekt):
    """Basisklasse für IGP-Objekte mit Multi-Liniengeometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiLine,
        Field(
            description="Raumbezug des Objektes",
            json_schema_extra={
                "typename": "GM_MultiCurve",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class IGPMultiPunktobjekt(IGPObjekt):
    """Basisklasse für IGP-Objekte mit Multi-Punktgeometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiPoint,
        Field(
            description="Raumbezug des Objektes",
            json_schema_extra={
                "typename": "GM_MultiPoint",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class IPGelenkpunkt(IPObjekt):
    """Gelenkpunkte sind Schnittpunkte von Trassenkorridorsegmenten oder alternativen Trassenabschnitten (Trassenalternativen)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiPoint,
        Field(
            description="Raumbezug des Objektes",
            json_schema_extra={
                "typename": "GM_MultiPoint",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class IPNetzkopplungspunkt(IPObjekt):
    """Netzkopplungspunkte (NKP) verbinden zwei Gasnetze, meistens durch eine Gasddruckregel- und Messanlage. In Wasserstoffnetzen werden an Netzkopplungs- und -anschlusspunkten Leistungsparameter dargestellt."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiPoint,
        Field(
            description="Raumbezug des Objektes",
            json_schema_extra={
                "typename": "GM_MultiPoint",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]
    einAusspeisung: Annotated[
        IPEinAusspeisung | None,
        Field(
            description="Parameter der Ein- und Ausspeiseenergie (Alternative zur Datenerfassung über PFS_StationFlaeche)",
            json_schema_extra={
                "typename": "IP_EinAusspeisung",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class IPNetzverknuepfungspunkt(IPObjekt):
    """Netzverknüpfungspunkte (NVP) legen die Anfangs-, Zwischen- und Endpunkte von Stromnetzausbau-Vorhaben fest. In Raumverträglichkeitsprüfungen bilden diese "Zwangspunkte" Grenzen des Untersuchungsraums."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiPoint,
        Field(
            description="Raumbezug des Objektes",
            json_schema_extra={
                "typename": "GM_MultiPoint",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class IPPlan(XPNetzPlan):
    """Abstrakte Oberklasse für die Planklassen RVP_Plan, IGP_Plan und PFS_Plan. Fachobjekte der Fachschema RVP und IGP besitzen eine Referenz auf diese Plan-Oberklasse."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    hatIPObjekt: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            description="Referenz auf ein spezifisches Objekt des Infrastrukturplans",
            json_schema_extra={
                "typename": [
                    "IP_Gelenkpunkt",
                    "IP_Netzkopplungspunkt",
                    "IP_Netzverknuepfungspunkt",
                    "IP_Stationierungspunkt",
                ],
                "stereotype": "Association",
                "reverseProperty": "gehoertZuIP",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    hatIGPObjekt: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            description="Referenz auf ein spezifisches Objekt des Infrastrukturplans",
            json_schema_extra={
                "typename": [
                    "IGP_AusbauformWechsel",
                    "IGP_Infrastrukturgebiet",
                    "IGP_Kopplungsraum",
                    "IGP_MassnahmeFlaeche",
                    "IGP_MassnahmeLinie",
                    "IGP_MassnahmePunkt",
                ],
                "stereotype": "Association",
                "reverseProperty": "gehoertZuIP",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    hatRVPObjekt: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            description="Referenz auf ein spezifisches RVP-Objekt des Plans",
            json_schema_extra={
                "typename": [
                    "RVP_Engstelle",
                    "RVP_Grobkorridor",
                    "RVP_KonfliktRaumordnung",
                    "RVP_Linienkorridor",
                    "RVP_LinienkorridorSegment",
                    "RVP_PotenzialflaecheStandort",
                    "RVP_Raumwiderstand",
                    "RVP_Riegel",
                    "RVP_StandortInfrastruktur",
                    "RVP_Stationierungslinie",
                    "RVP_Suchraum",
                    "RVP_Trassenkorridor",
                    "RVP_TrassenkorridorAchse",
                    "RVP_TrassenkorridorSegment",
                ],
                "stereotype": "Association",
                "reverseProperty": "gehoertZuIP",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    externerDienst: Annotated[
        list[IPWebservice] | None,
        Field(
            description="externer Webdienst",
            json_schema_extra={
                "typename": "IP_Webservice",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None


class ISAFlaechenobjekt(ISAObjekt):
    """Basisklasse für ISA-Objekte mit Flächengeometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiPolygon,
        Field(
            description="Raumbezug des Objektes",
            json_schema_extra={
                "typename": "GM_MultiSurface",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class ISAGrundstueckLiegenschaft(ISAFlaechenobjekt):
    """Hierunter fallen sämtliche Grundstücke und Liegenschaften öffentlicher Stellen, jedoch keine Gebäude. Diese werden gesondert als Bauwerke erfasst.
    TYP: Z.B. Angaben zur Flächennutzung (wie Siedlungsfläche, Brachland, Wald, Landwirtschaftliche Fläche)
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    strom: Annotated[
        Literal["1000", "2000", "9999"],
        Field(
            description="Das Attribut der Stromversorgung gibt der an einer Mitnutzung interessierten Person Anhaltspunkte ob sich eine Trägerstruktur für die Errichtung von Standorten für drahtlose Zugangspunkte mit geringer Reichweite eignet. Ob die Stromversorgung nur temporär geschaltet ist, ist für eine Aufnahme der Einrichtung in den ISA nicht entscheidend.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "StromVorhanden",
                        "alias": "Strom vorhanden",
                        "description": "Stromversorgung ist vorhanden",
                    },
                    "2000": {
                        "name": "KeinStrom",
                        "alias": "kein Strom",
                        "description": "Keine Stromversorgung vorhanden",
                    },
                    "9999": {
                        "name": "keineAngabe",
                        "alias": "keine Angabe",
                        "description": "Informationen liegen nicht vor",
                    },
                },
                "typename": "ISA_Stromversorgung",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]


class ISAMultiLinienobjekt(ISAObjekt):
    """Basisklasse für ISA-Objekte mit Liniengeometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiLine,
        Field(
            description="Raumbezug des Objektes",
            json_schema_extra={
                "typename": "GM_MultiCurve",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class ISAMultiPunktobjekt(ISAObjekt):
    """Basisklasse für ISA-Objekte mit Punktgeometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiPoint,
        Field(
            description="Raumbezug des Objektes",
            json_schema_extra={
                "typename": "GM_MultiPoint",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]
    tiefe_hoehe: Annotated[
        int,
        Field(
            description="Angabe der Verlegetiefe (für POP, HVt, KVz, Zugangspunkt) oder der Höhe als positive Ganzzahl in cm.\r\n0 = Information liegt nicht vor.\r\nDie Verlegetiefe gibt der an einer Mitnutzung interessierten Person Anhaltspunkte für die Erreichbarkeit der unterirdischen Einrichtungen und hilft bei der Koordinierung von Bauarbeiten.\r\nDie Höhe gibt der an einer Mitnutzung interessierten Person Anhaltspunkte ob sich eine Trägerstruktur für die oberirdische Verlegung von Glasfaser aber auch für die Errichtung von Standorten für drahtlose Zugangspunkte mit geringer Reichweite eignet.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]


class ISAPointOfPresence(ISAMultiPunktobjekt):
    """Unter Point of Presence sind aktive Knotenpunkte des Glasfaser-Zugangsnetzes zu verstehen. Hierunter fallen nur Knotenpunkte von Telekommunikationsnetzen.
    TYP: Z.B. genauere Bezeichnung (wie Mini-POP)
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class ISAReklametafelLitfasssauele(ISAMultiPunktobjekt):
    """Hierunter fallen Anzeigentafeln und Litfaßsäulen die zu Reklamezwecken genutzt werden ebenso wie städtische Informationstafeln.
    TYP: Z.B. genauere Bezeichnung
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    strom: Annotated[
        Literal["1000", "2000", "9999"],
        Field(
            description="Das Attribut der Stromversorgung gibt der an einer Mitnutzung interessierten Person Anhaltspunkte ob sich eine Trägerstruktur für die Errichtung von Standorten für drahtlose Zugangspunkte mit geringer Reichweite eignet. Ob die Stromversorgung nur temporär geschaltet ist, ist für eine Aufnahme der Einrichtung in den ISA nicht entscheidend.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "StromVorhanden",
                        "alias": "Strom vorhanden",
                        "description": "Stromversorgung ist vorhanden",
                    },
                    "2000": {
                        "name": "KeinStrom",
                        "alias": "kein Strom",
                        "description": "Keine Stromversorgung vorhanden",
                    },
                    "9999": {
                        "name": "keineAngabe",
                        "alias": "keine Angabe",
                        "description": "Informationen liegen nicht vor",
                    },
                },
                "typename": "ISA_Stromversorgung",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]


class ISARichtfunkstrecke(ISAMultiLinienobjekt):
    """Hierunter fallen direkte Punkt-zu-Punkt-Verbindung per Funk.
    TYP: Angaben zur Frequenz
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class ISAStrassenlaterne(ISAMultiPunktobjekt):
    """Hierunter fällt öffentliche Straßenbeleuchtung (Straßenlaternen).
    TYP: Z.B. Angaben zur Art (wie Überspannungsanlage, Peitschenleuchte, Wandleuchte, Hängelampe, Hauswand, Pilzleuchte)
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    strom: Annotated[
        Literal["1000", "2000", "9999"],
        Field(
            description="Das Attribut der Stromversorgung gibt der an einer Mitnutzung interessierten Person Anhaltspunkte ob sich eine Trägerstruktur für die Errichtung von Standorten für drahtlose Zugangspunkte mit geringer Reichweite eignet. Ob die Stromversorgung nur temporär geschaltet ist, ist für eine Aufnahme der Einrichtung in den ISA nicht entscheidend.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "StromVorhanden",
                        "alias": "Strom vorhanden",
                        "description": "Stromversorgung ist vorhanden",
                    },
                    "2000": {
                        "name": "KeinStrom",
                        "alias": "kein Strom",
                        "description": "Keine Stromversorgung vorhanden",
                    },
                    "9999": {
                        "name": "keineAngabe",
                        "alias": "keine Angabe",
                        "description": "Informationen liegen nicht vor",
                    },
                },
                "typename": "ISA_Stromversorgung",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]


class ISAStrassenmobiliar(ISAMultiPunktobjekt):
    """Alle sonstigen physischen Infrastrukturen, die für den Ausbau von drahtlosen Zugangspunkten mit geringer Reichweite geeignet sind und unter keine der anderen Kategorien fallen. Es sind nur festmontierte und keine beweglichen oder temporär aufgestellten Infrastrukturen zu liefern. Es sind keine Sitzbänke und Abfallbehälter zu liefern.
    TYP: Z.B. genauere Bezeichnung
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    strom: Annotated[
        Literal["1000", "2000", "9999"],
        Field(
            description="Das Attribut der Stromversorgung gibt der an einer Mitnutzung interessierten Person Anhaltspunkte ob sich eine Trägerstruktur für die Errichtung von Standorten für drahtlose Zugangspunkte mit geringer Reichweite eignet. Ob die Stromversorgung nur temporär geschaltet ist, ist für eine Aufnahme der Einrichtung in den ISA nicht entscheidend.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "StromVorhanden",
                        "alias": "Strom vorhanden",
                        "description": "Stromversorgung ist vorhanden",
                    },
                    "2000": {
                        "name": "KeinStrom",
                        "alias": "kein Strom",
                        "description": "Keine Stromversorgung vorhanden",
                    },
                    "9999": {
                        "name": "keineAngabe",
                        "alias": "keine Angabe",
                        "description": "Informationen liegen nicht vor",
                    },
                },
                "typename": "ISA_Stromversorgung",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]


class ISAVerkehrsschild(ISAMultiPunktobjekt):
    """Hierunter fallen alle dauerhaft aufgestellte Verkehrszeichen in Form von Schildern. Nicht zu liefern sind Standorte von temporären Verkehrsschildern, z.B. an Baustellen, und Verkehrszeichen in Form von Markierungen, wie z.B. eingezeichnete Radwege oder sonstige Markierungen auf der Fahrbahnoberfläche.
    TYP: Z.B. Angaben zur Art (wie Verkehrs- oder Parkleitsystem, Vorwegweiser, Autobahn-/Brückenbeschilderung)
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    strom: Annotated[
        Literal["1000", "2000", "9999"],
        Field(
            description="Das Attribut der Stromversorgung gibt der an einer Mitnutzung interessierten Person Anhaltspunkte ob sich eine Trägerstruktur für die Errichtung von Standorten für drahtlose Zugangspunkte mit geringer Reichweite eignet. Ob die Stromversorgung nur temporär geschaltet ist, ist für eine Aufnahme der Einrichtung in den ISA nicht entscheidend.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "StromVorhanden",
                        "alias": "Strom vorhanden",
                        "description": "Stromversorgung ist vorhanden",
                    },
                    "2000": {
                        "name": "KeinStrom",
                        "alias": "kein Strom",
                        "description": "Keine Stromversorgung vorhanden",
                    },
                    "9999": {
                        "name": "keineAngabe",
                        "alias": "keine Angabe",
                        "description": "Informationen liegen nicht vor",
                    },
                },
                "typename": "ISA_Stromversorgung",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]


class ISAZugangspunkt(ISAMultiPunktobjekt):
    """Hierunter fallen Netzzugangspunkte mit physischem Zugang zu bestehenden Leer- und Schutzrohrnetzen oder Glasfaserleitungen wie z.B. Muffen, Einstiegsschächte, Erdschächte, Fitting, Steuer-/Schaltschränke, Stromverteiler(kästen), Kabelschächte, nicht-begehbare Trafostationen. Einstiegsschächte für Abwasserleitungen sind nicht zu liefern.
    TYP: Z.B. genauere Bezeichnung wie Steuergeräte, Lichtsignalanlagen, Manholes, Handholes, Schaltverteiler, Standverteiler
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class PFSAlternativeTrasseAbschnitt(PFSTrasse):
    """Trassenabschnitt/-segment eines alternativen Verlaufs"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    variante: Annotated[
        str | None,
        Field(
            description="Bezeichnung der Variante",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class PFSLeitung(PFSTrasse):
    """Basisklasse für PFS-Leitungsobjekte mit Liniengeometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    bauweise: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Bauweise im Trassenabschnitt",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "OffeneBauweise",
                        "alias": "offene Bauweise",
                        "description": "offene Bauweise",
                    },
                    "2000": {
                        "name": "GeschlosseneBauweise",
                        "alias": "geschlossene Bauweise",
                        "description": "geschlossene Bauweise",
                    },
                    "3000": {
                        "name": "Oberirdisch",
                        "alias": "oberirdische Verlegung",
                        "description": "oberirdische Verlegung",
                    },
                },
                "typename": "XP_Bauweise",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    legeverfahren: Annotated[
        Literal[
            "1000",
            "2000",
            "3000",
            "4000",
            "5000",
            "6000",
            "60001",
            "60002",
            "7000",
            "8000",
            "9000",
            "9999",
        ]
        | None,
        Field(
            description="Legeverfahren/Verlegemethode im Trassenabschnitt",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Konventionell_offenerGraben",
                        "alias": "Konventionelle Verlegung im offenen Graben",
                        "description": "Ausschachtung mit Schaufel, Bagger, Fräse",
                    },
                    "2000": {
                        "name": "Pressbohrverfahren",
                        "alias": "Pressbohrverfahren",
                        "description": 'Unterirdische Verlegetechnik, die in verschiedenen Varianten zur Anwendung kommt (statisch, dynamisch, ungesteuert, gesteuert) und von Herstellern spezifisch bezeichnet wird ("Modifiziertes Direct-Pipe-Verfahren").  Im Breitbandausbau auch als Erdraketentechnik bekannt. Im Rohrleitungsbau können durch hydraulische oder pneumatische Presseinrichtungen Produktenrohrkreuzungen DN 1000 bis zu 100 m grabenlos verlegt werden.',
                    },
                    "3000": {
                        "name": "HorizontalSpuelbohrverfahren",
                        "alias": "Horizontal-Spülbohrverfahren",
                        "description": "Richtbohrtechnik für Horizontalbohrungen („Horizontal Directional Drilling“, HDD), die eine grabenlose Verlegung von Produkt- oder Leerrohren ermöglicht.  Die Bohrung ist anfangs meist schräg nach unten in das Erdreich gerichtet und verläuft dann in leichtem Bogen zum Ziel, wo sie schräg nach oben wieder zutage tritt.",
                    },
                    "4000": {
                        "name": "Pflugverfahren",
                        "alias": "Pflugverfahren",
                        "description": "Erstellung eines Leitungsgrabens (Breite > 30cm) oder Schlitzes mit einem Pflugschwert durch Verdrängung der Schicht(en) und gleichzeitigem Einbringen der Glasfasermedien. Der Einsatz des Pflugverfahrens ist ausschließlich in unbefestigten Oberflächen zulässig.",
                    },
                    "5000": {
                        "name": "Fraesverfahren_ungebundeOberfl",
                        "alias": "Fräsverfahren in ungebundenen Oberflächen",
                        "description": "Fräsverfahren in ungebunden Oberflächen (Schlitzbreite: 15 bis 30 cm, Schlitztiefe: 40 bis 120 cm)",
                    },
                    "6000": {
                        "name": "Trenching",
                        "alias": "Trenching",
                        "description": "Erstellung eines Schlitzes (< 30 cm) in gebundenen Verkehrsflächen in verschiedenen Verfahren durch rotierende, senkrecht stehende Werkzeuge, wobei die Schicht(en) gelöst, zerkleinert und gefördert wird (werden)",
                    },
                    "60001": {
                        "name": "Schleif_Saegeverfahren",
                        "alias": "Schleif-/Sägeverfahren",
                        "description": "Erstellung eines Schlitzes eine durch eine Schneideeinheit (Schlitzbreite: 1,5 bis 11 cm, Schlitztiefe: 7 bis 45 cm)",
                    },
                    "60002": {
                        "name": "Fraesverfahren",
                        "alias": "Fräsverfahren",
                        "description": "Erstellung eines Schlitzes durch ein Fräswerkzeug (Kette, Rad), (Schlitzbreite: 5 bis 15 cm, Schlitztiefe: 30 bis 60 cm)",
                    },
                    "7000": {
                        "name": "Rammverfahren",
                        "alias": "Rammverfahren",
                        "description": "Vortriebsverfahren, welches durch hydraulisches oder pneumatisches Vibrationsrammen das Rohr unter dem Hindernis hindurch schlägt. Mit dem Rammverfahren können Produkten- oder Mantelrohrkreuzungen bis zu 100 m Vortriebslänge grabenlos verlegt werden.",
                    },
                    "8000": {
                        "name": "Microtunneling",
                        "alias": "Microtunneling",
                        "description": "Für den grabenlosen Vortrieb werden in dem steuerbaren Verfahren zunächst Stahlbetonrohre mit großem Nenndurchmesser verlegt,  in denen nach Durchführung der Unterquerung das eigentliche Produktenrohr eingebracht/eingezogen wird. Es kommt nur bei schwierigen Kreuzungen zur Anwendung.",
                    },
                    "9000": {
                        "name": "oberirdischeVerlegung",
                        "alias": "oberirdische Verlegung",
                        "description": "oberirdische Verlegung mittels Holzmasten",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiges Verfahren",
                        "description": "Sonstiges Verfahren",
                    },
                },
                "typename": "XP_Legeverfahren",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    schutzstreifen: Annotated[
        PFSSchutzstreifenData | None,
        Field(
            description="Angaben zum Schutzstreifen",
            json_schema_extra={
                "typename": "PFS_SchutzstreifenData",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    arbeitsstreifen: Annotated[
        PFSArbeitsstreifenData | None,
        Field(
            description="Angaben zum Arbeitsstreifen",
            json_schema_extra={
                "typename": "PFS_ArbeitsstreifenData",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    schutzrohr: Annotated[
        list[PFSSchutzrohr] | None,
        Field(
            description="Im Trassenabschnitt verlegtes Kabelschutzrohr mit und ohne funktionalem Bezug zur Leitung",
            json_schema_extra={
                "typename": "PFS_Schutzrohr",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None


class PFSMittelspannungsleitung(PFSLeitung):
    """Freileitung/Erdkabel  mit einer Nennspannung von unter 110 kV oder Bahnstromfernleitung, die gemäß § 43, Abs. 2, Satz 5 ENWG in ein Planfeststellungsverfahren integriert werden können"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    erdkabel: Annotated[
        PFSErdkabel | None,
        Field(
            description="Leitungsabschnitt als Erdkabel ( XP_Leitungstyp = Erdkabel)",
            json_schema_extra={
                "typename": "PFS_Erdkabel",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class PFSMultiFlaechenobjekt(PFSObjekt):
    """Basisklasse für PFS-Objekte mit Flächengeometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiPolygon,
        Field(
            description="Raumbezug des Objektes",
            json_schema_extra={
                "typename": "GM_MultiSurface",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class PFSMultiPunktobjekt(PFSObjekt):
    """Basisklasse für PFS-Objekte mit Multi-Punktgeometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiPoint,
        Field(
            description="Raumbezug des Objektes",
            json_schema_extra={
                "typename": "GM_MultiPoint",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class PFSMultiVerkehrsweg(PFSObjekt):
    """Basisklasse für PFS-Verkehrswegeobjekte mit Liniengeometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiLine,
        Field(
            description="Raumbezug des Objektes",
            json_schema_extra={
                "typename": "GM_MultiCurve",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]
    breite: Annotated[
        definitions.Length | None,
        Field(
            description="Angabe in m.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None


class PFSPlan(IPPlan):
    """Klasse zur Modellierung eines Planfeststellungsverfahrens"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    hatPFSObjekt: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            description="Referenz auf ein spezifisches Objekt des PFS-Plans",
            json_schema_extra={
                "typename": [
                    "PFS_AlternativeTrasseAbschnitt",
                    "PFS_Armaturengruppe",
                    "PFS_Baugrube",
                    "PFS_BaugrubeFlaeche",
                    "PFS_Baustelle",
                    "PFS_Energiekopplungsanlage",
                    "PFS_Energiespeicher",
                    "PFS_GasversorgungsleitungAbschnitt",
                    "PFS_Gleis",
                    "PFS_HochspannungsleitungAbschnitt",
                    "PFS_Hochspannungsmast",
                    "PFS_Kanal",
                    "PFS_Kraftwerk",
                    "PFS_Messpfahl",
                    "PFS_Mittelspannungsleitung",
                    "PFS_Schutzstreifen",
                    "PFS_Station",
                    "PFS_StationFlaeche",
                    "PFS_Strasse",
                    "PFS_Umspannwerk",
                    "PFS_WaermeleitungAbschnitt",
                ],
                "stereotype": "Association",
                "reverseProperty": "gehoertZuPFS",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    status: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Status des Planfeststellungsverfahrens",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Antrag",
                        "alias": "Antrag",
                        "description": "Antrag auf Planfeststellung zum Bau und Betrieb von Leitungen und Infrastrukturobjekten",
                    },
                    "2000": {
                        "name": "Planergaenzung",
                        "alias": "Planergänzung",
                        "description": 'Planergänzung oder ergänzendes Verfahren im Sinne des § 75 Abs. 1a Satz 2 des Verwaltungsverfahrensgesetzes. Ergänzte PFS_Objekte müssen über das Attribut "planErgaezungAenderung" = true belegt werden.',
                    },
                    "3000": {
                        "name": "Planaenderung",
                        "alias": "Planänderung",
                        "description": 'Planänderung vor Fertigstellung des Vorhabens im Sinne § 76 Abs. 1 des Verwaltungsverfahrensgesetzes. Geänderte PFS_Objekte müssen über das Attribut "planErgaenzungAenderung" = true belegt werden.',
                    },
                },
                "typename": "PFS_PlanStatus",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    beteiligte: Annotated[
        list[XPAkteur] | None,
        Field(
            description="zentrale Akteure des Verfahrens",
            json_schema_extra={
                "typename": "XP_Akteur",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    antragDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Antrages (oder Datum des Erläuterungsberichts)",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    antragskonferenzDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum der Antragskonferenz",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    traegerbeteiligungStartDatum: Annotated[
        date_aliased | None,
        Field(
            description="Startdatum der Beteiligung der Behörden, deren Aufgabenbereich durch das Vorhaben berührt wird",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    traegerbeteiligungEndDatum: Annotated[
        date_aliased | None,
        Field(
            description="Ende der Trägerbeteiligung",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    auslegungGemeinden: Annotated[
        list[XPAuslegung] | None,
        Field(
            description="Gemeinden, in denen Planunterlagen ausgelegt werden oder wurden, da sich das Vorhaben voraussichtlich auswirken wird",
            json_schema_extra={
                "typename": "XP_Auslegung",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    auslegungInternetStartDatum: Annotated[
        date_aliased | None,
        Field(
            description="Startdatum der verwöchigen Veröffentlichung der Planunterlagen im Internet",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    auslegungInternetEndDatum: Annotated[
        date_aliased | None,
        Field(
            description='Enddatum für die "Auslegung" im Intenet',
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    planfeststellungsbeschlussDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum der Planfeststellung",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    referenzRVP: Annotated[
        PFSVersionRVP | None,
        Field(
            description="Vorausgegangene Raumverträglichkeitsprüfung, dessen Konkretisierung das Planfestellungsverfahren ist",
            json_schema_extra={
                "typename": "PFS_VersionRVP",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class PFSSchutzstreifen(PFSMultiFlaechenobjekt):
    """Dinglich zu sichernder Schutzstreifen (entspricht dem Attribut "schutzstreifen" im DataType PFS_Schutzstreifen)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class PFSStation(PFSMultiPunktobjekt):
    """Knoten innerhalb eines Infrastrukturnetzes oder zwischen Infrastrukturnetzen mit identischem Transportmedium"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "10006",
            "10007",
            "2000",
            "20001",
            "20002",
            "20003",
            "3000",
            "9999",
        ]
        | None,
        Field(
            description="Art der Station",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "StationGas",
                        "alias": "Station Gas",
                        "description": "Station für Medium Gas (Wasserstoff/Erdgas)",
                    },
                    "10001": {
                        "name": "Schieberstation",
                        "alias": "Schieberstation",
                        "description": "Über eine Schieberstation (Abzweigstation?)  kann mit Hilfe der dort installierten Kugelhähne der Gasfluss gestoppt bzw. umgelenkt werden",
                    },
                    "10002": {
                        "name": "Verdichterstation",
                        "alias": "Verdichterstation",
                        "description": "Eine Verdichterstation (Kompressorstation) ist eine Anlage in einer Transportleitung, bei der ein Kompressor das Gas wieder komprimiert, um Rohr-Druckverluste auszugleichen und den Volumenstrom zu regeln",
                    },
                    "10003": {
                        "name": "Regel_Messstation",
                        "alias": "Regel- und Messstation",
                        "description": "Eine Gas-Druckregelanlage (GDRA) ist eine Anlage zur ein- oder mehrstufigen Gas-Druckreduzierung. Bei einer Gas-Druckregel- und Messanlage (GDRMA) wird zusätzlich noch die Gas-Mengenmessung vorgenommen. (Anmerkung: Einspeise- und Übergabestationen können separat erfasst werden)",
                    },
                    "10004": {
                        "name": "Armaturstation",
                        "alias": "Armaturstation",
                        "description": "Kombination von Armaturengruppen wie Absperr- und und Abgangsarmaturengruppen",
                    },
                    "10005": {
                        "name": "Einspeisestation",
                        "alias": "Einspeisestation",
                        "description": "Die Einspeisungs- oder Empfangsstation leitet Erdgas oder Wasserstoff in ein Transportleitungsnetz. Die Einspeisung erfolgt z.B. aus einer Produktions- oder Speicheranlage oder über ein LNG-Terminal nach der Regasifizierung.",
                    },
                    "10006": {
                        "name": "Uebergabestation",
                        "alias": "Übergabe-/Entnahmestation",
                        "description": "Gas-Übergabestationen (auch Übernahme- oder Entnahmestation) dienen i.d.R. der Verteilung von Gas aus Transportleitungen in die Verbrauchernetze. Dafür muss das ankommende Gas heruntergeregelt werden. Wird Wasserstoff in ein Erdgasleitungsnetz übergeben, muss zusätzlich ein Mischer an der Übernahmestelle gewährleisten, dass sich Wasserstoff und Erdgas gleichmäßig durchmischen. \r\nEine weitere Variante ist die Übergabe von Gas an ein Kraftwerk.",
                    },
                    "10007": {
                        "name": "Molchstation",
                        "alias": "Molchstation",
                        "description": "Station um Molchungen zur Prüfung der Integrität der Fernleitung während der Betriebsphase durchzuführen.  \r\nDer Molch füllt den Leitungsquerschnitt aus und wandert entweder einfach mit dem Produktstrom durch die Leitung (meist bei Öl) oder wird durch Druck durch die Leitung gepresst. Im Rahmen der Molchtechnik werden neben dem Molch noch ins System eingebaute Schleusen benötigt, durch die der Molch in die Leitungen eingesetzt bzw. herausgenommen und von hinten mit Druck belegt werden kann.",
                    },
                    "2000": {
                        "name": "StationStrom",
                        "alias": "Station Strom",
                        "description": "Station für Medium Strom",
                    },
                    "20001": {
                        "name": "Transformatorenstation",
                        "alias": "Transformatorenstation",
                        "description": "In einer Transformatorenstation (Umspannstation, Netzstation, Ortsnetzstation oder kurz Trafostation) wird die elektrische Energie aus dem Mittelspannungsnetz mit einer elektrischen Spannung von 10 kV bis 36 kV auf die in Niederspannungsnetzen (Ortsnetzen) verwendeten 400/230 V zur allgemeinen Versorgung transformiert",
                    },
                    "20002": {
                        "name": "Konverterstation",
                        "alias": "Konverterstation",
                        "description": "Ein Konverter steht an den Verbindungspunkten von Gleich- und Wechselstromleitungen. Er verwandelt Wechsel- in Gleichstrom und kann ebenso Gleichstrom wieder zurück in Wechselstrom umwandeln und diesen ins Übertragungsnetz einspeisen.",
                    },
                    "20003": {
                        "name": "Phasenschieber",
                        "alias": "Phasenschieber",
                        "description": "Phasenschiebertransformatoren (PST), auch Querregler genannt, werden zur Steuerung der Stromflüsse zwischen Übertragungsnetzen eingesetzt. Der Phasenschiebertransformator speist einen Ausgleichsstrom in das System ein, der den Laststrom in der Leitung entweder verringert oder erhöht. Sinkt der Stromfluss in einer Leitung, werden die Stromflüsse im gesamten Verbundsystem neu verteilt.",
                    },
                    "3000": {
                        "name": "StationWaerme",
                        "alias": "Station (Fern-)Wärme",
                        "description": "Station im (Fern-)Wärmenetz",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstige Station",
                        "description": "Sonstige Station",
                    },
                },
                "typename": "XP_StationTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class PFSStationFlaeche(PFSMultiFlaechenobjekt):
    """Knoten innerhalb eines Infrastrukturnetzes oder zwischen Infrastrukturnetzen mit identischem Transportmedium (alternative Spezifizierung zu PFS_Station)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "10006",
            "10007",
            "2000",
            "20001",
            "20002",
            "20003",
            "3000",
            "9999",
        ]
        | None,
        Field(
            description="Art der Station",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "StationGas",
                        "alias": "Station Gas",
                        "description": "Station für Medium Gas (Wasserstoff/Erdgas)",
                    },
                    "10001": {
                        "name": "Schieberstation",
                        "alias": "Schieberstation",
                        "description": "Über eine Schieberstation (Abzweigstation?)  kann mit Hilfe der dort installierten Kugelhähne der Gasfluss gestoppt bzw. umgelenkt werden",
                    },
                    "10002": {
                        "name": "Verdichterstation",
                        "alias": "Verdichterstation",
                        "description": "Eine Verdichterstation (Kompressorstation) ist eine Anlage in einer Transportleitung, bei der ein Kompressor das Gas wieder komprimiert, um Rohr-Druckverluste auszugleichen und den Volumenstrom zu regeln",
                    },
                    "10003": {
                        "name": "Regel_Messstation",
                        "alias": "Regel- und Messstation",
                        "description": "Eine Gas-Druckregelanlage (GDRA) ist eine Anlage zur ein- oder mehrstufigen Gas-Druckreduzierung. Bei einer Gas-Druckregel- und Messanlage (GDRMA) wird zusätzlich noch die Gas-Mengenmessung vorgenommen. (Anmerkung: Einspeise- und Übergabestationen können separat erfasst werden)",
                    },
                    "10004": {
                        "name": "Armaturstation",
                        "alias": "Armaturstation",
                        "description": "Kombination von Armaturengruppen wie Absperr- und und Abgangsarmaturengruppen",
                    },
                    "10005": {
                        "name": "Einspeisestation",
                        "alias": "Einspeisestation",
                        "description": "Die Einspeisungs- oder Empfangsstation leitet Erdgas oder Wasserstoff in ein Transportleitungsnetz. Die Einspeisung erfolgt z.B. aus einer Produktions- oder Speicheranlage oder über ein LNG-Terminal nach der Regasifizierung.",
                    },
                    "10006": {
                        "name": "Uebergabestation",
                        "alias": "Übergabe-/Entnahmestation",
                        "description": "Gas-Übergabestationen (auch Übernahme- oder Entnahmestation) dienen i.d.R. der Verteilung von Gas aus Transportleitungen in die Verbrauchernetze. Dafür muss das ankommende Gas heruntergeregelt werden. Wird Wasserstoff in ein Erdgasleitungsnetz übergeben, muss zusätzlich ein Mischer an der Übernahmestelle gewährleisten, dass sich Wasserstoff und Erdgas gleichmäßig durchmischen. \r\nEine weitere Variante ist die Übergabe von Gas an ein Kraftwerk.",
                    },
                    "10007": {
                        "name": "Molchstation",
                        "alias": "Molchstation",
                        "description": "Station um Molchungen zur Prüfung der Integrität der Fernleitung während der Betriebsphase durchzuführen.  \r\nDer Molch füllt den Leitungsquerschnitt aus und wandert entweder einfach mit dem Produktstrom durch die Leitung (meist bei Öl) oder wird durch Druck durch die Leitung gepresst. Im Rahmen der Molchtechnik werden neben dem Molch noch ins System eingebaute Schleusen benötigt, durch die der Molch in die Leitungen eingesetzt bzw. herausgenommen und von hinten mit Druck belegt werden kann.",
                    },
                    "2000": {
                        "name": "StationStrom",
                        "alias": "Station Strom",
                        "description": "Station für Medium Strom",
                    },
                    "20001": {
                        "name": "Transformatorenstation",
                        "alias": "Transformatorenstation",
                        "description": "In einer Transformatorenstation (Umspannstation, Netzstation, Ortsnetzstation oder kurz Trafostation) wird die elektrische Energie aus dem Mittelspannungsnetz mit einer elektrischen Spannung von 10 kV bis 36 kV auf die in Niederspannungsnetzen (Ortsnetzen) verwendeten 400/230 V zur allgemeinen Versorgung transformiert",
                    },
                    "20002": {
                        "name": "Konverterstation",
                        "alias": "Konverterstation",
                        "description": "Ein Konverter steht an den Verbindungspunkten von Gleich- und Wechselstromleitungen. Er verwandelt Wechsel- in Gleichstrom und kann ebenso Gleichstrom wieder zurück in Wechselstrom umwandeln und diesen ins Übertragungsnetz einspeisen.",
                    },
                    "20003": {
                        "name": "Phasenschieber",
                        "alias": "Phasenschieber",
                        "description": "Phasenschiebertransformatoren (PST), auch Querregler genannt, werden zur Steuerung der Stromflüsse zwischen Übertragungsnetzen eingesetzt. Der Phasenschiebertransformator speist einen Ausgleichsstrom in das System ein, der den Laststrom in der Leitung entweder verringert oder erhöht. Sinkt der Stromfluss in einer Leitung, werden die Stromflüsse im gesamten Verbundsystem neu verteilt.",
                    },
                    "3000": {
                        "name": "StationWaerme",
                        "alias": "Station (Fern-)Wärme",
                        "description": "Station im (Fern-)Wärmenetz",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstige Station",
                        "description": "Sonstige Station",
                    },
                },
                "typename": "XP_StationTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    einAusspeisung: Annotated[
        IPEinAusspeisung | None,
        Field(
            description="Leistung der Einspeise- oder Übergabestation (Alternative zur Datenerfassung über IP_Netzkopplungspunkt)",
            json_schema_extra={
                "typename": "IP_EinAusspeisung",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    begrenzung: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Bestimmung der dargestellten Fläche",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Betriebsgelaende",
                        "alias": "Betriebsgelände",
                        "description": "gesamtes Betriebsgelände bzw. Grundstücksfläche",
                    },
                    "2000": {
                        "name": "EingezaeunteFlaeche",
                        "alias": "eingezäunte Fläche",
                        "description": "eingezäuntes Gelände der Infrastrukturgebäude (ohne Parkplätze und Nebengebäude)",
                    },
                    "3000": {
                        "name": "Gebaeudeflaeche",
                        "alias": "Gebäudefläche",
                        "description": "Fläche eines Gebäudes, das technische Anlagen enthält",
                    },
                },
                "typename": "XP_InfrastrukturFlaeche",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class PFSStrasse(PFSMultiVerkehrsweg):
    """Klassifizierte Straßen (Autobahn, Bundesstraßen, Landstraßen, Kreisstraßen)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class PFSUmspannwerk(PFSMultiFlaechenobjekt):
    """Knoten eines elektrischen Versorgungsnetzes, um Netze mit verschiedenen Spannungsebenen (z. B. 380 kV und 110 kV) durch Transformatoren zu verbinden. Ebenso können Teile des Netzes gleicher Spannung in Schaltanlagen miteinander verbunden oder abgeschaltet werden. Kleinere Umspannanlagen, in denen Mittel- auf Niederspannung transformiert wird, gehören zu den Stationen (s. PFS_Station und PFS_StationFlaeche)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    begrenzung: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Bestimmung der dargestellten Fläche",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Betriebsgelaende",
                        "alias": "Betriebsgelände",
                        "description": "gesamtes Betriebsgelände bzw. Grundstücksfläche",
                    },
                    "2000": {
                        "name": "EingezaeunteFlaeche",
                        "alias": "eingezäunte Fläche",
                        "description": "eingezäuntes Gelände der Infrastrukturgebäude (ohne Parkplätze und Nebengebäude)",
                    },
                    "3000": {
                        "name": "Gebaeudeflaeche",
                        "alias": "Gebäudefläche",
                        "description": "Fläche eines Gebäudes, das technische Anlagen enthält",
                    },
                },
                "typename": "XP_InfrastrukturFlaeche",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class PFSWaermeleitungAbschnitt(PFSLeitung):
    """Abschnitt einer (Fern-)Wärmeleitung. Der Abschnitt ist Bestandteil der Antrags- oder Vorzugstrasse."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"],
        Field(
            description="Art des transportierten Gases",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Strang",
                        "alias": "Strang",
                        "description": "Schematische Darstellung als Strang (mit Vor- und Rücklauf)",
                    },
                    "2000": {
                        "name": "Vorlauf",
                        "alias": "Vorlauf",
                        "description": "Vorlaufrohr",
                    },
                    "3000": {
                        "name": "Ruecklauf",
                        "alias": "Rücklauf",
                        "description": "Rücklaufrohr",
                    },
                    "4000": {
                        "name": "Doppelrohr",
                        "alias": "Doppelrohr",
                        "description": "Vor- und Rücklauf in einem Doppelrohr",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiger Typ",
                        "description": "Sonstiger Typ",
                    },
                },
                "typename": "XP_WaermeleitungTyp",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    netzEbene: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "6000", "7000", "8000", "9999"]
        | None,
        Field(
            description="Leitungsart im Gasnetz",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Fernleitung",
                        "alias": "Fernleitung",
                        "description": "Fernleitung gemäß Umweltverträglichkeitsprüfung (UVPG), Anlage 1 und ENWG § 3, Nr. 19d/20; Leitungen der Fernleitungsnetzbetreiber",
                    },
                    "2000": {
                        "name": "Verteilnetzleitung",
                        "alias": "Verteilnetzleitung",
                        "description": "Leitung eines Verteil(er)netzes; Leitungen der Versorgungsunternehmen",
                    },
                    "3000": {
                        "name": "Hauptleitung",
                        "alias": "Hauptleitung",
                        "description": "Hauptleitung, oberste Leitungskategorie in einem Trinkwasser und Wärmenetz",
                    },
                    "4000": {
                        "name": "Versorgungsleitung",
                        "alias": "Versorgungsleitung",
                        "description": "Versorgungsleitung, auch Ortsleitung (z.B Wasserleitungen innerhalb des Versorgungsgebietes im bebauten Bereich)",
                    },
                    "5000": {
                        "name": "Zubringerleitung",
                        "alias": "Zubringerleitung",
                        "description": "Zubringerleitung (z.B. Wasserleitungen zwischen Wassergewinnungs- und Versorgungsgebieten)",
                    },
                    "6000": {
                        "name": "Anschlussleitung",
                        "alias": "Hausanschlussleitung",
                        "description": "Anschlussleitung, Hausanschluss (z.B. Wasserleitungen von der Abzweigstelle der Versorgungsleitung bis zur Übergabestelle/Hauptabsperreinrichtung)",
                    },
                    "7000": {
                        "name": "Verbindungsleitung",
                        "alias": "Verbindungsleitung",
                        "description": "Verbindungsleitung (z.B. Wasserleitungen außerhalb der Versorgungsgebiete, die Versorgungsgebiete (Orte) miteinander verbinden), in der Wärmeversorung auch Transportleitung genannt (die eine Wärmeerzeuugungsinfrastruktur mit einem entfernten Versorgungsgebiet verbindet)",
                    },
                    "8000": {
                        "name": "Strassenablaufleitung",
                        "alias": "Straßenablaufleitung",
                        "description": "Straßenablaufleitung (in der Abwasserentsorgung)",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstige Leitung",
                        "description": "Sonstige Leitung",
                    },
                },
                "typename": "XP_RohrleitungNetz",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    regelueberdeckung: Annotated[
        definitions.Length | None,
        Field(
            description="Mindestabstand zwischen Oberkante des Weges und Oberkante des Rohres/Kabels in m.\r\n(gml:LengthType: uom=“m“ oder uom=“urn:adv:uom:m“)",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    nennweite: Annotated[
        str | None,
        Field(
            description='Die Nennweite DN ("diamètre nominal", "Durchmesser nach Norm") ist eine numerische Bezeichnung der ungefähren Durchmesser von Bauteilen in einem Rohrleitungssystem, die laut EN ISO 6708 "für Referenzzwecke verwendet wird".',
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    aussendurchmesser: Annotated[
        definitions.Length | None,
        Field(
            description="Außendurchmesser in m.\r\n(gml:LengthType: uom=“m“ oder uom=“urn:adv:uom:m“)",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    werkstoff: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "2000",
            "20001",
            "20002",
            "20003",
            "2500",
            "25001",
            "25002",
            "25003",
            "25004",
            "25005",
            "3000",
            "30001",
            "30002",
            "4000",
            "5000",
            "9999",
        ]
        | None,
        Field(
            description="Werkstoff der Leitung",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Kunststoff",
                        "alias": "Kunststoff",
                        "description": "Kunststoff",
                    },
                    "10001": {
                        "name": "Polyethylen_PE",
                        "alias": "Polyethylen ( PE)",
                        "description": "Polyethylen (PE)",
                    },
                    "10002": {
                        "name": "Polyethylen_PE_HD",
                        "alias": "High-Density Polyethylen",
                        "description": "High-Density Polyethylen",
                    },
                    "10003": {
                        "name": "Polypropylen_PP",
                        "alias": "Polypropylen ( PP)",
                        "description": "Polypropylen (PP)",
                    },
                    "10004": {
                        "name": "Polycarbonat_PC",
                        "alias": "Polycarbonat ( PC)",
                        "description": "Polycarbonat (PC)",
                    },
                    "10005": {
                        "name": "Polyvinylchlorid_PVC_U",
                        "alias": "Polyvinylchlorid ( PVC- U)",
                        "description": "Polyvinylchlorid (PVC-U)",
                    },
                    "2000": {"name": "Stahl", "alias": "Stahl", "description": "Stahl"},
                    "20001": {
                        "name": "StahlVerzinkt",
                        "alias": "Stahl verzinkt",
                        "description": "Stahl verzinkt",
                    },
                    "20002": {
                        "name": "Stahlgitter",
                        "alias": "Stahlgitter",
                        "description": "Stahlfachwerkskonstruktion (z.B. Freileitungsmast als Gittermast)",
                    },
                    "20003": {
                        "name": "Stahlrohr",
                        "alias": "Stahlrohr",
                        "description": "Rohrförmiger Profilstahl, dessen Wand aus Stahl besteht. Stahlrohre dienen der Durchleitung von flüssigen, gasförmigen oder festen Stoffen, oder werden als statische oder konstruktive Elemente verwendet (z.B. Freileitungsmast als Stahlrohrmast)",
                    },
                    "2500": {
                        "name": "Stahlverbundrohr",
                        "alias": "Stahlverbundrohr",
                        "description": "Stahlverbundrohre im Rohrleitungsbau",
                    },
                    "25001": {
                        "name": "St_PE",
                        "alias": "Stahlrohr mit Standard-Kunststoffumhüllung (PE)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PE-Basis",
                    },
                    "25002": {
                        "name": "St_PP",
                        "alias": "Stahlrohr mit Kunstoffumhüllung (PP)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PP-Basis für höhere Temperatur- und Härte-Anforderungen",
                    },
                    "25003": {
                        "name": "St_FZM",
                        "alias": "Stahlrohr mit FZM-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz durch Faserzementmörtel-Ummantelung (FZM)",
                    },
                    "25004": {
                        "name": "St_GFK",
                        "alias": "Stahlrohr mit GFK-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz aus glasfaserverstärktem Kunststoff (GFK) für höchste mechanische Abriebfestigkeit bei grabenlosem Rohrvortrieb",
                    },
                    "25005": {
                        "name": "St_ZM_PE",
                        "alias": "Stahl-Verbundrohr (ZM-PE)",
                        "description": "Stahlrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserohr)",
                    },
                    "3000": {
                        "name": "Gusseisen",
                        "alias": "Gusseisen",
                        "description": "Gusseisen",
                    },
                    "30001": {
                        "name": "GGG_ZM",
                        "alias": "duktiles Gussrohr mit ZM-Auskleidung",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung (z.B Abwasserrohr)",
                    },
                    "30002": {
                        "name": "GGG_ZM_PE",
                        "alias": "duktiles Guss-Verbundrohr (ZM-PE)",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserrohr)",
                    },
                    "4000": {
                        "name": "Beton",
                        "alias": "Beton",
                        "description": "Beton (z.B. Schacht)",
                    },
                    "5000": {
                        "name": "Holz",
                        "alias": "Holz",
                        "description": "Holz (z.B. Holzmast)",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiger Werkstoff",
                        "description": "Sonstiger Werkstoff",
                    },
                },
                "typename": "XP_Werkstoff",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class RVPLinienkorridor(RVPObjekt):
    """Alternativ zur Klasse RVP_TrassenkorridorSegment stellt diese Klasse den Trassenkorridor als Linie dar, die entlang der gedachten Mittelachse des Korridors verläuft. Die Linie repräsentiert nicht die Breite des Trassenkorridors.
    Der Linienkorridor wird entweder a) mit einer Postion versehen,  b) ohne eigene Position über die Referenz auf  RVP_LinienkorridorSegmente gebildet oder c) alternativ dazu nur über die Klasse RVP_LinienkorridorSegment dargestellt.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiLine | None,
        Field(
            description="Raumbezug des Korridors",
            json_schema_extra={
                "typename": "GM_MultiCurve",
                "stereotype": "Geometry",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    art: Annotated[
        Literal["1000", "10001", "10002", "10003", "2000", "20001", "20002", "9999"],
        Field(
            description="Variante des Linienkorridors",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Antragskorridor",
                        "alias": "Antragskorridor",
                        "description": "Trassenkorridor als Ergebnis des Verfahrens (auch Antragsvariante). Der Antragskorridor kann sich aus mehreren Segmenten zusammensetzen.",
                    },
                    "10001": {
                        "name": "FestgelegterTrassenkorridor",
                        "alias": "festgelegter Trassenkorridor",
                        "description": "Festgelegter Trassenkorridor",
                    },
                    "10002": {
                        "name": "BevorzugterTrassenkorridor",
                        "alias": "präferierter Trassenkorridor",
                        "description": "Bevorzugter Trassenkorridor (auch präferierter oder Vorschlagstrassenkorridor)",
                    },
                    "10003": {
                        "name": "VorgeschlagenerTrassenkorridor",
                        "alias": "vorgeschlagener Trassenkorridor",
                        "description": "Vorgeschlagener Trassenkorridor / Vorschlags(trassen)korridor / Trassenkorridorvorschlag",
                    },
                    "2000": {
                        "name": "Variantenkorridor",
                        "alias": "Variantenkorridor",
                        "description": "Variante eines Trassenkorridors bei mehreren möglichen Trassenverläufen. Die jeweilige Varianten kann aus mehreren Segmenten bestehen.",
                    },
                    "20001": {
                        "name": "AlternativerTrassenkorridor",
                        "alias": "Alternativer Trassenkorridor",
                        "description": "Ernsthaft zu berücksichtigende bzw. in Frage kommende Alternative (im Vergleich zum Antragskorridor)",
                    },
                    "20002": {
                        "name": "PotenziellerTrassenkorridor",
                        "alias": "potenzieller Trassenkorridor",
                        "description": "Potenzieller Trassenkorridor",
                    },
                    "9999": {
                        "name": "SonstigerKorridor",
                        "alias": "sonstiger Korridor",
                        "description": "sonstiger Korridor",
                    },
                },
                "typename": "RVP_KorridorTyp",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    status: Annotated[
        Literal["1000", "2000", "3000", "4000"],
        Field(
            description="Planungsstatus des Korridors",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "InBearbeitung",
                        "alias": "in Bearbeitung",
                        "description": "Trassenkorridor ist Bestandteil einer laufenden Raumverträglichkeitsprüfung oder einer Rauwiderstandsanalyse",
                    },
                    "2000": {
                        "name": "ErgebnisRVP",
                        "alias": "Ergebnis der Raumverträglichkeitsprüfung",
                        "description": "Trassenkorridor ist das Ergebnis der Räumverträglichkeitsprüfung",
                    },
                    "3000": {
                        "name": "LandesplanerischeFeststellung",
                        "alias": "Landesplanerische Festlegung",
                        "description": "Abschluss der Raumverträglichkeitsprüfung durch landesplanerische Feststellung",
                    },
                    "4000": {
                        "name": "Bestand",
                        "alias": "Bestandskorridor",
                        "description": "Trassenkorrior um Bestandsleitungen",
                    },
                },
                "typename": "RVP_KorridorStatus",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    breite: Annotated[
        definitions.Length | None,
        Field(
            description="Breite des Trassenkorridors in Metern.\r\n(gml:LengthType: uom=“m“ oder uom=“urn:adv:uom:m“)",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    bewertung: Annotated[
        str | None,
        Field(
            description="Gesamtbewertung der Variante",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    bestehtAus: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            description="Verweis auf die Segmente, aus denen sich der Linienkorridor zusammensetzt.",
            json_schema_extra={
                "typename": "RVP_LinienkorridorSegment",
                "stereotype": "Association",
                "multiplicity": "0..*",
            },
        ),
    ] = None


class RVPMultiFlaechenobjekt(RVPObjekt):
    """Basisklasse für RVP-Objekte mit Multi-Flächengeometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiPolygon,
        Field(
            description="Raumbezug des Objektes",
            json_schema_extra={
                "typename": "GM_MultiSurface",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class RVPMultiLinienobjekt(RVPObjekt):
    """Basisklasse für RVP-Objekte mit Multi-Liniengeometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiLine,
        Field(
            description="Raumbezug des Objektes",
            json_schema_extra={
                "typename": "GM_MultiCurve",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class RVPMultiPunktobjekt(RVPObjekt):
    """Basisklasse für RVP-Objekte mit Multi-Punktgeometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiPoint,
        Field(
            description="Raumbezug des Objektes",
            json_schema_extra={
                "typename": "GM_MultiPoint",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class RVPPlan(IPPlan):
    """Klasse zur Modellierung einer Raumverträglichkeitsprüfung"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    version: Annotated[
        RVPVersion,
        Field(
            description="Entwurfsversion/Variante des Plans",
            json_schema_extra={
                "typename": "RVP_Version",
                "stereotype": "DataType",
                "multiplicity": "1",
            },
        ),
    ]
    vorgaengerVersion: Annotated[
        RVPVorgaengerVersion | None,
        Field(
            description="Version des vorherigen Plans",
            json_schema_extra={
                "typename": "RVP_VorgaengerVersion",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    beteiligte: Annotated[
        list[XPAkteur] | None,
        Field(
            description="Zentrale Akteure des Verfahrens",
            json_schema_extra={
                "typename": "XP_Akteur",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    antragDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum der Einreichung der Verfahrensunterlagen durch Vorhabenträger",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    antragskonferenzDatum: Annotated[
        date_aliased | None,
        Field(
            description='Datum der Antragskonferenz ("Scoping")',
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    traegerbeteiligungStartDatum: Annotated[
        date_aliased | None,
        Field(
            description="Startdatum der Beteiligung der Behörden, deren Aufgabenbereich durch das Vorhaben berührt wird",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    traegerbeteiligungEndDatum: Annotated[
        date_aliased | None,
        Field(
            description="Ende der Trägerbeteiligung",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    auslegungGemeinden: Annotated[
        list[XPAuslegung] | None,
        Field(
            description="Gemeinden, in denen Planunterlagen ausgelegt werden oder wurden, da sich das Vorhaben voraussichtlich auswirken wird",
            json_schema_extra={
                "typename": "XP_Auslegung",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    auslegungInternetStartDatum: Annotated[
        date_aliased | None,
        Field(
            description="Startdatum der verwöchigen Veröffentlichung der Planunterlagen im Internet",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    auslegungInternetEndDatum: Annotated[
        date_aliased | None,
        Field(
            description='Enddatum für die "Auslegung" im Intenet',
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    eroerterungstermin: Annotated[
        date_aliased | None,
        Field(
            description="Erörterungstermin der vorgebrachten Anregungen und Bedenken",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    festlegungDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum der (landesplanerischen) Feststellung/Festlegung, raumodnerische Beurteilung,  Entscheid der Bundesfachplanung",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class RVPPotenzialflaecheStandort(RVPMultiFlaechenobjekt):
    """Potenzialfläche für Infrastrukturstandorte innerhalb eines Suchraums"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class RVPRaumwiderstand(RVPMultiFlaechenobjekt):
    """Die Klasse umfasst Bewertungsschemata der Raumwiderstandsanalyse"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal["1000", "2000", "3000", "4000"] | None,
        Field(
            description="Art des Raumwiderstands",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "FaktischerAusschlussbereich",
                        "alias": "faktischer Ausschlussbereich",
                        "description": "Bereiche, die aufgrund bestehender Nutzungen eindeutig nicht für eine Leitungsführung geeignet sind",
                    },
                    "2000": {
                        "name": "PlanungsrechtlicherAusschlussbereich",
                        "alias": "Planungsrechtlicher Ausschlussbereich",
                        "description": "Bereiche, die nicht mit Zielen bzw. Vorranggebieten der Raumordnung vereinbar sind",
                    },
                    "3000": {
                        "name": "Restriktionsbereich",
                        "alias": "Restriktionsbereich",
                        "description": "Bereiche, die projekt- oder raumspezifisch nur bedingt für eine Leitungsführung geeignet sind",
                    },
                    "4000": {
                        "name": "Eignungsbereich",
                        "alias": "Eignungsbereich",
                        "description": "Verbleibender Bereich innerhalb des Suchraums, der keiner der drei übrigen Raumwiderstandstypen zugeordnet ist",
                    },
                },
                "typename": "RVP_RaumwiderstandTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    klasse: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "9999"] | None,
        Field(
            description="Klasse des Raumwiderstands",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "RaumwiderstandsklasseI",
                        "alias": "Raumwiderstandsklasse I",
                        "description": "Definition der Raumwiderstandsklasse erfolgt im Rahmen der jeweiligen Analyse",
                    },
                    "2000": {
                        "name": "RaumwiderstandsklasseII",
                        "alias": "Raumwiderstandsklasse II",
                        "description": "Definition der Raumwiderstandsklasse erfolgt im Rahmen der jeweiligen Analyse",
                    },
                    "3000": {
                        "name": "RaumwiderstandsklasseIII",
                        "alias": "Raumwiderstandsklasse III",
                        "description": "Definition der Raumwiderstandsklasse erfolgt im Rahmen der jeweiligen Analyse",
                    },
                    "4000": {
                        "name": "RaumwiderstandsklasseIV",
                        "alias": "Raumwiderstandsklasse IV",
                        "description": "Definition der Raumwiderstandsklasse erfolgt im Rahmen der jeweiligen Analyse",
                    },
                    "5000": {
                        "name": "RaumwiderstandsklasseV",
                        "alias": "Raumwiderstandsklasse V",
                        "description": "Definition der Raumwiderstandsklasse erfolgt im Rahmen der jeweiligen Analyse",
                    },
                    "9999": {
                        "name": "nichtQualifizierbar",
                        "alias": "nicht qualifizierbar",
                        "description": "nicht qualifizierbare Raumwiderstandsklasse",
                    },
                },
                "typename": "RVP_RaumwiderstandKlasse",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    grossrauemigerSachverhalt: Annotated[
        bool | None,
        Field(
            description="Fläche ist großräumig = true (Hinweis: Filterattribut für Layerstyling)",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    externeReferenz: Annotated[
        XPNetzExterneReferenz | None,
        Field(
            description="Referenz auf ein Dokument der Raumwiderstandsanalyse",
            json_schema_extra={
                "typename": "XP_NetzExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class RVPRiegel(RVPMultiLinienobjekt):
    """Ein Konfliktbereich ist gekennzeichnet durch das Auftreten unterschiedlich ausgeprägter planerischer und technischer Hemmnisse in den entwickelten Trassenkorridoren.
    Der Konfliktbereich kann auch als Engstelle auftreten. Die Abgrenzung zwischen Riegel und Engstelle muss jeweils definiert werden, z.B.:
    Engstelle: verbleibender Trassierungsraum liegt zwischen dem 1- bis 2-fachen der Regelbaubreite.
    Riegel: verbleibender Trassierungsraum ist schmaler als die Regelbaubreite.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal["1000", "2000", "9999"] | None,
        Field(
            description="Art des Hemmnis bzw. Konflikts",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "PlanerischesHemmnis",
                        "alias": "planerisches Hemmnis",
                        "description": "Planerische Hemmnisse beziehen sich auf Planungen und Gebietsausweisungen, von denen hohe Raumwiderstände ausgehen",
                    },
                    "2000": {
                        "name": "TechnischesHemmnis",
                        "alias": "technisches Hemmnis",
                        "description": "Technische Hemmnisse sind Verkehrs- und Leitungsinfrastrukturen, die über- bzw. unterquert werden müssen.  Hinzu kommen sog. sonstige technische Hemmnisse, z. B. durch die Nähe einer Leitung zu Energieinfrastrukturen, die den Einbau von Schutzmaßnahmen erforderlich machen",
                    },
                    "9999": {
                        "name": "SonstigesHemmnis",
                        "alias": "sonstiges Hemmnis",
                        "description": "sonstiges Hemmnis",
                    },
                },
                "typename": "RVP_HemmnisTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    bewertung: Annotated[
        Literal["1000", "2000", "3000", "4000"] | None,
        Field(
            description="Bewertung ob Engstelle/Riegel überwunden bzw. passiert werden kann",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Ueberwindbar",
                        "alias": "überwindbar",
                        "description": "Überwindbar in offener Regelbauweise ohne besondere Vorkehrungen",
                    },
                    "2000": {
                        "name": "BedingtUeberwindbar",
                        "alias": "bedingt überwindbar",
                        "description": "bedingt überwindbar =  überwindbar unter Berücksichtigung von zusätzlichen Vorkehrungen / Maßnahmen, auch bautechnischer Art",
                    },
                    "3000": {
                        "name": "SchwerUeberwindbar",
                        "alias": "schwer überwindbar",
                        "description": "schwer überwindbar = überwindbar unter Berücksichtigung von aufwendigen zusätzlichen Vorkehrungen/Maßnahmen, auch bautechnischer Art",
                    },
                    "4000": {
                        "name": "NichtUeberwindbar",
                        "alias": "nicht überwindbar",
                        "description": "nicht überwindbar = nicht überwindbar aus rechtlichen und/oder bautechnischen Gründen auch unter Abwägung zusätzlicher Vorkehrungen/Maßnahmen",
                    },
                },
                "typename": "RVP_BewertungEngstelleRiegel",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class RVPStandortInfrastruktur(RVPMultiPunktobjekt):
    """Potenzieller Standort  eines Infrastrukturobjektes"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class RVPStationierungslinie(RVPMultiLinienobjekt):
    """Die Stationierungslinie unterteilt einen Trassenkorridor zur Orientierung in Teilabschnitte, deren Abstand in der Regel einen km beträgt (lotrecht zur Trassenkorridorachse)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class RVPSuchraum(RVPMultiFlaechenobjekt):
    """Im ersten Planungsschritt ist der Suchraum ein großräumig abgegrenzter Raum, in dem Linienverbindungen zwischen vorgegegenen Netzverknüpfungspunkten untersucht werden.
    Der Suchraum kann sich im weiteren Planungsverlauf auf einen Teilbereich beziehen, für den noch keine Festlegung von Trassenkorridoren oder Infrastrukturen erfolgen kann.
    Der Begriff Suchraum entspricht dem Untersuchungsraum.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"],
        Field(
            description="Art des Suchraums",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Grobkorridor",
                        "alias": "Grobkorridor",
                        "description": "Grobkorridore zwischen Netzverknüpfungspunkten",
                    },
                    "2000": {
                        "name": "Trassenkorridor",
                        "alias": "Trassenkorridor",
                        "description": "Trassenkorridore zwischen Netzverknüpfungspunkten",
                    },
                    "3000": {
                        "name": "Trassenfindung",
                        "alias": "Trassenfindung",
                        "description": "Trassenverlauf innerhalb eines Teilraums",
                    },
                    "4000": {
                        "name": "Infrastruktur",
                        "alias": "Infrastruktur",
                        "description": "Suchraum für zur Trasse gehörende Infrastruktur",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiges",
                        "description": "sonstiges",
                    },
                },
                "typename": "RVP_SuchraumTyp",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]


class RVPTrassenkorridorAchse(RVPMultiLinienobjekt):
    """Innerhalb eines Trassenkorridors verlaufende Trassenachse. Diese kann analog zu den Trassenkorridorsegmenten aus Abschnitten bestehen oder den Gesamtverlauf abbilden."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000"] | None,
        Field(
            description="Art der Trassenachse",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Mittelachse",
                        "alias": "Mittelachse",
                        "description": "Schematische Darstellung des Verlaufs der Trasse innerhalb eines Trassenkorridors",
                    },
                    "2000": {
                        "name": "Antragstrasse",
                        "alias": "Antragstrasse",
                        "description": "Potenzielle Trassenachse, die als Vorzugsvariante in den weiteren Planungsstufen fungiert",
                    },
                    "3000": {
                        "name": "PotenzielleTrassenachse",
                        "alias": "Potenzielle Trassenachse",
                        "description": "Potenzieller Trassenverlauf zur Prüfung der Durchgängigkeit des Trassenkorridors an Eng- und Konfliktstellen",
                    },
                    "4000": {
                        "name": "Trassenalternative",
                        "alias": "Trassenalternative",
                        "description": "Alternative potenzielle Trassenachse (bei einem kleinräumigen Vergleich von Trassenverläufen)",
                    },
                    "5000": {
                        "name": "VerworfeneTrassenalternative",
                        "alias": "verworfene Trassenalternative",
                        "description": "Trassenalternative, die geprüft und verworfen wurde",
                    },
                },
                "typename": "RVP_TrassenachseTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    bewertung: Annotated[
        str | None,
        Field(
            description="Bewertung im Rahmen eines Vergleichs von Trassenverläufen",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class RVPTrassenkorridorSegment(RVPMultiFlaechenobjekt):
    """Zu Planungsbeginn können Trassenkorridorsegmente und ihre Alternativen einen netzartigen Verlauf darstellen (Korridornetz).  Korridorsegmente werden zu Strängen oder Varianten zusammengesetzt. Dies kann über das Attribut "art" erfolgen. Wenn einzelne Segmente Bestandteil in verschiedenen Varianten sind, kann zusätzlich das Attritbut "korridorVariante" genutzt werden.
    Vollständige Korridore können alternativ dazu über die Klasse RVP_Trassenkorridor abgebildet werden.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    artKorridor: Annotated[
        Literal["1000", "10001", "10002", "10003", "2000", "20001", "20002", "9999"]
        | None,
        Field(
            description='Art des Korridors, dem das Segments zugewiesen wird. Bei Mehrfachbelegung in verschiedenen Varianten kann das Attribut "korridorVariante" genutzt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Antragskorridor",
                        "alias": "Antragskorridor",
                        "description": "Trassenkorridor als Ergebnis des Verfahrens (auch Antragsvariante). Der Antragskorridor kann sich aus mehreren Segmenten zusammensetzen.",
                    },
                    "10001": {
                        "name": "FestgelegterTrassenkorridor",
                        "alias": "festgelegter Trassenkorridor",
                        "description": "Festgelegter Trassenkorridor",
                    },
                    "10002": {
                        "name": "BevorzugterTrassenkorridor",
                        "alias": "präferierter Trassenkorridor",
                        "description": "Bevorzugter Trassenkorridor (auch präferierter oder Vorschlagstrassenkorridor)",
                    },
                    "10003": {
                        "name": "VorgeschlagenerTrassenkorridor",
                        "alias": "vorgeschlagener Trassenkorridor",
                        "description": "Vorgeschlagener Trassenkorridor / Vorschlags(trassen)korridor / Trassenkorridorvorschlag",
                    },
                    "2000": {
                        "name": "Variantenkorridor",
                        "alias": "Variantenkorridor",
                        "description": "Variante eines Trassenkorridors bei mehreren möglichen Trassenverläufen. Die jeweilige Varianten kann aus mehreren Segmenten bestehen.",
                    },
                    "20001": {
                        "name": "AlternativerTrassenkorridor",
                        "alias": "Alternativer Trassenkorridor",
                        "description": "Ernsthaft zu berücksichtigende bzw. in Frage kommende Alternative (im Vergleich zum Antragskorridor)",
                    },
                    "20002": {
                        "name": "PotenziellerTrassenkorridor",
                        "alias": "potenzieller Trassenkorridor",
                        "description": "Potenzieller Trassenkorridor",
                    },
                    "9999": {
                        "name": "SonstigerKorridor",
                        "alias": "sonstiger Korridor",
                        "description": "sonstiger Korridor",
                    },
                },
                "typename": "RVP_KorridorTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    artSegment: Annotated[
        Literal["1000", "2000", "3000", "9999"] | None,
        Field(
            description="Art des Korridorsegments",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "AlternativesKorridorsegment",
                        "alias": "alternatives Korridorsegment",
                        "description": "Alternatives Trassenkorridorsegment (auch Korridoralternative) bei Analyse und Darstellung eines Korridornetzes",
                    },
                    "2000": {
                        "name": "VerworfenesKorridorsegment",
                        "alias": "verworfenes Korridorsegment",
                        "description": "Korridorsegment, das im Rahmen einer (Raumwiderstands-)Analyse ausgeschlossen oder nicht weiter betrachtet wird",
                    },
                    "3000": {
                        "name": "RueckbauBestandsleitung",
                        "alias": "Rückbau Bestandsleitung",
                        "description": "Korridorsegment, in dem der Rückbau einer Bestandsleitung erfolgt",
                    },
                    "9999": {
                        "name": "SonstigesKorridorsegment",
                        "alias": "sonstiges Korridorsegment",
                        "description": "sonstiges Korridorsegment",
                    },
                },
                "typename": "RVP_KorridorSegmentTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    status: Annotated[
        Literal["1000", "2000", "3000", "4000"] | None,
        Field(
            description="Planungsstatus des Korridorsegments",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "InBearbeitung",
                        "alias": "in Bearbeitung",
                        "description": "Trassenkorridor ist Bestandteil einer laufenden Raumverträglichkeitsprüfung oder einer Rauwiderstandsanalyse",
                    },
                    "2000": {
                        "name": "ErgebnisRVP",
                        "alias": "Ergebnis der Raumverträglichkeitsprüfung",
                        "description": "Trassenkorridor ist das Ergebnis der Räumverträglichkeitsprüfung",
                    },
                    "3000": {
                        "name": "LandesplanerischeFeststellung",
                        "alias": "Landesplanerische Festlegung",
                        "description": "Abschluss der Raumverträglichkeitsprüfung durch landesplanerische Feststellung",
                    },
                    "4000": {
                        "name": "Bestand",
                        "alias": "Bestandskorridor",
                        "description": "Trassenkorrior um Bestandsleitungen",
                    },
                },
                "typename": "RVP_KorridorStatus",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    breite: Annotated[
        definitions.Length | None,
        Field(
            description="Breite des Trassenkorridors in Metern.\r\n(gml:LengthType: uom=“m“ oder uom=“urn:adv:uom:m“)",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    bewertung: Annotated[
        str | None,
        Field(
            description="Gesamtbewertung im Rahmen eines Vergleichs von Trassenverläufen",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    korridorVariante: Annotated[
        list[str] | None,
        Field(
            description="Wenn Korridorsegmente Bestandteil verschiedener Varianten sind, werden diese hier benannt.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..*",
            },
        ),
    ] = None


class BRABaugrube(BRAMultiPunktobjekt):
    """Baugrube für die geschlossene Bauweise"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal["1000", "2000"] | None,
        Field(
            description="Art der Baugrube (Start oder Ziel)",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Startgrube",
                        "alias": "Startgrube",
                        "description": "Startgrube",
                    },
                    "2000": {
                        "name": "Zielgrube",
                        "alias": "Zielgrube",
                        "description": "Zielgrube",
                    },
                },
                "typename": "XP_BaugrubeTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    startDatum: Annotated[
        date_aliased | None,
        Field(
            description="Geplante Errichtung der Baugrube",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    endDatum: Annotated[
        date_aliased | None,
        Field(
            description="Geplanter Abbau der Baugrube",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BRABaustelle(BRAMultiFlaechenobjekt):
    """Einzurichtende Baustellenfläche im Straßenraum"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal["1000", "2000", "3000"],
        Field(
            description="Auswahl der darzustellenden Baustellenfläche",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Baustelleneinrichtung",
                        "alias": "Fläche für Baustelleneinrichtung",
                        "description": "Produktions-, Transport-, Lager- und sonstige Einrichtungen, die zur Errichtung eines Bauwerks auf der Baustelle benötigt werden.",
                    },
                    "2000": {
                        "name": "Graben_Grube",
                        "alias": "Graben oder Grube",
                        "description": "Zur Verlegung von Leitungen auszuhebende Gräben und Gruben",
                    },
                    "3000": {
                        "name": "Bauabschnitt",
                        "alias": "Ausdehnung des Bauabschnitts",
                        "description": "Räumliche Ausdehnung eines oder mehrerer Bauabschnitte einer Breitbandtrasse",
                    },
                },
                "typename": "BRA_BaustelleTyp",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    startDatum: Annotated[
        date_aliased | None,
        Field(
            description="Geplanter Beginn der Baustelle",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    endDatum: Annotated[
        date_aliased | None,
        Field(
            description="Geplantes Ende der Baustelle",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BRABreitbandtrasseAbschnitt(BRALinienobjekt):
    """Die Klasse modelliert Attribute zum Bau und zur Lage der Leitungstrasse. Die Trasse verläuft in Abschnitten, die jeweils durch die unterschiedliche Belegung der Attribute gekennzeichnet sind."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    bauweise: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Angabe der Bauweise",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "OffeneBauweise",
                        "alias": "offene Bauweise",
                        "description": "offene Bauweise",
                    },
                    "2000": {
                        "name": "GeschlosseneBauweise",
                        "alias": "geschlossene Bauweise",
                        "description": "geschlossene Bauweise",
                    },
                    "3000": {
                        "name": "Oberirdisch",
                        "alias": "oberirdische Verlegung",
                        "description": "oberirdische Verlegung",
                    },
                },
                "typename": "XP_Bauweise",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    legeverfahren: Annotated[
        Literal[
            "1000",
            "2000",
            "3000",
            "4000",
            "5000",
            "6000",
            "60001",
            "60002",
            "7000",
            "8000",
            "9000",
            "9999",
        ]
        | None,
        Field(
            description="Auswahl der konventionellen oder alternativen Legeverfahren/Verlegemethoden",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Konventionell_offenerGraben",
                        "alias": "Konventionelle Verlegung im offenen Graben",
                        "description": "Ausschachtung mit Schaufel, Bagger, Fräse",
                    },
                    "2000": {
                        "name": "Pressbohrverfahren",
                        "alias": "Pressbohrverfahren",
                        "description": 'Unterirdische Verlegetechnik, die in verschiedenen Varianten zur Anwendung kommt (statisch, dynamisch, ungesteuert, gesteuert) und von Herstellern spezifisch bezeichnet wird ("Modifiziertes Direct-Pipe-Verfahren").  Im Breitbandausbau auch als Erdraketentechnik bekannt. Im Rohrleitungsbau können durch hydraulische oder pneumatische Presseinrichtungen Produktenrohrkreuzungen DN 1000 bis zu 100 m grabenlos verlegt werden.',
                    },
                    "3000": {
                        "name": "HorizontalSpuelbohrverfahren",
                        "alias": "Horizontal-Spülbohrverfahren",
                        "description": "Richtbohrtechnik für Horizontalbohrungen („Horizontal Directional Drilling“, HDD), die eine grabenlose Verlegung von Produkt- oder Leerrohren ermöglicht.  Die Bohrung ist anfangs meist schräg nach unten in das Erdreich gerichtet und verläuft dann in leichtem Bogen zum Ziel, wo sie schräg nach oben wieder zutage tritt.",
                    },
                    "4000": {
                        "name": "Pflugverfahren",
                        "alias": "Pflugverfahren",
                        "description": "Erstellung eines Leitungsgrabens (Breite > 30cm) oder Schlitzes mit einem Pflugschwert durch Verdrängung der Schicht(en) und gleichzeitigem Einbringen der Glasfasermedien. Der Einsatz des Pflugverfahrens ist ausschließlich in unbefestigten Oberflächen zulässig.",
                    },
                    "5000": {
                        "name": "Fraesverfahren_ungebundeOberfl",
                        "alias": "Fräsverfahren in ungebundenen Oberflächen",
                        "description": "Fräsverfahren in ungebunden Oberflächen (Schlitzbreite: 15 bis 30 cm, Schlitztiefe: 40 bis 120 cm)",
                    },
                    "6000": {
                        "name": "Trenching",
                        "alias": "Trenching",
                        "description": "Erstellung eines Schlitzes (< 30 cm) in gebundenen Verkehrsflächen in verschiedenen Verfahren durch rotierende, senkrecht stehende Werkzeuge, wobei die Schicht(en) gelöst, zerkleinert und gefördert wird (werden)",
                    },
                    "60001": {
                        "name": "Schleif_Saegeverfahren",
                        "alias": "Schleif-/Sägeverfahren",
                        "description": "Erstellung eines Schlitzes eine durch eine Schneideeinheit (Schlitzbreite: 1,5 bis 11 cm, Schlitztiefe: 7 bis 45 cm)",
                    },
                    "60002": {
                        "name": "Fraesverfahren",
                        "alias": "Fräsverfahren",
                        "description": "Erstellung eines Schlitzes durch ein Fräswerkzeug (Kette, Rad), (Schlitzbreite: 5 bis 15 cm, Schlitztiefe: 30 bis 60 cm)",
                    },
                    "7000": {
                        "name": "Rammverfahren",
                        "alias": "Rammverfahren",
                        "description": "Vortriebsverfahren, welches durch hydraulisches oder pneumatisches Vibrationsrammen das Rohr unter dem Hindernis hindurch schlägt. Mit dem Rammverfahren können Produkten- oder Mantelrohrkreuzungen bis zu 100 m Vortriebslänge grabenlos verlegt werden.",
                    },
                    "8000": {
                        "name": "Microtunneling",
                        "alias": "Microtunneling",
                        "description": "Für den grabenlosen Vortrieb werden in dem steuerbaren Verfahren zunächst Stahlbetonrohre mit großem Nenndurchmesser verlegt,  in denen nach Durchführung der Unterquerung das eigentliche Produktenrohr eingebracht/eingezogen wird. Es kommt nur bei schwierigen Kreuzungen zur Anwendung.",
                    },
                    "9000": {
                        "name": "oberirdischeVerlegung",
                        "alias": "oberirdische Verlegung",
                        "description": "oberirdische Verlegung mittels Holzmasten",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiges Verfahren",
                        "description": "Sonstiges Verfahren",
                    },
                },
                "typename": "XP_Legeverfahren",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    verfuellmethode: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Auswahl Verfüllmethode beim Trenching-Verfahren",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Konventionell",
                        "alias": "konventionell",
                        "description": "konventionelle Verfüllung, z.B. mit Aushub",
                    },
                    "2000": {
                        "name": "Fluessigboden",
                        "alias": "Flüssigboden",
                        "description": "z.B. Flüssigasphalt",
                    },
                    "3000": {
                        "name": "SonstigeVerfuellung",
                        "alias": "sonstige Verfüllung",
                        "description": "Sonstiges",
                    },
                },
                "typename": "BRA_Verfuellmethode",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    grabenbreite: Annotated[
        definitions.Length | None,
        Field(
            description="Breite des Leitungsgrabens in m.\r\n(gml:LengthType: uom=“m“ oder uom=“urn:adv:uom:m“)",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    grabentiefe: Annotated[
        definitions.Length | None,
        Field(
            description='Tiefe des Leitungsgrabens in m.\r\nEntspricht der "Verlegetiefe". \r\n(gml:LengthType: uom=“m“ oder uom=“urn:adv:uom:m“)',
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    strassenart: Annotated[
        Literal[
            "1000",
            "1100",
            "2000",
            "2100",
            "3000",
            "4000",
            "5000",
            "5100",
            "5200",
            "9999",
        ]
        | None,
        Field(
            description="Kategorie der Straße, die von der Verlegung betroffen ist.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Bundesautobahn",
                        "alias": "Bundesautobahn",
                        "description": "Bundesautobahn",
                    },
                    "1100": {
                        "name": "Bundesstrasse",
                        "alias": "Bundesstraße",
                        "description": "Bundesstraße",
                    },
                    "2000": {
                        "name": "Landesstrasse",
                        "alias": "Landesstraße",
                        "description": "Landesstraße",
                    },
                    "2100": {
                        "name": "Staatsstrasse",
                        "alias": "Staatsstraße",
                        "description": "Staatsstraße (Landesstraße in Bayern)",
                    },
                    "3000": {
                        "name": "Hauptverkehrsstrasse",
                        "alias": "Hauptverkehrsstraße",
                        "description": "Hauptverkehrsstraße (in Hamburg)",
                    },
                    "4000": {
                        "name": "Kreisstrasse",
                        "alias": "Kreisstraße",
                        "description": "Kreisstraße",
                    },
                    "5000": {
                        "name": "Gemeindestrasse",
                        "alias": "Gemeindestraße",
                        "description": "Gemeindestraße",
                    },
                    "5100": {
                        "name": "BSGB",
                        "alias": "Bezirksstraße mit Gesamtstädtischer Bedeutung",
                        "description": "Bezirksstraße mit Gesamtstädtischer Bedeutung (BSGB)",
                    },
                    "5200": {
                        "name": "Bezirksstrasse",
                        "alias": "Bezirksstraße",
                        "description": "Bezirksstraße",
                    },
                    "9999": {
                        "name": "SonstigeStrasse",
                        "alias": "sonstige Straße",
                        "description": "sonstige Straße",
                    },
                },
                "typename": "BRA_StrasseTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    baugrund: Annotated[
        Literal[
            "1000",
            "2100",
            "21001",
            "21002",
            "21003",
            "21004",
            "2200",
            "22001",
            "22002",
            "22003",
            "22004",
            "22005",
            "2300",
            "3000",
            "30001",
            "30002",
            "30003",
            "4000",
            "40001",
            "40002",
            "5000",
            "6000",
            "7000",
            "9999",
        ]
        | None,
        Field(
            description="Art der Wegefläche, in der die Verlegung erfolgt.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Fahrbahn",
                        "alias": "Fahrbahn",
                        "description": "Fahrbahn",
                    },
                    "2100": {
                        "name": "Bankett_Sicherheitstrennstreifen",
                        "alias": "Bankett / Sicherheitstrennstreifen",
                        "description": "Bankett / Sicherheitstrennstreifen",
                    },
                    "21001": {
                        "name": "Bankett_Fraesbereich",
                        "alias": "Bankett  - zulässiger Fräsbereich",
                        "description": "Bankett - zulässiger Fräsbereich nach DIN 18220",
                    },
                    "21002": {
                        "name": "Bankett",
                        "alias": "Bankett - außerhalb Fräsbereich",
                        "description": "Bankett  - außerhalb zulässigem Fräsbereich nach DIN 18220",
                    },
                    "21003": {
                        "name": "Sicherheitstrennstreifen_Fraesbereich",
                        "alias": "Sicherheitstrennstreifen  - zulässiger Fräsbereich",
                        "description": "Sicherheitstrennstreifen - zulässiger Fräsbereich nach DIN 18220",
                    },
                    "21004": {
                        "name": "Sicherheitstrennstreifen",
                        "alias": "Sicherheitstrennstreifen - außerhalb Fräsbereich",
                        "description": "Sicherheitstrennstreifen - außerhalb zulässigem Fräsbereich nach DIN 18220",
                    },
                    "2200": {
                        "name": "Entwaesserungsgraben_Boeschung",
                        "alias": "Entwässerungsgraben / Böschung",
                        "description": "Entwässerungsgraben / Böschung",
                    },
                    "22001": {
                        "name": "Entwaesserungsgraben",
                        "alias": "Entwässerungsgraben",
                        "description": "Entwässerungsgraben / Mulde (ohne Entwässerungsleitung)",
                    },
                    "22002": {
                        "name": "Mulde",
                        "alias": "Mulde (mit Entwässerungsleitung)",
                        "description": "Mulde (mit Entwässerungsleitung)",
                    },
                    "22003": {
                        "name": "StrassenseitigeGrabenboeschung",
                        "alias": "straßenseitige Grabenböschung",
                        "description": "straßenseitige Grabenböschung",
                    },
                    "22004": {
                        "name": "FeldseitigeBoeschung",
                        "alias": "feldseitige Böschung",
                        "description": "feldseitige Böschung",
                    },
                    "22005": {
                        "name": "Gelaende",
                        "alias": "Gelände",
                        "description": "Gelände",
                    },
                    "2300": {
                        "name": "Gehweg_Radweg_strassenbegleitend",
                        "alias": "straßenbegleitender Gehweg / Radweg",
                        "description": "straßenbegleitender Gehweg / Radweg (außerorts, gebundene Deckschicht)",
                    },
                    "3000": {
                        "name": "Weg_nichtStrassenbegleitend",
                        "alias": "nicht straßenbegleitender Weg",
                        "description": "nicht straßenbegleitender Weg (außerorts, Deckschicht ohne Bindemittel)",
                    },
                    "30001": {
                        "name": "Gehweg_Radweg",
                        "alias": "Gehweg / Radweg",
                        "description": "Gehweg / Radweg",
                    },
                    "30002": {
                        "name": "Feldweg_Waldweg",
                        "alias": "Feldweg / Waldweg",
                        "description": "öffentlicher Feldweg / Waldweg",
                    },
                    "30003": {
                        "name": "Wirtschaftsweg",
                        "alias": "Wirtschaftsweg",
                        "description": "Wirtschaftsweg (nicht straßenbegleitend, Deckschicht ohne Bindemittel)",
                    },
                    "4000": {
                        "name": "Gehweg_Radweg_innerorts",
                        "alias": "Gehweg / Radweg (innerorts)",
                        "description": "Gehweg / Radweg (innerorts)",
                    },
                    "40001": {
                        "name": "Gehweg",
                        "alias": "Gehweg",
                        "description": "Gehweg",
                    },
                    "40002": {
                        "name": "Radweg",
                        "alias": "Radweg",
                        "description": "Radweg",
                    },
                    "5000": {
                        "name": "Gruenstreifen",
                        "alias": "Grünstreifen / Straßenbegleitgrün (innerorts)",
                        "description": "Grünstreifen / Straßenbegleitgrün (innerorts)",
                    },
                    "6000": {
                        "name": "Parkplatz_Parkstreifen",
                        "alias": "Parkplatz / Parkstreifen",
                        "description": "Parkplatz / Parkstreifen",
                    },
                    "7000": {
                        "name": "Strassengrundstueck",
                        "alias": "Straßengrundstück",
                        "description": "Straßengrundstück",
                    },
                    "9999": {
                        "name": "SonstigeWegeflaechen",
                        "alias": "sonstige Wegeflächen",
                        "description": "sonstige Wegeflächen",
                    },
                },
                "typename": "BRA_BaugrundTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    istOrtsdurchfahrt: Annotated[
        bool | None,
        Field(
            description="Trasse betrifft eine Ortsdurchfahrt = true",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    istUeberfuehrungsbauwerk: Annotated[
        bool | None,
        Field(
            description="Trasse verläuft entlang einer Brücke = true",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    istGruenflaeche: Annotated[
        bool | None,
        Field(
            description="Trasse verläuft (teilweise) in einer Grünfläche = true",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    kreuztStrasse: Annotated[
        bool | None,
        Field(
            description="Trasse kreuzt im Verlauf dieses Abschnitts eine Straße =  true",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BRAHausanschluss(BRAMultiPunktobjekt):
    """Hausanschluss im Breitband-Netz"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    technik: Annotated[
        Literal[
            "1000",
            "2000",
            "3000",
            "4000",
            "5000",
            "6000",
            "7000",
            "8000",
            "9000",
            "9999",
        ]
        | None,
        Field(
            description="Auswahl der aktiven oder passiven Netztechnik",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Hauptverteiler_HVt",
                        "alias": "Hauptverteiler ( HVt) - konventionell",
                        "description": "Hauptverteiler (HVt) - konventionell",
                    },
                    "2000": {
                        "name": "GlasfaserHVt_PoP",
                        "alias": "Glasfaser-HVt/ PoP",
                        "description": "Glasfaser-HVt/ PoP",
                    },
                    "3000": {
                        "name": "DSLAM_MSAN",
                        "alias": "DSLAM/ MSAN",
                        "description": "DSLAM/MSAN",
                    },
                    "4000": {
                        "name": "GlasfaserVerteiler",
                        "alias": "Glasfaser-Verteiler",
                        "description": "Glasfaser-Verteiler",
                    },
                    "5000": {
                        "name": "Kabelmuffe",
                        "alias": "Kabelmuffe",
                        "description": "Kabelmuffe",
                    },
                    "6000": {
                        "name": "Hausuebergabepunkt_APL",
                        "alias": "Hausübergabepunkt/ APL",
                        "description": "Hausübergabepunkt/ APL",
                    },
                    "7000": {
                        "name": "UebergabepunktBackbone",
                        "alias": "Übergabepunkt Backbone",
                        "description": "Übergabepunkt Backbone",
                    },
                    "8000": {
                        "name": "OpticalLineTermination_OLT",
                        "alias": "Optical Line Termination (OLT)",
                        "description": "Optical Line Termination (OLT)",
                    },
                    "9000": {
                        "name": "OptischerSplitter",
                        "alias": "Optischer  Splitter",
                        "description": "Optischer Splitter",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "Sonstiges",
                        "description": "Sonstiges",
                    },
                },
                "typename": "BRA_Netztechnik",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BRAKabel(BRALinienobjekt):
    """TK-Kabel können mit und ohne Schutzrohr/Mikrorohr verlegt werden. Sofern sie nicht einem Rohr zugeordnet sind, wird in einem BRA_Ausbauplan der räumliche Verlauf der Kabel durch den Verlauf der BRA_BreitbandtrasseAbschnitte vorgegeben."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal["1000", "2000", "3000", "4000"] | None,
        Field(
            description="Art des Kabels",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Glasfaserkabel",
                        "alias": "Glasfaserkabel",
                        "description": "Glasfaserkabel",
                    },
                    "2000": {
                        "name": "Kupferkabel",
                        "alias": "Kupferkabel",
                        "description": "Kupferkabel",
                    },
                    "3000": {
                        "name": "Hybridkabel",
                        "alias": "Hybridkabel",
                        "description": "Hybridkabel",
                    },
                    "4000": {
                        "name": "Koaxialkabel",
                        "alias": "Koaxial-(TV)-Kabel",
                        "description": "Koaxial-(TV)-Kabel",
                    },
                },
                "typename": "XP_KabelTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    mikrorohrverbund: Annotated[
        AnyUrl | UUID | None,
        Field(
            description="Referenz auf den Mikrorohrverbund, in dem das Kabel liegt bzw. verlegt wird",
            json_schema_extra={
                "typename": "BRA_Mikrorohrverbund",
                "stereotype": "Association",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    mikrorohr: Annotated[
        AnyUrl | UUID | None,
        Field(
            description="Referenz auf das Mikrorohr, in dem das Kabel liegt bzw. verlegt wird",
            json_schema_extra={
                "typename": "BRA_Mikrorohr",
                "stereotype": "Association",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    schutzrohr: Annotated[
        AnyUrl | UUID | None,
        Field(
            description="Referenz auf das Schutzrohr, in dem das Kabel liegt bzw. verlegt wird (sofern kein weiteres Rohr genutzt wird)",
            json_schema_extra={
                "typename": "BRA_Schutzrohr",
                "stereotype": "Association",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BRAKompaktstation(BRAMultiPunktobjekt):
    """Knotenpunkt des Breitband-Netzes in Form einer Kompaktstation"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    technik: Annotated[
        Literal[
            "1000",
            "2000",
            "3000",
            "4000",
            "5000",
            "6000",
            "7000",
            "8000",
            "9000",
            "9999",
        ]
        | None,
        Field(
            description="Auswahl der aktiven oder passiven Netztechnik",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Hauptverteiler_HVt",
                        "alias": "Hauptverteiler ( HVt) - konventionell",
                        "description": "Hauptverteiler (HVt) - konventionell",
                    },
                    "2000": {
                        "name": "GlasfaserHVt_PoP",
                        "alias": "Glasfaser-HVt/ PoP",
                        "description": "Glasfaser-HVt/ PoP",
                    },
                    "3000": {
                        "name": "DSLAM_MSAN",
                        "alias": "DSLAM/ MSAN",
                        "description": "DSLAM/MSAN",
                    },
                    "4000": {
                        "name": "GlasfaserVerteiler",
                        "alias": "Glasfaser-Verteiler",
                        "description": "Glasfaser-Verteiler",
                    },
                    "5000": {
                        "name": "Kabelmuffe",
                        "alias": "Kabelmuffe",
                        "description": "Kabelmuffe",
                    },
                    "6000": {
                        "name": "Hausuebergabepunkt_APL",
                        "alias": "Hausübergabepunkt/ APL",
                        "description": "Hausübergabepunkt/ APL",
                    },
                    "7000": {
                        "name": "UebergabepunktBackbone",
                        "alias": "Übergabepunkt Backbone",
                        "description": "Übergabepunkt Backbone",
                    },
                    "8000": {
                        "name": "OpticalLineTermination_OLT",
                        "alias": "Optical Line Termination (OLT)",
                        "description": "Optical Line Termination (OLT)",
                    },
                    "9000": {
                        "name": "OptischerSplitter",
                        "alias": "Optischer  Splitter",
                        "description": "Optischer Splitter",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "Sonstiges",
                        "description": "Sonstiges",
                    },
                },
                "typename": "BRA_Netztechnik",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    werkstoff: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "2000",
            "20001",
            "20002",
            "20003",
            "2500",
            "25001",
            "25002",
            "25003",
            "25004",
            "25005",
            "3000",
            "30001",
            "30002",
            "4000",
            "5000",
            "9999",
        ]
        | None,
        Field(
            description="Werkstoff der Kompaktstation",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Kunststoff",
                        "alias": "Kunststoff",
                        "description": "Kunststoff",
                    },
                    "10001": {
                        "name": "Polyethylen_PE",
                        "alias": "Polyethylen ( PE)",
                        "description": "Polyethylen (PE)",
                    },
                    "10002": {
                        "name": "Polyethylen_PE_HD",
                        "alias": "High-Density Polyethylen",
                        "description": "High-Density Polyethylen",
                    },
                    "10003": {
                        "name": "Polypropylen_PP",
                        "alias": "Polypropylen ( PP)",
                        "description": "Polypropylen (PP)",
                    },
                    "10004": {
                        "name": "Polycarbonat_PC",
                        "alias": "Polycarbonat ( PC)",
                        "description": "Polycarbonat (PC)",
                    },
                    "10005": {
                        "name": "Polyvinylchlorid_PVC_U",
                        "alias": "Polyvinylchlorid ( PVC- U)",
                        "description": "Polyvinylchlorid (PVC-U)",
                    },
                    "2000": {"name": "Stahl", "alias": "Stahl", "description": "Stahl"},
                    "20001": {
                        "name": "StahlVerzinkt",
                        "alias": "Stahl verzinkt",
                        "description": "Stahl verzinkt",
                    },
                    "20002": {
                        "name": "Stahlgitter",
                        "alias": "Stahlgitter",
                        "description": "Stahlfachwerkskonstruktion (z.B. Freileitungsmast als Gittermast)",
                    },
                    "20003": {
                        "name": "Stahlrohr",
                        "alias": "Stahlrohr",
                        "description": "Rohrförmiger Profilstahl, dessen Wand aus Stahl besteht. Stahlrohre dienen der Durchleitung von flüssigen, gasförmigen oder festen Stoffen, oder werden als statische oder konstruktive Elemente verwendet (z.B. Freileitungsmast als Stahlrohrmast)",
                    },
                    "2500": {
                        "name": "Stahlverbundrohr",
                        "alias": "Stahlverbundrohr",
                        "description": "Stahlverbundrohre im Rohrleitungsbau",
                    },
                    "25001": {
                        "name": "St_PE",
                        "alias": "Stahlrohr mit Standard-Kunststoffumhüllung (PE)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PE-Basis",
                    },
                    "25002": {
                        "name": "St_PP",
                        "alias": "Stahlrohr mit Kunstoffumhüllung (PP)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PP-Basis für höhere Temperatur- und Härte-Anforderungen",
                    },
                    "25003": {
                        "name": "St_FZM",
                        "alias": "Stahlrohr mit FZM-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz durch Faserzementmörtel-Ummantelung (FZM)",
                    },
                    "25004": {
                        "name": "St_GFK",
                        "alias": "Stahlrohr mit GFK-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz aus glasfaserverstärktem Kunststoff (GFK) für höchste mechanische Abriebfestigkeit bei grabenlosem Rohrvortrieb",
                    },
                    "25005": {
                        "name": "St_ZM_PE",
                        "alias": "Stahl-Verbundrohr (ZM-PE)",
                        "description": "Stahlrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserohr)",
                    },
                    "3000": {
                        "name": "Gusseisen",
                        "alias": "Gusseisen",
                        "description": "Gusseisen",
                    },
                    "30001": {
                        "name": "GGG_ZM",
                        "alias": "duktiles Gussrohr mit ZM-Auskleidung",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung (z.B Abwasserrohr)",
                    },
                    "30002": {
                        "name": "GGG_ZM_PE",
                        "alias": "duktiles Guss-Verbundrohr (ZM-PE)",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserrohr)",
                    },
                    "4000": {
                        "name": "Beton",
                        "alias": "Beton",
                        "description": "Beton (z.B. Schacht)",
                    },
                    "5000": {
                        "name": "Holz",
                        "alias": "Holz",
                        "description": "Holz (z.B. Holzmast)",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiger Werkstoff",
                        "description": "Sonstiger Werkstoff",
                    },
                },
                "typename": "XP_Werkstoff",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BRAMast(BRAMultiPunktobjekt):
    """Neu erstellter (Holz-)Mast für oberirdische Leitungen (Nutzung von Bestandsmasten erfolgt über:  BST_Mast)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class BSTAbwasserleitung(BSTMultiLinienobjekt):
    """Kanal oder Rohr zur Abwasserbeseitigung"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Auswahl des Kanaltyps bezogen auf die Art der Entwässerung",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Schmutzwasser",
                        "alias": "Schmutzwasser",
                        "description": "Schmutzwasser",
                    },
                    "2000": {
                        "name": "Regenwasser",
                        "alias": "Regenwasser",
                        "description": "Regenwasser",
                    },
                    "3000": {
                        "name": "Mischwasser",
                        "alias": "Mischwasser",
                        "description": "Mischwasser",
                    },
                },
                "typename": "BST_KanalTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    netzEbene: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "6000", "7000", "8000", "9999"]
        | None,
        Field(
            description="Leitungsart innerhalb des Abwassernetzes",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Fernleitung",
                        "alias": "Fernleitung",
                        "description": "Fernleitung gemäß Umweltverträglichkeitsprüfung (UVPG), Anlage 1 und ENWG § 3, Nr. 19d/20; Leitungen der Fernleitungsnetzbetreiber",
                    },
                    "2000": {
                        "name": "Verteilnetzleitung",
                        "alias": "Verteilnetzleitung",
                        "description": "Leitung eines Verteil(er)netzes; Leitungen der Versorgungsunternehmen",
                    },
                    "3000": {
                        "name": "Hauptleitung",
                        "alias": "Hauptleitung",
                        "description": "Hauptleitung, oberste Leitungskategorie in einem Trinkwasser und Wärmenetz",
                    },
                    "4000": {
                        "name": "Versorgungsleitung",
                        "alias": "Versorgungsleitung",
                        "description": "Versorgungsleitung, auch Ortsleitung (z.B Wasserleitungen innerhalb des Versorgungsgebietes im bebauten Bereich)",
                    },
                    "5000": {
                        "name": "Zubringerleitung",
                        "alias": "Zubringerleitung",
                        "description": "Zubringerleitung (z.B. Wasserleitungen zwischen Wassergewinnungs- und Versorgungsgebieten)",
                    },
                    "6000": {
                        "name": "Anschlussleitung",
                        "alias": "Hausanschlussleitung",
                        "description": "Anschlussleitung, Hausanschluss (z.B. Wasserleitungen von der Abzweigstelle der Versorgungsleitung bis zur Übergabestelle/Hauptabsperreinrichtung)",
                    },
                    "7000": {
                        "name": "Verbindungsleitung",
                        "alias": "Verbindungsleitung",
                        "description": "Verbindungsleitung (z.B. Wasserleitungen außerhalb der Versorgungsgebiete, die Versorgungsgebiete (Orte) miteinander verbinden), in der Wärmeversorung auch Transportleitung genannt (die eine Wärmeerzeuugungsinfrastruktur mit einem entfernten Versorgungsgebiet verbindet)",
                    },
                    "8000": {
                        "name": "Strassenablaufleitung",
                        "alias": "Straßenablaufleitung",
                        "description": "Straßenablaufleitung (in der Abwasserentsorgung)",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstige Leitung",
                        "description": "Sonstige Leitung",
                    },
                },
                "typename": "XP_RohrleitungNetz",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    werkstoff: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "2000",
            "20001",
            "20002",
            "20003",
            "2500",
            "25001",
            "25002",
            "25003",
            "25004",
            "25005",
            "3000",
            "30001",
            "30002",
            "4000",
            "5000",
            "9999",
        ]
        | None,
        Field(
            description="Werkstoff der Leitung",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Kunststoff",
                        "alias": "Kunststoff",
                        "description": "Kunststoff",
                    },
                    "10001": {
                        "name": "Polyethylen_PE",
                        "alias": "Polyethylen ( PE)",
                        "description": "Polyethylen (PE)",
                    },
                    "10002": {
                        "name": "Polyethylen_PE_HD",
                        "alias": "High-Density Polyethylen",
                        "description": "High-Density Polyethylen",
                    },
                    "10003": {
                        "name": "Polypropylen_PP",
                        "alias": "Polypropylen ( PP)",
                        "description": "Polypropylen (PP)",
                    },
                    "10004": {
                        "name": "Polycarbonat_PC",
                        "alias": "Polycarbonat ( PC)",
                        "description": "Polycarbonat (PC)",
                    },
                    "10005": {
                        "name": "Polyvinylchlorid_PVC_U",
                        "alias": "Polyvinylchlorid ( PVC- U)",
                        "description": "Polyvinylchlorid (PVC-U)",
                    },
                    "2000": {"name": "Stahl", "alias": "Stahl", "description": "Stahl"},
                    "20001": {
                        "name": "StahlVerzinkt",
                        "alias": "Stahl verzinkt",
                        "description": "Stahl verzinkt",
                    },
                    "20002": {
                        "name": "Stahlgitter",
                        "alias": "Stahlgitter",
                        "description": "Stahlfachwerkskonstruktion (z.B. Freileitungsmast als Gittermast)",
                    },
                    "20003": {
                        "name": "Stahlrohr",
                        "alias": "Stahlrohr",
                        "description": "Rohrförmiger Profilstahl, dessen Wand aus Stahl besteht. Stahlrohre dienen der Durchleitung von flüssigen, gasförmigen oder festen Stoffen, oder werden als statische oder konstruktive Elemente verwendet (z.B. Freileitungsmast als Stahlrohrmast)",
                    },
                    "2500": {
                        "name": "Stahlverbundrohr",
                        "alias": "Stahlverbundrohr",
                        "description": "Stahlverbundrohre im Rohrleitungsbau",
                    },
                    "25001": {
                        "name": "St_PE",
                        "alias": "Stahlrohr mit Standard-Kunststoffumhüllung (PE)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PE-Basis",
                    },
                    "25002": {
                        "name": "St_PP",
                        "alias": "Stahlrohr mit Kunstoffumhüllung (PP)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PP-Basis für höhere Temperatur- und Härte-Anforderungen",
                    },
                    "25003": {
                        "name": "St_FZM",
                        "alias": "Stahlrohr mit FZM-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz durch Faserzementmörtel-Ummantelung (FZM)",
                    },
                    "25004": {
                        "name": "St_GFK",
                        "alias": "Stahlrohr mit GFK-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz aus glasfaserverstärktem Kunststoff (GFK) für höchste mechanische Abriebfestigkeit bei grabenlosem Rohrvortrieb",
                    },
                    "25005": {
                        "name": "St_ZM_PE",
                        "alias": "Stahl-Verbundrohr (ZM-PE)",
                        "description": "Stahlrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserohr)",
                    },
                    "3000": {
                        "name": "Gusseisen",
                        "alias": "Gusseisen",
                        "description": "Gusseisen",
                    },
                    "30001": {
                        "name": "GGG_ZM",
                        "alias": "duktiles Gussrohr mit ZM-Auskleidung",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung (z.B Abwasserrohr)",
                    },
                    "30002": {
                        "name": "GGG_ZM_PE",
                        "alias": "duktiles Guss-Verbundrohr (ZM-PE)",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserrohr)",
                    },
                    "4000": {
                        "name": "Beton",
                        "alias": "Beton",
                        "description": "Beton (z.B. Schacht)",
                    },
                    "5000": {
                        "name": "Holz",
                        "alias": "Holz",
                        "description": "Holz (z.B. Holzmast)",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiger Werkstoff",
                        "description": "Sonstiger Werkstoff",
                    },
                },
                "typename": "XP_Werkstoff",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BSTArmatur(BSTMultiPunktobjekt):
    """Bauteil zum Verändern und Steuern von Stoffströmen, das insbesondere in Rohrleitungen für Gase und Flüssigkeiten verwendet wird"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    funktion: Annotated[
        Literal["1000", "2000", "3000", "9999"] | None,
        Field(
            description="Funktion der Armatur",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Absperrarmatur",
                        "alias": "Absperrarmatur",
                        "description": "Absperrung von Stoffströmen durch Hähne und Klappen",
                    },
                    "2000": {
                        "name": "Regulierarmatur",
                        "alias": "Regulierarmatur",
                        "description": "Regulierung des Volumenstroms mittels Schieber und Ventilen",
                    },
                    "3000": {
                        "name": "Entlueftungsarmatur",
                        "alias": "Entlüftungsarmatur",
                        "description": "Dient dem Enfernen von Gasen, insbesondere Luft, aus einer flüssigkeitsführenden Anlage",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstige Funktion",
                        "description": "sonstige Funktion",
                    },
                },
                "typename": "XP_ArmaturFunktion",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    einsatzgebiet: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "9999"] | None,
        Field(
            description="Einsatzgebiet der Armatur",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Streckenarmatur",
                        "alias": "Streckenarmatur",
                        "description": "Armaturen in Abständen entlang einer Leitung",
                    },
                    "2000": {
                        "name": "Ausblasearmatur",
                        "alias": "Ausblasearmatur",
                        "description": "Dient dem kontrollierten Ableiten von Gasen und Gas-Luftgemischen innerhalb eines Rohrnetzes",
                    },
                    "3000": {
                        "name": "Hauptabsperreinrichtung",
                        "alias": "Hauptabsperreinrichtung",
                        "description": "Hauptabsperreinrichtung",
                    },
                    "4000": {
                        "name": "Ein_Ausgangsarmatur",
                        "alias": "Ein-/ Ausgangsarmatur",
                        "description": "Eingangs- und Ausgangsarmaturen im Rohrnetz",
                    },
                    "5000": {
                        "name": "Hydrant",
                        "alias": "Hydrant",
                        "description": "Hydrant",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiges Einsatzgebiet",
                        "description": "sonstiges Einsatzgebiet",
                    },
                },
                "typename": "XP_ArmaturEinsatzgebiet",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BSTBaum(BSTMultiPunktobjekt):
    """Straßenbaum im näheren Umfeld einer Baumaßnahme"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    nrBaumkataster: Annotated[
        str | None,
        Field(
            description="Nummer des Baumes im kommunalen Straßenbaumkataster",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    stammumfang: Annotated[
        definitions.Length | None,
        Field(
            description="Umfang des Stammes",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    kronendurchmesser: Annotated[
        definitions.Length | None,
        Field(
            description="Durchmesser der Baumkrone (Kronentraufbereich)",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None


class BSTEnergiespeicher(BSTMultiFlaechenobjekt):
    """Energiespeicher dienen der Speicherung von momentan verfügbarer, aber nicht benötigter Energie zur späteren Nutzung. Diese Speicherung geht häufig einher mit einer Wandlung der Energieform, wie der von elektrischer in chemische oder potenzielle Energie."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal[
            "1000", "2000", "20001", "20002", "3000", "30001", "30002", "4000", "9999"
        ]
        | None,
        Field(
            description="Art des Energiespeichers",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Gasspeicher",
                        "alias": "Gasspeicher",
                        "description": "Oberirdische Nieder- und Mitteldruckbehälter (Gastürme, Gasometer) sowie Hochdruckbehälter (Röhrenspeicher, Kugelspeicher) zur Aufbewahrung von Gasen aller Art",
                    },
                    "2000": {
                        "name": "Untergrundspeicher",
                        "alias": "Untergrundspeicher",
                        "description": "Ein Untergrundspeicher (auch Untertagespeicher) ist ein Speicher in natürlichen oder künstlichen Hohlräumen unter der Erdoberfläche. - Untergrundspeicher gemäß Bundesberggesetz (BBergG) § 126",
                    },
                    "20001": {
                        "name": "Kavernenspeicher",
                        "alias": "Kavernenspeicher",
                        "description": "Große, künstlich angelegte Hohlräume in mächtigen unterirdischen Salzformationen, wie z.B. Salzstöcken. Kavernenspeicher werden durch einen Solprozess bergmännisch angelegt.",
                    },
                    "20002": {
                        "name": "Porenspeicher",
                        "alias": "Porenspeicher",
                        "description": "Natürliche Lagerstätten, die sich durch ihre geologische Formation zur Speicherung von Gas eignen. Sie befinden sich in porösem Gestein, in dem das Gas ähnlich einem stabilen Schwamm aufgenommen und eingelagert wird.",
                    },
                    "3000": {
                        "name": "Stromspeicher",
                        "alias": "Stromspeicher",
                        "description": "Großspeicheranlagen im Stromnetz",
                    },
                    "30001": {
                        "name": "Batteriespeicher",
                        "alias": "Batteriespeicher",
                        "description": "Großbatteriespeicher (z.B. an einer PV-Anlage)",
                    },
                    "30002": {
                        "name": "Pumpspeicherkraftwerk",
                        "alias": "Pumpspeicherkraftwerk",
                        "description": "Ein Pumpspeicherkraftwerk (PSW) speichert elektrische Energie in Form von potentieller Energie (Lageenergie) in einem Stausee",
                    },
                    "4000": {
                        "name": "Fernwaermespeicher",
                        "alias": "Fernwärmespeicher",
                        "description": "Zumeist drucklose, mit Wasser gefüllte Behälter, die Schwankungen im Wärmebedarf des Fernwärmenetzes bei gleicher Erzeugungsleistung der Fernheizwerke ausgleichen sollen",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstige Speicher",
                        "description": "Sonstige Speicher",
                    },
                },
                "typename": "XP_EnergiespeicherTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gasArt: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "2000",
            "20001",
            "20002",
            "20003",
            "20004",
            "3000",
            "4000",
            "5000",
            "6000",
            "9999",
        ]
        | None,
        Field(
            description="Art des gespeicherten Gases",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Erdgas",
                        "alias": "Erdgas",
                        "description": "Erdgas",
                    },
                    "10001": {
                        "name": "L_Gas",
                        "alias": "L-Gas",
                        "description": "L-Gas (low calorific gas)",
                    },
                    "10002": {
                        "name": "H_Gas",
                        "alias": "H-Gas",
                        "description": "H-Gas (high calorific gas)",
                    },
                    "2000": {
                        "name": "Wasserstoff",
                        "alias": "Wasserstoff",
                        "description": "Wasserstoff (H2)",
                    },
                    "20001": {
                        "name": "GruenerWasserstoff",
                        "alias": "grüner Wasserstoff",
                        "description": "Durch die Elektrolyse von Wasser hergestellter Wasserstoff unter Verwendung von Strom aus erneuerbaren Energiequellen",
                    },
                    "20002": {
                        "name": "BlauerWasserstoff",
                        "alias": "blauer Wasserstoff",
                        "description": "Grauer Wasserstoff, bei dessen Entstehung das CO2 jedoch teilweise abgeschieden und im Erdboden gespeichert wird (CCS, Carbon Capture and Storage). Maximal 90 Prozent des CO₂ sind speicherbar.",
                    },
                    "20003": {
                        "name": "OrangenerWasserstoff",
                        "alias": "orangener Wasserstoff",
                        "description": "Auf Basis von Abfall und Reststoffen produzierter Wasserstoff, der als CO2-frei gilt",
                    },
                    "20004": {
                        "name": "GrauerWasserstoff",
                        "alias": "grauer Wasserstoff",
                        "description": "Mittels Dampfreformierung meist aus fossilem Erdgas hergestellter Wasserstoff. Dabei entstehen rund 10 Tonnen CO₂ pro Tonne Wasserstoff. Das CO2 wird in die Atmosphäre abgegeben.",
                    },
                    "3000": {
                        "name": "Erdgas_H2_Gemisch",
                        "alias": "Erdgas-Wasserstoff-Gemisch",
                        "description": "Erdgas-Wasserstoff-Gemisch",
                    },
                    "4000": {
                        "name": "Biogas",
                        "alias": "Biogas",
                        "description": "Biogas",
                    },
                    "5000": {
                        "name": "Fluessiggas",
                        "alias": "Flüssiggas",
                        "description": "Flüssiggas",
                    },
                    "6000": {
                        "name": "SynthetischesMethan",
                        "alias": "synthetisch erzeugtes Methan",
                        "description": "Wird durch wasserelektrolytisch erzeugten Wasserstoff und anschließende Methanisierung hergestellt",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiges Gas",
                        "description": "sonstiges Gas",
                    },
                },
                "typename": "XP_GasTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gasDruckstufe: Annotated[
        Literal["1000", "2000", "3000", "9999"] | None,
        Field(
            description="Druckstufe des Gases",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Niederdruck",
                        "alias": "Niederdruck",
                        "description": "Niederdruck",
                    },
                    "2000": {
                        "name": "Mitteldruck",
                        "alias": "Mitteldruck",
                        "description": "Mitteldruck",
                    },
                    "3000": {
                        "name": "Hochdruck",
                        "alias": "Hochdruck",
                        "description": "Hochdruck",
                    },
                    "9999": {
                        "name": "UnbekannterDruck",
                        "alias": "Unbekannter Druck",
                        "description": "Unbekannter Druck",
                    },
                },
                "typename": "XP_GasDruckstufe",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BSTGasleitung(BSTMultiLinienobjekt):
    """Gasleitung (s. a. XP_GasTyp)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    gasArt: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "2000",
            "20001",
            "20002",
            "20003",
            "20004",
            "3000",
            "4000",
            "5000",
            "6000",
            "9999",
        ],
        Field(
            description="Art des transportierten Gases",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Erdgas",
                        "alias": "Erdgas",
                        "description": "Erdgas",
                    },
                    "10001": {
                        "name": "L_Gas",
                        "alias": "L-Gas",
                        "description": "L-Gas (low calorific gas)",
                    },
                    "10002": {
                        "name": "H_Gas",
                        "alias": "H-Gas",
                        "description": "H-Gas (high calorific gas)",
                    },
                    "2000": {
                        "name": "Wasserstoff",
                        "alias": "Wasserstoff",
                        "description": "Wasserstoff (H2)",
                    },
                    "20001": {
                        "name": "GruenerWasserstoff",
                        "alias": "grüner Wasserstoff",
                        "description": "Durch die Elektrolyse von Wasser hergestellter Wasserstoff unter Verwendung von Strom aus erneuerbaren Energiequellen",
                    },
                    "20002": {
                        "name": "BlauerWasserstoff",
                        "alias": "blauer Wasserstoff",
                        "description": "Grauer Wasserstoff, bei dessen Entstehung das CO2 jedoch teilweise abgeschieden und im Erdboden gespeichert wird (CCS, Carbon Capture and Storage). Maximal 90 Prozent des CO₂ sind speicherbar.",
                    },
                    "20003": {
                        "name": "OrangenerWasserstoff",
                        "alias": "orangener Wasserstoff",
                        "description": "Auf Basis von Abfall und Reststoffen produzierter Wasserstoff, der als CO2-frei gilt",
                    },
                    "20004": {
                        "name": "GrauerWasserstoff",
                        "alias": "grauer Wasserstoff",
                        "description": "Mittels Dampfreformierung meist aus fossilem Erdgas hergestellter Wasserstoff. Dabei entstehen rund 10 Tonnen CO₂ pro Tonne Wasserstoff. Das CO2 wird in die Atmosphäre abgegeben.",
                    },
                    "3000": {
                        "name": "Erdgas_H2_Gemisch",
                        "alias": "Erdgas-Wasserstoff-Gemisch",
                        "description": "Erdgas-Wasserstoff-Gemisch",
                    },
                    "4000": {
                        "name": "Biogas",
                        "alias": "Biogas",
                        "description": "Biogas",
                    },
                    "5000": {
                        "name": "Fluessiggas",
                        "alias": "Flüssiggas",
                        "description": "Flüssiggas",
                    },
                    "6000": {
                        "name": "SynthetischesMethan",
                        "alias": "synthetisch erzeugtes Methan",
                        "description": "Wird durch wasserelektrolytisch erzeugten Wasserstoff und anschließende Methanisierung hergestellt",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiges Gas",
                        "description": "sonstiges Gas",
                    },
                },
                "typename": "XP_GasTyp",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    druckstufe: Annotated[
        Literal["1000", "2000", "3000", "9999"] | None,
        Field(
            description="Angabe der Druckstufe",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Niederdruck",
                        "alias": "Niederdruck",
                        "description": "Niederdruck",
                    },
                    "2000": {
                        "name": "Mitteldruck",
                        "alias": "Mitteldruck",
                        "description": "Mitteldruck",
                    },
                    "3000": {
                        "name": "Hochdruck",
                        "alias": "Hochdruck",
                        "description": "Hochdruck",
                    },
                    "9999": {
                        "name": "UnbekannterDruck",
                        "alias": "Unbekannter Druck",
                        "description": "Unbekannter Druck",
                    },
                },
                "typename": "XP_GasDruckstufe",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    netzEbene: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "6000", "7000", "8000", "9999"]
        | None,
        Field(
            description="Leitungsart innerhalb des Gasnetzes",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Fernleitung",
                        "alias": "Fernleitung",
                        "description": "Fernleitung gemäß Umweltverträglichkeitsprüfung (UVPG), Anlage 1 und ENWG § 3, Nr. 19d/20; Leitungen der Fernleitungsnetzbetreiber",
                    },
                    "2000": {
                        "name": "Verteilnetzleitung",
                        "alias": "Verteilnetzleitung",
                        "description": "Leitung eines Verteil(er)netzes; Leitungen der Versorgungsunternehmen",
                    },
                    "3000": {
                        "name": "Hauptleitung",
                        "alias": "Hauptleitung",
                        "description": "Hauptleitung, oberste Leitungskategorie in einem Trinkwasser und Wärmenetz",
                    },
                    "4000": {
                        "name": "Versorgungsleitung",
                        "alias": "Versorgungsleitung",
                        "description": "Versorgungsleitung, auch Ortsleitung (z.B Wasserleitungen innerhalb des Versorgungsgebietes im bebauten Bereich)",
                    },
                    "5000": {
                        "name": "Zubringerleitung",
                        "alias": "Zubringerleitung",
                        "description": "Zubringerleitung (z.B. Wasserleitungen zwischen Wassergewinnungs- und Versorgungsgebieten)",
                    },
                    "6000": {
                        "name": "Anschlussleitung",
                        "alias": "Hausanschlussleitung",
                        "description": "Anschlussleitung, Hausanschluss (z.B. Wasserleitungen von der Abzweigstelle der Versorgungsleitung bis zur Übergabestelle/Hauptabsperreinrichtung)",
                    },
                    "7000": {
                        "name": "Verbindungsleitung",
                        "alias": "Verbindungsleitung",
                        "description": "Verbindungsleitung (z.B. Wasserleitungen außerhalb der Versorgungsgebiete, die Versorgungsgebiete (Orte) miteinander verbinden), in der Wärmeversorung auch Transportleitung genannt (die eine Wärmeerzeuugungsinfrastruktur mit einem entfernten Versorgungsgebiet verbindet)",
                    },
                    "8000": {
                        "name": "Strassenablaufleitung",
                        "alias": "Straßenablaufleitung",
                        "description": "Straßenablaufleitung (in der Abwasserentsorgung)",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstige Leitung",
                        "description": "Sonstige Leitung",
                    },
                },
                "typename": "XP_RohrleitungNetz",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    werkstoff: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "2000",
            "20001",
            "20002",
            "20003",
            "2500",
            "25001",
            "25002",
            "25003",
            "25004",
            "25005",
            "3000",
            "30001",
            "30002",
            "4000",
            "5000",
            "9999",
        ]
        | None,
        Field(
            description="Werkstoff der Leitung",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Kunststoff",
                        "alias": "Kunststoff",
                        "description": "Kunststoff",
                    },
                    "10001": {
                        "name": "Polyethylen_PE",
                        "alias": "Polyethylen ( PE)",
                        "description": "Polyethylen (PE)",
                    },
                    "10002": {
                        "name": "Polyethylen_PE_HD",
                        "alias": "High-Density Polyethylen",
                        "description": "High-Density Polyethylen",
                    },
                    "10003": {
                        "name": "Polypropylen_PP",
                        "alias": "Polypropylen ( PP)",
                        "description": "Polypropylen (PP)",
                    },
                    "10004": {
                        "name": "Polycarbonat_PC",
                        "alias": "Polycarbonat ( PC)",
                        "description": "Polycarbonat (PC)",
                    },
                    "10005": {
                        "name": "Polyvinylchlorid_PVC_U",
                        "alias": "Polyvinylchlorid ( PVC- U)",
                        "description": "Polyvinylchlorid (PVC-U)",
                    },
                    "2000": {"name": "Stahl", "alias": "Stahl", "description": "Stahl"},
                    "20001": {
                        "name": "StahlVerzinkt",
                        "alias": "Stahl verzinkt",
                        "description": "Stahl verzinkt",
                    },
                    "20002": {
                        "name": "Stahlgitter",
                        "alias": "Stahlgitter",
                        "description": "Stahlfachwerkskonstruktion (z.B. Freileitungsmast als Gittermast)",
                    },
                    "20003": {
                        "name": "Stahlrohr",
                        "alias": "Stahlrohr",
                        "description": "Rohrförmiger Profilstahl, dessen Wand aus Stahl besteht. Stahlrohre dienen der Durchleitung von flüssigen, gasförmigen oder festen Stoffen, oder werden als statische oder konstruktive Elemente verwendet (z.B. Freileitungsmast als Stahlrohrmast)",
                    },
                    "2500": {
                        "name": "Stahlverbundrohr",
                        "alias": "Stahlverbundrohr",
                        "description": "Stahlverbundrohre im Rohrleitungsbau",
                    },
                    "25001": {
                        "name": "St_PE",
                        "alias": "Stahlrohr mit Standard-Kunststoffumhüllung (PE)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PE-Basis",
                    },
                    "25002": {
                        "name": "St_PP",
                        "alias": "Stahlrohr mit Kunstoffumhüllung (PP)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PP-Basis für höhere Temperatur- und Härte-Anforderungen",
                    },
                    "25003": {
                        "name": "St_FZM",
                        "alias": "Stahlrohr mit FZM-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz durch Faserzementmörtel-Ummantelung (FZM)",
                    },
                    "25004": {
                        "name": "St_GFK",
                        "alias": "Stahlrohr mit GFK-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz aus glasfaserverstärktem Kunststoff (GFK) für höchste mechanische Abriebfestigkeit bei grabenlosem Rohrvortrieb",
                    },
                    "25005": {
                        "name": "St_ZM_PE",
                        "alias": "Stahl-Verbundrohr (ZM-PE)",
                        "description": "Stahlrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserohr)",
                    },
                    "3000": {
                        "name": "Gusseisen",
                        "alias": "Gusseisen",
                        "description": "Gusseisen",
                    },
                    "30001": {
                        "name": "GGG_ZM",
                        "alias": "duktiles Gussrohr mit ZM-Auskleidung",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung (z.B Abwasserrohr)",
                    },
                    "30002": {
                        "name": "GGG_ZM_PE",
                        "alias": "duktiles Guss-Verbundrohr (ZM-PE)",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserrohr)",
                    },
                    "4000": {
                        "name": "Beton",
                        "alias": "Beton",
                        "description": "Beton (z.B. Schacht)",
                    },
                    "5000": {
                        "name": "Holz",
                        "alias": "Holz",
                        "description": "Holz (z.B. Holzmast)",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiger Werkstoff",
                        "description": "Sonstiger Werkstoff",
                    },
                },
                "typename": "XP_Werkstoff",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BSTHausanschluss(BSTMultiPunktobjekt):
    """Hausanschluss eines Infrastrukturnetzes"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class BSTKraftwerk(BSTMultiFlaechenobjekt):
    """Technische Anlage, in der durch Energieumwandlung Elektrizität erzeugt wird. In der Kraft-Wärme-Kopplung wird zusätzlich thermische Energie bereitgestellt."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"] | None,
        Field(
            description="Art des Kraftwerks",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "ThermischeTurbine",
                        "alias": "Thermisch arbeitende Turbine",
                        "description": "Thermische arbeitende Dampfturbinen- und Gasturbinen-Kraftwerke oder Gas-und-Dampf-Kombikraftwerke",
                    },
                    "2000": {
                        "name": "Windkraft",
                        "alias": "Windkraftanlage",
                        "description": "Eine Windkraftanlage (WKA) oder Windenergieanlage (WEA) wandelt Bewegungsenergie des Windes in elektrische Energie um und speist sie in ein Stromnetz ein. Sie werden an Land (onshore) und in Offshore-Windparks im Küstenvorfeld der Meere installiert. Eine Gruppe von Windkraftanlagen wird Windpark genannt.",
                    },
                    "3000": {
                        "name": "Photovoltaik",
                        "alias": "Photovoltaik-Freinflächenanlage",
                        "description": "Eine Photovoltaikanlage, auch PV-Anlage (bzw. PVA) wandelt mittels Solarzellen ein Teil der Sonnenstrahlung in elektrische Energie um.  Die Photovoltaik-Freiflächenanlage (auch Solarpark) wird auf einer freien Fläche als fest montiertes System aufgestellt, bei dem mittels einer Unterkonstruktion die Photovoltaikmodule in einem optimalen Winkel zur Sonne (Azimut) ausgerichtet sind.",
                    },
                    "4000": {
                        "name": "Wasserkraft",
                        "alias": "Wasserkraftwerk",
                        "description": "Ein Wasserkraftwerk wandelt die potentielle Energie des Wassers in der Regel über Turbinen in mechanische bzw. elektrische Energie um. Dies kann an Fließgewässern oder Stauseen erfolgen oder durch Strömungs- und Gezeitenkraftwerke auf dem Meer (Pumpspeicherkraftwerke s. PFS_Energiespeicheer)",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiges Kraftwerk",
                        "description": "Sonstiges Kraftwerk",
                    },
                },
                "typename": "XP_KraftwerkTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    primaerenergie: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"] | None,
        Field(
            description="Energieträger, der in Dampf- und Gasturbinenkraftwerken in Sekundärenergie gewandelt wird",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "FossilerBrennstoff",
                        "alias": "fossiler Brennstoff",
                        "description": "Fossile Energie wird aus Brennstoffen gewonnen, die in geologischer Vorzeit aus Abbauprodukten von toten Pflanzen und Tieren entstanden sind. Dazu gehören Braunkohle, Steinkohle, Torf, Erdgas und Erdöl.",
                    },
                    "2000": {
                        "name": "Ersatzbrennstoff",
                        "alias": "Ersatzbrennstoff",
                        "description": "Ersatzbrennstoffe (EBS) bzw. Sekundärbrennstoffe (SBS) sind Brennstoffe, die aus Abfällen gewonnen werden. Dabei kann es sich sowohl um feste, flüssige oder gasförmige Abfälle aus Haushalten, Industrie oder Gewerbe handeln.",
                    },
                    "3000": {
                        "name": "Biomasse",
                        "alias": "Biomasse",
                        "description": "Der energietechnische Biomasse-Begriff umfasst tierische und pflanzliche Erzeugnisse, die zur Gewinnung von Heizenergie, von elektrischer Energie und als Kraftstoffe verwendet werden können (u.a. Holzpellets, Hackschnitzel, Stroh, Getreide, Altholz, Biogas). Energietechnisch relevante Biomasse kann in gasförmiger, flüssiger und fester Form vorliegen.",
                    },
                    "4000": {
                        "name": "Erdwaerme",
                        "alias": "Erdwärme",
                        "description": "Geothermie bezeichnet die in den oberen Schichten der Erdkruste gespeicherte Wärme und deren Ausbeutung zur Wärme- oder Stromerzeugung. In der Energiegewinnung wird zwischen tiefer und oberflächennaher Geothermie unterschieden. Die tiefe Geothermie wird von Kraftwerken zur Stromerzeugung genutzt.",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiger Energieträger",
                        "description": "Sonstige Energieträger",
                    },
                },
                "typename": "XP_PrimaerenergieTraeger",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    kraftWaermeKopplung: Annotated[
        bool | None,
        Field(
            description="Kraft-Wärme-Kopplung (KWK) ist die gleichzeitige Gewinnung von mechanischer Energie und nutzbarer Wärme, die in einem gemeinsamen thermodynamischen Prozess entstehen. Die mechanische Energie wird in der Regel unmittelbar in elektrischen Strom umgewandelt. Die Wärme wird für Heizzwecke als Nah- oder Fernwärme oder für Produktionsprozesse als Prozesswärme genutzt.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BSTMast(BSTMultiPunktobjekt):
    """Senkrecht stehendes und pfeilerähnliches Bauwerk eines Infrastruktnetzes"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "6000"] | None,
        Field(
            description="Typ des Mastes",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Funkmast",
                        "alias": "Funkmast",
                        "description": "ortsfester Funkanlagenstandort",
                    },
                    "2000": {
                        "name": "Sendemast",
                        "alias": "Sendemast",
                        "description": "Zumeist Konstruktion aus Stahlfachwerk oder Stahlrohr, die zur Aufnahme von Antennen für Sendezwecke bzw. zur unmittelbaren Verwendung als Sendeantenne dient (Für digitalen Datenfunk ist häufig die Nutzung vorhandener hoher Bauwerke ausreichend)",
                    },
                    "3000": {
                        "name": "Telefonmast",
                        "alias": "Telefonmast",
                        "description": "Ein Telefonmast (Telegrafenmast) trägt eine oberirdisch gezogene Fernsprechleitung",
                    },
                    "4000": {
                        "name": "Freileitungsmast",
                        "alias": "Freileitungsmast",
                        "description": "Der Freileitungsmast (Strommast) ist eine Konstruktion für die Aufhängung einer elektrischen Freileitung. Je nach Funktion lässt sich zwischen Trag-, Abspann-, Abzweig-, Kabelend- und Endabspannmasten unterscheiden. Je nach der elektrischen Spannung der Freileitung werden unterschiedliche Freileitungsmasten aus verschiedenen Materialen verwendet (Masten zur Nachrichtenübermittlung werden separat als Telefonmasten erfasst)",
                    },
                    "5000": {
                        "name": "Strassenleuchte",
                        "alias": "Straßenleuchte",
                        "description": "Trägersystem der Straßenbeleuchtung. Die Leuchte wird an der Spitze eines Holz-, Stahl-, Aluminium- oder Betonmastes montiert, wobei ein Ausleger über die Straße ragt. Teilweise werden Straßenleuchten in dicht bebauten Gebieten an Seilen hängend über der Straße (Überspannungsanlage) oder an Hauswänden angebracht.",
                    },
                    "6000": {
                        "name": "Ampel",
                        "alias": "Ampel",
                        "description": "Signalgeber einer Lichtsignalanlage (LSA) oder Lichtzeichenanlage (LZA). Sie dient der Steuerung des Straßen- und Schienenverkehrs.",
                    },
                },
                "typename": "BST_MastTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    werkstoff: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "2000",
            "20001",
            "20002",
            "20003",
            "2500",
            "25001",
            "25002",
            "25003",
            "25004",
            "25005",
            "3000",
            "30001",
            "30002",
            "4000",
            "5000",
            "9999",
        ]
        | None,
        Field(
            description="Werkstoff des Masts",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Kunststoff",
                        "alias": "Kunststoff",
                        "description": "Kunststoff",
                    },
                    "10001": {
                        "name": "Polyethylen_PE",
                        "alias": "Polyethylen ( PE)",
                        "description": "Polyethylen (PE)",
                    },
                    "10002": {
                        "name": "Polyethylen_PE_HD",
                        "alias": "High-Density Polyethylen",
                        "description": "High-Density Polyethylen",
                    },
                    "10003": {
                        "name": "Polypropylen_PP",
                        "alias": "Polypropylen ( PP)",
                        "description": "Polypropylen (PP)",
                    },
                    "10004": {
                        "name": "Polycarbonat_PC",
                        "alias": "Polycarbonat ( PC)",
                        "description": "Polycarbonat (PC)",
                    },
                    "10005": {
                        "name": "Polyvinylchlorid_PVC_U",
                        "alias": "Polyvinylchlorid ( PVC- U)",
                        "description": "Polyvinylchlorid (PVC-U)",
                    },
                    "2000": {"name": "Stahl", "alias": "Stahl", "description": "Stahl"},
                    "20001": {
                        "name": "StahlVerzinkt",
                        "alias": "Stahl verzinkt",
                        "description": "Stahl verzinkt",
                    },
                    "20002": {
                        "name": "Stahlgitter",
                        "alias": "Stahlgitter",
                        "description": "Stahlfachwerkskonstruktion (z.B. Freileitungsmast als Gittermast)",
                    },
                    "20003": {
                        "name": "Stahlrohr",
                        "alias": "Stahlrohr",
                        "description": "Rohrförmiger Profilstahl, dessen Wand aus Stahl besteht. Stahlrohre dienen der Durchleitung von flüssigen, gasförmigen oder festen Stoffen, oder werden als statische oder konstruktive Elemente verwendet (z.B. Freileitungsmast als Stahlrohrmast)",
                    },
                    "2500": {
                        "name": "Stahlverbundrohr",
                        "alias": "Stahlverbundrohr",
                        "description": "Stahlverbundrohre im Rohrleitungsbau",
                    },
                    "25001": {
                        "name": "St_PE",
                        "alias": "Stahlrohr mit Standard-Kunststoffumhüllung (PE)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PE-Basis",
                    },
                    "25002": {
                        "name": "St_PP",
                        "alias": "Stahlrohr mit Kunstoffumhüllung (PP)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PP-Basis für höhere Temperatur- und Härte-Anforderungen",
                    },
                    "25003": {
                        "name": "St_FZM",
                        "alias": "Stahlrohr mit FZM-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz durch Faserzementmörtel-Ummantelung (FZM)",
                    },
                    "25004": {
                        "name": "St_GFK",
                        "alias": "Stahlrohr mit GFK-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz aus glasfaserverstärktem Kunststoff (GFK) für höchste mechanische Abriebfestigkeit bei grabenlosem Rohrvortrieb",
                    },
                    "25005": {
                        "name": "St_ZM_PE",
                        "alias": "Stahl-Verbundrohr (ZM-PE)",
                        "description": "Stahlrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserohr)",
                    },
                    "3000": {
                        "name": "Gusseisen",
                        "alias": "Gusseisen",
                        "description": "Gusseisen",
                    },
                    "30001": {
                        "name": "GGG_ZM",
                        "alias": "duktiles Gussrohr mit ZM-Auskleidung",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung (z.B Abwasserrohr)",
                    },
                    "30002": {
                        "name": "GGG_ZM_PE",
                        "alias": "duktiles Guss-Verbundrohr (ZM-PE)",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserrohr)",
                    },
                    "4000": {
                        "name": "Beton",
                        "alias": "Beton",
                        "description": "Beton (z.B. Schacht)",
                    },
                    "5000": {
                        "name": "Holz",
                        "alias": "Holz",
                        "description": "Holz (z.B. Holzmast)",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiger Werkstoff",
                        "description": "Sonstiger Werkstoff",
                    },
                },
                "typename": "XP_Werkstoff",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BSTStrassenbeleuchtung(BSTStromleitung):
    """Stromleitung für die Straßenbeleuchtung"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class IGPAusbauformWechsel(IGPMultiPunktobjekt):
    """Sofern für ein Vorhaben nur abschnittsweise eine Änderung oder Erweiterung einer bestehenden Leitung oder ein Ersatz- oder Parallelneubau zu einer bestehenden Leitung vorgesehen ist, benennt der zuständige Übertragungsnetzbetreiber den voraussichtlichen Ort für den Wechsel zwischen den Ausbauformen"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "9999"],
        Field(
            description="Art des Ausbauformwechsels",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Aenderung_Neubau",
                        "alias": "Änderung/Erweiterung - Neubau",
                        "description": "Vorgesehener Anschluss einer geänderten bzw. erweiterten Bestandsleitung an eine neu zu bauende Leitung",
                    },
                    "2000": {
                        "name": "Aenderung_Ersatzneubau",
                        "alias": "Änderung/Erweiterung - Ersatzneubau",
                        "description": "Vorgesehener Anschluss einer geänderten bzw. erweiterten Bestandsleitung an einen Ersatzneubau",
                    },
                    "3000": {
                        "name": "Aenderung_Parallelneubau",
                        "alias": "Änderung/Erweiterung - Parallelneubau",
                        "description": "Vorgesehener Anschluss einer geänderten bzw. erweiterten Bestandsleitung an einen Parallelneubau",
                    },
                    "4000": {
                        "name": "Ersatzneubau_Neubau",
                        "alias": "Ersatzneubau - Neubau",
                        "description": "Vorgesehener Anschluss eines Ersatzneubaus an einen Leitungsneubau",
                    },
                    "5000": {
                        "name": "Parallelneubau_Neubau",
                        "alias": "Parallelneubau - Neubau",
                        "description": "Vorgesehener Anschluss eines Parallelneubaus an einen Leitungsneubau",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "Sonstiges",
                        "description": "sonstiges",
                    },
                },
                "typename": "IGP_AusbauformWechselTyp",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]


class IGPInfrastrukturgebiet(IGPMultiFlaechenobjekt):
    """Infrastrukturgebiet gemäß EnWG.
    Bei den Infrastrukturgebieten handelt es sich nicht um einen Korridor mit gleichbleibender Breite, sondern um einen mäandrierenden Gebietsstreifen, aus dem inselförmige Bereiche mit erwartbar höherer Konfliktlage ausgenommen sein können. Infrastrukturgebiete werden in der Regel eine Breite von circa fünf bis zehn Kilometer aufweisen, wenngleich einer Vorhersage dieser Breite, die sich aus den Merkmalen der Raum- und Umweltsituation ergibt, Grenzen gesetzt sind. Sofern die Bestätigung des Netzentwicklungsplans für die Vorhaben eine Änderung und Erweiterung von Leitungen im Sinne von § 3 Nummer 1 NABEG, einen Ersatzneubau im Sinne von § 3 Nummer 4 NABEG oder einen Parallelneubau im Sinne von § 3 Nummer 5 NABEG vorsieht, werden Infrastrukturgebiete in der Regel eine geringere Breite aufweisen.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    massnahmeNEP: Annotated[
        str,
        Field(
            description="Im Netzentwicklungsplan Strom (NEP) bestätigte Maßnahme für Energieleitungen",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    uebertragungstyp: Annotated[
        Literal["1000", "2000"] | None,
        Field(
            description="Typ der Übertragung von Hochspannungsstrom",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "HGUe",
                        "alias": "HGÜ",
                        "description": "Hochspannungs-Gleichstrom-Übertragung (HGÜ)",
                    },
                    "2000": {
                        "name": "HDUe",
                        "alias": "HDÜ",
                        "description": "Hochspannungs-Drehstrom-Übertragung (HDÜ) - Drehstrom = Dreiphasenwechselstrom",
                    },
                },
                "typename": "IGP_UebertragungTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    leitungsart: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "10006",
            "2000",
            "20001",
            "20002",
            "20003",
        ]
        | None,
        Field(
            description="Bei Höchstspannungs-Drehstrom-Übertragungen (HDÜ) ist eine Freileitung zugrunde zu legen, bei Höchstspannungs-Gleichstrom-Übertragungen (HGÜ) hingegen ein Erdkabel",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Erdverlegt",
                        "alias": "erdverlegte (Rohr-)Leitungen",
                        "description": "Oberkategorie für erdverlegte (Rohr-)Leitungen",
                    },
                    "10001": {
                        "name": "Erdkabel",
                        "alias": "Erdkabel",
                        "description": "Ein Erdkabel ist ein im Erdboden verlegtes elektrisch genutztes Kabel mit einer besonders robusten Isolierung nach außen, dem Kabelmantel, der eine Zerstörung derselben durch chemische Einflüsse im Erdreich bzw. im Boden lebender Kleintiere verhindert.",
                    },
                    "10002": {
                        "name": "Seekabel",
                        "alias": "Seekabel",
                        "description": "Ein Seekabel (auch Unterseekabel, Unterwasserkabel) ist ein im Wesentlichen in einem Gewässer verlegtes Kabel zur Datenübertragung oder die Übertragung elektrischer Energie.",
                    },
                    "10003": {
                        "name": "Schutzrohr",
                        "alias": "Schutzrohr",
                        "description": "Im Schutzrohr verlegte oder zu verlegende Kabel/Leitungen. - Schutzrohre schützen erdverlegte Leitungen vor mechanischen Einflüssen und Feuchtigkeit.",
                    },
                    "10004": {
                        "name": "Leerrohr",
                        "alias": "Leerrohr (unbelegtes Schutzrohr)",
                        "description": "Über die Baumaßnahme hinaus unbelegtes Schutzrohr",
                    },
                    "10005": {
                        "name": "Leitungsbuendel",
                        "alias": "Leitungsbündel",
                        "description": "Bündel von Kabeln und/oder Schutzrohren in den Sparten Sparten Strom und Telekommunikation im Bestand",
                    },
                    "10006": {
                        "name": "Dueker",
                        "alias": "Düker",
                        "description": "Druckleitung zur Unterquerung von Straßen, Flüssen, Bahngleisen etc. Im Düker kann die Flüssigkeit das Hindernis überwinden, ohne dass Pumpen eingesetzt werden müssen.",
                    },
                    "2000": {
                        "name": "Oberirdisch",
                        "alias": "oberirdischer Verlauf",
                        "description": "Oberirdisch verlegte Leitungen und Rohre",
                    },
                    "20001": {
                        "name": "Freileitung",
                        "alias": "Freileitung",
                        "description": "Elektrische Leitung, deren spannungsführende Leiter im Freien durch die Luft geführt und meist auch nur durch die umgebende Luft voneinander und vom Erdboden isoliert sind. In der Regel werden die Leiterseile von Freileitungsmasten getragen, an denen sie mit Isolatoren befestigt sind.",
                    },
                    "20002": {
                        "name": "Heberleitung",
                        "alias": "Heberleitung",
                        "description": "Leitung zur Überquerung von Straßen oder zur Verbindung von Behältern (Gegenstück zu einem Düker)",
                    },
                    "20003": {
                        "name": "Rohrbruecke",
                        "alias": "Rohrbrücke",
                        "description": "Eine Rohrbrücke oder Rohrleitungsbrücke dient dazu, einzelne oder mehrere Rohrleitungen oberirdisch über größere Entfernungen zu führen.",
                    },
                },
                "typename": "XP_LeitungTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class IGPKopplungsraum(IGPMultiFlaechenobjekt):
    """Räume, an denen die Infrastrukturgebiete von Maßnahmen miteinander gekoppelt werden, so dass hier die gemeinsame Führung beginnt beziehungsweise endet. Kopplungsräume sind Räume, die von mehreren Maßnahmen erreicht werden müssen, um eine Bündelung zu ermöglichen."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    massnahmeNEP: Annotated[
        list[str] | None,
        Field(
            description="Im Netzentwicklungsplan Strom (NEP) bestätigte Maßnahmen für Energieleitungen",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..*",
            },
        ),
    ] = None


class IGPMassnahmeFlaeche(IGPMultiFlaechenobjekt):
    """Nach § 36 des Bundesnaturschutzgesetzes in Verbindung mit § 34 Absatz 5 des Bundesnaturschutzgesetzes notwendige Maßnahmen sind in dem Infrastrukturgebieteplan vorzusehen.
    Infrastrukturgebieteplan sieht Regeln für verhältnismäßige Minderungsmaßnahmen vor, die zu ergreifen sind, um mögliche Auswirkungen auf die Erhaltungsziele im Sinne des § 7 Absatz 1 Nummer 9 des Bundesnaturschutzgesetzes und auf besonders geschützte Arten nach § 7 Absatz 2 Nummer 13 des Bundesnaturschutzgesetzes zu vermeiden oder, falls dies nicht möglich ist, solche Auswirkungen erheblich zu verringern.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class IGPMassnahmeLinie(IGPMultiLinienobjekt):
    """Nach § 36 des Bundesnaturschutzgesetzes in Verbindung mit § 34 Absatz 5 des Bundesnaturschutzgesetzes notwendige Maßnahmen sind in dem Infrastrukturgebieteplan vorzusehen.
    Infrastrukturgebieteplan sieht Regeln für verhältnismäßige Minderungsmaßnahmen vor, die zu ergreifen sind, um mögliche Auswirkungen auf die Erhaltungsziele im Sinne des § 7 Absatz 1 Nummer 9 des Bundesnaturschutzgesetzes und auf besonders geschützte Arten nach § 7 Absatz 2 Nummer 13 des Bundesnaturschutzgesetzes zu vermeiden oder, falls dies nicht möglich ist, solche Auswirkungen erheblich zu verringern.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class IGPMassnahmePunkt(IGPMultiPunktobjekt):
    """Nach § 36 des Bundesnaturschutzgesetzes in Verbindung mit § 34 Absatz 5 des Bundesnaturschutzgesetzes notwendige Maßnahmen sind in dem Infrastrukturgebieteplan vorzusehen.
    Infrastrukturgebieteplan sieht Regeln für verhältnismäßige Minderungsmaßnahmen vor, die zu ergreifen sind, um mögliche Auswirkungen auf die Erhaltungsziele im Sinne des § 7 Absatz 1 Nummer 9 des Bundesnaturschutzgesetzes und auf besonders geschützte Arten nach § 7 Absatz 2 Nummer 13 des Bundesnaturschutzgesetzes zu vermeiden oder, falls dies nicht möglich ist, solche Auswirkungen erheblich zu verringern.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class IGPPlan(IPPlan):
    """Klasse zur Modellierung eines Infrastrukturgebieteplans"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    version: Annotated[
        IGPVersion,
        Field(
            description="Entwurfsversion/Variante des Plans",
            json_schema_extra={
                "typename": "IGP_Version",
                "stereotype": "DataType",
                "multiplicity": "1",
            },
        ),
    ]
    vorgaengerVersion: Annotated[
        IGPVorgaengerVersion | None,
        Field(
            description="Version des vorherigen Plans",
            json_schema_extra={
                "typename": "IGP_VorgaengerVersion",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    beteiligte: Annotated[
        list[XPAkteur] | None,
        Field(
            description="Zentrale Akteure des Verfahrens",
            json_schema_extra={
                "typename": "XP_Akteur",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    bundesbedarfsplanDatum: Annotated[
        date_aliased | None,
        Field(
            description="Die Ausweisung des Infrastrukturgebiets erfolgt spätestens 20 Monate, nachdem der Bundesbedarfsplan nach § 12e EnWG geändert wurde",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    auslegungInternetStartDatum: Annotated[
        date_aliased | None,
        Field(
            description="Die Unterlagen für die Strategische Umweltprüfung sowie der Entwurf des Infrastrukturgebieteplans sind für die Dauer von einem Monat auf der Internetseite der Planfeststellungsbehörde oder der nach Landesrecht zuständigen Behörde auszulegen",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    auslegungInternetEndDatum: Annotated[
        date_aliased | None,
        Field(
            description="Die Unterlagen für die Strategische Umweltprüfung sowie der Entwurf des Infrastrukturgebieteplans sind für die Dauer von einem Monat auf der Internetseite der Planfeststellungsbehörde oder der nach Landesrecht zuständigen Behörde auszulegen",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ausweisungDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum der Ausweisung",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class ISAAbwasserleitung(ISAMultiLinienobjekt):
    """Hierunter fallen Abwasserkanäle, Haltungen sowie weitere Rohre, die zur Abwasserbeseitigung benutzt werden.
    TYP: Z.B. Angaben zur Art der Abwasserleitung (wie Mischwasser / Regenwasser / Schmutzwasser / Druckrohrleitung ), Nennweite, Angaben zum Material
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    verlegetiefe: Annotated[
        int,
        Field(
            description="Positive Ganzzahl in cm (0 = Information liegt nicht vor).\r\nDie Verlegetiefe gibt der an einer Mitnutzung interessierten Person Anhaltspunkte für die Erreichbarkeit der unterirdischen Einrichtungen und hilft bei der Koordinierung von Bauarbeiten.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]


class ISAAmpel(ISAMultiPunktobjekt):
    """Hierunter fallen alle dauerhaft angebrachten Lichtzeichenanlagen. Nicht zu liefern sind temporär aufgestellte Lichtzeichenanlagen, wie z.B. Baustellenampeln.
    TYP: Z.B. Angaben zur Art (wie Ampelbrücke, Peitschenmast, Fußgängerampel, Kreuzungsampel)
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    strom: Annotated[
        Literal["1000", "2000", "9999"],
        Field(
            description="Das Attribut der Stromversorgung gibt der an einer Mitnutzung interessierten Person Anhaltspunkte ob sich eine Trägerstruktur für die Errichtung von Standorten für drahtlose Zugangspunkte mit geringer Reichweite eignet. Ob die Stromversorgung nur temporär geschaltet ist, ist für eine Aufnahme der Einrichtung in den ISA nicht entscheidend.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "StromVorhanden",
                        "alias": "Strom vorhanden",
                        "description": "Stromversorgung ist vorhanden",
                    },
                    "2000": {
                        "name": "KeinStrom",
                        "alias": "kein Strom",
                        "description": "Keine Stromversorgung vorhanden",
                    },
                    "9999": {
                        "name": "keineAngabe",
                        "alias": "keine Angabe",
                        "description": "Informationen liegen nicht vor",
                    },
                },
                "typename": "ISA_Stromversorgung",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]


class ISABauwerk(ISAMultiPunktobjekt):
    """Hierunter fallen Gebäude öffentlicher Stellen und andere oberirdische Bauwerke, die für den Ausbau von Hochgeschwindigkeitsnetzen genutzt werden können (insbesondere als Standort für drahtlose Zugangspunkte mit geringer Reichweite, Antennenstandort oder Technikraum), die aber nicht einer der engeren Kategorien wie HVt, KVz, PoP oder Funkmast zugeordnet werden können. Beispiele hierfür sind öffentliche Gebäude wie Schulen, Kirchen etc. und Wassertürme, Wasserhochbehälter, begehbare Trafostationen, Drosselsysteme, Rechen.
    TYP: Z.B. genauere Bezeichnung
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    strom: Annotated[
        Literal["1000", "2000", "9999"],
        Field(
            description="Das Attribut der Stromversorgung gibt der an einer Mitnutzung interessierten Person Anhaltspunkte ob sich eine Trägerstruktur für die Errichtung von Standorten für drahtlose Zugangspunkte mit geringer Reichweite eignet. Ob die Stromversorgung nur temporär geschaltet ist, ist für eine Aufnahme der Einrichtung in den ISA nicht entscheidend.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "StromVorhanden",
                        "alias": "Strom vorhanden",
                        "description": "Stromversorgung ist vorhanden",
                    },
                    "2000": {
                        "name": "KeinStrom",
                        "alias": "kein Strom",
                        "description": "Keine Stromversorgung vorhanden",
                    },
                    "9999": {
                        "name": "keineAngabe",
                        "alias": "keine Angabe",
                        "description": "Informationen liegen nicht vor",
                    },
                },
                "typename": "ISA_Stromversorgung",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]


class ISAFunkmast(ISAMultiPunktobjekt):
    """Hierunter fallen alle Einrichtungen, die als Trägerstrukturen für Funktechnologien genutzt werden können wie z. B. Masten, Türme, Pfähle, Antennenanlagen oder -standorte."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    strom: Annotated[
        Literal["1000", "2000", "9999"],
        Field(
            description="Das Attribut der Stromversorgung gibt der an einer Mitnutzung interessierten Person Anhaltspunkte ob sich eine Trägerstruktur für die Errichtung von Standorten für drahtlose Zugangspunkte mit geringer Reichweite eignet. Ob die Stromversorgung nur temporär geschaltet ist, ist für eine Aufnahme der Einrichtung in den ISA nicht entscheidend.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "StromVorhanden",
                        "alias": "Strom vorhanden",
                        "description": "Stromversorgung ist vorhanden",
                    },
                    "2000": {
                        "name": "KeinStrom",
                        "alias": "kein Strom",
                        "description": "Keine Stromversorgung vorhanden",
                    },
                    "9999": {
                        "name": "keineAngabe",
                        "alias": "keine Angabe",
                        "description": "Informationen liegen nicht vor",
                    },
                },
                "typename": "ISA_Stromversorgung",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]


class ISAGlasfaser(ISAMultiLinienobjekt):
    """Hierunter fallen Lichtwellenleiter-Kabel (LWL-Kabel) inkl. Glasfaser-Hausanschlüsse.
    TYP: Z.B. Art der Verlegung: erdverlegt/Erdkabel, oberirdische Verlegung/Luftkabel; Kabel-Durchmesser, Faseranzahl
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    verlegetiefe: Annotated[
        int,
        Field(
            description="Positive Ganzzahl in cm (0 = Information liegt nicht vor).\r\nDie Verlegetiefe gibt der an einer Mitnutzung interessierten Person Anhaltspunkte für die Erreichbarkeit der unterirdischen Einrichtungen und hilft bei der Koordinierung von Bauarbeiten.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]


class ISAHaltestelle(ISAMultiPunktobjekt):
    """Hier sind Haltestellenpunkte von Bus- und Straßenbahnhaltestellen sowie U-Bahnhöfen zu liefern.
    TYP: Z.B. Angaben zur Lage (oberirdisch/unterirdisch), genauere Bezeichnung der gelieferten Punktgeometrie (wie Haltestellenmittelpunkt, Haltestellenmast, Zugänge zur Haltestelle) oder Ausstattungsmerkmale (wie Haltestellenschild , Wartehallen, dynamische Fahrgastinformationen)
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    strom: Annotated[
        Literal["1000", "2000", "9999"],
        Field(
            description="Das Attribut der Stromversorgung gibt der an einer Mitnutzung interessierten Person Anhaltspunkte ob sich eine Trägerstruktur für die Errichtung von Standorten für drahtlose Zugangspunkte mit geringer Reichweite eignet. Ob die Stromversorgung nur temporär geschaltet ist, ist für eine Aufnahme der Einrichtung in den ISA nicht entscheidend.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "StromVorhanden",
                        "alias": "Strom vorhanden",
                        "description": "Stromversorgung ist vorhanden",
                    },
                    "2000": {
                        "name": "KeinStrom",
                        "alias": "kein Strom",
                        "description": "Keine Stromversorgung vorhanden",
                    },
                    "9999": {
                        "name": "keineAngabe",
                        "alias": "keine Angabe",
                        "description": "Informationen liegen nicht vor",
                    },
                },
                "typename": "ISA_Stromversorgung",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]


class ISAHauptverteiler(ISAMultiPunktobjekt):
    """Unter Hauptverteiler (HVt) sind übergeordnete Knotenpunkte des Konzentrations- zum Zugangsnetz zu verstehen. Diese befinden sich in der Regel in einer Vermittlungsstelle. Hierunter fallen nur HVt, die sich für Telekommunikationszwecke eignen, aber nicht die HVt, die ausschließlich einer anderen gegenwärtigen Nutzung (z.B. Elektrizität) zuzuordnen sind.
    TYP: Z.B. genauere Bezeichnung
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class ISAHolzMast(ISAMultiPunktobjekt):
    """Hierunter fallen alle Einrichtungen, die als Trägerstrukturen für die oberirdische Verlegung von Glasfasern verwendet werden (können). Beispiele hierfür sind Holzmasten oder Freileitungsmasten für Hoch-, Mittel- und Niederspannung, sofern sie nicht bereits als Funkmast genutzt werden.
    TYP: Z.B. Angaben zur Art (wie Hoch-, Mittel- oder Niedrigspannung), Angaben zum Material/Typ (wie Holzmast, Stahlbetonmast, Stahlrohrmast, A-Mast)
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    strom: Annotated[
        Literal["1000", "2000", "9999"],
        Field(
            description="Das Attribut der Stromversorgung gibt der an einer Mitnutzung interessierten Person Anhaltspunkte ob sich eine Trägerstruktur für die Errichtung von Standorten für drahtlose Zugangspunkte mit geringer Reichweite eignet. Ob die Stromversorgung nur temporär geschaltet ist, ist für eine Aufnahme der Einrichtung in den ISA nicht entscheidend.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "StromVorhanden",
                        "alias": "Strom vorhanden",
                        "description": "Stromversorgung ist vorhanden",
                    },
                    "2000": {
                        "name": "KeinStrom",
                        "alias": "kein Strom",
                        "description": "Keine Stromversorgung vorhanden",
                    },
                    "9999": {
                        "name": "keineAngabe",
                        "alias": "keine Angabe",
                        "description": "Informationen liegen nicht vor",
                    },
                },
                "typename": "ISA_Stromversorgung",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]


class ISAKabelverzweiger(ISAMultiPunktobjekt):
    """Unter Kabelverzweigern (KVz) sind passive Knotenpunkte des Zugangssnetzes zu verstehen. Diese stellen die Verbindung zwischen HVt und den Hausanschlüssen dar. Hierunter fallen nur KVz, die sich für Telekommunikationszwecke eignen, aber nicht KVz, die ausschließlich einer anderen gegenwärtigen Nutzung (z.B. Elektrizität) zuzuordnen sind.
    TYP: Z.B. genauere Bezeichnung (wie Multifunktionsgehäuse, Netzverteiler (NVZ), Outdoor-DSLAM)
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class ISALehrrohr(ISAMultiLinienobjekt):
    """Hierunter fallen – unabhängig vom Belegungsgrad – jegliche Mantelstrukturen/Rohre aus den Sparten Telekommunikation, Gas, Elektrizität, Fernwärme, Wasser und Verkehr. Beispiele hierfür sind Kabelschutzrohre, Mikrokabelschutzrohre, Speed Pipes, stillgelegte Versorgungsleitungen, Fernleitungen, Kabelkanäle und –tröge, papierummantelte Bleirohre oder stillgelegte, aber noch nicht verfüllte Trinkwasserleitungen, Betonkanalsysteme, Düker, Kollektoren. Bestehende Hausanschlüsse sind auch zu liefern.
    TYP: Z.B. Nennweite, Typ des Leerrohrs (vgl. Hinweise Zuordnung), Angaben zum Material.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    verlegetiefe: Annotated[
        int,
        Field(
            description="Positive Ganzzahl in cm (0 = Information liegt nicht vor).\r\nDie Verlegetiefe gibt der an einer Mitnutzung interessierten Person Anhaltspunkte für die Erreichbarkeit der unterirdischen Einrichtungen und hilft bei der Koordinierung von Bauarbeiten.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]


class PFSArmaturengruppe(PFSMultiPunktobjekt):
    """Bauteil zum Verändern und Steuern von Stoffströmen, das insbesondere in Rohrleitungen für Gase und Flüssigkeiten verwendet wird"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    funktion: Annotated[
        list[Literal["1000", "2000", "3000", "9999"]] | None,
        Field(
            description="Funktion(en) der Armaturengruppe.",
            json_schema_extra={
                "typename": "XP_ArmaturFunktion",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {
                        "name": "Absperrarmatur",
                        "alias": "Absperrarmatur",
                        "description": "Absperrung von Stoffströmen durch Hähne und Klappen",
                    },
                    "2000": {
                        "name": "Regulierarmatur",
                        "alias": "Regulierarmatur",
                        "description": "Regulierung des Volumenstroms mittels Schieber und Ventilen",
                    },
                    "3000": {
                        "name": "Entlueftungsarmatur",
                        "alias": "Entlüftungsarmatur",
                        "description": "Dient dem Enfernen von Gasen, insbesondere Luft, aus einer flüssigkeitsführenden Anlage",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstige Funktion",
                        "description": "sonstige Funktion",
                    },
                },
            },
        ),
    ] = None
    einsatzgebiet: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000", "9999"]] | None,
        Field(
            description="Einsatzgebiet(e) der Armaturengruppe",
            json_schema_extra={
                "typename": "XP_ArmaturEinsatzgebiet",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {
                        "name": "Streckenarmatur",
                        "alias": "Streckenarmatur",
                        "description": "Armaturen in Abständen entlang einer Leitung",
                    },
                    "2000": {
                        "name": "Ausblasearmatur",
                        "alias": "Ausblasearmatur",
                        "description": "Dient dem kontrollierten Ableiten von Gasen und Gas-Luftgemischen innerhalb eines Rohrnetzes",
                    },
                    "3000": {
                        "name": "Hauptabsperreinrichtung",
                        "alias": "Hauptabsperreinrichtung",
                        "description": "Hauptabsperreinrichtung",
                    },
                    "4000": {
                        "name": "Ein_Ausgangsarmatur",
                        "alias": "Ein-/ Ausgangsarmatur",
                        "description": "Eingangs- und Ausgangsarmaturen im Rohrnetz",
                    },
                    "5000": {
                        "name": "Hydrant",
                        "alias": "Hydrant",
                        "description": "Hydrant",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiges Einsatzgebiet",
                        "description": "sonstiges Einsatzgebiet",
                    },
                },
            },
        ),
    ] = None


class PFSBaugrube(PFSMultiPunktobjekt):
    """Baugrube zur Erstellung von geschlossenen Querungen von Straßen, Gräben u.a."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal["1000", "2000"] | None,
        Field(
            description="Auswahl der Start- und Zielgrube",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Startgrube",
                        "alias": "Startgrube",
                        "description": "Startgrube",
                    },
                    "2000": {
                        "name": "Zielgrube",
                        "alias": "Zielgrube",
                        "description": "Zielgrube",
                    },
                },
                "typename": "XP_BaugrubeTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class PFSBaugrubeFlaeche(PFSMultiFlaechenobjekt):
    """Baugrube zur Erstellung von geschlossenen Querungen (alternative Spezifizierung zu PFS_Baugrube)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal["1000", "2000"] | None,
        Field(
            description="Art der Baustelle",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Startgrube",
                        "alias": "Startgrube",
                        "description": "Startgrube",
                    },
                    "2000": {
                        "name": "Zielgrube",
                        "alias": "Zielgrube",
                        "description": "Zielgrube",
                    },
                },
                "typename": "XP_BaugrubeTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class PFSBaustelle(PFSMultiFlaechenobjekt):
    """Geplante temporäre Flächennutzungen während der Bauphase"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "6000"] | None,
        Field(
            description="Art der Baustelle",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Lagerplatz",
                        "alias": "Lagerplatz",
                        "description": "Temporär genutzte Fläche für die Lagerung von Baumaterial wie Rohre und Leitungen",
                    },
                    "2000": {
                        "name": "TechnischeAnlage",
                        "alias": "technische Anlage",
                        "description": "Temporär eingerichte technische Anlage z.B. zur Behandlung von Wasser. Zu der Anlage können auch Zu- und Ablaufbecken sowie Flächen für Aufstellung und Betrieb gehören.",
                    },
                    "3000": {
                        "name": "BauzeitlicheZufahrt",
                        "alias": "bauzeitliche Zufahrt",
                        "description": "Trassenzufahrt oder Überfahrt für Baufahrzeuge und einzusetzende Maschinen",
                    },
                    "4000": {
                        "name": "Baufeld",
                        "alias": "Baufeld",
                        "description": "geplantes Baufeld",
                    },
                    "5000": {
                        "name": "Entwaesserung",
                        "alias": "Entwässerung",
                        "description": "Fläche zur Versickerung (bei Grundwasser) oder eine temporäre Ablaufleitung",
                    },
                    "6000": {
                        "name": "Arbeitsstreifen",
                        "alias": "Arbeitsstreifen",
                        "description": "Regelarbeitsstreifen auf freier Feldflur entlang der Trasse",
                    },
                },
                "typename": "PFS_BaustelleTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class PFSEnergiekopplungsanlage(PFSMultiFlaechenobjekt):
    """Anlagen zur Umwandlung von Strom in andere Energieträger wie Wärme, Kälte, Produkt, Kraft- oder Rohstoff und insbesondere Elektrolyseanlagen ("Power-to-X"-Anlagen)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    elektrolyseleistung: Annotated[
        definitions.GenericMeasure | None,
        Field(
            description="Elektrolyseleistung in MWh/hel",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "MW",
            },
        ),
    ] = None
    begrenzung: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Bestimmung der dargestellten Fläche",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Betriebsgelaende",
                        "alias": "Betriebsgelände",
                        "description": "gesamtes Betriebsgelände bzw. Grundstücksfläche",
                    },
                    "2000": {
                        "name": "EingezaeunteFlaeche",
                        "alias": "eingezäunte Fläche",
                        "description": "eingezäuntes Gelände der Infrastrukturgebäude (ohne Parkplätze und Nebengebäude)",
                    },
                    "3000": {
                        "name": "Gebaeudeflaeche",
                        "alias": "Gebäudefläche",
                        "description": "Fläche eines Gebäudes, das technische Anlagen enthält",
                    },
                },
                "typename": "XP_InfrastrukturFlaeche",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class PFSEnergiespeicher(PFSMultiFlaechenobjekt):
    """Energiespeicher dienen der Speicherung von momentan verfügbarer, aber nicht benötigter Energie zur späteren Nutzung. Diese Speicherung geht häufig einher mit einer Wandlung der Energieform, wie der von elektrischer in chemische oder potenzielle Energie."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal[
            "1000", "2000", "20001", "20002", "3000", "30001", "30002", "4000", "9999"
        ]
        | None,
        Field(
            description="Art des Energiespeichers",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Gasspeicher",
                        "alias": "Gasspeicher",
                        "description": "Oberirdische Nieder- und Mitteldruckbehälter (Gastürme, Gasometer) sowie Hochdruckbehälter (Röhrenspeicher, Kugelspeicher) zur Aufbewahrung von Gasen aller Art",
                    },
                    "2000": {
                        "name": "Untergrundspeicher",
                        "alias": "Untergrundspeicher",
                        "description": "Ein Untergrundspeicher (auch Untertagespeicher) ist ein Speicher in natürlichen oder künstlichen Hohlräumen unter der Erdoberfläche. - Untergrundspeicher gemäß Bundesberggesetz (BBergG) § 126",
                    },
                    "20001": {
                        "name": "Kavernenspeicher",
                        "alias": "Kavernenspeicher",
                        "description": "Große, künstlich angelegte Hohlräume in mächtigen unterirdischen Salzformationen, wie z.B. Salzstöcken. Kavernenspeicher werden durch einen Solprozess bergmännisch angelegt.",
                    },
                    "20002": {
                        "name": "Porenspeicher",
                        "alias": "Porenspeicher",
                        "description": "Natürliche Lagerstätten, die sich durch ihre geologische Formation zur Speicherung von Gas eignen. Sie befinden sich in porösem Gestein, in dem das Gas ähnlich einem stabilen Schwamm aufgenommen und eingelagert wird.",
                    },
                    "3000": {
                        "name": "Stromspeicher",
                        "alias": "Stromspeicher",
                        "description": "Großspeicheranlagen im Stromnetz",
                    },
                    "30001": {
                        "name": "Batteriespeicher",
                        "alias": "Batteriespeicher",
                        "description": "Großbatteriespeicher (z.B. an einer PV-Anlage)",
                    },
                    "30002": {
                        "name": "Pumpspeicherkraftwerk",
                        "alias": "Pumpspeicherkraftwerk",
                        "description": "Ein Pumpspeicherkraftwerk (PSW) speichert elektrische Energie in Form von potentieller Energie (Lageenergie) in einem Stausee",
                    },
                    "4000": {
                        "name": "Fernwaermespeicher",
                        "alias": "Fernwärmespeicher",
                        "description": "Zumeist drucklose, mit Wasser gefüllte Behälter, die Schwankungen im Wärmebedarf des Fernwärmenetzes bei gleicher Erzeugungsleistung der Fernheizwerke ausgleichen sollen",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstige Speicher",
                        "description": "Sonstige Speicher",
                    },
                },
                "typename": "XP_EnergiespeicherTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gasArt: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "2000",
            "20001",
            "20002",
            "20003",
            "20004",
            "3000",
            "4000",
            "5000",
            "6000",
            "9999",
        ]
        | None,
        Field(
            description="Art des Gases",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Erdgas",
                        "alias": "Erdgas",
                        "description": "Erdgas",
                    },
                    "10001": {
                        "name": "L_Gas",
                        "alias": "L-Gas",
                        "description": "L-Gas (low calorific gas)",
                    },
                    "10002": {
                        "name": "H_Gas",
                        "alias": "H-Gas",
                        "description": "H-Gas (high calorific gas)",
                    },
                    "2000": {
                        "name": "Wasserstoff",
                        "alias": "Wasserstoff",
                        "description": "Wasserstoff (H2)",
                    },
                    "20001": {
                        "name": "GruenerWasserstoff",
                        "alias": "grüner Wasserstoff",
                        "description": "Durch die Elektrolyse von Wasser hergestellter Wasserstoff unter Verwendung von Strom aus erneuerbaren Energiequellen",
                    },
                    "20002": {
                        "name": "BlauerWasserstoff",
                        "alias": "blauer Wasserstoff",
                        "description": "Grauer Wasserstoff, bei dessen Entstehung das CO2 jedoch teilweise abgeschieden und im Erdboden gespeichert wird (CCS, Carbon Capture and Storage). Maximal 90 Prozent des CO₂ sind speicherbar.",
                    },
                    "20003": {
                        "name": "OrangenerWasserstoff",
                        "alias": "orangener Wasserstoff",
                        "description": "Auf Basis von Abfall und Reststoffen produzierter Wasserstoff, der als CO2-frei gilt",
                    },
                    "20004": {
                        "name": "GrauerWasserstoff",
                        "alias": "grauer Wasserstoff",
                        "description": "Mittels Dampfreformierung meist aus fossilem Erdgas hergestellter Wasserstoff. Dabei entstehen rund 10 Tonnen CO₂ pro Tonne Wasserstoff. Das CO2 wird in die Atmosphäre abgegeben.",
                    },
                    "3000": {
                        "name": "Erdgas_H2_Gemisch",
                        "alias": "Erdgas-Wasserstoff-Gemisch",
                        "description": "Erdgas-Wasserstoff-Gemisch",
                    },
                    "4000": {
                        "name": "Biogas",
                        "alias": "Biogas",
                        "description": "Biogas",
                    },
                    "5000": {
                        "name": "Fluessiggas",
                        "alias": "Flüssiggas",
                        "description": "Flüssiggas",
                    },
                    "6000": {
                        "name": "SynthetischesMethan",
                        "alias": "synthetisch erzeugtes Methan",
                        "description": "Wird durch wasserelektrolytisch erzeugten Wasserstoff und anschließende Methanisierung hergestellt",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiges Gas",
                        "description": "sonstiges Gas",
                    },
                },
                "typename": "XP_GasTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gasDruckstufe: Annotated[
        Literal["1000", "2000", "3000", "9999"] | None,
        Field(
            description="Druckstufe des Gases",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Niederdruck",
                        "alias": "Niederdruck",
                        "description": "Niederdruck",
                    },
                    "2000": {
                        "name": "Mitteldruck",
                        "alias": "Mitteldruck",
                        "description": "Mitteldruck",
                    },
                    "3000": {
                        "name": "Hochdruck",
                        "alias": "Hochdruck",
                        "description": "Hochdruck",
                    },
                    "9999": {
                        "name": "UnbekannterDruck",
                        "alias": "Unbekannter Druck",
                        "description": "Unbekannter Druck",
                    },
                },
                "typename": "XP_GasDruckstufe",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    begrenzung: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Bestimmung der dargestellten Fläche",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Betriebsgelaende",
                        "alias": "Betriebsgelände",
                        "description": "gesamtes Betriebsgelände bzw. Grundstücksfläche",
                    },
                    "2000": {
                        "name": "EingezaeunteFlaeche",
                        "alias": "eingezäunte Fläche",
                        "description": "eingezäuntes Gelände der Infrastrukturgebäude (ohne Parkplätze und Nebengebäude)",
                    },
                    "3000": {
                        "name": "Gebaeudeflaeche",
                        "alias": "Gebäudefläche",
                        "description": "Fläche eines Gebäudes, das technische Anlagen enthält",
                    },
                },
                "typename": "XP_InfrastrukturFlaeche",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class PFSGasversorgungsleitungAbschnitt(PFSLeitung):
    """Abschnitt einer Gasversorgungsleitung ("Pipeline"). Der Begriff der Gasversorgungsleitung umfasst auch Wasserstoffnetze (EnWG § 43l, Abs 1). Der Abschnitt ist Bestandteil der Antrags- oder Vorzugstrasse."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    gasArt: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "2000",
            "20001",
            "20002",
            "20003",
            "20004",
            "3000",
            "4000",
            "5000",
            "6000",
            "9999",
        ],
        Field(
            description="Art des transportierten Gases",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Erdgas",
                        "alias": "Erdgas",
                        "description": "Erdgas",
                    },
                    "10001": {
                        "name": "L_Gas",
                        "alias": "L-Gas",
                        "description": "L-Gas (low calorific gas)",
                    },
                    "10002": {
                        "name": "H_Gas",
                        "alias": "H-Gas",
                        "description": "H-Gas (high calorific gas)",
                    },
                    "2000": {
                        "name": "Wasserstoff",
                        "alias": "Wasserstoff",
                        "description": "Wasserstoff (H2)",
                    },
                    "20001": {
                        "name": "GruenerWasserstoff",
                        "alias": "grüner Wasserstoff",
                        "description": "Durch die Elektrolyse von Wasser hergestellter Wasserstoff unter Verwendung von Strom aus erneuerbaren Energiequellen",
                    },
                    "20002": {
                        "name": "BlauerWasserstoff",
                        "alias": "blauer Wasserstoff",
                        "description": "Grauer Wasserstoff, bei dessen Entstehung das CO2 jedoch teilweise abgeschieden und im Erdboden gespeichert wird (CCS, Carbon Capture and Storage). Maximal 90 Prozent des CO₂ sind speicherbar.",
                    },
                    "20003": {
                        "name": "OrangenerWasserstoff",
                        "alias": "orangener Wasserstoff",
                        "description": "Auf Basis von Abfall und Reststoffen produzierter Wasserstoff, der als CO2-frei gilt",
                    },
                    "20004": {
                        "name": "GrauerWasserstoff",
                        "alias": "grauer Wasserstoff",
                        "description": "Mittels Dampfreformierung meist aus fossilem Erdgas hergestellter Wasserstoff. Dabei entstehen rund 10 Tonnen CO₂ pro Tonne Wasserstoff. Das CO2 wird in die Atmosphäre abgegeben.",
                    },
                    "3000": {
                        "name": "Erdgas_H2_Gemisch",
                        "alias": "Erdgas-Wasserstoff-Gemisch",
                        "description": "Erdgas-Wasserstoff-Gemisch",
                    },
                    "4000": {
                        "name": "Biogas",
                        "alias": "Biogas",
                        "description": "Biogas",
                    },
                    "5000": {
                        "name": "Fluessiggas",
                        "alias": "Flüssiggas",
                        "description": "Flüssiggas",
                    },
                    "6000": {
                        "name": "SynthetischesMethan",
                        "alias": "synthetisch erzeugtes Methan",
                        "description": "Wird durch wasserelektrolytisch erzeugten Wasserstoff und anschließende Methanisierung hergestellt",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiges Gas",
                        "description": "sonstiges Gas",
                    },
                },
                "typename": "XP_GasTyp",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    netzEbene: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "6000", "7000", "8000", "9999"]
        | None,
        Field(
            description="Leitungsart im Gasnetz",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Fernleitung",
                        "alias": "Fernleitung",
                        "description": "Fernleitung gemäß Umweltverträglichkeitsprüfung (UVPG), Anlage 1 und ENWG § 3, Nr. 19d/20; Leitungen der Fernleitungsnetzbetreiber",
                    },
                    "2000": {
                        "name": "Verteilnetzleitung",
                        "alias": "Verteilnetzleitung",
                        "description": "Leitung eines Verteil(er)netzes; Leitungen der Versorgungsunternehmen",
                    },
                    "3000": {
                        "name": "Hauptleitung",
                        "alias": "Hauptleitung",
                        "description": "Hauptleitung, oberste Leitungskategorie in einem Trinkwasser und Wärmenetz",
                    },
                    "4000": {
                        "name": "Versorgungsleitung",
                        "alias": "Versorgungsleitung",
                        "description": "Versorgungsleitung, auch Ortsleitung (z.B Wasserleitungen innerhalb des Versorgungsgebietes im bebauten Bereich)",
                    },
                    "5000": {
                        "name": "Zubringerleitung",
                        "alias": "Zubringerleitung",
                        "description": "Zubringerleitung (z.B. Wasserleitungen zwischen Wassergewinnungs- und Versorgungsgebieten)",
                    },
                    "6000": {
                        "name": "Anschlussleitung",
                        "alias": "Hausanschlussleitung",
                        "description": "Anschlussleitung, Hausanschluss (z.B. Wasserleitungen von der Abzweigstelle der Versorgungsleitung bis zur Übergabestelle/Hauptabsperreinrichtung)",
                    },
                    "7000": {
                        "name": "Verbindungsleitung",
                        "alias": "Verbindungsleitung",
                        "description": "Verbindungsleitung (z.B. Wasserleitungen außerhalb der Versorgungsgebiete, die Versorgungsgebiete (Orte) miteinander verbinden), in der Wärmeversorung auch Transportleitung genannt (die eine Wärmeerzeuugungsinfrastruktur mit einem entfernten Versorgungsgebiet verbindet)",
                    },
                    "8000": {
                        "name": "Strassenablaufleitung",
                        "alias": "Straßenablaufleitung",
                        "description": "Straßenablaufleitung (in der Abwasserentsorgung)",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstige Leitung",
                        "description": "Sonstige Leitung",
                    },
                },
                "typename": "XP_RohrleitungNetz",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    regelueberdeckung: Annotated[
        definitions.Length | None,
        Field(
            description="Mindestabstand zwischen Oberkante des Weges und Oberkante des Rohres in m.\r\n(gml:LengthType: uom=“m“ oder uom=“urn:adv:uom:m“)",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    nennweite: Annotated[
        str | None,
        Field(
            description='Die Nennweite DN ("diamètre nominal", "Durchmesser nach Norm") ist eine numerische Bezeichnung der ungefähren Durchmesser von Bauteilen in einem Rohrleitungssystem, die laut EN ISO 6708 "für Referenzzwecke verwendet wird".',
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    aussendurchmesser: Annotated[
        definitions.Length | None,
        Field(
            description="Außendurchmesser in m\r\n(gml:LengthType: uom=“m“ oder uom=“urn:adv:uom:m“)",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    werkstoff: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "2000",
            "20001",
            "20002",
            "20003",
            "2500",
            "25001",
            "25002",
            "25003",
            "25004",
            "25005",
            "3000",
            "30001",
            "30002",
            "4000",
            "5000",
            "9999",
        ]
        | None,
        Field(
            description="Werkstoff der Leitung",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Kunststoff",
                        "alias": "Kunststoff",
                        "description": "Kunststoff",
                    },
                    "10001": {
                        "name": "Polyethylen_PE",
                        "alias": "Polyethylen ( PE)",
                        "description": "Polyethylen (PE)",
                    },
                    "10002": {
                        "name": "Polyethylen_PE_HD",
                        "alias": "High-Density Polyethylen",
                        "description": "High-Density Polyethylen",
                    },
                    "10003": {
                        "name": "Polypropylen_PP",
                        "alias": "Polypropylen ( PP)",
                        "description": "Polypropylen (PP)",
                    },
                    "10004": {
                        "name": "Polycarbonat_PC",
                        "alias": "Polycarbonat ( PC)",
                        "description": "Polycarbonat (PC)",
                    },
                    "10005": {
                        "name": "Polyvinylchlorid_PVC_U",
                        "alias": "Polyvinylchlorid ( PVC- U)",
                        "description": "Polyvinylchlorid (PVC-U)",
                    },
                    "2000": {"name": "Stahl", "alias": "Stahl", "description": "Stahl"},
                    "20001": {
                        "name": "StahlVerzinkt",
                        "alias": "Stahl verzinkt",
                        "description": "Stahl verzinkt",
                    },
                    "20002": {
                        "name": "Stahlgitter",
                        "alias": "Stahlgitter",
                        "description": "Stahlfachwerkskonstruktion (z.B. Freileitungsmast als Gittermast)",
                    },
                    "20003": {
                        "name": "Stahlrohr",
                        "alias": "Stahlrohr",
                        "description": "Rohrförmiger Profilstahl, dessen Wand aus Stahl besteht. Stahlrohre dienen der Durchleitung von flüssigen, gasförmigen oder festen Stoffen, oder werden als statische oder konstruktive Elemente verwendet (z.B. Freileitungsmast als Stahlrohrmast)",
                    },
                    "2500": {
                        "name": "Stahlverbundrohr",
                        "alias": "Stahlverbundrohr",
                        "description": "Stahlverbundrohre im Rohrleitungsbau",
                    },
                    "25001": {
                        "name": "St_PE",
                        "alias": "Stahlrohr mit Standard-Kunststoffumhüllung (PE)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PE-Basis",
                    },
                    "25002": {
                        "name": "St_PP",
                        "alias": "Stahlrohr mit Kunstoffumhüllung (PP)",
                        "description": "Stahlrohr mit  Kunststoffumhüllung auf PP-Basis für höhere Temperatur- und Härte-Anforderungen",
                    },
                    "25003": {
                        "name": "St_FZM",
                        "alias": "Stahlrohr mit FZM-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz durch Faserzementmörtel-Ummantelung (FZM)",
                    },
                    "25004": {
                        "name": "St_GFK",
                        "alias": "Stahlrohr mit GFK-Ummantelung",
                        "description": "Stahlrohr mit mit Kunststoff-Umhüllung und zusätzlichem Außenschutz aus glasfaserverstärktem Kunststoff (GFK) für höchste mechanische Abriebfestigkeit bei grabenlosem Rohrvortrieb",
                    },
                    "25005": {
                        "name": "St_ZM_PE",
                        "alias": "Stahl-Verbundrohr (ZM-PE)",
                        "description": "Stahlrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserohr)",
                    },
                    "3000": {
                        "name": "Gusseisen",
                        "alias": "Gusseisen",
                        "description": "Gusseisen",
                    },
                    "30001": {
                        "name": "GGG_ZM",
                        "alias": "duktiles Gussrohr mit ZM-Auskleidung",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung (z.B Abwasserrohr)",
                    },
                    "30002": {
                        "name": "GGG_ZM_PE",
                        "alias": "duktiles Guss-Verbundrohr (ZM-PE)",
                        "description": "duktiles Gussrohr mit Zementmörtelauskleidung und PE-Außenschutz (z.B. Abwasserrohr)",
                    },
                    "4000": {
                        "name": "Beton",
                        "alias": "Beton",
                        "description": "Beton (z.B. Schacht)",
                    },
                    "5000": {
                        "name": "Holz",
                        "alias": "Holz",
                        "description": "Holz (z.B. Holzmast)",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiger Werkstoff",
                        "description": "Sonstiger Werkstoff",
                    },
                },
                "typename": "XP_Werkstoff",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    rohrgraben: Annotated[
        PFSRohrgraben | None,
        Field(
            description="Rohrgraben zur Verlegung der Leitung in offener Bauweise",
            json_schema_extra={
                "typename": "PFS_Rohrgraben",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class PFSGleis(PFSMultiVerkehrsweg):
    """Fahrbahn von schienengebundenen Fahrzeugen. Schienen, Schwellen, Befestigungsmittel und Schotterbett bilden den Gleiskörper und sind dem Begriff Oberbau zugeordnet. Dämme, An- und Einschnitte sowie Brücken gehören zum Unterbau."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class PFSHochspannungsleitungAbschnitt(PFSLeitung):
    """Abschnitt einer ober- oder unterirdischen Hochspannungsleitung (Stromleitung zur Übertragung von elektrischer Energie über große Distanzen). Der Abschnitt ist Bestandteil der Antrags- oder Vorzugstrasse."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    spannung: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Spannung in Kilovolt",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "110_kV",
                        "alias": "110 kV",
                        "description": "Hochspannung 110 Kilovolt",
                    },
                    "2000": {
                        "name": "220_kV",
                        "alias": "220 kV",
                        "description": "Höchstspannung 220 Kilovolt",
                    },
                    "3000": {
                        "name": "380_kV",
                        "alias": "380 kV",
                        "description": "Höchstspannung 380 Kilovolt",
                    },
                },
                "typename": "PFS_Hochspannung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    erdkabel: Annotated[
        PFSErdkabel | None,
        Field(
            description="Leitungsabschnitt als Erdkabel ( XP_Leitungstyp = Erdkabel)",
            json_schema_extra={
                "typename": "PFS_Erdkabel",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class PFSHochspannungsmast(PFSMultiPunktobjekt):
    """Freileitungsmast eines Hochspannungsnetzes"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"] | None,
        Field(
            description='Art des Hochspannungsmast ("Mastbild")',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Einebenenmast",
                        "alias": "Einebenenmast",
                        "description": "Beim Einebenmast sind die Leiterseile in einer horizontalen Linie angeordnet und hängen in einer Ebene. Hierdurch ergeben sich die geringsten Masthöhen",
                    },
                    "2000": {
                        "name": "Donaumast",
                        "alias": "Donaumast",
                        "description": "Der Donaumast hat zwei Traversen, in der Regel ist die breitere Traverse mit je zwei Leiterseilen unten, die schmalere mit einem Leiterseil oben. \r\nDas Donau-Mastbild ist in der 380-kV-Spannungsebene die am häufigsten verwendete Mastbauform.",
                    },
                    "3000": {
                        "name": "Tonnenmast",
                        "alias": "Tonnenmast",
                        "description": "Beim Tonnenmast  sind die Leiterseile auf drei Traversen übereinander  angeordnet. Dies ergibt die geringstmögliche Ausladung und somit die geringste dauerhafte Flächeninanspruchnahme (Schutzbereich).",
                    },
                    "4000": {
                        "name": "Kompaktmast",
                        "alias": "Kompaktmast",
                        "description": "Maste mit einer sehr kompakten Bauform werden als Kompaktmaste oder Vollwandmast bezeichnet",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstige Masten",
                        "description": "Sonstige Masten",
                    },
                },
                "typename": "PFS_MastTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    hoehe: Annotated[
        definitions.Length | None,
        Field(
            description="Höhe in Metern",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    traversenbreite: Annotated[
        definitions.Length | None,
        Field(
            description="Maximale Gesamtbreite der Traversen",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None


class PFSKanal(PFSMultiVerkehrsweg):
    """Wasserstraße mit künstlich hergestelltem Gewässerbett"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class PFSKraftwerk(PFSMultiFlaechenobjekt):
    """Technische Anlage, in der durch Energieumwandlung Elektrizität erzeugt wird. In der Kraft-Wärme-Kopplung wird zusätzlich thermische Energie bereitgestellt."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"] | None,
        Field(
            description="Art des Kraftwerks",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "ThermischeTurbine",
                        "alias": "Thermisch arbeitende Turbine",
                        "description": "Thermische arbeitende Dampfturbinen- und Gasturbinen-Kraftwerke oder Gas-und-Dampf-Kombikraftwerke",
                    },
                    "2000": {
                        "name": "Windkraft",
                        "alias": "Windkraftanlage",
                        "description": "Eine Windkraftanlage (WKA) oder Windenergieanlage (WEA) wandelt Bewegungsenergie des Windes in elektrische Energie um und speist sie in ein Stromnetz ein. Sie werden an Land (onshore) und in Offshore-Windparks im Küstenvorfeld der Meere installiert. Eine Gruppe von Windkraftanlagen wird Windpark genannt.",
                    },
                    "3000": {
                        "name": "Photovoltaik",
                        "alias": "Photovoltaik-Freinflächenanlage",
                        "description": "Eine Photovoltaikanlage, auch PV-Anlage (bzw. PVA) wandelt mittels Solarzellen ein Teil der Sonnenstrahlung in elektrische Energie um.  Die Photovoltaik-Freiflächenanlage (auch Solarpark) wird auf einer freien Fläche als fest montiertes System aufgestellt, bei dem mittels einer Unterkonstruktion die Photovoltaikmodule in einem optimalen Winkel zur Sonne (Azimut) ausgerichtet sind.",
                    },
                    "4000": {
                        "name": "Wasserkraft",
                        "alias": "Wasserkraftwerk",
                        "description": "Ein Wasserkraftwerk wandelt die potentielle Energie des Wassers in der Regel über Turbinen in mechanische bzw. elektrische Energie um. Dies kann an Fließgewässern oder Stauseen erfolgen oder durch Strömungs- und Gezeitenkraftwerke auf dem Meer (Pumpspeicherkraftwerke s. PFS_Energiespeicheer)",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiges Kraftwerk",
                        "description": "Sonstiges Kraftwerk",
                    },
                },
                "typename": "XP_KraftwerkTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    primaerenergie: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"] | None,
        Field(
            description="Energieträger, der in Gas- und Dampfturbinenkraftwerken in Sekundärenergie gewandelt wird",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "FossilerBrennstoff",
                        "alias": "fossiler Brennstoff",
                        "description": "Fossile Energie wird aus Brennstoffen gewonnen, die in geologischer Vorzeit aus Abbauprodukten von toten Pflanzen und Tieren entstanden sind. Dazu gehören Braunkohle, Steinkohle, Torf, Erdgas und Erdöl.",
                    },
                    "2000": {
                        "name": "Ersatzbrennstoff",
                        "alias": "Ersatzbrennstoff",
                        "description": "Ersatzbrennstoffe (EBS) bzw. Sekundärbrennstoffe (SBS) sind Brennstoffe, die aus Abfällen gewonnen werden. Dabei kann es sich sowohl um feste, flüssige oder gasförmige Abfälle aus Haushalten, Industrie oder Gewerbe handeln.",
                    },
                    "3000": {
                        "name": "Biomasse",
                        "alias": "Biomasse",
                        "description": "Der energietechnische Biomasse-Begriff umfasst tierische und pflanzliche Erzeugnisse, die zur Gewinnung von Heizenergie, von elektrischer Energie und als Kraftstoffe verwendet werden können (u.a. Holzpellets, Hackschnitzel, Stroh, Getreide, Altholz, Biogas). Energietechnisch relevante Biomasse kann in gasförmiger, flüssiger und fester Form vorliegen.",
                    },
                    "4000": {
                        "name": "Erdwaerme",
                        "alias": "Erdwärme",
                        "description": "Geothermie bezeichnet die in den oberen Schichten der Erdkruste gespeicherte Wärme und deren Ausbeutung zur Wärme- oder Stromerzeugung. In der Energiegewinnung wird zwischen tiefer und oberflächennaher Geothermie unterschieden. Die tiefe Geothermie wird von Kraftwerken zur Stromerzeugung genutzt.",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiger Energieträger",
                        "description": "Sonstige Energieträger",
                    },
                },
                "typename": "XP_PrimaerenergieTraeger",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    kraftWaermeKopplung: Annotated[
        bool | None,
        Field(
            description="Kraft-Wärme-Kopplung (KWK) ist die gleichzeitige Gewinnung von mechanischer Energie und nutzbarer Wärme, die in einem gemeinsamen thermodynamischen Prozess entstehen. Die mechanische Energie wird in der Regel unmittelbar in elektrischen Strom umgewandelt. Die Wärme wird für Heizzwecke als Nah- oder Fernwärme oder für Produktionsprozesse als Prozesswärme genutzt.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    begrenzung: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Bestimmung der dargestellten Fläche",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Betriebsgelaende",
                        "alias": "Betriebsgelände",
                        "description": "gesamtes Betriebsgelände bzw. Grundstücksfläche",
                    },
                    "2000": {
                        "name": "EingezaeunteFlaeche",
                        "alias": "eingezäunte Fläche",
                        "description": "eingezäuntes Gelände der Infrastrukturgebäude (ohne Parkplätze und Nebengebäude)",
                    },
                    "3000": {
                        "name": "Gebaeudeflaeche",
                        "alias": "Gebäudefläche",
                        "description": "Fläche eines Gebäudes, das technische Anlagen enthält",
                    },
                },
                "typename": "XP_InfrastrukturFlaeche",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class PFSMesspfahl(PFSMultiPunktobjekt):
    """Messstellen zur Überwachung des Korrosionsschutzsystems entlang der Rohrleitung, idR. Schilderpfahl mit Messkontakt (SMK)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class RVPEngstelle(RVPMultiPunktobjekt):
    """Ein Konfliktbereich ist gekennzeichnet durch das Auftreten unterschiedlich ausgeprägter planerischer und technischer Hemmnisse in den entwickelten Trassenkorridoren.
    Der Konfliktbereich kann auch als Riegel auftreten. Die Abgrenzung zwischen Riegel und Engstelle muss jeweils definiert werden, z.B.
    Engstelle: verbleibender Trassierungsraum liegt zwischen dem 1- bis 2-fachen der Regelbaubreite.
    Riegel: verbleibender Trassierungsraum ist schmaler als die Regelbaubreite.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        Literal["1000", "2000", "9999"] | None,
        Field(
            description="Art des Hemmnis bzw. Konflikts",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "PlanerischesHemmnis",
                        "alias": "planerisches Hemmnis",
                        "description": "Planerische Hemmnisse beziehen sich auf Planungen und Gebietsausweisungen, von denen hohe Raumwiderstände ausgehen",
                    },
                    "2000": {
                        "name": "TechnischesHemmnis",
                        "alias": "technisches Hemmnis",
                        "description": "Technische Hemmnisse sind Verkehrs- und Leitungsinfrastrukturen, die über- bzw. unterquert werden müssen.  Hinzu kommen sog. sonstige technische Hemmnisse, z. B. durch die Nähe einer Leitung zu Energieinfrastrukturen, die den Einbau von Schutzmaßnahmen erforderlich machen",
                    },
                    "9999": {
                        "name": "SonstigesHemmnis",
                        "alias": "sonstiges Hemmnis",
                        "description": "sonstiges Hemmnis",
                    },
                },
                "typename": "RVP_HemmnisTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    bewertung: Annotated[
        Literal["1000", "2000", "3000", "4000"] | None,
        Field(
            description="Bewertung ob Engstelle/Riegel überwunden bzw. passiert werden kann",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Ueberwindbar",
                        "alias": "überwindbar",
                        "description": "Überwindbar in offener Regelbauweise ohne besondere Vorkehrungen",
                    },
                    "2000": {
                        "name": "BedingtUeberwindbar",
                        "alias": "bedingt überwindbar",
                        "description": "bedingt überwindbar =  überwindbar unter Berücksichtigung von zusätzlichen Vorkehrungen / Maßnahmen, auch bautechnischer Art",
                    },
                    "3000": {
                        "name": "SchwerUeberwindbar",
                        "alias": "schwer überwindbar",
                        "description": "schwer überwindbar = überwindbar unter Berücksichtigung von aufwendigen zusätzlichen Vorkehrungen/Maßnahmen, auch bautechnischer Art",
                    },
                    "4000": {
                        "name": "NichtUeberwindbar",
                        "alias": "nicht überwindbar",
                        "description": "nicht überwindbar = nicht überwindbar aus rechtlichen und/oder bautechnischen Gründen auch unter Abwägung zusätzlicher Vorkehrungen/Maßnahmen",
                    },
                },
                "typename": "RVP_BewertungEngstelleRiegel",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class RVPGrobkorridor(RVPMultiFlaechenobjekt):
    """Die Grobkorridorfindung leitet von der Darstellung der Netzverknüpfungspunkte zu den konkreten Trassenkorridoren über. Es sollen großräumige Raumwiderstände identifiziert und relativ konfliktarme Bereiche für Trassenkorridore ermittelt werden. Dieser methodische Schritt ermöglicht eine Entscheidung über die Größe des Suchraums für das Auffinden und die Auswahl in Betracht kommender Trassenkorridore."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"


class RVPKonfliktRaumordnung(RVPMultiFlaechenobjekt):
    """Kategorien der Bundesfachplanung/BNetzA zur Raumverträglichkeitsstudie"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    restriktionsniveau: Annotated[
        Literal["1000", "2000", "3000", "4000"] | None,
        Field(
            description="Das allgemeine Restriktionsniveau ist als Basis einer vorhabenübergreifenden Methode zur Raumverträglichkeitsstudie in der Bundesfachplanung zu sehen, da es für die gängigen raumordnerischen Festlegungen eine planunabhängige Einstufung vornimmt. Das Restriktionsniveau beschreibt im gesamtplanerischen Kontext den Stellenwert der relevanten Erfordernisse der Raumordnung gegenüber dem Neubau einer Höchstspannungsleitung. \r\nDas spezifische Restriktionsniveau kann sich aus dem allgemeinen ableiten. Zusätzlich werden hier jedoch die relevanten Pläne und Programme in ihren konkreten textlichen Festlegungen und Begründungen ausgewertet.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "SehrHoch",
                        "alias": "sehr hoch",
                        "description": "sehr hoch",
                    },
                    "2000": {"name": "Hoch", "alias": "hoch", "description": "hoch"},
                    "3000": {
                        "name": "Mittel",
                        "alias": "mittel",
                        "description": "mittel",
                    },
                    "4000": {
                        "name": "Gering",
                        "alias": "gering",
                        "description": "gering",
                    },
                },
                "typename": "RVP_BewertungSkala",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    konfliktpotenzial: Annotated[
        Literal["1000", "2000", "3000", "4000"] | None,
        Field(
            description="Das Konfliktpotenzial beschreibt den Grad der Vereinbarkeit eines Vorhabens mit einer (flächenhaften) raumordnerischen Festlegung, die bei Durchführung einer konkreten Ausbauform zu erwarten ist. Das Konfliktpotenzial setzt sich zusammen aus den Auswirkungen des Vorhabens auf die raumordnerischen Festlegungen sowie deren Stellenwert (sachliche Bestimmtheit/ Kategorie nach § 3 Abs. 1 ROG) im planerischen Gesamtkontext.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "SehrHoch",
                        "alias": "sehr hoch",
                        "description": "sehr hoch",
                    },
                    "2000": {"name": "Hoch", "alias": "hoch", "description": "hoch"},
                    "3000": {
                        "name": "Mittel",
                        "alias": "mittel",
                        "description": "mittel",
                    },
                    "4000": {
                        "name": "Gering",
                        "alias": "gering",
                        "description": "gering",
                    },
                },
                "typename": "RVP_BewertungSkala",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    konformitaet: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Bewertung der Konformität mit den Erfordernissen der Raumordnung, basierend auf dem spezifischen Restriktionsniveau und dem ermittelten Konfliktpotenzial",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Gegeben",
                        "alias": "gegeben",
                        "description": "Konformität ist gegeben",
                    },
                    "2000": {
                        "name": "KannErreichtWerden",
                        "alias": "kann erreicht werden",
                        "description": "Konformität kann errreicht werden",
                    },
                    "3000": {
                        "name": "KannNichtErreichtWerden",
                        "alias": "kann nicht erreicht werden",
                        "description": "Konformität kann nicht erreicht werden",
                    },
                },
                "typename": "RVP_BewertungKonformitaet",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    externeReferenz: Annotated[
        XPNetzExterneReferenz | None,
        Field(
            description="Referenz auf ein Dokument der Raumwiderstandsanalyse",
            json_schema_extra={
                "typename": "XP_NetzExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class RVPLinienkorridorSegment(RVPMultiLinienobjekt):
    """Zu Planungsbeginn können Linienkorridorsegmente und ihre Alternativen einen netzartigen Verlauf darstellen ("Korridornetz"). Korridorsegmente werden zu Strängen oder Varianten zusammengesetzt (s. Attribut "artSegment"). Wenn einzelne Segmente Bestandteil verschiedener Varianten sind, kann zusätzlich das Attritbut "korridorVariante" belegt werden.
    Vollständige Linienkorridore können alternativ dazu über die Klasse RVP_Linienkorridor abgebildet werden.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xtrasse.de/2.0"
    stereotype: ClassVar[str] = "FeatureType"
    artKorridor: Annotated[
        Literal["1000", "10001", "10002", "10003", "2000", "20001", "20002", "9999"]
        | None,
        Field(
            description='Art des Korridors, dem das Segegment zugewiesen wird. Bei Mehrfachbelegung in verschiedenen Varianten kann das Attribut "korridorVariante" genutzt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Antragskorridor",
                        "alias": "Antragskorridor",
                        "description": "Trassenkorridor als Ergebnis des Verfahrens (auch Antragsvariante). Der Antragskorridor kann sich aus mehreren Segmenten zusammensetzen.",
                    },
                    "10001": {
                        "name": "FestgelegterTrassenkorridor",
                        "alias": "festgelegter Trassenkorridor",
                        "description": "Festgelegter Trassenkorridor",
                    },
                    "10002": {
                        "name": "BevorzugterTrassenkorridor",
                        "alias": "präferierter Trassenkorridor",
                        "description": "Bevorzugter Trassenkorridor (auch präferierter oder Vorschlagstrassenkorridor)",
                    },
                    "10003": {
                        "name": "VorgeschlagenerTrassenkorridor",
                        "alias": "vorgeschlagener Trassenkorridor",
                        "description": "Vorgeschlagener Trassenkorridor / Vorschlags(trassen)korridor / Trassenkorridorvorschlag",
                    },
                    "2000": {
                        "name": "Variantenkorridor",
                        "alias": "Variantenkorridor",
                        "description": "Variante eines Trassenkorridors bei mehreren möglichen Trassenverläufen. Die jeweilige Varianten kann aus mehreren Segmenten bestehen.",
                    },
                    "20001": {
                        "name": "AlternativerTrassenkorridor",
                        "alias": "Alternativer Trassenkorridor",
                        "description": "Ernsthaft zu berücksichtigende bzw. in Frage kommende Alternative (im Vergleich zum Antragskorridor)",
                    },
                    "20002": {
                        "name": "PotenziellerTrassenkorridor",
                        "alias": "potenzieller Trassenkorridor",
                        "description": "Potenzieller Trassenkorridor",
                    },
                    "9999": {
                        "name": "SonstigerKorridor",
                        "alias": "sonstiger Korridor",
                        "description": "sonstiger Korridor",
                    },
                },
                "typename": "RVP_KorridorTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    artSegment: Annotated[
        Literal["1000", "2000", "3000", "9999"] | None,
        Field(
            description="Art des Korridorsegments",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "AlternativesKorridorsegment",
                        "alias": "alternatives Korridorsegment",
                        "description": "Alternatives Trassenkorridorsegment (auch Korridoralternative) bei Analyse und Darstellung eines Korridornetzes",
                    },
                    "2000": {
                        "name": "VerworfenesKorridorsegment",
                        "alias": "verworfenes Korridorsegment",
                        "description": "Korridorsegment, das im Rahmen einer (Raumwiderstands-)Analyse ausgeschlossen oder nicht weiter betrachtet wird",
                    },
                    "3000": {
                        "name": "RueckbauBestandsleitung",
                        "alias": "Rückbau Bestandsleitung",
                        "description": "Korridorsegment, in dem der Rückbau einer Bestandsleitung erfolgt",
                    },
                    "9999": {
                        "name": "SonstigesKorridorsegment",
                        "alias": "sonstiges Korridorsegment",
                        "description": "sonstiges Korridorsegment",
                    },
                },
                "typename": "RVP_KorridorSegmentTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    status: Annotated[
        Literal["1000", "2000", "3000", "4000"] | None,
        Field(
            description="Planungsstatus des Korridorsegments",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "InBearbeitung",
                        "alias": "in Bearbeitung",
                        "description": "Trassenkorridor ist Bestandteil einer laufenden Raumverträglichkeitsprüfung oder einer Rauwiderstandsanalyse",
                    },
                    "2000": {
                        "name": "ErgebnisRVP",
                        "alias": "Ergebnis der Raumverträglichkeitsprüfung",
                        "description": "Trassenkorridor ist das Ergebnis der Räumverträglichkeitsprüfung",
                    },
                    "3000": {
                        "name": "LandesplanerischeFeststellung",
                        "alias": "Landesplanerische Festlegung",
                        "description": "Abschluss der Raumverträglichkeitsprüfung durch landesplanerische Feststellung",
                    },
                    "4000": {
                        "name": "Bestand",
                        "alias": "Bestandskorridor",
                        "description": "Trassenkorrior um Bestandsleitungen",
                    },
                },
                "typename": "RVP_KorridorStatus",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    breite: Annotated[
        definitions.Length | None,
        Field(
            description="Breite des Trassenkorridors in Metern.\r\n(gml:LengthType: uom=“m“ oder uom=“urn:adv:uom:m“)",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    bewertung: Annotated[
        str | None,
        Field(
            description="Bewertung im Rahmen eines Vergleichs von Trassenverläufen",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    korridorVariante: Annotated[
        list[str] | None,
        Field(
            description="Wenn Korridorsegmente Bestandteil verschiedener Varianten sind, werden diese hier benannt",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
