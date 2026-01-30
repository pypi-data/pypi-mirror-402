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
            description="Anwendungsschema XWärmeplan",
            json_schema_extra={
                "full_name": "XWärmeplan",
                "prefix": "xwp",
                "full_version": "0.9",
                "namespace_uri": "http://www.xwaermeplan.de/0/9",
            },
        ),
    ]


class WPBereich(BaseFeature):
    """Diese Klasse modelliert einen Bereich eines Wärmeplans, z.B. einen räumlichen oder sachlichen Teilbereich. Im Fall eines gemeinsamen Wärmeplans dienen Bereiche der gesonderten Darstellung der Ergebnisse für jede Gemeinde. Bei einer getrennten Darstellung einer gemeinsam durchgeführten Planung können die Gemeindeflächen der Partner als Bereiche vermerkt werden."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    id: str | None = None
    nummer: Annotated[
        int,
        Field(
            description="Nummer des Bereichs. Bereichsnummern beginnen standardmäßig mit 0 und sollten, wenn einem Planobjekt mehrere Bereichsobjekte zugeordnet sind, eindeutig sein.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    name: Annotated[
        str | None,
        Field(
            description="Bezeichnung des Bereiches",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    bedeutung: Annotated[
        str | None,
        Field(
            description="Detaillierte Erklärung der semantischen Bedeutung eines Bereiches",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    geltungsbereich: Annotated[
        definitions.MultiPolygon | None,
        Field(
            description="Räumliche Abgrenzung des Bereiches.",
            json_schema_extra={
                "typename": "GM_MultiSurface",
                "stereotype": "Geometry",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gehoertZuPlan: Annotated[
        AnyUrl | UUID,
        Field(
            description="Referenz eines Bereichs auf den zugehörigen Plan",
            json_schema_extra={
                "typename": "WP_Plan",
                "stereotype": "Association",
                "reverseProperty": "bereich",
                "sourceOrTarget": "source",
                "multiplicity": "1",
            },
        ),
    ]
    planinhalt: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            description="Verweis auf einen raumbezogenen Planinhalt des Bereichs",
            json_schema_extra={
                "typename": [
                    "WP_AbwasserNetzAbschnitt",
                    "WP_AnschlussGruenesMethan",
                    "WP_Anschlusszwang",
                    "WP_Ausschlussgebiet",
                    "WP_DezentraleErzeugung",
                    "WP_Eignungspruefung",
                    "WP_EnergieEinspargebiet",
                    "WP_GasErzeugung",
                    "WP_GasNetzBaublock",
                    "WP_GasSpeicher",
                    "WP_GebaeudeBaublock",
                    "WP_Grossverbraucher",
                    "WP_NichtBeplantesTeilgebiet",
                    "WP_PotenzialEnergieEinsparung",
                    "WP_PotenzialWaermeNutzung",
                    "WP_PotenzialWaermeSpeicherung",
                    "WP_WaermeNetzAbschnitt",
                    "WP_WaermeSpeicher",
                    "WP_Waermeerzeugungsanlage",
                    "WP_Waermeliniendichte",
                    "WP_Waermeverbrauch",
                    "WP_WaermeversorgungsartZieljahr",
                    "WP_Waermeversorgungsgebiet2030",
                    "WP_Waermeversorgungsgebiet2035",
                    "WP_Waermeversorgungsgebiet2040",
                    "WP_WaermeversorgungsgebietZieljahr",
                ],
                "stereotype": "Association",
                "reverseProperty": "gehoertZuBereich",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            },
        ),
    ] = None


class WPEnergieTraegerMenge(BaseFeature):
    """Datentyp Energieträger mit Angabe zum Endenergieverbrauch oder Potenzial zur Wärmeerzeugung"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "DataType"
    traeger: Annotated[
        Literal[
            "1100",
            "11001",
            "11002",
            "1200",
            "12001",
            "12002",
            "12003",
            "1300",
            "13001",
            "13002",
            "2000",
            "20001",
            "20002",
            "3100",
            "31001",
            "31002",
            "3200",
            "32001",
            "32002",
            "32003",
            "32004",
            "4000",
            "40001",
            "40002",
            "40003",
            "40004",
            "4100",
            "5000",
            "6000",
            "7100",
            "7200",
            "72001",
            "72002",
            "7300",
            "73001",
            "73002",
            "73003",
            "73004",
            "73005",
            "9999",
        ],
        Field(
            description="Energieträger",
            json_schema_extra={
                "enumDescription": {
                    "1100": {
                        "name": "Kohle",
                        "alias": "Kohle",
                        "description": "Kohle (Oberkategorie)",
                    },
                    "11001": {
                        "name": "Braunkohle",
                        "alias": "Braunkohle",
                        "description": "Braunkohle",
                    },
                    "11002": {
                        "name": "Steinkohle",
                        "alias": "Steinkohle",
                        "description": "Steinkohle",
                    },
                    "1200": {
                        "name": "FossilesGas",
                        "alias": "Fossiles Gas",
                        "description": "Fossiles Gas (Oberkategorie)",
                    },
                    "12001": {
                        "name": "Erdgas",
                        "alias": "Erdgas",
                        "description": "Erdgas",
                    },
                    "12002": {
                        "name": "Fluessiggas",
                        "alias": "Flüssiggas",
                        "description": "Flüssiggas",
                    },
                    "12003": {
                        "name": "Grubengas",
                        "alias": "Grubengas",
                        "description": "Grubengas",
                    },
                    "1300": {
                        "name": "Mineraloelprodukte",
                        "alias": "Mineralölprodukte",
                        "description": "Mineralölprodukte (Oberkategorie)",
                    },
                    "13001": {
                        "name": "Heizoel",
                        "alias": "Heizöl",
                        "description": "Heizöl",
                    },
                    "13002": {
                        "name": "Dieselkraftstoff",
                        "alias": "Dieselkraftstoff",
                        "description": "Dieselkraftstoff",
                    },
                    "2000": {
                        "name": "Abfall",
                        "alias": "Abfall",
                        "description": "Abfall (Oberkategorie)",
                    },
                    "20001": {
                        "name": "NichtBiogenerAbfall",
                        "alias": "nicht biogener Abfall",
                        "description": "Nicht biogener Abfall",
                    },
                    "20002": {
                        "name": "BiogenerAbfall",
                        "alias": "biogener Abfall",
                        "description": "Biogener Abfall",
                    },
                    "3100": {
                        "name": "Biomasse",
                        "alias": "Biomasse",
                        "description": "Biomasse (Oberkategorie)",
                    },
                    "31001": {
                        "name": "FesteBiomasse",
                        "alias": "feste Biomasse",
                        "description": "Feste Biomasse",
                    },
                    "31002": {
                        "name": "FluessigeBiomasse",
                        "alias": "flüssige Biomasse",
                        "description": "Flüssige Biomasse",
                    },
                    "3200": {
                        "name": "GasfoermigeBiomasse",
                        "alias": "gasförmige Biomasse",
                        "description": "Gasförmige Biomasse (Oberkategorie)",
                    },
                    "32001": {
                        "name": "Biogas",
                        "alias": "Biogas",
                        "description": "Biogas",
                    },
                    "32002": {
                        "name": "Biomethan",
                        "alias": "Biomethan",
                        "description": "Biomethan",
                    },
                    "32003": {
                        "name": "Klaergas",
                        "alias": "Klärgas",
                        "description": "Klärgas",
                    },
                    "32004": {
                        "name": "Deponiegas",
                        "alias": "Deponiegas",
                        "description": "Deponiegas",
                    },
                    "4000": {
                        "name": "Wasserstoff",
                        "alias": "Wasserstoff",
                        "description": "Wasserstoff (H2) (Oberkategorie)",
                    },
                    "40001": {
                        "name": "GruenerWasserstoff",
                        "alias": "grüner Wasserstoff",
                        "description": "Durch die Elektrolyse von Wasser hergestellter Wasserstoff unter Verwendung von Strom aus erneuerbaren Energiequellen",
                    },
                    "40002": {
                        "name": "BlauerWasserstoff",
                        "alias": "blauer Wasserstoff",
                        "description": "Wasserstoff aus der Reformierung von Erdgas, dessen Erzeugung mit einem Kohlenstoffdioxid-Abscheidungsverfahren und Kohlenstoffdioxid-Speicherungsverfahren gekoppelt wird",
                    },
                    "40003": {
                        "name": "OrangenerWasserstoff",
                        "alias": "orangener Wasserstoff",
                        "description": "Wasserstoff, der aus Biomasse oder unter Verwendung von Strom aus Anlagen der Abfallwirtschaft hergestellt wird",
                    },
                    "40004": {
                        "name": "TuerkiserWasserstoff",
                        "alias": "türkiser Wasserstoff",
                        "description": "Wasserstoff, der über die Pyrolyse von Erdgas hergestellt wird",
                    },
                    "4100": {
                        "name": "Wasserstoffderivate",
                        "alias": "Wasserstoffderivate",
                        "description": "Wasserstoffderivate, z.B. grünes Methan. Der aus Ökostrom erzeugte grüne Wasserstoff wird mit CO2 zu Methan gewandelt.",
                    },
                    "5000": {
                        "name": "UnvermeidbareAbwaerme",
                        "alias": "unvermeidbare Abwärme",
                        "description": "Unvermeidbare Abwärme",
                    },
                    "6000": {"name": "Strom", "alias": "Strom", "description": "Strom"},
                    "7100": {
                        "name": "Solarthermie",
                        "alias": "Solarthermie",
                        "description": "Solarthermie",
                    },
                    "7200": {
                        "name": "Geothermie",
                        "alias": "Geothermie",
                        "description": "Dem Erdboden entnommene Wärme (Oberkategorie)",
                    },
                    "72001": {
                        "name": "OberflaechennaheGeothermie",
                        "alias": "Oberflächennahe Geothermie",
                        "description": "Oberflächennahe Geothermie",
                    },
                    "72002": {
                        "name": "TiefeGeothermie",
                        "alias": "Tiefe Geothermie",
                        "description": "Tiefe Geothermie",
                    },
                    "7300": {
                        "name": "Umweltwaerme",
                        "alias": "Umweltwärme",
                        "description": "Umweltwärme (Oberkategorie)",
                    },
                    "73001": {
                        "name": "Grundwasser",
                        "alias": "Grundwasser",
                        "description": "Umweltwärme aus Grundwasser",
                    },
                    "73002": {
                        "name": "Oberflaechengewaesser",
                        "alias": "Oberflächengewässer",
                        "description": "Umweltwärme aus Oberflächengewässern",
                    },
                    "73003": {
                        "name": "Grubenwasser",
                        "alias": "Grubenwasser",
                        "description": "Umweltwärme aus Grubenwasser",
                    },
                    "73004": {
                        "name": "Luft",
                        "alias": "Luft",
                        "description": "Umweltwärme aus Luft",
                    },
                    "73005": {
                        "name": "Abwasser",
                        "alias": "Abwasser",
                        "description": "Umweltwärme aus Abwasser",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "Sonstiges",
                        "description": "Sonstiges",
                    },
                },
                "typename": "WP_EnergieTraeger",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    energieMenge: Annotated[
        definitions.GenericMeasure,
        Field(
            description="Innerhalb eines Jahres verbrauchte oder erzeugbare Wärmeenergie in MWh",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "1",
                "uom": "MWh/a",
            },
        ),
    ]


class WPEnergieTraegerVerbrauch(BaseFeature):
    """Datentyp für die Erfassung von Endenergieverbräuchen nach Energieträgern. Werden aggregierte Daten für das Plangebiet eingetragen, ist die Angabe von Endenergieverbräuchen nach Energieträgern je Sektor möglich."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "DataType"
    traeger: Annotated[
        Literal[
            "1100",
            "11001",
            "11002",
            "1200",
            "12001",
            "12002",
            "12003",
            "1300",
            "13001",
            "13002",
            "2000",
            "20001",
            "20002",
            "3100",
            "31001",
            "31002",
            "3200",
            "32001",
            "32002",
            "32003",
            "32004",
            "4000",
            "40001",
            "40002",
            "40003",
            "40004",
            "4100",
            "5000",
            "6000",
            "7100",
            "7200",
            "72001",
            "72002",
            "7300",
            "73001",
            "73002",
            "73003",
            "73004",
            "73005",
            "9999",
        ],
        Field(
            description="Energieträger",
            json_schema_extra={
                "enumDescription": {
                    "1100": {
                        "name": "Kohle",
                        "alias": "Kohle",
                        "description": "Kohle (Oberkategorie)",
                    },
                    "11001": {
                        "name": "Braunkohle",
                        "alias": "Braunkohle",
                        "description": "Braunkohle",
                    },
                    "11002": {
                        "name": "Steinkohle",
                        "alias": "Steinkohle",
                        "description": "Steinkohle",
                    },
                    "1200": {
                        "name": "FossilesGas",
                        "alias": "Fossiles Gas",
                        "description": "Fossiles Gas (Oberkategorie)",
                    },
                    "12001": {
                        "name": "Erdgas",
                        "alias": "Erdgas",
                        "description": "Erdgas",
                    },
                    "12002": {
                        "name": "Fluessiggas",
                        "alias": "Flüssiggas",
                        "description": "Flüssiggas",
                    },
                    "12003": {
                        "name": "Grubengas",
                        "alias": "Grubengas",
                        "description": "Grubengas",
                    },
                    "1300": {
                        "name": "Mineraloelprodukte",
                        "alias": "Mineralölprodukte",
                        "description": "Mineralölprodukte (Oberkategorie)",
                    },
                    "13001": {
                        "name": "Heizoel",
                        "alias": "Heizöl",
                        "description": "Heizöl",
                    },
                    "13002": {
                        "name": "Dieselkraftstoff",
                        "alias": "Dieselkraftstoff",
                        "description": "Dieselkraftstoff",
                    },
                    "2000": {
                        "name": "Abfall",
                        "alias": "Abfall",
                        "description": "Abfall (Oberkategorie)",
                    },
                    "20001": {
                        "name": "NichtBiogenerAbfall",
                        "alias": "nicht biogener Abfall",
                        "description": "Nicht biogener Abfall",
                    },
                    "20002": {
                        "name": "BiogenerAbfall",
                        "alias": "biogener Abfall",
                        "description": "Biogener Abfall",
                    },
                    "3100": {
                        "name": "Biomasse",
                        "alias": "Biomasse",
                        "description": "Biomasse (Oberkategorie)",
                    },
                    "31001": {
                        "name": "FesteBiomasse",
                        "alias": "feste Biomasse",
                        "description": "Feste Biomasse",
                    },
                    "31002": {
                        "name": "FluessigeBiomasse",
                        "alias": "flüssige Biomasse",
                        "description": "Flüssige Biomasse",
                    },
                    "3200": {
                        "name": "GasfoermigeBiomasse",
                        "alias": "gasförmige Biomasse",
                        "description": "Gasförmige Biomasse (Oberkategorie)",
                    },
                    "32001": {
                        "name": "Biogas",
                        "alias": "Biogas",
                        "description": "Biogas",
                    },
                    "32002": {
                        "name": "Biomethan",
                        "alias": "Biomethan",
                        "description": "Biomethan",
                    },
                    "32003": {
                        "name": "Klaergas",
                        "alias": "Klärgas",
                        "description": "Klärgas",
                    },
                    "32004": {
                        "name": "Deponiegas",
                        "alias": "Deponiegas",
                        "description": "Deponiegas",
                    },
                    "4000": {
                        "name": "Wasserstoff",
                        "alias": "Wasserstoff",
                        "description": "Wasserstoff (H2) (Oberkategorie)",
                    },
                    "40001": {
                        "name": "GruenerWasserstoff",
                        "alias": "grüner Wasserstoff",
                        "description": "Durch die Elektrolyse von Wasser hergestellter Wasserstoff unter Verwendung von Strom aus erneuerbaren Energiequellen",
                    },
                    "40002": {
                        "name": "BlauerWasserstoff",
                        "alias": "blauer Wasserstoff",
                        "description": "Wasserstoff aus der Reformierung von Erdgas, dessen Erzeugung mit einem Kohlenstoffdioxid-Abscheidungsverfahren und Kohlenstoffdioxid-Speicherungsverfahren gekoppelt wird",
                    },
                    "40003": {
                        "name": "OrangenerWasserstoff",
                        "alias": "orangener Wasserstoff",
                        "description": "Wasserstoff, der aus Biomasse oder unter Verwendung von Strom aus Anlagen der Abfallwirtschaft hergestellt wird",
                    },
                    "40004": {
                        "name": "TuerkiserWasserstoff",
                        "alias": "türkiser Wasserstoff",
                        "description": "Wasserstoff, der über die Pyrolyse von Erdgas hergestellt wird",
                    },
                    "4100": {
                        "name": "Wasserstoffderivate",
                        "alias": "Wasserstoffderivate",
                        "description": "Wasserstoffderivate, z.B. grünes Methan. Der aus Ökostrom erzeugte grüne Wasserstoff wird mit CO2 zu Methan gewandelt.",
                    },
                    "5000": {
                        "name": "UnvermeidbareAbwaerme",
                        "alias": "unvermeidbare Abwärme",
                        "description": "Unvermeidbare Abwärme",
                    },
                    "6000": {"name": "Strom", "alias": "Strom", "description": "Strom"},
                    "7100": {
                        "name": "Solarthermie",
                        "alias": "Solarthermie",
                        "description": "Solarthermie",
                    },
                    "7200": {
                        "name": "Geothermie",
                        "alias": "Geothermie",
                        "description": "Dem Erdboden entnommene Wärme (Oberkategorie)",
                    },
                    "72001": {
                        "name": "OberflaechennaheGeothermie",
                        "alias": "Oberflächennahe Geothermie",
                        "description": "Oberflächennahe Geothermie",
                    },
                    "72002": {
                        "name": "TiefeGeothermie",
                        "alias": "Tiefe Geothermie",
                        "description": "Tiefe Geothermie",
                    },
                    "7300": {
                        "name": "Umweltwaerme",
                        "alias": "Umweltwärme",
                        "description": "Umweltwärme (Oberkategorie)",
                    },
                    "73001": {
                        "name": "Grundwasser",
                        "alias": "Grundwasser",
                        "description": "Umweltwärme aus Grundwasser",
                    },
                    "73002": {
                        "name": "Oberflaechengewaesser",
                        "alias": "Oberflächengewässer",
                        "description": "Umweltwärme aus Oberflächengewässern",
                    },
                    "73003": {
                        "name": "Grubenwasser",
                        "alias": "Grubenwasser",
                        "description": "Umweltwärme aus Grubenwasser",
                    },
                    "73004": {
                        "name": "Luft",
                        "alias": "Luft",
                        "description": "Umweltwärme aus Luft",
                    },
                    "73005": {
                        "name": "Abwasser",
                        "alias": "Abwasser",
                        "description": "Umweltwärme aus Abwasser",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "Sonstiges",
                        "description": "Sonstiges",
                    },
                },
                "typename": "WP_EnergieTraeger",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    verbrauchSektorIndustrie: Annotated[
        definitions.GenericMeasure | None,
        Field(
            description="Jährlicher Endenergieverbrauch in Megawattstunden für den jeweiligen Energieträger im Sektor Industrie",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "MWh/a",
            },
        ),
    ] = None
    verbrauchSektorGHD: Annotated[
        definitions.GenericMeasure | None,
        Field(
            description="Jährlicher Endenergieverbrauch in Megawattstunden für den jeweiligen Energieträger im Sektor Gewerbe, Handel, Dienstleistungen",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "MWh/a",
            },
        ),
    ] = None
    verbrauchSektorHaushalte: Annotated[
        definitions.GenericMeasure | None,
        Field(
            description="Jährlicher Endenergieverbrauch in Megawattstunden für den jeweiligen Energieträger im Sektor private Haushalte",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "MWh/a",
            },
        ),
    ] = None
    verbrauchSektorLiegenschaften: Annotated[
        definitions.GenericMeasure | None,
        Field(
            description="Jährlicher Endenergieverbrauch in Megawattstunden für den jeweiligen Energieträger im Sektor öffentliche Liegenschaften",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "MWh/a",
            },
        ),
    ] = None
    verbrauchGesamt: Annotated[
        definitions.GenericMeasure,
        Field(
            description="Gesamter jährlicher Endenergieverbrauch in Megawattstunden für den jeweiligen Energieträger",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "1",
                "uom": "MWh/a",
            },
        ),
    ]


class WPGebaeudeNetzanschluss(BaseFeature):
    """Angaben zu Gebäuden, die an ein Leitungsnetz angeschlossen sind"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "DataType"
    anzahl: Annotated[
        int,
        Field(
            description="Anzahl der Gebäude",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    anteil: Annotated[
        definitions.Scale,
        Field(
            description="Anteil der Gebäude an Gesamtheit der Gebäude im beplanten Gebiet in Prozent",
            json_schema_extra={
                "typename": "Scale",
                "stereotype": "Measure",
                "multiplicity": "1",
                "uom": "vH",
            },
        ),
    ]


class WPGemeinde(BaseFeature):
    """Spezifikation einer für die Aufstellung des Plans zuständigen Gemeinde"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "DataType"
    ars: Annotated[
        str,
        Field(
            description="Amtlicher Regionalschlüssel",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    name: Annotated[
        str | None,
        Field(
            description="Name der Gemeinde.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class WPObjekt(BaseFeature):
    """Abstrakte Oberklasse für alle XWärmeplan-Fachobjekte. Die Attribute dieser Klasse werden über den Vererbungs-Mechanismus an alle Fachobjekte weitergegeben."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
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
        str | None,
        Field(
            description="Name des Objekts (kann für Kodierung von Links in GML, HTML, JSON verwendet werden)",
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
    refTextInhalt: Annotated[
        AnyUrl | UUID | None,
        Field(
            description="Referenz eines raumbezogenen Fachobjektes auf einen textuell formulierten Planinhalt",
            json_schema_extra={
                "typename": "WP_TextAbschnitt",
                "stereotype": "Association",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refMassnahme: Annotated[
        AnyUrl | UUID | None,
        Field(
            description="Referenz eines raumbezogenen Fachobjektes auf eine Maßnahme zur Umsetzung des Wärmeplans",
            json_schema_extra={
                "typename": "WP_Massnahme",
                "stereotype": "Association",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gehoertZuBereich: Annotated[
        AnyUrl | UUID,
        Field(
            description="Verweis auf den Bereich, zu dem der Planinhalt gehört.",
            json_schema_extra={
                "typename": "WP_Bereich",
                "stereotype": "Association",
                "reverseProperty": "planinhalt",
                "sourceOrTarget": "source",
                "multiplicity": "1",
            },
        ),
    ]


class WPPotenzialanalyseAggregiert(BaseFeature):
    """Zusammenfassende aggregierte Daten der Potenzialanalyse für das Planungsgebiet entsprechend WPG Anlage 2 II"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    id: str | None = None
    ars: Annotated[
        str | None,
        Field(
            description="Regionalschlüssel der betreffenden Gemeinde (Attribut istGemeinsamerWaermeplan = true)",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    endenergieeinsparungGebaeude: Annotated[
        definitions.GenericMeasure | None,
        Field(
            description="Potenziale zur Energieeinsparung durch Wärmebedarfsreduktion von Gebäuden nach Anlage 2 Abschnitt II und § 16 Abs. 2 WPG (Zieljahr gegenüber Basisjahr)",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "MWh",
            },
        ),
    ] = None
    endenergieeinsparungProzesse: Annotated[
        definitions.GenericMeasure | None,
        Field(
            description="Potenziale zur Energieeinsparung durch Steigerung der Energieeffizienz von industrielle und gewerblichen Prozessen nach Anlage 2 Abschnitt II und § 16 Abs. 2 WPG (Zieljahr gegenüber Basisjahr)",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "MWh",
            },
        ),
    ] = None
    erneuerbareEnergienAbwaerme: Annotated[
        list[WPEnergieTraegerVerbrauch],
        Field(
            description="Potenziale erneuerbarer Energien (EE) und unvermeidbarer Abwärme zur Wärmeversorgung nach Energieträgern nach Anlage 2 Abschnitt II und § 16 Abs. 1 WPG\r\nKonformitätsbedingungen: zulässige Enumerationswerte 12003, 2000 bis 32004, 40001, 4100, ab 5000",
            json_schema_extra={
                "typename": "WP_EnergieTraegerVerbrauch",
                "stereotype": "DataType",
                "multiplicity": "1..*",
            },
            min_length=1,
        ),
    ]
    gehoertZuPlan: Annotated[
        AnyUrl | UUID,
        Field(
            description="Relation der Potenzialanalyse auf den zugehörigen Plan",
            json_schema_extra={
                "typename": "WP_Plan",
                "stereotype": "Association",
                "reverseProperty": "potenzialanalyse",
                "sourceOrTarget": "source",
                "multiplicity": "1",
            },
        ),
    ]


class WPPunktobjekt(WPObjekt):
    """Abstrakte Oberklasse für alle WP-Fachobjekte mit (Multi-)Punktgeometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiPoint,
        Field(
            description="Punktgeometrie",
            json_schema_extra={
                "typename": "GM_MultiPoint",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class WPSektorVerbrauch(BaseFeature):
    """Datentyp zur Erfassung von sektorspezifischen Endenergieverbräuchen"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "DataType"
    sektor: Annotated[
        Literal["1000", "2000", "3000", "4000"],
        Field(
            description="Verbrauchssektor",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Industrie",
                        "alias": "Industrie",
                        "description": "Industrie",
                    },
                    "2000": {
                        "name": "GewerbeHandelDienstleistungen",
                        "alias": "Gewerbe, Handel, Dienstleistungen",
                        "description": "Gewerbe, Handel, Dienstleistungen",
                    },
                    "3000": {
                        "name": "PrivateHaushalte",
                        "alias": "Private Haushalte",
                        "description": "Private Haushalte",
                    },
                    "4000": {
                        "name": "OeffentlicheLiegenschaften",
                        "alias": "Öffentliche Liegenschaften",
                        "description": "Öffentliche Liegenschaften",
                    },
                },
                "typename": "WP_Sektor",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    verbrauch: Annotated[
        definitions.GenericMeasure,
        Field(
            description="Jährlicher Endenergieverbrauch in Megawattstunden",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "1",
                "uom": "MWh/a",
            },
        ),
    ]


class WPVerbundenerPlan(BaseFeature):
    """Spezifikation eines anderen Plans, der mit dem Ausgangsplan oder Planbereich verbunden ist und diesen ändert bzw. von ihm geändert wird."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "DataType"
    planName: Annotated[
        str | None,
        Field(
            description='Name (Attribut "name" von "XP_Plan") des verbundenen Plans.',
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    nummer: Annotated[
        str | None,
        Field(
            description='Nummer (Attribut "nummer" von "XP_Plan") des verbundenen Plans',
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ersetzungsdatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum, an dem die Ersetzung in Kraft getreten ist. Das Attribut muss mit dem Datum des Inkrafttretens des ersetzenden Plans konsistent sein.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class WPWaermeSpeicher(WPPunktobjekt):
    """Gewerblich betriebene Wärmespeicher entsprechend WPG Anlage 2 I.2.10"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    status: Annotated[
        Literal["1000", "2000", "3000"],
        Field(
            description="Errichtungsstatus des Wärmespeichers",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Bestehend",
                        "alias": "bestehend",
                        "description": "bestehend",
                    },
                    "2000": {
                        "name": "Geplant",
                        "alias": "geplant",
                        "description": "geplant",
                    },
                    "3000": {
                        "name": "Genehmigt",
                        "alias": "genehmigt",
                        "description": "genehmigt",
                    },
                },
                "typename": "WP_Status",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    speicherkapazitaet: Annotated[
        definitions.GenericMeasure | None,
        Field(
            description="Speicherkapazität in Megawattstunden",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "MWh",
            },
        ),
    ] = None


class WPWaermeerzeugungsanlage(WPPunktobjekt):
    """Wärmeerzeugungsanlagen, einschließlich Kraft-Wärmekopplungsanlagen, entsprechend WPG Anlage 2 I.2.9"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    status: Annotated[
        Literal["1000", "2000", "3000"],
        Field(
            description="Errichtungsstatus der Erzeugungsanlage",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Bestehend",
                        "alias": "bestehend",
                        "description": "bestehend",
                    },
                    "2000": {
                        "name": "Geplant",
                        "alias": "geplant",
                        "description": "geplant",
                    },
                    "3000": {
                        "name": "Genehmigt",
                        "alias": "genehmigt",
                        "description": "genehmigt",
                    },
                },
                "typename": "WP_Status",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    nennleistung: Annotated[
        definitions.GenericMeasure,
        Field(
            description="Nennleistung in Megawatt",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "1",
                "uom": "MW",
            },
        ),
    ]
    inbetriebnahmeJahr: Annotated[
        int,
        Field(
            description="Jahr der Inbetriebnahme. Bei geplanten Netzen wird der früheste Zeitpunkt eingetragen.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    energietraeger: Annotated[
        Literal[
            "1100",
            "11001",
            "11002",
            "1200",
            "12001",
            "12002",
            "12003",
            "1300",
            "13001",
            "13002",
            "2000",
            "20001",
            "20002",
            "3100",
            "31001",
            "31002",
            "3200",
            "32001",
            "32002",
            "32003",
            "32004",
            "4000",
            "40001",
            "40002",
            "40003",
            "40004",
            "4100",
            "5000",
            "6000",
            "7100",
            "7200",
            "72001",
            "72002",
            "7300",
            "73001",
            "73002",
            "73003",
            "73004",
            "73005",
            "9999",
        ],
        Field(
            description="Energieträger",
            json_schema_extra={
                "enumDescription": {
                    "1100": {
                        "name": "Kohle",
                        "alias": "Kohle",
                        "description": "Kohle (Oberkategorie)",
                    },
                    "11001": {
                        "name": "Braunkohle",
                        "alias": "Braunkohle",
                        "description": "Braunkohle",
                    },
                    "11002": {
                        "name": "Steinkohle",
                        "alias": "Steinkohle",
                        "description": "Steinkohle",
                    },
                    "1200": {
                        "name": "FossilesGas",
                        "alias": "Fossiles Gas",
                        "description": "Fossiles Gas (Oberkategorie)",
                    },
                    "12001": {
                        "name": "Erdgas",
                        "alias": "Erdgas",
                        "description": "Erdgas",
                    },
                    "12002": {
                        "name": "Fluessiggas",
                        "alias": "Flüssiggas",
                        "description": "Flüssiggas",
                    },
                    "12003": {
                        "name": "Grubengas",
                        "alias": "Grubengas",
                        "description": "Grubengas",
                    },
                    "1300": {
                        "name": "Mineraloelprodukte",
                        "alias": "Mineralölprodukte",
                        "description": "Mineralölprodukte (Oberkategorie)",
                    },
                    "13001": {
                        "name": "Heizoel",
                        "alias": "Heizöl",
                        "description": "Heizöl",
                    },
                    "13002": {
                        "name": "Dieselkraftstoff",
                        "alias": "Dieselkraftstoff",
                        "description": "Dieselkraftstoff",
                    },
                    "2000": {
                        "name": "Abfall",
                        "alias": "Abfall",
                        "description": "Abfall (Oberkategorie)",
                    },
                    "20001": {
                        "name": "NichtBiogenerAbfall",
                        "alias": "nicht biogener Abfall",
                        "description": "Nicht biogener Abfall",
                    },
                    "20002": {
                        "name": "BiogenerAbfall",
                        "alias": "biogener Abfall",
                        "description": "Biogener Abfall",
                    },
                    "3100": {
                        "name": "Biomasse",
                        "alias": "Biomasse",
                        "description": "Biomasse (Oberkategorie)",
                    },
                    "31001": {
                        "name": "FesteBiomasse",
                        "alias": "feste Biomasse",
                        "description": "Feste Biomasse",
                    },
                    "31002": {
                        "name": "FluessigeBiomasse",
                        "alias": "flüssige Biomasse",
                        "description": "Flüssige Biomasse",
                    },
                    "3200": {
                        "name": "GasfoermigeBiomasse",
                        "alias": "gasförmige Biomasse",
                        "description": "Gasförmige Biomasse (Oberkategorie)",
                    },
                    "32001": {
                        "name": "Biogas",
                        "alias": "Biogas",
                        "description": "Biogas",
                    },
                    "32002": {
                        "name": "Biomethan",
                        "alias": "Biomethan",
                        "description": "Biomethan",
                    },
                    "32003": {
                        "name": "Klaergas",
                        "alias": "Klärgas",
                        "description": "Klärgas",
                    },
                    "32004": {
                        "name": "Deponiegas",
                        "alias": "Deponiegas",
                        "description": "Deponiegas",
                    },
                    "4000": {
                        "name": "Wasserstoff",
                        "alias": "Wasserstoff",
                        "description": "Wasserstoff (H2) (Oberkategorie)",
                    },
                    "40001": {
                        "name": "GruenerWasserstoff",
                        "alias": "grüner Wasserstoff",
                        "description": "Durch die Elektrolyse von Wasser hergestellter Wasserstoff unter Verwendung von Strom aus erneuerbaren Energiequellen",
                    },
                    "40002": {
                        "name": "BlauerWasserstoff",
                        "alias": "blauer Wasserstoff",
                        "description": "Wasserstoff aus der Reformierung von Erdgas, dessen Erzeugung mit einem Kohlenstoffdioxid-Abscheidungsverfahren und Kohlenstoffdioxid-Speicherungsverfahren gekoppelt wird",
                    },
                    "40003": {
                        "name": "OrangenerWasserstoff",
                        "alias": "orangener Wasserstoff",
                        "description": "Wasserstoff, der aus Biomasse oder unter Verwendung von Strom aus Anlagen der Abfallwirtschaft hergestellt wird",
                    },
                    "40004": {
                        "name": "TuerkiserWasserstoff",
                        "alias": "türkiser Wasserstoff",
                        "description": "Wasserstoff, der über die Pyrolyse von Erdgas hergestellt wird",
                    },
                    "4100": {
                        "name": "Wasserstoffderivate",
                        "alias": "Wasserstoffderivate",
                        "description": "Wasserstoffderivate, z.B. grünes Methan. Der aus Ökostrom erzeugte grüne Wasserstoff wird mit CO2 zu Methan gewandelt.",
                    },
                    "5000": {
                        "name": "UnvermeidbareAbwaerme",
                        "alias": "unvermeidbare Abwärme",
                        "description": "Unvermeidbare Abwärme",
                    },
                    "6000": {"name": "Strom", "alias": "Strom", "description": "Strom"},
                    "7100": {
                        "name": "Solarthermie",
                        "alias": "Solarthermie",
                        "description": "Solarthermie",
                    },
                    "7200": {
                        "name": "Geothermie",
                        "alias": "Geothermie",
                        "description": "Dem Erdboden entnommene Wärme (Oberkategorie)",
                    },
                    "72001": {
                        "name": "OberflaechennaheGeothermie",
                        "alias": "Oberflächennahe Geothermie",
                        "description": "Oberflächennahe Geothermie",
                    },
                    "72002": {
                        "name": "TiefeGeothermie",
                        "alias": "Tiefe Geothermie",
                        "description": "Tiefe Geothermie",
                    },
                    "7300": {
                        "name": "Umweltwaerme",
                        "alias": "Umweltwärme",
                        "description": "Umweltwärme (Oberkategorie)",
                    },
                    "73001": {
                        "name": "Grundwasser",
                        "alias": "Grundwasser",
                        "description": "Umweltwärme aus Grundwasser",
                    },
                    "73002": {
                        "name": "Oberflaechengewaesser",
                        "alias": "Oberflächengewässer",
                        "description": "Umweltwärme aus Oberflächengewässern",
                    },
                    "73003": {
                        "name": "Grubenwasser",
                        "alias": "Grubenwasser",
                        "description": "Umweltwärme aus Grubenwasser",
                    },
                    "73004": {
                        "name": "Luft",
                        "alias": "Luft",
                        "description": "Umweltwärme aus Luft",
                    },
                    "73005": {
                        "name": "Abwasser",
                        "alias": "Abwasser",
                        "description": "Umweltwärme aus Abwasser",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "Sonstiges",
                        "description": "Sonstiges",
                    },
                },
                "typename": "WP_EnergieTraeger",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    art: Annotated[
        Literal[
            "1000",
            "2100",
            "2200",
            "2300",
            "2400",
            "3000",
            "4000",
            "5100",
            "5200",
            "6000",
            "60001",
            "60002",
            "60003",
            "7000",
            "70001",
            "70002",
            "70003",
            "9999",
        ]
        | None,
        Field(
            description="Art der Wärmeerzeugung",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Stromdirektheizung",
                        "alias": "Stromdirektheizung",
                        "description": "Stromdirektheizungen wandeln elektrischen Widerstand Strom in Wärme um. Bauformen sind Fußbodenheizungen, Wärmestrahler oder Nachtspeicherheizungen.",
                    },
                    "2100": {
                        "name": "Kohleheizung",
                        "alias": "Kohleheizung",
                        "description": "Kohleheizung",
                    },
                    "2200": {
                        "name": "Erdgasheizung",
                        "alias": "Erdgasheizung",
                        "description": "Erdgasheizung",
                    },
                    "2300": {
                        "name": "Fluessiggasheizung",
                        "alias": "Flüssiggasheizung",
                        "description": "Flüssiggasheizung",
                    },
                    "2400": {
                        "name": "Oelheizung",
                        "alias": "Ölheizung",
                        "description": "Ölheizung",
                    },
                    "3000": {
                        "name": "Hausuebergabestation",
                        "alias": "Hausübergabestation",
                        "description": "leitungsgebundene Wärme, Hausübergabestation",
                    },
                    "4000": {
                        "name": "Solarthermieanlage",
                        "alias": "Solarthermische Anlage",
                        "description": "Solarthermische Anlage",
                    },
                    "5100": {
                        "name": "Erdgas_BHKW",
                        "alias": "Erdgas-Blockheizkraftwerk",
                        "description": "Erdgas-Blockheizkraftwerk",
                    },
                    "5200": {
                        "name": "Biomasse_BHKW",
                        "alias": "Biomasse-Blockheizkraftwerk",
                        "description": "Biomasse-Blockheizkraftwerk",
                    },
                    "6000": {
                        "name": "Biomasseheizung",
                        "alias": "Biomasseheizung",
                        "description": "Biomasseheizung (Oberkategorie)",
                    },
                    "60001": {
                        "name": "Scheitholzheizung",
                        "alias": "Scheitholzheizung",
                        "description": "Scheitholzheizung",
                    },
                    "60002": {
                        "name": "Hackschnitzelheizung",
                        "alias": "Hackschnitzelheizung",
                        "description": "Hackschnitzelheizung",
                    },
                    "60003": {
                        "name": "Pelletheizung",
                        "alias": "Pelettheizung",
                        "description": "Pelettheizung",
                    },
                    "7000": {
                        "name": "Waermepumpe",
                        "alias": "Wärmepumpe",
                        "description": "Wärmepumpe (Oberkategorie)",
                    },
                    "70001": {
                        "name": "LuftWasserWaermepumpe",
                        "alias": "Luft-Wasser-Wärmepumpe",
                        "description": "Luft-Wasser-Wärmepumpe",
                    },
                    "70002": {
                        "name": "SoleWasserWaermepumpe",
                        "alias": "Sole-Wasser-Wärmepumpe",
                        "description": "Sole-Wasser-Wärmepumpe",
                    },
                    "70003": {
                        "name": "WasserWasserWaermepumpe",
                        "alias": "Wasser-Wasser-Wärmepumpe",
                        "description": "Wasser-Wasser-Wärmepumpe",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstige dezentrale Wärmeerzeungsanlage",
                        "description": "Sonstige dezentrale Wärmeerzeungsanlage",
                    },
                },
                "typename": "WP_WaermeerzeugerTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class WPZielszenarioIndikatoren(BaseFeature):
    """Indikatoren des Zielszenario entsprechend WPG Anlage 2 III. Die Indikatoren sind für das beplante Gebiet als Ganzes und jeweils für die Jahre 2030, 2035, 2040 und 2045 anzugeben."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    id: str | None = None
    ars: Annotated[
        str | None,
        Field(
            description="Regionalschlüssel der betreffenden Gemeinde (Attribut istGemeinsamerWaermeplan = true)",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    betrachtungszeitpunkt: Annotated[
        Literal["1000", "2000", "3000", "4000"],
        Field(
            description="Betrachtungszeitpunkt für die jeweiligen Indikatoren",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "2030", "alias": "2030", "description": "2030"},
                    "2000": {"name": "2035", "alias": "2035", "description": "2035"},
                    "3000": {"name": "2040", "alias": "2040", "description": "2040"},
                    "4000": {"name": "2045", "alias": "2045", "description": "2045"},
                },
                "typename": "WP_Betrachtungszeitpunkt",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    eevGesamtNachEnergieTraeger: Annotated[
        list[WPEnergieTraegerVerbrauch],
        Field(
            description="Jährlicher Endenergieverbrauch der gesamten Wärmeversorgung nach Energieträgern und optional nach Sektoren",
            json_schema_extra={
                "typename": "WP_EnergieTraegerVerbrauch",
                "stereotype": "DataType",
                "multiplicity": "1..*",
            },
            min_length=1,
        ),
    ]
    eevGesamtNachEnergieSektor: Annotated[
        list[WPSektorVerbrauch],
        Field(
            description="Jährlicher Endenergieverbrauch der gesamten Wärmeversorgung nach Energiesektoren",
            json_schema_extra={
                "typename": "WP_SektorVerbrauch",
                "stereotype": "DataType",
                "multiplicity": "1..*",
            },
            min_length=1,
        ),
    ]
    eevLeitungsgebWaermeNachEnergieTraeger: Annotated[
        list[WPEnergieTraegerMenge],
        Field(
            description="Jährlicher Endenergieverbrauch der leitungsgebundenen Wärmeversorgung nach Energieträgern",
            json_schema_extra={
                "typename": "WP_EnergieTraegerMenge",
                "stereotype": "DataType",
                "multiplicity": "1..*",
            },
            min_length=1,
        ),
    ]
    co2FaktorLokalerStrom: Annotated[
        definitions.GenericMeasure | None,
        Field(
            description="CO2-Faktor für lokal erzeugten Strom, der für die Berechnung der Treibhausgasemissionen genutzt werden soll.",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "tCO2/MWh",
            },
        ),
    ] = None
    anteilLeitungsgebWaermeversorgung: Annotated[
        definitions.Scale,
        Field(
            description="Anteil der leitungsgebundenen Wärmeversorgung am gesamten Endenergieverbrauch der Wärmeversorgung in Prozent",
            json_schema_extra={
                "typename": "Scale",
                "stereotype": "Measure",
                "multiplicity": "1",
                "uom": "vH",
            },
        ),
    ]
    gebaeudeAnschlussWaermenetz: Annotated[
        WPGebaeudeNetzanschluss,
        Field(
            description="Anzahl der Gebäude mit Anschluss an ein Wärmenetz",
            json_schema_extra={
                "typename": "WP_GebaeudeNetzanschluss",
                "stereotype": "DataType",
                "multiplicity": "1",
            },
        ),
    ]
    eevGasnetzNachEnergieTraeger: Annotated[
        list[WPEnergieTraegerMenge],
        Field(
            description="Jährliche Endenergieverbrauch aus Gasnetzen nach Energieträgern",
            json_schema_extra={
                "typename": "WP_EnergieTraegerMenge",
                "stereotype": "DataType",
                "multiplicity": "1..*",
            },
            min_length=1,
        ),
    ]
    gebaeudeAnschlussGasnetz: Annotated[
        WPGebaeudeNetzanschluss,
        Field(
            description="Anzahl der Gebäude mit Anschluss an ein Gasnetz",
            json_schema_extra={
                "typename": "WP_GebaeudeNetzanschluss",
                "stereotype": "DataType",
                "multiplicity": "1",
            },
        ),
    ]
    bedarfGruenesMethanZieljahr: Annotated[
        definitions.GenericMeasure,
        Field(
            description="Bedarf an grünem Methan für das Zieljahr nach § 28 Abs. 5 WPG",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "1",
                "uom": "MWh",
            },
        ),
    ]
    sanierungsrate: Annotated[
        definitions.GenericMeasure | None,
        Field(
            description="Jährliche Sanierungsrate der Gebäude",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "vH/a",
            },
        ),
    ] = None
    gehoertZuPlan: Annotated[
        AnyUrl | UUID,
        Field(
            description="Relation der Zielszenarioindikatoren auf den zugehörigen Plan",
            json_schema_extra={
                "typename": "WP_Plan",
                "stereotype": "Association",
                "reverseProperty": "zielszenario",
                "sourceOrTarget": "source",
                "multiplicity": "1",
            },
        ),
    ]


class WPExterneReferenz(BaseFeature):
    """Verweis auf ein extern gespeichertes Dokument oder einen extern gespeicherten, georeferenzierten Plan."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "DataType"
    art: Annotated[
        Literal[
            "1000",
            "1010",
            "1020",
            "1030",
            "1040",
            "1050",
            "1060",
            "1065",
            "1070",
            "1080",
            "1090",
            "2000",
            "2100",
            "2200",
            "2300",
            "2400",
            "2500",
            "2600",
            "2700",
            "2800",
            "2850",
            "2900",
            "3000",
            "3100",
            "4000",
            "5000",
            "6000",
            "9998",
            "9999",
        ]
        | None,
        Field(
            description="Typ / Inhalt des referierten Dokuments oder Rasterplans.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Beschreibung",
                        "alias": "Beschreibung",
                        "description": "Beschreibung eines Plans",
                    },
                    "1010": {
                        "name": "Begruendung",
                        "alias": "Begründung",
                        "description": "Begründung eines Plans",
                    },
                    "1020": {
                        "name": "Legende",
                        "alias": "Legende",
                        "description": "Plan-Legende",
                    },
                    "1030": {
                        "name": "Rechtsplan",
                        "alias": "Rechtsplan",
                        "description": "Elektronische Version des rechtsverbindlichen Plans",
                    },
                    "1040": {
                        "name": "Plangrundlage",
                        "alias": "Plangrundlage",
                        "description": "Elektronische Version der Plangrundlage, z.B. ein katasterplan",
                    },
                    "1050": {
                        "name": "Umweltbericht",
                        "alias": "Umweltbericht",
                        "description": "Umweltbericht - Ergebnis der Umweltprüfung bzgl. der Umweltbelange",
                    },
                    "1060": {
                        "name": "Satzung",
                        "alias": "Satzung",
                        "description": "Satzung",
                    },
                    "1065": {
                        "name": "Verordnung",
                        "alias": "Verordnung",
                        "description": "Elektronische Version des Verordnungstextes",
                    },
                    "1070": {
                        "name": "Karte",
                        "alias": "Karte",
                        "description": "Referenz auf eine Karte, die in Bezug zum Plan steht",
                    },
                    "1080": {
                        "name": "Erlaeuterung",
                        "alias": "Erläuterung",
                        "description": "Erläuterungsbericht",
                    },
                    "1090": {
                        "name": "ZusammenfassendeErklaerung",
                        "alias": "Zusammenfassende Erklärung",
                        "description": "Zusammenfassende Erklärung zum Bebauungsplan gemäß BauGB",
                    },
                    "2000": {
                        "name": "Koordinatenliste",
                        "alias": "Koordinatenliste",
                        "description": "Koordinaten-Liste",
                    },
                    "2100": {
                        "name": "Grundstuecksverzeichnis",
                        "alias": "Grundstücksverzeichnis",
                        "description": "Grundstücksverzeichnis",
                    },
                    "2200": {
                        "name": "Pflanzliste",
                        "alias": "Pflanzliste",
                        "description": "Pflanzliste",
                    },
                    "2300": {
                        "name": "Gruenordnungsplan",
                        "alias": "Grünordnungsplan",
                        "description": "Grünordnungsplan",
                    },
                    "2400": {
                        "name": "Erschliessungsvertrag",
                        "alias": "Erschliessungsvertrag",
                        "description": "Erschließungsvertrag",
                    },
                    "2500": {
                        "name": "Durchfuehrungsvertrag",
                        "alias": "Durchführungsvertrag",
                        "description": "Durchführungsvertrag",
                    },
                    "2600": {
                        "name": "StaedtebaulicherVertrag",
                        "alias": "Städtebaulicher Vertrag",
                        "description": "Elektronische Version eines städtebaulichen Vertrages",
                    },
                    "2700": {
                        "name": "UmweltbezogeneStellungnahmen",
                        "alias": "Umweltbezogene Stellungnahmen",
                        "description": "Elektronisches Dokument mit umweltbezogenen Stellungnahmen.",
                    },
                    "2800": {
                        "name": "ÖffentlichkeitseteiligungsBeschluss",
                        "alias": "Öffentlichkeitsbeteiligungs-Beschluss",
                        "description": "Dokument mit dem Beschluss des Gemeinderats zur Öffentlichkeitsbeteiligung",
                    },
                    "2850": {
                        "name": "Aufstellungsbeschluss",
                        "alias": "Aufstellungsbeschluss",
                        "description": "Dokument mit dem Beschluss des Gemeinderats zur Planaufstellung",
                    },
                    "2900": {
                        "name": "VorhabenUndErschliessungsplan",
                        "alias": "Vorhaben Und Erschließungsplan",
                        "description": "Referenz auf einen Vorhaben- und Erschließungsplan nach §7 BauBG-MaßnahmenG von 1993",
                    },
                    "3000": {
                        "name": "MetadatenPlan",
                        "alias": "Metadaten des Plans",
                        "description": "Referenz auf den Metadatensatz des Plans",
                    },
                    "3100": {
                        "name": "StaedtebaulEntwicklungskonzeptInnenentwicklung",
                        "alias": "Städtebauliches Entwicklungskonzept Innenentwicklung",
                        "description": "Städtebauliches Entwicklungskonzept zur Stärkung der Innenentwicklung",
                    },
                    "4000": {
                        "name": "Genehmigung",
                        "alias": "Genehmigung",
                        "description": "Referenz auf ein Dokument mit dem Text der Genehmigung",
                    },
                    "5000": {
                        "name": "Bekanntmachung",
                        "alias": "Bekanntmachung",
                        "description": "Referenz auf den Bekanntmachungs-Text",
                    },
                    "6000": {
                        "name": "Schutzgebietsverordnung",
                        "alias": "Schutzgebietsverordnung",
                        "description": "Rechtliche Grundlage für die Ausweisung und das Management eines Schutzgebietes.",
                    },
                    "9998": {
                        "name": "Rechtsverbindlich",
                        "alias": "Rechtsverbindlich",
                        "description": "Sonstiges rechtsverbindliches Dokument",
                    },
                    "9999": {
                        "name": "Informell",
                        "alias": "Informell",
                        "description": "Sonstiges nicht-rechtsverbindliches Dokument",
                    },
                },
                "typename": "WP_ExterneReferenzTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    referenzName: Annotated[
        str,
        Field(
            description='Name bzw. Titel des referierten Dokuments. Der Standardname ist "Unbekannt".',
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
            description="Dokumentennummer, z.B. Gesetzes- und Verordnungsblatt-Nummer, Jahrgang",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    seitenangabe: Annotated[
        int | None,
        Field(
            description="Seitenangabe, wenn ein Teil eines umfangreiches Dokumentes referenziert wird, z.B. die Gesetz- und Verorderungsblatt-Seite",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    referenzURL: Annotated[
        AnyUrl,
        Field(
            description='URI des referierten Dokuments, über den auf das Dokument lesend zugegriffen werden kann. Wenn der XPlanGML Datensatz und das referierte Dokument in einem hierarchischen Ordnersystem gespeichert sind, kann die URI auch einen relativen Pfad vom XPlanGML-Datensatz zum Dokument enthalten. \r\nStandardmäßig wird der Wert des Attributes "referenzName" verwendet.',
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


class WPFlaechenobjekt(WPObjekt):
    """Abstrakte Oberklasse für alle WP-Fachobjekte mit (Multi-)Flächengeometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiPolygon,
        Field(
            description="Flächengeometrie",
            json_schema_extra={
                "typename": "GM_MultiSurface",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class WPGasErzeugung(WPPunktobjekt):
    """Anlage zur Erzeugung von Wasserstoff oder synthetischen Gasen mit einer Kapazität von mehr als 1 Megawatt installierter Elektrolyseleistung entsprechend WPG Anlage 2 I.2.11"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    status: Annotated[
        Literal["1000", "2000", "3000"],
        Field(
            description="Errichtungsstatus der Erzeugungsanlage",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Bestehend",
                        "alias": "bestehend",
                        "description": "bestehend",
                    },
                    "2000": {
                        "name": "Geplant",
                        "alias": "geplant",
                        "description": "geplant",
                    },
                    "3000": {
                        "name": "Genehmigt",
                        "alias": "genehmigt",
                        "description": "genehmigt",
                    },
                },
                "typename": "WP_Status",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    gasArt: Annotated[
        Literal[
            "1100",
            "11001",
            "11002",
            "1200",
            "12001",
            "12002",
            "12003",
            "1300",
            "13001",
            "13002",
            "2000",
            "20001",
            "20002",
            "3100",
            "31001",
            "31002",
            "3200",
            "32001",
            "32002",
            "32003",
            "32004",
            "4000",
            "40001",
            "40002",
            "40003",
            "40004",
            "4100",
            "5000",
            "6000",
            "7100",
            "7200",
            "72001",
            "72002",
            "7300",
            "73001",
            "73002",
            "73003",
            "73004",
            "73005",
            "9999",
        ],
        Field(
            description="Gasart (Erdgas, Wasserstoff)",
            json_schema_extra={
                "enumDescription": {
                    "1100": {
                        "name": "Kohle",
                        "alias": "Kohle",
                        "description": "Kohle (Oberkategorie)",
                    },
                    "11001": {
                        "name": "Braunkohle",
                        "alias": "Braunkohle",
                        "description": "Braunkohle",
                    },
                    "11002": {
                        "name": "Steinkohle",
                        "alias": "Steinkohle",
                        "description": "Steinkohle",
                    },
                    "1200": {
                        "name": "FossilesGas",
                        "alias": "Fossiles Gas",
                        "description": "Fossiles Gas (Oberkategorie)",
                    },
                    "12001": {
                        "name": "Erdgas",
                        "alias": "Erdgas",
                        "description": "Erdgas",
                    },
                    "12002": {
                        "name": "Fluessiggas",
                        "alias": "Flüssiggas",
                        "description": "Flüssiggas",
                    },
                    "12003": {
                        "name": "Grubengas",
                        "alias": "Grubengas",
                        "description": "Grubengas",
                    },
                    "1300": {
                        "name": "Mineraloelprodukte",
                        "alias": "Mineralölprodukte",
                        "description": "Mineralölprodukte (Oberkategorie)",
                    },
                    "13001": {
                        "name": "Heizoel",
                        "alias": "Heizöl",
                        "description": "Heizöl",
                    },
                    "13002": {
                        "name": "Dieselkraftstoff",
                        "alias": "Dieselkraftstoff",
                        "description": "Dieselkraftstoff",
                    },
                    "2000": {
                        "name": "Abfall",
                        "alias": "Abfall",
                        "description": "Abfall (Oberkategorie)",
                    },
                    "20001": {
                        "name": "NichtBiogenerAbfall",
                        "alias": "nicht biogener Abfall",
                        "description": "Nicht biogener Abfall",
                    },
                    "20002": {
                        "name": "BiogenerAbfall",
                        "alias": "biogener Abfall",
                        "description": "Biogener Abfall",
                    },
                    "3100": {
                        "name": "Biomasse",
                        "alias": "Biomasse",
                        "description": "Biomasse (Oberkategorie)",
                    },
                    "31001": {
                        "name": "FesteBiomasse",
                        "alias": "feste Biomasse",
                        "description": "Feste Biomasse",
                    },
                    "31002": {
                        "name": "FluessigeBiomasse",
                        "alias": "flüssige Biomasse",
                        "description": "Flüssige Biomasse",
                    },
                    "3200": {
                        "name": "GasfoermigeBiomasse",
                        "alias": "gasförmige Biomasse",
                        "description": "Gasförmige Biomasse (Oberkategorie)",
                    },
                    "32001": {
                        "name": "Biogas",
                        "alias": "Biogas",
                        "description": "Biogas",
                    },
                    "32002": {
                        "name": "Biomethan",
                        "alias": "Biomethan",
                        "description": "Biomethan",
                    },
                    "32003": {
                        "name": "Klaergas",
                        "alias": "Klärgas",
                        "description": "Klärgas",
                    },
                    "32004": {
                        "name": "Deponiegas",
                        "alias": "Deponiegas",
                        "description": "Deponiegas",
                    },
                    "4000": {
                        "name": "Wasserstoff",
                        "alias": "Wasserstoff",
                        "description": "Wasserstoff (H2) (Oberkategorie)",
                    },
                    "40001": {
                        "name": "GruenerWasserstoff",
                        "alias": "grüner Wasserstoff",
                        "description": "Durch die Elektrolyse von Wasser hergestellter Wasserstoff unter Verwendung von Strom aus erneuerbaren Energiequellen",
                    },
                    "40002": {
                        "name": "BlauerWasserstoff",
                        "alias": "blauer Wasserstoff",
                        "description": "Wasserstoff aus der Reformierung von Erdgas, dessen Erzeugung mit einem Kohlenstoffdioxid-Abscheidungsverfahren und Kohlenstoffdioxid-Speicherungsverfahren gekoppelt wird",
                    },
                    "40003": {
                        "name": "OrangenerWasserstoff",
                        "alias": "orangener Wasserstoff",
                        "description": "Wasserstoff, der aus Biomasse oder unter Verwendung von Strom aus Anlagen der Abfallwirtschaft hergestellt wird",
                    },
                    "40004": {
                        "name": "TuerkiserWasserstoff",
                        "alias": "türkiser Wasserstoff",
                        "description": "Wasserstoff, der über die Pyrolyse von Erdgas hergestellt wird",
                    },
                    "4100": {
                        "name": "Wasserstoffderivate",
                        "alias": "Wasserstoffderivate",
                        "description": "Wasserstoffderivate, z.B. grünes Methan. Der aus Ökostrom erzeugte grüne Wasserstoff wird mit CO2 zu Methan gewandelt.",
                    },
                    "5000": {
                        "name": "UnvermeidbareAbwaerme",
                        "alias": "unvermeidbare Abwärme",
                        "description": "Unvermeidbare Abwärme",
                    },
                    "6000": {"name": "Strom", "alias": "Strom", "description": "Strom"},
                    "7100": {
                        "name": "Solarthermie",
                        "alias": "Solarthermie",
                        "description": "Solarthermie",
                    },
                    "7200": {
                        "name": "Geothermie",
                        "alias": "Geothermie",
                        "description": "Dem Erdboden entnommene Wärme (Oberkategorie)",
                    },
                    "72001": {
                        "name": "OberflaechennaheGeothermie",
                        "alias": "Oberflächennahe Geothermie",
                        "description": "Oberflächennahe Geothermie",
                    },
                    "72002": {
                        "name": "TiefeGeothermie",
                        "alias": "Tiefe Geothermie",
                        "description": "Tiefe Geothermie",
                    },
                    "7300": {
                        "name": "Umweltwaerme",
                        "alias": "Umweltwärme",
                        "description": "Umweltwärme (Oberkategorie)",
                    },
                    "73001": {
                        "name": "Grundwasser",
                        "alias": "Grundwasser",
                        "description": "Umweltwärme aus Grundwasser",
                    },
                    "73002": {
                        "name": "Oberflaechengewaesser",
                        "alias": "Oberflächengewässer",
                        "description": "Umweltwärme aus Oberflächengewässern",
                    },
                    "73003": {
                        "name": "Grubenwasser",
                        "alias": "Grubenwasser",
                        "description": "Umweltwärme aus Grubenwasser",
                    },
                    "73004": {
                        "name": "Luft",
                        "alias": "Luft",
                        "description": "Umweltwärme aus Luft",
                    },
                    "73005": {
                        "name": "Abwasser",
                        "alias": "Abwasser",
                        "description": "Umweltwärme aus Abwasser",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "Sonstiges",
                        "description": "Sonstiges",
                    },
                },
                "typename": "WP_EnergieTraeger",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    leistung: Annotated[
        definitions.GenericMeasure | None,
        Field(
            description="Elektrolyseleistung",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "MW",
            },
        ),
    ] = None


class WPGasNetz(BaseFeature):
    """Informationen zu Gasnetzabschnitten entsprechend WPG Anlage 2 I.2.8.b)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "DataType"
    netzId: Annotated[
        str,
        Field(
            description="ID des Netzes (kann im Features WP_GasNetzBaublock referenziert werden)",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    text: Annotated[
        str | None,
        Field(
            description="Name oder Hinweis",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    status: Annotated[
        Literal["1000", "2000", "3000"],
        Field(
            description="Errichtungsstatus des Gasnetzabschnitts",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Bestehend",
                        "alias": "bestehend",
                        "description": "bestehend",
                    },
                    "2000": {
                        "name": "Geplant",
                        "alias": "geplant",
                        "description": "geplant",
                    },
                    "3000": {
                        "name": "Genehmigt",
                        "alias": "genehmigt",
                        "description": "genehmigt",
                    },
                },
                "typename": "WP_Status",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    gasArt: Annotated[
        Literal[
            "1100",
            "11001",
            "11002",
            "1200",
            "12001",
            "12002",
            "12003",
            "1300",
            "13001",
            "13002",
            "2000",
            "20001",
            "20002",
            "3100",
            "31001",
            "31002",
            "3200",
            "32001",
            "32002",
            "32003",
            "32004",
            "4000",
            "40001",
            "40002",
            "40003",
            "40004",
            "4100",
            "5000",
            "6000",
            "7100",
            "7200",
            "72001",
            "72002",
            "7300",
            "73001",
            "73002",
            "73003",
            "73004",
            "73005",
            "9999",
        ],
        Field(
            description="Gasart (Erdgas, Wasserstoff, grünes Methan)",
            json_schema_extra={
                "enumDescription": {
                    "1100": {
                        "name": "Kohle",
                        "alias": "Kohle",
                        "description": "Kohle (Oberkategorie)",
                    },
                    "11001": {
                        "name": "Braunkohle",
                        "alias": "Braunkohle",
                        "description": "Braunkohle",
                    },
                    "11002": {
                        "name": "Steinkohle",
                        "alias": "Steinkohle",
                        "description": "Steinkohle",
                    },
                    "1200": {
                        "name": "FossilesGas",
                        "alias": "Fossiles Gas",
                        "description": "Fossiles Gas (Oberkategorie)",
                    },
                    "12001": {
                        "name": "Erdgas",
                        "alias": "Erdgas",
                        "description": "Erdgas",
                    },
                    "12002": {
                        "name": "Fluessiggas",
                        "alias": "Flüssiggas",
                        "description": "Flüssiggas",
                    },
                    "12003": {
                        "name": "Grubengas",
                        "alias": "Grubengas",
                        "description": "Grubengas",
                    },
                    "1300": {
                        "name": "Mineraloelprodukte",
                        "alias": "Mineralölprodukte",
                        "description": "Mineralölprodukte (Oberkategorie)",
                    },
                    "13001": {
                        "name": "Heizoel",
                        "alias": "Heizöl",
                        "description": "Heizöl",
                    },
                    "13002": {
                        "name": "Dieselkraftstoff",
                        "alias": "Dieselkraftstoff",
                        "description": "Dieselkraftstoff",
                    },
                    "2000": {
                        "name": "Abfall",
                        "alias": "Abfall",
                        "description": "Abfall (Oberkategorie)",
                    },
                    "20001": {
                        "name": "NichtBiogenerAbfall",
                        "alias": "nicht biogener Abfall",
                        "description": "Nicht biogener Abfall",
                    },
                    "20002": {
                        "name": "BiogenerAbfall",
                        "alias": "biogener Abfall",
                        "description": "Biogener Abfall",
                    },
                    "3100": {
                        "name": "Biomasse",
                        "alias": "Biomasse",
                        "description": "Biomasse (Oberkategorie)",
                    },
                    "31001": {
                        "name": "FesteBiomasse",
                        "alias": "feste Biomasse",
                        "description": "Feste Biomasse",
                    },
                    "31002": {
                        "name": "FluessigeBiomasse",
                        "alias": "flüssige Biomasse",
                        "description": "Flüssige Biomasse",
                    },
                    "3200": {
                        "name": "GasfoermigeBiomasse",
                        "alias": "gasförmige Biomasse",
                        "description": "Gasförmige Biomasse (Oberkategorie)",
                    },
                    "32001": {
                        "name": "Biogas",
                        "alias": "Biogas",
                        "description": "Biogas",
                    },
                    "32002": {
                        "name": "Biomethan",
                        "alias": "Biomethan",
                        "description": "Biomethan",
                    },
                    "32003": {
                        "name": "Klaergas",
                        "alias": "Klärgas",
                        "description": "Klärgas",
                    },
                    "32004": {
                        "name": "Deponiegas",
                        "alias": "Deponiegas",
                        "description": "Deponiegas",
                    },
                    "4000": {
                        "name": "Wasserstoff",
                        "alias": "Wasserstoff",
                        "description": "Wasserstoff (H2) (Oberkategorie)",
                    },
                    "40001": {
                        "name": "GruenerWasserstoff",
                        "alias": "grüner Wasserstoff",
                        "description": "Durch die Elektrolyse von Wasser hergestellter Wasserstoff unter Verwendung von Strom aus erneuerbaren Energiequellen",
                    },
                    "40002": {
                        "name": "BlauerWasserstoff",
                        "alias": "blauer Wasserstoff",
                        "description": "Wasserstoff aus der Reformierung von Erdgas, dessen Erzeugung mit einem Kohlenstoffdioxid-Abscheidungsverfahren und Kohlenstoffdioxid-Speicherungsverfahren gekoppelt wird",
                    },
                    "40003": {
                        "name": "OrangenerWasserstoff",
                        "alias": "orangener Wasserstoff",
                        "description": "Wasserstoff, der aus Biomasse oder unter Verwendung von Strom aus Anlagen der Abfallwirtschaft hergestellt wird",
                    },
                    "40004": {
                        "name": "TuerkiserWasserstoff",
                        "alias": "türkiser Wasserstoff",
                        "description": "Wasserstoff, der über die Pyrolyse von Erdgas hergestellt wird",
                    },
                    "4100": {
                        "name": "Wasserstoffderivate",
                        "alias": "Wasserstoffderivate",
                        "description": "Wasserstoffderivate, z.B. grünes Methan. Der aus Ökostrom erzeugte grüne Wasserstoff wird mit CO2 zu Methan gewandelt.",
                    },
                    "5000": {
                        "name": "UnvermeidbareAbwaerme",
                        "alias": "unvermeidbare Abwärme",
                        "description": "Unvermeidbare Abwärme",
                    },
                    "6000": {"name": "Strom", "alias": "Strom", "description": "Strom"},
                    "7100": {
                        "name": "Solarthermie",
                        "alias": "Solarthermie",
                        "description": "Solarthermie",
                    },
                    "7200": {
                        "name": "Geothermie",
                        "alias": "Geothermie",
                        "description": "Dem Erdboden entnommene Wärme (Oberkategorie)",
                    },
                    "72001": {
                        "name": "OberflaechennaheGeothermie",
                        "alias": "Oberflächennahe Geothermie",
                        "description": "Oberflächennahe Geothermie",
                    },
                    "72002": {
                        "name": "TiefeGeothermie",
                        "alias": "Tiefe Geothermie",
                        "description": "Tiefe Geothermie",
                    },
                    "7300": {
                        "name": "Umweltwaerme",
                        "alias": "Umweltwärme",
                        "description": "Umweltwärme (Oberkategorie)",
                    },
                    "73001": {
                        "name": "Grundwasser",
                        "alias": "Grundwasser",
                        "description": "Umweltwärme aus Grundwasser",
                    },
                    "73002": {
                        "name": "Oberflaechengewaesser",
                        "alias": "Oberflächengewässer",
                        "description": "Umweltwärme aus Oberflächengewässern",
                    },
                    "73003": {
                        "name": "Grubenwasser",
                        "alias": "Grubenwasser",
                        "description": "Umweltwärme aus Grubenwasser",
                    },
                    "73004": {
                        "name": "Luft",
                        "alias": "Luft",
                        "description": "Umweltwärme aus Luft",
                    },
                    "73005": {
                        "name": "Abwasser",
                        "alias": "Abwasser",
                        "description": "Umweltwärme aus Abwasser",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "Sonstiges",
                        "description": "Sonstiges",
                    },
                },
                "typename": "WP_EnergieTraeger",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    trassenlaenge: Annotated[
        definitions.GenericMeasure,
        Field(
            description="Trassenlänge in Metern",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "1",
                "uom": "m",
            },
        ),
    ]
    anzahlAnschluesse: Annotated[
        int,
        Field(
            description="Anzahl der Hausanschlüsse",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    inbetriebnahmeJahr: Annotated[
        int | None,
        Field(
            description="Jahr der Inbetriebnahme bei Bestandsnetzen",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    geplanteInbetriebnZeit: Annotated[
        str | None,
        Field(
            description="Jahr oder Zeitraum einer geplanten Inbetriebnahme",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class WPGasSpeicher(WPPunktobjekt):
    """Gewerblich betriebene Gasspeicher entsprechend WPG Anlage 2 I.2.10"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    status: Annotated[
        Literal["1000", "2000", "3000"],
        Field(
            description="Errichtungsstatus des Gasspeichers",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Bestehend",
                        "alias": "bestehend",
                        "description": "bestehend",
                    },
                    "2000": {
                        "name": "Geplant",
                        "alias": "geplant",
                        "description": "geplant",
                    },
                    "3000": {
                        "name": "Genehmigt",
                        "alias": "genehmigt",
                        "description": "genehmigt",
                    },
                },
                "typename": "WP_Status",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    gasArt: Annotated[
        Literal[
            "1100",
            "11001",
            "11002",
            "1200",
            "12001",
            "12002",
            "12003",
            "1300",
            "13001",
            "13002",
            "2000",
            "20001",
            "20002",
            "3100",
            "31001",
            "31002",
            "3200",
            "32001",
            "32002",
            "32003",
            "32004",
            "4000",
            "40001",
            "40002",
            "40003",
            "40004",
            "4100",
            "5000",
            "6000",
            "7100",
            "7200",
            "72001",
            "72002",
            "7300",
            "73001",
            "73002",
            "73003",
            "73004",
            "73005",
            "9999",
        ],
        Field(
            description="Gasart (Erdgas, Wasserstoff)",
            json_schema_extra={
                "enumDescription": {
                    "1100": {
                        "name": "Kohle",
                        "alias": "Kohle",
                        "description": "Kohle (Oberkategorie)",
                    },
                    "11001": {
                        "name": "Braunkohle",
                        "alias": "Braunkohle",
                        "description": "Braunkohle",
                    },
                    "11002": {
                        "name": "Steinkohle",
                        "alias": "Steinkohle",
                        "description": "Steinkohle",
                    },
                    "1200": {
                        "name": "FossilesGas",
                        "alias": "Fossiles Gas",
                        "description": "Fossiles Gas (Oberkategorie)",
                    },
                    "12001": {
                        "name": "Erdgas",
                        "alias": "Erdgas",
                        "description": "Erdgas",
                    },
                    "12002": {
                        "name": "Fluessiggas",
                        "alias": "Flüssiggas",
                        "description": "Flüssiggas",
                    },
                    "12003": {
                        "name": "Grubengas",
                        "alias": "Grubengas",
                        "description": "Grubengas",
                    },
                    "1300": {
                        "name": "Mineraloelprodukte",
                        "alias": "Mineralölprodukte",
                        "description": "Mineralölprodukte (Oberkategorie)",
                    },
                    "13001": {
                        "name": "Heizoel",
                        "alias": "Heizöl",
                        "description": "Heizöl",
                    },
                    "13002": {
                        "name": "Dieselkraftstoff",
                        "alias": "Dieselkraftstoff",
                        "description": "Dieselkraftstoff",
                    },
                    "2000": {
                        "name": "Abfall",
                        "alias": "Abfall",
                        "description": "Abfall (Oberkategorie)",
                    },
                    "20001": {
                        "name": "NichtBiogenerAbfall",
                        "alias": "nicht biogener Abfall",
                        "description": "Nicht biogener Abfall",
                    },
                    "20002": {
                        "name": "BiogenerAbfall",
                        "alias": "biogener Abfall",
                        "description": "Biogener Abfall",
                    },
                    "3100": {
                        "name": "Biomasse",
                        "alias": "Biomasse",
                        "description": "Biomasse (Oberkategorie)",
                    },
                    "31001": {
                        "name": "FesteBiomasse",
                        "alias": "feste Biomasse",
                        "description": "Feste Biomasse",
                    },
                    "31002": {
                        "name": "FluessigeBiomasse",
                        "alias": "flüssige Biomasse",
                        "description": "Flüssige Biomasse",
                    },
                    "3200": {
                        "name": "GasfoermigeBiomasse",
                        "alias": "gasförmige Biomasse",
                        "description": "Gasförmige Biomasse (Oberkategorie)",
                    },
                    "32001": {
                        "name": "Biogas",
                        "alias": "Biogas",
                        "description": "Biogas",
                    },
                    "32002": {
                        "name": "Biomethan",
                        "alias": "Biomethan",
                        "description": "Biomethan",
                    },
                    "32003": {
                        "name": "Klaergas",
                        "alias": "Klärgas",
                        "description": "Klärgas",
                    },
                    "32004": {
                        "name": "Deponiegas",
                        "alias": "Deponiegas",
                        "description": "Deponiegas",
                    },
                    "4000": {
                        "name": "Wasserstoff",
                        "alias": "Wasserstoff",
                        "description": "Wasserstoff (H2) (Oberkategorie)",
                    },
                    "40001": {
                        "name": "GruenerWasserstoff",
                        "alias": "grüner Wasserstoff",
                        "description": "Durch die Elektrolyse von Wasser hergestellter Wasserstoff unter Verwendung von Strom aus erneuerbaren Energiequellen",
                    },
                    "40002": {
                        "name": "BlauerWasserstoff",
                        "alias": "blauer Wasserstoff",
                        "description": "Wasserstoff aus der Reformierung von Erdgas, dessen Erzeugung mit einem Kohlenstoffdioxid-Abscheidungsverfahren und Kohlenstoffdioxid-Speicherungsverfahren gekoppelt wird",
                    },
                    "40003": {
                        "name": "OrangenerWasserstoff",
                        "alias": "orangener Wasserstoff",
                        "description": "Wasserstoff, der aus Biomasse oder unter Verwendung von Strom aus Anlagen der Abfallwirtschaft hergestellt wird",
                    },
                    "40004": {
                        "name": "TuerkiserWasserstoff",
                        "alias": "türkiser Wasserstoff",
                        "description": "Wasserstoff, der über die Pyrolyse von Erdgas hergestellt wird",
                    },
                    "4100": {
                        "name": "Wasserstoffderivate",
                        "alias": "Wasserstoffderivate",
                        "description": "Wasserstoffderivate, z.B. grünes Methan. Der aus Ökostrom erzeugte grüne Wasserstoff wird mit CO2 zu Methan gewandelt.",
                    },
                    "5000": {
                        "name": "UnvermeidbareAbwaerme",
                        "alias": "unvermeidbare Abwärme",
                        "description": "Unvermeidbare Abwärme",
                    },
                    "6000": {"name": "Strom", "alias": "Strom", "description": "Strom"},
                    "7100": {
                        "name": "Solarthermie",
                        "alias": "Solarthermie",
                        "description": "Solarthermie",
                    },
                    "7200": {
                        "name": "Geothermie",
                        "alias": "Geothermie",
                        "description": "Dem Erdboden entnommene Wärme (Oberkategorie)",
                    },
                    "72001": {
                        "name": "OberflaechennaheGeothermie",
                        "alias": "Oberflächennahe Geothermie",
                        "description": "Oberflächennahe Geothermie",
                    },
                    "72002": {
                        "name": "TiefeGeothermie",
                        "alias": "Tiefe Geothermie",
                        "description": "Tiefe Geothermie",
                    },
                    "7300": {
                        "name": "Umweltwaerme",
                        "alias": "Umweltwärme",
                        "description": "Umweltwärme (Oberkategorie)",
                    },
                    "73001": {
                        "name": "Grundwasser",
                        "alias": "Grundwasser",
                        "description": "Umweltwärme aus Grundwasser",
                    },
                    "73002": {
                        "name": "Oberflaechengewaesser",
                        "alias": "Oberflächengewässer",
                        "description": "Umweltwärme aus Oberflächengewässern",
                    },
                    "73003": {
                        "name": "Grubenwasser",
                        "alias": "Grubenwasser",
                        "description": "Umweltwärme aus Grubenwasser",
                    },
                    "73004": {
                        "name": "Luft",
                        "alias": "Luft",
                        "description": "Umweltwärme aus Luft",
                    },
                    "73005": {
                        "name": "Abwasser",
                        "alias": "Abwasser",
                        "description": "Umweltwärme aus Abwasser",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "Sonstiges",
                        "description": "Sonstiges",
                    },
                },
                "typename": "WP_EnergieTraeger",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    speicherkapazitaet: Annotated[
        definitions.GenericMeasure | None,
        Field(
            description="Speicherkapazität in Megawattstunden",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "MWh",
            },
        ),
    ] = None


class WPGeometrieobjekt(WPObjekt):
    """Abstrakte Oberklasse für alle WP-Fachobjekte mit variabler Geometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiPoint | definitions.MultiLine | definitions.MultiPolygon,
        Field(
            description="Punkt-, Linien oder Flächengeometrie",
            json_schema_extra={
                "typename": "WP_VariableGeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class WPGrossverbraucher(WPPunktobjekt):
    """Kunden oder Letztverbraucher entsprechend WPG Anlage 2 I.2.7 (bestehende sowie bekannte potenzielle Großverbraucher von Wärme oder Gas sowie bekannte potenzielle Großverbraucher, die gasförmige Energieträger nach § 3 Absatz 1 Nummer 4, 8, 12 oder Nummer 15 Buchstabe e, f, j oder Absatz 2 WPG zu stofflichen Zwecken einsetzen)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    name: Annotated[
        str,
        Field(
            description="Name des Großverbrauchers",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    art: Annotated[
        Literal["1000", "2000", "3000"],
        Field(
            description="Art des Energieverbrauchs",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Waerme",
                        "alias": "Wärme",
                        "description": "Großverbrauch von Wärme",
                    },
                    "2000": {
                        "name": "Gas",
                        "alias": "Gas",
                        "description": "Großverbrauch von Gas",
                    },
                    "3000": {
                        "name": "GasStofflicheZwecke",
                        "alias": "Gas für stoffliche Zwecke",
                        "description": "Potenzielle Großverbraucher von gasförmigen Energieträgern für stoffliche Zwecke",
                    },
                },
                "typename": "WP_GrossverbrauchTyp",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    abnahmeleistung: Annotated[
        definitions.GenericMeasure | None,
        Field(
            description="Abnahmeleistung des Großverbrauchers",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "MWh",
            },
        ),
    ] = None


class WPLinienobjekt(WPObjekt):
    """Abstrakte Oberklasse für alle WP-Fachobjekte mit (Multi-)Liniengeometrie"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.MultiLine,
        Field(
            description="Liniengeometrie",
            json_schema_extra={
                "typename": "GM_MultiCurve",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class WPMassnahme(BaseFeature):
    """Maßnahmen der Umsetzungsstrategie entsprechend WPG Anlage 2 VI"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    id: str | None = None
    ars: Annotated[
        str | None,
        Field(
            description="Regionalschlüssel der betreffenden Gemeinde (Attribut istGemeinsamerWaermeplan = true)",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    kategorie: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "6000", "9999"],
        Field(
            description="Kategorie, der die Maßnahme zugeordnet werden kann",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Potenzialerschliessung_AusbauEE",
                        "alias": "Potenzialerschließung, Ausbau erneu. Energien",
                        "description": "Potenzialerschließung, Flächensicherung und Ausbau erneuerbarer Energien",
                    },
                    "2000": {
                        "name": "Waermenetzausbau",
                        "alias": "Wärmenetzausbau & -transformation",
                        "description": "Wärmenetzausbau und -transformation",
                    },
                    "3000": {
                        "name": "SanierungIndustrieGebaeude",
                        "alias": "Sanierung in Industrie & Gebäuden",
                        "description": "Sanierung/Modernisierung und Effizienzsteigerung in Industrie und Gebäuden",
                    },
                    "4000": {
                        "name": "WaermeversorgungGebaeude",
                        "alias": "Umstellung Wärmeversorgung in Gebäuden",
                        "description": "Heizungsumstellung und Transformation der Wärmeversorgung in Gebäuden und Quartieren",
                    },
                    "5000": {
                        "name": "Strom_Wasserstoffnetzausbau",
                        "alias": "Strom-/Wasserstoffnetzausbau",
                        "description": "Stromnetz- und Wasserstoffnetzausbau",
                    },
                    "6000": {
                        "name": "Verbraucherverhalten_Suffizienz",
                        "alias": "Verbraucherverhalten & Suffizienz",
                        "description": "Verbraucherverhalten und Suffizienz",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "Sonstiges",
                        "description": "Sonstige Kategorie",
                    },
                },
                "typename": "WP_KategorieMassnahme",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    bezeichnung: Annotated[
        str,
        Field(
            description="Bezeichnung der Maßnahme",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    abschlussUmsetzung: Annotated[
        date_aliased,
        Field(
            description="Zeitpunkt, an dem dem die Maßnahme abgeschlossen sein soll",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "1",
            },
        ),
    ]
    kosten: Annotated[
        int,
        Field(
            description="Erwartete Kosten für Planung und Umsetzung der Maßnahme in Euro",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    kostentragenderSektor: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000"]] | None,
        Field(
            description="Kostentragender Sektor",
            json_schema_extra={
                "typename": "WP_Kostentraeger",
                "stereotype": "Enumeration",
                "multiplicity": "0..2",
                "enumDescription": {
                    "1000": {
                        "name": "Gemeinde",
                        "alias": "Gemeinde",
                        "description": "Gemeinde",
                    },
                    "2000": {
                        "name": "SektorHaushalte",
                        "alias": "Sektor Haushalte",
                        "description": "Sektor der privaten Haushalte",
                    },
                    "3000": {
                        "name": "SektorIndustrie",
                        "alias": "Sektor Industrie",
                        "description": "Sektor Industrie",
                    },
                    "4000": {
                        "name": "SektorGHD",
                        "alias": "Sektor GHD",
                        "description": "Sektor Gewerbe, Handel, Dienstleistungen",
                    },
                    "5000": {
                        "name": "SektorEnergiewirtschaft",
                        "alias": "Sektor Energiewirtschaft",
                        "description": "Sektor Energiewirtschaft",
                    },
                },
            },
            max_length=2,
        ),
    ] = None
    endenergieEinsparung: Annotated[
        definitions.GenericMeasure | None,
        Field(
            description="Erwartete Einsparung von Endeenergie",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "MWh/a",
            },
        ),
    ] = None
    treibausgaseEinsparung: Annotated[
        definitions.GenericMeasure | None,
        Field(
            description="Erwartete Einsparung von Treibhausgasen",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "tCO2e/a",
            },
        ),
    ] = None
    finanzierung: Annotated[
        list[Literal["1000", "2000", "3000", "9999"]] | None,
        Field(
            description="Ermittelter Finanzierungsmechanismus zur Umsetzung (mandatorisch für Gebiete mit mehr als 45.000 Einwohnern)",
            json_schema_extra={
                "typename": "WP_Finanzierungsmechanismus",
                "stereotype": "Enumeration",
                "multiplicity": "0..2",
                "enumDescription": {
                    "1000": {
                        "name": "KommunaleMittel",
                        "alias": "Kommunale Mittel",
                        "description": "Private Investitionen",
                    },
                    "2000": {
                        "name": "PrivateInvestitionen",
                        "alias": "Private Investitionen",
                        "description": "Private Investitionen",
                    },
                    "3000": {
                        "name": "Foerderprogramme",
                        "alias": "Förderprogramm",
                        "description": "Förderprogramme",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "Sonstige Finanzierung",
                        "description": "Sonstige Finanzierung",
                    },
                },
            },
            max_length=2,
        ),
    ] = None
    begruendung: Annotated[
        str | None,
        Field(
            description="Begründung bzw. Erläuterung der Maßnahme",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refDokument: Annotated[
        WPExterneReferenz | None,
        Field(
            description="Referenz auf ein externes Dokument zu der Maßnahme",
            json_schema_extra={
                "typename": "WP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gehoertZuPlan: Annotated[
        AnyUrl | UUID,
        Field(
            description="Relation der Maßnahme  auf den zugehörigen Plan",
            json_schema_extra={
                "typename": "WP_Plan",
                "stereotype": "Association",
                "reverseProperty": "massnahme",
                "sourceOrTarget": "source",
                "multiplicity": "1",
            },
        ),
    ]


class WPNichtBeplantesTeilgebiet(WPFlaechenobjekt):
    """Gebiet, das nicht als voraussichtliches Wärmeversorgungsgebiete überplant ist."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"


class WPPlan(BaseFeature):
    """Die Klasse modelliert einen Wärmeplan gemäß § 23 Wärmeplanungsgesetz (WPG). Sie umfasst die in der Anlage 2 aufgeführte kartografische Darstellung der Bestands- und Potenzialanalyse, die Einteilung in Wärmeversorgungsgebiete, die Indikatoren des Zielszenarios, die Darstellung der Wärmeversorgungsarten für das Zieljahr sowie Maßnahmen der Umsetzungsstrategie. Die textlichen und grafischen Erläuterungen der Eignungsprüfung, Bestandsanalyse, des Zielszenarios und der Umsetzungsstrategie können dem Wärmeplan als externe Referenzen beigefügt werden."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    id: str | None = None
    name: Annotated[
        str,
        Field(
            description="Name des Wärmeplans. Das Attribut name setzt sich aus den Attributen nameBasis, nummer und fassungsbezeichnung zusammen.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    nameBasis: Annotated[
        str | None,
        Field(
            description="Unveränderlicher Basisname des Plans",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    fassungsbezeichnung: Annotated[
        str | None,
        Field(
            description="Bezeichnung einer fortlaufenden Fassung des Plans",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
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
        str,
        Field(
            description="Kommentierende Beschreibung des Plans",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    planungsverantwortlicheStelle: Annotated[
        WPGemeinde,
        Field(
            description="Planungsverantwortliche Stelle bzw. planungsverantwortliche Stelle, die in der interkommunalen Kooperation  den Wärmeplan hauptverantwortlich erstellt",
            json_schema_extra={
                "typename": "WP_Gemeinde",
                "stereotype": "DataType",
                "multiplicity": "1",
            },
        ),
    ]
    istPlanungGemeindeverband: Annotated[
        bool,
        Field(
            description="Wärmeplanung wurde in landesrechtlich verankertem Gemeindeverband durchgeführt = true. Default = false.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    istPlanungKonvoi: Annotated[
        bool,
        Field(
            description="Wärmeplanung wurde in freiwilliger Kooperation benachbarter Gemeinden (im Konvoi) durchgeführt = true. Default = false.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    istGemeinsamerWaermeplan: Annotated[
        bool,
        Field(
            description="Dieser Wärmeplan ist ein gemeinsamer Wärmeplan von mindestens zwei planungsverantwortlichen Stellen = true. Default = false.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    beteiligteGemeinden: Annotated[
        list[WPGemeinde] | None,
        Field(
            description="Weitere beteiligte Gemeinden bei einer interkommunalen Zusammenarbeit in der Wärmeplanung und/oder bei der gemeinsamen Erstellung dieses Wärmeplans",
            json_schema_extra={
                "typename": "WP_Gemeinde",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    gesetzlicheGrundlage: Annotated[
        Literal["1000", "2000", "3000"],
        Field(
            description="Gesetzliche Grundlage des Wärmeplans",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "WPG",
                        "alias": "WPG",
                        "description": "Wärmeplan auf Basis des Wärmeplanungsgesetz und der Umsetzungsrichtlinen der Länder",
                    },
                    "2000": {
                        "name": "Landesgesetz",
                        "alias": "Landesverordnung",
                        "description": "Landesgesetz, z.B. Klimaschutz- und Klimawandelanpassungsgesetz Baden-Württemberg (KlimaG BW) vom 7.2.23",
                    },
                    "3000": {
                        "name": "Kommunalrichtlinie",
                        "alias": "Kommunalrichtlinie",
                        "description": "Über die Kommunalrichtlinie (KRL) der NKI geförderter Wärmeplan",
                    },
                },
                "typename": "WP_GesetzlicheGrundlage",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    zieljahr: Annotated[
        str,
        Field(
            description="Das Jahr, in dem spätestens die Umstellung auf eine treibhausgasneutrale Wärmeversorgung abgeschlossen sein soll.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    basisJahrDatenerfassung: Annotated[
        str,
        Field(
            description="Basisjahr der Datenerfassung",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    istvereinfachtesVerfahren: Annotated[
        bool,
        Field(
            description="Wärmeplanung wurde als vereinfachtes Verfahren durchgeführt = true. Default = false.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    istFortschreibung: Annotated[
        bool,
        Field(
            description="Der Plan ist eine Forschreibung gemäß § 25 WPG = true. Default = false.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    ersetztPlan: Annotated[
        WPVerbundenerPlan | None,
        Field(
            description="Verweis auf vorherigen Wärmeplan, der durch den vorliegenden Plan ersetzt wird.",
            json_schema_extra={
                "typename": "WP_VerbundenerPlan",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    aufstellungsbeschlussDatum: Annotated[
        date_aliased,
        Field(
            description="Beschluss oder die Entscheidung der planungsverantwortlichen Stelle über die Durchführung der Wärmeplanung gemäß § 13 WPG",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "1",
            },
        ),
    ]
    beschlussDatum: Annotated[
        date_aliased,
        Field(
            description="WPG § 13: Der Wärmeplan wird durch das nach Maßgabe des Landesrechts zuständige Gremium oder die zuständige Stelle beschlossen",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "1",
            },
        ),
    ]
    technHerstellDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum, an dem der Plan technisch ausgefertigt wurde.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    technischePlanerstellung: Annotated[
        str | None,
        Field(
            description="Bezeichnung der Institution oder Firma, die den Plan technisch erstellt hat.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    externeReferenz: Annotated[
        list[WPExterneReferenz] | None,
        Field(
            description="Referenz auf ein Dokument",
            json_schema_extra={
                "typename": "WP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    raeumlicherGeltungsbereich: Annotated[
        definitions.MultiPolygon,
        Field(
            description="Grenze des räumlichen Geltungsbereiches des Plans",
            json_schema_extra={
                "typename": "GM_MultiSurface",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]
    bestandsanalyse: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            description="Referenz auf Daten der Bestandsanalyse",
            json_schema_extra={
                "typename": "WP_BestandsanalyseAggregiert",
                "stereotype": "Association",
                "reverseProperty": "gehoertZuPlan",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    potenzialanalyse: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            description="Referenz auf Daten der Potenzialanalyse",
            json_schema_extra={
                "typename": "WP_PotenzialanalyseAggregiert",
                "stereotype": "Association",
                "reverseProperty": "gehoertZuPlan",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    zielszenario: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            description="Referenz auf Zielszenarioindikatoren",
            json_schema_extra={
                "typename": "WP_ZielszenarioIndikatoren",
                "stereotype": "Association",
                "reverseProperty": "gehoertZuPlan",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    massnahme: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            description="Referenz auf eine Maßnahme zur Umsetzung des Wärmeplans",
            json_schema_extra={
                "typename": "WP_Massnahme",
                "stereotype": "Association",
                "reverseProperty": "gehoertZuPlan",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    text: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            description="Referenz des Plans auf einen Text",
            json_schema_extra={
                "typename": "WP_TextAbschnitt",
                "stereotype": "Association",
                "reverseProperty": "gehoertZuPlan",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    bereich: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            description="Referenz des Plans auf einen Bereich",
            json_schema_extra={
                "typename": "WP_Bereich",
                "stereotype": "Association",
                "reverseProperty": "gehoertZuPlan",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            },
        ),
    ] = None


class WPPotenzialEnergieEinsparung(WPGeometrieobjekt):
    """Raumbezogenes Potenzial zur Energieeinsparung durch Wärmebedarfsreduktion in Gebäuden sowie in industriellen oder gewerblichen Prozessen entsprechend WPG Anlage 2 II."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    potenzial: Annotated[
        definitions.GenericMeasure,
        Field(
            description="Jährliche Endenergieeinsparung in Megawattstunden",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "1",
                "uom": "MWh/a",
            },
        ),
    ]
    art: Annotated[
        Literal["1000", "2000", "9999"] | None,
        Field(
            description="Verbrauchsbereich der Energie, die potenziell eingespart werden kann.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Gebaeudeenergie",
                        "alias": "Gebäudeenergie",
                        "description": "Gebäudeenergie",
                    },
                    "2000": {
                        "name": "Prozesswaerme",
                        "alias": "Prozesswärme",
                        "description": "Prozesswärme",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstige Energieeinsparung",
                        "description": "Sonstige Energieeinsparung",
                    },
                },
                "typename": "WP_Energieverbrauchsbereich",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class WPPotenzialWaermeNutzung(WPGeometrieobjekt):
    """Raumbezogenes Potenzial zur Nutzung/Erzeugung von Wärme aus erneuerbaren Energien und zur Nutzung von unvermeidbarer Abwärme entsprechend WPG Anlage 2 II."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    potenzial: Annotated[
        list[WPEnergieTraegerMenge],
        Field(
            description="Potenzial der Wärmeerzeugung je Energieträger",
            json_schema_extra={
                "typename": "WP_EnergieTraegerMenge",
                "stereotype": "DataType",
                "multiplicity": "1..*",
            },
            min_length=1,
        ),
    ]


class WPPotenzialWaermeSpeicherung(WPGeometrieobjekt):
    """Raumbezogenes Potenzial zur Wärmespeicherung entsprechend WPG Anlage 2 II."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    potenzial: Annotated[
        definitions.GenericMeasure,
        Field(
            description="Maximal speicherbare Wärmeenergie",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "1",
                "uom": "MWh",
            },
        ),
    ]
    art: Annotated[
        Literal[
            "1000",
            "2000",
            "20001",
            "20002",
            "3000",
            "30001",
            "30002",
            "4000",
            "40001",
            "40002",
            "40003",
            "40004",
            "40005",
            "9999",
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
                        "name": "SaisonalerWaermespeicher",
                        "alias": "Saisonaler Wärmespeicher",
                        "description": "Das Funktionsprinzip der saisonalen Speicherung besteht darin, das überschüssige Wärmeangebot insbesondere in den Sommermonaten zur Beladung des Speichers zu nutzen. In den kälteren Monaten wird die gespeicherte Wärme zur Deckung des Wärmebedarfs genutzt. Der Speicher besteht aus künstlichen oder natürlichen Behältern, die an einen Be- und Entladekreislauf angeschlossen sind.",
                    },
                    "40001": {
                        "name": "Behaelterspeicher",
                        "alias": "Behälterspeicher",
                        "description": "Zumeist drucklose, mit Wasser gefüllte Behälter, die im Untergrund oder oberirdisch gebaut werden",
                    },
                    "40002": {
                        "name": "Erdbeckenspeicher",
                        "alias": "Erdbeckenspeicher",
                        "description": "Erdbeckenspeicher verwenden oberirdische Becken wie natürliche Seen oder künstlich angelegte Reservoirs mit einer wärmegedämmten Abdeckung zur Speicherung von thermischer Energie.  Als Speichermedium kann entweder Wasser oder ein Kies-Wasser-Gemisch verwendet werden.",
                    },
                    "40003": {
                        "name": "Aquiferspeicher",
                        "alias": "Aquiferspeicher",
                        "description": "Aquifer-Wärmespeicher nutzen unterirdische geologische Formationen, wie poröse Gesteinsschichten oder Grundwasserleiter, um Wärme zu speichern. Warmes Wasser wird in den Untergrund gepumpt und bei Bedarf wieder abgepumpt.",
                    },
                    "40004": {
                        "name": "Erdsondenspeicher",
                        "alias": "Erdsondenspeicher",
                        "description": "Erdsondenspeicher nutzen das Gestein im Untergrund zur Wärmespeicherung. Hierzu werden Rohre in den Boden eingelassen, durch die eine Flüssigkeit zirkuliert und über die Wärme in Erd- oder Gesteinsschichten gespeichert wird.",
                    },
                    "40005": {
                        "name": "Latentwaermespeicher",
                        "alias": "Latentwärmespeicher",
                        "description": "Thermischer Energiespeicher, der Wärme über sog. Phasenwechselmaterialien (PCM) speichert. Latentwärmespeicher nutzen den Phasenübergang eines Materials – meist von fest zu flüssig oder umgekehrt. Dabei bleibt die Temperatur nahezu konstant, während große Energiemengen aufgenommen oder abgegeben werden. Die während des Phasenübergangs zugeführte Energie bleibt als latente, „verborgene“ Wärme im Stoff gebunden.",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstiges Speicher",
                        "description": "Sonstige Speicher",
                    },
                },
                "typename": "WP_EnergieSpeicherTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class WPTextAbschnitt(BaseFeature):
    """Ein Abschnitt der textlich formulierten Inhalte  des Plans"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    id: str | None = None
    title: Annotated[
        str,
        Field(
            description="Titel des Abschnitts (kann für Kodierung von Links in GML, HTML, JSON verwendet werden)",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    text: Annotated[
        str,
        Field(
            description="Inhalt eines Abschnitts der textlichen Planinhalte",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    refText: Annotated[
        WPExterneReferenz | None,
        Field(
            description="Referenz auf ein externes Dokument, das den zugehörigen Textabschnitt enthält.",
            json_schema_extra={
                "typename": "WP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gehoertZuPlan: Annotated[
        AnyUrl | UUID,
        Field(
            description="Referenz eines Textes auf den zugehörigen Plan",
            json_schema_extra={
                "typename": "WP_Plan",
                "stereotype": "Association",
                "reverseProperty": "text",
                "sourceOrTarget": "source",
                "multiplicity": "1",
            },
        ),
    ]


class WPWaermeNetz(BaseFeature):
    """Informationen zu Wärmenetzabschnitten entsprechend WPG Anlage 2 I.2.8.a)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "DataType"
    netzId: Annotated[
        str,
        Field(
            description="ID des Netzes (kann im Features WP_WaermeNetzAbschnitt referenziert werden)",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    text: Annotated[
        str | None,
        Field(
            description="Name oder Hinweis",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    status: Annotated[
        Literal["1000", "2000", "3000"],
        Field(
            description="Errichtungsstatus des Wärmenetzabschnitts",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Bestehend",
                        "alias": "bestehend",
                        "description": "bestehend",
                    },
                    "2000": {
                        "name": "Geplant",
                        "alias": "geplant",
                        "description": "geplant",
                    },
                    "3000": {
                        "name": "Genehmigt",
                        "alias": "genehmigt",
                        "description": "genehmigt",
                    },
                },
                "typename": "WP_Status",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    art: Annotated[
        Literal["1000", "2000"],
        Field(
            description="Art",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Wasser",
                        "alias": "Wasser",
                        "description": "Wasser",
                    },
                    "2000": {"name": "Dampf", "alias": "Dampf", "description": "Dampf"},
                },
                "typename": "WP_WaermeTyp",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    temperatur: Annotated[
        definitions.GenericMeasure,
        Field(
            description="Temperatur",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "1",
                "uom": "°C",
            },
        ),
    ]
    trassenlaenge: Annotated[
        definitions.GenericMeasure,
        Field(
            description="Trassenlänge",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "1",
                "uom": "m",
            },
        ),
    ]
    anzahlAnschluesse: Annotated[
        int,
        Field(
            description="Anzahl der Hausanschlüsse",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    geplanteInbetriebnZeit: Annotated[
        str | None,
        Field(
            description="Jahr oder Zeitraum einer geplanten Inbetriebnahme",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    inbetriebnahmeJahr: Annotated[
        int | None,
        Field(
            description="Jahr der  Inbetriebnahme bei Bestandsnetzen",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class WPWaermeNetzAbschnitt(WPGeometrieobjekt):
    """Informationen zu Wärmenetzabschnitten entsprechend WPG Anlage 2 I.2.8.a). Pflichtangaben erfolgen im Datentyp WP_GasNetz. Die optionale Angabe der Anzahl der Hausanschlüsse erfolgt auf Baublockebene im Feature WP_GebaeudeBaublock."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    refNetzID: Annotated[
        str | None,
        Field(
            description="ID des Netzes, zum dem der Abschnitt gehört (siehe Datentyp WP_WaermeNetz)",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    status: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Errichtungsstatus des Wärmenetzabschnitts",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Bestehend",
                        "alias": "bestehend",
                        "description": "bestehend",
                    },
                    "2000": {
                        "name": "Geplant",
                        "alias": "geplant",
                        "description": "geplant",
                    },
                    "3000": {
                        "name": "Genehmigt",
                        "alias": "genehmigt",
                        "description": "genehmigt",
                    },
                },
                "typename": "WP_Status",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    geplanteInbetriebnZeit: Annotated[
        str | None,
        Field(
            description="Jahr oder Zeitraum einer geplanten Inbetriebnahme",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    inbetriebnahmeJahr: Annotated[
        int | None,
        Field(
            description="Jahr der Inbetriebnahme bei Bestandsleitungen",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class WPWaermeerzeugerAngaben(BaseFeature):
    """Datentyp für die Erfassung von Informationen zu dezentralen Wärmeerzeugern"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "DataType"
    art: Annotated[
        Literal[
            "1000",
            "2100",
            "2200",
            "2300",
            "2400",
            "3000",
            "4000",
            "5100",
            "5200",
            "6000",
            "60001",
            "60002",
            "60003",
            "7000",
            "70001",
            "70002",
            "70003",
            "9999",
        ],
        Field(
            description="Art der Wärmeerzeugungsanlage",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Stromdirektheizung",
                        "alias": "Stromdirektheizung",
                        "description": "Stromdirektheizungen wandeln elektrischen Widerstand Strom in Wärme um. Bauformen sind Fußbodenheizungen, Wärmestrahler oder Nachtspeicherheizungen.",
                    },
                    "2100": {
                        "name": "Kohleheizung",
                        "alias": "Kohleheizung",
                        "description": "Kohleheizung",
                    },
                    "2200": {
                        "name": "Erdgasheizung",
                        "alias": "Erdgasheizung",
                        "description": "Erdgasheizung",
                    },
                    "2300": {
                        "name": "Fluessiggasheizung",
                        "alias": "Flüssiggasheizung",
                        "description": "Flüssiggasheizung",
                    },
                    "2400": {
                        "name": "Oelheizung",
                        "alias": "Ölheizung",
                        "description": "Ölheizung",
                    },
                    "3000": {
                        "name": "Hausuebergabestation",
                        "alias": "Hausübergabestation",
                        "description": "leitungsgebundene Wärme, Hausübergabestation",
                    },
                    "4000": {
                        "name": "Solarthermieanlage",
                        "alias": "Solarthermische Anlage",
                        "description": "Solarthermische Anlage",
                    },
                    "5100": {
                        "name": "Erdgas_BHKW",
                        "alias": "Erdgas-Blockheizkraftwerk",
                        "description": "Erdgas-Blockheizkraftwerk",
                    },
                    "5200": {
                        "name": "Biomasse_BHKW",
                        "alias": "Biomasse-Blockheizkraftwerk",
                        "description": "Biomasse-Blockheizkraftwerk",
                    },
                    "6000": {
                        "name": "Biomasseheizung",
                        "alias": "Biomasseheizung",
                        "description": "Biomasseheizung (Oberkategorie)",
                    },
                    "60001": {
                        "name": "Scheitholzheizung",
                        "alias": "Scheitholzheizung",
                        "description": "Scheitholzheizung",
                    },
                    "60002": {
                        "name": "Hackschnitzelheizung",
                        "alias": "Hackschnitzelheizung",
                        "description": "Hackschnitzelheizung",
                    },
                    "60003": {
                        "name": "Pelletheizung",
                        "alias": "Pelettheizung",
                        "description": "Pelettheizung",
                    },
                    "7000": {
                        "name": "Waermepumpe",
                        "alias": "Wärmepumpe",
                        "description": "Wärmepumpe (Oberkategorie)",
                    },
                    "70001": {
                        "name": "LuftWasserWaermepumpe",
                        "alias": "Luft-Wasser-Wärmepumpe",
                        "description": "Luft-Wasser-Wärmepumpe",
                    },
                    "70002": {
                        "name": "SoleWasserWaermepumpe",
                        "alias": "Sole-Wasser-Wärmepumpe",
                        "description": "Sole-Wasser-Wärmepumpe",
                    },
                    "70003": {
                        "name": "WasserWasserWaermepumpe",
                        "alias": "Wasser-Wasser-Wärmepumpe",
                        "description": "Wasser-Wasser-Wärmepumpe",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstige dezentrale Wärmeerzeungsanlage",
                        "description": "Sonstige dezentrale Wärmeerzeungsanlage",
                    },
                },
                "typename": "WP_WaermeerzeugerTyp",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    anzahl: Annotated[
        int,
        Field(
            description="Anzahl der Wärmeerzeugungsanlagen",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    altersklasse: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "6000"] | None,
        Field(
            description="Überwiegende Baualtersklasse der Wärmeerzeugungsanlagen",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "bis1990",
                        "alias": "bis1990",
                        "description": "bis 1990",
                    },
                    "2000": {
                        "name": "1991_1999",
                        "alias": "1991 - 1999",
                        "description": "1991 bis 1999",
                    },
                    "3000": {
                        "name": "2000_2009",
                        "alias": "2000 - 2009",
                        "description": "2000 bis 2009",
                    },
                    "4000": {
                        "name": "2010_2019",
                        "alias": "2010 - 2019",
                        "description": "2010 bis 2019",
                    },
                    "5000": {
                        "name": "2020_2029",
                        "alias": "2020 - 2029",
                        "description": "2020 bis 2029",
                    },
                    "6000": {
                        "name": "ab2030",
                        "alias": "ab 2030",
                        "description": "ab 2030",
                    },
                },
                "typename": "WP_Altersklasse",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    feuerungsleistung: Annotated[
        definitions.GenericMeasure | None,
        Field(
            description="Gesamtfeuerungsleistung der Wärmeerzeugungsanlagen in Megawatt",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "MW",
            },
        ),
    ] = None


class WPWaermeerzeugerEnergietraeger(BaseFeature):
    """Datentyp  der dezentralen Wärmeerzeuger ( einschließlich Hausübergabestationen) und der eingesetzten Energieträger"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "DataType"
    heizung: Annotated[
        Literal[
            "1000",
            "2100",
            "2200",
            "2300",
            "2400",
            "3000",
            "4000",
            "5100",
            "5200",
            "6000",
            "60001",
            "60002",
            "60003",
            "7000",
            "70001",
            "70002",
            "70003",
            "9999",
        ],
        Field(
            description="Art der Heizung",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Stromdirektheizung",
                        "alias": "Stromdirektheizung",
                        "description": "Stromdirektheizungen wandeln durch elektrischen Widerstand Strom in Wärme um. Bauformen sind Fußbodenheizungen, Wärmestrahler oder Nachtspeicherheizungen.",
                    },
                    "2100": {
                        "name": "Kohleheizung",
                        "alias": "Kohleheizung",
                        "description": "Kohleheizung",
                    },
                    "2200": {
                        "name": "Erdgasheizung",
                        "alias": "Erdgasheizung",
                        "description": "Erdgasheizung",
                    },
                    "2300": {
                        "name": "Fluessiggasheizung",
                        "alias": "Flüssiggasheizung",
                        "description": "Flüssiggasheizung",
                    },
                    "2400": {
                        "name": "Oelheizung",
                        "alias": "Ölheizung",
                        "description": "Ölheizung",
                    },
                    "3000": {
                        "name": "Hausuebergabestation",
                        "alias": "Hausübergabestation",
                        "description": "leitungsgebundene Wärme, Hausübergabestation",
                    },
                    "4000": {
                        "name": "Solarthermieanlage",
                        "alias": "Solarthermieanlage",
                        "description": "Solarthermische Anlage",
                    },
                    "5100": {
                        "name": "Erdgas_BHKW",
                        "alias": "Erdgas-BHKW",
                        "description": "Mit Erdgas betriebenes Blockheizkraftwerk (BHKW), das das Prinzip der Kraft-Wärme-Kopplung (KWK) nutzt.",
                    },
                    "5200": {
                        "name": "Biomasse_BHKW",
                        "alias": "Biomasse-BHKW",
                        "description": "Mit Biomasse betriebenes Blockheizkraftwerk (BHKW), das das Prinzip der Kraft-Wärme-Kopplung (KWK) nutzt.",
                    },
                    "6000": {
                        "name": "Biomasseheizung",
                        "alias": "Biomasseheizung",
                        "description": "Oberkategrie von Heizungen, die mit Biomasse befeuert werden.",
                    },
                    "60001": {
                        "name": "Scheitzholzheizung",
                        "alias": "Scheitzholzheizung",
                        "description": "Scheitzholheizung",
                    },
                    "60002": {
                        "name": "Hackschnitzelheizung",
                        "alias": "Hackschnitzelheizung",
                        "description": "Hackschnitzheizung",
                    },
                    "60003": {
                        "name": "Pelettheizung",
                        "alias": "Pelettheizung",
                        "description": "Pelettheizung",
                    },
                    "7000": {
                        "name": "Waermepumpe",
                        "alias": "Wärmepumpe",
                        "description": "Eine Wärmepumpenheizung ist die Anwendung der Wärmepumpe für Heizzwecke. Sie entzieht der Umwelt thermische Energie und bringt diese unter Aufwendung technischer Arbeit mit einem Verdichter über einen thermodynamischen Kreisprozess auf ein höheres, für Heizzwecke nutzbares Temperaturniveau.",
                    },
                    "70001": {
                        "name": "Luft_Wasser_Waermepumpe",
                        "alias": "Luft-Wasser-Wärmepumpe",
                        "description": "Wärmeerzeugung mit Umgebungsluft",
                    },
                    "70002": {
                        "name": "Sole_Wasser_Waermepumpe",
                        "alias": "Sole-Wasser-Wärmepumpe",
                        "description": "Wärmeerzeugung über das Erdreich",
                    },
                    "70003": {
                        "name": "Wasser_Wasser_Waermepumpe",
                        "alias": "Wasser-Wasser-Wärmepumpe",
                        "description": "Wärmeerzeugung mit Grundwasser",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "sonstige dezentrale Wärmeerzeungsanlage",
                        "description": "Sonstige dezentrale Wärmeerzeungsanlage",
                    },
                },
                "typename": "WP_WaermeerzeugerEnergietraegerTyp",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    anzahl: Annotated[
        int,
        Field(
            description="Anteil des jährlichen Energieverbrauchs in Prozent",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]


class WPWaermeliniendichte(WPLinienobjekt):
    """Wärmeliniendichten in Megawattstunden pro Meter und Jahr in Form einer straßenabschnittbezogenen Darstellung entsprechend  WPG Anlage 2 I.2.2"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    waermeliniendichte: Annotated[
        definitions.GenericMeasure,
        Field(
            description="Quotient aus der Wärmemenge in Megawattstunden, die innerhalb eines Leitungsabschnitts an die angeschlossenen Verbraucher innerhalb eines Jahres abgesetzt wird, und der Länge dieses Leitungsabschnitts in Metern",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "1",
                "uom": "MWh/(m*a)",
            },
        ),
    ]


class WPAbwasserNetzAbschnitt(WPLinienobjekt):
    """Informationen zu Abwassernetzabschnitten entsprechend WPG Anlage 2 I.2.8.c)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    status: Annotated[
        Literal["1000", "2000", "3000"],
        Field(
            description="Errichtungsstatus des Abwassernetzabschnitts",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Bestehend",
                        "alias": "bestehend",
                        "description": "bestehend",
                    },
                    "2000": {
                        "name": "Geplant",
                        "alias": "geplant",
                        "description": "geplant",
                    },
                    "3000": {
                        "name": "Genehmigt",
                        "alias": "genehmigt",
                        "description": "genehmigt",
                    },
                },
                "typename": "WP_Status",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    trockenwetterabfluss: Annotated[
        definitions.GenericMeasure,
        Field(
            description="Als Trockenwetterabfluss werden sämtliche Abwasserarten bezeichnet, in denen kein Regen- bzw. Niederschlagswasser enthalten ist.",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "1",
                "uom": "m3/s",
            },
        ),
    ]


class WPAnschlussGruenesMethan(WPGeometrieobjekt):
    """Grundstück, das an einem bestehenden oder in Planung befindlichen Gasverteilernetz mit grünem Methan anliegt (WPG § 28 Abs. 1)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"


class WPAnschlusszwang(WPGeometrieobjekt):
    """Gebiet oder Straßenabschnitt mit Anschluss- und Benutzungszwang aufgrund eines Satzungsbeschlusses entsprechend WPG Anlage 2 IV."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    satzungsbeschluss: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Satzungsbeschlusses",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class WPAusschlussgebiet(WPFlaechenobjekt):
    """Ausschlussgebiete (z.B. Schutzgebiete) entsprechend WPG Anlage 2 II."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    art: Annotated[
        str,
        Field(
            description="Art des Ausschlussgebiets",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]


class WPBaublock(WPFlaechenobjekt):
    """Abstrakte Oberklasse für alle baublockbezogene WP-Fachobjekte. Gemäß WPG § 3 ist "Baublock" ein Gebäude oder mehrere Gebäude oder Liegenschaften, das oder die von mehreren oder sämtlichen Seiten von Straßen, Schienen oder sonstigen natürlichen oder baulichen Grenzen umschlossen und für die Zwecke der Wärmeplanung als zusammengehörig zu betrachten ist oder sind."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    baublockId: Annotated[
        str | None,
        Field(
            description="ID des Baublocks",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class WPBeplantesTeilgebiet(WPFlaechenobjekt):
    """Abstrakte Oberklasse für beplante Teilgebiete. Gemäß § 3 WPG ist  "beplantes Teilgebiet" ein Teil des beplanten Gebiets, das aus mehreren Grundstücken oder aus Teilen von, aus einzelnen oder mehreren Baublöcken besteht und von der planungsverantwortlichen Stelle für die Untersuchung der möglichen Wärmeversorgungsarten sowie für die entsprechende Einteilung in voraussichtliche Wärmeversorgungsgebiete zusammengefasst wird."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    istVerkuerzteWaermeplanung: Annotated[
        bool,
        Field(
            description="Teilgebiet, für das eine verkürzte Wärmeplanung gemäß § 14 Abs. 4 WPG durchgeführt wurdet = true. Default = false",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]


class WPBestandsanalyseAggregiert(BaseFeature):
    """Zusammenfassende aggregierte Daten für das Planungsgebiet, die die Grundlage für eine textliche und grafische Darstellungen der Bestandsanalyse bilden, entsprechend WPG Anlage 2 I"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    id: str | None = None
    ars: Annotated[
        str | None,
        Field(
            description="Regionalschlüssel der betreffenden Gemeinde (Attribut istGemeinsamerWaermeplan = true)",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    stichtag: Annotated[
        date_aliased,
        Field(
            description="Datum des Stichtags",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "1",
            },
        ),
    ]
    eevGesamtNachEnergieTraeger: Annotated[
        list[WPEnergieTraegerVerbrauch],
        Field(
            description="Jährlicher Endenergieverbrauch der gesamten Wärmeversorgung nach Energieträgern und optional nach Sektoren",
            json_schema_extra={
                "typename": "WP_EnergieTraegerVerbrauch",
                "stereotype": "DataType",
                "multiplicity": "1..*",
            },
            min_length=1,
        ),
    ]
    eevGesamtNachEnergieSektor: Annotated[
        list[WPSektorVerbrauch],
        Field(
            description="Jährlicher Endenergieverbrauch der gesamten Wärmeversorgung nach Energiesektoren",
            json_schema_extra={
                "typename": "WP_SektorVerbrauch",
                "stereotype": "DataType",
                "multiplicity": "1..*",
            },
            min_length=1,
        ),
    ]
    eevLeitungsgebWaermeNachEnergieTraeger: Annotated[
        list[WPEnergieTraegerVerbrauch],
        Field(
            description="Jährlicher Endenergieverbrauch der leitungsgebundenen Wärmeversorgung nach Energieträgern",
            json_schema_extra={
                "typename": "WP_EnergieTraegerVerbrauch",
                "stereotype": "DataType",
                "multiplicity": "1..*",
            },
            min_length=1,
        ),
    ]
    co2FaktorLokalerStrom: Annotated[
        definitions.GenericMeasure | None,
        Field(
            description="CO2-Faktor für lokal erzeugten Strom",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "tCO2/MWh",
            },
        ),
    ] = None
    waermerzeugerMitEnergietraeger: Annotated[
        list[WPWaermeerzeugerEnergietraeger],
        Field(
            description="Anzahl dezentraler Wärmeerzeuger, einschließlich Hausübergabestationen, nach Art der Wärmeerzeuger einschließlich des eingesetzten Energieträgers",
            json_schema_extra={
                "typename": "WP_WaermeerzeugerEnergietraeger",
                "stereotype": "DataType",
                "multiplicity": "1..*",
            },
            min_length=1,
        ),
    ]
    waermenetz: Annotated[
        list[WPWaermeNetz] | None,
        Field(
            description="Informationen zum Wärmenetz. Weitere optionale Angaben sind im Feature WP_Waremnetzabschnitt und WP_GebauedeBaublock möglich.",
            json_schema_extra={
                "typename": "WP_WaermeNetz",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    gasnetz: Annotated[
        list[WPGasNetz] | None,
        Field(
            description="Informationen zum Gasnetz. Weitere optionale Angaben sind im Feature WP_GasnetzAbschnitt möglich.",
            json_schema_extra={
                "typename": "WP_GasNetz",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    gehoertZuPlan: Annotated[
        AnyUrl | UUID,
        Field(
            description="Relation der Bestandsanalyse auf den zugehörigen Plan",
            json_schema_extra={
                "typename": "WP_Plan",
                "stereotype": "Association",
                "reverseProperty": "bestandsanalyse",
                "sourceOrTarget": "source",
                "multiplicity": "1",
            },
        ),
    ]


class WPDezentraleErzeugung(WPBaublock):
    """Baublockbezogene Informationen zur dezentralen Wärmeerzeugung entsprechend WPG Anlage 2 I.2.4"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    waermeerzeuger: Annotated[
        list[WPWaermeerzeugerAngaben],
        Field(
            description="Angaben zu dezentralen Wäremerzeugern",
            json_schema_extra={
                "typename": "WP_WaermeerzeugerAngaben",
                "stereotype": "DataType",
                "multiplicity": "1..*",
            },
            min_length=1,
        ),
    ]


class WPEignungspruefung(WPFlaechenobjekt):
    """Beplantes Gebiet oder Teilgebiet, das sich mit hoher Wahrscheinlichkeit nicht für Versorgung mit Fernwärme oder Wasserstoff eignet, entsprechend WPG Anlage 2 IV und § 14 WPG"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    ungeeignetWaermenetz: Annotated[
        bool | None,
        Field(
            description="ungeeingnet für ein Wärmenetz",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ungeeignetWasserstoffnetz: Annotated[
        bool | None,
        Field(
            description="Ungeeignet für ein Wasserstoffnetz",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class WPEnergieEinspargebiet(WPBeplantesTeilgebiet):
    """Gebiet, für das ein erhöhtes Energieeinsparpotenzial nach § 18 Absatz 5 vorliegt, entsprechend WPG Anlage 2 IV."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    sanierungsgebiet: Annotated[
        bool | None,
        Field(
            description="Gebiet erscheint geeignet, zukünftig in einer gesonderten städtebaulichen Entscheidung als Sanierungsgebiet im Sinne des Ersten Abschnitts des Ersten Teils des Zweiten Kapitels des Baugesetzbuchs festgelegt werden.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    reduktionEnergieverbrauch: Annotated[
        bool | None,
        Field(
            description="Gebiet mit einem hohen Anteil an Gebäuden mit einem hohen spezifischen Endenergieverbrauch für Raumwärme, in denen Maßnahmen zur Reduktion des Endenergiebedarfs besonders geeignet sind, die Transformation zu einer treibhausgasneutralen Wärmeversorgung unterstützen.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class WPGasNetzBaublock(WPBaublock):
    """Informationen zu Gasnetzabschnitten entsprechend WPG Anlage 2 I.2.8.b). Pflichtangaben erfolgen im Datentyp WP_GasNetz."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    refNetzID: Annotated[
        str | None,
        Field(
            description="ID des Netzes, zum dem der Abschnit gehört (siehe Datentyp WP_GasNetz)",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    status: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Errichtungsstatus des Gasnetzabschnitts",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Bestehend",
                        "alias": "bestehend",
                        "description": "bestehend",
                    },
                    "2000": {
                        "name": "Geplant",
                        "alias": "geplant",
                        "description": "geplant",
                    },
                    "3000": {
                        "name": "Genehmigt",
                        "alias": "genehmigt",
                        "description": "genehmigt",
                    },
                },
                "typename": "WP_Status",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gasArt: Annotated[
        Literal[
            "1100",
            "11001",
            "11002",
            "1200",
            "12001",
            "12002",
            "12003",
            "1300",
            "13001",
            "13002",
            "2000",
            "20001",
            "20002",
            "3100",
            "31001",
            "31002",
            "3200",
            "32001",
            "32002",
            "32003",
            "32004",
            "4000",
            "40001",
            "40002",
            "40003",
            "40004",
            "4100",
            "5000",
            "6000",
            "7100",
            "7200",
            "72001",
            "72002",
            "7300",
            "73001",
            "73002",
            "73003",
            "73004",
            "73005",
            "9999",
        ]
        | None,
        Field(
            description="Gasart (Erdgas, Wasserstoff, grünes Methan)",
            json_schema_extra={
                "enumDescription": {
                    "1100": {
                        "name": "Kohle",
                        "alias": "Kohle",
                        "description": "Kohle (Oberkategorie)",
                    },
                    "11001": {
                        "name": "Braunkohle",
                        "alias": "Braunkohle",
                        "description": "Braunkohle",
                    },
                    "11002": {
                        "name": "Steinkohle",
                        "alias": "Steinkohle",
                        "description": "Steinkohle",
                    },
                    "1200": {
                        "name": "FossilesGas",
                        "alias": "Fossiles Gas",
                        "description": "Fossiles Gas (Oberkategorie)",
                    },
                    "12001": {
                        "name": "Erdgas",
                        "alias": "Erdgas",
                        "description": "Erdgas",
                    },
                    "12002": {
                        "name": "Fluessiggas",
                        "alias": "Flüssiggas",
                        "description": "Flüssiggas",
                    },
                    "12003": {
                        "name": "Grubengas",
                        "alias": "Grubengas",
                        "description": "Grubengas",
                    },
                    "1300": {
                        "name": "Mineraloelprodukte",
                        "alias": "Mineralölprodukte",
                        "description": "Mineralölprodukte (Oberkategorie)",
                    },
                    "13001": {
                        "name": "Heizoel",
                        "alias": "Heizöl",
                        "description": "Heizöl",
                    },
                    "13002": {
                        "name": "Dieselkraftstoff",
                        "alias": "Dieselkraftstoff",
                        "description": "Dieselkraftstoff",
                    },
                    "2000": {
                        "name": "Abfall",
                        "alias": "Abfall",
                        "description": "Abfall (Oberkategorie)",
                    },
                    "20001": {
                        "name": "NichtBiogenerAbfall",
                        "alias": "nicht biogener Abfall",
                        "description": "Nicht biogener Abfall",
                    },
                    "20002": {
                        "name": "BiogenerAbfall",
                        "alias": "biogener Abfall",
                        "description": "Biogener Abfall",
                    },
                    "3100": {
                        "name": "Biomasse",
                        "alias": "Biomasse",
                        "description": "Biomasse (Oberkategorie)",
                    },
                    "31001": {
                        "name": "FesteBiomasse",
                        "alias": "feste Biomasse",
                        "description": "Feste Biomasse",
                    },
                    "31002": {
                        "name": "FluessigeBiomasse",
                        "alias": "flüssige Biomasse",
                        "description": "Flüssige Biomasse",
                    },
                    "3200": {
                        "name": "GasfoermigeBiomasse",
                        "alias": "gasförmige Biomasse",
                        "description": "Gasförmige Biomasse (Oberkategorie)",
                    },
                    "32001": {
                        "name": "Biogas",
                        "alias": "Biogas",
                        "description": "Biogas",
                    },
                    "32002": {
                        "name": "Biomethan",
                        "alias": "Biomethan",
                        "description": "Biomethan",
                    },
                    "32003": {
                        "name": "Klaergas",
                        "alias": "Klärgas",
                        "description": "Klärgas",
                    },
                    "32004": {
                        "name": "Deponiegas",
                        "alias": "Deponiegas",
                        "description": "Deponiegas",
                    },
                    "4000": {
                        "name": "Wasserstoff",
                        "alias": "Wasserstoff",
                        "description": "Wasserstoff (H2) (Oberkategorie)",
                    },
                    "40001": {
                        "name": "GruenerWasserstoff",
                        "alias": "grüner Wasserstoff",
                        "description": "Durch die Elektrolyse von Wasser hergestellter Wasserstoff unter Verwendung von Strom aus erneuerbaren Energiequellen",
                    },
                    "40002": {
                        "name": "BlauerWasserstoff",
                        "alias": "blauer Wasserstoff",
                        "description": "Wasserstoff aus der Reformierung von Erdgas, dessen Erzeugung mit einem Kohlenstoffdioxid-Abscheidungsverfahren und Kohlenstoffdioxid-Speicherungsverfahren gekoppelt wird",
                    },
                    "40003": {
                        "name": "OrangenerWasserstoff",
                        "alias": "orangener Wasserstoff",
                        "description": "Wasserstoff, der aus Biomasse oder unter Verwendung von Strom aus Anlagen der Abfallwirtschaft hergestellt wird",
                    },
                    "40004": {
                        "name": "TuerkiserWasserstoff",
                        "alias": "türkiser Wasserstoff",
                        "description": "Wasserstoff, der über die Pyrolyse von Erdgas hergestellt wird",
                    },
                    "4100": {
                        "name": "Wasserstoffderivate",
                        "alias": "Wasserstoffderivate",
                        "description": "Wasserstoffderivate, z.B. grünes Methan. Der aus Ökostrom erzeugte grüne Wasserstoff wird mit CO2 zu Methan gewandelt.",
                    },
                    "5000": {
                        "name": "UnvermeidbareAbwaerme",
                        "alias": "unvermeidbare Abwärme",
                        "description": "Unvermeidbare Abwärme",
                    },
                    "6000": {"name": "Strom", "alias": "Strom", "description": "Strom"},
                    "7100": {
                        "name": "Solarthermie",
                        "alias": "Solarthermie",
                        "description": "Solarthermie",
                    },
                    "7200": {
                        "name": "Geothermie",
                        "alias": "Geothermie",
                        "description": "Dem Erdboden entnommene Wärme (Oberkategorie)",
                    },
                    "72001": {
                        "name": "OberflaechennaheGeothermie",
                        "alias": "Oberflächennahe Geothermie",
                        "description": "Oberflächennahe Geothermie",
                    },
                    "72002": {
                        "name": "TiefeGeothermie",
                        "alias": "Tiefe Geothermie",
                        "description": "Tiefe Geothermie",
                    },
                    "7300": {
                        "name": "Umweltwaerme",
                        "alias": "Umweltwärme",
                        "description": "Umweltwärme (Oberkategorie)",
                    },
                    "73001": {
                        "name": "Grundwasser",
                        "alias": "Grundwasser",
                        "description": "Umweltwärme aus Grundwasser",
                    },
                    "73002": {
                        "name": "Oberflaechengewaesser",
                        "alias": "Oberflächengewässer",
                        "description": "Umweltwärme aus Oberflächengewässern",
                    },
                    "73003": {
                        "name": "Grubenwasser",
                        "alias": "Grubenwasser",
                        "description": "Umweltwärme aus Grubenwasser",
                    },
                    "73004": {
                        "name": "Luft",
                        "alias": "Luft",
                        "description": "Umweltwärme aus Luft",
                    },
                    "73005": {
                        "name": "Abwasser",
                        "alias": "Abwasser",
                        "description": "Umweltwärme aus Abwasser",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "alias": "Sonstiges",
                        "description": "Sonstiges",
                    },
                },
                "typename": "WP_EnergieTraeger",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    inbetriebnahmeJahr: Annotated[
        int | None,
        Field(
            description="Jahr der Inbetriebnahme bei Bestandsnetzen",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    geplanteInbetriebnahmeZeit: Annotated[
        str | None,
        Field(
            description="Jahr oder Zeitraum einer geplanten Inbetriebnahme",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    anzahlAnschluesse: Annotated[
        int | None,
        Field(
            description="Anzahl der Hausanschlüsse",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class WPGebaeudeBaublock(WPBaublock):
    """Baublockbezogene Informationen zu Gebäudedaten entsprechend WPG Anlage 2 I.2.5 und I.2.6"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    gebaeudetyp: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "10003",
            "10004",
            "2000",
            "20001",
            "20002",
            "20003",
            "20004",
            "20005",
            "20006",
            "20007",
            "20008",
            "20009",
            "20010",
        ],
        Field(
            description="Überwiegender Gebäudetyp im Baublock",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Wohngebaeude",
                        "alias": "Wohngebäude",
                        "description": "Gebäude, das nach seiner Zweckbestimmung überwiegend dem Wohnen dient, einschließlich von Wohn-, Alten- oder Pflegeheimen sowie ähnlicher Einrichtungen (GEG § 3)",
                    },
                    "10001": {
                        "name": "Einfamlienhaus",
                        "alias": "Einfamilienhaus",
                        "description": "Freistehendes Wohngebäude mit 1-2 Wohnungen",
                    },
                    "10002": {
                        "name": "Reihenhaus",
                        "alias": "Reihenhaus",
                        "description": "Wohngebäude mit 1 bis 2 Wohnungen als Doppelhaus, gereihtes Haus oder sonstiger Gebäudetyp",
                    },
                    "10003": {
                        "name": "Mehrfamilienhaus",
                        "alias": "Mehrfamilienhaus (3-12 WE)",
                        "description": "Wohngebäude mit 3 bis 12 Wohnungen",
                    },
                    "10004": {
                        "name": "GroßesMehrfamilienhaus",
                        "alias": "Großes Mehrfamilienhaus (>=13 WE)",
                        "description": "Wohngebäude mit 13 oder mehr Wohnungen",
                    },
                    "2000": {
                        "name": "Nichtwohngebaeude",
                        "alias": "Nichtwohngebäude",
                        "description": "Gebäude, das nach seiner Zweckbestimmung NICHT überwiegend dem Wohnen dient. (Wohn-, Alten- oder Pflegeheimen sowie ähnliche Einrichtungen sind Wohngebäude, s. GEG § 3)",
                    },
                    "20001": {
                        "name": "Buerogebaeude",
                        "alias": "Bürogebäude",
                        "description": "Büro-, Verwaltungs-, Amtsgebäude",
                    },
                    "20002": {
                        "name": "Handel",
                        "alias": "Handel",
                        "description": "Gebäude des Groß- und Einzelhandels",
                    },
                    "20003": {
                        "name": "Beherbergung_Gaststaette",
                        "alias": "Beherbergung/Gaststätten",
                        "description": "Gebäude für Beherbergung und Gastronomie",
                    },
                    "20004": {
                        "name": "Krankenhaus",
                        "alias": "Krankenhäuser",
                        "description": "Krankenhäuser",
                    },
                    "20005": {
                        "name": "Kultureinrichtung",
                        "alias": "Kultureinrichtungen",
                        "description": "Kultureinrichtungen",
                    },
                    "20006": {
                        "name": "Bildungseinrichtung",
                        "alias": "Bildungseinrichtungen",
                        "description": "Bildungseinrichtungen",
                    },
                    "20007": {
                        "name": "Sporteinrichtung",
                        "alias": "Sporteinrichtungen",
                        "description": "Sporteinrichtungen",
                    },
                    "20008": {
                        "name": "Schwimmbad",
                        "alias": "Schwimmbäder",
                        "description": "Schwimmbäder",
                    },
                    "20009": {
                        "name": "Lagergebaeude",
                        "alias": "Lagergebäude",
                        "description": "Lagergebäude",
                    },
                    "20010": {
                        "name": "Industrie",
                        "alias": "Industrie",
                        "description": "Industrie und Gewerbe",
                    },
                },
                "typename": "WP_GebaeudeTyp",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    baualtersklasse: Annotated[
        Literal[
            "1000",
            "10001",
            "10002",
            "2000",
            "3000",
            "30001",
            "30002",
            "4000",
            "40001",
            "40002",
            "40003",
            "5000",
            "9999",
        ],
        Field(
            description="Überwiegende Baualtersklasse der Gebäude im Baublock",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "vor1949",
                        "alias": "vor 1949 (Oberkategorie)",
                        "description": "vor 1949 (Oberkategorie)",
                    },
                    "10001": {
                        "name": "bis1918",
                        "alias": "bis 1918",
                        "description": "bis 1918",
                    },
                    "10002": {
                        "name": "1919_1948",
                        "alias": "1919 - 1948",
                        "description": "1919 bis 1948",
                    },
                    "2000": {
                        "name": "1949_bis_1968",
                        "alias": "1949 - 1968",
                        "description": "1949 bis 1968",
                    },
                    "3000": {
                        "name": "1969_bis_2001",
                        "alias": "1969 - 2001 (Oberkategorie)",
                        "description": "1969 bis 2001 (Oberkategorie)",
                    },
                    "30001": {
                        "name": "1969_1983",
                        "alias": "1969 - 1983",
                        "description": "1969 bis 1983",
                    },
                    "30002": {
                        "name": "1984_2001",
                        "alias": "1984 - 2001",
                        "description": "1984 bis 2001",
                    },
                    "4000": {
                        "name": "2002_bis_2029",
                        "alias": "2002 - 2029 (Oberkategorie)",
                        "description": "2002 bis 2029 (Oberkategorie)",
                    },
                    "40001": {
                        "name": "2002_2009",
                        "alias": "2002 - 2009",
                        "description": "2002 bis 2009",
                    },
                    "40002": {
                        "name": "2010_2016",
                        "alias": "2010 - 2016",
                        "description": "2010 bis 2016",
                    },
                    "40003": {
                        "name": "2017_2029",
                        "alias": "2017 - 2029",
                        "description": "2017 bis 2029",
                    },
                    "5000": {
                        "name": "ab2030",
                        "alias": "ab 2030",
                        "description": "ab 2030",
                    },
                    "9999": {
                        "name": "unbekannt",
                        "alias": "unbekannt",
                        "description": "unbekannt",
                    },
                },
                "typename": "WP_Baualtersklasse",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    nutzflaeche: Annotated[
        definitions.GenericMeasure | None,
        Field(
            description="Gesamtnutzfläche der Gebäude im Baublock in Hektar",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "ha",
            },
        ),
    ] = None
    anzahlAnschluesseWaermeNetz: Annotated[
        int | None,
        Field(
            description="Anzahl der Hausanschlüsse an ein Wärmenetz",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class WPWaermeverbrauch(WPBaublock):
    """Baublockbezogene Informationen zum Wärmeverbrauch entsprechend WPG Anlage 2 I.2.1 und I.2.3 sowie darüber hinausgehende optionale Informationen"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    verbrauchsDichte: Annotated[
        definitions.GenericMeasure,
        Field(
            description="Wärmeverbrauch in Megawattstunden pro Hektar und Jahr",
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "multiplicity": "1",
                "uom": "MWh/(ha*a)",
            },
        ),
    ]
    energietraegerVerbrauch: Annotated[
        list[WPEnergieTraegerMenge],
        Field(
            description="Jährlicher Endenergieverbrauch für Wärme je Energieträger",
            json_schema_extra={
                "typename": "WP_EnergieTraegerMenge",
                "stereotype": "DataType",
                "multiplicity": "1..*",
            },
            min_length=1,
        ),
    ]


class WPWaermeversorgungsartZieljahr(WPBeplantesTeilgebiet):
    """Eignungsstufen der Wärmeversorgungsarten für das Zieljahr entsprechend WPG Anlage 2 V. (und  WPG  § 28  Abs. 2)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    eignungDezentraleVersorgung: Annotated[
        Literal["1000", "2000", "3000", "4000"],
        Field(
            description="Eigenungsstufen für die dezentrale Versorgung",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "SehrWahrscheinlichGeeignet",
                        "alias": "sehr wahrscheinlich geeignet",
                        "description": "sehr wahrscheinlich geeignet",
                    },
                    "2000": {
                        "name": "WahrscheinlichGeeignet",
                        "alias": "wahrscheinlich geeignet",
                        "description": "wahrscheinlich geeignet",
                    },
                    "3000": {
                        "name": "WahrscheinlichUngeeignet",
                        "alias": "wahrscheinlich ungeeignet",
                        "description": "wahrscheinlich ungeeignet",
                    },
                    "4000": {
                        "name": "SehrWahrscheinlichUngeeignet",
                        "alias": "sehr wahrscheinlich ungeeignet",
                        "description": "sehr wahrscheinlich ungeeignet",
                    },
                },
                "typename": "WP_Eignungsstufe",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    eignungWaermenetz: Annotated[
        Literal["1000", "2000", "3000", "4000"],
        Field(
            description="Eignungsstufen für Versorgung über ein Wärmenetz",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "SehrWahrscheinlichGeeignet",
                        "alias": "sehr wahrscheinlich geeignet",
                        "description": "sehr wahrscheinlich geeignet",
                    },
                    "2000": {
                        "name": "WahrscheinlichGeeignet",
                        "alias": "wahrscheinlich geeignet",
                        "description": "wahrscheinlich geeignet",
                    },
                    "3000": {
                        "name": "WahrscheinlichUngeeignet",
                        "alias": "wahrscheinlich ungeeignet",
                        "description": "wahrscheinlich ungeeignet",
                    },
                    "4000": {
                        "name": "SehrWahrscheinlichUngeeignet",
                        "alias": "sehr wahrscheinlich ungeeignet",
                        "description": "sehr wahrscheinlich ungeeignet",
                    },
                },
                "typename": "WP_Eignungsstufe",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    eignungWasserstoffnetz: Annotated[
        Literal["1000", "2000", "3000", "4000"],
        Field(
            description="Eignungsstufen für Versorgung über ein Wasserstoffnetz",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "SehrWahrscheinlichGeeignet",
                        "alias": "sehr wahrscheinlich geeignet",
                        "description": "sehr wahrscheinlich geeignet",
                    },
                    "2000": {
                        "name": "WahrscheinlichGeeignet",
                        "alias": "wahrscheinlich geeignet",
                        "description": "wahrscheinlich geeignet",
                    },
                    "3000": {
                        "name": "WahrscheinlichUngeeignet",
                        "alias": "wahrscheinlich ungeeignet",
                        "description": "wahrscheinlich ungeeignet",
                    },
                    "4000": {
                        "name": "SehrWahrscheinlichUngeeignet",
                        "alias": "sehr wahrscheinlich ungeeignet",
                        "description": "sehr wahrscheinlich ungeeignet",
                    },
                },
                "typename": "WP_Eignungsstufe",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    eignungGruenesMethan: Annotated[
        Literal["1000", "2000", "3000", "4000"] | None,
        Field(
            description="Eignungsstufen für Versorgung mit grünem Methan",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "SehrWahrscheinlichGeeignet",
                        "alias": "sehr wahrscheinlich geeignet",
                        "description": "sehr wahrscheinlich geeignet",
                    },
                    "2000": {
                        "name": "WahrscheinlichGeeignet",
                        "alias": "wahrscheinlich geeignet",
                        "description": "wahrscheinlich geeignet",
                    },
                    "3000": {
                        "name": "WahrscheinlichUngeeignet",
                        "alias": "wahrscheinlich ungeeignet",
                        "description": "wahrscheinlich ungeeignet",
                    },
                    "4000": {
                        "name": "SehrWahrscheinlichUngeeignet",
                        "alias": "sehr wahrscheinlich ungeeignet",
                        "description": "sehr wahrscheinlich ungeeignet",
                    },
                },
                "typename": "WP_Eignungsstufe",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class WPWaermversorgungsgebiet(WPBeplantesTeilgebiet):
    """Abstrakte Oberklasse für Wärmeversorgungsgebiete. Die räumliche Einteilung in konkrete Wärmeversorgungsgebiete für die Betrachtungszeitpunkte ist variabel."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
    versorgungsart: Annotated[
        Literal["1000", "10001", "10002", "10003", "2000", "3000", "4000"],
        Field(
            description="Geplante Art der Wärmeversorgung für das betrachtete Gebiet",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Waermenetzgebiet",
                        "alias": "Wärmenetzgebiet",
                        "description": "Beplantes Teilgebiet, in dem ein Wärmenetz besteht oder geplant ist und ein erheblicher Anteil der ansässigen Letztverbraucher über das Wärmenetz versorgt werden soll.",
                    },
                    "10001": {
                        "name": "Waermenetzverdichtungsgebiet",
                        "alias": "Wärmenetzverdichtungsgebiet",
                        "description": "Beplantes Teilgebiet, in dem Letztverbraucher, die sich in unmittelbarer Nähe zu einem bestehenden Wärmenetz befinden, mit diesem verbunden werden sollen, ohne dass hierfür der Ausbau des Wärmenetzes erforderlich würde.",
                    },
                    "10002": {
                        "name": "Waermenetzausbaugebiet",
                        "alias": "Wärmenetzausbaugebiet",
                        "description": "Beplantes Teilgebiet, in dem es bislang kein Wärmenetz gibt und das durch den Neubau von Wärmeleitungen erstmals an ein bestehendes Wärmenetz angeschlossen werden soll.",
                    },
                    "10003": {
                        "name": "Waemenetzneubaugebiet",
                        "alias": "Wärmenetzneubaugebiet",
                        "description": "Beplantes Teilgebiet, das an ein neues Wärmenetz angeschlossen werden soll.",
                    },
                    "2000": {
                        "name": "Wasserstoffnetzgebiet",
                        "alias": "Wasserstoffnetzgebiet",
                        "description": "Beplantes Teilgebiet, in dem ein Wasserstoffnetz besteht oder geplant ist und ein erheblicher Anteil der ansässigen Letztverbraucher über das Wasserstoffnetz zum Zweck der Wärmeerzeugung versorgt werden soll.",
                    },
                    "3000": {
                        "name": "GebietDezentrWaeVersorgung",
                        "alias": "Gebiet der dezentralen Wärmeversorgung",
                        "description": "Beplantes Teilgebiet, das überwiegend nicht über ein Wärme- oder ein Gasnetz versorgt werden soll.",
                    },
                    "4000": {
                        "name": "Pruefgebiet",
                        "alias": "Prüfgebiet",
                        "description": "Beplantes Teilgebiet, das nicht in ein voraussichtliches Wärmeversorgungsgebiet eingeteilt werden soll, weil die für eine Einteilung erforderlichen Umstände noch nicht ausreichend bekannt sind oder weil ein erheblicher Anteil der ansässigen Letztverbraucher auf andere Art mit Wärme versorgt werden soll.",
                    },
                },
                "typename": "WP_WaermeversorgungTyp",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    energietraegerVerbrauch: Annotated[
        list[WPEnergieTraegerMenge] | None,
        Field(
            description="Jährlicher Endenergieverbrauch für Wärme je Energieträger",
            json_schema_extra={
                "typename": "WP_EnergieTraegerMenge",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None


class WPWaermeversorgungsgebiet2030(WPWaermversorgungsgebiet):
    """Einteilung des beplanten Gebiets in voraussichtliche Wärmeversorgungsgebiete in 2030 entsprechend WPG Anlage 2 IV."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"


class WPWaermeversorgungsgebiet2035(WPWaermversorgungsgebiet):
    """Einteilung des beplanten Gebiets in voraussichtliche Wärmeversorgungsgebiete in 2035 entsprechend WPG Anlage 2 IV."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"


class WPWaermeversorgungsgebiet2040(WPWaermversorgungsgebiet):
    """Einteilung des beplanten Gebiets in voraussichtliche Wärmeversorgungsgebiete in 2040 entsprechend WPG Anlage 2 IV."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"


class WPWaermeversorgungsgebietZieljahr(WPWaermversorgungsgebiet):
    """Einteilung des beplanten Gebiets in voraussichtliche Wärmeversorgungsgebiete im Zieljahr entsprechend WPG Anlage 2 IV."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xwaermeplan.de/0/9"
    stereotype: ClassVar[str] = "FeatureType"
