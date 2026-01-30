# generated from JSON Schema


from __future__ import annotations

from datetime import date as date_aliased
from datetime import timedelta
from typing import Annotated, Any, ClassVar, Literal
from uuid import UUID

from pydantic import AnyUrl, Field, RootModel

from ..base import BaseFeature
from . import definitions


class Model(RootModel[Any]):
    root: Annotated[
        Any,
        Field(
            json_schema_extra={
                "full_name": "XPlanGML 4.1",
                "prefix": "xplan",
                "full_version": "4.1",
                "namespace_uri": "http://www.xplanung.de/xplangml/4/1",
            }
        ),
    ]


class BPTiefeProzentualBezugTypen(RootModel[Literal["1000", "9999"]]):
    root: Annotated[
        Literal["1000", "9999"],
        Field(
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Gebaeudehoehe"},
                    "9999": {"name": "Unbestimmt"},
                }
            }
        ),
    ]


class BPWirksamkeitBedingung(BaseFeature):
    """Spezifikation von Bedingungen für die Wirksamkeit oder Unwirksamkeit einer Festsetzung."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "DataType"
    bedingung: Annotated[
        str | None,
        Field(
            description="Textlich formulierte Bedingung für die Wirksamkeit oder Unwirksamkeit einer Festsetzung.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    datumAbsolut: Annotated[
        date_aliased | None,
        Field(
            description="Datum an dem eine Festsetzung wirksam oder unwirksam wird.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    datumRelativ: Annotated[
        timedelta | None,
        Field(
            description="Zeitspanne, nach der eine Festsetzung wirksam oder unwirksam wird, wenn die im Attribut bedingung spezifizierte Bedingung erfüllt ist.",
            json_schema_extra={
                "typename": "TM_Duration",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class LPSchutzgebietDetailTypen(RootModel[AnyUrl]):
    root: AnyUrl


class LPSonstigeAbgrenzuung(BaseFeature):
    """false"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    id: str | None = None


class VegetationsobjektTypen(RootModel[AnyUrl]):
    root: AnyUrl


class XPBereich(BaseFeature):
    """Abstrakte Oberklasse für die Modellierung von Planbereichen. Ein Planbereich fasst die Inhalte eines Plans nach bestimmten Kriterien zusammen."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    id: str | None = None
    nummer: Annotated[
        int,
        Field(
            description="Nummer des Bereichs. Wenn der Bereich als Ebene eines BPlans interpretiert wird, kann aus dem Attribut die vertikale Reihenfolge der Ebenen rekonstruiert werden.",
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
        Literal[
            "1000",
            "1500",
            "1600",
            "1650",
            "1700",
            "1800",
            "2000",
            "2500",
            "3000",
            "3500",
            "4000",
            "9999",
        ]
        | None,
        Field(
            description="Spezifikation der semantischen Bedeutung eines Bereiches.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Aenderungsbereich"},
                    "1500": {"name": "Ergaenzungsbereich"},
                    "1600": {"name": "Teilbereich"},
                    "1650": {"name": "Gesamtbereich", "description": "Gesamtbereich"},
                    "1700": {"name": "Eingriffsbereich"},
                    "1800": {"name": "Ausgleichsbereich"},
                    "2000": {"name": "Nebenzeichnung"},
                    "2500": {"name": "Variante"},
                    "3000": {"name": "VertikaleGliederung"},
                    "3500": {"name": "Erstnutzung"},
                    "4000": {"name": "Folgenutzung"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "XP_BedeutungenBereich",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteBedeutung: Annotated[
        str | None,
        Field(
            description="Detaillierte Erklärung der semantischen Bedeutung eines Bereiches, in Ergänzung des Attributs bedeutung.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    erstellungsMasstab: Annotated[
        int | None,
        Field(
            description="Der bei der Erstellung der Inhalte des Planbereichs benutzte Kartenmassstab. Wenn dieses Attribut nicht spezifiziert ist, gilt für den Bereich der auf Planebene (XP_Plan) spezifizierte Masstab.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    geltungsbereich: Annotated[
        definitions.Polygon | definitions.MultiPolygon | None,
        Field(
            description="Räumliche Abgrenzung des Bereiches. Wenn dieses Attribut nicht spezifiziert ist, gilt für den Bereich der auf Planebene (XP_Plan) spezifizierte Geltungsbereich.",
            json_schema_extra={
                "typename": "XP_Flaechengeometrie",
                "stereotype": "Geometry",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    nachrichtlich: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": [
                    "BP_AbgrabungsFlaeche",
                    "BP_AbstandsFlaeche",
                    "BP_AbstandsMass",
                    "BP_AnpflanzungBindungErhaltung",
                    "BP_AufschuettungsFlaeche",
                    "BP_AusgleichsFlaeche",
                    "BP_AusgleichsMassnahme",
                    "BP_BauGrenze",
                    "BP_BauLinie",
                    "BP_Baugebiet",
                    "BP_BaugebietsTeilFlaeche",
                    "BP_BereichOhneEinAusfahrtLinie",
                    "BP_BesondererNutzungszweckFlaeche",
                    "BP_BodenschaetzeFlaeche",
                    "BP_DenkmalschutzEinzelanlage",
                    "BP_DenkmalschutzEnsembleFlaeche",
                    "BP_EinfahrtPunkt",
                    "BP_EinfahrtsbereichLinie",
                    "BP_EingriffsBereich",
                    "BP_ErhaltungsBereichFlaeche",
                    "BP_ErneuerbareEnergieFlaeche",
                    "BP_FestsetzungNachLandesrecht",
                    "BP_FirstRichtungsLinie",
                    "BP_FoerderungsFlaeche",
                    "BP_FreiFlaeche",
                    "BP_GebaeudeFlaeche",
                    "BP_GemeinbedarfsFlaeche",
                    "BP_GemeinschaftsanlagenFlaeche",
                    "BP_GemeinschaftsanlagenZuordnung",
                    "BP_GenerischesObjekt",
                    "BP_GewaesserFlaeche",
                    "BP_GruenFlaeche",
                    "BP_HoehenMass",
                    "BP_Immissionsschutz",
                    "BP_KennzeichnungsFlaeche",
                    "BP_KleintierhaltungFlaeche",
                    "BP_Landwirtschaft",
                    "BP_LuftreinhalteFlaeche",
                    "BP_NebenanlagenAusschlussFlaeche",
                    "BP_NebenanlagenFlaeche",
                    "BP_NutzungsartenGrenze",
                    "BP_PersGruppenBestimmteFlaeche",
                    "BP_RegelungVergnuegungsstaetten",
                    "BP_RekultivierungsFlaeche",
                    "BP_SchutzPflegeEntwicklungsFlaeche",
                    "BP_SchutzPflegeEntwicklungsMassnahme",
                    "BP_Schutzgebiet",
                    "BP_SpezielleBauweise",
                    "BP_SpielSportanlagenFlaeche",
                    "BP_StrassenVerkehrsFlaeche",
                    "BP_StrassenbegrenzungsLinie",
                    "BP_Strassenkoerper",
                    "BP_TextlicheFestsetzungsFlaeche",
                    "BP_UeberbaubareGrundstuecksFlaeche",
                    "BP_UnverbindlicheVormerkung",
                    "BP_VerEntsorgung",
                    "BP_Veraenderungssperre",
                    "BP_VerkehrsflaecheBesondererZweckbestimmung",
                    "BP_WaldFlaeche",
                    "BP_WasserwirtschaftsFlaeche",
                    "BP_Wegerecht",
                    "FP_Abgrabung",
                    "FP_AbgrabungsFlaeche",
                    "FP_AnpassungKlimawandel",
                    "FP_Aufschuettung",
                    "FP_AufschuettungsFlaeche",
                    "FP_AusgleichsFlaeche",
                    "FP_BebauungsFlaeche",
                    "FP_Bodenschaetze",
                    "FP_BodenschaetzeFlaeche",
                    "FP_Gemeinbedarf",
                    "FP_GenerischesObjekt",
                    "FP_Gewaesser",
                    "FP_Gruen",
                    "FP_KeineZentrAbwasserBeseitigungFlaeche",
                    "FP_Kennzeichnung",
                    "FP_LandwirtschaftsFlaeche",
                    "FP_NutzungsbeschraenkungsFlaeche",
                    "FP_PrivilegiertesVorhaben",
                    "FP_SchutzPflegeEntwicklung",
                    "FP_SpielSportanlage",
                    "FP_Strassenverkehr",
                    "FP_TextlicheDarstellungsFlaeche",
                    "FP_UnverbindlicheVormerkung",
                    "FP_VerEntsorgung",
                    "FP_VorbehalteFlaeche",
                    "FP_WaldFlaeche",
                    "FP_Wasserwirtschaft",
                    "FP_ZentralerVersorgungsbereich",
                    "LP_Abgrenzung",
                    "LP_AllgGruenflaeche",
                    "LP_AnpflanzungBindungErhaltung",
                    "LP_Ausgleich",
                    "LP_Biotopverbundflaeche",
                    "LP_Bodenschutzrecht",
                    "LP_Denkmalschutzrecht",
                    "LP_ErholungFreizeit",
                    "LP_Forstrecht",
                    "LP_GenerischesObjekt",
                    "LP_Landschaftsbild",
                    "LP_NutzungsAusschluss",
                    "LP_NutzungserfordernisRegelung",
                    "LP_PlanerischeVertiefung",
                    "LP_SchutzPflegeEntwicklung",
                    "LP_SchutzobjektBundesrecht",
                    "LP_SchutzobjektInternatRecht",
                    "LP_SonstigesRecht",
                    "LP_TextlicheFestsetzungsFlaeche",
                    "LP_WasserrechtGemeingebrEinschraenkungNaturschutz",
                    "LP_WasserrechtSchutzgebiet",
                    "LP_WasserrechtSonstige",
                    "LP_WasserrechtWirtschaftAbflussHochwSchutz",
                    "LP_ZuBegruenendeGrundstueckflaeche",
                    "LP_Zwischennutzung",
                    "RP_Achse",
                    "RP_Bodenschutz",
                    "RP_Energieversorgung",
                    "RP_Entsorgung",
                    "RP_Forstwirtschaft",
                    "RP_FreizeitErholung",
                    "RP_GemeindeFunktionSiedlungsentwicklung",
                    "RP_GenerischesObjekt",
                    "RP_Gewaesser",
                    "RP_Grenze",
                    "RP_GruenzugGruenzaesur",
                    "RP_Klimaschutz",
                    "RP_Kommunikation",
                    "RP_KulturellesSachgut",
                    "RP_Landwirtschaft",
                    "RP_NaturLandschaft",
                    "RP_NaturschutzrechtlichesSchutzgebiet",
                    "RP_Raumkategorie",
                    "RP_Rohstoffsicherung",
                    "RP_SonstigeInfrastruktur",
                    "RP_SonstigeSiedlungsstruktur",
                    "RP_SonstigerFreiraumstruktur",
                    "RP_SozialeInfrastruktur",
                    "RP_Sperrgebiet",
                    "RP_Verkehr",
                    "RP_VorbHochwasserschutz",
                    "RP_Wasserschutz",
                    "RP_Wasserwirtschaft",
                    "RP_Windenergienutzung",
                    "RP_ZentralerOrt",
                    "SO_Bodenschutzrecht",
                    "SO_Denkmalschutzrecht",
                    "SO_Forstrecht",
                    "SO_Gebiet",
                    "SO_Grenze",
                    "SO_Linienobjekt",
                    "SO_Luftverkehrsrecht",
                    "SO_Objekt",
                    "SO_Schienenverkehrsrecht",
                    "SO_SchutzgebietNaturschutzrecht",
                    "SO_SchutzgebietSonstigesRecht",
                    "SO_SchutzgebietWasserrecht",
                    "SO_SonstigesRecht",
                    "SO_Strassenverkehrsrecht",
                    "SO_Wasserrecht",
                ],
                "stereotype": "Association",
                "reverseProperty": "gehoertNachrichtlichZuBereich",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            }
        ),
    ] = None
    praesentationsobjekt: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": [
                    "XP_FPO",
                    "XP_LPO",
                    "XP_LTO",
                    "XP_Nutzungsschablone",
                    "XP_PPO",
                    "XP_PTO",
                    "XP_Praesentationsobjekt",
                ],
                "stereotype": "Association",
                "reverseProperty": "gehoertZuBereich",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            }
        ),
    ] = None
    rasterBasis: Annotated[
        AnyUrl | UUID | None,
        Field(
            json_schema_extra={
                "typename": "XP_RasterplanBasis",
                "stereotype": "Association",
                "multiplicity": "0..1",
            }
        ),
    ] = None


class XPDatumAttribut(BaseFeature):
    """Generische Attribute vom Datentyp "Datum" """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "DataType"
    name: Annotated[
        str,
        Field(
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            }
        ),
    ]
    wert: Annotated[
        date_aliased,
        Field(
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "1",
            }
        ),
    ]


class XPDoubleAttribut(BaseFeature):
    """Generisches Attribut vom Datentyp "Double"."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "DataType"
    name: Annotated[
        str,
        Field(
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            }
        ),
    ]
    wert: Annotated[
        float,
        Field(
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "1",
            }
        ),
    ]


class XPGemeinde(BaseFeature):
    """Spezifikation einer Gemeinde"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "DataType"
    ags: Annotated[
        str | None,
        Field(
            description="Amtlicher Gemeindsschlüssel (früher Gemeinde-Kennziffer)",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    rs: Annotated[
        str | None,
        Field(
            description="Regionalschlüssel",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gemeindeName: Annotated[
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
    ortsteilName: Annotated[
        str | None,
        Field(
            description="Name des Ortsteils",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class XPHoehenangabe(BaseFeature):
    """Spezifikation einer Angabe zur vertikalen Höhe oder zu einem Bereich vertikaler Höhen. Es ist möglich, spezifische Höhenangaben (z.B. die First- oder Traufhöhe eines Gebäudes) vorzugeben oder einzuschränken, oder den Gültigkeitsbereich eines Planinhalts auf eine bestimmte Höhe (hZwingend) bzw. einen Höhenbereich (hMin - hMax) zu beschränken, was vor allem bei der höhenabhängigen Festsetzung einer überbaubaren Grundstücksfläche (BP_UeberbaubareGrundstuecksflaeche), einer Baulinie (BP_Baulinie) oder einer Baugrenze (BP_Baugrenze) relevant ist. In diesem Fall bleibt das Attribut bezugspunkt unbelegt."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "DataType"
    abweichenderHoehenbezug: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            }
        ),
    ] = None
    hoehenbezug: Annotated[
        Literal["1000", "2000", "2500", "3000"] | None,
        Field(
            description="Art des Höhenbezuges.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "absolutNHN",
                        "description": "Absolute Höhenangabe",
                    },
                    "2000": {
                        "name": "relativGelaendeoberkante",
                        "description": "Höhenangabe relativ zur Geländeoberkante an der Position des Planinhalts.",
                    },
                    "2500": {
                        "name": "relativGehwegOberkante",
                        "description": "Höhenangabe relativ zur Gehweg-Oberkante an der Position des Planinhalts.",
                    },
                    "3000": {
                        "name": "relativBezugshoehe",
                        "description": "Höhenangabe relativ zu der auf Planebene festgelegten absoluten Bezugshöhe (Attribut bezugshoehe von XP_Plan).",
                    },
                },
                "typename": "XP_ArtHoehenbezug",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    bezugspunkt: Annotated[
        Literal["1000", "2000", "3000", "3500", "4000", "4500", "5000", "5500", "6000"]
        | None,
        Field(
            description="Bestimmung des Bezugspunktes der Höhenangaben. Wenn dies Attribut nicht belegt ist, soll die Höhenangabe als verikale Einschränkung des zugeordneten Planinhalts interpretiert werden.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "TH",
                        "description": "Traufhöhe als Höhenbezugspunkt",
                    },
                    "2000": {
                        "name": "FH",
                        "description": "Firsthöhe als Höhenbezugspunkt.",
                    },
                    "3000": {
                        "name": "OK",
                        "description": "Oberkante als Höhenbezugspunkt.",
                    },
                    "3500": {"name": "LH", "description": "Lichte Höhe"},
                    "4000": {"name": "SH", "description": "Sockelhöhe"},
                    "4500": {"name": "EFH", "description": "Erdgeschoss Fußbodenhöhe"},
                    "5000": {"name": "HBA", "description": "Höhe Baulicher Anlagen"},
                    "5500": {"name": "UK", "description": "Unterkante"},
                    "6000": {"name": "GBH", "description": "Gebäudehöhe"},
                },
                "typename": "XP_ArtHoehenbezugspunkt",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    hMin: Annotated[
        definitions.Length | None,
        Field(
            description="Minimal zulassige Höhe des Bezugspunktes (bezugspunkt) bei einer Bereichsangabe, bzw. untere Grenze des vertikalen Gültigkeitsbereiches eines Planinhalts, wenn bezugspunkt nicht belegt ist. In diesem Fall gilt: Ist  hMax nicht belegt, gilt die Festlegung ab der Höhe hMin.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    hMax: Annotated[
        definitions.Length | None,
        Field(
            description="Maximal zulässige Höhe des Bezugspunktes (bezugspunkt) bei einer Bereichsangabe, bzw. obere Grenze des vertikalen Gültigkeitsbereiches eines Planinhalts, wenn bezugspunkt nicht belegt ist.  In diesem Fall gilt: Ist  hMin nicht belegt, gilt die Festlegung bis zur Höhe hMax.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    hZwingend: Annotated[
        definitions.Length | None,
        Field(
            description="Zwingend einzuhaltende Höhe des Bezugspunktes (bezugspunkt) , bzw. Beschränkung der vertikalen Gültigkeitsbereiches eines Planinhalts auf eine bestimmte Höhe.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    h: Annotated[
        definitions.Length | None,
        Field(
            description="Maximal zulässige Höhe des Bezugspunktes (bezugspunkt) .",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None


class XPIntegerAttribut(BaseFeature):
    """Generische Attribute vom Datentyp "Integer"."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "DataType"
    name: Annotated[
        str,
        Field(
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            }
        ),
    ]
    wert: Annotated[
        int,
        Field(
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "1",
            }
        ),
    ]


class XPPlangeber(BaseFeature):
    """Spezifikation der Institution, die für den Plan verantwortlich ist."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "DataType"
    name: Annotated[
        str,
        Field(
            description="Name des Plangebers.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    kennziffer: Annotated[
        str | None,
        Field(
            description="Kennziffer des Plangebers.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class XPStringAttribut(BaseFeature):
    """Generisches Attribut vom Datentyp "CharacterString" """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "DataType"
    name: Annotated[
        str,
        Field(
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            }
        ),
    ]
    wert: Annotated[
        str,
        Field(
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            }
        ),
    ]


class XPURLAttribut(BaseFeature):
    """Generische Attribute vom Datentyp "URL" """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "DataType"
    name: Annotated[
        str,
        Field(
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            }
        ),
    ]
    wert: Annotated[
        AnyUrl,
        Field(
            json_schema_extra={
                "typename": "URI",
                "stereotype": "BasicType",
                "multiplicity": "1",
            }
        ),
    ]


class XPVerbundenerPlan(BaseFeature):
    """Spezifikation eines anderen Plans, der mit dem Ausgangsplan verbunden ist und diesen ändert bzw. von ihm geändert wird."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "DataType"
    planName: Annotated[
        str,
        Field(
            description="Name (Attribut name von XP_Plan) des verbundenen Plans.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    rechtscharakter: Annotated[
        Literal["1000", "1100", "2000"],
        Field(
            description="Rechtscharakter der Planänderung.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Aenderung", "description": "Änderung des Plans"},
                    "1100": {
                        "name": "Ergaenzung",
                        "description": "Ergänzung eines Plans",
                    },
                    "2000": {"name": "Aufhebung", "description": "Aufhebung des Plans"},
                },
                "typename": "XP_RechtscharakterPlanaenderung",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    nummer: Annotated[
        str | None,
        Field(
            description="Nummer des verbundenen Plans",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class XPVerfahrensMerkmal(BaseFeature):
    """Vermerk eines am Planungsverfahrens beteiligten Akteurs."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "DataType"
    vermerk: Annotated[
        str,
        Field(
            description="Inhat des Vermerks",
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
            description="Datum des Vermerks",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "1",
            },
        ),
    ]
    signatur: Annotated[
        str,
        Field(
            description="Unterschrift",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    signiert: Annotated[
        bool,
        Field(
            description="Angabe, ob die Unterschrift erfolgt ist.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]


class BPBereich(XPBereich):
    """Diese Klasse modelliert einen Bereich eines Bebauungsplans, z.B. eine vertikale Ebene."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    versionBauNVO: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"] | None,
        Field(
            description="Benutzte Version der BauNVO",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Version_1962"},
                    "2000": {"name": "Version_1968"},
                    "3000": {"name": "Version_1977"},
                    "4000": {"name": "Version_1990"},
                    "9999": {"name": "AndereGesetzlicheBestimmung"},
                },
                "typename": "XP_VersionBauNVO",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    versionBauNVOText: Annotated[
        str | None,
        Field(
            description="Textliche Spezifikation einer anderen Gesetzesgrundlage als der BauNVO. In diesem Fall muss das Attribut versionBauNVO den Wert 9999 haben.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    versionBauGB: Annotated[
        date_aliased | None,
        Field(
            description="Datum der zugrunde liegenden Version des BauGB.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    versionBauGBText: Annotated[
        str | None,
        Field(
            description="Zugrunde liegende Version des BauGB.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gehoertZuPlan: Annotated[
        AnyUrl | UUID,
        Field(
            json_schema_extra={
                "typename": "BP_Plan",
                "stereotype": "Association",
                "reverseProperty": "bereich",
                "sourceOrTarget": "source",
                "multiplicity": "1",
            }
        ),
    ]
    inhaltBPlan: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": [
                    "BP_AbgrabungsFlaeche",
                    "BP_AbstandsFlaeche",
                    "BP_AbstandsMass",
                    "BP_AnpflanzungBindungErhaltung",
                    "BP_AufschuettungsFlaeche",
                    "BP_AusgleichsFlaeche",
                    "BP_AusgleichsMassnahme",
                    "BP_BauGrenze",
                    "BP_BauLinie",
                    "BP_Baugebiet",
                    "BP_BaugebietsTeilFlaeche",
                    "BP_BereichOhneEinAusfahrtLinie",
                    "BP_BesondererNutzungszweckFlaeche",
                    "BP_BodenschaetzeFlaeche",
                    "BP_DenkmalschutzEinzelanlage",
                    "BP_DenkmalschutzEnsembleFlaeche",
                    "BP_EinfahrtPunkt",
                    "BP_EinfahrtsbereichLinie",
                    "BP_EingriffsBereich",
                    "BP_ErhaltungsBereichFlaeche",
                    "BP_ErneuerbareEnergieFlaeche",
                    "BP_FestsetzungNachLandesrecht",
                    "BP_FirstRichtungsLinie",
                    "BP_FoerderungsFlaeche",
                    "BP_FreiFlaeche",
                    "BP_GebaeudeFlaeche",
                    "BP_GemeinbedarfsFlaeche",
                    "BP_GemeinschaftsanlagenFlaeche",
                    "BP_GemeinschaftsanlagenZuordnung",
                    "BP_GenerischesObjekt",
                    "BP_GewaesserFlaeche",
                    "BP_GruenFlaeche",
                    "BP_HoehenMass",
                    "BP_Immissionsschutz",
                    "BP_KennzeichnungsFlaeche",
                    "BP_KleintierhaltungFlaeche",
                    "BP_Landwirtschaft",
                    "BP_LuftreinhalteFlaeche",
                    "BP_NebenanlagenAusschlussFlaeche",
                    "BP_NebenanlagenFlaeche",
                    "BP_NutzungsartenGrenze",
                    "BP_PersGruppenBestimmteFlaeche",
                    "BP_RegelungVergnuegungsstaetten",
                    "BP_RekultivierungsFlaeche",
                    "BP_SchutzPflegeEntwicklungsFlaeche",
                    "BP_SchutzPflegeEntwicklungsMassnahme",
                    "BP_Schutzgebiet",
                    "BP_SpezielleBauweise",
                    "BP_SpielSportanlagenFlaeche",
                    "BP_StrassenVerkehrsFlaeche",
                    "BP_StrassenbegrenzungsLinie",
                    "BP_Strassenkoerper",
                    "BP_TextlicheFestsetzungsFlaeche",
                    "BP_UeberbaubareGrundstuecksFlaeche",
                    "BP_UnverbindlicheVormerkung",
                    "BP_VerEntsorgung",
                    "BP_Veraenderungssperre",
                    "BP_VerkehrsflaecheBesondererZweckbestimmung",
                    "BP_WaldFlaeche",
                    "BP_WasserwirtschaftsFlaeche",
                    "BP_Wegerecht",
                ],
                "stereotype": "Association",
                "reverseProperty": "gehoertZuBP_Bereich",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            }
        ),
    ] = None
    rasterAenderung: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "BP_RasterplanAenderung",
                "stereotype": "Association",
                "multiplicity": "0..*",
            }
        ),
    ] = None


class FPBereich(XPBereich):
    """Diese Klasse modelliert einen Bereich eines Flächennutzungsplans."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    versionBauNVO: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"] | None,
        Field(
            description="Benutzte Version der BauNVO",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Version_1962"},
                    "2000": {"name": "Version_1968"},
                    "3000": {"name": "Version_1977"},
                    "4000": {"name": "Version_1990"},
                    "9999": {"name": "AndereGesetzlicheBestimmung"},
                },
                "typename": "XP_VersionBauNVO",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    versionBauNVOText: Annotated[
        str | None,
        Field(
            description="Textliche Spezifikation einer anderen Gesetzesgrundlage als der BauNVO. In diesem Fall muss das Attribut versionBauNVO den Wert 9999 haben.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    versionBauGB: Annotated[
        date_aliased | None,
        Field(
            description="Datum der zugrunde liegenden Version des BauGB.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    versionBauGBText: Annotated[
        str | None,
        Field(
            description="Zugrunde liegende Version des BauGB.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gehoertZuPlan: Annotated[
        AnyUrl | UUID,
        Field(
            json_schema_extra={
                "typename": "FP_Plan",
                "stereotype": "Association",
                "reverseProperty": "bereich",
                "sourceOrTarget": "target",
                "multiplicity": "1",
            }
        ),
    ]
    inhaltFPlan: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": [
                    "FP_Abgrabung",
                    "FP_AbgrabungsFlaeche",
                    "FP_AnpassungKlimawandel",
                    "FP_Aufschuettung",
                    "FP_AufschuettungsFlaeche",
                    "FP_AusgleichsFlaeche",
                    "FP_BebauungsFlaeche",
                    "FP_Bodenschaetze",
                    "FP_BodenschaetzeFlaeche",
                    "FP_Gemeinbedarf",
                    "FP_GenerischesObjekt",
                    "FP_Gewaesser",
                    "FP_Gruen",
                    "FP_KeineZentrAbwasserBeseitigungFlaeche",
                    "FP_Kennzeichnung",
                    "FP_LandwirtschaftsFlaeche",
                    "FP_NutzungsbeschraenkungsFlaeche",
                    "FP_PrivilegiertesVorhaben",
                    "FP_SchutzPflegeEntwicklung",
                    "FP_SpielSportanlage",
                    "FP_Strassenverkehr",
                    "FP_TextlicheDarstellungsFlaeche",
                    "FP_UnverbindlicheVormerkung",
                    "FP_VerEntsorgung",
                    "FP_VorbehalteFlaeche",
                    "FP_WaldFlaeche",
                    "FP_Wasserwirtschaft",
                    "FP_ZentralerVersorgungsbereich",
                ],
                "stereotype": "Association",
                "reverseProperty": "gehoertZuFP_Bereich",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            }
        ),
    ] = None
    rasterAenderung: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "FP_RasterplanAenderung",
                "stereotype": "Association",
                "multiplicity": "0..*",
            }
        ),
    ] = None


class LPBereich(XPBereich):
    """Ein Bereich eines Landschaftsplans."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gehoertZuPlan: Annotated[
        AnyUrl | UUID,
        Field(
            json_schema_extra={
                "typename": "LP_Plan",
                "stereotype": "Association",
                "reverseProperty": "bereich",
                "sourceOrTarget": "source",
                "multiplicity": "1",
            }
        ),
    ]
    inhaltLPlan: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": [
                    "LP_Abgrenzung",
                    "LP_AllgGruenflaeche",
                    "LP_AnpflanzungBindungErhaltung",
                    "LP_Ausgleich",
                    "LP_Biotopverbundflaeche",
                    "LP_Bodenschutzrecht",
                    "LP_Denkmalschutzrecht",
                    "LP_ErholungFreizeit",
                    "LP_Forstrecht",
                    "LP_GenerischesObjekt",
                    "LP_Landschaftsbild",
                    "LP_NutzungsAusschluss",
                    "LP_NutzungserfordernisRegelung",
                    "LP_PlanerischeVertiefung",
                    "LP_SchutzPflegeEntwicklung",
                    "LP_SchutzobjektBundesrecht",
                    "LP_SchutzobjektInternatRecht",
                    "LP_SonstigesRecht",
                    "LP_TextlicheFestsetzungsFlaeche",
                    "LP_WasserrechtGemeingebrEinschraenkungNaturschutz",
                    "LP_WasserrechtSchutzgebiet",
                    "LP_WasserrechtSonstige",
                    "LP_WasserrechtWirtschaftAbflussHochwSchutz",
                    "LP_ZuBegruenendeGrundstueckflaeche",
                    "LP_Zwischennutzung",
                ],
                "stereotype": "Association",
                "reverseProperty": "gehoertZuLP_Bereich",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            }
        ),
    ] = None
    rasterAenderung: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "LP_RasterplanAenderung",
                "stereotype": "Association",
                "multiplicity": "0..*",
            }
        ),
    ] = None


class RPBereich(XPBereich):
    """Die Klasse modelliert einen Bereich eines Regionalplans,"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    versionBROG: Annotated[
        date_aliased | None,
        Field(
            description="Datum der zugrunde liegenden Version des ROG.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    versionBROGText: Annotated[
        str | None,
        Field(
            description="Titel der zugrunde liegenden Version des Bundesraumordnungsgesetzes.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    versionLPLG: Annotated[
        date_aliased | None,
        Field(
            description="Datum des zugrunde liegenden Landesplanungsgesetzes.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    versionLPLGText: Annotated[
        str | None,
        Field(
            description="Titel des zugrunde liegenden Landesplanungsgesetzes.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gehoertZuPlan: Annotated[
        AnyUrl | UUID,
        Field(
            json_schema_extra={
                "typename": "RP_Plan",
                "stereotype": "Association",
                "reverseProperty": "bereich",
                "sourceOrTarget": "source",
                "multiplicity": "1",
            }
        ),
    ]
    inhaltRPlan: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": [
                    "RP_Achse",
                    "RP_Bodenschutz",
                    "RP_Energieversorgung",
                    "RP_Entsorgung",
                    "RP_Forstwirtschaft",
                    "RP_FreizeitErholung",
                    "RP_GemeindeFunktionSiedlungsentwicklung",
                    "RP_GenerischesObjekt",
                    "RP_Gewaesser",
                    "RP_Grenze",
                    "RP_GruenzugGruenzaesur",
                    "RP_Klimaschutz",
                    "RP_Kommunikation",
                    "RP_KulturellesSachgut",
                    "RP_Landwirtschaft",
                    "RP_NaturLandschaft",
                    "RP_NaturschutzrechtlichesSchutzgebiet",
                    "RP_Raumkategorie",
                    "RP_Rohstoffsicherung",
                    "RP_SonstigeInfrastruktur",
                    "RP_SonstigeSiedlungsstruktur",
                    "RP_SonstigerFreiraumstruktur",
                    "RP_SozialeInfrastruktur",
                    "RP_Sperrgebiet",
                    "RP_Verkehr",
                    "RP_VorbHochwasserschutz",
                    "RP_Wasserschutz",
                    "RP_Wasserwirtschaft",
                    "RP_Windenergienutzung",
                    "RP_ZentralerOrt",
                ],
                "stereotype": "Association",
                "reverseProperty": "gehoertZuRP_Bereich",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            }
        ),
    ] = None
    rasterAenderung: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "RP_RasterplanAenderung",
                "stereotype": "Association",
                "multiplicity": "0..*",
            }
        ),
    ] = None


class SOBereich(XPBereich):
    """Bereich eines sonstigen raumbezogenen Plans."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gehoertZuPlan: Annotated[
        AnyUrl | UUID,
        Field(
            json_schema_extra={
                "typename": "SO_Plan",
                "stereotype": "Association",
                "reverseProperty": "bereich",
                "sourceOrTarget": "source",
                "multiplicity": "1",
            }
        ),
    ]
    inhaltSoPlan: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": [
                    "SO_Bodenschutzrecht",
                    "SO_Denkmalschutzrecht",
                    "SO_Forstrecht",
                    "SO_Gebiet",
                    "SO_Grenze",
                    "SO_Linienobjekt",
                    "SO_Luftverkehrsrecht",
                    "SO_Objekt",
                    "SO_Schienenverkehrsrecht",
                    "SO_SchutzgebietNaturschutzrecht",
                    "SO_SchutzgebietSonstigesRecht",
                    "SO_SchutzgebietWasserrecht",
                    "SO_SonstigesRecht",
                    "SO_Strassenverkehrsrecht",
                    "SO_Wasserrecht",
                ],
                "stereotype": "Association",
                "reverseProperty": "gehoertZuSO_Bereich",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            }
        ),
    ] = None
    rasterAenderung: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "SO_RasterplanAenderung",
                "stereotype": "Association",
                "multiplicity": "0..*",
            }
        ),
    ] = None


class XPAbstraktesPraesentationsobjekt(BaseFeature):
    """Abstrakte Basisklasse für alle Präsentationsobjekte. Die Attribute entsprechen dem ALKIS-Objekt AP_GPO, wobei das Attribut "signaturnummer" in stylesheetId umbenannt wurde. Bei freien Präsentationsobjekten ist die Relation "dientZurDarstellungVon" unbelegt, bei gebundenen Präsentationsobjekten zeigt die Relation auf ein von XP_Objekt abgeleitetes Fachobjekt.
    Freie Präsentationsobjekte dürfen ausschließlich zur graphischen Annotation eines Plans verwendet werden
    Gebundene Präsentationsobjekte mit Raumbezug dienen ausschließlich dazu, Attributwerte des verbundenen Fachobjekts im Plan darzustellen. Die Namen der darzustellenden Fachobjekt-Attribute werden über das Attribut "art" spezifiziert.
    """

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    id: str | None = None
    stylesheetId: Annotated[
        AnyUrl | None,
        Field(
            description='Das Attribut "stylesheetId" zeigt auf ein extern definierte Stylesheet, das Parameter zur Visualisierung von Flächen, Linien, Punkten und Texten enthält. Jedem Stylesheet ist weiterhin eine Darstellungspriorität zugeordnet.  Ausserdem kann ein Stylesheet logische Elemente enthalten,  die die Visualisierung abhängig machen vom Wert des durch "art" definierten Attributes des Fachobjektes, das durch die Relation "dientZurDarstellungVon" referiert wird.',
            json_schema_extra={
                "typename": "XP_StylesheetListe",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    darstellungsprioritaet: Annotated[
        int | None,
        Field(
            description="Enthält die Darstellungspriorität für Elemente der Signatur. Eine vom Standardwert abweichende Priorität wird über dieses Attribut definiert und nicht über eine neue Signatur.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    art: Annotated[
        list[str] | None,
        Field(
            description="'Art' gibt die Namen der Attribute an, die mit dem Präsentationsobjekt dargestellt werden sollen. \r\n\r\nDie Attributart 'Art' darf nur bei \"Freien Präsentationsobjekten (dientZurDarstellungVon = NULL) nicht belegt sein.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    index: Annotated[
        list[int] | None,
        Field(
            description="Wenn das Attribut art des Fachobjektes mehrfach belegt ist gibt index an, auf welche Instanz des Attributs sich das Präsentationsobjekt bezieht.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    gehoertZuBereich: Annotated[
        AnyUrl | UUID | None,
        Field(
            json_schema_extra={
                "typename": [
                    "BP_Bereich",
                    "FP_Bereich",
                    "LP_Bereich",
                    "RP_Bereich",
                    "SO_Bereich",
                ],
                "stereotype": "Association",
                "reverseProperty": "praesentationsobjekt",
                "sourceOrTarget": "source",
                "multiplicity": "0..1",
            }
        ),
    ] = None
    dientZurDarstellungVon: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": [
                    "BP_AbgrabungsFlaeche",
                    "BP_AbstandsFlaeche",
                    "BP_AbstandsMass",
                    "BP_AnpflanzungBindungErhaltung",
                    "BP_AufschuettungsFlaeche",
                    "BP_AusgleichsFlaeche",
                    "BP_AusgleichsMassnahme",
                    "BP_BauGrenze",
                    "BP_BauLinie",
                    "BP_Baugebiet",
                    "BP_BaugebietsTeilFlaeche",
                    "BP_BereichOhneEinAusfahrtLinie",
                    "BP_BesondererNutzungszweckFlaeche",
                    "BP_BodenschaetzeFlaeche",
                    "BP_DenkmalschutzEinzelanlage",
                    "BP_DenkmalschutzEnsembleFlaeche",
                    "BP_EinfahrtPunkt",
                    "BP_EinfahrtsbereichLinie",
                    "BP_EingriffsBereich",
                    "BP_ErhaltungsBereichFlaeche",
                    "BP_ErneuerbareEnergieFlaeche",
                    "BP_FestsetzungNachLandesrecht",
                    "BP_FirstRichtungsLinie",
                    "BP_FoerderungsFlaeche",
                    "BP_FreiFlaeche",
                    "BP_GebaeudeFlaeche",
                    "BP_GemeinbedarfsFlaeche",
                    "BP_GemeinschaftsanlagenFlaeche",
                    "BP_GemeinschaftsanlagenZuordnung",
                    "BP_GenerischesObjekt",
                    "BP_GewaesserFlaeche",
                    "BP_GruenFlaeche",
                    "BP_HoehenMass",
                    "BP_Immissionsschutz",
                    "BP_KennzeichnungsFlaeche",
                    "BP_KleintierhaltungFlaeche",
                    "BP_Landwirtschaft",
                    "BP_LuftreinhalteFlaeche",
                    "BP_NebenanlagenAusschlussFlaeche",
                    "BP_NebenanlagenFlaeche",
                    "BP_NutzungsartenGrenze",
                    "BP_PersGruppenBestimmteFlaeche",
                    "BP_RegelungVergnuegungsstaetten",
                    "BP_RekultivierungsFlaeche",
                    "BP_SchutzPflegeEntwicklungsFlaeche",
                    "BP_SchutzPflegeEntwicklungsMassnahme",
                    "BP_Schutzgebiet",
                    "BP_SpezielleBauweise",
                    "BP_SpielSportanlagenFlaeche",
                    "BP_StrassenVerkehrsFlaeche",
                    "BP_StrassenbegrenzungsLinie",
                    "BP_Strassenkoerper",
                    "BP_TextlicheFestsetzungsFlaeche",
                    "BP_UeberbaubareGrundstuecksFlaeche",
                    "BP_UnverbindlicheVormerkung",
                    "BP_VerEntsorgung",
                    "BP_Veraenderungssperre",
                    "BP_VerkehrsflaecheBesondererZweckbestimmung",
                    "BP_WaldFlaeche",
                    "BP_WasserwirtschaftsFlaeche",
                    "BP_Wegerecht",
                    "FP_Abgrabung",
                    "FP_AbgrabungsFlaeche",
                    "FP_AnpassungKlimawandel",
                    "FP_Aufschuettung",
                    "FP_AufschuettungsFlaeche",
                    "FP_AusgleichsFlaeche",
                    "FP_BebauungsFlaeche",
                    "FP_Bodenschaetze",
                    "FP_BodenschaetzeFlaeche",
                    "FP_Gemeinbedarf",
                    "FP_GenerischesObjekt",
                    "FP_Gewaesser",
                    "FP_Gruen",
                    "FP_KeineZentrAbwasserBeseitigungFlaeche",
                    "FP_Kennzeichnung",
                    "FP_LandwirtschaftsFlaeche",
                    "FP_NutzungsbeschraenkungsFlaeche",
                    "FP_PrivilegiertesVorhaben",
                    "FP_SchutzPflegeEntwicklung",
                    "FP_SpielSportanlage",
                    "FP_Strassenverkehr",
                    "FP_TextlicheDarstellungsFlaeche",
                    "FP_UnverbindlicheVormerkung",
                    "FP_VerEntsorgung",
                    "FP_VorbehalteFlaeche",
                    "FP_WaldFlaeche",
                    "FP_Wasserwirtschaft",
                    "FP_ZentralerVersorgungsbereich",
                    "LP_Abgrenzung",
                    "LP_AllgGruenflaeche",
                    "LP_AnpflanzungBindungErhaltung",
                    "LP_Ausgleich",
                    "LP_Biotopverbundflaeche",
                    "LP_Bodenschutzrecht",
                    "LP_Denkmalschutzrecht",
                    "LP_ErholungFreizeit",
                    "LP_Forstrecht",
                    "LP_GenerischesObjekt",
                    "LP_Landschaftsbild",
                    "LP_NutzungsAusschluss",
                    "LP_NutzungserfordernisRegelung",
                    "LP_PlanerischeVertiefung",
                    "LP_SchutzPflegeEntwicklung",
                    "LP_SchutzobjektBundesrecht",
                    "LP_SchutzobjektInternatRecht",
                    "LP_SonstigesRecht",
                    "LP_TextlicheFestsetzungsFlaeche",
                    "LP_WasserrechtGemeingebrEinschraenkungNaturschutz",
                    "LP_WasserrechtSchutzgebiet",
                    "LP_WasserrechtSonstige",
                    "LP_WasserrechtWirtschaftAbflussHochwSchutz",
                    "LP_ZuBegruenendeGrundstueckflaeche",
                    "LP_Zwischennutzung",
                    "RP_Achse",
                    "RP_Bodenschutz",
                    "RP_Energieversorgung",
                    "RP_Entsorgung",
                    "RP_Forstwirtschaft",
                    "RP_FreizeitErholung",
                    "RP_GemeindeFunktionSiedlungsentwicklung",
                    "RP_GenerischesObjekt",
                    "RP_Gewaesser",
                    "RP_Grenze",
                    "RP_GruenzugGruenzaesur",
                    "RP_Klimaschutz",
                    "RP_Kommunikation",
                    "RP_KulturellesSachgut",
                    "RP_Landwirtschaft",
                    "RP_NaturLandschaft",
                    "RP_NaturschutzrechtlichesSchutzgebiet",
                    "RP_Raumkategorie",
                    "RP_Rohstoffsicherung",
                    "RP_SonstigeInfrastruktur",
                    "RP_SonstigeSiedlungsstruktur",
                    "RP_SonstigerFreiraumstruktur",
                    "RP_SozialeInfrastruktur",
                    "RP_Sperrgebiet",
                    "RP_Verkehr",
                    "RP_VorbHochwasserschutz",
                    "RP_Wasserschutz",
                    "RP_Wasserwirtschaft",
                    "RP_Windenergienutzung",
                    "RP_ZentralerOrt",
                    "SO_Bodenschutzrecht",
                    "SO_Denkmalschutzrecht",
                    "SO_Forstrecht",
                    "SO_Gebiet",
                    "SO_Grenze",
                    "SO_Linienobjekt",
                    "SO_Luftverkehrsrecht",
                    "SO_Objekt",
                    "SO_Schienenverkehrsrecht",
                    "SO_SchutzgebietNaturschutzrecht",
                    "SO_SchutzgebietSonstigesRecht",
                    "SO_SchutzgebietWasserrecht",
                    "SO_SonstigesRecht",
                    "SO_Strassenverkehrsrecht",
                    "SO_Wasserrecht",
                ],
                "stereotype": "Association",
                "reverseProperty": "wirdDargestelltDurch",
                "sourceOrTarget": "source",
                "multiplicity": "0..*",
            }
        ),
    ] = None


class XPExterneReferenz(BaseFeature):
    """Verweis auf ein extern gespeichertes Dokument, einen extern gespeicherten, georeferenzierten Plan oder einen Datenbank-Eintrag. Einer der beiden Attribute "referenzName" bzw. "referenzURL" muss belegt sein."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "DataType"
    georefURL: Annotated[
        AnyUrl | None,
        Field(
            description="Referenz auf eine Georeferenzierungs-Datei. Das Arrtibut ist nur relevant bei Verweisen auf georeferenzierte Rasterbilder.",
            json_schema_extra={
                "typename": "URI",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    georefMimeType: Annotated[
        AnyUrl | None,
        Field(
            description="Mime-Type der Georeferenzierungs-Datei. Das Arrtibut ist nur relevant bei Verweisen auf georeferenzierte Rasterbilder.",
            json_schema_extra={
                "typename": "XP_MimeTypes",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    art: Annotated[
        AnyUrl | None,
        Field(
            description="Typisierung der referierten Dokumente",
            json_schema_extra={
                "typename": "XP_ExterneReferenzArt",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    informationssystemURL: Annotated[
        AnyUrl | None,
        Field(
            description="URI des des zugehörigen Informationssystems",
            json_schema_extra={
                "typename": "URI",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    referenzName: Annotated[
        str | None,
        Field(
            description="Name des referierten Dokuments.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    referenzURL: Annotated[
        AnyUrl | None,
        Field(
            description="URI des referierten Dokuments, bzw. Datenbank-Schlüssel.",
            json_schema_extra={
                "typename": "URI",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    referenzMimeType: Annotated[
        AnyUrl | None,
        Field(
            description="Mime-Type des referierten Dokumentes",
            json_schema_extra={
                "typename": "XP_MimeTypes",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
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


class XPFPO(XPAbstraktesPraesentationsobjekt):
    """Flächenförmiges Präsentationsobjekt. Entspricht der ALKIS Objektklasse AP_FPO."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Polygon | definitions.MultiPolygon,
        Field(
            json_schema_extra={
                "typename": "XP_Flaechengeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            }
        ),
    ]


class XPLPO(XPAbstraktesPraesentationsobjekt):
    """Linienförmiges Präsentationsobjekt Entspricht der ALKIS Objektklasse AP_LPO."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Line | definitions.MultiLine,
        Field(
            json_schema_extra={
                "typename": "XP_Liniengeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            }
        ),
    ]


class XPObjekt(BaseFeature):
    """Abstrakte Oberklasse für alle XPlanGML-Fachobjekte. Die Attribute dieser Klasse werden über den Vererbungs-Mechanismus an alle Fachobjekte weitergegeben."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    id: str | None = None
    uuid: Annotated[
        str | None,
        Field(
            description="Eindeutiger Identifier des Objektes.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    text: Annotated[
        str | None,
        Field(
            description="Beliebiger Text",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    rechtsstand: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Gibt an ob der Planinhalt bereits besteht, geplant ist, oder zukünftig wegfallen soll.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Geplant",
                        "description": "Der Planinhalt bezieht sich auf eine Planung",
                    },
                    "2000": {
                        "name": "Bestehend",
                        "description": "Der Planinhalt stellt den altuellen Zustand dar.",
                    },
                    "3000": {
                        "name": "Fortfallend",
                        "description": "Der Planinhalt beschreibt einen zukünftig fortfallenden Zustand.",
                    },
                },
                "typename": "XP_Rechtsstand",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gesetzlicheGrundlage: Annotated[
        AnyUrl | None,
        Field(
            description="Angagbe der Gesetzlichen Grundlage des Planinhalts.",
            json_schema_extra={
                "typename": "XP_GesetzlicheGrundlage",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    textSchluessel: Annotated[
        list[str] | None,
        Field(
            description="Abschnitts- oder Schlüsselnummer der Text-Abschnitte (XP_TextAbschnitt), die dem Objekt explizit zugeordnet sind.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    textSchluesselBegruendung: Annotated[
        list[str] | None,
        Field(
            description="Abschnitts- oder Schlüsselnummer der Abschnitte der Begründung (XP_BegruendungAbschnitt), die dem Objekt explizit zugeordnet sind.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    gliederung1: Annotated[
        str | None,
        Field(
            description='Kennung im Plan für eine erste Gliederungsebene (z.B. GE-E für ein "Eingeschränktes Gewerbegebiet")',
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gliederung2: Annotated[
        str | None,
        Field(
            description='Kennung im Plan für eine zweite Gliederungsebene (z.B. GE-E 3 für die "Variante 3 eines eingeschränkten Gewerbegebiets")',
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ebene: Annotated[
        int | None,
        Field(
            description='Zuordnung des Objektes zu einer vertikalen Ebene. Der Standard-Ebene 0 sind Objekte auf der Erdoberfläche zugeordnet. Nur unter diesen Objekten wird der Flächenschluss hergestellt. Bei Plan-Objekten, die unterirdische Bereiche (z.B. Tunnel) modellieren, ist ebene < 0. Bei "überirdischen" Objekten (z.B. Festsetzungen auf Brücken) ist ebene > 0.',
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = 0
    rechtsverbindlich: Annotated[
        list[XPExterneReferenz] | None,
        Field(
            description="Referenz auf rechtsverbindliche Dokumente.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    informell: Annotated[
        list[XPExterneReferenz] | None,
        Field(
            description="Referenz auf nicht-rechtsverbindliche Dokumente.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    hatGenerAttribut: Annotated[
        list[
            XPDatumAttribut
            | XPDoubleAttribut
            | XPIntegerAttribut
            | XPStringAttribut
            | XPURLAttribut
        ]
        | None,
        Field(
            description="Erweiterung des definierten Attributsatzes eines Objektes durch generische Attribute.",
            json_schema_extra={
                "typename": [
                    "XP_DatumAttribut",
                    "XP_DoubleAttribut",
                    "XP_IntegerAttribut",
                    "XP_StringAttribut",
                    "XP_URLAttribut",
                ],
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    hoehenangabe: Annotated[
        list[XPHoehenangabe] | None,
        Field(
            description="Angaben zur vertikalen Lage eines Planinhalts.",
            json_schema_extra={
                "typename": "XP_Hoehenangabe",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    gehoertNachrichtlichZuBereich: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": [
                    "BP_Bereich",
                    "FP_Bereich",
                    "LP_Bereich",
                    "RP_Bereich",
                    "SO_Bereich",
                ],
                "stereotype": "Association",
                "reverseProperty": "nachrichtlich",
                "sourceOrTarget": "source",
                "multiplicity": "0..*",
            }
        ),
    ] = None
    wirdDargestelltDurch: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": [
                    "XP_FPO",
                    "XP_LPO",
                    "XP_LTO",
                    "XP_Nutzungsschablone",
                    "XP_PPO",
                    "XP_PTO",
                    "XP_Praesentationsobjekt",
                ],
                "stereotype": "Association",
                "reverseProperty": "dientZurDarstellungVon",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            }
        ),
    ] = None
    refTextInhalt: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": [
                    "BP_TextAbschnitt",
                    "FP_TextAbschnitt",
                    "LP_TextAbschnitt",
                    "RP_TextAbschnitt",
                    "SO_TextAbschnitt",
                    "XP_TextAbschnitt",
                ],
                "stereotype": "Association",
                "multiplicity": "0..*",
            }
        ),
    ] = None
    refBegruendungInhalt: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "XP_BegruendungAbschnitt",
                "stereotype": "Association",
                "multiplicity": "0..*",
            }
        ),
    ] = None


class XPPPO(XPAbstraktesPraesentationsobjekt):
    """Punktförmiges Präsentationsobjekt. Entspricht der ALKIS-Objektklasse AP_PPO."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Point | definitions.MultiPoint,
        Field(
            json_schema_extra={
                "typename": "XP_Punktgeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            }
        ),
    ]
    drehwinkel: Annotated[
        definitions.Angle | None,
        Field(
            description="Winkel um den der Text oder die Signatur mit punktförmiger Bezugsgeometrie aus der Horizontalen gedreht ist. Angabe im Bogenmaß; Zählweise im mathematisch positiven Sinn (von Ost über Nord nach West und Süd).",
            json_schema_extra={
                "typename": "Angle",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "grad",
            },
        ),
    ] = None
    skalierung: Annotated[
        float | None,
        Field(
            description="Skalierungsfaktor für Symbole.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = 1.0


class XPPlan(BaseFeature):
    """Abstrakte Oberklasse für alle Klassen von raumbezogenen Plänen.."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    id: str | None = None
    name: Annotated[
        str | None,
        Field(
            description="Name des Plans.",
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
            description="Nummer des Plans.",
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
            description="Interner Identifikator des Plans.",
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
            description="Kommentierende Beschreibung des Plans.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    kommentar: Annotated[
        str | None,
        Field(
            description="Beliebiger Kommentar zum Plan",
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
            description="Datum, an dem der Plan technisch ausgefertigt wurde.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    genehmigungsDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum der Genehmigung des Plans",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    untergangsDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum, an dem der Plan (z.B. durch Ratsbeschluss oder Gerichtsurteil) aufgehoben oder für nichtig erklärt wurde.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    aendert: Annotated[
        list[XPVerbundenerPlan] | None,
        Field(
            description="Bezeichnung eines anderen Planes der Gemeinde, der durch den vorliegenden Plan geändert wird.",
            json_schema_extra={
                "typename": "XP_VerbundenerPlan",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    wurdeGeaendertVon: Annotated[
        list[XPVerbundenerPlan] | None,
        Field(
            description="Bezeichnung eines anderen Plans , durch den der vorliegende Plan geändert wurde.",
            json_schema_extra={
                "typename": "XP_VerbundenerPlan",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    erstellungsMassstab: Annotated[
        int | None,
        Field(
            description="Der bei der Erstellung des Plans benutzte Kartenmassstab.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    xPlanGMLVersion: Annotated[
        str | None,
        Field(
            description="Version des XPlanGML-Schemas, nach dem der Datensatz erstellt wurde. Da diese Version auch aus dem Namespace des GML-Datensatzes ermittelt werden kann ist dies Attribut redundant und wird in einer zukünftiger Version des Standards wegfallen.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = "4.1"
    bezugshoehe: Annotated[
        definitions.Length | None,
        Field(
            description="Standard Bezugshöhe (absolut NhN) für relative Höhenangaben von Planinhalten.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    raeumlicherGeltungsbereich: Annotated[
        definitions.Polygon | definitions.MultiPolygon | None,
        Field(
            description="Grenze des räumlichen Geltungsbereiches des Plans.",
            json_schema_extra={
                "typename": "XP_Flaechengeometrie",
                "stereotype": "Geometry",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    verfahrensMerkmale: Annotated[
        list[XPVerfahrensMerkmal] | None,
        Field(
            description="Vermerke der am Planungssverfahrens beteiligten Akteure.",
            json_schema_extra={
                "typename": "XP_VerfahrensMerkmal",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    rechtsverbindlich: Annotated[
        list[XPExterneReferenz] | None,
        Field(
            description="Referenz ein rechtsverbindliche Dokumente",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    informell: Annotated[
        list[XPExterneReferenz] | None,
        Field(
            description="Referenz auf nicht-rechtsverbindliche Dokumente",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    hatGenerAttribut: Annotated[
        list[
            XPDatumAttribut
            | XPDoubleAttribut
            | XPIntegerAttribut
            | XPStringAttribut
            | XPURLAttribut
        ]
        | None,
        Field(
            description="Erweiterung der vorgegebenen Attribute durch generische Attribute.",
            json_schema_extra={
                "typename": [
                    "XP_DatumAttribut",
                    "XP_DoubleAttribut",
                    "XP_IntegerAttribut",
                    "XP_StringAttribut",
                    "XP_URLAttribut",
                ],
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    refBeschreibung: Annotated[
        list[XPExterneReferenz] | None,
        Field(
            description="Referenz auf die Beschreibung des Plans.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    refBegruendung: Annotated[
        list[XPExterneReferenz] | None,
        Field(
            description="Referenz auf die Bebründung des Plans.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    refExternalCodeList: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf ein GML-Dictionary mit Codelists.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refLegende: Annotated[
        list[XPExterneReferenz] | None,
        Field(
            description="Referenz auf die Legende des Plans.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    refRechtsplan: Annotated[
        list[XPExterneReferenz] | None,
        Field(
            description="Referenz auf eine elektronische Version des rechtsverbindlichen Plans.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    refPlangrundlage: Annotated[
        list[XPExterneReferenz] | None,
        Field(
            description="Referenz auf eine elektronische Version der Plangrundlage, z.B. ein Katasterplan.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    texte: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": [
                    "BP_TextAbschnitt",
                    "FP_TextAbschnitt",
                    "LP_TextAbschnitt",
                    "RP_TextAbschnitt",
                    "SO_TextAbschnitt",
                    "XP_TextAbschnitt",
                ],
                "stereotype": "Association",
                "multiplicity": "0..*",
            }
        ),
    ] = None
    begruendungsTexte: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "XP_BegruendungAbschnitt",
                "stereotype": "Association",
                "multiplicity": "0..*",
            }
        ),
    ] = None


class XPPraesentationsobjekt(XPAbstraktesPraesentationsobjekt):
    """Entspricht der ALKIS-Objektklasse AP_Darstellung mit dem Unterschied, dass auf das Attribut "positionierungssregel" verzichtet wurde.  Die Klasse darf nur als gebundenes Präsentationsobjekt verwendet werden. Die Standard-Darstellung des verbundenen Fachobjekts wird dann durch die über stylesheetId spezifizierte Darstellung ersetzt. Die Umsetzung dieses Konzeptes ist der Implementierung überlassen."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class XPRasterplanAenderung(BaseFeature):
    """Basisklasse für georeferenzierte Rasterdarstellungen von Änderungen des Basisplans, die nicht in die Rasterdarstellung XP_RasterplanBasis integriert sind.
    Im Standard sind nur georeferenzierte Rasterpläne zugelassen. Die über refScan referierte externe Referenz muss deshalb entweder vom Typ "PlanMitGeoreferenz" sein oder einen WMS-Request enthalten.
    """

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    id: str | None = None
    nameAenderung: Annotated[
        str | None,
        Field(
            description="Bezeichnung des Plan-Änderung",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    nummerAenderung: Annotated[
        int | None,
        Field(
            description="Nummer der Änderung",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    beschreibung: Annotated[
        str | None,
        Field(
            description="Nähere Beschreibung der Plan-Änderung",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refBeschreibung: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf das Beschreibungs-Dokument",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refBegruendung: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf das Begründungs-Dokument",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refScan: Annotated[
        list[XPExterneReferenz],
        Field(
            description="Referenz auf eine rasterversion der Plan-Änderung.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "1..*",
            },
            min_length=1,
        ),
    ]
    refText: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf die textlichen Inhalte der Planänderung.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refLegende: Annotated[
        list[XPExterneReferenz] | None,
        Field(
            description="Referenz auf die Legende der Plan-Änderung.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    geltungsbereichAenderung: Annotated[
        definitions.Polygon | definitions.MultiPolygon | None,
        Field(
            description="Raeumlicher Bereich des georeferenzierten Rasterbildes, in dem die Änderung wirksam ist.",
            json_schema_extra={
                "typename": "XP_Flaechengeometrie",
                "stereotype": "Geometry",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    besonderheiten: Annotated[
        str | None,
        Field(
            description="Besonderheiten der Änderung",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class XPRasterplanBasis(BaseFeature):
    """Georeferenzierte Rasterdarstellung eines Plans. Das über refScan referierte Rasterbild zeigt den Basisplan, dessen Geltungsbereich durch den Geltungsbereich des Gesamtplans (Attribut geltungsbereich von XP_Plan) repräsentiert ist. Diesem Basisplan können Änderungen überlagert sein, denen jeweils eigene Rasterbilder und Geltungsbereiche zugeordnet sind (XP_RasterplanAenderung und abgeleitete Klassen).

    Im Standard sind nur georeferenzierte Rasterpläne zugelassen. Die über refScan referierte externe Referenz muss deshalb entweder vom Typ "PlanMitGeoreferenz" sein oder einen WMS-Request enthalten.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    id: str | None = None
    refScan: Annotated[
        list[XPExterneReferenz],
        Field(
            description="Referenz auf eine georeferenzierte Rasterversion des Basisplans",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "1..*",
            },
            min_length=1,
        ),
    ]
    refText: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf die textlich fprmulierten Inhalte des Plans.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refLegende: Annotated[
        list[XPExterneReferenz] | None,
        Field(
            description="Referenz auf die Legende des Plans.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None


class XPSPEMassnahmenDaten(BaseFeature):
    """Spezifikation der Attribute für einer Schutz-, Pflege- oder Entwicklungsmaßnahme."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "DataType"
    klassifizMassnahme: Annotated[
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
            "2200",
            "2300",
            "9999",
        ]
        | None,
        Field(
            description="Klassifikation der Maßnahme",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "ArtentreicherGehoelzbestand"},
                    "1100": {"name": "NaturnaherWald"},
                    "1200": {"name": "ExtensivesGruenland"},
                    "1300": {"name": "Feuchtgruenland"},
                    "1400": {"name": "Obstwiese"},
                    "1500": {"name": "NaturnaherUferbereich"},
                    "1600": {"name": "Roehrichtzone"},
                    "1700": {"name": "Ackerrandstreifen"},
                    "1800": {"name": "Ackerbrache"},
                    "1900": {"name": "Gruenlandbrache"},
                    "2000": {"name": "Sukzessionsflaeche"},
                    "2100": {"name": "Hochstaudenflur"},
                    "2200": {"name": "Trockenrasen"},
                    "2300": {"name": "Heide"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "XP_SPEMassnahmenTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    massnahmeText: Annotated[
        str | None,
        Field(
            description="Durchzuführende Maßnahme als freier Text.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    massnahmeKuerzel: Annotated[
        str | None,
        Field(
            description="Kürzel der durchzuführenden Maßnahme.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class XPTPO(XPAbstraktesPraesentationsobjekt):
    """Abstrakte Oberklasse für textliche Präsentationsobjekte. Entspricht der ALKIS Objektklasse AP_TPO"""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    schriftinhalt: Annotated[
        str | None,
        Field(
            description="Schriftinhalt; enthält die darzustellenden Zeichen",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    fontSperrung: Annotated[
        float | None,
        Field(
            description="Die Zeichensperrung steuert den zusätzlichen Raum, der zwischen 2 aufeinanderfolgende Zeichenkörper geschoben wird. Er ist ein Faktor, der mit der angegebenen Zeichenhöhe mulitpliziert wird, um den einzufügenden Zusatzabstand zu erhalten. Mit der Abhängigkeit von der Zeichenhöhe wird erreicht, dass das Schriftbild unabhängig von der Zeichenhöhe gleich wirkt. Der Defaultwert ist 0.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = 0.0
    skalierung: Annotated[
        float | None,
        Field(
            description="Skalierungsfaktor für die Schriftgröße (fontGroesse * skalierung).",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = 1.0
    horizontaleAusrichtung: Annotated[
        Literal["linksbündig", "rechtsbündig", "zentrisch"] | None,
        Field(
            description="Gibt die Ausrichtung des Textes bezüglich der Textgeometrie an.\r\nlinksbündig : Der Text beginnt an der Punktgeometrie bzw. am Anfangspunkt der Liniengeometrie.\r\nrechtsbündig: Der Text endet an der Punktgeometrie bzw. am Endpunkt der Liniengeometrie\r\nzentrisch: Der Text erstreckt sich von der Punktgeometrie gleich weit nach links und rechts bzw. steht auf der Mitte der Standlinie.",
            json_schema_extra={
                "enumDescription": {
                    "linksbündig": {
                        "name": "linksbündig",
                        "description": "Text linksbündig am Textpunkt bzw. am ersten Punkt der Linie.",
                    },
                    "rechtsbündig": {
                        "name": "rechtsbündig",
                        "description": "Text rechtsbündig am Textpunkt bzw. am letzten Punkt der Linie.",
                    },
                    "zentrisch": {
                        "name": "zentrisch",
                        "description": "Text zentriert am Textpunkt bzw. in der Mitte der Textstandlinie.",
                    },
                },
                "typename": "XP_HorizontaleAusrichtung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    vertikaleAusrichtung: Annotated[
        Literal["Basis", "Mitte", "Oben"] | None,
        Field(
            description="Die vertikale Ausrichtung eines Textes gibt an, ob die Bezugsgeometrie die Basis (Grundlinie) des Textes, die Mitte oder obere Buchstabenbegrenzung betrifft.",
            json_schema_extra={
                "enumDescription": {
                    "Basis": {
                        "name": "Basis",
                        "description": "Textgeometrie bezieht sich auf die Basis- bzw. Grundlinie der Buchstaben.",
                    },
                    "Mitte": {
                        "name": "Mitte",
                        "description": "Textgeometrie bezieht sich auf die Mittellinie der Buchstaben.",
                    },
                    "Oben": {
                        "name": "Oben",
                        "description": "Textgeometrie bezieht sich auf die Oberlinie der Großbuchstaben.",
                    },
                },
                "typename": "XP_VertikaleAusrichtung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    hat: Annotated[
        AnyUrl | UUID | None,
        Field(
            json_schema_extra={
                "typename": "XP_LPO",
                "stereotype": "Association",
                "multiplicity": "0..1",
            }
        ),
    ] = None


class XPTextAbschnitt(BaseFeature):
    """Ein Abschnitt der textlich formulierten Inhalte  des Plans."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    id: str | None = None
    schluessel: Annotated[
        str | None,
        Field(
            description="Schlüssel zur Referenzierung des Abschnitts.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gesetzlicheGrundlage: Annotated[
        str | None,
        Field(
            description="Gesetzliche Grundlage des Text-Abschnittes",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    text: Annotated[
        str | None,
        Field(
            description="Inhalt eines Abschnitts der textlichen Planinhalte",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refText: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf ein externes Dokument das den zug Textabschnitt enthält.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPObjekt(XPObjekt):
    """Basisklasse für alle raumbezogenen Festsetzungen, Hinweise, Vermerke und Kennzeichnungen eines Bebauungsplans."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    rechtscharakter: Annotated[
        Literal["1000", "3000", "4000", "5000"] | None,
        Field(
            description="Rechtliche Charakterisierung des Planinhaltes.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Festsetzung"},
                    "3000": {"name": "Hinweis"},
                    "4000": {"name": "Vermerk"},
                    "5000": {"name": "Kennzeichnung"},
                },
                "typename": "BP_Rechtscharakter",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    startBedingung: Annotated[
        BPWirksamkeitBedingung | None,
        Field(
            description="Notwendige Bedingung für die Wirksamkeit einer Festsetzung.",
            json_schema_extra={
                "typename": "BP_WirksamkeitBedingung",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    endeBedingung: Annotated[
        BPWirksamkeitBedingung | None,
        Field(
            description="Notwendige Bedingung für das Ende der Wirksamkeit einer Festsetzung",
            json_schema_extra={
                "typename": "BP_WirksamkeitBedingung",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    wirdAusgeglichenDurchFlaeche: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "BP_AusgleichsFlaeche",
                "stereotype": "Association",
                "multiplicity": "0..*",
            }
        ),
    ] = None
    wirdAusgeglichenDurchABE: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "BP_AnpflanzungBindungErhaltung",
                "stereotype": "Association",
                "multiplicity": "0..*",
            }
        ),
    ] = None
    wirdAusgeglichenDurchSPEMassnahme: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "BP_SchutzPflegeEntwicklungsMassnahme",
                "stereotype": "Association",
                "multiplicity": "0..*",
            }
        ),
    ] = None
    wirdAusgeglichenDurchSPEFlaeche: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "BP_SchutzPflegeEntwicklungsFlaeche",
                "stereotype": "Association",
                "multiplicity": "0..*",
            }
        ),
    ] = None
    wirdAusgeglichenDurchMassnahme: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "BP_AusgleichsMassnahme",
                "stereotype": "Association",
                "multiplicity": "0..*",
            }
        ),
    ] = None
    gehoertZuBP_Bereich: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "BP_Bereich",
                "stereotype": "Association",
                "reverseProperty": "inhaltBPlan",
                "sourceOrTarget": "source",
                "multiplicity": "0..*",
            }
        ),
    ] = None


class BPPlan(XPPlan):
    """Die Klasse modelliert einen Bebauungsplan"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gemeinde: Annotated[
        list[XPGemeinde],
        Field(
            description="Die für den Plan zuständige Gemeinde.",
            json_schema_extra={
                "typename": "XP_Gemeinde",
                "stereotype": "DataType",
                "multiplicity": "1..*",
            },
            min_length=1,
        ),
    ]
    plangeber: Annotated[
        XPPlangeber | None,
        Field(
            description="Für den BPlan verantwortliche Stelle.",
            json_schema_extra={
                "typename": "XP_Plangeber",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    planArt: Annotated[
        list[
            Literal[
                "1000",
                "10000",
                "10001",
                "3000",
                "4000",
                "40000",
                "40001",
                "40002",
                "5000",
                "7000",
                "9999",
            ]
        ],
        Field(
            description="Typ des vorliegenden BPlans.",
            json_schema_extra={
                "typename": "BP_PlanArt",
                "stereotype": "Enumeration",
                "multiplicity": "1..*",
                "enumDescription": {
                    "1000": {
                        "name": "BPlan",
                        "description": "Unspezifizierter Bebauungsplan",
                    },
                    "10000": {
                        "name": "EinfacherBPlan",
                        "description": "Einfacher BPlan, §30 Abs. 3 BauGB.",
                    },
                    "10001": {
                        "name": "QualifizierterBPlan",
                        "description": "Qualifizierter BPlan, §30 Abs. 1 BauGB.",
                    },
                    "3000": {
                        "name": "VorhabenbezogenerBPlan",
                        "description": "Vorhabensbezogener Bebauungsplan",
                    },
                    "4000": {
                        "name": "InnenbereichsSatzung",
                        "description": "Eine Innenbereichssatzung kann entweder eine Klarstellungssatzung, eine Entwicklungssatzung oder eine Ergänzungssatzung sein.",
                    },
                    "40000": {
                        "name": "KlarstellungsSatzung",
                        "description": "Klarstellungssatzung nach  § 34 Abs.4 Nr.1 BauGB.",
                    },
                    "40001": {
                        "name": "EntwicklungsSatzung",
                        "description": "Entwicklungssatzung nach  § 34 Abs.4 Nr. 2 BauGB.",
                    },
                    "40002": {
                        "name": "ErgaenzungsSatzung",
                        "description": "Ergänzungssatzung nach  § 34 Abs.4 Nr. 3 BauGB.",
                    },
                    "5000": {
                        "name": "AussenbereichsSatzung",
                        "description": "Außenbereichssatzung nach § 35 Abs. 6 BauGB.",
                    },
                    "7000": {
                        "name": "OertlicheBauvorschrift",
                        "description": "Örtliche Bauvorschrift.",
                    },
                    "9999": {"name": "Sonstiges", "description": "Sonstige Planart."},
                },
            },
            min_length=1,
        ),
    ]
    sonstPlanArt: Annotated[
        AnyUrl | None,
        Field(
            description='Spezifikation einer "Sonstigen Planart", wenn kein Plantyp aus der Enumeration BP_PlanArt zutraffend ist.',
            json_schema_extra={
                "typename": "BP_SonstPlanArt",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    verfahren: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Verfahrensart der BPlan-Aufstellung oder -Änderung.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Normal",
                        "description": "Nomales BPlan Verfahren.",
                    },
                    "2000": {
                        "name": "Parag13",
                        "description": "BPlan Verfahren nach Parag. 13 BauGB.",
                    },
                    "3000": {
                        "name": "Parag13a",
                        "description": "BPlan Verfahren nach Parag 13a BauGB.",
                    },
                },
                "typename": "BP_Verfahren",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    rechtsstand: Annotated[
        Literal[
            "1000",
            "2000",
            "2100",
            "2200",
            "2300",
            "2400",
            "3000",
            "4000",
            "4500",
            "5000",
        ]
        | None,
        Field(
            description="Aktueller Rechtsstand des Plans",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Aufstellungsbeschluss",
                        "description": "Ein Aufstellungsbeschluss der Gemeinde liegt vor",
                    },
                    "2000": {
                        "name": "Entwurf",
                        "description": "Ein Planentwurf liegt vor",
                    },
                    "2100": {
                        "name": "FruehzeitigeBehoerdenBeteiligung",
                        "description": "Die frühzeitige Beteiligung der Behörden (§ 4 Abs. 1 BauGB) hat stattgefunden.",
                    },
                    "2200": {
                        "name": "FruehzeitigeOeffentlichkeitsBeteiligung",
                        "description": "Die frühzeitige Beteiligung der Öffentlichkeit (§ 3 Abs. 1 BauGB), bzw. bei einem Verfahren nach § 13a BauGB die Unterrichtung der Öffentlichkeit (§ 13a Abs. 3 BauGB) hat stattgefunden.",
                    },
                    "2300": {
                        "name": "BehoerdenBeteiligung",
                        "description": "Die Beteiligung der Behörden hat stattgefunden (§ 4 Abs. 2 BauGB).",
                    },
                    "2400": {
                        "name": "OeffentlicheAuslegung",
                        "description": "Der Plan hat öffentlich ausgelegen. (§ 3 Abs. 2 BauGB).",
                    },
                    "3000": {
                        "name": "Satzung",
                        "description": "Die Satzung wurde durch Beschluss der Gemeinde verabschiedet.",
                    },
                    "4000": {
                        "name": "InkraftGetreten",
                        "description": "Der Plan ist inkraft getreten.",
                    },
                    "4500": {
                        "name": "TeilweiseUntergegangen",
                        "description": "Der Plan ist, z. B. durch einen Gerichtsbeschluss oder neuen Plan, teilweise untergegangen.",
                    },
                    "5000": {
                        "name": "Untergegangen",
                        "description": "Der Plan wurde aufgehoben oder für nichtig erklärt.",
                    },
                },
                "typename": "BP_Rechtsstand",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    status: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definieter aktueller Status des Plans.",
            json_schema_extra={
                "typename": "BP_Status",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    hoehenbezug: Annotated[
        str | None,
        Field(
            description="Bei Höhenangaben im Plan standardmäßig verwendeter Höhenbezug (z.B. Höhe über NN).",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    aenderungenBisDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum der berücksichtigten Plan-Änderungen.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    aufstellungsbeschlussDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Aufstellungsbeschlusses.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    veraenderungssperreDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum der Veränderungssperre",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    auslegungsStartDatum: Annotated[
        list[date_aliased] | None,
        Field(
            description="Start-Datum des Auslegungs-Zeitraums. Bei mehrfacher öffentlicher Auslegung können mehrere Datumsangeben spezifiziert werden.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    auslegungsEndDatum: Annotated[
        list[date_aliased] | None,
        Field(
            description="End-Datum des Auslegungs-Zeitraums. Bei mehrfacher öffentlicher Auslegung können mehrere Datumsangeben spezifiziert werden.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    traegerbeteiligungsStartDatum: Annotated[
        list[date_aliased] | None,
        Field(
            description="Start-Datum der Trägerbeteiligung. Bei mehrfacher Trägerbeteiligung können mehrere Datumsangeben spezifiziert werden.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    traegerbeteiligungsEndDatum: Annotated[
        list[date_aliased] | None,
        Field(
            description="End-Datum der Trägerbeteiligung. Bei mehrfacher Trägerbeteiligung können mehrere Datumsangeben spezifiziert werden.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    satzungsbeschlussDatum: Annotated[
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
    rechtsverordnungsDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum der Rechtsverordnung.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    inkrafttretensDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Inkrafttretens.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ausfertigungsDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum der Ausfertigung",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    veraenderungssperre: Annotated[
        bool | None,
        Field(
            description="Gibt an ob es im gesamten Geltungsbereich des Plans eine Veränderungssperre gibt.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False
    staedtebaulicherVertrag: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob es zum Plan einen städtebaulichen Vertrag gibt.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False
    erschliessungsVertrag: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob es für den Plan einen Erschließungsvertrag gibt.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False
    durchfuehrungsVertrag: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob für das gebiet ein Durchführungsvertrag (Kombination aus Städtebaulichen Vertrag und Erschließungsvertrag) existiert.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False
    gruenordnungsplan: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob für den BPlan ein zugehöriger Grünordnungsplan existiert.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False
    refKoordinatenListe: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf eine Koordinaten-Liste.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refGrundstuecksverzeichnis: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf ein Grundstücksverzeichnis.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refPflanzliste: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf eine Pflanzliste.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refUmweltbericht: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf den Umweltbericht.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refSatzung: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf die Satzung",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refGruenordnungsplan: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf den Grünordnungsplan",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    bereich: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "BP_Bereich",
                "stereotype": "Association",
                "reverseProperty": "gehoertZuPlan",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            }
        ),
    ] = None


class BPPunktobjekt(BPObjekt):
    """Basisklasse für alle Objekte eines Bebauungsplans mit punktförmigem Raumbezug (Einzelpunkt oder Punktmenge)."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Point | definitions.MultiPoint,
        Field(
            description="Punktförmiger Raumbezug (Einzelpunkt oder Punktmenge).",
            json_schema_extra={
                "typename": "XP_Punktgeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class BPRasterplanAenderung(XPRasterplanAenderung):
    """Georeferenziertes Rasterbild der Änderung eines Basisplans. Die abgeleitete Klasse besitzt Datums-Attribute, die spezifisch für Bebauungspläne sind."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    aufstellungsbeschlussDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Aufstellungsbeschlusses",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    auslegungsStartDatum: Annotated[
        list[date_aliased] | None,
        Field(
            description="Start-Datum der öffentlichen Auslegung.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    auslegungsEndDatum: Annotated[
        list[date_aliased] | None,
        Field(
            description="End-Datum der öffentlichen Auslegung.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    traegerbeteiligungsStartDatum: Annotated[
        list[date_aliased] | None,
        Field(
            description="Start-Datum der Trägerbeteiligung.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    traegerbeteiligungsEndDatum: Annotated[
        list[date_aliased] | None,
        Field(
            description="End-Datum der Trägerbeteiligung.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    veraenderungssperreDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum einer Veränderungssperre",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    satzungsbeschlussDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Satzungsbeschlusses der Änderung.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    rechtsverordnungsDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum der Rechtsverordnung",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    inkrafttretensDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Inkrafttretens der Änderung",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPTextAbschnitt(XPTextAbschnitt):
    """Texlich formulierter Inhalt eines Bebauungsplans, der einen anderen Rechtscharakter als das zugrunde liegende Fachobjekt hat (Attribut rechtscharakter des Fachobjektes), oder dem Plan als Ganzes zugeordnet ist."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    rechtscharakter: Annotated[
        Literal["1000", "3000", "4000", "5000"],
        Field(
            description="Rechtscharakter des textlich formulierten Planinhalts.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Festsetzung"},
                    "3000": {"name": "Hinweis"},
                    "4000": {"name": "Vermerk"},
                    "5000": {"name": "Kennzeichnung"},
                },
                "typename": "BP_Rechtscharakter",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]


class FPObjekt(XPObjekt):
    """Basisklasse für alle Fachobjekte des Flächennutzungsplans."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    rechtscharakter: Annotated[
        Literal["1000", "3000", "4000", "5000"] | None,
        Field(
            description="Rechtliche Charakterisierung des Planinhalts",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Darstellung"},
                    "3000": {"name": "Hinweis"},
                    "4000": {"name": "Vermerk"},
                    "5000": {"name": "Kennzeichnung"},
                },
                "typename": "FP_Rechtscharakter",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    spezifischePraegung: Annotated[
        AnyUrl | None,
        Field(
            description="Spezifische bauliche Prägung einer Darstellung.",
            json_schema_extra={
                "typename": "FP_SpezifischePraegungTypen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gehoertZuFP_Bereich: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "FP_Bereich",
                "stereotype": "Association",
                "reverseProperty": "inhaltFPlan",
                "sourceOrTarget": "source",
                "multiplicity": "0..*",
            }
        ),
    ] = None
    wirdAusgeglichenDurchFlaeche: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "FP_AusgleichsFlaeche",
                "stereotype": "Association",
                "multiplicity": "0..*",
            }
        ),
    ] = None
    wirdAusgeglichenDurchSPE: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "FP_SchutzPflegeEntwicklung",
                "stereotype": "Association",
                "multiplicity": "0..*",
            }
        ),
    ] = None


class FPPlan(XPPlan):
    """Klasse zur Modellierung eines gesamten Flächennutzungsplans."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gemeinde: Annotated[
        list[XPGemeinde],
        Field(
            description="Zuständige Gemeinde",
            json_schema_extra={
                "typename": "XP_Gemeinde",
                "stereotype": "DataType",
                "multiplicity": "1..*",
            },
            min_length=1,
        ),
    ]
    plangeber: Annotated[
        XPPlangeber | None,
        Field(
            description="Für die Planung zuständige Institution",
            json_schema_extra={
                "typename": "XP_Plangeber",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    planArt: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "9999"] | None,
        Field(
            description="Typ des FPlans",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "FPlan",
                        "description": "Flächennutzungsplan nach §5 BauGB.",
                    },
                    "2000": {
                        "name": "GemeinsamerFPlan",
                        "description": "Gemeinsamer FPlan nach §204 BauGB",
                    },
                    "3000": {
                        "name": "RegFPlan",
                        "description": "Regionaler FPlan, der Zugleich die Funktion eines Regionalplans als auch eines gemeinssamen FPlans nach § 204 BauGB erfüllt.",
                    },
                    "4000": {
                        "name": "FPlanRegPlan",
                        "description": "Flächennutzungsplan mit regionalplanerischen Festlegungen (nur in HH, HB, B).",
                    },
                    "5000": {
                        "name": "SachlicherTeilplan",
                        "description": "Sachlicher Teilflächennutzungsplan nach §5 Abs. 2b BauGB.",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstiger Flächennutzungsplan",
                    },
                },
                "typename": "FP_PlanArt",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    sonstPlanArt: Annotated[
        AnyUrl | None,
        Field(
            description="Sonstige Art eines FPlans bei planArt == 9999.",
            json_schema_extra={
                "typename": "FP_SonstPlanArt",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    sachgebiet: Annotated[
        str | None,
        Field(
            description="Sachgebiet eines Teilflächennutzungsplans",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    verfahren: Annotated[
        Literal["1000", "2000"] | None,
        Field(
            description="Verfahren nach dem ein FPlan aufgestellt oder geändert wird.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Normal",
                        "description": "Normales FPlan Verfahren.",
                    },
                    "2000": {
                        "name": "Parag13",
                        "description": "FPlan Verfahren nach Parag 13 BauGB.",
                    },
                },
                "typename": "FP_Verfahren",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    rechtsstand: Annotated[
        Literal["1000", "2000", "2100", "2200", "2300", "2400", "3000", "4000", "5000"]
        | None,
        Field(
            description="Rechtsstand de4s Plans",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Aufstellungsbeschluss"},
                    "2000": {"name": "Entwurf"},
                    "2100": {"name": "FruehzeitigeBehoerdenBeteiligung"},
                    "2200": {"name": "FruehzeitigeOeffentlichkeitsBeteiligung"},
                    "2300": {"name": "BehoerdenBeteiligung"},
                    "2400": {"name": "OeffentlicheAuslegung"},
                    "3000": {"name": "Plan"},
                    "4000": {"name": "Wirksamkeit"},
                    "5000": {"name": "Untergegangen"},
                },
                "typename": "FP_Rechtsstand",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    status: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine ExternalCodeList definierter Status des Plans.",
            json_schema_extra={
                "typename": "FP_Status",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    aufstellungsbeschlussDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Plan-Aufstellungsbeschlusses.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    auslegungsStartDatum: Annotated[
        date_aliased | None,
        Field(
            description="Start-Datum der öffentlichen Auslegung.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    auslegungsEndDatum: Annotated[
        date_aliased | None,
        Field(
            description="End-Datum der öffentlichen Auslegung.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    traegerbeteiligungsStartDatum: Annotated[
        date_aliased | None,
        Field(
            description="Start-Datum der Trägerbeteiligung.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    traegerbeteiligungsEndDatum: Annotated[
        date_aliased | None,
        Field(
            description="End-Datum der Trägerbeteiligung.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    aenderungenBisDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum, bis zu dem Änderungen des Plans berücksichtigt wurden.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    entwurfsbeschlussDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Entwurfsbeschlusses",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    planbeschlussDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Planbeschlusses",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    wirksamkeitsDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum der Wirksamkeit",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refUmweltbericht: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf den Umweltbericht.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refErlaeuterung: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf den Erläuterungsbericht..",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    bereich: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "FP_Bereich",
                "stereotype": "Association",
                "reverseProperty": "gehoertZuPlan",
                "sourceOrTarget": "source",
                "multiplicity": "0..*",
            }
        ),
    ] = None


class FPPunktobjekt(FPObjekt):
    """Basisklasse für alle Objekte eines Flächennutzungsplans mit punktförmigem Raumbezug (Einzelpunkt oder Punktmenge)."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Point | definitions.MultiPoint,
        Field(
            json_schema_extra={
                "typename": "XP_Punktgeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            }
        ),
    ]


class FPRasterplanAenderung(XPRasterplanAenderung):
    """Georeferenziertes Rasterbild der Änderung eines Basisplans. Die abgeleitete Klasse besitzt Datums-Attribute, die spezifisch für Flächennutzungspläne sind."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    aufstellungbeschlussDatum: Annotated[
        date_aliased | None,
        Field(
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            }
        ),
    ] = None
    auslegungsStartDatum: Annotated[
        list[date_aliased] | None,
        Field(
            description="Start-Datum der öffentlichen Auslegung.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    auslegungsEndDatum: Annotated[
        list[date_aliased] | None,
        Field(
            description="End-Datum der öffentlichen Auslegung.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    traegerbeteiligungsStartDatum: Annotated[
        list[date_aliased] | None,
        Field(
            description="Start-Datum der Trägerbeteiligung.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    traegerbeteiligungsEndDatum: Annotated[
        list[date_aliased] | None,
        Field(
            description="End-Datum der Trägerbeteiligung.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    aenderungenBisDatum: Annotated[
        date_aliased | None,
        Field(
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            }
        ),
    ] = None
    entwurfsbeschlussDatum: Annotated[
        date_aliased | None,
        Field(
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            }
        ),
    ] = None
    planbeschlussDatum: Annotated[
        date_aliased | None,
        Field(
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            }
        ),
    ] = None
    wirksamkeitsDatum: Annotated[
        date_aliased | None,
        Field(
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            }
        ),
    ] = None


class FPTextAbschnitt(XPTextAbschnitt):
    """Texlich formulierter Inhalt eines Flächennutzungsplans, der einen anderen Rechtscharakter als das zugrunde liegende Fachobjekt hat (Attribut rechtscharakter des Fachobjektes), oder dem Plan als Ganzes zugeordnet ist."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    rechtscharakter: Annotated[
        Literal["1000", "3000", "4000", "5000"],
        Field(
            description="Rechtscharakter des textlich formulierten Planinhalts.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Darstellung"},
                    "3000": {"name": "Hinweis"},
                    "4000": {"name": "Vermerk"},
                    "5000": {"name": "Kennzeichnung"},
                },
                "typename": "FP_Rechtscharakter",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]


class LPObjekt(XPObjekt):
    """Basisklasse für alle spezifischen Inhalte eines Landschaftsplans."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    status: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "9999"] | None,
        Field(
            description="Rechtliche Charakterisierung des Planinhalts.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Festsetzung",
                        "description": "Festsetzung im Landschaftsplan",
                    },
                    "2000": {
                        "name": "Geplant",
                        "description": "Geplante Festsetzung im Landschaftsplan",
                    },
                    "3000": {
                        "name": "NachrichtlichUebernommen",
                        "description": "Nachrichtliche Übernahmen im Landschaftsplan",
                    },
                    "4000": {
                        "name": "DarstellungKennzeichnung",
                        "description": "Darstellungen und Kennzeichnungen im Landschaftsplan.",
                    },
                    "5000": {
                        "name": "FestsetzungInBPlan",
                        "description": "Planinhalt aus dem Bereich Naturschutzrecht, der in einem BPlan festgesetzt wird.",
                    },
                    "9999": {"name": "SonstigerStatus"},
                },
                "typename": "LP_Status",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    konkretisierung: Annotated[
        str | None,
        Field(
            description="Textliche Konkretisierung der rechtlichen Charakterisierung.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gehoertZuLP_Bereich: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "LP_Bereich",
                "stereotype": "Association",
                "reverseProperty": "inhaltLPlan",
                "sourceOrTarget": "source",
                "multiplicity": "0..*",
            }
        ),
    ] = None


class LPPlan(XPPlan):
    """Die Klasse modelliert ein Planwerk mit landschaftsplanerischen Festlegungen, Darstellungen bzw. Festsetzungen."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    bundesland: Annotated[
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
            "2200",
            "2300",
            "2400",
            "2500",
            "3000",
        ],
        Field(
            description="Zuständiges Bundesland",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "BB", "description": "Brandenburg"},
                    "1100": {"name": "BE", "description": "Berlin"},
                    "1200": {"name": "BW", "description": "Baden-Württemberg"},
                    "1300": {"name": "BY", "description": "Bayern"},
                    "1400": {"name": "HB"},
                    "1500": {"name": "HE", "description": "Hessen"},
                    "1600": {"name": "HH"},
                    "1700": {"name": "MV", "description": "Mecklenburg-Vorpommern"},
                    "1800": {"name": "NI", "description": "Niedersachsen"},
                    "1900": {"name": "NW", "description": "Nordrhein-Westfalen"},
                    "2000": {"name": "RP", "description": "Rheinland-Pfalz"},
                    "2100": {"name": "SH", "description": "Schleswig-Holstein"},
                    "2200": {"name": "SL", "description": "Saarland"},
                    "2300": {"name": "SN", "description": "Sachsen"},
                    "2400": {"name": "ST", "description": "Sachsen-Anhalt"},
                    "2500": {"name": "TH", "description": "Thüringen"},
                    "3000": {"name": "Bund", "description": "Der Bund."},
                },
                "typename": "XP_Bundeslaender",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    rechtlicheAussenwirkung: Annotated[
        bool,
        Field(
            description="Gibt an, ob der Plan eine rechtliche Außenwirkung hat.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    planArt: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "9999"]],
        Field(
            description="Typ des vorliegenden Landschaftsplans.",
            json_schema_extra={
                "typename": "LP_PlanArt",
                "stereotype": "Enumeration",
                "multiplicity": "1..*",
                "enumDescription": {
                    "1000": {
                        "name": "Landschaftsprogramm",
                        "description": "Die überörtlichen konkretisierten Ziele, Erfordernisse und Maßnahmen des Naturschutzes und der Landschaftspflege werden für den Bereich eines Landes im Landschaftsprogramm dargestellt (§ 10, Abs .1 BNatSchG)\r\nLandschaftspflege werden für den Bereich eines Landes im Landschaftsprogramm o",
                    },
                    "2000": {
                        "name": "Landschaftsrahmenplan",
                        "description": "Die überörtlichen konkretisierten Ziele, Erfordernisse und Maßnahmen des Naturschutzes und der Landschaftspflege werden für Teile des Landes in Landschaftsrahmenplänen dargestellt (§ 10, Abs .1 BNatSchG)",
                    },
                    "3000": {
                        "name": "Landschaftsplan",
                        "description": "Die für die örtliche Ebene konkretisierten Ziele, Erfordernisse und Maßnahmen des Naturschutzes und der Landschaftspflege werden auf der Grundlage der Landschaftsrahmenpläne für die Gebiete der Gemeinden in Landschaftsplänen  dargestellt. (§ 11, Abs .1 BNatSchG)",
                    },
                    "4000": {
                        "name": "Gruenordnungsplan",
                        "description": "Die für die örtliche Ebene konkretisierten Ziele, Erfordernisse und Maßnahmen des Naturschutzes und der Landschaftspflege werden für Teile eines Gemeindegebiets in Grünordnungsplänen dargestellt. (§ 11, Abs .1  BNatSchG)",
                    },
                    "9999": {"name": "Sonstiges", "description": "sonstige Planart"},
                },
            },
            min_length=1,
        ),
    ]
    sonstPlanArt: Annotated[
        AnyUrl | None,
        Field(
            description='Spezifikation einer "Sonstigen Planart", wenn kein Plantyp aus der Enumeration LP_PlanArt zutreffend ist.',
            json_schema_extra={
                "typename": "LP_SonstPlanArt",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    planungstraegerGKZ: Annotated[
        str,
        Field(
            description="Gemeindekennziffer des Planungsträgers.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    planungstraeger: Annotated[
        str | None,
        Field(
            description="Bezeichnung des Planungsträgers.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    rechtsstand: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000"] | None,
        Field(
            description="Rechtsstand des Plans",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Aufstellungsbeschluss"},
                    "2000": {"name": "Entwurf"},
                    "3000": {"name": "Plan"},
                    "4000": {"name": "Wirksamkeit"},
                    "5000": {"name": "Untergegangen"},
                },
                "typename": "LP_Rechtsstand",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    aufstellungsbeschlussDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Aufstellungsbeschlusses",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    auslegungsDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum der öffentlichen Auslegung.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    tOeBbeteiligungsDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum der Beteiligung der Träger öffentlicher Belange.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    oeffentlichkeitsbeteiligungDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum der Öffentlichkeits-Beteiligung.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    aenderungenBisDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum, bis zum Planänderungen berücksichtigt wurden.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    entwurfsbeschlussDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Entwurfsbeschlusses.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    planbeschlussDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Planbeschlusses.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    inkrafttretenDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Inkrafttretens.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    sonstVerfahrensDatum: Annotated[
        date_aliased | None,
        Field(
            description="Sonstiges Verfahrens-Datum.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    bereich: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "LP_Bereich",
                "stereotype": "Association",
                "reverseProperty": "gehoertZuPlan",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            }
        ),
    ] = None


class LPPunktobjekt(LPObjekt):
    """Basisklasse für alle Objekte eines Landschaftsplans mit punktförmigem Raumbezug (Einzelpunkt oder Punktmenge)."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Point | definitions.MultiPoint,
        Field(
            description="Punktförmiger Raumbezug (Einzelpunkt oder Punktmenge).",
            json_schema_extra={
                "typename": "XP_Punktgeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class LPRasterplanAenderung(XPRasterplanAenderung):
    """false"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    aufstellungsbeschlussDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Aufstellungsbeschlusses",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    auslegungsDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum der öffentlichen Auslegung",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    tOeBbeteiligungsDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum der Beteiligung der Träger öffentlicher Belange",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    aenderungenBisDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum bis zu dem Änderungen des Plans berücksichtigt wurden.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    entwurfsbeschlussDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Entwurfsbeschlusses.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    planbeschlussDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Planbeschlusses.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    inkrafttretenDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Inkrafttretens des Plans..",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    sonstVerfahrensDatum: Annotated[
        date_aliased | None,
        Field(
            description="Sonstiges Verfahrensdatum",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class LPTextAbschnitt(XPTextAbschnitt):
    """Texlich formulierter Inhalt eines Landschaftsplans, der einen anderen Rechtscharakter als das zugrunde liegende Fachobjekt hat (Attribut rechtscharakter des Fachobjektes), oder dem Plan als Ganzes zugeordnet ist."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    status: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "9999"],
        Field(
            description="Rechtscharakter des textlich formulierten Planinhalts.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Festsetzung",
                        "description": "Festsetzung im Landschaftsplan",
                    },
                    "2000": {
                        "name": "Geplant",
                        "description": "Geplante Festsetzung im Landschaftsplan",
                    },
                    "3000": {
                        "name": "NachrichtlichUebernommen",
                        "description": "Nachrichtliche Übernahmen im Landschaftsplan",
                    },
                    "4000": {
                        "name": "DarstellungKennzeichnung",
                        "description": "Darstellungen und Kennzeichnungen im Landschaftsplan.",
                    },
                    "5000": {
                        "name": "FestsetzungInBPlan",
                        "description": "Planinhalt aus dem Bereich Naturschutzrecht, der in einem BPlan festgesetzt wird.",
                    },
                    "9999": {"name": "SonstigerStatus"},
                },
                "typename": "LP_Status",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]


class RPObjekt(XPObjekt):
    """Basisklasse für alle spezifischen Festlegungen eines Regionalplans."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    rechtscharakter: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000"] | None,
        Field(
            description="Rechtscharakter des Planinhalts.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "ZielDerRaumordnung"},
                    "2000": {"name": "GrundsatzDerRaumordnung"},
                    "3000": {"name": "NachrichtlicheUbernahme"},
                    "4000": {"name": "NachrichtlicheUebernahmeZiel"},
                    "5000": {"name": "NachrichtlicheUebernahmeGrundsatz"},
                },
                "typename": "RP_Rechtscharakter",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    konkretisierung: Annotated[
        str | None,
        Field(
            description="Konkretisierung des Rechtscharakters.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gehoertZuRP_Bereich: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "RP_Bereich",
                "stereotype": "Association",
                "reverseProperty": "inhaltRPlan",
                "sourceOrTarget": "source",
                "multiplicity": "0..*",
            }
        ),
    ] = None


class RPPlan(XPPlan):
    """Die Klasse modelliert einen Regionalplan."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    bundesland: Annotated[
        list[
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
                "2200",
                "2300",
                "2400",
                "2500",
                "3000",
            ]
        ],
        Field(
            description="Zuständige Bundesländer",
            json_schema_extra={
                "typename": "XP_Bundeslaender",
                "stereotype": "Enumeration",
                "multiplicity": "1..*",
                "enumDescription": {
                    "1000": {"name": "BB", "description": "Brandenburg"},
                    "1100": {"name": "BE", "description": "Berlin"},
                    "1200": {"name": "BW", "description": "Baden-Württemberg"},
                    "1300": {"name": "BY", "description": "Bayern"},
                    "1400": {"name": "HB"},
                    "1500": {"name": "HE", "description": "Hessen"},
                    "1600": {"name": "HH"},
                    "1700": {"name": "MV", "description": "Mecklenburg-Vorpommern"},
                    "1800": {"name": "NI", "description": "Niedersachsen"},
                    "1900": {"name": "NW", "description": "Nordrhein-Westfalen"},
                    "2000": {"name": "RP", "description": "Rheinland-Pfalz"},
                    "2100": {"name": "SH", "description": "Schleswig-Holstein"},
                    "2200": {"name": "SL", "description": "Saarland"},
                    "2300": {"name": "SN", "description": "Sachsen"},
                    "2400": {"name": "ST", "description": "Sachsen-Anhalt"},
                    "2500": {"name": "TH", "description": "Thüringen"},
                    "3000": {"name": "Bund", "description": "Der Bund."},
                },
            },
            min_length=1,
        ),
    ]
    planArt: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "5100", "9999"] | None,
        Field(
            description="Art des Regionalplans.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Regionalplan"},
                    "2000": {"name": "SachlicherTeilplan"},
                    "3000": {"name": "Braunkohlenplan"},
                    "4000": {
                        "name": "LandesweiterRaumordnungsplan",
                        "description": "Landesweiter Raumordnungsplan",
                    },
                    "5000": {
                        "name": "AWZPlan",
                        "description": "Plan des Bundes für den Gesamtraum und die ausschließliche Wirtschaftszone (AWZ).",
                    },
                    "5100": {
                        "name": "StandortkonzeptBund",
                        "description": "Raumordnungsplan für das Bundesgebiet mit übergreifenden Standortkonzepten für Seehäfen, Binnenhäfen sowie Flughäfen gem. §17 Abs. 2 ROG",
                    },
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "RP_Art",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    sonstPlanArt: Annotated[
        AnyUrl | None,
        Field(
            description="Spezifikation einer weiteren Planart (CodeList) bei planArt == 9999.",
            json_schema_extra={
                "typename": "RP_SonstPlanArt",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    planungsregion: Annotated[
        int | None,
        Field(
            description="Kennziffer der Planungsregion.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    teilabschnitt: Annotated[
        int | None,
        Field(
            description="Kennziffer des Teilabschnittes.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    rechtsstand: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000"] | None,
        Field(
            description="Rechtsstand des Plans.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Aufstellungsbeschluss"},
                    "2000": {"name": "Entwurf"},
                    "3000": {"name": "Plan"},
                    "4000": {"name": "Inkraftgetreten"},
                    "5000": {"name": "Untergegangen"},
                },
                "typename": "RP_Rechtsstand",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    status: Annotated[
        AnyUrl | None,
        Field(
            description="Status des Plans, definiert über eine CodeList.",
            json_schema_extra={
                "typename": "RP_Status",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    aufstellungsbeschlussDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Aufstellungsbeschlusses.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    auslegungStartDatum: Annotated[
        date_aliased | None,
        Field(
            description="Start-Datum der öffentlichen Auslegung.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    auslegungsEndDatum: Annotated[
        date_aliased | None,
        Field(
            description="End-Datum der öffentlichen Auslegung.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    traegerbeteiligungsStartDatum: Annotated[
        date_aliased | None,
        Field(
            description="Start-Datum der Trägerbeteiligung",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    traegerbeteiligungsEndDatum: Annotated[
        date_aliased | None,
        Field(
            description="End-Datum der Trägerbeteiligung.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    aenderungenBisDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum, bis zu dem Planänderungen berücksichtigt wurden.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    entwurfsbeschlussDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Entwurfsbeschlusses",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    planbeschlussDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Planbeschlusses",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    datumDesInkrafttretens: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Inkrafttretens des Plans.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refUmweltbericht: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf den Umweltbericht",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refSatzung: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf die Satzung",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    bereich: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "RP_Bereich",
                "stereotype": "Association",
                "reverseProperty": "gehoertZuPlan",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            }
        ),
    ] = None


class RPPunktobjekt(RPObjekt):
    """Basisklasse für alle Objekte eines Regionalplans mit punktförmigem Raumbezug (Einzelpunkt oder Punktmenge)."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Point | definitions.MultiPoint,
        Field(
            description="Punktförmiger Raumbezug.",
            json_schema_extra={
                "typename": "XP_Punktgeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class RPRasterplanAenderung(XPRasterplanAenderung):
    """false"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    aufstellungsbeschlussDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Aufstellungsbeschlusses",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    auslegungsStartDatum: Annotated[
        date_aliased | None,
        Field(
            description="Beginn der öffentlichen Auslegung",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    auslegungsEndDatum: Annotated[
        date_aliased | None,
        Field(
            description="Ende der öffentlichen Auslegung",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    traegerbeteiligungsStartDatum: Annotated[
        date_aliased | None,
        Field(
            description="Beginn der Beteiligung der Träger öffentlicher Belange",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    traegerbeteiligungsEndDatum: Annotated[
        date_aliased | None,
        Field(
            description="Ende der Beteiligung der Träger öffentlicher Belange",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    aenderungenBisDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum, bis zu dem Änderungen des Plans berücksichtigt wurden.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    entwurfsbeschlussDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Entwurfsbeschlusses.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    satzungsbeschlussDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Satzungsbeschlusses.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    datumDesInkrafttretens: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Inkrafttretens.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class RPTextAbschnitt(XPTextAbschnitt):
    """Texlich formulierter Inhalt eines Regionalplans, der einen anderen Rechtscharakter als das zugrunde liegende Fachobjekt hat (Attribut rechtscharakter des Fachobjektes), oder dem Plan als Ganzes zugeordnet ist."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    rechtscharakter: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000"],
        Field(
            description="Rechtscharakter des textlich formulierten Planinhalts.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "ZielDerRaumordnung"},
                    "2000": {"name": "GrundsatzDerRaumordnung"},
                    "3000": {"name": "NachrichtlicheUbernahme"},
                    "4000": {"name": "NachrichtlicheUebernahmeZiel"},
                    "5000": {"name": "NachrichtlicheUebernahmeGrundsatz"},
                },
                "typename": "RP_Rechtscharakter",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]


class SOObjekt(XPObjekt):
    """Basisklasse für die Inhalte sonstiger raumbezogener Planwerke sowie von Klassen zur Modellierung nachrichtlicher Übernahmen."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    rechtscharakter: Annotated[
        Literal["3000", "4000", "5000", "9999"] | None,
        Field(
            description="Rechtscharakter des Planinhalts.",
            json_schema_extra={
                "enumDescription": {
                    "3000": {"name": "Hinweis"},
                    "4000": {"name": "Vermerk"},
                    "5000": {"name": "Kennzeichnung"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "SO_Rechtscharakter",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    sonstRechtscharakter: Annotated[
        AnyUrl | None,
        Field(
            description="Klassifizierung des Rechtscharakters wenn das Attribut 'rechtscharakter' den Wert 'Sonstiges' (1000)  hat.",
            json_schema_extra={
                "typename": "SO_SonstRechtscharakter",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gehoertZuSO_Bereich: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "SO_Bereich",
                "stereotype": "Association",
                "reverseProperty": "inhaltSoPlan",
                "sourceOrTarget": "source",
                "multiplicity": "0..*",
            }
        ),
    ] = None


class SOPlan(XPPlan):
    """Klasse für sonstige, z. B. länderspezifische raumbezogene Planwerke."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    planTyp: Annotated[
        AnyUrl,
        Field(
            description="Typ des Plans.",
            json_schema_extra={
                "typename": "SO_PlanTyp",
                "stereotype": "Codelist",
                "multiplicity": "1",
            },
        ),
    ]
    plangeber: Annotated[
        XPPlangeber | None,
        Field(
            description="Für den Plan zuständige Stelle.",
            json_schema_extra={
                "typename": "XP_Plangeber",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    bereich: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "SO_Bereich",
                "stereotype": "Association",
                "reverseProperty": "gehoertZuPlan",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            }
        ),
    ] = None


class SOPunktobjekt(SOObjekt):
    """Basisklasse für Objekte mit punktförmigem Raumbezug (Einzelpunkt oder Punktmenge)."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Point | definitions.MultiPoint,
        Field(
            json_schema_extra={
                "typename": "XP_Punktgeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            }
        ),
    ]


class SORasterplanAenderung(XPRasterplanAenderung):
    """false"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class SOTextAbschnitt(XPTextAbschnitt):
    """Texlich formulierter Inhalt eines Sonstigen Plans, der einen anderen Rechtscharakter als das zugrunde liegende Fachobjekt hat (Attribut rechtscharakter des Fachobjektes), oder dem Plan als Ganzes zugeordnet ist."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    rechtscharakter: Annotated[
        Literal["3000", "4000", "5000", "9999"],
        Field(
            description="Rechtscharakter des textlich formulierten Planinhalts.",
            json_schema_extra={
                "enumDescription": {
                    "3000": {"name": "Hinweis"},
                    "4000": {"name": "Vermerk"},
                    "5000": {"name": "Kennzeichnung"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "SO_Rechtscharakter",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]


class XPBegruendungAbschnitt(BaseFeature):
    """Ein Abschnitt der Begründung des Plans."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    id: str | None = None
    schluessel: Annotated[
        str | None,
        Field(
            description="Schlüssel zur Referenzierung des Abschnitts von einem Fachobjekt aus.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    text: Annotated[
        str | None,
        Field(
            description="Inhalt eines Abschnitts der Begründung.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refText: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf ein externes Dokument das den Begründungs-Abschnitt enthält.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class XPLTO(XPTPO):
    """Textförmiges Präsentationsobjekt mit linienförmiger Textgeometrie. Entspricht der ALKIS-Objektklasse AP_LTO."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Line | definitions.MultiLine,
        Field(
            json_schema_extra={
                "typename": "XP_Liniengeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            }
        ),
    ]


class XPPTO(XPTPO):
    """Textförmiges Präsentationsobjekt mit punktförmiger Festlegung der Textposition. Entspricht der ALKIS-Objektklasse AP_PTO."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Point | definitions.MultiPoint,
        Field(
            json_schema_extra={
                "typename": "XP_Punktgeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            }
        ),
    ]
    drehwinkel: Annotated[
        definitions.Angle | None,
        Field(
            description="Winkel um den der Text oder die Signatur mit punktförmiger Bezugsgeometrie aus der Horizontalen gedreht ist. Angabe im Bogenmaß; Zählweise im mathematisch positiven Sinn (von Ost über Nord nach West und Süd).",
            json_schema_extra={
                "typename": "Angle",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "grad",
            },
        ),
    ] = None


class BPBaugebiet(BPObjekt):
    """Aggregation verschiedener Teilflächen eines Baugebiets. Die spezifizierten Attribute gelten für alle aggregierten Objekte BP_BaugebietsTeilFlaeche, in denen das Attribut nicht belegt ist."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    DNmin: Annotated[
        definitions.Angle | None,
        Field(
            description="Minimal zulässige Dachneigung bei einer Bereichsangabe.",
            json_schema_extra={
                "typename": "Angle",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "grad",
            },
        ),
    ] = None
    DNmax: Annotated[
        definitions.Angle | None,
        Field(
            description="Maximal zulässige Dachneigung bei einer Bereichsangabe.",
            json_schema_extra={
                "typename": "Angle",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "grad",
            },
        ),
    ] = None
    DN: Annotated[
        definitions.Angle | None,
        Field(
            description="Maximal zulässige Dachneigung.",
            json_schema_extra={
                "typename": "Angle",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "grad",
            },
        ),
    ] = None
    DNZwingend: Annotated[
        definitions.Angle | None,
        Field(
            description="Zwingend vorgeschriebene Dachneigung.",
            json_schema_extra={
                "typename": "Angle",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "grad",
            },
        ),
    ] = None
    FR: Annotated[
        definitions.Angle | None,
        Field(
            description="Vorgeschriebene Firstrichtung (Gradangabe)",
            json_schema_extra={
                "typename": "Angle",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "grad",
            },
        ),
    ] = None
    dachform: Annotated[
        list[
            Literal[
                "1000",
                "2100",
                "2200",
                "3100",
                "3200",
                "3300",
                "3400",
                "3500",
                "3600",
                "3700",
                "3800",
                "3900",
                "4000",
                "5000",
                "9999",
            ]
        ]
        | None,
        Field(
            description="Vorgeschriebene Dachformen",
            json_schema_extra={
                "typename": "BP_Dachform",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Flachdach"},
                    "2100": {"name": "Pultdach"},
                    "2200": {"name": "Versetztes Pultdach"},
                    "3100": {"name": "Satteldach"},
                    "3200": {"name": "Walmdach"},
                    "3300": {"name": "Krüppelwalmdach"},
                    "3400": {"name": "Mansarddach"},
                    "3500": {"name": "Zeltdach"},
                    "3600": {"name": "Kegeldach"},
                    "3700": {"name": "Kuppeldach"},
                    "3800": {"name": "Sheddach"},
                    "3900": {"name": "Bogendach"},
                    "4000": {"name": "Turmdach"},
                    "5000": {"name": "Mischform"},
                    "9999": {"name": "Sonstiges"},
                },
            },
        ),
    ] = None
    detaillierteDachform: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definierte Dachform.",
            json_schema_extra={
                "typename": "BP_DetailDachform",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    MaxZahlWohnungen: Annotated[
        int | None,
        Field(
            description="Höchstzulässige Zahl der Wohnungen in Wohngebäuden",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Fmin: Annotated[
        definitions.Area | None,
        Field(
            description="Mindestmaß für die Größe (Fläche) eines Baugrundstücks.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Fmax: Annotated[
        definitions.Area | None,
        Field(
            description="Höchstmaß für die Größe (Fläche) eines Baugrundstücks.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Bmin: Annotated[
        definitions.Length | None,
        Field(
            description="Minimale Breite von Baugrundstücken",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Bmax: Annotated[
        definitions.Length | None,
        Field(
            description="Maximale Breite von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Tmin: Annotated[
        definitions.Length | None,
        Field(
            description="Minimale Tiefe von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Tmax: Annotated[
        definitions.Length | None,
        Field(
            description="Maximale Tiefe von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    GFZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Geschossflächenzahl .",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl bei einer Bereichsangabe. Das Attribut GFZmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZ_Ausn: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl als Ausnahme.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFmin: Annotated[
        definitions.Area | None,
        Field(
            description="Minimal zulässige Geschossfläche",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GFmax: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Geschossfläche bei einer Bereichsabgabe. Das Attribut GFmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GF: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Geschossfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GF_Ausn: Annotated[
        definitions.Area | None,
        Field(
            description="Ausnahmsweise maximal zulässige Geschossfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    BMZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Baumassenzahl",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Baumassenzahl bei einer Bereichsangabe. Das Attribut BMZmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Baumassenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZ_Ausn: Annotated[
        float | None,
        Field(
            description="Ausnahmsweise maximal zulässige Baumassenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMmin: Annotated[
        definitions.Volume | None,
        Field(
            description="Minimal zulässinge Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BMmax: Annotated[
        definitions.Volume | None,
        Field(
            description="Maximal zulässinge Baumasse bei einer Bereichsangabe. Das Attribut BMmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BM: Annotated[
        definitions.Volume | None,
        Field(
            description="Maximal zulässige Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BM_Ausn: Annotated[
        definitions.Volume | None,
        Field(
            description="Ausnahmsweise maximal zulässige Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    GRZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Grundflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Grundflächenzahl bei einer Bereichsangabe.  Das Attribut GRZmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Grundflächenzahl",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZ_Ausn: Annotated[
        float | None,
        Field(
            description="Ausnahmsweise maximal zulässige Grundflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRmin: Annotated[
        definitions.Area | None,
        Field(
            description="Minimal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GRmax: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Grundfläche bei einer Bereichsangabe. Das Attribut GRmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GR: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GR_Ausn: Annotated[
        definitions.Area | None,
        Field(
            description="Ausnahmsweise maximal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Zmin: Annotated[
        int | None,
        Field(
            description="Minimal zulässige Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Zmax: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der oberirdischen Vollgeschosse bei einer Bereichsangabe. Das Attribut Zmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Zzwingend: Annotated[
        int | None,
        Field(
            description="Zwingend vorgeschriebene Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z: Annotated[
        int | None,
        Field(
            description="Maximalzahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Ausn: Annotated[
        int | None,
        Field(
            description="Ausnahmsweise maximal zulässige Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Staffel: Annotated[
        int | None,
        Field(
            description="Maximalzahl von oberirdischen zurückgesetzten Vollgeschossen als Staffelgeschoss..",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Dach: Annotated[
        int | None,
        Field(
            description="Maximalzahl der zusätzlich erlaubten Dachgeschosse, die gleichzeitig Vollgeschosse sind.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUmin: Annotated[
        int | None,
        Field(
            description="Minimal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUmax: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der unterirdischen Geschosse bei einer Bereichsangabe. Das Attribut ZUmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUzwingend: Annotated[
        int | None,
        Field(
            description="Zwingend vorgeschriebene Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZU: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZU_Ausn: Annotated[
        int | None,
        Field(
            description="Ausnahmsweise maximal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    allgArtDerBaulNutzung: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"] | None,
        Field(
            description="Spezifikation der allgemeinen Art der baulichen N utzung.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "WohnBauflaeche"},
                    "2000": {"name": "GemischteBauflaeche"},
                    "3000": {"name": "GewerblicheBauflaeche"},
                    "4000": {"name": "SonderBauflaeche"},
                    "9999": {"name": "SonstigeBauflaeche"},
                },
                "typename": "XP_AllgArtDerBaulNutzung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    besondereArtDerBaulNutzung: Annotated[
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
            "2000",
            "2100",
            "3000",
            "4000",
            "9999",
        ]
        | None,
        Field(
            description="Festsetzung der Art der baulichen Nutzung (§9, Abs. 1, Nr. 1 BauGB).",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Kleinsiedlungsgebiet",
                        "description": "Kleinsiedlungsgebiet",
                    },
                    "1100": {
                        "name": "ReinesWohngebiet",
                        "description": "Reines Wohngebiet",
                    },
                    "1200": {
                        "name": "AllgWohngebiet",
                        "description": "Allgemeines Wohngebiet",
                    },
                    "1300": {
                        "name": "BesonderesWohngebiet",
                        "description": "Besonderes Wohngebiet",
                    },
                    "1400": {"name": "Dorfgebiet", "description": "Dorfgebiet"},
                    "1500": {"name": "Mischgebiet"},
                    "1600": {"name": "Kerngebiet", "description": "Kerngebiet"},
                    "1700": {"name": "Gewerbegebiet"},
                    "1800": {
                        "name": "Industriegebiet",
                        "description": "Industriegebiet",
                    },
                    "2000": {
                        "name": "SondergebietErholung",
                        "description": "Sondergebiet, das der Erholung dient (§ 10 BauNVO); z.B. Wochenendhausgebiet",
                    },
                    "2100": {
                        "name": "SondergebietSonst",
                        "description": "Sonstiges Sondergebiet (§ 11 BauNVO); z.B. Klinikgebiet",
                    },
                    "3000": {"name": "Wochenendhausgebiet"},
                    "4000": {"name": "Sondergebiet"},
                    "9999": {
                        "name": "SonstigesGebiet",
                        "description": "Sonstiges Gebiet",
                    },
                },
                "typename": "XP_BesondereArtDerBaulNutzung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    sondernutzung: Annotated[
        Literal[
            "1000",
            "1100",
            "1200",
            "1300",
            "1400",
            "1500",
            "1600",
            "16000",
            "16001",
            "16002",
            "1700",
            "1800",
            "1900",
            "2000",
            "2100",
            "2200",
            "2300",
            "2400",
            "2500",
            "2600",
            "2700",
            "2800",
            "2900",
            "9999",
        ]
        | None,
        Field(
            description='Bei Nutzungsform "Sondergebiet": Spezifische Nutzung der Sonderbaufläche nach §§ 10 und 11 BauNVO.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Wochenendhausgebiet"},
                    "1100": {"name": "Ferienhausgebiet"},
                    "1200": {"name": "Campingplatzgebiet"},
                    "1300": {"name": "Kurgebiet"},
                    "1400": {"name": "SonstSondergebietErholung"},
                    "1500": {"name": "Einzelhandelsgebiet"},
                    "1600": {"name": "GrossflaechigerEinzelhandel"},
                    "16000": {"name": "Ladengebiet"},
                    "16001": {"name": "Einkaufszentrum"},
                    "16002": {"name": "SonstGrossflEinzelhandel"},
                    "1700": {"name": "Verkehrsuebungsplatz"},
                    "1800": {"name": "Hafengebiet"},
                    "1900": {"name": "SondergebietErneuerbareEnergie"},
                    "2000": {"name": "SondergebietMilitaer"},
                    "2100": {"name": "SondergebietLandwirtschaft"},
                    "2200": {"name": "SondergebietSport"},
                    "2300": {"name": "SondergebietGesundheitSoziales"},
                    "2400": {"name": "Golfplatz"},
                    "2500": {"name": "SondergebietKultur"},
                    "2600": {"name": "SondergebietTourismus"},
                    "2700": {"name": "SondergebietBueroUndVerwaltung"},
                    "2800": {"name": "SondergebietHochschuleEinrichtungen"},
                    "2900": {"name": "SondergebietMesse"},
                    "9999": {"name": "SondergebietAndereNutzungen"},
                },
                "typename": "XP_Sondernutzungen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteArtDerBaulNutzung: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definierte Nutzungsart.",
            json_schema_extra={
                "typename": "BP_DetailArtDerBaulNutzung",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    nutzungText: Annotated[
        str | None,
        Field(
            description='Bei Nutzungsform "Sondergebiet": Kurzform der besonderen Art der baulichen Nutzung.',
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    abweichungBauNVO: Annotated[
        Literal["1000", "2000", "3000", "9999"] | None,
        Field(
            description="Art der Abweichung von der BauNVO.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "EinschraenkungNutzung",
                        "description": "Einschränkung einer generell erlaubten Nutzung.",
                    },
                    "2000": {
                        "name": "AusschlussNutzung",
                        "description": "Ausschluss einer generell erlaubten Nutzung.",
                    },
                    "3000": {
                        "name": "AusweitungNutzung",
                        "description": "Eine neu ausnahmsweise zulässige Nutzung wird generell zulässig.",
                    },
                    "9999": {
                        "name": "SonstAbweichung",
                        "description": "Sonstige Abweichung.",
                    },
                },
                "typename": "XP_AbweichungBauNVOTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    bauweise: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Festsetzung der Bauweise  (§9, Abs. 1, Nr. 2 BauGB).",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "OffeneBauweise",
                        "description": "Offene Bauweise",
                    },
                    "2000": {
                        "name": "GeschlosseneBauweise",
                        "description": "Geschlossene Bauweise",
                    },
                    "3000": {
                        "name": "AbweichendeBauweise",
                        "description": "Abweichende Bauweise",
                    },
                },
                "typename": "BP_Bauweise",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    abweichendeBauweise: Annotated[
        AnyUrl | None,
        Field(
            description='Nähere Bezeichnung einer "Abweichenden Bauweise".',
            json_schema_extra={
                "typename": "BP_AbweichendeBauweise",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    vertikaleDifferenzierung: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob eine vertikale Differenzierung des Gebäudes vorgeschrieben ist.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False
    bebauungsArt: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "6000", "7000"] | None,
        Field(
            description="Detaillierte Festsetzung der Bauweise (§9, Abs. 1, Nr. 2 BauGB).",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Einzelhaeuser",
                        "description": "Nur Einzelhäuser zulässig.",
                    },
                    "2000": {
                        "name": "Doppelhaeuser",
                        "description": "Nur Doppelhäuser zulässig.",
                    },
                    "3000": {
                        "name": "Hausgruppen",
                        "description": "Nur Hausgruppen zulässig.",
                    },
                    "4000": {
                        "name": "EinzelDoppelhaeuser",
                        "description": "Nur Einzel- oder Doppelhäuser zulässig.",
                    },
                    "5000": {
                        "name": "EinzelhaeuserHausgruppen",
                        "description": "Nur Einzelhäuser oder Hausgruppen zulässig.",
                    },
                    "6000": {
                        "name": "DoppelhaeuserHausgruppen",
                        "description": "Nur Doppelhäuser oder Hausgruppen zulässig.",
                    },
                    "7000": {"name": "Reihenhaeuser"},
                },
                "typename": "BP_BebauungsArt",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    bebauungVordereGrenze: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Festsetzung der Bebauung der vorderen Grundstücksgrenze (§9, Abs. 1, Nr. 2 BauGB).",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Verboten",
                        "description": "Eine Bebauung der Grenze ist verboten.",
                    },
                    "2000": {
                        "name": "Erlaubt",
                        "description": "Eine Bebauung der Grenze ist erlaubt.",
                    },
                    "3000": {
                        "name": "Erzwungen",
                        "description": "Eine Bebauung der Grenze ist vorgeschrieben.",
                    },
                },
                "typename": "BP_GrenzBebauung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    bebauungRueckwaertigeGrenze: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Festsetzung der Bebauung der rückwärtigen Grundstücksgrenze (§9, Abs. 1, Nr. 2 BauGB).",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Verboten",
                        "description": "Eine Bebauung der Grenze ist verboten.",
                    },
                    "2000": {
                        "name": "Erlaubt",
                        "description": "Eine Bebauung der Grenze ist erlaubt.",
                    },
                    "3000": {
                        "name": "Erzwungen",
                        "description": "Eine Bebauung der Grenze ist vorgeschrieben.",
                    },
                },
                "typename": "BP_GrenzBebauung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    bebauungSeitlicheGrenze: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Festsetzung der Bebauung der seitlichen Grundstücksgrenze (§9, Abs. 1, Nr. 2 BauGB).",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Verboten",
                        "description": "Eine Bebauung der Grenze ist verboten.",
                    },
                    "2000": {
                        "name": "Erlaubt",
                        "description": "Eine Bebauung der Grenze ist erlaubt.",
                    },
                    "3000": {
                        "name": "Erzwungen",
                        "description": "Eine Bebauung der Grenze ist vorgeschrieben.",
                    },
                },
                "typename": "BP_GrenzBebauung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refGebaeudequerschnitt: Annotated[
        list[XPExterneReferenz] | None,
        Field(
            description="Referenz auf ein Dokument mit vorgeschriebenen Gebäudequerschnitten.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    zugunstenVon: Annotated[
        str | None,
        Field(
            description="Angabe des Begünstigen einer Ausweisung.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    flaechenteil: Annotated[
        list[AnyUrl | UUID],
        Field(
            json_schema_extra={
                "typename": "BP_BaugebietsTeilFlaeche",
                "stereotype": "Association",
                "multiplicity": "1..*",
            }
        ),
    ]
    abweichungText: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": [
                    "BP_TextAbschnitt",
                    "FP_TextAbschnitt",
                    "LP_TextAbschnitt",
                    "RP_TextAbschnitt",
                    "SO_TextAbschnitt",
                    "XP_TextAbschnitt",
                ],
                "stereotype": "Association",
                "multiplicity": "0..*",
            }
        ),
    ] = None


class BPEinfahrtPunkt(BPPunktobjekt):
    """Einfahrt (§9 Abs. 1 Nr. 11 und Abs. 6 BauGB)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    richtung: Annotated[
        definitions.Angle,
        Field(
            description="Winkel-Richtung der Einfahrt (in Grad).",
            json_schema_extra={
                "typename": "Angle",
                "stereotype": "Measure",
                "multiplicity": "1",
                "uom": "grad",
            },
        ),
    ]


class BPFlaechenobjekt(BPObjekt):
    """Basisklasse für alle Objekte eines Bebauungsplans mit flächenhaftem Raumbezug. Die von BP_Flaechenobjekt abgeleiteten Fachobjekte können sowohl als Flächenschlussobjekte als auch als Überlagerungsobjekte auftreten."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Polygon | definitions.MultiPolygon,
        Field(
            description="Flächenhafter Raumbezug des Objektes (Eine Einzelfläche oder eine Menge von Flächen, die sich nicht überlappen dürfen). .",
            json_schema_extra={
                "typename": "XP_Flaechengeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]
    flaechenschluss: Annotated[
        bool,
        Field(
            description="Zeigt an, ob das Objekt als Flächenschlussobjekt oder Überlagerungsobjekt gebildet werden soll.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]


class BPFlaechenschlussobjekt(BPFlaechenobjekt):
    """Basisklasse für alle Objekte eines Bebauungsplans mit flächenhaftem Raumbezug, die immer Flächenschlussobjekte sind."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class BPGemeinbedarfsFlaeche(BPFlaechenschlussobjekt):
    """Einrichtungen und Anlagen zur Versorgung mit Gütern und Dienstleistungen des öffentlichen und privaten Bereichs, hier Flächen für den Gemeindebedarf (§9, Abs. 1, Nr.5 und Abs. 6 BauGB)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    MaxZahlWohnungen: Annotated[
        int | None,
        Field(
            description="Höchstzulässige Zahl der Wohnungen in Wohngebäuden",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Fmin: Annotated[
        definitions.Area | None,
        Field(
            description="Mindestmaß für die Größe (Fläche) eines Baugrundstücks.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Fmax: Annotated[
        definitions.Area | None,
        Field(
            description="Höchstmaß für die Größe (Fläche) eines Baugrundstücks.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Bmin: Annotated[
        definitions.Length | None,
        Field(
            description="Minimale Breite von Baugrundstücken",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Bmax: Annotated[
        definitions.Length | None,
        Field(
            description="Maximale Breite von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Tmin: Annotated[
        definitions.Length | None,
        Field(
            description="Minimale Tiefe von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Tmax: Annotated[
        definitions.Length | None,
        Field(
            description="Maximale Tiefe von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    GFZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Geschossflächenzahl .",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl bei einer Bereichsangabe. Das Attribut GFZmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZ_Ausn: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl als Ausnahme.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFmin: Annotated[
        definitions.Area | None,
        Field(
            description="Minimal zulässige Geschossfläche",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GFmax: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Geschossfläche bei einer Bereichsabgabe. Das Attribut GFmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GF: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Geschossfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GF_Ausn: Annotated[
        definitions.Area | None,
        Field(
            description="Ausnahmsweise maximal zulässige Geschossfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    BMZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Baumassenzahl",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Baumassenzahl bei einer Bereichsangabe. Das Attribut BMZmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Baumassenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZ_Ausn: Annotated[
        float | None,
        Field(
            description="Ausnahmsweise maximal zulässige Baumassenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMmin: Annotated[
        definitions.Volume | None,
        Field(
            description="Minimal zulässinge Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BMmax: Annotated[
        definitions.Volume | None,
        Field(
            description="Maximal zulässinge Baumasse bei einer Bereichsangabe. Das Attribut BMmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BM: Annotated[
        definitions.Volume | None,
        Field(
            description="Maximal zulässige Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BM_Ausn: Annotated[
        definitions.Volume | None,
        Field(
            description="Ausnahmsweise maximal zulässige Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    GRZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Grundflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Grundflächenzahl bei einer Bereichsangabe.  Das Attribut GRZmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Grundflächenzahl",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZ_Ausn: Annotated[
        float | None,
        Field(
            description="Ausnahmsweise maximal zulässige Grundflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRmin: Annotated[
        definitions.Area | None,
        Field(
            description="Minimal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GRmax: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Grundfläche bei einer Bereichsangabe. Das Attribut GRmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GR: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GR_Ausn: Annotated[
        definitions.Area | None,
        Field(
            description="Ausnahmsweise maximal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Zmin: Annotated[
        int | None,
        Field(
            description="Minimal zulässige Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Zmax: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der oberirdischen Vollgeschosse bei einer Bereichsangabe. Das Attribut Zmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Zzwingend: Annotated[
        int | None,
        Field(
            description="Zwingend vorgeschriebene Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z: Annotated[
        int | None,
        Field(
            description="Maximalzahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Ausn: Annotated[
        int | None,
        Field(
            description="Ausnahmsweise maximal zulässige Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Staffel: Annotated[
        int | None,
        Field(
            description="Maximalzahl von oberirdischen zurückgesetzten Vollgeschossen als Staffelgeschoss..",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Dach: Annotated[
        int | None,
        Field(
            description="Maximalzahl der zusätzlich erlaubten Dachgeschosse, die gleichzeitig Vollgeschosse sind.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUmin: Annotated[
        int | None,
        Field(
            description="Minimal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUmax: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der unterirdischen Geschosse bei einer Bereichsangabe. Das Attribut ZUmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUzwingend: Annotated[
        int | None,
        Field(
            description="Zwingend vorgeschriebene Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZU: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZU_Ausn: Annotated[
        int | None,
        Field(
            description="Ausnahmsweise maximal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    zweckbestimmung: Annotated[
        list[
            Literal[
                "1000",
                "1200",
                "1400",
                "1600",
                "1800",
                "2000",
                "2200",
                "2400",
                "2600",
                "9999",
            ]
        ]
        | None,
        Field(
            description="Allgemeine Zweckbestimmungen der festgesetzten Fläche",
            json_schema_extra={
                "typename": "XP_ZweckbestimmungGemeinbedarf",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {
                        "name": "OffentlicheVerwaltung",
                        "description": "Einrichtungen und Anlagen für öffentliche Verwaltung",
                    },
                    "1200": {
                        "name": "BildungForschung",
                        "description": "Einrichtungen und Anlagen für Schulen und sonstige Bildungs- und Forschungseinrichtungen.",
                    },
                    "1400": {
                        "name": "Kirche",
                        "description": "Kirchliche Einrichtungen",
                    },
                    "1600": {
                        "name": "Sozial",
                        "description": "Einrichtungen und Anlagen für soziale Zwecke.",
                    },
                    "1800": {
                        "name": "Gesundheit",
                        "description": "Einrichtungen und Anlagen für gesundheitliche Zwecke.",
                    },
                    "2000": {
                        "name": "Kultur",
                        "description": "Einrichtungen und Anlagen für kulturelle Zwecke.",
                    },
                    "2200": {
                        "name": "Sport",
                        "description": "Einrichtungen und Anlagen für sportliche Zwecke.",
                    },
                    "2400": {
                        "name": "SicherheitOrdnung",
                        "description": "Einrichtungen und Anlagen für Sicherheit und Ordnung.",
                    },
                    "2600": {
                        "name": "Infrastruktur",
                        "description": "Einrichtungen und Anlagen der Infrastruktur.",
                    },
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
            },
        ),
    ] = None
    weitereZweckbestimmung1: Annotated[
        Literal[
            "1000",
            "1200",
            "1400",
            "1600",
            "1800",
            "2000",
            "2200",
            "2400",
            "2600",
            "9999",
        ]
        | None,
        Field(
            description='Weitere allgemeine Zweckbestimmung der festgesetzten Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "OffentlicheVerwaltung",
                        "description": "Einrichtungen und Anlagen für öffentliche Verwaltung",
                    },
                    "1200": {
                        "name": "BildungForschung",
                        "description": "Einrichtungen und Anlagen für Schulen und sonstige Bildungs- und Forschungseinrichtungen.",
                    },
                    "1400": {
                        "name": "Kirche",
                        "description": "Kirchliche Einrichtungen",
                    },
                    "1600": {
                        "name": "Sozial",
                        "description": "Einrichtungen und Anlagen für soziale Zwecke.",
                    },
                    "1800": {
                        "name": "Gesundheit",
                        "description": "Einrichtungen und Anlagen für gesundheitliche Zwecke.",
                    },
                    "2000": {
                        "name": "Kultur",
                        "description": "Einrichtungen und Anlagen für kulturelle Zwecke.",
                    },
                    "2200": {
                        "name": "Sport",
                        "description": "Einrichtungen und Anlagen für sportliche Zwecke.",
                    },
                    "2400": {
                        "name": "SicherheitOrdnung",
                        "description": "Einrichtungen und Anlagen für Sicherheit und Ordnung.",
                    },
                    "2600": {
                        "name": "Infrastruktur",
                        "description": "Einrichtungen und Anlagen der Infrastruktur.",
                    },
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungGemeinbedarf",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung2: Annotated[
        Literal[
            "1000",
            "1200",
            "1400",
            "1600",
            "1800",
            "2000",
            "2200",
            "2400",
            "2600",
            "9999",
        ]
        | None,
        Field(
            description='Weitere allgemeine Zweckbestimmung der festgesetzten Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "OffentlicheVerwaltung",
                        "description": "Einrichtungen und Anlagen für öffentliche Verwaltung",
                    },
                    "1200": {
                        "name": "BildungForschung",
                        "description": "Einrichtungen und Anlagen für Schulen und sonstige Bildungs- und Forschungseinrichtungen.",
                    },
                    "1400": {
                        "name": "Kirche",
                        "description": "Kirchliche Einrichtungen",
                    },
                    "1600": {
                        "name": "Sozial",
                        "description": "Einrichtungen und Anlagen für soziale Zwecke.",
                    },
                    "1800": {
                        "name": "Gesundheit",
                        "description": "Einrichtungen und Anlagen für gesundheitliche Zwecke.",
                    },
                    "2000": {
                        "name": "Kultur",
                        "description": "Einrichtungen und Anlagen für kulturelle Zwecke.",
                    },
                    "2200": {
                        "name": "Sport",
                        "description": "Einrichtungen und Anlagen für sportliche Zwecke.",
                    },
                    "2400": {
                        "name": "SicherheitOrdnung",
                        "description": "Einrichtungen und Anlagen für Sicherheit und Ordnung.",
                    },
                    "2600": {
                        "name": "Infrastruktur",
                        "description": "Einrichtungen und Anlagen der Infrastruktur.",
                    },
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungGemeinbedarf",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung3: Annotated[
        Literal[
            "1000",
            "1200",
            "1400",
            "1600",
            "1800",
            "2000",
            "2200",
            "2400",
            "2600",
            "9999",
        ]
        | None,
        Field(
            description='Weitere allgemeine Zweckbestimmung der festgesetzten Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "OffentlicheVerwaltung",
                        "description": "Einrichtungen und Anlagen für öffentliche Verwaltung",
                    },
                    "1200": {
                        "name": "BildungForschung",
                        "description": "Einrichtungen und Anlagen für Schulen und sonstige Bildungs- und Forschungseinrichtungen.",
                    },
                    "1400": {
                        "name": "Kirche",
                        "description": "Kirchliche Einrichtungen",
                    },
                    "1600": {
                        "name": "Sozial",
                        "description": "Einrichtungen und Anlagen für soziale Zwecke.",
                    },
                    "1800": {
                        "name": "Gesundheit",
                        "description": "Einrichtungen und Anlagen für gesundheitliche Zwecke.",
                    },
                    "2000": {
                        "name": "Kultur",
                        "description": "Einrichtungen und Anlagen für kulturelle Zwecke.",
                    },
                    "2200": {
                        "name": "Sport",
                        "description": "Einrichtungen und Anlagen für sportliche Zwecke.",
                    },
                    "2400": {
                        "name": "SicherheitOrdnung",
                        "description": "Einrichtungen und Anlagen für Sicherheit und Ordnung.",
                    },
                    "2600": {
                        "name": "Infrastruktur",
                        "description": "Einrichtungen und Anlagen der Infrastruktur.",
                    },
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungGemeinbedarf",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung4: Annotated[
        Literal[
            "1000",
            "1200",
            "1400",
            "1600",
            "1800",
            "2000",
            "2200",
            "2400",
            "2600",
            "9999",
        ]
        | None,
        Field(
            description='Weitere allgemeine Zweckbestimmung der festgesetzten Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "OffentlicheVerwaltung",
                        "description": "Einrichtungen und Anlagen für öffentliche Verwaltung",
                    },
                    "1200": {
                        "name": "BildungForschung",
                        "description": "Einrichtungen und Anlagen für Schulen und sonstige Bildungs- und Forschungseinrichtungen.",
                    },
                    "1400": {
                        "name": "Kirche",
                        "description": "Kirchliche Einrichtungen",
                    },
                    "1600": {
                        "name": "Sozial",
                        "description": "Einrichtungen und Anlagen für soziale Zwecke.",
                    },
                    "1800": {
                        "name": "Gesundheit",
                        "description": "Einrichtungen und Anlagen für gesundheitliche Zwecke.",
                    },
                    "2000": {
                        "name": "Kultur",
                        "description": "Einrichtungen und Anlagen für kulturelle Zwecke.",
                    },
                    "2200": {
                        "name": "Sport",
                        "description": "Einrichtungen und Anlagen für sportliche Zwecke.",
                    },
                    "2400": {
                        "name": "SicherheitOrdnung",
                        "description": "Einrichtungen und Anlagen für Sicherheit und Ordnung.",
                    },
                    "2600": {
                        "name": "Infrastruktur",
                        "description": "Einrichtungen und Anlagen der Infrastruktur.",
                    },
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungGemeinbedarf",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    besondereZweckbestimmung: Annotated[
        list[
            Literal[
                "10000",
                "10001",
                "10002",
                "10003",
                "12000",
                "12001",
                "12002",
                "12003",
                "12004",
                "14000",
                "14001",
                "14002",
                "14003",
                "16000",
                "16001",
                "16002",
                "16003",
                "16004",
                "18000",
                "18001",
                "20000",
                "20001",
                "20002",
                "22000",
                "22001",
                "22002",
                "24000",
                "24001",
                "24002",
                "24003",
                "26000",
                "26001",
            ]
        ]
        | None,
        Field(
            description="Besondere Zweckbestimmungen der festgesetzten Fläche, die die zugehörigen allgemeinen Zweckbestimmungen detaillieren oder ersetzen.",
            json_schema_extra={
                "typename": "XP_BesondereZweckbestGemeinbedarf",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "10000": {
                        "name": "KommunaleEinrichtung",
                        "description": "Kommunale Einrichtung wie z. B. Rathaus, Gesundheitsamt, Gesundheitsfürsorgestelle, Gartenbauamt, Gartenarbeitsstützpunkt, Fuhrpark.",
                    },
                    "10001": {
                        "name": "BetriebOeffentlZweckbestimmung",
                        "description": "Betrieb mit öffentlicher Zweckbestimmung wie z.B. ein Stadtreinigungsbetrieb, Autobusbetriebshof, Omnibusbahnhof.",
                    },
                    "10002": {
                        "name": "AnlageBundLand",
                        "description": "Eine Anlage des Bundes oder eines Bundeslandes wie z. B.  Arbeitsamt, Autobahnmeisterei, Brückenmeisterei, Patentamt, Wasserbauhof, Finanzamt.",
                    },
                    "10003": {
                        "name": "SonstigeOeffentlicheVerwaltung",
                        "description": "Sonstige Einrichtung oder Anlage der öffentlichen Verwaltung wie z. B. die Industrie und Handelskammer oder Handwerkskammer.",
                    },
                    "12000": {
                        "name": "Schule",
                        "description": "Schulische Einrichtung. Darunter fallen u. a. Allgemeinbildende Schule, Oberstufenzentrum, Sonderschule, Fachschule, Volkshochschule,\r\nKonservatorium.",
                    },
                    "12001": {
                        "name": "Hochschule",
                        "description": "Hochschule, Fachhochschule, Berufsakademie, o. Ä.",
                    },
                    "12002": {
                        "name": "BerufsbildendeSchule",
                        "description": "Berufsbildende Schule",
                    },
                    "12003": {
                        "name": "Forschungseinrichtung",
                        "description": "Forschungseinrichtung, Forschungsinstitut.",
                    },
                    "12004": {
                        "name": "SonstigesBildungForschung",
                        "description": "Sonstige Anlage oder Einrichtung aus Bildung und Forschung.",
                    },
                    "14000": {
                        "name": "Sakralgebaeude",
                        "description": "Religiösen Zwecken dienendes Gebäude wie z. B. Kirche, \r\n Kapelle, Moschee, Synagoge, Gebetssaal.",
                    },
                    "14001": {
                        "name": "KirchlicheVerwaltung",
                        "description": "Kirchliches Verwaltungsgebäude, z. B. Pfarramt, Bischöfliches Ordinariat, Konsistorium.",
                    },
                    "14002": {
                        "name": "Kirchengemeinde",
                        "description": "Religiöse Gemeinde- oder Versammlungseinrichtung, z. B. Gemeindehaus, Gemeindezentrum.",
                    },
                    "14003": {
                        "name": "SonstigesKirche",
                        "description": "Sonstige religiösen Zwecken dienende Anlage oder Einrichtung.",
                    },
                    "16000": {
                        "name": "EinrichtungKinder",
                        "description": "Soziale Einrichtung für Kinder, wie z. B. Kinderheim, Kindertagesstätte, Kindergarten.",
                    },
                    "16001": {
                        "name": "EinrichtungJugendliche",
                        "description": "Soziale Einrichtung für Jugendliche, wie z. B. Jugendfreizeitheim/-stätte, Jugendgästehaus, Jugendherberge, Jugendheim.",
                    },
                    "16002": {
                        "name": "EinrichtungFamilienErwachsene",
                        "description": "Soziale Einrichtung für Familien und Erwachsene, wie z. B. Bildungszentrum, Volkshochschule, Kleinkinderfürsorgestelle, Säuglingsfürsorgestelle, Nachbarschaftsheim.",
                    },
                    "16003": {
                        "name": "EinrichtungSenioren",
                        "description": "Soziale Einrichtung für Senioren, wie z. B. Alten-/Seniorentagesstätte, Alten-/Seniorenheim, Alten-/Seniorenwohnheim, Altersheim.",
                    },
                    "16004": {
                        "name": "SonstigeSozialeEinrichtung",
                        "description": "Sonstige soziale Einrichtung, z. B. Pflegeheim, Schwesternwohnheim, Studentendorf, Studentenwohnheim. Tierheim, Übergangsheim.",
                    },
                    "18000": {
                        "name": "Krankenhaus",
                        "description": "Krankenhaus oder vergleichbare Einrichtung (z. B. Klinik, Hospital, Krankenheim, Heil- und Pflegeanstalt),",
                    },
                    "18001": {
                        "name": "SonstigesGesundheit",
                        "description": "Sonstige Gesundheits-Einrichtung, z. B. Sanatorium, Kurklinik, Desinfektionsanstalt.",
                    },
                    "20000": {
                        "name": "MusikTheater",
                        "description": "Kulturelle Einrichtung aus dem Bereich Musik oder Theater (z. B. Theater, Konzerthaus, Musikhalle, Oper).",
                    },
                    "20001": {
                        "name": "Bildung",
                        "description": "Kulturelle Einrichtung mit Bildungsfunktion ( z. B. Museum, Bibliothek, Bücherei, Stadtbücherei, Volksbücherei).",
                    },
                    "20002": {
                        "name": "SonstigeKultur",
                        "description": "Sonstige kulturelle Einrichtung, wie z. B. Archiv, Landesbildstelle, Rundfunk und Fernsehen, Kongress- und Veranstaltungshalle, Mehrzweckhalle..",
                    },
                    "22000": {
                        "name": "Bad",
                        "description": "Schwimmbad, Freibad, Hallenbad, Schwimmhalle o. Ä..",
                    },
                    "22001": {
                        "name": "SportplatzSporthalle",
                        "description": "Sportplatz, Sporthalle, Tennishalle o. Ä.",
                    },
                    "22002": {
                        "name": "SonstigerSport",
                        "description": "Sonstige Sporteinrichtung.",
                    },
                    "24000": {
                        "name": "Feuerwehr",
                        "description": "Einrichtung oder Anlage der Feuerwehr.",
                    },
                    "24001": {"name": "Schutzbauwerk", "description": "Schutzbauwerk"},
                    "24002": {
                        "name": "Justiz",
                        "description": "Einrichtung der Justiz, wie z. B. Justizvollzug, Gericht, Haftanstalt.",
                    },
                    "24003": {
                        "name": "SonstigeSicherheitOrdnung",
                        "description": "Sonstige Anlage oder Einrichtung für Sicherheit und Ordnung, z. B. Polizei, Zoll, Feuerwehr, Zivilschutz, Bundeswehr, Landesverteidigung.",
                    },
                    "26000": {"name": "Post", "description": "Einrichtung der Post."},
                    "26001": {
                        "name": "SonstigeInfrastruktur",
                        "description": "Sonstige Anlage oder Einrichtung der Infrastruktur.",
                    },
                },
            },
        ),
    ] = None
    weitereBesondZweckbestimmung1: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "12000",
            "12001",
            "12002",
            "12003",
            "12004",
            "14000",
            "14001",
            "14002",
            "14003",
            "16000",
            "16001",
            "16002",
            "16003",
            "16004",
            "18000",
            "18001",
            "20000",
            "20001",
            "20002",
            "22000",
            "22001",
            "22002",
            "24000",
            "24001",
            "24002",
            "24003",
            "26000",
            "26001",
        ]
        | None,
        Field(
            description='Weitere besondere Zweckbestimmung der festgesetzten Fläche, die die zugehörige allgemeine Zweckbestimmung detailliert oder ersetzt.. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {
                        "name": "KommunaleEinrichtung",
                        "description": "Kommunale Einrichtung wie z. B. Rathaus, Gesundheitsamt, Gesundheitsfürsorgestelle, Gartenbauamt, Gartenarbeitsstützpunkt, Fuhrpark.",
                    },
                    "10001": {
                        "name": "BetriebOeffentlZweckbestimmung",
                        "description": "Betrieb mit öffentlicher Zweckbestimmung wie z.B. ein Stadtreinigungsbetrieb, Autobusbetriebshof, Omnibusbahnhof.",
                    },
                    "10002": {
                        "name": "AnlageBundLand",
                        "description": "Eine Anlage des Bundes oder eines Bundeslandes wie z. B.  Arbeitsamt, Autobahnmeisterei, Brückenmeisterei, Patentamt, Wasserbauhof, Finanzamt.",
                    },
                    "10003": {
                        "name": "SonstigeOeffentlicheVerwaltung",
                        "description": "Sonstige Einrichtung oder Anlage der öffentlichen Verwaltung wie z. B. die Industrie und Handelskammer oder Handwerkskammer.",
                    },
                    "12000": {
                        "name": "Schule",
                        "description": "Schulische Einrichtung. Darunter fallen u. a. Allgemeinbildende Schule, Oberstufenzentrum, Sonderschule, Fachschule, Volkshochschule,\r\nKonservatorium.",
                    },
                    "12001": {
                        "name": "Hochschule",
                        "description": "Hochschule, Fachhochschule, Berufsakademie, o. Ä.",
                    },
                    "12002": {
                        "name": "BerufsbildendeSchule",
                        "description": "Berufsbildende Schule",
                    },
                    "12003": {
                        "name": "Forschungseinrichtung",
                        "description": "Forschungseinrichtung, Forschungsinstitut.",
                    },
                    "12004": {
                        "name": "SonstigesBildungForschung",
                        "description": "Sonstige Anlage oder Einrichtung aus Bildung und Forschung.",
                    },
                    "14000": {
                        "name": "Sakralgebaeude",
                        "description": "Religiösen Zwecken dienendes Gebäude wie z. B. Kirche, \r\n Kapelle, Moschee, Synagoge, Gebetssaal.",
                    },
                    "14001": {
                        "name": "KirchlicheVerwaltung",
                        "description": "Kirchliches Verwaltungsgebäude, z. B. Pfarramt, Bischöfliches Ordinariat, Konsistorium.",
                    },
                    "14002": {
                        "name": "Kirchengemeinde",
                        "description": "Religiöse Gemeinde- oder Versammlungseinrichtung, z. B. Gemeindehaus, Gemeindezentrum.",
                    },
                    "14003": {
                        "name": "SonstigesKirche",
                        "description": "Sonstige religiösen Zwecken dienende Anlage oder Einrichtung.",
                    },
                    "16000": {
                        "name": "EinrichtungKinder",
                        "description": "Soziale Einrichtung für Kinder, wie z. B. Kinderheim, Kindertagesstätte, Kindergarten.",
                    },
                    "16001": {
                        "name": "EinrichtungJugendliche",
                        "description": "Soziale Einrichtung für Jugendliche, wie z. B. Jugendfreizeitheim/-stätte, Jugendgästehaus, Jugendherberge, Jugendheim.",
                    },
                    "16002": {
                        "name": "EinrichtungFamilienErwachsene",
                        "description": "Soziale Einrichtung für Familien und Erwachsene, wie z. B. Bildungszentrum, Volkshochschule, Kleinkinderfürsorgestelle, Säuglingsfürsorgestelle, Nachbarschaftsheim.",
                    },
                    "16003": {
                        "name": "EinrichtungSenioren",
                        "description": "Soziale Einrichtung für Senioren, wie z. B. Alten-/Seniorentagesstätte, Alten-/Seniorenheim, Alten-/Seniorenwohnheim, Altersheim.",
                    },
                    "16004": {
                        "name": "SonstigeSozialeEinrichtung",
                        "description": "Sonstige soziale Einrichtung, z. B. Pflegeheim, Schwesternwohnheim, Studentendorf, Studentenwohnheim. Tierheim, Übergangsheim.",
                    },
                    "18000": {
                        "name": "Krankenhaus",
                        "description": "Krankenhaus oder vergleichbare Einrichtung (z. B. Klinik, Hospital, Krankenheim, Heil- und Pflegeanstalt),",
                    },
                    "18001": {
                        "name": "SonstigesGesundheit",
                        "description": "Sonstige Gesundheits-Einrichtung, z. B. Sanatorium, Kurklinik, Desinfektionsanstalt.",
                    },
                    "20000": {
                        "name": "MusikTheater",
                        "description": "Kulturelle Einrichtung aus dem Bereich Musik oder Theater (z. B. Theater, Konzerthaus, Musikhalle, Oper).",
                    },
                    "20001": {
                        "name": "Bildung",
                        "description": "Kulturelle Einrichtung mit Bildungsfunktion ( z. B. Museum, Bibliothek, Bücherei, Stadtbücherei, Volksbücherei).",
                    },
                    "20002": {
                        "name": "SonstigeKultur",
                        "description": "Sonstige kulturelle Einrichtung, wie z. B. Archiv, Landesbildstelle, Rundfunk und Fernsehen, Kongress- und Veranstaltungshalle, Mehrzweckhalle..",
                    },
                    "22000": {
                        "name": "Bad",
                        "description": "Schwimmbad, Freibad, Hallenbad, Schwimmhalle o. Ä..",
                    },
                    "22001": {
                        "name": "SportplatzSporthalle",
                        "description": "Sportplatz, Sporthalle, Tennishalle o. Ä.",
                    },
                    "22002": {
                        "name": "SonstigerSport",
                        "description": "Sonstige Sporteinrichtung.",
                    },
                    "24000": {
                        "name": "Feuerwehr",
                        "description": "Einrichtung oder Anlage der Feuerwehr.",
                    },
                    "24001": {"name": "Schutzbauwerk", "description": "Schutzbauwerk"},
                    "24002": {
                        "name": "Justiz",
                        "description": "Einrichtung der Justiz, wie z. B. Justizvollzug, Gericht, Haftanstalt.",
                    },
                    "24003": {
                        "name": "SonstigeSicherheitOrdnung",
                        "description": "Sonstige Anlage oder Einrichtung für Sicherheit und Ordnung, z. B. Polizei, Zoll, Feuerwehr, Zivilschutz, Bundeswehr, Landesverteidigung.",
                    },
                    "26000": {"name": "Post", "description": "Einrichtung der Post."},
                    "26001": {
                        "name": "SonstigeInfrastruktur",
                        "description": "Sonstige Anlage oder Einrichtung der Infrastruktur.",
                    },
                },
                "typename": "XP_BesondereZweckbestGemeinbedarf",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereBesondZweckbestimmung2: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "12000",
            "12001",
            "12002",
            "12003",
            "12004",
            "14000",
            "14001",
            "14002",
            "14003",
            "16000",
            "16001",
            "16002",
            "16003",
            "16004",
            "18000",
            "18001",
            "20000",
            "20001",
            "20002",
            "22000",
            "22001",
            "22002",
            "24000",
            "24001",
            "24002",
            "24003",
            "26000",
            "26001",
        ]
        | None,
        Field(
            description='Weitere besondere Zweckbestimmung der festgesetzten Fläche, die die zugehörige allgemeine Zweckbestimmung detailliert oder ersetzt. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {
                        "name": "KommunaleEinrichtung",
                        "description": "Kommunale Einrichtung wie z. B. Rathaus, Gesundheitsamt, Gesundheitsfürsorgestelle, Gartenbauamt, Gartenarbeitsstützpunkt, Fuhrpark.",
                    },
                    "10001": {
                        "name": "BetriebOeffentlZweckbestimmung",
                        "description": "Betrieb mit öffentlicher Zweckbestimmung wie z.B. ein Stadtreinigungsbetrieb, Autobusbetriebshof, Omnibusbahnhof.",
                    },
                    "10002": {
                        "name": "AnlageBundLand",
                        "description": "Eine Anlage des Bundes oder eines Bundeslandes wie z. B.  Arbeitsamt, Autobahnmeisterei, Brückenmeisterei, Patentamt, Wasserbauhof, Finanzamt.",
                    },
                    "10003": {
                        "name": "SonstigeOeffentlicheVerwaltung",
                        "description": "Sonstige Einrichtung oder Anlage der öffentlichen Verwaltung wie z. B. die Industrie und Handelskammer oder Handwerkskammer.",
                    },
                    "12000": {
                        "name": "Schule",
                        "description": "Schulische Einrichtung. Darunter fallen u. a. Allgemeinbildende Schule, Oberstufenzentrum, Sonderschule, Fachschule, Volkshochschule,\r\nKonservatorium.",
                    },
                    "12001": {
                        "name": "Hochschule",
                        "description": "Hochschule, Fachhochschule, Berufsakademie, o. Ä.",
                    },
                    "12002": {
                        "name": "BerufsbildendeSchule",
                        "description": "Berufsbildende Schule",
                    },
                    "12003": {
                        "name": "Forschungseinrichtung",
                        "description": "Forschungseinrichtung, Forschungsinstitut.",
                    },
                    "12004": {
                        "name": "SonstigesBildungForschung",
                        "description": "Sonstige Anlage oder Einrichtung aus Bildung und Forschung.",
                    },
                    "14000": {
                        "name": "Sakralgebaeude",
                        "description": "Religiösen Zwecken dienendes Gebäude wie z. B. Kirche, \r\n Kapelle, Moschee, Synagoge, Gebetssaal.",
                    },
                    "14001": {
                        "name": "KirchlicheVerwaltung",
                        "description": "Kirchliches Verwaltungsgebäude, z. B. Pfarramt, Bischöfliches Ordinariat, Konsistorium.",
                    },
                    "14002": {
                        "name": "Kirchengemeinde",
                        "description": "Religiöse Gemeinde- oder Versammlungseinrichtung, z. B. Gemeindehaus, Gemeindezentrum.",
                    },
                    "14003": {
                        "name": "SonstigesKirche",
                        "description": "Sonstige religiösen Zwecken dienende Anlage oder Einrichtung.",
                    },
                    "16000": {
                        "name": "EinrichtungKinder",
                        "description": "Soziale Einrichtung für Kinder, wie z. B. Kinderheim, Kindertagesstätte, Kindergarten.",
                    },
                    "16001": {
                        "name": "EinrichtungJugendliche",
                        "description": "Soziale Einrichtung für Jugendliche, wie z. B. Jugendfreizeitheim/-stätte, Jugendgästehaus, Jugendherberge, Jugendheim.",
                    },
                    "16002": {
                        "name": "EinrichtungFamilienErwachsene",
                        "description": "Soziale Einrichtung für Familien und Erwachsene, wie z. B. Bildungszentrum, Volkshochschule, Kleinkinderfürsorgestelle, Säuglingsfürsorgestelle, Nachbarschaftsheim.",
                    },
                    "16003": {
                        "name": "EinrichtungSenioren",
                        "description": "Soziale Einrichtung für Senioren, wie z. B. Alten-/Seniorentagesstätte, Alten-/Seniorenheim, Alten-/Seniorenwohnheim, Altersheim.",
                    },
                    "16004": {
                        "name": "SonstigeSozialeEinrichtung",
                        "description": "Sonstige soziale Einrichtung, z. B. Pflegeheim, Schwesternwohnheim, Studentendorf, Studentenwohnheim. Tierheim, Übergangsheim.",
                    },
                    "18000": {
                        "name": "Krankenhaus",
                        "description": "Krankenhaus oder vergleichbare Einrichtung (z. B. Klinik, Hospital, Krankenheim, Heil- und Pflegeanstalt),",
                    },
                    "18001": {
                        "name": "SonstigesGesundheit",
                        "description": "Sonstige Gesundheits-Einrichtung, z. B. Sanatorium, Kurklinik, Desinfektionsanstalt.",
                    },
                    "20000": {
                        "name": "MusikTheater",
                        "description": "Kulturelle Einrichtung aus dem Bereich Musik oder Theater (z. B. Theater, Konzerthaus, Musikhalle, Oper).",
                    },
                    "20001": {
                        "name": "Bildung",
                        "description": "Kulturelle Einrichtung mit Bildungsfunktion ( z. B. Museum, Bibliothek, Bücherei, Stadtbücherei, Volksbücherei).",
                    },
                    "20002": {
                        "name": "SonstigeKultur",
                        "description": "Sonstige kulturelle Einrichtung, wie z. B. Archiv, Landesbildstelle, Rundfunk und Fernsehen, Kongress- und Veranstaltungshalle, Mehrzweckhalle..",
                    },
                    "22000": {
                        "name": "Bad",
                        "description": "Schwimmbad, Freibad, Hallenbad, Schwimmhalle o. Ä..",
                    },
                    "22001": {
                        "name": "SportplatzSporthalle",
                        "description": "Sportplatz, Sporthalle, Tennishalle o. Ä.",
                    },
                    "22002": {
                        "name": "SonstigerSport",
                        "description": "Sonstige Sporteinrichtung.",
                    },
                    "24000": {
                        "name": "Feuerwehr",
                        "description": "Einrichtung oder Anlage der Feuerwehr.",
                    },
                    "24001": {"name": "Schutzbauwerk", "description": "Schutzbauwerk"},
                    "24002": {
                        "name": "Justiz",
                        "description": "Einrichtung der Justiz, wie z. B. Justizvollzug, Gericht, Haftanstalt.",
                    },
                    "24003": {
                        "name": "SonstigeSicherheitOrdnung",
                        "description": "Sonstige Anlage oder Einrichtung für Sicherheit und Ordnung, z. B. Polizei, Zoll, Feuerwehr, Zivilschutz, Bundeswehr, Landesverteidigung.",
                    },
                    "26000": {"name": "Post", "description": "Einrichtung der Post."},
                    "26001": {
                        "name": "SonstigeInfrastruktur",
                        "description": "Sonstige Anlage oder Einrichtung der Infrastruktur.",
                    },
                },
                "typename": "XP_BesondereZweckbestGemeinbedarf",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereBesondZweckbestimmung3: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "12000",
            "12001",
            "12002",
            "12003",
            "12004",
            "14000",
            "14001",
            "14002",
            "14003",
            "16000",
            "16001",
            "16002",
            "16003",
            "16004",
            "18000",
            "18001",
            "20000",
            "20001",
            "20002",
            "22000",
            "22001",
            "22002",
            "24000",
            "24001",
            "24002",
            "24003",
            "26000",
            "26001",
        ]
        | None,
        Field(
            description='Weitere besondere Zweckbestimmung der festgesetzten Fläche, die die zugehörige allgemeine Zweckbestimmung detailliert oder ersetzt. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {
                        "name": "KommunaleEinrichtung",
                        "description": "Kommunale Einrichtung wie z. B. Rathaus, Gesundheitsamt, Gesundheitsfürsorgestelle, Gartenbauamt, Gartenarbeitsstützpunkt, Fuhrpark.",
                    },
                    "10001": {
                        "name": "BetriebOeffentlZweckbestimmung",
                        "description": "Betrieb mit öffentlicher Zweckbestimmung wie z.B. ein Stadtreinigungsbetrieb, Autobusbetriebshof, Omnibusbahnhof.",
                    },
                    "10002": {
                        "name": "AnlageBundLand",
                        "description": "Eine Anlage des Bundes oder eines Bundeslandes wie z. B.  Arbeitsamt, Autobahnmeisterei, Brückenmeisterei, Patentamt, Wasserbauhof, Finanzamt.",
                    },
                    "10003": {
                        "name": "SonstigeOeffentlicheVerwaltung",
                        "description": "Sonstige Einrichtung oder Anlage der öffentlichen Verwaltung wie z. B. die Industrie und Handelskammer oder Handwerkskammer.",
                    },
                    "12000": {
                        "name": "Schule",
                        "description": "Schulische Einrichtung. Darunter fallen u. a. Allgemeinbildende Schule, Oberstufenzentrum, Sonderschule, Fachschule, Volkshochschule,\r\nKonservatorium.",
                    },
                    "12001": {
                        "name": "Hochschule",
                        "description": "Hochschule, Fachhochschule, Berufsakademie, o. Ä.",
                    },
                    "12002": {
                        "name": "BerufsbildendeSchule",
                        "description": "Berufsbildende Schule",
                    },
                    "12003": {
                        "name": "Forschungseinrichtung",
                        "description": "Forschungseinrichtung, Forschungsinstitut.",
                    },
                    "12004": {
                        "name": "SonstigesBildungForschung",
                        "description": "Sonstige Anlage oder Einrichtung aus Bildung und Forschung.",
                    },
                    "14000": {
                        "name": "Sakralgebaeude",
                        "description": "Religiösen Zwecken dienendes Gebäude wie z. B. Kirche, \r\n Kapelle, Moschee, Synagoge, Gebetssaal.",
                    },
                    "14001": {
                        "name": "KirchlicheVerwaltung",
                        "description": "Kirchliches Verwaltungsgebäude, z. B. Pfarramt, Bischöfliches Ordinariat, Konsistorium.",
                    },
                    "14002": {
                        "name": "Kirchengemeinde",
                        "description": "Religiöse Gemeinde- oder Versammlungseinrichtung, z. B. Gemeindehaus, Gemeindezentrum.",
                    },
                    "14003": {
                        "name": "SonstigesKirche",
                        "description": "Sonstige religiösen Zwecken dienende Anlage oder Einrichtung.",
                    },
                    "16000": {
                        "name": "EinrichtungKinder",
                        "description": "Soziale Einrichtung für Kinder, wie z. B. Kinderheim, Kindertagesstätte, Kindergarten.",
                    },
                    "16001": {
                        "name": "EinrichtungJugendliche",
                        "description": "Soziale Einrichtung für Jugendliche, wie z. B. Jugendfreizeitheim/-stätte, Jugendgästehaus, Jugendherberge, Jugendheim.",
                    },
                    "16002": {
                        "name": "EinrichtungFamilienErwachsene",
                        "description": "Soziale Einrichtung für Familien und Erwachsene, wie z. B. Bildungszentrum, Volkshochschule, Kleinkinderfürsorgestelle, Säuglingsfürsorgestelle, Nachbarschaftsheim.",
                    },
                    "16003": {
                        "name": "EinrichtungSenioren",
                        "description": "Soziale Einrichtung für Senioren, wie z. B. Alten-/Seniorentagesstätte, Alten-/Seniorenheim, Alten-/Seniorenwohnheim, Altersheim.",
                    },
                    "16004": {
                        "name": "SonstigeSozialeEinrichtung",
                        "description": "Sonstige soziale Einrichtung, z. B. Pflegeheim, Schwesternwohnheim, Studentendorf, Studentenwohnheim. Tierheim, Übergangsheim.",
                    },
                    "18000": {
                        "name": "Krankenhaus",
                        "description": "Krankenhaus oder vergleichbare Einrichtung (z. B. Klinik, Hospital, Krankenheim, Heil- und Pflegeanstalt),",
                    },
                    "18001": {
                        "name": "SonstigesGesundheit",
                        "description": "Sonstige Gesundheits-Einrichtung, z. B. Sanatorium, Kurklinik, Desinfektionsanstalt.",
                    },
                    "20000": {
                        "name": "MusikTheater",
                        "description": "Kulturelle Einrichtung aus dem Bereich Musik oder Theater (z. B. Theater, Konzerthaus, Musikhalle, Oper).",
                    },
                    "20001": {
                        "name": "Bildung",
                        "description": "Kulturelle Einrichtung mit Bildungsfunktion ( z. B. Museum, Bibliothek, Bücherei, Stadtbücherei, Volksbücherei).",
                    },
                    "20002": {
                        "name": "SonstigeKultur",
                        "description": "Sonstige kulturelle Einrichtung, wie z. B. Archiv, Landesbildstelle, Rundfunk und Fernsehen, Kongress- und Veranstaltungshalle, Mehrzweckhalle..",
                    },
                    "22000": {
                        "name": "Bad",
                        "description": "Schwimmbad, Freibad, Hallenbad, Schwimmhalle o. Ä..",
                    },
                    "22001": {
                        "name": "SportplatzSporthalle",
                        "description": "Sportplatz, Sporthalle, Tennishalle o. Ä.",
                    },
                    "22002": {
                        "name": "SonstigerSport",
                        "description": "Sonstige Sporteinrichtung.",
                    },
                    "24000": {
                        "name": "Feuerwehr",
                        "description": "Einrichtung oder Anlage der Feuerwehr.",
                    },
                    "24001": {"name": "Schutzbauwerk", "description": "Schutzbauwerk"},
                    "24002": {
                        "name": "Justiz",
                        "description": "Einrichtung der Justiz, wie z. B. Justizvollzug, Gericht, Haftanstalt.",
                    },
                    "24003": {
                        "name": "SonstigeSicherheitOrdnung",
                        "description": "Sonstige Anlage oder Einrichtung für Sicherheit und Ordnung, z. B. Polizei, Zoll, Feuerwehr, Zivilschutz, Bundeswehr, Landesverteidigung.",
                    },
                    "26000": {"name": "Post", "description": "Einrichtung der Post."},
                    "26001": {
                        "name": "SonstigeInfrastruktur",
                        "description": "Sonstige Anlage oder Einrichtung der Infrastruktur.",
                    },
                },
                "typename": "XP_BesondereZweckbestGemeinbedarf",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereBesondZweckbestimmung4: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "12000",
            "12001",
            "12002",
            "12003",
            "12004",
            "14000",
            "14001",
            "14002",
            "14003",
            "16000",
            "16001",
            "16002",
            "16003",
            "16004",
            "18000",
            "18001",
            "20000",
            "20001",
            "20002",
            "22000",
            "22001",
            "22002",
            "24000",
            "24001",
            "24002",
            "24003",
            "26000",
            "26001",
        ]
        | None,
        Field(
            description='Weitere besondere Zweckbestimmung der festgesetzten Fläche, die die zugehörige allgemeine Zweckbestimmung detailliert oder ersetzt. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {
                        "name": "KommunaleEinrichtung",
                        "description": "Kommunale Einrichtung wie z. B. Rathaus, Gesundheitsamt, Gesundheitsfürsorgestelle, Gartenbauamt, Gartenarbeitsstützpunkt, Fuhrpark.",
                    },
                    "10001": {
                        "name": "BetriebOeffentlZweckbestimmung",
                        "description": "Betrieb mit öffentlicher Zweckbestimmung wie z.B. ein Stadtreinigungsbetrieb, Autobusbetriebshof, Omnibusbahnhof.",
                    },
                    "10002": {
                        "name": "AnlageBundLand",
                        "description": "Eine Anlage des Bundes oder eines Bundeslandes wie z. B.  Arbeitsamt, Autobahnmeisterei, Brückenmeisterei, Patentamt, Wasserbauhof, Finanzamt.",
                    },
                    "10003": {
                        "name": "SonstigeOeffentlicheVerwaltung",
                        "description": "Sonstige Einrichtung oder Anlage der öffentlichen Verwaltung wie z. B. die Industrie und Handelskammer oder Handwerkskammer.",
                    },
                    "12000": {
                        "name": "Schule",
                        "description": "Schulische Einrichtung. Darunter fallen u. a. Allgemeinbildende Schule, Oberstufenzentrum, Sonderschule, Fachschule, Volkshochschule,\r\nKonservatorium.",
                    },
                    "12001": {
                        "name": "Hochschule",
                        "description": "Hochschule, Fachhochschule, Berufsakademie, o. Ä.",
                    },
                    "12002": {
                        "name": "BerufsbildendeSchule",
                        "description": "Berufsbildende Schule",
                    },
                    "12003": {
                        "name": "Forschungseinrichtung",
                        "description": "Forschungseinrichtung, Forschungsinstitut.",
                    },
                    "12004": {
                        "name": "SonstigesBildungForschung",
                        "description": "Sonstige Anlage oder Einrichtung aus Bildung und Forschung.",
                    },
                    "14000": {
                        "name": "Sakralgebaeude",
                        "description": "Religiösen Zwecken dienendes Gebäude wie z. B. Kirche, \r\n Kapelle, Moschee, Synagoge, Gebetssaal.",
                    },
                    "14001": {
                        "name": "KirchlicheVerwaltung",
                        "description": "Kirchliches Verwaltungsgebäude, z. B. Pfarramt, Bischöfliches Ordinariat, Konsistorium.",
                    },
                    "14002": {
                        "name": "Kirchengemeinde",
                        "description": "Religiöse Gemeinde- oder Versammlungseinrichtung, z. B. Gemeindehaus, Gemeindezentrum.",
                    },
                    "14003": {
                        "name": "SonstigesKirche",
                        "description": "Sonstige religiösen Zwecken dienende Anlage oder Einrichtung.",
                    },
                    "16000": {
                        "name": "EinrichtungKinder",
                        "description": "Soziale Einrichtung für Kinder, wie z. B. Kinderheim, Kindertagesstätte, Kindergarten.",
                    },
                    "16001": {
                        "name": "EinrichtungJugendliche",
                        "description": "Soziale Einrichtung für Jugendliche, wie z. B. Jugendfreizeitheim/-stätte, Jugendgästehaus, Jugendherberge, Jugendheim.",
                    },
                    "16002": {
                        "name": "EinrichtungFamilienErwachsene",
                        "description": "Soziale Einrichtung für Familien und Erwachsene, wie z. B. Bildungszentrum, Volkshochschule, Kleinkinderfürsorgestelle, Säuglingsfürsorgestelle, Nachbarschaftsheim.",
                    },
                    "16003": {
                        "name": "EinrichtungSenioren",
                        "description": "Soziale Einrichtung für Senioren, wie z. B. Alten-/Seniorentagesstätte, Alten-/Seniorenheim, Alten-/Seniorenwohnheim, Altersheim.",
                    },
                    "16004": {
                        "name": "SonstigeSozialeEinrichtung",
                        "description": "Sonstige soziale Einrichtung, z. B. Pflegeheim, Schwesternwohnheim, Studentendorf, Studentenwohnheim. Tierheim, Übergangsheim.",
                    },
                    "18000": {
                        "name": "Krankenhaus",
                        "description": "Krankenhaus oder vergleichbare Einrichtung (z. B. Klinik, Hospital, Krankenheim, Heil- und Pflegeanstalt),",
                    },
                    "18001": {
                        "name": "SonstigesGesundheit",
                        "description": "Sonstige Gesundheits-Einrichtung, z. B. Sanatorium, Kurklinik, Desinfektionsanstalt.",
                    },
                    "20000": {
                        "name": "MusikTheater",
                        "description": "Kulturelle Einrichtung aus dem Bereich Musik oder Theater (z. B. Theater, Konzerthaus, Musikhalle, Oper).",
                    },
                    "20001": {
                        "name": "Bildung",
                        "description": "Kulturelle Einrichtung mit Bildungsfunktion ( z. B. Museum, Bibliothek, Bücherei, Stadtbücherei, Volksbücherei).",
                    },
                    "20002": {
                        "name": "SonstigeKultur",
                        "description": "Sonstige kulturelle Einrichtung, wie z. B. Archiv, Landesbildstelle, Rundfunk und Fernsehen, Kongress- und Veranstaltungshalle, Mehrzweckhalle..",
                    },
                    "22000": {
                        "name": "Bad",
                        "description": "Schwimmbad, Freibad, Hallenbad, Schwimmhalle o. Ä..",
                    },
                    "22001": {
                        "name": "SportplatzSporthalle",
                        "description": "Sportplatz, Sporthalle, Tennishalle o. Ä.",
                    },
                    "22002": {
                        "name": "SonstigerSport",
                        "description": "Sonstige Sporteinrichtung.",
                    },
                    "24000": {
                        "name": "Feuerwehr",
                        "description": "Einrichtung oder Anlage der Feuerwehr.",
                    },
                    "24001": {"name": "Schutzbauwerk", "description": "Schutzbauwerk"},
                    "24002": {
                        "name": "Justiz",
                        "description": "Einrichtung der Justiz, wie z. B. Justizvollzug, Gericht, Haftanstalt.",
                    },
                    "24003": {
                        "name": "SonstigeSicherheitOrdnung",
                        "description": "Sonstige Anlage oder Einrichtung für Sicherheit und Ordnung, z. B. Polizei, Zoll, Feuerwehr, Zivilschutz, Bundeswehr, Landesverteidigung.",
                    },
                    "26000": {"name": "Post", "description": "Einrichtung der Post."},
                    "26001": {
                        "name": "SonstigeInfrastruktur",
                        "description": "Sonstige Anlage oder Einrichtung der Infrastruktur.",
                    },
                },
                "typename": "XP_BesondereZweckbestGemeinbedarf",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteZweckbestimmung: Annotated[
        list[AnyUrl] | None,
        Field(
            description="Über eine CodeList definierte zusätzliche Zweckbestimmungen.",
            json_schema_extra={
                "typename": "BP_DetailZweckbestGemeinbedarf",
                "stereotype": "Codelist",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung1: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestGemeinbedarf",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung2: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestGemeinbedarf",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung3: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestGemeinbedarf",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung4: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestGemeinbedarf",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    zugunstenVon: Annotated[
        str | None,
        Field(
            description="Angabe des Begünstigten einer Ausweisung.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPGeometrieobjekt(BPObjekt):
    """Basisklasse für alle Objekte eines Bebauungsplans mit variablem Raumbezug."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Point
        | definitions.MultiPoint
        | definitions.Line
        | definitions.MultiLine
        | definitions.Polygon
        | definitions.MultiPolygon,
        Field(
            description="Raumbezug - Entweder punktförmig, linienförmig oder flächenhaft, gemischte Geometrie ist nicht zugelassen.",
            json_schema_extra={
                "typename": "XP_VariableGeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]
    flaechenschluss: Annotated[
        bool | None,
        Field(
            description="Zeigt bei flächenhaftem Raumbezug an, ob das Objekt als Flächenschlussobjekt oder Überlagerungsobjekt gebildet werden soll.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False


class BPGewaesserFlaeche(BPFlaechenschlussobjekt):
    """Wasserfläche (§9 Abs. 1 Nr. 16 und Abs. 6 BauGB)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    zweckbestimmung: Annotated[
        Literal["1000", "1100", "1200", "9999"] | None,
        Field(
            description="Zweckbestimmung der Wasserfläche.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Hafen"},
                    "1100": {"name": "Wasserflaeche"},
                    "1200": {"name": "Fliessgewaesser"},
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungGewaesser",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteZweckbestimmung: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definierte  Zweckbestimmung der Fläche.",
            json_schema_extra={
                "typename": "BP_DetailZweckbestGewaesser",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPGruenFlaeche(BPFlaechenschlussobjekt):
    """Festsetzungen von öffentlichen und privaten Grünflächen(§9, Abs. 1, Nr. 15 BauGB)  und von Flächen für die Kleintierhaltung (§9, Abs. 1, Nr. 19 BauGB)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    MaxZahlWohnungen: Annotated[
        int | None,
        Field(
            description="Höchstzulässige Zahl der Wohnungen in Wohngebäuden",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Fmin: Annotated[
        definitions.Area | None,
        Field(
            description="Mindestmaß für die Größe (Fläche) eines Baugrundstücks.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Fmax: Annotated[
        definitions.Area | None,
        Field(
            description="Höchstmaß für die Größe (Fläche) eines Baugrundstücks.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Bmin: Annotated[
        definitions.Length | None,
        Field(
            description="Minimale Breite von Baugrundstücken",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Bmax: Annotated[
        definitions.Length | None,
        Field(
            description="Maximale Breite von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Tmin: Annotated[
        definitions.Length | None,
        Field(
            description="Minimale Tiefe von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Tmax: Annotated[
        definitions.Length | None,
        Field(
            description="Maximale Tiefe von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    GFZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Geschossflächenzahl .",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl bei einer Bereichsangabe. Das Attribut GFZmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZ_Ausn: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl als Ausnahme.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFmin: Annotated[
        definitions.Area | None,
        Field(
            description="Minimal zulässige Geschossfläche",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GFmax: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Geschossfläche bei einer Bereichsabgabe. Das Attribut GFmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GF: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Geschossfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GF_Ausn: Annotated[
        definitions.Area | None,
        Field(
            description="Ausnahmsweise maximal zulässige Geschossfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    BMZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Baumassenzahl",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Baumassenzahl bei einer Bereichsangabe. Das Attribut BMZmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Baumassenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZ_Ausn: Annotated[
        float | None,
        Field(
            description="Ausnahmsweise maximal zulässige Baumassenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMmin: Annotated[
        definitions.Volume | None,
        Field(
            description="Minimal zulässinge Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BMmax: Annotated[
        definitions.Volume | None,
        Field(
            description="Maximal zulässinge Baumasse bei einer Bereichsangabe. Das Attribut BMmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BM: Annotated[
        definitions.Volume | None,
        Field(
            description="Maximal zulässige Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BM_Ausn: Annotated[
        definitions.Volume | None,
        Field(
            description="Ausnahmsweise maximal zulässige Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    GRZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Grundflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Grundflächenzahl bei einer Bereichsangabe.  Das Attribut GRZmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Grundflächenzahl",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZ_Ausn: Annotated[
        float | None,
        Field(
            description="Ausnahmsweise maximal zulässige Grundflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRmin: Annotated[
        definitions.Area | None,
        Field(
            description="Minimal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GRmax: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Grundfläche bei einer Bereichsangabe. Das Attribut GRmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GR: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GR_Ausn: Annotated[
        definitions.Area | None,
        Field(
            description="Ausnahmsweise maximal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Zmin: Annotated[
        int | None,
        Field(
            description="Minimal zulässige Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Zmax: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der oberirdischen Vollgeschosse bei einer Bereichsangabe. Das Attribut Zmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Zzwingend: Annotated[
        int | None,
        Field(
            description="Zwingend vorgeschriebene Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z: Annotated[
        int | None,
        Field(
            description="Maximalzahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Ausn: Annotated[
        int | None,
        Field(
            description="Ausnahmsweise maximal zulässige Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Staffel: Annotated[
        int | None,
        Field(
            description="Maximalzahl von oberirdischen zurückgesetzten Vollgeschossen als Staffelgeschoss..",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Dach: Annotated[
        int | None,
        Field(
            description="Maximalzahl der zusätzlich erlaubten Dachgeschosse, die gleichzeitig Vollgeschosse sind.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUmin: Annotated[
        int | None,
        Field(
            description="Minimal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUmax: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der unterirdischen Geschosse bei einer Bereichsangabe. Das Attribut ZUmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUzwingend: Annotated[
        int | None,
        Field(
            description="Zwingend vorgeschriebene Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZU: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZU_Ausn: Annotated[
        int | None,
        Field(
            description="Ausnahmsweise maximal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    zweckbestimmung: Annotated[
        list[
            Literal[
                "1000",
                "1200",
                "1400",
                "1600",
                "1800",
                "2000",
                "2200",
                "2400",
                "2600",
                "9999",
            ]
        ]
        | None,
        Field(
            description="Allgemeine Zweckbestimmungen der Grünfläche",
            json_schema_extra={
                "typename": "XP_ZweckbestimmungGruen",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {
                        "name": "Parkanlage",
                        "description": "Parkanlage; auch: Erholungsgrün, Grünanlage, Naherholung.",
                    },
                    "1200": {
                        "name": "Dauerkleingaerten",
                        "description": "Dauerkleingarten; auch: Gartenfläche, Hofgärten, Gartenland",
                    },
                    "1400": {"name": "Sportplatz", "description": "Sportplatz"},
                    "1600": {"name": "Spielplatz", "description": "Spielplatz"},
                    "1800": {"name": "Zeltplatz", "description": "Zeltplatz"},
                    "2000": {
                        "name": "Badeplatz",
                        "description": "Badeplatz, auch Schwimmbad, Liegewiese",
                    },
                    "2200": {
                        "name": "FreizeitErholung",
                        "description": "Anlage für Freizeit und Erholung.",
                    },
                    "2400": {
                        "name": "SpezGruenflaeche",
                        "description": "Spezielle Grünfläche",
                    },
                    "2600": {"name": "Friedhof", "description": "Friedhof"},
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
            },
        ),
    ] = None
    weitereZweckbestimmung1: Annotated[
        Literal[
            "1000",
            "1200",
            "1400",
            "1600",
            "1800",
            "2000",
            "2200",
            "2400",
            "2600",
            "9999",
        ]
        | None,
        Field(
            description='Weitere allgemeine Zweckbestimmung der Grünfläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Parkanlage",
                        "description": "Parkanlage; auch: Erholungsgrün, Grünanlage, Naherholung.",
                    },
                    "1200": {
                        "name": "Dauerkleingaerten",
                        "description": "Dauerkleingarten; auch: Gartenfläche, Hofgärten, Gartenland",
                    },
                    "1400": {"name": "Sportplatz", "description": "Sportplatz"},
                    "1600": {"name": "Spielplatz", "description": "Spielplatz"},
                    "1800": {"name": "Zeltplatz", "description": "Zeltplatz"},
                    "2000": {
                        "name": "Badeplatz",
                        "description": "Badeplatz, auch Schwimmbad, Liegewiese",
                    },
                    "2200": {
                        "name": "FreizeitErholung",
                        "description": "Anlage für Freizeit und Erholung.",
                    },
                    "2400": {
                        "name": "SpezGruenflaeche",
                        "description": "Spezielle Grünfläche",
                    },
                    "2600": {"name": "Friedhof", "description": "Friedhof"},
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungGruen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung2: Annotated[
        Literal[
            "1000",
            "1200",
            "1400",
            "1600",
            "1800",
            "2000",
            "2200",
            "2400",
            "2600",
            "9999",
        ]
        | None,
        Field(
            description='Weitere allgemeine Zweckbestimmung der Grünfläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Parkanlage",
                        "description": "Parkanlage; auch: Erholungsgrün, Grünanlage, Naherholung.",
                    },
                    "1200": {
                        "name": "Dauerkleingaerten",
                        "description": "Dauerkleingarten; auch: Gartenfläche, Hofgärten, Gartenland",
                    },
                    "1400": {"name": "Sportplatz", "description": "Sportplatz"},
                    "1600": {"name": "Spielplatz", "description": "Spielplatz"},
                    "1800": {"name": "Zeltplatz", "description": "Zeltplatz"},
                    "2000": {
                        "name": "Badeplatz",
                        "description": "Badeplatz, auch Schwimmbad, Liegewiese",
                    },
                    "2200": {
                        "name": "FreizeitErholung",
                        "description": "Anlage für Freizeit und Erholung.",
                    },
                    "2400": {
                        "name": "SpezGruenflaeche",
                        "description": "Spezielle Grünfläche",
                    },
                    "2600": {"name": "Friedhof", "description": "Friedhof"},
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungGruen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung3: Annotated[
        Literal[
            "1000",
            "1200",
            "1400",
            "1600",
            "1800",
            "2000",
            "2200",
            "2400",
            "2600",
            "9999",
        ]
        | None,
        Field(
            description='Weitere allgemeine Zweckbestimmung der Grünfläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Parkanlage",
                        "description": "Parkanlage; auch: Erholungsgrün, Grünanlage, Naherholung.",
                    },
                    "1200": {
                        "name": "Dauerkleingaerten",
                        "description": "Dauerkleingarten; auch: Gartenfläche, Hofgärten, Gartenland",
                    },
                    "1400": {"name": "Sportplatz", "description": "Sportplatz"},
                    "1600": {"name": "Spielplatz", "description": "Spielplatz"},
                    "1800": {"name": "Zeltplatz", "description": "Zeltplatz"},
                    "2000": {
                        "name": "Badeplatz",
                        "description": "Badeplatz, auch Schwimmbad, Liegewiese",
                    },
                    "2200": {
                        "name": "FreizeitErholung",
                        "description": "Anlage für Freizeit und Erholung.",
                    },
                    "2400": {
                        "name": "SpezGruenflaeche",
                        "description": "Spezielle Grünfläche",
                    },
                    "2600": {"name": "Friedhof", "description": "Friedhof"},
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungGruen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung4: Annotated[
        Literal[
            "1000",
            "1200",
            "1400",
            "1600",
            "1800",
            "2000",
            "2200",
            "2400",
            "2600",
            "9999",
        ]
        | None,
        Field(
            description='Weitere allgemeine Zweckbestimmung der Grünfläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Parkanlage",
                        "description": "Parkanlage; auch: Erholungsgrün, Grünanlage, Naherholung.",
                    },
                    "1200": {
                        "name": "Dauerkleingaerten",
                        "description": "Dauerkleingarten; auch: Gartenfläche, Hofgärten, Gartenland",
                    },
                    "1400": {"name": "Sportplatz", "description": "Sportplatz"},
                    "1600": {"name": "Spielplatz", "description": "Spielplatz"},
                    "1800": {"name": "Zeltplatz", "description": "Zeltplatz"},
                    "2000": {
                        "name": "Badeplatz",
                        "description": "Badeplatz, auch Schwimmbad, Liegewiese",
                    },
                    "2200": {
                        "name": "FreizeitErholung",
                        "description": "Anlage für Freizeit und Erholung.",
                    },
                    "2400": {
                        "name": "SpezGruenflaeche",
                        "description": "Spezielle Grünfläche",
                    },
                    "2600": {"name": "Friedhof", "description": "Friedhof"},
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungGruen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    besondereZweckbestimmung: Annotated[
        list[
            Literal[
                "10000",
                "10001",
                "10002",
                "10003",
                "12000",
                "14000",
                "14001",
                "14002",
                "14003",
                "14004",
                "14005",
                "14006",
                "14007",
                "16000",
                "16001",
                "18000",
                "22000",
                "22001",
                "24000",
                "24001",
                "24002",
                "24003",
                "24004",
                "24005",
                "24006",
                "99990",
            ]
        ]
        | None,
        Field(
            description="Besondere Zweckbestimmungen der Grünfläche, die die zugehörige allgemeine Zweckbestimmungen detaillieren oder ersetzen.",
            json_schema_extra={
                "typename": "XP_BesondereZweckbestimmungGruen",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "10000": {"name": "ParkanlageHistorisch"},
                    "10001": {"name": "ParkanlageNaturnah"},
                    "10002": {"name": "ParkanlageWaldcharakter"},
                    "10003": {"name": "NaturnaheUferParkanlage"},
                    "12000": {"name": "ErholungsGaerten"},
                    "14000": {"name": "Reitsportanlage"},
                    "14001": {"name": "Hundesportanlage"},
                    "14002": {"name": "Wassersportanlage"},
                    "14003": {"name": "Schiessstand"},
                    "14004": {"name": "Golfplatz"},
                    "14005": {"name": "Skisport"},
                    "14006": {"name": "Tennisanlage"},
                    "14007": {"name": "SonstigerSportplatz"},
                    "16000": {"name": "Bolzplatz"},
                    "16001": {"name": "Abenteuerspielplatz"},
                    "18000": {"name": "Campingplatz"},
                    "22000": {"name": "Kleintierhaltung"},
                    "22001": {"name": "Festplatz"},
                    "24000": {"name": "StrassenbegleitGruen"},
                    "24001": {"name": "BoeschungsFlaeche"},
                    "24002": {"name": "FeldWaldWiese"},
                    "24003": {"name": "Uferschutzstreifen"},
                    "24004": {"name": "Abschirmgruen"},
                    "24005": {"name": "UmweltbildungsparkSchaugatter"},
                    "24006": {"name": "RuhenderVerkehr"},
                    "99990": {"name": "Gaertnerei"},
                },
            },
        ),
    ] = None
    weitereBesondZweckbestimmung1: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "12000",
            "14000",
            "14001",
            "14002",
            "14003",
            "14004",
            "14005",
            "14006",
            "14007",
            "16000",
            "16001",
            "18000",
            "22000",
            "22001",
            "24000",
            "24001",
            "24002",
            "24003",
            "24004",
            "24005",
            "24006",
            "99990",
        ]
        | None,
        Field(
            description='Weitere besondere Zweckbestimmung der Grünfläche, die die zugehörige allgemeine Zweckbestimmung detailliert oder ersetzt. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {"name": "ParkanlageHistorisch"},
                    "10001": {"name": "ParkanlageNaturnah"},
                    "10002": {"name": "ParkanlageWaldcharakter"},
                    "10003": {"name": "NaturnaheUferParkanlage"},
                    "12000": {"name": "ErholungsGaerten"},
                    "14000": {"name": "Reitsportanlage"},
                    "14001": {"name": "Hundesportanlage"},
                    "14002": {"name": "Wassersportanlage"},
                    "14003": {"name": "Schiessstand"},
                    "14004": {"name": "Golfplatz"},
                    "14005": {"name": "Skisport"},
                    "14006": {"name": "Tennisanlage"},
                    "14007": {"name": "SonstigerSportplatz"},
                    "16000": {"name": "Bolzplatz"},
                    "16001": {"name": "Abenteuerspielplatz"},
                    "18000": {"name": "Campingplatz"},
                    "22000": {"name": "Kleintierhaltung"},
                    "22001": {"name": "Festplatz"},
                    "24000": {"name": "StrassenbegleitGruen"},
                    "24001": {"name": "BoeschungsFlaeche"},
                    "24002": {"name": "FeldWaldWiese"},
                    "24003": {"name": "Uferschutzstreifen"},
                    "24004": {"name": "Abschirmgruen"},
                    "24005": {"name": "UmweltbildungsparkSchaugatter"},
                    "24006": {"name": "RuhenderVerkehr"},
                    "99990": {"name": "Gaertnerei"},
                },
                "typename": "XP_BesondereZweckbestimmungGruen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereBesondZweckbestimmung2: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "12000",
            "14000",
            "14001",
            "14002",
            "14003",
            "14004",
            "14005",
            "14006",
            "14007",
            "16000",
            "16001",
            "18000",
            "22000",
            "22001",
            "24000",
            "24001",
            "24002",
            "24003",
            "24004",
            "24005",
            "24006",
            "99990",
        ]
        | None,
        Field(
            description='Weitere besondere Zweckbestimmung der Grünfläche, die die zugehörige allgemeine Zweckbestimmung detailliert oder ersetzt. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {"name": "ParkanlageHistorisch"},
                    "10001": {"name": "ParkanlageNaturnah"},
                    "10002": {"name": "ParkanlageWaldcharakter"},
                    "10003": {"name": "NaturnaheUferParkanlage"},
                    "12000": {"name": "ErholungsGaerten"},
                    "14000": {"name": "Reitsportanlage"},
                    "14001": {"name": "Hundesportanlage"},
                    "14002": {"name": "Wassersportanlage"},
                    "14003": {"name": "Schiessstand"},
                    "14004": {"name": "Golfplatz"},
                    "14005": {"name": "Skisport"},
                    "14006": {"name": "Tennisanlage"},
                    "14007": {"name": "SonstigerSportplatz"},
                    "16000": {"name": "Bolzplatz"},
                    "16001": {"name": "Abenteuerspielplatz"},
                    "18000": {"name": "Campingplatz"},
                    "22000": {"name": "Kleintierhaltung"},
                    "22001": {"name": "Festplatz"},
                    "24000": {"name": "StrassenbegleitGruen"},
                    "24001": {"name": "BoeschungsFlaeche"},
                    "24002": {"name": "FeldWaldWiese"},
                    "24003": {"name": "Uferschutzstreifen"},
                    "24004": {"name": "Abschirmgruen"},
                    "24005": {"name": "UmweltbildungsparkSchaugatter"},
                    "24006": {"name": "RuhenderVerkehr"},
                    "99990": {"name": "Gaertnerei"},
                },
                "typename": "XP_BesondereZweckbestimmungGruen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereBesondZweckbestimmung3: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "12000",
            "14000",
            "14001",
            "14002",
            "14003",
            "14004",
            "14005",
            "14006",
            "14007",
            "16000",
            "16001",
            "18000",
            "22000",
            "22001",
            "24000",
            "24001",
            "24002",
            "24003",
            "24004",
            "24005",
            "24006",
            "99990",
        ]
        | None,
        Field(
            description='Weitere besondere Zweckbestimmung der Grünfläche, die die zugehörige allgemeine Zweckbestimmung detailliert oder ersetzt. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {"name": "ParkanlageHistorisch"},
                    "10001": {"name": "ParkanlageNaturnah"},
                    "10002": {"name": "ParkanlageWaldcharakter"},
                    "10003": {"name": "NaturnaheUferParkanlage"},
                    "12000": {"name": "ErholungsGaerten"},
                    "14000": {"name": "Reitsportanlage"},
                    "14001": {"name": "Hundesportanlage"},
                    "14002": {"name": "Wassersportanlage"},
                    "14003": {"name": "Schiessstand"},
                    "14004": {"name": "Golfplatz"},
                    "14005": {"name": "Skisport"},
                    "14006": {"name": "Tennisanlage"},
                    "14007": {"name": "SonstigerSportplatz"},
                    "16000": {"name": "Bolzplatz"},
                    "16001": {"name": "Abenteuerspielplatz"},
                    "18000": {"name": "Campingplatz"},
                    "22000": {"name": "Kleintierhaltung"},
                    "22001": {"name": "Festplatz"},
                    "24000": {"name": "StrassenbegleitGruen"},
                    "24001": {"name": "BoeschungsFlaeche"},
                    "24002": {"name": "FeldWaldWiese"},
                    "24003": {"name": "Uferschutzstreifen"},
                    "24004": {"name": "Abschirmgruen"},
                    "24005": {"name": "UmweltbildungsparkSchaugatter"},
                    "24006": {"name": "RuhenderVerkehr"},
                    "99990": {"name": "Gaertnerei"},
                },
                "typename": "XP_BesondereZweckbestimmungGruen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereBesondZweckbestimmung4: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "12000",
            "14000",
            "14001",
            "14002",
            "14003",
            "14004",
            "14005",
            "14006",
            "14007",
            "16000",
            "16001",
            "18000",
            "22000",
            "22001",
            "24000",
            "24001",
            "24002",
            "24003",
            "24004",
            "24005",
            "24006",
            "99990",
        ]
        | None,
        Field(
            description='Weitere besondere Zweckbestimmung der Grünfläche, die die zugehörige allgemeine Zweckbestimmung detailliert oder ersetzt. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {"name": "ParkanlageHistorisch"},
                    "10001": {"name": "ParkanlageNaturnah"},
                    "10002": {"name": "ParkanlageWaldcharakter"},
                    "10003": {"name": "NaturnaheUferParkanlage"},
                    "12000": {"name": "ErholungsGaerten"},
                    "14000": {"name": "Reitsportanlage"},
                    "14001": {"name": "Hundesportanlage"},
                    "14002": {"name": "Wassersportanlage"},
                    "14003": {"name": "Schiessstand"},
                    "14004": {"name": "Golfplatz"},
                    "14005": {"name": "Skisport"},
                    "14006": {"name": "Tennisanlage"},
                    "14007": {"name": "SonstigerSportplatz"},
                    "16000": {"name": "Bolzplatz"},
                    "16001": {"name": "Abenteuerspielplatz"},
                    "18000": {"name": "Campingplatz"},
                    "22000": {"name": "Kleintierhaltung"},
                    "22001": {"name": "Festplatz"},
                    "24000": {"name": "StrassenbegleitGruen"},
                    "24001": {"name": "BoeschungsFlaeche"},
                    "24002": {"name": "FeldWaldWiese"},
                    "24003": {"name": "Uferschutzstreifen"},
                    "24004": {"name": "Abschirmgruen"},
                    "24005": {"name": "UmweltbildungsparkSchaugatter"},
                    "24006": {"name": "RuhenderVerkehr"},
                    "99990": {"name": "Gaertnerei"},
                },
                "typename": "XP_BesondereZweckbestimmungGruen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteZweckbestimmung: Annotated[
        list[AnyUrl] | None,
        Field(
            description="Über eine CodeList definierte zusätzliche Zweckbestimmungen.",
            json_schema_extra={
                "typename": "BP_DetailZweckbestGruenFlaeche",
                "stereotype": "Codelist",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung1: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestGruenFlaeche",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung2: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestGruenFlaeche",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung3: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestGruenFlaeche",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung4: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestGruenFlaeche",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    nutzungsform: Annotated[
        Literal["1000", "2000"] | None,
        Field(
            description="Nutzungform der festgesetzten Fläche.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Privat", "description": "Private Nutzung"},
                    "2000": {
                        "name": "Oeffentlich",
                        "description": "Öffentliche Nutzung",
                    },
                },
                "typename": "XP_Nutzungsform",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    zugunstenVon: Annotated[
        str | None,
        Field(
            description="Angabe des Begünstigen einer Ausweisung.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPHoehenMass(BPGeometrieobjekt):
    """Festsetzungen nach §9 Abs. 1 Nr. 1 BauGB für übereinanderliegende Geschosse und Ebenen und sonstige Teile baulicher Anlagen (§9 Abs.3 BauGB), sowie Hinweise auf Geländehöhen."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class BPImmissionsschutz(BPGeometrieobjekt):
    """Festsetzung einer von der Bebauung freizuhaltenden Schutzfläche und ihre Nutzung, sowie einer Fläche für besondere Anlagen und Vorkehrungen zum Schutz vor schädlichen Umwelteinwirkungen und sonstigen Gefahren im Sinne des Bundes-Immissionsschutzgesetzes sowie die zum Schutz vor solchen Einwirkungen oder zur  Vermeidung oder Minderung solcher Einwirkungen zu treffenden baulichen und sonstigen technischen Vorkehrungen (§9, Abs. 1, Nr. 24 BauGB)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    nutzung: Annotated[
        str | None,
        Field(
            description="Festgesetzte Nutzung einer Schutzfläche",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPKennzeichnungsFlaeche(BPFlaechenobjekt):
    """Flächen für Kennzeichnungen gemäß §9 Abs. 5 BauGB."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    zweckbestimmung: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000", "6000", "7000", "9999"]]
        | None,
        Field(
            description="Zweckbestimmungen der Fläche.",
            json_schema_extra={
                "typename": "XP_ZweckbestimmungKennzeichnung",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {
                        "name": "Naturgewalten",
                        "description": "Flächen, bei deren Bebauung besondere bauliche Sicherungsmaßnahmen gegen Naturgewalten erforderlich sind (§5, Abs. 3, Nr. 1 BauGB).",
                    },
                    "2000": {
                        "name": "Abbauflaeche",
                        "description": "Flächen, unter denen der Bergbau umgeht oder die für den Abbau von Mineralien bestimmt sind (§5, Abs. 3, Nr. 2 BauGB).",
                    },
                    "3000": {
                        "name": "AeussereEinwirkungen",
                        "description": "Flächen, bei deren Bebauung besondere bauliche Sicherungsmaßnahmen gegen äußere Einwirkungen erforderlich sind (§5, Abs. 3, Nr. 1 BauGB).",
                    },
                    "4000": {
                        "name": "SchadstoffBelastBoden",
                        "description": "Für bauliche Nutzung vorgesehene Flächen, deren Böden erheblich mit umweltgefährdenden Stoffen belastet sind (§5, Abs. 3, Nr. 3 BauGB).",
                    },
                    "5000": {
                        "name": "LaermBelastung",
                        "description": "ür bauliche Nutzung vorgesehene Flächen, die erheblichen Lärmbelastung ausgesetzt sind.",
                    },
                    "6000": {"name": "Bergbau"},
                    "7000": {"name": "Bodenordnung"},
                    "9999": {
                        "name": "AndereGesetzlVorschriften",
                        "description": "Kennzeichnung nach anderen gesetzlichen Vorschriften.",
                    },
                },
            },
        ),
    ] = None
    weitereZweckbestimmung: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "6000", "7000", "9999"] | None,
        Field(
            description='Weitere Zweckbestimmung der Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Naturgewalten",
                        "description": "Flächen, bei deren Bebauung besondere bauliche Sicherungsmaßnahmen gegen Naturgewalten erforderlich sind (§5, Abs. 3, Nr. 1 BauGB).",
                    },
                    "2000": {
                        "name": "Abbauflaeche",
                        "description": "Flächen, unter denen der Bergbau umgeht oder die für den Abbau von Mineralien bestimmt sind (§5, Abs. 3, Nr. 2 BauGB).",
                    },
                    "3000": {
                        "name": "AeussereEinwirkungen",
                        "description": "Flächen, bei deren Bebauung besondere bauliche Sicherungsmaßnahmen gegen äußere Einwirkungen erforderlich sind (§5, Abs. 3, Nr. 1 BauGB).",
                    },
                    "4000": {
                        "name": "SchadstoffBelastBoden",
                        "description": "Für bauliche Nutzung vorgesehene Flächen, deren Böden erheblich mit umweltgefährdenden Stoffen belastet sind (§5, Abs. 3, Nr. 3 BauGB).",
                    },
                    "5000": {
                        "name": "LaermBelastung",
                        "description": "ür bauliche Nutzung vorgesehene Flächen, die erheblichen Lärmbelastung ausgesetzt sind.",
                    },
                    "6000": {"name": "Bergbau"},
                    "7000": {"name": "Bodenordnung"},
                    "9999": {
                        "name": "AndereGesetzlVorschriften",
                        "description": "Kennzeichnung nach anderen gesetzlichen Vorschriften.",
                    },
                },
                "typename": "XP_ZweckbestimmungKennzeichnung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPKleintierhaltungFlaeche(BPFlaechenschlussobjekt):
    """Fläche für die Errichtung von Anlagen für die Kleintierhaltung woe Ausstellungs- und Zuchtanlagen, Zwinger, Koppeln und dergleichen (§9 Abs. 19 BauGB)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class BPLandwirtschaft(BPGeometrieobjekt):
    """Festsetzungen für die Landwirtschaft  (§9, Abs. 1, Nr. 18a BauGB)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    zweckbestimmung: Annotated[
        list[
            Literal[
                "1000", "1100", "1200", "1300", "1400", "1500", "1600", "1700", "9999"
            ]
        ]
        | None,
        Field(
            description="Zweckbestimmungen der Ausweisung.",
            json_schema_extra={
                "typename": "XP_ZweckbestimmungLandwirtschaft",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {
                        "name": "LandwirtschaftAllgemein",
                        "description": "Allgemeine Landwirtschaft",
                    },
                    "1100": {"name": "Ackerbau", "description": "Ackerbau"},
                    "1200": {
                        "name": "WiesenWeidewirtschaft",
                        "description": "Wiesen- und Weidewirtschaft",
                    },
                    "1300": {
                        "name": "GartenbaulicheErzeugung",
                        "description": "Gartenbauliche Erzeugung",
                    },
                    "1400": {"name": "Obstbau", "description": "Obstbau"},
                    "1500": {"name": "Weinbau", "description": "Weinbau"},
                    "1600": {"name": "Imkerei", "description": "Imkerei"},
                    "1700": {
                        "name": "Binnenfischerei",
                        "description": "Binnenfischerei",
                    },
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
            },
        ),
    ] = None
    weitereZweckbestimmung1: Annotated[
        Literal["1000", "1100", "1200", "1300", "1400", "1500", "1600", "1700", "9999"]
        | None,
        Field(
            description='Weitere Zweckbestimmung der Ausweisung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "LandwirtschaftAllgemein",
                        "description": "Allgemeine Landwirtschaft",
                    },
                    "1100": {"name": "Ackerbau", "description": "Ackerbau"},
                    "1200": {
                        "name": "WiesenWeidewirtschaft",
                        "description": "Wiesen- und Weidewirtschaft",
                    },
                    "1300": {
                        "name": "GartenbaulicheErzeugung",
                        "description": "Gartenbauliche Erzeugung",
                    },
                    "1400": {"name": "Obstbau", "description": "Obstbau"},
                    "1500": {"name": "Weinbau", "description": "Weinbau"},
                    "1600": {"name": "Imkerei", "description": "Imkerei"},
                    "1700": {
                        "name": "Binnenfischerei",
                        "description": "Binnenfischerei",
                    },
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungLandwirtschaft",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung2: Annotated[
        Literal["1000", "1100", "1200", "1300", "1400", "1500", "1600", "1700", "9999"]
        | None,
        Field(
            description='Weitere Zweckbestimmung der Ausweisung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "LandwirtschaftAllgemein",
                        "description": "Allgemeine Landwirtschaft",
                    },
                    "1100": {"name": "Ackerbau", "description": "Ackerbau"},
                    "1200": {
                        "name": "WiesenWeidewirtschaft",
                        "description": "Wiesen- und Weidewirtschaft",
                    },
                    "1300": {
                        "name": "GartenbaulicheErzeugung",
                        "description": "Gartenbauliche Erzeugung",
                    },
                    "1400": {"name": "Obstbau", "description": "Obstbau"},
                    "1500": {"name": "Weinbau", "description": "Weinbau"},
                    "1600": {"name": "Imkerei", "description": "Imkerei"},
                    "1700": {
                        "name": "Binnenfischerei",
                        "description": "Binnenfischerei",
                    },
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungLandwirtschaft",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung3: Annotated[
        Literal["1000", "1100", "1200", "1300", "1400", "1500", "1600", "1700", "9999"]
        | None,
        Field(
            description='Weitere Zweckbestimmung der Ausweisung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "LandwirtschaftAllgemein",
                        "description": "Allgemeine Landwirtschaft",
                    },
                    "1100": {"name": "Ackerbau", "description": "Ackerbau"},
                    "1200": {
                        "name": "WiesenWeidewirtschaft",
                        "description": "Wiesen- und Weidewirtschaft",
                    },
                    "1300": {
                        "name": "GartenbaulicheErzeugung",
                        "description": "Gartenbauliche Erzeugung",
                    },
                    "1400": {"name": "Obstbau", "description": "Obstbau"},
                    "1500": {"name": "Weinbau", "description": "Weinbau"},
                    "1600": {"name": "Imkerei", "description": "Imkerei"},
                    "1700": {
                        "name": "Binnenfischerei",
                        "description": "Binnenfischerei",
                    },
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungLandwirtschaft",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteZweckbestimmung: Annotated[
        list[AnyUrl] | None,
        Field(
            description="Über eine CodeList definierte zusätzliche Zweckbestimmungen.",
            json_schema_extra={
                "typename": "BP_DetailZweckbestLandwirtschaft",
                "stereotype": "Codelist",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung1: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestLandwirtschaft",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung2: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestLandwirtschaft",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung3: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestLandwirtschaft",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPLinienobjekt(BPObjekt):
    """Basisklasse für alle Objekte eines Bebauungsplans mit linienförmigem Raumbezug (Eine einzelne zusammenhängende Kurve, die aus Linienstücken und Kreisbögen zusammengesetzt sein kann, oder eine Menge derartiger Kurven)."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Line | definitions.MultiLine,
        Field(
            description="Linienförmiger Raumbezug (Einzelne zusammenhängende Kurve, die aus Linienstücken und Kreisbögen aufgebaut sit, oder eine Menge derartiger Kurven),",
            json_schema_extra={
                "typename": "XP_Liniengeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class BPNutzungsartenGrenze(BPLinienobjekt):
    """Abgrenzung unterschiedlicher Nutzung, z.B. von Baugebieten wenn diese nach PlanzVO in der gleichen Farbe dargestellt werden, oder Abgrenzung unterschiedlicher Nutzungsmaße innerhalb eines Baugebiets ("Knödellinie", §1 Abs. 4, §16 Abs. 5 BauNVO)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    typ: Annotated[
        Literal["1000", "9999"] | None,
        Field(
            description="Typ der Abgrenzung. Wenn das Attribut nicht belegt ist, ist die Abgrenzung eine Nutzungsarten-Grenze (Schlüsselnummer 1000).",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Nutzungsartengrenze",
                        "description": "Nutzungsarten-Grenze zur Abgrenzung von Baugebieten mit unterschiedlicher Art oder unterschiedlichem Maß der baulichen Nutzung.",
                    },
                    "9999": {
                        "name": "SonstigeAbgrenzung",
                        "description": "Sonstige Abgrenzung",
                    },
                },
                "typename": "BP_AbgrenzungenTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detailTyp: Annotated[
        AnyUrl | None,
        Field(
            description="Detaillierter Typ der Abgrenzung, wenn das Attribut typ den Wert 9999 (Sonstige Abgrenzung) hat.",
            json_schema_extra={
                "typename": "BP_DetailAbgrenzungenTypen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPRekultivierungsFlaeche(BPFlaechenobjekt):
    """Rekultivierungs-Fläche"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class BPSchutzPflegeEntwicklungsFlaeche(BPFlaechenobjekt):
    """Umgrenzung von Flächen für Maßnahmen zum Schutz, zur Pflege und zur Entwicklung von Natur und Landschaft (§9 Abs. 1 Nr. 20 und Abs. 4 BauGB)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    ziel: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"] | None,
        Field(
            description='Unterscheidung nach den Zielen "Schutz, Pflege" und "Entwicklung".',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "SchutzPflege"},
                    "2000": {"name": "Entwicklung"},
                    "3000": {"name": "Anlage"},
                    "4000": {"name": "SchutzPflegeEntwicklung"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "XP_SPEZiele",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    massnahme: Annotated[
        list[XPSPEMassnahmenDaten] | None,
        Field(
            description="Durchzuführende Maßnahmen.",
            json_schema_extra={
                "typename": "XP_SPEMassnahmenDaten",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    weitereMassnahme1: Annotated[
        XPSPEMassnahmenDaten | None,
        Field(
            description='Weitere durchzuführende Massnahme. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen massnahme mehrfach belegt werden.',
            json_schema_extra={
                "typename": "XP_SPEMassnahmenDaten",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereMassnahme2: Annotated[
        XPSPEMassnahmenDaten | None,
        Field(
            description='Weitere durchzuführende Massnahme. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen massnahme mehrfach belegt werden.',
            json_schema_extra={
                "typename": "XP_SPEMassnahmenDaten",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    istAusgleich: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob die Fläche zum Ausglich von Eingriffen genutzt wird.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False
    refMassnahmenText: Annotated[
        XPExterneReferenz | None,
        Field(
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            }
        ),
    ] = None
    refLandschaftsplan: Annotated[
        XPExterneReferenz | None,
        Field(
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            }
        ),
    ] = None


class BPSchutzPflegeEntwicklungsMassnahme(BPGeometrieobjekt):
    """Maßnahmen zum Schutz, zur Pflege und zur Entwicklung von Natur und Landschaft (§9 Abs. 1 Nr. 20 und Abs. 4 BauGB)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    ziel: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"] | None,
        Field(
            description='Unterscheidung nach den Zielen "Schutz, Pflege" und "Entwicklung".',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "SchutzPflege"},
                    "2000": {"name": "Entwicklung"},
                    "3000": {"name": "Anlage"},
                    "4000": {"name": "SchutzPflegeEntwicklung"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "XP_SPEZiele",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    massnahme: Annotated[
        list[XPSPEMassnahmenDaten] | None,
        Field(
            description="Durchzuführende Maßnahmen",
            json_schema_extra={
                "typename": "XP_SPEMassnahmenDaten",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    weitereMassnahme1: Annotated[
        XPSPEMassnahmenDaten | None,
        Field(
            description='Weitere durchzuführende Massnahme. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen massnahme mehrfach belegt werden.',
            json_schema_extra={
                "typename": "XP_SPEMassnahmenDaten",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereMassnahme2: Annotated[
        XPSPEMassnahmenDaten | None,
        Field(
            description='Weitere durchzuführende Massnahme. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen massnahme mehrfach belegt werden.',
            json_schema_extra={
                "typename": "XP_SPEMassnahmenDaten",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    istAusgleich: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob die Maßnahme zum Ausgleich von Eingriffen genutzt wird.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False
    refMassnahmenText: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf ein Dokument, das die durchzuführenden Maßnahmen beschreibt.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refLandschaftsplan: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf den Landschaftsplan.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPSchutzgebiet(BPGeometrieobjekt):
    """Umgrenzung von Schutzgebieten und Schutzobjekten im Sinne des Naturschutzrechts (§9 Abs. 4 BauGB), sofern es sich um eine Festsetzung des Bebauungsplans handelt."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    zweckbestimmung: Annotated[
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
            "18000",
            "18001",
            "2000",
            "9999",
        ]
        | None,
        Field(
            description="Zweckbestimmung des Schutzgebiets",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Naturschutzgebiet",
                        "description": "Naturschutzgebiet",
                    },
                    "1100": {"name": "Nationalpark", "description": "Nationalpark"},
                    "1200": {
                        "name": "Biosphaerenreservat",
                        "description": "Biosphaerenreservate",
                    },
                    "1300": {
                        "name": "Landschaftsschutzgebiet",
                        "description": "Landschaftsschutzgebiet",
                    },
                    "1400": {"name": "Naturpark", "description": "Naturpark"},
                    "1500": {"name": "Naturdenkmal", "description": "Naturdenkmal"},
                    "1600": {
                        "name": "GeschuetzterLandschaftsBestandteil",
                        "description": "Geschützter Bestandteil der Landschaft",
                    },
                    "1700": {
                        "name": "GesetzlichGeschuetztesBiotop",
                        "description": "Gesetzlich geschützte Biotope",
                    },
                    "1800": {
                        "name": "Natura2000",
                        "description": 'Schutzgebiet nach Europäischem Recht. Die umfasst das "Gebiet Gemeinschaftlicher Bedeutung" (FFH-Gebiet) und das "Europäische Vogelschutzgebiet"',
                    },
                    "18000": {
                        "name": "GebietGemeinschaftlicherBedeutung",
                        "description": "Gebiete von gemeinschaftlicher Bedeutung",
                    },
                    "18001": {
                        "name": "EuropaeischesVogelschutzgebiet",
                        "description": "Europäische Vogelschutzgebiete",
                    },
                    "2000": {"name": "NationalesNaturmonument"},
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_KlassifizSchutzgebietNaturschutzrecht",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteZweckbestimmung: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definierte Zweckbestimmung des Schutzgebietes.",
            json_schema_extra={
                "typename": "BP_DetailZweckbestNaturschutzgebiet",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPSpielSportanlagenFlaeche(BPFlaechenschlussobjekt):
    """Einrichtungen und Anlagen zur Versorgung mit Gütern und Dienstleistungen des öffentlichen und privaten Bereichs, hier Flächen für Sport- und Spielanlagen (§9, Abs. 1, Nr. 5 und Abs. 6 BauGB)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    MaxZahlWohnungen: Annotated[
        int | None,
        Field(
            description="Höchstzulässige Zahl der Wohnungen in Wohngebäuden",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Fmin: Annotated[
        definitions.Area | None,
        Field(
            description="Mindestmaß für die Größe (Fläche) eines Baugrundstücks.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Fmax: Annotated[
        definitions.Area | None,
        Field(
            description="Höchstmaß für die Größe (Fläche) eines Baugrundstücks.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Bmin: Annotated[
        definitions.Length | None,
        Field(
            description="Minimale Breite von Baugrundstücken",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Bmax: Annotated[
        definitions.Length | None,
        Field(
            description="Maximale Breite von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Tmin: Annotated[
        definitions.Length | None,
        Field(
            description="Minimale Tiefe von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Tmax: Annotated[
        definitions.Length | None,
        Field(
            description="Maximale Tiefe von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    GFZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Geschossflächenzahl .",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl bei einer Bereichsangabe. Das Attribut GFZmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZ_Ausn: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl als Ausnahme.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFmin: Annotated[
        definitions.Area | None,
        Field(
            description="Minimal zulässige Geschossfläche",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GFmax: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Geschossfläche bei einer Bereichsabgabe. Das Attribut GFmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GF: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Geschossfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GF_Ausn: Annotated[
        definitions.Area | None,
        Field(
            description="Ausnahmsweise maximal zulässige Geschossfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    BMZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Baumassenzahl",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Baumassenzahl bei einer Bereichsangabe. Das Attribut BMZmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Baumassenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZ_Ausn: Annotated[
        float | None,
        Field(
            description="Ausnahmsweise maximal zulässige Baumassenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMmin: Annotated[
        definitions.Volume | None,
        Field(
            description="Minimal zulässinge Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BMmax: Annotated[
        definitions.Volume | None,
        Field(
            description="Maximal zulässinge Baumasse bei einer Bereichsangabe. Das Attribut BMmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BM: Annotated[
        definitions.Volume | None,
        Field(
            description="Maximal zulässige Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BM_Ausn: Annotated[
        definitions.Volume | None,
        Field(
            description="Ausnahmsweise maximal zulässige Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    GRZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Grundflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Grundflächenzahl bei einer Bereichsangabe.  Das Attribut GRZmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Grundflächenzahl",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZ_Ausn: Annotated[
        float | None,
        Field(
            description="Ausnahmsweise maximal zulässige Grundflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRmin: Annotated[
        definitions.Area | None,
        Field(
            description="Minimal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GRmax: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Grundfläche bei einer Bereichsangabe. Das Attribut GRmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GR: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GR_Ausn: Annotated[
        definitions.Area | None,
        Field(
            description="Ausnahmsweise maximal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Zmin: Annotated[
        int | None,
        Field(
            description="Minimal zulässige Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Zmax: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der oberirdischen Vollgeschosse bei einer Bereichsangabe. Das Attribut Zmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Zzwingend: Annotated[
        int | None,
        Field(
            description="Zwingend vorgeschriebene Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z: Annotated[
        int | None,
        Field(
            description="Maximalzahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Ausn: Annotated[
        int | None,
        Field(
            description="Ausnahmsweise maximal zulässige Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Staffel: Annotated[
        int | None,
        Field(
            description="Maximalzahl von oberirdischen zurückgesetzten Vollgeschossen als Staffelgeschoss..",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Dach: Annotated[
        int | None,
        Field(
            description="Maximalzahl der zusätzlich erlaubten Dachgeschosse, die gleichzeitig Vollgeschosse sind.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUmin: Annotated[
        int | None,
        Field(
            description="Minimal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUmax: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der unterirdischen Geschosse bei einer Bereichsangabe. Das Attribut ZUmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUzwingend: Annotated[
        int | None,
        Field(
            description="Zwingend vorgeschriebene Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZU: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZU_Ausn: Annotated[
        int | None,
        Field(
            description="Ausnahmsweise maximal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    zweckbestimmung: Annotated[
        list[Literal["1000", "2000", "3000", "9999"]] | None,
        Field(
            description="Zweckbestimmungen der festgesetzten Fläche.",
            json_schema_extra={
                "typename": "XP_ZweckbestimmungSpielSportanlage",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Sportanlage", "description": "Sportanlage"},
                    "2000": {"name": "Spielanlage", "description": "Spielanlage"},
                    "3000": {
                        "name": "SpielSportanlage",
                        "description": "Spiel- und/oder Sportanlage.",
                    },
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
            },
        ),
    ] = None
    weitereZweckbestimmung1: Annotated[
        Literal["1000", "2000", "3000", "9999"] | None,
        Field(
            description='Weitere Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Sportanlage", "description": "Sportanlage"},
                    "2000": {"name": "Spielanlage", "description": "Spielanlage"},
                    "3000": {
                        "name": "SpielSportanlage",
                        "description": "Spiel- und/oder Sportanlage.",
                    },
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungSpielSportanlage",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteZweckbestimmung: Annotated[
        list[AnyUrl] | None,
        Field(
            description="Über eine CodeList definierte zusätzliche Zweckbestimmungen.",
            json_schema_extra={
                "typename": "BP_DetailZweckbestSpielSportanlage",
                "stereotype": "Codelist",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung1: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestSpielSportanlage",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    zugunstenVon: Annotated[
        str | None,
        Field(
            description="Angabe des Begünstigten einer Ausweisung.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPStrassenVerkehrsFlaeche(BPFlaechenschlussobjekt):
    """Strassenverkehrsfläche (§9 Abs. 1 Nr. 11 und Abs. 6 BauGB) ."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    MaxZahlWohnungen: Annotated[
        int | None,
        Field(
            description="Höchstzulässige Zahl der Wohnungen in Wohngebäuden",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Fmin: Annotated[
        definitions.Area | None,
        Field(
            description="Mindestmaß für die Größe (Fläche) eines Baugrundstücks.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Fmax: Annotated[
        definitions.Area | None,
        Field(
            description="Höchstmaß für die Größe (Fläche) eines Baugrundstücks.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Bmin: Annotated[
        definitions.Length | None,
        Field(
            description="Minimale Breite von Baugrundstücken",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Bmax: Annotated[
        definitions.Length | None,
        Field(
            description="Maximale Breite von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Tmin: Annotated[
        definitions.Length | None,
        Field(
            description="Minimale Tiefe von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Tmax: Annotated[
        definitions.Length | None,
        Field(
            description="Maximale Tiefe von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    GFZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Geschossflächenzahl .",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl bei einer Bereichsangabe. Das Attribut GFZmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZ_Ausn: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl als Ausnahme.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFmin: Annotated[
        definitions.Area | None,
        Field(
            description="Minimal zulässige Geschossfläche",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GFmax: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Geschossfläche bei einer Bereichsabgabe. Das Attribut GFmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GF: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Geschossfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GF_Ausn: Annotated[
        definitions.Area | None,
        Field(
            description="Ausnahmsweise maximal zulässige Geschossfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    BMZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Baumassenzahl",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Baumassenzahl bei einer Bereichsangabe. Das Attribut BMZmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Baumassenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZ_Ausn: Annotated[
        float | None,
        Field(
            description="Ausnahmsweise maximal zulässige Baumassenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMmin: Annotated[
        definitions.Volume | None,
        Field(
            description="Minimal zulässinge Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BMmax: Annotated[
        definitions.Volume | None,
        Field(
            description="Maximal zulässinge Baumasse bei einer Bereichsangabe. Das Attribut BMmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BM: Annotated[
        definitions.Volume | None,
        Field(
            description="Maximal zulässige Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BM_Ausn: Annotated[
        definitions.Volume | None,
        Field(
            description="Ausnahmsweise maximal zulässige Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    GRZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Grundflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Grundflächenzahl bei einer Bereichsangabe.  Das Attribut GRZmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Grundflächenzahl",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZ_Ausn: Annotated[
        float | None,
        Field(
            description="Ausnahmsweise maximal zulässige Grundflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRmin: Annotated[
        definitions.Area | None,
        Field(
            description="Minimal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GRmax: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Grundfläche bei einer Bereichsangabe. Das Attribut GRmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GR: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GR_Ausn: Annotated[
        definitions.Area | None,
        Field(
            description="Ausnahmsweise maximal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Zmin: Annotated[
        int | None,
        Field(
            description="Minimal zulässige Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Zmax: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der oberirdischen Vollgeschosse bei einer Bereichsangabe. Das Attribut Zmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Zzwingend: Annotated[
        int | None,
        Field(
            description="Zwingend vorgeschriebene Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z: Annotated[
        int | None,
        Field(
            description="Maximalzahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Ausn: Annotated[
        int | None,
        Field(
            description="Ausnahmsweise maximal zulässige Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Staffel: Annotated[
        int | None,
        Field(
            description="Maximalzahl von oberirdischen zurückgesetzten Vollgeschossen als Staffelgeschoss..",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Dach: Annotated[
        int | None,
        Field(
            description="Maximalzahl der zusätzlich erlaubten Dachgeschosse, die gleichzeitig Vollgeschosse sind.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUmin: Annotated[
        int | None,
        Field(
            description="Minimal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUmax: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der unterirdischen Geschosse bei einer Bereichsangabe. Das Attribut ZUmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUzwingend: Annotated[
        int | None,
        Field(
            description="Zwingend vorgeschriebene Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZU: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZU_Ausn: Annotated[
        int | None,
        Field(
            description="Ausnahmsweise maximal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    nutzungsform: Annotated[
        Literal["1000", "2000"] | None,
        Field(
            description="Nutzungsform der Fläche",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Privat", "description": "Private Nutzung"},
                    "2000": {
                        "name": "Oeffentlich",
                        "description": "Öffentliche Nutzung",
                    },
                },
                "typename": "XP_Nutzungsform",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    begrenzungslinie: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "BP_StrassenbegrenzungsLinie",
                "stereotype": "Association",
                "multiplicity": "0..*",
            }
        ),
    ] = None


class BPStrassenbegrenzungsLinie(BPLinienobjekt):
    """Straßenbegrenzungslinie (§9 Abs. 1 Nr. 11 und Abs. 6 BauGB) ."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    bautiefe: Annotated[
        definitions.Length | None,
        Field(
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            }
        ),
    ] = None


class BPStrassenkoerper(BPGeometrieobjekt):
    """Flächen für Aufschüttungen, Abgrabungen und Stützmauern, soweit sie zur Herstellung des Straßenkörpers erforderlich sind (§9, Abs. 1, Nr. 26 BauGB)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    typ: Annotated[
        Literal["1000", "2000", "3000"],
        Field(
            description="Notwendige Maßnahme zur Herstellung des Straßenkörpers.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Aufschuettung"},
                    "2000": {"name": "Abgrabung"},
                    "3000": {"name": "Stuetzmauer"},
                },
                "typename": "BP_StrassenkoerperHerstellung",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]


class BPUeberlagerungsobjekt(BPFlaechenobjekt):
    """Basisklasse für alle Objekte eines Bebauungsplans mit flächenhaftem Raumbezug, die immer Überlagerungsobjekte sind."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class BPUnverbindlicheVormerkung(BPGeometrieobjekt):
    """Unverbindliche Vormerkung späterer Planungsabsichten."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    vormerkung: Annotated[
        str | None,
        Field(
            description="Text der Vormerkung.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPVerEntsorgung(BPGeometrieobjekt):
    """Flächen und Leitungen für Versorgungsanlagen, für die Abfallentsorgung und Abwasserbeseitigung sowie für Ablagerungen (§9 Abs. 1, Nr. 12, 14 und Abs. 6 BauGB)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    MaxZahlWohnungen: Annotated[
        int | None,
        Field(
            description="Höchstzulässige Zahl der Wohnungen in Wohngebäuden",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Fmin: Annotated[
        definitions.Area | None,
        Field(
            description="Mindestmaß für die Größe (Fläche) eines Baugrundstücks.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Fmax: Annotated[
        definitions.Area | None,
        Field(
            description="Höchstmaß für die Größe (Fläche) eines Baugrundstücks.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Bmin: Annotated[
        definitions.Length | None,
        Field(
            description="Minimale Breite von Baugrundstücken",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Bmax: Annotated[
        definitions.Length | None,
        Field(
            description="Maximale Breite von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Tmin: Annotated[
        definitions.Length | None,
        Field(
            description="Minimale Tiefe von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Tmax: Annotated[
        definitions.Length | None,
        Field(
            description="Maximale Tiefe von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    GFZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Geschossflächenzahl .",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl bei einer Bereichsangabe. Das Attribut GFZmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZ_Ausn: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl als Ausnahme.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFmin: Annotated[
        definitions.Area | None,
        Field(
            description="Minimal zulässige Geschossfläche",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GFmax: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Geschossfläche bei einer Bereichsabgabe. Das Attribut GFmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GF: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Geschossfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GF_Ausn: Annotated[
        definitions.Area | None,
        Field(
            description="Ausnahmsweise maximal zulässige Geschossfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    BMZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Baumassenzahl",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Baumassenzahl bei einer Bereichsangabe. Das Attribut BMZmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Baumassenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZ_Ausn: Annotated[
        float | None,
        Field(
            description="Ausnahmsweise maximal zulässige Baumassenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMmin: Annotated[
        definitions.Volume | None,
        Field(
            description="Minimal zulässinge Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BMmax: Annotated[
        definitions.Volume | None,
        Field(
            description="Maximal zulässinge Baumasse bei einer Bereichsangabe. Das Attribut BMmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BM: Annotated[
        definitions.Volume | None,
        Field(
            description="Maximal zulässige Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BM_Ausn: Annotated[
        definitions.Volume | None,
        Field(
            description="Ausnahmsweise maximal zulässige Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    GRZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Grundflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Grundflächenzahl bei einer Bereichsangabe.  Das Attribut GRZmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Grundflächenzahl",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZ_Ausn: Annotated[
        float | None,
        Field(
            description="Ausnahmsweise maximal zulässige Grundflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRmin: Annotated[
        definitions.Area | None,
        Field(
            description="Minimal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GRmax: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Grundfläche bei einer Bereichsangabe. Das Attribut GRmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GR: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GR_Ausn: Annotated[
        definitions.Area | None,
        Field(
            description="Ausnahmsweise maximal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Zmin: Annotated[
        int | None,
        Field(
            description="Minimal zulässige Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Zmax: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der oberirdischen Vollgeschosse bei einer Bereichsangabe. Das Attribut Zmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Zzwingend: Annotated[
        int | None,
        Field(
            description="Zwingend vorgeschriebene Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z: Annotated[
        int | None,
        Field(
            description="Maximalzahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Ausn: Annotated[
        int | None,
        Field(
            description="Ausnahmsweise maximal zulässige Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Staffel: Annotated[
        int | None,
        Field(
            description="Maximalzahl von oberirdischen zurückgesetzten Vollgeschossen als Staffelgeschoss..",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Dach: Annotated[
        int | None,
        Field(
            description="Maximalzahl der zusätzlich erlaubten Dachgeschosse, die gleichzeitig Vollgeschosse sind.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUmin: Annotated[
        int | None,
        Field(
            description="Minimal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUmax: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der unterirdischen Geschosse bei einer Bereichsangabe. Das Attribut ZUmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUzwingend: Annotated[
        int | None,
        Field(
            description="Zwingend vorgeschriebene Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZU: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZU_Ausn: Annotated[
        int | None,
        Field(
            description="Ausnahmsweise maximal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    zweckbestimmung: Annotated[
        list[
            Literal[
                "1000",
                "1200",
                "1300",
                "1400",
                "1600",
                "1800",
                "2000",
                "2200",
                "2400",
                "2600",
                "2800",
                "3000",
                "9999",
            ]
        ]
        | None,
        Field(
            description="Allgemeine Zweckbestimmungen der Fläche",
            json_schema_extra={
                "typename": "XP_ZweckbestimmungVerEntsorgung",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {
                        "name": "Elektrizitaet",
                        "description": "Versorgung mit Elektrizität",
                    },
                    "1200": {"name": "Gas", "description": "Gas-Versorgung"},
                    "1300": {"name": "Erdoel"},
                    "1400": {
                        "name": "Waermeversorgung",
                        "description": "Versorgung mit Fernwärme",
                    },
                    "1600": {"name": "Trinkwasser", "description": "Wasser-Versorgung"},
                    "1800": {"name": "Abwasser", "description": "Abwasser-Entsorgung"},
                    "2000": {
                        "name": "Regenwasser",
                        "description": "Regenwasser Entsorgung",
                    },
                    "2200": {
                        "name": "Abfallentsorgung",
                        "description": "Abfall-Beseitigung",
                    },
                    "2400": {
                        "name": "Ablagerung",
                        "description": "Ablagerungen, Deponien",
                    },
                    "2600": {
                        "name": "Telekommunikation",
                        "description": "Einrichtungen und Anlagen zur Telekommunikation",
                    },
                    "2800": {
                        "name": "ErneuerbareEnergien",
                        "description": "Anlagen, Einrichtungen oder sonstige Maßnahmen zur dezentralen und zentralen Erzeugung, Verteilung oder Speicherung von Strom, Wärme oder Kälte aus erneuerbaren Energien.",
                    },
                    "3000": {
                        "name": "KraftWaermeKopplung",
                        "description": "Anlagen, Einrichtungen oder sonstige Maßnahmen zur dezentralen und zentralen Erzeugung, Verteilung oder Speicherung von Strom, Wärme oder Kälte aus Kraft-Wärme Kopplung.",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstige Zweckbestimmung",
                    },
                },
            },
        ),
    ] = None
    weitereZweckbestimmung1: Annotated[
        Literal[
            "1000",
            "1200",
            "1300",
            "1400",
            "1600",
            "1800",
            "2000",
            "2200",
            "2400",
            "2600",
            "2800",
            "3000",
            "9999",
        ]
        | None,
        Field(
            description='Weitere allgemeine Zweckbestimmung der Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Elektrizitaet",
                        "description": "Versorgung mit Elektrizität",
                    },
                    "1200": {"name": "Gas", "description": "Gas-Versorgung"},
                    "1300": {"name": "Erdoel"},
                    "1400": {
                        "name": "Waermeversorgung",
                        "description": "Versorgung mit Fernwärme",
                    },
                    "1600": {"name": "Trinkwasser", "description": "Wasser-Versorgung"},
                    "1800": {"name": "Abwasser", "description": "Abwasser-Entsorgung"},
                    "2000": {
                        "name": "Regenwasser",
                        "description": "Regenwasser Entsorgung",
                    },
                    "2200": {
                        "name": "Abfallentsorgung",
                        "description": "Abfall-Beseitigung",
                    },
                    "2400": {
                        "name": "Ablagerung",
                        "description": "Ablagerungen, Deponien",
                    },
                    "2600": {
                        "name": "Telekommunikation",
                        "description": "Einrichtungen und Anlagen zur Telekommunikation",
                    },
                    "2800": {
                        "name": "ErneuerbareEnergien",
                        "description": "Anlagen, Einrichtungen oder sonstige Maßnahmen zur dezentralen und zentralen Erzeugung, Verteilung oder Speicherung von Strom, Wärme oder Kälte aus erneuerbaren Energien.",
                    },
                    "3000": {
                        "name": "KraftWaermeKopplung",
                        "description": "Anlagen, Einrichtungen oder sonstige Maßnahmen zur dezentralen und zentralen Erzeugung, Verteilung oder Speicherung von Strom, Wärme oder Kälte aus Kraft-Wärme Kopplung.",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstige Zweckbestimmung",
                    },
                },
                "typename": "XP_ZweckbestimmungVerEntsorgung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung2: Annotated[
        Literal[
            "1000",
            "1200",
            "1300",
            "1400",
            "1600",
            "1800",
            "2000",
            "2200",
            "2400",
            "2600",
            "2800",
            "3000",
            "9999",
        ]
        | None,
        Field(
            description='Weitere allgemeine Zweckbestimmung der Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Elektrizitaet",
                        "description": "Versorgung mit Elektrizität",
                    },
                    "1200": {"name": "Gas", "description": "Gas-Versorgung"},
                    "1300": {"name": "Erdoel"},
                    "1400": {
                        "name": "Waermeversorgung",
                        "description": "Versorgung mit Fernwärme",
                    },
                    "1600": {"name": "Trinkwasser", "description": "Wasser-Versorgung"},
                    "1800": {"name": "Abwasser", "description": "Abwasser-Entsorgung"},
                    "2000": {
                        "name": "Regenwasser",
                        "description": "Regenwasser Entsorgung",
                    },
                    "2200": {
                        "name": "Abfallentsorgung",
                        "description": "Abfall-Beseitigung",
                    },
                    "2400": {
                        "name": "Ablagerung",
                        "description": "Ablagerungen, Deponien",
                    },
                    "2600": {
                        "name": "Telekommunikation",
                        "description": "Einrichtungen und Anlagen zur Telekommunikation",
                    },
                    "2800": {
                        "name": "ErneuerbareEnergien",
                        "description": "Anlagen, Einrichtungen oder sonstige Maßnahmen zur dezentralen und zentralen Erzeugung, Verteilung oder Speicherung von Strom, Wärme oder Kälte aus erneuerbaren Energien.",
                    },
                    "3000": {
                        "name": "KraftWaermeKopplung",
                        "description": "Anlagen, Einrichtungen oder sonstige Maßnahmen zur dezentralen und zentralen Erzeugung, Verteilung oder Speicherung von Strom, Wärme oder Kälte aus Kraft-Wärme Kopplung.",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstige Zweckbestimmung",
                    },
                },
                "typename": "XP_ZweckbestimmungVerEntsorgung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung3: Annotated[
        Literal[
            "1000",
            "1200",
            "1300",
            "1400",
            "1600",
            "1800",
            "2000",
            "2200",
            "2400",
            "2600",
            "2800",
            "3000",
            "9999",
        ]
        | None,
        Field(
            description='Weitere allgemeine Zweckbestimmung der Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Elektrizitaet",
                        "description": "Versorgung mit Elektrizität",
                    },
                    "1200": {"name": "Gas", "description": "Gas-Versorgung"},
                    "1300": {"name": "Erdoel"},
                    "1400": {
                        "name": "Waermeversorgung",
                        "description": "Versorgung mit Fernwärme",
                    },
                    "1600": {"name": "Trinkwasser", "description": "Wasser-Versorgung"},
                    "1800": {"name": "Abwasser", "description": "Abwasser-Entsorgung"},
                    "2000": {
                        "name": "Regenwasser",
                        "description": "Regenwasser Entsorgung",
                    },
                    "2200": {
                        "name": "Abfallentsorgung",
                        "description": "Abfall-Beseitigung",
                    },
                    "2400": {
                        "name": "Ablagerung",
                        "description": "Ablagerungen, Deponien",
                    },
                    "2600": {
                        "name": "Telekommunikation",
                        "description": "Einrichtungen und Anlagen zur Telekommunikation",
                    },
                    "2800": {
                        "name": "ErneuerbareEnergien",
                        "description": "Anlagen, Einrichtungen oder sonstige Maßnahmen zur dezentralen und zentralen Erzeugung, Verteilung oder Speicherung von Strom, Wärme oder Kälte aus erneuerbaren Energien.",
                    },
                    "3000": {
                        "name": "KraftWaermeKopplung",
                        "description": "Anlagen, Einrichtungen oder sonstige Maßnahmen zur dezentralen und zentralen Erzeugung, Verteilung oder Speicherung von Strom, Wärme oder Kälte aus Kraft-Wärme Kopplung.",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstige Zweckbestimmung",
                    },
                },
                "typename": "XP_ZweckbestimmungVerEntsorgung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    besondereZweckbestimmung: Annotated[
        list[
            Literal[
                "10000",
                "10001",
                "10002",
                "10003",
                "10004",
                "10005",
                "10006",
                "10007",
                "10008",
                "10009",
                "10010",
                "12000",
                "12001",
                "12002",
                "12003",
                "12004",
                "12005",
                "13000",
                "13001",
                "13002",
                "13003",
                "14000",
                "14001",
                "14002",
                "16000",
                "16001",
                "16002",
                "16003",
                "16004",
                "16005",
                "18000",
                "18001",
                "18002",
                "18003",
                "18004",
                "18005",
                "20000",
                "20001",
                "22000",
                "22001",
                "22002",
                "22003",
                "24000",
                "24001",
                "24002",
                "24003",
                "24004",
                "24005",
                "26000",
                "26001",
                "26002",
                "28000",
                "28001",
                "28002",
                "28003",
                "28004",
                "99990",
            ]
        ]
        | None,
        Field(
            description="Besondere Zweckbestimmungen der Fläche, die die zugehörige allgemeine Zweckbestimmungen detaillieren oder ersetzen.",
            json_schema_extra={
                "typename": "XP_BesondereZweckbestimmungVerEntsorgung",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "10000": {"name": "Hochspannungsleitung"},
                    "10001": {"name": "TrafostationUmspannwerk"},
                    "10002": {"name": "Solarkraftwerk"},
                    "10003": {"name": "Windkraftwerk"},
                    "10004": {"name": "Geothermiekraftwerk"},
                    "10005": {"name": "Elektrizitaetswerk"},
                    "10006": {"name": "Wasserkraftwerk"},
                    "10007": {"name": "BiomasseKraftwerk"},
                    "10008": {"name": "Kabelleitung"},
                    "10009": {"name": "Niederspannungsleitung"},
                    "10010": {"name": "Leitungsmast"},
                    "12000": {"name": "Ferngasleitung"},
                    "12001": {"name": "Gaswerk"},
                    "12002": {"name": "Gasbehaelter"},
                    "12003": {"name": "Gasdruckregler"},
                    "12004": {"name": "Gasstation"},
                    "12005": {"name": "Gasleitung"},
                    "13000": {"name": "Erdoelleitung"},
                    "13001": {"name": "Bohrstelle"},
                    "13002": {"name": "Erdoelpumpstation"},
                    "13003": {"name": "Oeltank"},
                    "14000": {"name": "Blockheizkraftwerk"},
                    "14001": {"name": "Fernwaermeleitung"},
                    "14002": {"name": "Fernheizwerk"},
                    "16000": {"name": "Wasserwerk"},
                    "16001": {"name": "Wasserleitung"},
                    "16002": {"name": "Wasserspeicher"},
                    "16003": {"name": "Brunnen"},
                    "16004": {"name": "Pumpwerk"},
                    "16005": {"name": "Quelle"},
                    "18000": {"name": "Abwasserleitung"},
                    "18001": {"name": "Abwasserrueckhaltebecken"},
                    "18002": {"name": "Abwasserpumpwerk"},
                    "18003": {"name": "Klaeranlage"},
                    "18004": {"name": "AnlageKlaerschlamm"},
                    "18005": {"name": "SonstigeAbwasserBehandlungsanlage"},
                    "20000": {"name": "RegenwasserRueckhaltebecken"},
                    "20001": {"name": "Niederschlagswasserleitung"},
                    "22000": {"name": "Muellumladestation"},
                    "22001": {"name": "Muellbeseitigungsanlage"},
                    "22002": {"name": "Muellsortieranlage"},
                    "22003": {"name": "Recyclinghof"},
                    "24000": {"name": "Erdaushubdeponie"},
                    "24001": {"name": "Bauschuttdeponie"},
                    "24002": {"name": "Hausmuelldeponie"},
                    "24003": {"name": "Sondermuelldeponie"},
                    "24004": {"name": "StillgelegteDeponie"},
                    "24005": {"name": "RekultivierteDeponie"},
                    "26000": {"name": "Fernmeldeanlage"},
                    "26001": {"name": "Mobilfunkstrecke"},
                    "26002": {"name": "Fernmeldekabel"},
                    "28000": {"name": "Windenergie"},
                    "28001": {"name": "Photovoltaik"},
                    "28002": {"name": "Biomasse"},
                    "28003": {"name": "Geothermie"},
                    "28004": {"name": "SonstErneuerbareEnergie"},
                    "99990": {"name": "Produktenleitung"},
                },
            },
        ),
    ] = None
    weitereBesondZweckbestimmung1: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "10006",
            "10007",
            "10008",
            "10009",
            "10010",
            "12000",
            "12001",
            "12002",
            "12003",
            "12004",
            "12005",
            "13000",
            "13001",
            "13002",
            "13003",
            "14000",
            "14001",
            "14002",
            "16000",
            "16001",
            "16002",
            "16003",
            "16004",
            "16005",
            "18000",
            "18001",
            "18002",
            "18003",
            "18004",
            "18005",
            "20000",
            "20001",
            "22000",
            "22001",
            "22002",
            "22003",
            "24000",
            "24001",
            "24002",
            "24003",
            "24004",
            "24005",
            "26000",
            "26001",
            "26002",
            "28000",
            "28001",
            "28002",
            "28003",
            "28004",
            "99990",
        ]
        | None,
        Field(
            description='Weitere besondere Zweckbestimmung der Fläche, die die zugehörige allgemeine Zweckbestimmung detailliert oder ersetzt. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {"name": "Hochspannungsleitung"},
                    "10001": {"name": "TrafostationUmspannwerk"},
                    "10002": {"name": "Solarkraftwerk"},
                    "10003": {"name": "Windkraftwerk"},
                    "10004": {"name": "Geothermiekraftwerk"},
                    "10005": {"name": "Elektrizitaetswerk"},
                    "10006": {"name": "Wasserkraftwerk"},
                    "10007": {"name": "BiomasseKraftwerk"},
                    "10008": {"name": "Kabelleitung"},
                    "10009": {"name": "Niederspannungsleitung"},
                    "10010": {"name": "Leitungsmast"},
                    "12000": {"name": "Ferngasleitung"},
                    "12001": {"name": "Gaswerk"},
                    "12002": {"name": "Gasbehaelter"},
                    "12003": {"name": "Gasdruckregler"},
                    "12004": {"name": "Gasstation"},
                    "12005": {"name": "Gasleitung"},
                    "13000": {"name": "Erdoelleitung"},
                    "13001": {"name": "Bohrstelle"},
                    "13002": {"name": "Erdoelpumpstation"},
                    "13003": {"name": "Oeltank"},
                    "14000": {"name": "Blockheizkraftwerk"},
                    "14001": {"name": "Fernwaermeleitung"},
                    "14002": {"name": "Fernheizwerk"},
                    "16000": {"name": "Wasserwerk"},
                    "16001": {"name": "Wasserleitung"},
                    "16002": {"name": "Wasserspeicher"},
                    "16003": {"name": "Brunnen"},
                    "16004": {"name": "Pumpwerk"},
                    "16005": {"name": "Quelle"},
                    "18000": {"name": "Abwasserleitung"},
                    "18001": {"name": "Abwasserrueckhaltebecken"},
                    "18002": {"name": "Abwasserpumpwerk"},
                    "18003": {"name": "Klaeranlage"},
                    "18004": {"name": "AnlageKlaerschlamm"},
                    "18005": {"name": "SonstigeAbwasserBehandlungsanlage"},
                    "20000": {"name": "RegenwasserRueckhaltebecken"},
                    "20001": {"name": "Niederschlagswasserleitung"},
                    "22000": {"name": "Muellumladestation"},
                    "22001": {"name": "Muellbeseitigungsanlage"},
                    "22002": {"name": "Muellsortieranlage"},
                    "22003": {"name": "Recyclinghof"},
                    "24000": {"name": "Erdaushubdeponie"},
                    "24001": {"name": "Bauschuttdeponie"},
                    "24002": {"name": "Hausmuelldeponie"},
                    "24003": {"name": "Sondermuelldeponie"},
                    "24004": {"name": "StillgelegteDeponie"},
                    "24005": {"name": "RekultivierteDeponie"},
                    "26000": {"name": "Fernmeldeanlage"},
                    "26001": {"name": "Mobilfunkstrecke"},
                    "26002": {"name": "Fernmeldekabel"},
                    "28000": {"name": "Windenergie"},
                    "28001": {"name": "Photovoltaik"},
                    "28002": {"name": "Biomasse"},
                    "28003": {"name": "Geothermie"},
                    "28004": {"name": "SonstErneuerbareEnergie"},
                    "99990": {"name": "Produktenleitung"},
                },
                "typename": "XP_BesondereZweckbestimmungVerEntsorgung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereBesondZweckbestimmung2: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "10006",
            "10007",
            "10008",
            "10009",
            "10010",
            "12000",
            "12001",
            "12002",
            "12003",
            "12004",
            "12005",
            "13000",
            "13001",
            "13002",
            "13003",
            "14000",
            "14001",
            "14002",
            "16000",
            "16001",
            "16002",
            "16003",
            "16004",
            "16005",
            "18000",
            "18001",
            "18002",
            "18003",
            "18004",
            "18005",
            "20000",
            "20001",
            "22000",
            "22001",
            "22002",
            "22003",
            "24000",
            "24001",
            "24002",
            "24003",
            "24004",
            "24005",
            "26000",
            "26001",
            "26002",
            "28000",
            "28001",
            "28002",
            "28003",
            "28004",
            "99990",
        ]
        | None,
        Field(
            description='Weitere besondere Zweckbestimmung der Fläche, die die zugehörige allgemeine Zweckbestimmung detailliert oder ersetzt. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {"name": "Hochspannungsleitung"},
                    "10001": {"name": "TrafostationUmspannwerk"},
                    "10002": {"name": "Solarkraftwerk"},
                    "10003": {"name": "Windkraftwerk"},
                    "10004": {"name": "Geothermiekraftwerk"},
                    "10005": {"name": "Elektrizitaetswerk"},
                    "10006": {"name": "Wasserkraftwerk"},
                    "10007": {"name": "BiomasseKraftwerk"},
                    "10008": {"name": "Kabelleitung"},
                    "10009": {"name": "Niederspannungsleitung"},
                    "10010": {"name": "Leitungsmast"},
                    "12000": {"name": "Ferngasleitung"},
                    "12001": {"name": "Gaswerk"},
                    "12002": {"name": "Gasbehaelter"},
                    "12003": {"name": "Gasdruckregler"},
                    "12004": {"name": "Gasstation"},
                    "12005": {"name": "Gasleitung"},
                    "13000": {"name": "Erdoelleitung"},
                    "13001": {"name": "Bohrstelle"},
                    "13002": {"name": "Erdoelpumpstation"},
                    "13003": {"name": "Oeltank"},
                    "14000": {"name": "Blockheizkraftwerk"},
                    "14001": {"name": "Fernwaermeleitung"},
                    "14002": {"name": "Fernheizwerk"},
                    "16000": {"name": "Wasserwerk"},
                    "16001": {"name": "Wasserleitung"},
                    "16002": {"name": "Wasserspeicher"},
                    "16003": {"name": "Brunnen"},
                    "16004": {"name": "Pumpwerk"},
                    "16005": {"name": "Quelle"},
                    "18000": {"name": "Abwasserleitung"},
                    "18001": {"name": "Abwasserrueckhaltebecken"},
                    "18002": {"name": "Abwasserpumpwerk"},
                    "18003": {"name": "Klaeranlage"},
                    "18004": {"name": "AnlageKlaerschlamm"},
                    "18005": {"name": "SonstigeAbwasserBehandlungsanlage"},
                    "20000": {"name": "RegenwasserRueckhaltebecken"},
                    "20001": {"name": "Niederschlagswasserleitung"},
                    "22000": {"name": "Muellumladestation"},
                    "22001": {"name": "Muellbeseitigungsanlage"},
                    "22002": {"name": "Muellsortieranlage"},
                    "22003": {"name": "Recyclinghof"},
                    "24000": {"name": "Erdaushubdeponie"},
                    "24001": {"name": "Bauschuttdeponie"},
                    "24002": {"name": "Hausmuelldeponie"},
                    "24003": {"name": "Sondermuelldeponie"},
                    "24004": {"name": "StillgelegteDeponie"},
                    "24005": {"name": "RekultivierteDeponie"},
                    "26000": {"name": "Fernmeldeanlage"},
                    "26001": {"name": "Mobilfunkstrecke"},
                    "26002": {"name": "Fernmeldekabel"},
                    "28000": {"name": "Windenergie"},
                    "28001": {"name": "Photovoltaik"},
                    "28002": {"name": "Biomasse"},
                    "28003": {"name": "Geothermie"},
                    "28004": {"name": "SonstErneuerbareEnergie"},
                    "99990": {"name": "Produktenleitung"},
                },
                "typename": "XP_BesondereZweckbestimmungVerEntsorgung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereBesondZweckbestimmung3: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "10006",
            "10007",
            "10008",
            "10009",
            "10010",
            "12000",
            "12001",
            "12002",
            "12003",
            "12004",
            "12005",
            "13000",
            "13001",
            "13002",
            "13003",
            "14000",
            "14001",
            "14002",
            "16000",
            "16001",
            "16002",
            "16003",
            "16004",
            "16005",
            "18000",
            "18001",
            "18002",
            "18003",
            "18004",
            "18005",
            "20000",
            "20001",
            "22000",
            "22001",
            "22002",
            "22003",
            "24000",
            "24001",
            "24002",
            "24003",
            "24004",
            "24005",
            "26000",
            "26001",
            "26002",
            "28000",
            "28001",
            "28002",
            "28003",
            "28004",
            "99990",
        ]
        | None,
        Field(
            description='Weitere besondere Zweckbestimmung der Fläche, die die zugehörige allgemeine Zweckbestimmung detailliert oder ersetzt. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {"name": "Hochspannungsleitung"},
                    "10001": {"name": "TrafostationUmspannwerk"},
                    "10002": {"name": "Solarkraftwerk"},
                    "10003": {"name": "Windkraftwerk"},
                    "10004": {"name": "Geothermiekraftwerk"},
                    "10005": {"name": "Elektrizitaetswerk"},
                    "10006": {"name": "Wasserkraftwerk"},
                    "10007": {"name": "BiomasseKraftwerk"},
                    "10008": {"name": "Kabelleitung"},
                    "10009": {"name": "Niederspannungsleitung"},
                    "10010": {"name": "Leitungsmast"},
                    "12000": {"name": "Ferngasleitung"},
                    "12001": {"name": "Gaswerk"},
                    "12002": {"name": "Gasbehaelter"},
                    "12003": {"name": "Gasdruckregler"},
                    "12004": {"name": "Gasstation"},
                    "12005": {"name": "Gasleitung"},
                    "13000": {"name": "Erdoelleitung"},
                    "13001": {"name": "Bohrstelle"},
                    "13002": {"name": "Erdoelpumpstation"},
                    "13003": {"name": "Oeltank"},
                    "14000": {"name": "Blockheizkraftwerk"},
                    "14001": {"name": "Fernwaermeleitung"},
                    "14002": {"name": "Fernheizwerk"},
                    "16000": {"name": "Wasserwerk"},
                    "16001": {"name": "Wasserleitung"},
                    "16002": {"name": "Wasserspeicher"},
                    "16003": {"name": "Brunnen"},
                    "16004": {"name": "Pumpwerk"},
                    "16005": {"name": "Quelle"},
                    "18000": {"name": "Abwasserleitung"},
                    "18001": {"name": "Abwasserrueckhaltebecken"},
                    "18002": {"name": "Abwasserpumpwerk"},
                    "18003": {"name": "Klaeranlage"},
                    "18004": {"name": "AnlageKlaerschlamm"},
                    "18005": {"name": "SonstigeAbwasserBehandlungsanlage"},
                    "20000": {"name": "RegenwasserRueckhaltebecken"},
                    "20001": {"name": "Niederschlagswasserleitung"},
                    "22000": {"name": "Muellumladestation"},
                    "22001": {"name": "Muellbeseitigungsanlage"},
                    "22002": {"name": "Muellsortieranlage"},
                    "22003": {"name": "Recyclinghof"},
                    "24000": {"name": "Erdaushubdeponie"},
                    "24001": {"name": "Bauschuttdeponie"},
                    "24002": {"name": "Hausmuelldeponie"},
                    "24003": {"name": "Sondermuelldeponie"},
                    "24004": {"name": "StillgelegteDeponie"},
                    "24005": {"name": "RekultivierteDeponie"},
                    "26000": {"name": "Fernmeldeanlage"},
                    "26001": {"name": "Mobilfunkstrecke"},
                    "26002": {"name": "Fernmeldekabel"},
                    "28000": {"name": "Windenergie"},
                    "28001": {"name": "Photovoltaik"},
                    "28002": {"name": "Biomasse"},
                    "28003": {"name": "Geothermie"},
                    "28004": {"name": "SonstErneuerbareEnergie"},
                    "99990": {"name": "Produktenleitung"},
                },
                "typename": "XP_BesondereZweckbestimmungVerEntsorgung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteZweckbestimmung: Annotated[
        list[AnyUrl] | None,
        Field(
            description="Über eine CodeList definierte zusätzliche Zweckbestimmungen.",
            json_schema_extra={
                "typename": "BP_DetailZweckbestVerEntsorgung",
                "stereotype": "Codelist",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung1: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestVerEntsorgung",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung2: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestVerEntsorgung",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung3: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestVerEntsorgung",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    textlicheErgaenzung: Annotated[
        str | None,
        Field(
            description="Zusätzliche textliche Beschreibung der Ver- bzw. Entsorgungseinrichtung.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    zugunstenVon: Annotated[
        str | None,
        Field(
            description="Angabe des Begünstigen einer Ausweisung.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPVeraenderungssperre(BPUeberlagerungsobjekt):
    """Ausweisung einer Veränderungssperre, die nicht den gesamten Geltungsbereich des Plans umfasst. Bei Verwendung dieser Klasse muss das Attribut 'veraenderungssperre" des zugehörigen Plans (Klasse BP_Plan) auf "false" gesetzt werden."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gueltigkeitsDatum: Annotated[
        date_aliased,
        Field(
            description="Datum bis zu dem die Veränderungssperre bestehen bleibt.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "1",
            },
        ),
    ]
    verlaengerung: Annotated[
        Literal["1000", "2000", "3000"],
        Field(
            description="Gibt an, ob die Veränderungssperre bereits ein- oder zweimal verlängert wurde.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Keine"},
                    "2000": {"name": "ErsteVerlaengerung"},
                    "3000": {"name": "ZweiteVerlaengerung"},
                },
                "typename": "XP_VerlaengerungVeraenderungssperre",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]
    refBeschluss: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf das Dokument mit dem zug. Beschluss.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPVerkehrsflaecheBesondererZweckbestimmung(BPFlaechenschlussobjekt):
    """Verkehrsfläche besonderer Zweckbestimmung (§9 Abs. 1 Nr. 11 und Abs. 6 BauGB)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    MaxZahlWohnungen: Annotated[
        int | None,
        Field(
            description="Höchstzulässige Zahl der Wohnungen in Wohngebäuden",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Fmin: Annotated[
        definitions.Area | None,
        Field(
            description="Mindestmaß für die Größe (Fläche) eines Baugrundstücks.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Fmax: Annotated[
        definitions.Area | None,
        Field(
            description="Höchstmaß für die Größe (Fläche) eines Baugrundstücks.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Bmin: Annotated[
        definitions.Length | None,
        Field(
            description="Minimale Breite von Baugrundstücken",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Bmax: Annotated[
        definitions.Length | None,
        Field(
            description="Maximale Breite von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Tmin: Annotated[
        definitions.Length | None,
        Field(
            description="Minimale Tiefe von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Tmax: Annotated[
        definitions.Length | None,
        Field(
            description="Maximale Tiefe von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    GFZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Geschossflächenzahl .",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl bei einer Bereichsangabe. Das Attribut GFZmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZ_Ausn: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl als Ausnahme.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFmin: Annotated[
        definitions.Area | None,
        Field(
            description="Minimal zulässige Geschossfläche",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GFmax: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Geschossfläche bei einer Bereichsabgabe. Das Attribut GFmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GF: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Geschossfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GF_Ausn: Annotated[
        definitions.Area | None,
        Field(
            description="Ausnahmsweise maximal zulässige Geschossfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    BMZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Baumassenzahl",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Baumassenzahl bei einer Bereichsangabe. Das Attribut BMZmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Baumassenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZ_Ausn: Annotated[
        float | None,
        Field(
            description="Ausnahmsweise maximal zulässige Baumassenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMmin: Annotated[
        definitions.Volume | None,
        Field(
            description="Minimal zulässinge Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BMmax: Annotated[
        definitions.Volume | None,
        Field(
            description="Maximal zulässinge Baumasse bei einer Bereichsangabe. Das Attribut BMmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BM: Annotated[
        definitions.Volume | None,
        Field(
            description="Maximal zulässige Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BM_Ausn: Annotated[
        definitions.Volume | None,
        Field(
            description="Ausnahmsweise maximal zulässige Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    GRZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Grundflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Grundflächenzahl bei einer Bereichsangabe.  Das Attribut GRZmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Grundflächenzahl",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZ_Ausn: Annotated[
        float | None,
        Field(
            description="Ausnahmsweise maximal zulässige Grundflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRmin: Annotated[
        definitions.Area | None,
        Field(
            description="Minimal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GRmax: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Grundfläche bei einer Bereichsangabe. Das Attribut GRmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GR: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GR_Ausn: Annotated[
        definitions.Area | None,
        Field(
            description="Ausnahmsweise maximal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Zmin: Annotated[
        int | None,
        Field(
            description="Minimal zulässige Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Zmax: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der oberirdischen Vollgeschosse bei einer Bereichsangabe. Das Attribut Zmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Zzwingend: Annotated[
        int | None,
        Field(
            description="Zwingend vorgeschriebene Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z: Annotated[
        int | None,
        Field(
            description="Maximalzahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Ausn: Annotated[
        int | None,
        Field(
            description="Ausnahmsweise maximal zulässige Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Staffel: Annotated[
        int | None,
        Field(
            description="Maximalzahl von oberirdischen zurückgesetzten Vollgeschossen als Staffelgeschoss..",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Dach: Annotated[
        int | None,
        Field(
            description="Maximalzahl der zusätzlich erlaubten Dachgeschosse, die gleichzeitig Vollgeschosse sind.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUmin: Annotated[
        int | None,
        Field(
            description="Minimal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUmax: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der unterirdischen Geschosse bei einer Bereichsangabe. Das Attribut ZUmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUzwingend: Annotated[
        int | None,
        Field(
            description="Zwingend vorgeschriebene Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZU: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZU_Ausn: Annotated[
        int | None,
        Field(
            description="Ausnahmsweise maximal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    zweckbestimmung: Annotated[
        Literal[
            "1000",
            "1100",
            "1200",
            "1300",
            "1400",
            "1500",
            "1550",
            "1580",
            "1600",
            "1700",
            "1800",
            "2000",
            "2100",
            "2200",
            "2300",
            "2400",
            "9999",
        ]
        | None,
        Field(
            description="Zweckbestimmung der Fläche",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Parkierungsflaeche",
                        "description": "Fläche für das Parken von Fahrzeugen",
                    },
                    "1100": {
                        "name": "Fussgaengerbereich",
                        "description": "Fußgängerbereich",
                    },
                    "1200": {
                        "name": "VerkehrsberuhigterBereich",
                        "description": "Verkehrsberuhigte Zone",
                    },
                    "1300": {"name": "RadFussweg", "description": "Rad- und Fußweg"},
                    "1400": {"name": "Radweg", "description": "Reiner Radweg"},
                    "1500": {"name": "Fussweg", "description": "Reiner Fußweg"},
                    "1550": {"name": "Wanderweg", "description": "Wanderweg"},
                    "1580": {"name": "Wirtschaftsweg"},
                    "1600": {"name": "FahrradAbstellplatz"},
                    "1700": {
                        "name": "UeberfuehrenderVerkehrsweg",
                        "description": "Brückenbereich",
                    },
                    "1800": {"name": "UnterfuehrenderVerkehrsweg"},
                    "2000": {"name": "P_RAnlage"},
                    "2100": {"name": "Platz"},
                    "2200": {"name": "Anschlussflaeche"},
                    "2300": {"name": "LandwirtschaftlicherVerkehr"},
                    "2400": {"name": "Verkehrsgruen"},
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstige Zweckbestimmung",
                    },
                },
                "typename": "BP_ZweckbestimmungStrassenverkehr",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteZweckbestimmung: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definierte  Zweckbestimmung der Fläche.",
            json_schema_extra={
                "typename": "BP_DetailZweckbestStrassenverkehr",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    nutzungsform: Annotated[
        Literal["1000", "2000"] | None,
        Field(
            description="Nutzungsform der Fläche.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Privat", "description": "Private Nutzung"},
                    "2000": {
                        "name": "Oeffentlich",
                        "description": "Öffentliche Nutzung",
                    },
                },
                "typename": "XP_Nutzungsform",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    begrenzungslinie: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "BP_StrassenbegrenzungsLinie",
                "stereotype": "Association",
                "multiplicity": "0..*",
            }
        ),
    ] = None


class BPWaldFlaeche(BPFlaechenschlussobjekt):
    """Festsetzung von Waldflächen  (§9, Abs. 1, Nr. 18b BauGB)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    zweckbestimmung: Annotated[
        list[Literal["1000", "1200", "1400", "1600", "1800", "9999"]] | None,
        Field(
            description="Zweckbestimmungen der Waldfläche",
            json_schema_extra={
                "typename": "XP_ZweckbestimmungWald",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Naturwald"},
                    "1200": {"name": "Nutzwald"},
                    "1400": {"name": "Erholungswald", "description": "Erholungswald"},
                    "1600": {"name": "Schutzwald", "description": "Schutzwald"},
                    "1800": {"name": "FlaecheForstwirtschaft"},
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
            },
        ),
    ] = None
    weitereZweckbestimmung1: Annotated[
        Literal["1000", "1200", "1400", "1600", "1800", "9999"] | None,
        Field(
            description='Weitere Zweckbestimmung der Waldfläche Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Naturwald"},
                    "1200": {"name": "Nutzwald"},
                    "1400": {"name": "Erholungswald", "description": "Erholungswald"},
                    "1600": {"name": "Schutzwald", "description": "Schutzwald"},
                    "1800": {"name": "FlaecheForstwirtschaft"},
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungWald",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung2: Annotated[
        Literal["1000", "1200", "1400", "1600", "1800", "9999"] | None,
        Field(
            description='Weitere Zweckbestimmung der Waldfläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Naturwald"},
                    "1200": {"name": "Nutzwald"},
                    "1400": {"name": "Erholungswald", "description": "Erholungswald"},
                    "1600": {"name": "Schutzwald", "description": "Schutzwald"},
                    "1800": {"name": "FlaecheForstwirtschaft"},
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungWald",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteZweckbestimmung: Annotated[
        list[AnyUrl] | None,
        Field(
            description="Über eine CodeList definierte zusätzliche Zweckbestimmung.",
            json_schema_extra={
                "typename": "BP_DetailZweckbestWaldFlaeche",
                "stereotype": "Codelist",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung1: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestWaldFlaeche",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung2: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestWaldFlaeche",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPWasserwirtschaftsFlaeche(BPFlaechenobjekt):
    """Flächen für die Wasserwirtschaft, den Hochwasserschutz  und die Regelungen des Wasserabflusses (§9 Abs. 1 Nr. 16 und Abs. 6a BauGB)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    zweckbestimmung: Annotated[
        Literal["1000", "1100", "1200", "1300", "9999"] | None,
        Field(
            description="Zweckbestimmung der Fläche.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "HochwasserRueckhaltebecken",
                        "description": "Hochwasser-Rückhaltebecken",
                    },
                    "1100": {
                        "name": "Ueberschwemmgebiet",
                        "description": "Überschwemmungs-gefährdetes Gebiet",
                    },
                    "1200": {"name": "Versickerungsflaeche"},
                    "1300": {"name": "Entwaesserungsgraben"},
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstige Zweckbestimmung",
                    },
                },
                "typename": "XP_ZweckbestimmungWasserwirtschaft",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteZweckbestimmung: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definierte  Zweckbestimmung der Fläche.",
            json_schema_extra={
                "typename": "BP_DetailZweckbestWasserwirtschaft",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPWegerecht(BPGeometrieobjekt):
    """Festsetzung von Flächen, die mit Geh-, Fahr-, und Leitungsrechten zugunsten der Allgemeinheit, eines Erschließungsträgers, oder eines beschränkten Personenkreises belastet sind  (§ 9 Abs. 1 Nr. 21 und Abs. 6 BauGB)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    typ: Annotated[
        Literal["1000", "2000", "3000", "4000", "4100", "4200", "5000"] | None,
        Field(
            description="Typ des Wegerechts",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Gehrecht", "description": "Gehrecht"},
                    "2000": {"name": "Fahrrecht", "description": "Fahrrecht"},
                    "3000": {
                        "name": "GehFahrrecht",
                        "description": "Geh- und Fahrrecht",
                    },
                    "4000": {"name": "Leitungsrecht"},
                    "4100": {
                        "name": "GehLeitungsrecht",
                        "description": "Geh- und Leitungsrecht",
                    },
                    "4200": {
                        "name": "FahrLeitungsrecht",
                        "description": "Fahr- und Leitungsrecht",
                    },
                    "5000": {
                        "name": "GehFahrLeitungsrecht",
                        "description": "Geh-, Fahr- und Leitungsrecht",
                    },
                },
                "typename": "BP_WegerechtTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    zugunstenVon: Annotated[
        str | None,
        Field(
            description="Inhaber der Rechte.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    thema: Annotated[
        str | None,
        Field(
            description="Beschreibung des Rechtes.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    breite: Annotated[
        definitions.Length | None,
        Field(
            description="Breite des Wegerechts bei linienförmiger Ausweisung der Geometrie.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None


class FPFlaechenobjekt(FPObjekt):
    """Basisklasse für alle Objekte eines Flächennutzungsplans mit flächenhaftem Raumbezug (eine Einzelfläche oder eine Menge von Flächen, die sich nicht überlappen dürfen).  Die von FP_Flaechenobjekt abgeleiteten Fachobjekte können sowohl als Flächenschlussobjekte als auch als Überlagerungsobjekte auftreten."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Polygon | definitions.MultiPolygon,
        Field(
            json_schema_extra={
                "typename": "XP_Flaechengeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            }
        ),
    ]
    flaechenschluss: Annotated[
        bool,
        Field(
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "1",
            }
        ),
    ]


class FPFlaechenschlussobjekt(FPFlaechenobjekt):
    """Basisklasse für alle Objekte eines Flächennutzungsplans mit flächenhaftem Raumbezug, die immer Flächenschlussobjekte sind."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class FPGeometrieobjekt(FPObjekt):
    """Basisklasse für alle Objekte eines Flächennutzungsplans mit variablem Raumbezug. Ein konkretes Objekt muss entweder punktförmigen, linienförmigen oder flächenhaften Raumbezug haben, gemischte Geometrie ist nicht zugelassen."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Point
        | definitions.MultiPoint
        | definitions.Line
        | definitions.MultiLine
        | definitions.Polygon
        | definitions.MultiPolygon,
        Field(
            json_schema_extra={
                "typename": "XP_VariableGeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            }
        ),
    ]
    flaechenschluss: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            }
        ),
    ] = False


class FPGewaesser(FPGeometrieobjekt):
    """Darstellung von Wasserflächen nach §5, Abs. 2, Nr. 7 BauGB."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    zweckbestimmung: Annotated[
        Literal["1000", "1100", "1200", "9999"] | None,
        Field(
            description="Zweckbestimmung des Gewässers.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Hafen"},
                    "1100": {"name": "Wasserflaeche"},
                    "1200": {"name": "Fliessgewaesser"},
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungGewaesser",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteZweckbestimmung: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definierte zusätzliche Zweckbestimmung des Objektes.",
            json_schema_extra={
                "typename": "FP_DetailZweckbestGewaesser",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class FPGruen(FPGeometrieobjekt):
    """Darstellung einer Grünfläche nach §5, Abs. 2, Nr. 5 BauGB,"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    zweckbestimmung: Annotated[
        list[
            Literal[
                "1000",
                "1200",
                "1400",
                "1600",
                "1800",
                "2000",
                "2200",
                "2400",
                "2600",
                "9999",
            ]
        ]
        | None,
        Field(
            description="Allgemeine Zweckbestimmungen der Grünfläche.",
            json_schema_extra={
                "typename": "XP_ZweckbestimmungGruen",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {
                        "name": "Parkanlage",
                        "description": "Parkanlage; auch: Erholungsgrün, Grünanlage, Naherholung.",
                    },
                    "1200": {
                        "name": "Dauerkleingaerten",
                        "description": "Dauerkleingarten; auch: Gartenfläche, Hofgärten, Gartenland",
                    },
                    "1400": {"name": "Sportplatz", "description": "Sportplatz"},
                    "1600": {"name": "Spielplatz", "description": "Spielplatz"},
                    "1800": {"name": "Zeltplatz", "description": "Zeltplatz"},
                    "2000": {
                        "name": "Badeplatz",
                        "description": "Badeplatz, auch Schwimmbad, Liegewiese",
                    },
                    "2200": {
                        "name": "FreizeitErholung",
                        "description": "Anlage für Freizeit und Erholung.",
                    },
                    "2400": {
                        "name": "SpezGruenflaeche",
                        "description": "Spezielle Grünfläche",
                    },
                    "2600": {"name": "Friedhof", "description": "Friedhof"},
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
            },
        ),
    ] = None
    weitereZweckbestimmung1: Annotated[
        Literal[
            "1000",
            "1200",
            "1400",
            "1600",
            "1800",
            "2000",
            "2200",
            "2400",
            "2600",
            "9999",
        ]
        | None,
        Field(
            description='Weitere allgemeine Zweckbestimmung der Grünfläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Parkanlage",
                        "description": "Parkanlage; auch: Erholungsgrün, Grünanlage, Naherholung.",
                    },
                    "1200": {
                        "name": "Dauerkleingaerten",
                        "description": "Dauerkleingarten; auch: Gartenfläche, Hofgärten, Gartenland",
                    },
                    "1400": {"name": "Sportplatz", "description": "Sportplatz"},
                    "1600": {"name": "Spielplatz", "description": "Spielplatz"},
                    "1800": {"name": "Zeltplatz", "description": "Zeltplatz"},
                    "2000": {
                        "name": "Badeplatz",
                        "description": "Badeplatz, auch Schwimmbad, Liegewiese",
                    },
                    "2200": {
                        "name": "FreizeitErholung",
                        "description": "Anlage für Freizeit und Erholung.",
                    },
                    "2400": {
                        "name": "SpezGruenflaeche",
                        "description": "Spezielle Grünfläche",
                    },
                    "2600": {"name": "Friedhof", "description": "Friedhof"},
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungGruen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung2: Annotated[
        Literal[
            "1000",
            "1200",
            "1400",
            "1600",
            "1800",
            "2000",
            "2200",
            "2400",
            "2600",
            "9999",
        ]
        | None,
        Field(
            description='Weitere allgemeine Zweckbestimmung der Grünfläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Parkanlage",
                        "description": "Parkanlage; auch: Erholungsgrün, Grünanlage, Naherholung.",
                    },
                    "1200": {
                        "name": "Dauerkleingaerten",
                        "description": "Dauerkleingarten; auch: Gartenfläche, Hofgärten, Gartenland",
                    },
                    "1400": {"name": "Sportplatz", "description": "Sportplatz"},
                    "1600": {"name": "Spielplatz", "description": "Spielplatz"},
                    "1800": {"name": "Zeltplatz", "description": "Zeltplatz"},
                    "2000": {
                        "name": "Badeplatz",
                        "description": "Badeplatz, auch Schwimmbad, Liegewiese",
                    },
                    "2200": {
                        "name": "FreizeitErholung",
                        "description": "Anlage für Freizeit und Erholung.",
                    },
                    "2400": {
                        "name": "SpezGruenflaeche",
                        "description": "Spezielle Grünfläche",
                    },
                    "2600": {"name": "Friedhof", "description": "Friedhof"},
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungGruen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung3: Annotated[
        Literal[
            "1000",
            "1200",
            "1400",
            "1600",
            "1800",
            "2000",
            "2200",
            "2400",
            "2600",
            "9999",
        ]
        | None,
        Field(
            description='Weitere allgemeine Zweckbestimmung der Grünfläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Parkanlage",
                        "description": "Parkanlage; auch: Erholungsgrün, Grünanlage, Naherholung.",
                    },
                    "1200": {
                        "name": "Dauerkleingaerten",
                        "description": "Dauerkleingarten; auch: Gartenfläche, Hofgärten, Gartenland",
                    },
                    "1400": {"name": "Sportplatz", "description": "Sportplatz"},
                    "1600": {"name": "Spielplatz", "description": "Spielplatz"},
                    "1800": {"name": "Zeltplatz", "description": "Zeltplatz"},
                    "2000": {
                        "name": "Badeplatz",
                        "description": "Badeplatz, auch Schwimmbad, Liegewiese",
                    },
                    "2200": {
                        "name": "FreizeitErholung",
                        "description": "Anlage für Freizeit und Erholung.",
                    },
                    "2400": {
                        "name": "SpezGruenflaeche",
                        "description": "Spezielle Grünfläche",
                    },
                    "2600": {"name": "Friedhof", "description": "Friedhof"},
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungGruen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung4: Annotated[
        Literal[
            "1000",
            "1200",
            "1400",
            "1600",
            "1800",
            "2000",
            "2200",
            "2400",
            "2600",
            "9999",
        ]
        | None,
        Field(
            description='Weitere allgemeine Zweckbestimmung der Grünfläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Parkanlage",
                        "description": "Parkanlage; auch: Erholungsgrün, Grünanlage, Naherholung.",
                    },
                    "1200": {
                        "name": "Dauerkleingaerten",
                        "description": "Dauerkleingarten; auch: Gartenfläche, Hofgärten, Gartenland",
                    },
                    "1400": {"name": "Sportplatz", "description": "Sportplatz"},
                    "1600": {"name": "Spielplatz", "description": "Spielplatz"},
                    "1800": {"name": "Zeltplatz", "description": "Zeltplatz"},
                    "2000": {
                        "name": "Badeplatz",
                        "description": "Badeplatz, auch Schwimmbad, Liegewiese",
                    },
                    "2200": {
                        "name": "FreizeitErholung",
                        "description": "Anlage für Freizeit und Erholung.",
                    },
                    "2400": {
                        "name": "SpezGruenflaeche",
                        "description": "Spezielle Grünfläche",
                    },
                    "2600": {"name": "Friedhof", "description": "Friedhof"},
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungGruen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung5: Annotated[
        Literal[
            "1000",
            "1200",
            "1400",
            "1600",
            "1800",
            "2000",
            "2200",
            "2400",
            "2600",
            "9999",
        ]
        | None,
        Field(
            description='Weitere allgemeine Zweckbestimmung der Grünfläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Parkanlage",
                        "description": "Parkanlage; auch: Erholungsgrün, Grünanlage, Naherholung.",
                    },
                    "1200": {
                        "name": "Dauerkleingaerten",
                        "description": "Dauerkleingarten; auch: Gartenfläche, Hofgärten, Gartenland",
                    },
                    "1400": {"name": "Sportplatz", "description": "Sportplatz"},
                    "1600": {"name": "Spielplatz", "description": "Spielplatz"},
                    "1800": {"name": "Zeltplatz", "description": "Zeltplatz"},
                    "2000": {
                        "name": "Badeplatz",
                        "description": "Badeplatz, auch Schwimmbad, Liegewiese",
                    },
                    "2200": {
                        "name": "FreizeitErholung",
                        "description": "Anlage für Freizeit und Erholung.",
                    },
                    "2400": {
                        "name": "SpezGruenflaeche",
                        "description": "Spezielle Grünfläche",
                    },
                    "2600": {"name": "Friedhof", "description": "Friedhof"},
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungGruen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    besondereZweckbestimmung: Annotated[
        list[
            Literal[
                "10000",
                "10001",
                "10002",
                "10003",
                "12000",
                "14000",
                "14001",
                "14002",
                "14003",
                "14004",
                "14005",
                "14006",
                "14007",
                "16000",
                "16001",
                "18000",
                "22000",
                "22001",
                "24000",
                "24001",
                "24002",
                "24003",
                "24004",
                "24005",
                "24006",
                "99990",
            ]
        ]
        | None,
        Field(
            description="Besondere Zweckbestimmungen der Grünfläche, die die zugehörige allgemeinen Zweckbestimmungen detaillieren oder ersetzen.",
            json_schema_extra={
                "typename": "XP_BesondereZweckbestimmungGruen",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "10000": {"name": "ParkanlageHistorisch"},
                    "10001": {"name": "ParkanlageNaturnah"},
                    "10002": {"name": "ParkanlageWaldcharakter"},
                    "10003": {"name": "NaturnaheUferParkanlage"},
                    "12000": {"name": "ErholungsGaerten"},
                    "14000": {"name": "Reitsportanlage"},
                    "14001": {"name": "Hundesportanlage"},
                    "14002": {"name": "Wassersportanlage"},
                    "14003": {"name": "Schiessstand"},
                    "14004": {"name": "Golfplatz"},
                    "14005": {"name": "Skisport"},
                    "14006": {"name": "Tennisanlage"},
                    "14007": {"name": "SonstigerSportplatz"},
                    "16000": {"name": "Bolzplatz"},
                    "16001": {"name": "Abenteuerspielplatz"},
                    "18000": {"name": "Campingplatz"},
                    "22000": {"name": "Kleintierhaltung"},
                    "22001": {"name": "Festplatz"},
                    "24000": {"name": "StrassenbegleitGruen"},
                    "24001": {"name": "BoeschungsFlaeche"},
                    "24002": {"name": "FeldWaldWiese"},
                    "24003": {"name": "Uferschutzstreifen"},
                    "24004": {"name": "Abschirmgruen"},
                    "24005": {"name": "UmweltbildungsparkSchaugatter"},
                    "24006": {"name": "RuhenderVerkehr"},
                    "99990": {"name": "Gaertnerei"},
                },
            },
        ),
    ] = None
    weitereBesondZweckbestimmung1: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "12000",
            "14000",
            "14001",
            "14002",
            "14003",
            "14004",
            "14005",
            "14006",
            "14007",
            "16000",
            "16001",
            "18000",
            "22000",
            "22001",
            "24000",
            "24001",
            "24002",
            "24003",
            "24004",
            "24005",
            "24006",
            "99990",
        ]
        | None,
        Field(
            description='Weitere  besondere Zweckbestimmung der Grünfläche, die die zugehörige allgemeine Zweckbestimmung detailliert oder ersetzt. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {"name": "ParkanlageHistorisch"},
                    "10001": {"name": "ParkanlageNaturnah"},
                    "10002": {"name": "ParkanlageWaldcharakter"},
                    "10003": {"name": "NaturnaheUferParkanlage"},
                    "12000": {"name": "ErholungsGaerten"},
                    "14000": {"name": "Reitsportanlage"},
                    "14001": {"name": "Hundesportanlage"},
                    "14002": {"name": "Wassersportanlage"},
                    "14003": {"name": "Schiessstand"},
                    "14004": {"name": "Golfplatz"},
                    "14005": {"name": "Skisport"},
                    "14006": {"name": "Tennisanlage"},
                    "14007": {"name": "SonstigerSportplatz"},
                    "16000": {"name": "Bolzplatz"},
                    "16001": {"name": "Abenteuerspielplatz"},
                    "18000": {"name": "Campingplatz"},
                    "22000": {"name": "Kleintierhaltung"},
                    "22001": {"name": "Festplatz"},
                    "24000": {"name": "StrassenbegleitGruen"},
                    "24001": {"name": "BoeschungsFlaeche"},
                    "24002": {"name": "FeldWaldWiese"},
                    "24003": {"name": "Uferschutzstreifen"},
                    "24004": {"name": "Abschirmgruen"},
                    "24005": {"name": "UmweltbildungsparkSchaugatter"},
                    "24006": {"name": "RuhenderVerkehr"},
                    "99990": {"name": "Gaertnerei"},
                },
                "typename": "XP_BesondereZweckbestimmungGruen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereBesondZweckbestimmung2: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "12000",
            "14000",
            "14001",
            "14002",
            "14003",
            "14004",
            "14005",
            "14006",
            "14007",
            "16000",
            "16001",
            "18000",
            "22000",
            "22001",
            "24000",
            "24001",
            "24002",
            "24003",
            "24004",
            "24005",
            "24006",
            "99990",
        ]
        | None,
        Field(
            description='Weitere  besondere Zweckbestimmung der Grünfläche, die die zugehörige allgemeine Zweckbestimmung detailliert oder ersetzt. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {"name": "ParkanlageHistorisch"},
                    "10001": {"name": "ParkanlageNaturnah"},
                    "10002": {"name": "ParkanlageWaldcharakter"},
                    "10003": {"name": "NaturnaheUferParkanlage"},
                    "12000": {"name": "ErholungsGaerten"},
                    "14000": {"name": "Reitsportanlage"},
                    "14001": {"name": "Hundesportanlage"},
                    "14002": {"name": "Wassersportanlage"},
                    "14003": {"name": "Schiessstand"},
                    "14004": {"name": "Golfplatz"},
                    "14005": {"name": "Skisport"},
                    "14006": {"name": "Tennisanlage"},
                    "14007": {"name": "SonstigerSportplatz"},
                    "16000": {"name": "Bolzplatz"},
                    "16001": {"name": "Abenteuerspielplatz"},
                    "18000": {"name": "Campingplatz"},
                    "22000": {"name": "Kleintierhaltung"},
                    "22001": {"name": "Festplatz"},
                    "24000": {"name": "StrassenbegleitGruen"},
                    "24001": {"name": "BoeschungsFlaeche"},
                    "24002": {"name": "FeldWaldWiese"},
                    "24003": {"name": "Uferschutzstreifen"},
                    "24004": {"name": "Abschirmgruen"},
                    "24005": {"name": "UmweltbildungsparkSchaugatter"},
                    "24006": {"name": "RuhenderVerkehr"},
                    "99990": {"name": "Gaertnerei"},
                },
                "typename": "XP_BesondereZweckbestimmungGruen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereBesondZweckbestimmung3: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "12000",
            "14000",
            "14001",
            "14002",
            "14003",
            "14004",
            "14005",
            "14006",
            "14007",
            "16000",
            "16001",
            "18000",
            "22000",
            "22001",
            "24000",
            "24001",
            "24002",
            "24003",
            "24004",
            "24005",
            "24006",
            "99990",
        ]
        | None,
        Field(
            description='Weitere  besondere Zweckbestimmung der Grünfläche, die die zugehörige allgemeine Zweckbestimmung detailliert oder ersetzt. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {"name": "ParkanlageHistorisch"},
                    "10001": {"name": "ParkanlageNaturnah"},
                    "10002": {"name": "ParkanlageWaldcharakter"},
                    "10003": {"name": "NaturnaheUferParkanlage"},
                    "12000": {"name": "ErholungsGaerten"},
                    "14000": {"name": "Reitsportanlage"},
                    "14001": {"name": "Hundesportanlage"},
                    "14002": {"name": "Wassersportanlage"},
                    "14003": {"name": "Schiessstand"},
                    "14004": {"name": "Golfplatz"},
                    "14005": {"name": "Skisport"},
                    "14006": {"name": "Tennisanlage"},
                    "14007": {"name": "SonstigerSportplatz"},
                    "16000": {"name": "Bolzplatz"},
                    "16001": {"name": "Abenteuerspielplatz"},
                    "18000": {"name": "Campingplatz"},
                    "22000": {"name": "Kleintierhaltung"},
                    "22001": {"name": "Festplatz"},
                    "24000": {"name": "StrassenbegleitGruen"},
                    "24001": {"name": "BoeschungsFlaeche"},
                    "24002": {"name": "FeldWaldWiese"},
                    "24003": {"name": "Uferschutzstreifen"},
                    "24004": {"name": "Abschirmgruen"},
                    "24005": {"name": "UmweltbildungsparkSchaugatter"},
                    "24006": {"name": "RuhenderVerkehr"},
                    "99990": {"name": "Gaertnerei"},
                },
                "typename": "XP_BesondereZweckbestimmungGruen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereBesondZweckbestimmung4: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "12000",
            "14000",
            "14001",
            "14002",
            "14003",
            "14004",
            "14005",
            "14006",
            "14007",
            "16000",
            "16001",
            "18000",
            "22000",
            "22001",
            "24000",
            "24001",
            "24002",
            "24003",
            "24004",
            "24005",
            "24006",
            "99990",
        ]
        | None,
        Field(
            description='Weitere  besondere Zweckbestimmung der Grünfläche, die die zugehörige allgemeine Zweckbestimmung detailliert oder ersetzt. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {"name": "ParkanlageHistorisch"},
                    "10001": {"name": "ParkanlageNaturnah"},
                    "10002": {"name": "ParkanlageWaldcharakter"},
                    "10003": {"name": "NaturnaheUferParkanlage"},
                    "12000": {"name": "ErholungsGaerten"},
                    "14000": {"name": "Reitsportanlage"},
                    "14001": {"name": "Hundesportanlage"},
                    "14002": {"name": "Wassersportanlage"},
                    "14003": {"name": "Schiessstand"},
                    "14004": {"name": "Golfplatz"},
                    "14005": {"name": "Skisport"},
                    "14006": {"name": "Tennisanlage"},
                    "14007": {"name": "SonstigerSportplatz"},
                    "16000": {"name": "Bolzplatz"},
                    "16001": {"name": "Abenteuerspielplatz"},
                    "18000": {"name": "Campingplatz"},
                    "22000": {"name": "Kleintierhaltung"},
                    "22001": {"name": "Festplatz"},
                    "24000": {"name": "StrassenbegleitGruen"},
                    "24001": {"name": "BoeschungsFlaeche"},
                    "24002": {"name": "FeldWaldWiese"},
                    "24003": {"name": "Uferschutzstreifen"},
                    "24004": {"name": "Abschirmgruen"},
                    "24005": {"name": "UmweltbildungsparkSchaugatter"},
                    "24006": {"name": "RuhenderVerkehr"},
                    "99990": {"name": "Gaertnerei"},
                },
                "typename": "XP_BesondereZweckbestimmungGruen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereBesondZweckbestimmung5: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "12000",
            "14000",
            "14001",
            "14002",
            "14003",
            "14004",
            "14005",
            "14006",
            "14007",
            "16000",
            "16001",
            "18000",
            "22000",
            "22001",
            "24000",
            "24001",
            "24002",
            "24003",
            "24004",
            "24005",
            "24006",
            "99990",
        ]
        | None,
        Field(
            description='Weitere  besondere Zweckbestimmung der Grünfläche, die die zugehörige allgemeine Zweckbestimmung detailliert oder ersetzt. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {"name": "ParkanlageHistorisch"},
                    "10001": {"name": "ParkanlageNaturnah"},
                    "10002": {"name": "ParkanlageWaldcharakter"},
                    "10003": {"name": "NaturnaheUferParkanlage"},
                    "12000": {"name": "ErholungsGaerten"},
                    "14000": {"name": "Reitsportanlage"},
                    "14001": {"name": "Hundesportanlage"},
                    "14002": {"name": "Wassersportanlage"},
                    "14003": {"name": "Schiessstand"},
                    "14004": {"name": "Golfplatz"},
                    "14005": {"name": "Skisport"},
                    "14006": {"name": "Tennisanlage"},
                    "14007": {"name": "SonstigerSportplatz"},
                    "16000": {"name": "Bolzplatz"},
                    "16001": {"name": "Abenteuerspielplatz"},
                    "18000": {"name": "Campingplatz"},
                    "22000": {"name": "Kleintierhaltung"},
                    "22001": {"name": "Festplatz"},
                    "24000": {"name": "StrassenbegleitGruen"},
                    "24001": {"name": "BoeschungsFlaeche"},
                    "24002": {"name": "FeldWaldWiese"},
                    "24003": {"name": "Uferschutzstreifen"},
                    "24004": {"name": "Abschirmgruen"},
                    "24005": {"name": "UmweltbildungsparkSchaugatter"},
                    "24006": {"name": "RuhenderVerkehr"},
                    "99990": {"name": "Gaertnerei"},
                },
                "typename": "XP_BesondereZweckbestimmungGruen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteZweckbestimmung: Annotated[
        list[AnyUrl] | None,
        Field(
            description="Über eine CodeList definierte zusätzliche Zweckbestimmungen.",
            json_schema_extra={
                "typename": "FP_DetailZweckbestGruen",
                "stereotype": "Codelist",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung1: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "FP_DetailZweckbestGruen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung2: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "FP_DetailZweckbestGruen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung3: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "FP_DetailZweckbestGruen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung4: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "FP_DetailZweckbestGruen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung5: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "FP_DetailZweckbestGruen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    nutzungsform: Annotated[
        Literal["1000", "2000"] | None,
        Field(
            description="Nutzungsform der Grünfläche.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Privat", "description": "Private Nutzung"},
                    "2000": {
                        "name": "Oeffentlich",
                        "description": "Öffentliche Nutzung",
                    },
                },
                "typename": "XP_Nutzungsform",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class FPKeineZentrAbwasserBeseitigungFlaeche(FPFlaechenobjekt):
    """Baufläche, für die eine zentrale Abwasserbeseitigung nicht vorgesehen ist (§5, Abs. 2, Nr. 1 BauGB)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class FPKennzeichnung(FPGeometrieobjekt):
    """Kennzeichnungen gemäß §5 Abs. 3 BauGB."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    zweckbestimmung: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000", "6000", "7000", "9999"]]
        | None,
        Field(
            description="Zweckbestimmungen der Kennzeichnung.",
            json_schema_extra={
                "typename": "XP_ZweckbestimmungKennzeichnung",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {
                        "name": "Naturgewalten",
                        "description": "Flächen, bei deren Bebauung besondere bauliche Sicherungsmaßnahmen gegen Naturgewalten erforderlich sind (§5, Abs. 3, Nr. 1 BauGB).",
                    },
                    "2000": {
                        "name": "Abbauflaeche",
                        "description": "Flächen, unter denen der Bergbau umgeht oder die für den Abbau von Mineralien bestimmt sind (§5, Abs. 3, Nr. 2 BauGB).",
                    },
                    "3000": {
                        "name": "AeussereEinwirkungen",
                        "description": "Flächen, bei deren Bebauung besondere bauliche Sicherungsmaßnahmen gegen äußere Einwirkungen erforderlich sind (§5, Abs. 3, Nr. 1 BauGB).",
                    },
                    "4000": {
                        "name": "SchadstoffBelastBoden",
                        "description": "Für bauliche Nutzung vorgesehene Flächen, deren Böden erheblich mit umweltgefährdenden Stoffen belastet sind (§5, Abs. 3, Nr. 3 BauGB).",
                    },
                    "5000": {
                        "name": "LaermBelastung",
                        "description": "ür bauliche Nutzung vorgesehene Flächen, die erheblichen Lärmbelastung ausgesetzt sind.",
                    },
                    "6000": {"name": "Bergbau"},
                    "7000": {"name": "Bodenordnung"},
                    "9999": {
                        "name": "AndereGesetzlVorschriften",
                        "description": "Kennzeichnung nach anderen gesetzlichen Vorschriften.",
                    },
                },
            },
        ),
    ] = None
    weitereZweckbestimmung1: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "6000", "7000", "9999"] | None,
        Field(
            description='Weitere Zweckbestimmung der Kennzeichnung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Naturgewalten",
                        "description": "Flächen, bei deren Bebauung besondere bauliche Sicherungsmaßnahmen gegen Naturgewalten erforderlich sind (§5, Abs. 3, Nr. 1 BauGB).",
                    },
                    "2000": {
                        "name": "Abbauflaeche",
                        "description": "Flächen, unter denen der Bergbau umgeht oder die für den Abbau von Mineralien bestimmt sind (§5, Abs. 3, Nr. 2 BauGB).",
                    },
                    "3000": {
                        "name": "AeussereEinwirkungen",
                        "description": "Flächen, bei deren Bebauung besondere bauliche Sicherungsmaßnahmen gegen äußere Einwirkungen erforderlich sind (§5, Abs. 3, Nr. 1 BauGB).",
                    },
                    "4000": {
                        "name": "SchadstoffBelastBoden",
                        "description": "Für bauliche Nutzung vorgesehene Flächen, deren Böden erheblich mit umweltgefährdenden Stoffen belastet sind (§5, Abs. 3, Nr. 3 BauGB).",
                    },
                    "5000": {
                        "name": "LaermBelastung",
                        "description": "ür bauliche Nutzung vorgesehene Flächen, die erheblichen Lärmbelastung ausgesetzt sind.",
                    },
                    "6000": {"name": "Bergbau"},
                    "7000": {"name": "Bodenordnung"},
                    "9999": {
                        "name": "AndereGesetzlVorschriften",
                        "description": "Kennzeichnung nach anderen gesetzlichen Vorschriften.",
                    },
                },
                "typename": "XP_ZweckbestimmungKennzeichnung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class FPLandwirtschaftsFlaeche(FPFlaechenschlussobjekt):
    """Darstellung einer Landwirtschaftsfläche nach §5, Abs. 2, Nr. 9a."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    weitereZweckbestimmung2: Annotated[
        Literal["1000", "1100", "1200", "1300", "1400", "1500", "1600", "1700", "9999"]
        | None,
        Field(
            description='Weitere Zweckbestimmung der Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "LandwirtschaftAllgemein",
                        "description": "Allgemeine Landwirtschaft",
                    },
                    "1100": {"name": "Ackerbau", "description": "Ackerbau"},
                    "1200": {
                        "name": "WiesenWeidewirtschaft",
                        "description": "Wiesen- und Weidewirtschaft",
                    },
                    "1300": {
                        "name": "GartenbaulicheErzeugung",
                        "description": "Gartenbauliche Erzeugung",
                    },
                    "1400": {"name": "Obstbau", "description": "Obstbau"},
                    "1500": {"name": "Weinbau", "description": "Weinbau"},
                    "1600": {"name": "Imkerei", "description": "Imkerei"},
                    "1700": {
                        "name": "Binnenfischerei",
                        "description": "Binnenfischerei",
                    },
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungLandwirtschaft",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung3: Annotated[
        Literal["1000", "1100", "1200", "1300", "1400", "1500", "1600", "1700", "9999"]
        | None,
        Field(
            description='Weitere Zweckbestimmung der Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "LandwirtschaftAllgemein",
                        "description": "Allgemeine Landwirtschaft",
                    },
                    "1100": {"name": "Ackerbau", "description": "Ackerbau"},
                    "1200": {
                        "name": "WiesenWeidewirtschaft",
                        "description": "Wiesen- und Weidewirtschaft",
                    },
                    "1300": {
                        "name": "GartenbaulicheErzeugung",
                        "description": "Gartenbauliche Erzeugung",
                    },
                    "1400": {"name": "Obstbau", "description": "Obstbau"},
                    "1500": {"name": "Weinbau", "description": "Weinbau"},
                    "1600": {"name": "Imkerei", "description": "Imkerei"},
                    "1700": {
                        "name": "Binnenfischerei",
                        "description": "Binnenfischerei",
                    },
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungLandwirtschaft",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteZweckbestimmung: Annotated[
        list[AnyUrl] | None,
        Field(
            description="Über eine CodeList definierte zusätzliche Zweckbestimmungen.",
            json_schema_extra={
                "typename": "FP_DetailZweckbestLandwirtschaftsFlaeche",
                "stereotype": "Codelist",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung1: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "FP_DetailZweckbestLandwirtschaftsFlaeche",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung2: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "FP_DetailZweckbestLandwirtschaftsFlaeche",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung3: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "FP_DetailZweckbestLandwirtschaftsFlaeche",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    zweckbestimmung: Annotated[
        list[
            Literal[
                "1000", "1100", "1200", "1300", "1400", "1500", "1600", "1700", "9999"
            ]
        ]
        | None,
        Field(
            description="Zweckbestimmungen der Fläche.",
            json_schema_extra={
                "typename": "XP_ZweckbestimmungLandwirtschaft",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {
                        "name": "LandwirtschaftAllgemein",
                        "description": "Allgemeine Landwirtschaft",
                    },
                    "1100": {"name": "Ackerbau", "description": "Ackerbau"},
                    "1200": {
                        "name": "WiesenWeidewirtschaft",
                        "description": "Wiesen- und Weidewirtschaft",
                    },
                    "1300": {
                        "name": "GartenbaulicheErzeugung",
                        "description": "Gartenbauliche Erzeugung",
                    },
                    "1400": {"name": "Obstbau", "description": "Obstbau"},
                    "1500": {"name": "Weinbau", "description": "Weinbau"},
                    "1600": {"name": "Imkerei", "description": "Imkerei"},
                    "1700": {
                        "name": "Binnenfischerei",
                        "description": "Binnenfischerei",
                    },
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
            },
        ),
    ] = None
    weitereZweckbestimmung1: Annotated[
        Literal["1000", "1100", "1200", "1300", "1400", "1500", "1600", "1700", "9999"]
        | None,
        Field(
            description='Weitere Zweckbestimmung der Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "LandwirtschaftAllgemein",
                        "description": "Allgemeine Landwirtschaft",
                    },
                    "1100": {"name": "Ackerbau", "description": "Ackerbau"},
                    "1200": {
                        "name": "WiesenWeidewirtschaft",
                        "description": "Wiesen- und Weidewirtschaft",
                    },
                    "1300": {
                        "name": "GartenbaulicheErzeugung",
                        "description": "Gartenbauliche Erzeugung",
                    },
                    "1400": {"name": "Obstbau", "description": "Obstbau"},
                    "1500": {"name": "Weinbau", "description": "Weinbau"},
                    "1600": {"name": "Imkerei", "description": "Imkerei"},
                    "1700": {
                        "name": "Binnenfischerei",
                        "description": "Binnenfischerei",
                    },
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungLandwirtschaft",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class FPLinienobjekt(FPObjekt):
    """Basisklasse für alle Objekte eines Flächennutzungsplans mit linienförmigem Raumbezug (eine einzelne zusammenhängende Kurve, die aus Linienstücken und Kreisbögen zusammengesetzt sein kann, oder eine Menge derartiger Kurven)."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Line | definitions.MultiLine,
        Field(
            json_schema_extra={
                "typename": "XP_Liniengeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            }
        ),
    ]


class FPPrivilegiertesVorhaben(FPGeometrieobjekt):
    """Standorte für privilegierte Außenbereichsvorhaben und für sonstige Anlagen in Außenbereichen gem. § 35 Abs. 1 und 2 BauGB."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    zweckbestimmung: Annotated[
        list[Literal["1000", "1200", "1400", "1600", "1800", "2000", "9999"]] | None,
        Field(
            description="Zweckbestimmungen des Vorhabens.",
            json_schema_extra={
                "typename": "FP_ZweckbestimmungPrivilegiertesVorhaben",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {
                        "name": "LandForstwirtschaft",
                        "description": 'Vorhaben nach §35 Abs. 1 Nr. 1 oder 2 BauGB: Vorhaben, dass "einem land- oder forstwirtschaftlichen Betrieb dient und nur einen untergeordnetenTeil der Betriebsfläche einnimmt", oder "einem Betrieb der gartenbaulichen Erzeugung dient".',
                    },
                    "1200": {
                        "name": "OeffentlicheVersorgung",
                        "description": 'Vorhaben nach §35 Abs. 1 Nr. 3 BauBG: Vorhaben dass "der öffentlichen Versorgung mit Elektrizität, Gas,\r\nTelekommunikationsdienstleistungen, Wärme und Wasser, der Abwasserwirtschaft" ... dient.',
                    },
                    "1400": {
                        "name": "OrtsgebundenerGewerbebetrieb",
                        "description": 'Vorhaben nach §35 Abs. 1 Nr. 3 BauGB: Vorhaben das ...."einem ortsgebundenen gewerblichen Betrieb dient".',
                    },
                    "1600": {
                        "name": "BesonderesVorhaben",
                        "description": 'Vorhaben nach §35 Abs. 1 Nr. 4 BauGB: Vorhaben, dass "wegen seiner besonderen Anforderungen an die Umgebung, wegen seiner nachteiligen Wirkung auf die Umgebung oder wegen seiner besonderen Zweckbestimmung nur im Außenbereich ausgeführt werden soll".',
                    },
                    "1800": {
                        "name": "ErneuerbareEnergie",
                        "description": 'Vorhaben nach §35 Abs 1 Nr.. 5 oder 6 BauGB: Vorhaben  dass "der Erforschung, Entwicklung oder Nutzung der Wind- oder Wasserenergie dient" oder "der energetischen Nutzung von Biomasse ...".',
                    },
                    "2000": {
                        "name": "Kernenergie",
                        "description": 'Vorhaben nach §35 Abs. 1 Nr. 7 BauGB: Vorhaben das "der Erforschung, Entwicklung oder Nutzung der Kernenergie zu friedlichen Zwecken oder der Entsorgung radioaktiver Abfälle dient".',
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstiges Vorhaben im Aussenbereich nach §35 Abs. 2 BauGB.",
                    },
                },
            },
        ),
    ] = None
    weitereZweckbestimmung1: Annotated[
        Literal["1000", "1200", "1400", "1600", "1800", "2000", "9999"] | None,
        Field(
            description='Weitere Zweckbestimmung des Vorhabens. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "LandForstwirtschaft",
                        "description": 'Vorhaben nach §35 Abs. 1 Nr. 1 oder 2 BauGB: Vorhaben, dass "einem land- oder forstwirtschaftlichen Betrieb dient und nur einen untergeordnetenTeil der Betriebsfläche einnimmt", oder "einem Betrieb der gartenbaulichen Erzeugung dient".',
                    },
                    "1200": {
                        "name": "OeffentlicheVersorgung",
                        "description": 'Vorhaben nach §35 Abs. 1 Nr. 3 BauBG: Vorhaben dass "der öffentlichen Versorgung mit Elektrizität, Gas,\r\nTelekommunikationsdienstleistungen, Wärme und Wasser, der Abwasserwirtschaft" ... dient.',
                    },
                    "1400": {
                        "name": "OrtsgebundenerGewerbebetrieb",
                        "description": 'Vorhaben nach §35 Abs. 1 Nr. 3 BauGB: Vorhaben das ...."einem ortsgebundenen gewerblichen Betrieb dient".',
                    },
                    "1600": {
                        "name": "BesonderesVorhaben",
                        "description": 'Vorhaben nach §35 Abs. 1 Nr. 4 BauGB: Vorhaben, dass "wegen seiner besonderen Anforderungen an die Umgebung, wegen seiner nachteiligen Wirkung auf die Umgebung oder wegen seiner besonderen Zweckbestimmung nur im Außenbereich ausgeführt werden soll".',
                    },
                    "1800": {
                        "name": "ErneuerbareEnergie",
                        "description": 'Vorhaben nach §35 Abs 1 Nr.. 5 oder 6 BauGB: Vorhaben  dass "der Erforschung, Entwicklung oder Nutzung der Wind- oder Wasserenergie dient" oder "der energetischen Nutzung von Biomasse ...".',
                    },
                    "2000": {
                        "name": "Kernenergie",
                        "description": 'Vorhaben nach §35 Abs. 1 Nr. 7 BauGB: Vorhaben das "der Erforschung, Entwicklung oder Nutzung der Kernenergie zu friedlichen Zwecken oder der Entsorgung radioaktiver Abfälle dient".',
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstiges Vorhaben im Aussenbereich nach §35 Abs. 2 BauGB.",
                    },
                },
                "typename": "FP_ZweckbestimmungPrivilegiertesVorhaben",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung2: Annotated[
        Literal["1000", "1200", "1400", "1600", "1800", "2000", "9999"] | None,
        Field(
            description='Weitere Zweckbestimmung des Vorhabens.Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "LandForstwirtschaft",
                        "description": 'Vorhaben nach §35 Abs. 1 Nr. 1 oder 2 BauGB: Vorhaben, dass "einem land- oder forstwirtschaftlichen Betrieb dient und nur einen untergeordnetenTeil der Betriebsfläche einnimmt", oder "einem Betrieb der gartenbaulichen Erzeugung dient".',
                    },
                    "1200": {
                        "name": "OeffentlicheVersorgung",
                        "description": 'Vorhaben nach §35 Abs. 1 Nr. 3 BauBG: Vorhaben dass "der öffentlichen Versorgung mit Elektrizität, Gas,\r\nTelekommunikationsdienstleistungen, Wärme und Wasser, der Abwasserwirtschaft" ... dient.',
                    },
                    "1400": {
                        "name": "OrtsgebundenerGewerbebetrieb",
                        "description": 'Vorhaben nach §35 Abs. 1 Nr. 3 BauGB: Vorhaben das ...."einem ortsgebundenen gewerblichen Betrieb dient".',
                    },
                    "1600": {
                        "name": "BesonderesVorhaben",
                        "description": 'Vorhaben nach §35 Abs. 1 Nr. 4 BauGB: Vorhaben, dass "wegen seiner besonderen Anforderungen an die Umgebung, wegen seiner nachteiligen Wirkung auf die Umgebung oder wegen seiner besonderen Zweckbestimmung nur im Außenbereich ausgeführt werden soll".',
                    },
                    "1800": {
                        "name": "ErneuerbareEnergie",
                        "description": 'Vorhaben nach §35 Abs 1 Nr.. 5 oder 6 BauGB: Vorhaben  dass "der Erforschung, Entwicklung oder Nutzung der Wind- oder Wasserenergie dient" oder "der energetischen Nutzung von Biomasse ...".',
                    },
                    "2000": {
                        "name": "Kernenergie",
                        "description": 'Vorhaben nach §35 Abs. 1 Nr. 7 BauGB: Vorhaben das "der Erforschung, Entwicklung oder Nutzung der Kernenergie zu friedlichen Zwecken oder der Entsorgung radioaktiver Abfälle dient".',
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstiges Vorhaben im Aussenbereich nach §35 Abs. 2 BauGB.",
                    },
                },
                "typename": "FP_ZweckbestimmungPrivilegiertesVorhaben",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    besondereZweckbestimmung: Annotated[
        list[
            Literal[
                "10000",
                "10001",
                "10002",
                "10003",
                "10004",
                "12000",
                "12001",
                "12002",
                "12003",
                "12004",
                "12005",
                "16000",
                "16001",
                "16002",
                "18000",
                "18001",
                "18002",
                "18003",
                "20000",
                "20001",
                "99990",
                "99991",
            ]
        ]
        | None,
        Field(
            description="Besondere Zweckbestimmungendes Vorhabens, die die spezifizierten allgemeinen Zweckbestimmungen detaillieren.",
            json_schema_extra={
                "typename": "FP_BesondZweckbestPrivilegiertesVorhaben",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "10000": {"name": "Aussiedlerhof"},
                    "10001": {"name": "Altenteil"},
                    "10002": {"name": "Reiterhof"},
                    "10003": {"name": "Gartenbaubetrieb"},
                    "10004": {"name": "Baumschule"},
                    "12000": {
                        "name": "Wasser",
                        "description": "Öffentliche Wasserversorgung",
                    },
                    "12001": {"name": "Gas", "description": "Gasversorgung"},
                    "12002": {"name": "Waerme", "description": "Wärmeversorgung"},
                    "12003": {
                        "name": "Elektrizitaet",
                        "description": "Versorgung mit Elektrizität.",
                    },
                    "12004": {
                        "name": "Telekommunikation",
                        "description": "Versorgung mit Telekommunikations-Dienstleistungen.",
                    },
                    "12005": {"name": "Abwasser", "description": "Abwasser Entsorgung"},
                    "16000": {
                        "name": "BesondereUmgebungsAnforderung",
                        "description": "Vorhaben dass wegen seiner besonderen Anforderungen an die Umgebung nur im Aussenbereich durchgeführt werden soll.",
                    },
                    "16001": {
                        "name": "NachteiligeUmgebungsWirkung",
                        "description": "Vorhaben dass wegen seiner nachteiligen Wirkung auf die Umgebung nur im Aussenbereich durchgeführt werden soll.",
                    },
                    "16002": {
                        "name": "BesondereZweckbestimmung",
                        "description": "Vorhaben dass wegen seiner besonderen Zweckbestimmung nur im Aussenbereich durchgeführt werden soll.",
                    },
                    "18000": {
                        "name": "Windenergie",
                        "description": "Vorhaben zur Erforschung, Entwicklung oder Nutzung der Windenergie.",
                    },
                    "18001": {
                        "name": "Wasserenergie",
                        "description": "Vorhaben zur Erforschung, Entwicklung oder Nutzung der Wasserenergie.",
                    },
                    "18002": {
                        "name": "Solarenergie",
                        "description": "Vorhaben zur Erforschung, Entwicklung oder Nutzung der Solarenergie.",
                    },
                    "18003": {
                        "name": "Biomasse",
                        "description": "Vorhaben zur energetischen Nutzung der Biomasse.",
                    },
                    "20000": {
                        "name": "NutzungKernerergie",
                        "description": "Vorhaben der Erforschung, Entwicklung oder Nutzung der Kernenergie zu friedlichen Zwecken.",
                    },
                    "20001": {
                        "name": "EntsorgungRadioaktiveAbfaelle",
                        "description": "Vorhaben zur Entsorgung radioaktiver Abfälle.",
                    },
                    "99990": {"name": "StandortEinzelhof"},
                    "99991": {"name": "BebauteFlaecheAussenbereich"},
                },
            },
        ),
    ] = None
    weitereBesondZweckbestimmung1: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "10004",
            "12000",
            "12001",
            "12002",
            "12003",
            "12004",
            "12005",
            "16000",
            "16001",
            "16002",
            "18000",
            "18001",
            "18002",
            "18003",
            "20000",
            "20001",
            "99990",
            "99991",
        ]
        | None,
        Field(
            description='Besondere Zweckbestimmung des Vorhabens, die die spezifizierte allgemeine Zweckbestimmung detaillieren. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {"name": "Aussiedlerhof"},
                    "10001": {"name": "Altenteil"},
                    "10002": {"name": "Reiterhof"},
                    "10003": {"name": "Gartenbaubetrieb"},
                    "10004": {"name": "Baumschule"},
                    "12000": {
                        "name": "Wasser",
                        "description": "Öffentliche Wasserversorgung",
                    },
                    "12001": {"name": "Gas", "description": "Gasversorgung"},
                    "12002": {"name": "Waerme", "description": "Wärmeversorgung"},
                    "12003": {
                        "name": "Elektrizitaet",
                        "description": "Versorgung mit Elektrizität.",
                    },
                    "12004": {
                        "name": "Telekommunikation",
                        "description": "Versorgung mit Telekommunikations-Dienstleistungen.",
                    },
                    "12005": {"name": "Abwasser", "description": "Abwasser Entsorgung"},
                    "16000": {
                        "name": "BesondereUmgebungsAnforderung",
                        "description": "Vorhaben dass wegen seiner besonderen Anforderungen an die Umgebung nur im Aussenbereich durchgeführt werden soll.",
                    },
                    "16001": {
                        "name": "NachteiligeUmgebungsWirkung",
                        "description": "Vorhaben dass wegen seiner nachteiligen Wirkung auf die Umgebung nur im Aussenbereich durchgeführt werden soll.",
                    },
                    "16002": {
                        "name": "BesondereZweckbestimmung",
                        "description": "Vorhaben dass wegen seiner besonderen Zweckbestimmung nur im Aussenbereich durchgeführt werden soll.",
                    },
                    "18000": {
                        "name": "Windenergie",
                        "description": "Vorhaben zur Erforschung, Entwicklung oder Nutzung der Windenergie.",
                    },
                    "18001": {
                        "name": "Wasserenergie",
                        "description": "Vorhaben zur Erforschung, Entwicklung oder Nutzung der Wasserenergie.",
                    },
                    "18002": {
                        "name": "Solarenergie",
                        "description": "Vorhaben zur Erforschung, Entwicklung oder Nutzung der Solarenergie.",
                    },
                    "18003": {
                        "name": "Biomasse",
                        "description": "Vorhaben zur energetischen Nutzung der Biomasse.",
                    },
                    "20000": {
                        "name": "NutzungKernerergie",
                        "description": "Vorhaben der Erforschung, Entwicklung oder Nutzung der Kernenergie zu friedlichen Zwecken.",
                    },
                    "20001": {
                        "name": "EntsorgungRadioaktiveAbfaelle",
                        "description": "Vorhaben zur Entsorgung radioaktiver Abfälle.",
                    },
                    "99990": {"name": "StandortEinzelhof"},
                    "99991": {"name": "BebauteFlaecheAussenbereich"},
                },
                "typename": "FP_BesondZweckbestPrivilegiertesVorhaben",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereBesondZweckbestimmung2: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "10004",
            "12000",
            "12001",
            "12002",
            "12003",
            "12004",
            "12005",
            "16000",
            "16001",
            "16002",
            "18000",
            "18001",
            "18002",
            "18003",
            "20000",
            "20001",
            "99990",
            "99991",
        ]
        | None,
        Field(
            description='Besondere Zweckbestimmung des Vorhabens, die die spezifizierte allgemeine Zweckbestimmung detaillieren. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {"name": "Aussiedlerhof"},
                    "10001": {"name": "Altenteil"},
                    "10002": {"name": "Reiterhof"},
                    "10003": {"name": "Gartenbaubetrieb"},
                    "10004": {"name": "Baumschule"},
                    "12000": {
                        "name": "Wasser",
                        "description": "Öffentliche Wasserversorgung",
                    },
                    "12001": {"name": "Gas", "description": "Gasversorgung"},
                    "12002": {"name": "Waerme", "description": "Wärmeversorgung"},
                    "12003": {
                        "name": "Elektrizitaet",
                        "description": "Versorgung mit Elektrizität.",
                    },
                    "12004": {
                        "name": "Telekommunikation",
                        "description": "Versorgung mit Telekommunikations-Dienstleistungen.",
                    },
                    "12005": {"name": "Abwasser", "description": "Abwasser Entsorgung"},
                    "16000": {
                        "name": "BesondereUmgebungsAnforderung",
                        "description": "Vorhaben dass wegen seiner besonderen Anforderungen an die Umgebung nur im Aussenbereich durchgeführt werden soll.",
                    },
                    "16001": {
                        "name": "NachteiligeUmgebungsWirkung",
                        "description": "Vorhaben dass wegen seiner nachteiligen Wirkung auf die Umgebung nur im Aussenbereich durchgeführt werden soll.",
                    },
                    "16002": {
                        "name": "BesondereZweckbestimmung",
                        "description": "Vorhaben dass wegen seiner besonderen Zweckbestimmung nur im Aussenbereich durchgeführt werden soll.",
                    },
                    "18000": {
                        "name": "Windenergie",
                        "description": "Vorhaben zur Erforschung, Entwicklung oder Nutzung der Windenergie.",
                    },
                    "18001": {
                        "name": "Wasserenergie",
                        "description": "Vorhaben zur Erforschung, Entwicklung oder Nutzung der Wasserenergie.",
                    },
                    "18002": {
                        "name": "Solarenergie",
                        "description": "Vorhaben zur Erforschung, Entwicklung oder Nutzung der Solarenergie.",
                    },
                    "18003": {
                        "name": "Biomasse",
                        "description": "Vorhaben zur energetischen Nutzung der Biomasse.",
                    },
                    "20000": {
                        "name": "NutzungKernerergie",
                        "description": "Vorhaben der Erforschung, Entwicklung oder Nutzung der Kernenergie zu friedlichen Zwecken.",
                    },
                    "20001": {
                        "name": "EntsorgungRadioaktiveAbfaelle",
                        "description": "Vorhaben zur Entsorgung radioaktiver Abfälle.",
                    },
                    "99990": {"name": "StandortEinzelhof"},
                    "99991": {"name": "BebauteFlaecheAussenbereich"},
                },
                "typename": "FP_BesondZweckbestPrivilegiertesVorhaben",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    vorhaben: Annotated[
        str | None,
        Field(
            description="Nähere Beschreibung des Vorhabens.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class FPSchutzPflegeEntwicklung(FPGeometrieobjekt):
    """Umgrenzung von Flächen für Maßnahmen zum Schutz, zur Pflege und zur Entwicklung von Natur und Landschaft (§5 Abs. 2, Nr. 10 BauGB)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    ziel: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"] | None,
        Field(
            description='Unterscheidung nach den Zielen "Schutz, Pflege" und "Entwicklung".',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "SchutzPflege"},
                    "2000": {"name": "Entwicklung"},
                    "3000": {"name": "Anlage"},
                    "4000": {"name": "SchutzPflegeEntwicklung"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "XP_SPEZiele",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    massnahme: Annotated[
        list[XPSPEMassnahmenDaten] | None,
        Field(
            description="Durchzuführende Maßnahmen.",
            json_schema_extra={
                "typename": "XP_SPEMassnahmenDaten",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    weitereMassnahme1: Annotated[
        XPSPEMassnahmenDaten | None,
        Field(
            description='Weitere durchzuführende Massnahme. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen massnahme mehrfach belegt werden.',
            json_schema_extra={
                "typename": "XP_SPEMassnahmenDaten",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereMassnahme2: Annotated[
        XPSPEMassnahmenDaten | None,
        Field(
            description='Weitere durchzuführende Massnahme. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen massnahme mehrfach belegt werden.',
            json_schema_extra={
                "typename": "XP_SPEMassnahmenDaten",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    istAusgleich: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob die Maßnahme zum Ausgkeich eines Eingriffs benutzt wird.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False


class FPSpielSportanlage(FPGeometrieobjekt):
    """Darstellung von Flächen für Spiel- und Sportanlagen nach §5,  Abs. 2, Nr. 2 BauGB."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    zweckbestimmung: Annotated[
        list[Literal["1000", "2000", "3000", "9999"]] | None,
        Field(
            description="Zweckbestimmungen der Fläche",
            json_schema_extra={
                "typename": "XP_ZweckbestimmungSpielSportanlage",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Sportanlage", "description": "Sportanlage"},
                    "2000": {"name": "Spielanlage", "description": "Spielanlage"},
                    "3000": {
                        "name": "SpielSportanlage",
                        "description": "Spiel- und/oder Sportanlage.",
                    },
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
            },
        ),
    ] = None
    weitereZweckbestimmung1: Annotated[
        Literal["1000", "2000", "3000", "9999"] | None,
        Field(
            description='Weitere Zweckbestimmung der Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Sportanlage", "description": "Sportanlage"},
                    "2000": {"name": "Spielanlage", "description": "Spielanlage"},
                    "3000": {
                        "name": "SpielSportanlage",
                        "description": "Spiel- und/oder Sportanlage.",
                    },
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungSpielSportanlage",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteZweckbestimmung: Annotated[
        list[AnyUrl] | None,
        Field(
            description="Über eine CodeList definierte zusätzliche Zweckbestimmungen.",
            json_schema_extra={
                "typename": "FP_DetailZweckbestSpielSportanlage",
                "stereotype": "Codelist",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung1: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "FP_DetailZweckbestSpielSportanlage",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class FPStrassenverkehr(FPGeometrieobjekt):
    """Darstellung von Flächen für den überörtlichen Verkehr und für die örtlichen Hauptverkehrszüge ( §5, Abs. 2, Nr. 3 BauGB)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    zweckbestimmung: Annotated[
        Literal["1000", "1200", "1400", "1600", "9999"] | None,
        Field(
            description="Allgemeine Zweckbestimmung des Objektes.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Autobahn",
                        "description": "Autobahn und autobahnähnliche Straße.",
                    },
                    "1200": {
                        "name": "Hauptverkehrsstrasse",
                        "description": "Sonstige örtliche oder überörtliche Hauptverkehrsstraße bzw. Weg.",
                    },
                    "1400": {
                        "name": "SonstigerVerkehrswegAnlage",
                        "description": "Sonstiger Verkehrsweg oder Anlage.",
                    },
                    "1600": {
                        "name": "RuhenderVerkehr",
                        "description": "Fläche oder Anlage für den ruhenden Verkehr.",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstige Zweckbestimmung",
                    },
                },
                "typename": "FP_ZweckbestimmungStrassenverkehr",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    besondereZweckbestimmung: Annotated[
        Literal[
            "14000",
            "14001",
            "14002",
            "14003",
            "14004",
            "14005",
            "14006",
            "14007",
            "14008",
            "14009",
            "14010",
            "14011",
        ]
        | None,
        Field(
            description="Besondere Zweckbestimmung des Objektes, der die allgemiene Zweckbestimmung detaillliert oder ersetzt.",
            json_schema_extra={
                "enumDescription": {
                    "14000": {"name": "VerkehrsberuhigterBereich"},
                    "14001": {"name": "Platz"},
                    "14002": {"name": "Fussgaengerbereich"},
                    "14003": {"name": "RadFussweg"},
                    "14004": {"name": "Radweg"},
                    "14005": {"name": "Fussweg"},
                    "14006": {"name": "Wanderweg"},
                    "14007": {"name": "ReitKutschweg"},
                    "14008": {"name": "Rastanlage"},
                    "14009": {"name": "Busbahnhof"},
                    "14010": {"name": "UeberfuehrenderVerkehrsweg"},
                    "14011": {"name": "UnterfuehrenderVerkehrsweg"},
                },
                "typename": "FP_BesondereZweckbestimmungStrassenverkehr",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteZweckbestimmung: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definierte zusätzliche Zweckbestimmung",
            json_schema_extra={
                "typename": "FP_DetailZweckbestStrassenverkehr",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    nutzungsform: Annotated[
        Literal["1000", "2000"] | None,
        Field(
            description="Nutzungsform",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Privat", "description": "Private Nutzung"},
                    "2000": {
                        "name": "Oeffentlich",
                        "description": "Öffentliche Nutzung",
                    },
                },
                "typename": "XP_Nutzungsform",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class FPUeberlagerungsobjekt(FPFlaechenobjekt):
    """Basisklasse für alle Objekte eines Flächennutzungsplans mit flächenhaftem Raumbezug, die immer Überlagerungsobjekte sind."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class FPUnverbindlicheVormerkung(FPGeometrieobjekt):
    """Unverbindliche Vormerkung späterer Planungsabsichten"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    vormerkung: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            }
        ),
    ] = None


class FPVerEntsorgung(FPGeometrieobjekt):
    """Flächen für Versorgungsanlagen, für die Abfallentsorgung und Abwasserbeseitigung sowie für Ablagerungen (§5, Abs. 2, Nr. 4 BauGB)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    zweckbestimmung: Annotated[
        list[
            Literal[
                "1000",
                "1200",
                "1300",
                "1400",
                "1600",
                "1800",
                "2000",
                "2200",
                "2400",
                "2600",
                "2800",
                "3000",
                "9999",
            ]
        ]
        | None,
        Field(
            description="Allgemeine Zweckbestimmungen der Fläche.",
            json_schema_extra={
                "typename": "XP_ZweckbestimmungVerEntsorgung",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {
                        "name": "Elektrizitaet",
                        "description": "Versorgung mit Elektrizität",
                    },
                    "1200": {"name": "Gas", "description": "Gas-Versorgung"},
                    "1300": {"name": "Erdoel"},
                    "1400": {
                        "name": "Waermeversorgung",
                        "description": "Versorgung mit Fernwärme",
                    },
                    "1600": {"name": "Trinkwasser", "description": "Wasser-Versorgung"},
                    "1800": {"name": "Abwasser", "description": "Abwasser-Entsorgung"},
                    "2000": {
                        "name": "Regenwasser",
                        "description": "Regenwasser Entsorgung",
                    },
                    "2200": {
                        "name": "Abfallentsorgung",
                        "description": "Abfall-Beseitigung",
                    },
                    "2400": {
                        "name": "Ablagerung",
                        "description": "Ablagerungen, Deponien",
                    },
                    "2600": {
                        "name": "Telekommunikation",
                        "description": "Einrichtungen und Anlagen zur Telekommunikation",
                    },
                    "2800": {
                        "name": "ErneuerbareEnergien",
                        "description": "Anlagen, Einrichtungen oder sonstige Maßnahmen zur dezentralen und zentralen Erzeugung, Verteilung oder Speicherung von Strom, Wärme oder Kälte aus erneuerbaren Energien.",
                    },
                    "3000": {
                        "name": "KraftWaermeKopplung",
                        "description": "Anlagen, Einrichtungen oder sonstige Maßnahmen zur dezentralen und zentralen Erzeugung, Verteilung oder Speicherung von Strom, Wärme oder Kälte aus Kraft-Wärme Kopplung.",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstige Zweckbestimmung",
                    },
                },
            },
        ),
    ] = None
    weitereZweckbestimmung1: Annotated[
        Literal[
            "1000",
            "1200",
            "1300",
            "1400",
            "1600",
            "1800",
            "2000",
            "2200",
            "2400",
            "2600",
            "2800",
            "3000",
            "9999",
        ]
        | None,
        Field(
            description='Weitere allgemeine Zweckbestimmung der Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Elektrizitaet",
                        "description": "Versorgung mit Elektrizität",
                    },
                    "1200": {"name": "Gas", "description": "Gas-Versorgung"},
                    "1300": {"name": "Erdoel"},
                    "1400": {
                        "name": "Waermeversorgung",
                        "description": "Versorgung mit Fernwärme",
                    },
                    "1600": {"name": "Trinkwasser", "description": "Wasser-Versorgung"},
                    "1800": {"name": "Abwasser", "description": "Abwasser-Entsorgung"},
                    "2000": {
                        "name": "Regenwasser",
                        "description": "Regenwasser Entsorgung",
                    },
                    "2200": {
                        "name": "Abfallentsorgung",
                        "description": "Abfall-Beseitigung",
                    },
                    "2400": {
                        "name": "Ablagerung",
                        "description": "Ablagerungen, Deponien",
                    },
                    "2600": {
                        "name": "Telekommunikation",
                        "description": "Einrichtungen und Anlagen zur Telekommunikation",
                    },
                    "2800": {
                        "name": "ErneuerbareEnergien",
                        "description": "Anlagen, Einrichtungen oder sonstige Maßnahmen zur dezentralen und zentralen Erzeugung, Verteilung oder Speicherung von Strom, Wärme oder Kälte aus erneuerbaren Energien.",
                    },
                    "3000": {
                        "name": "KraftWaermeKopplung",
                        "description": "Anlagen, Einrichtungen oder sonstige Maßnahmen zur dezentralen und zentralen Erzeugung, Verteilung oder Speicherung von Strom, Wärme oder Kälte aus Kraft-Wärme Kopplung.",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstige Zweckbestimmung",
                    },
                },
                "typename": "XP_ZweckbestimmungVerEntsorgung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung2: Annotated[
        Literal[
            "1000",
            "1200",
            "1300",
            "1400",
            "1600",
            "1800",
            "2000",
            "2200",
            "2400",
            "2600",
            "2800",
            "3000",
            "9999",
        ]
        | None,
        Field(
            description='Weitere allgemeine Zweckbestimmung der Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Elektrizitaet",
                        "description": "Versorgung mit Elektrizität",
                    },
                    "1200": {"name": "Gas", "description": "Gas-Versorgung"},
                    "1300": {"name": "Erdoel"},
                    "1400": {
                        "name": "Waermeversorgung",
                        "description": "Versorgung mit Fernwärme",
                    },
                    "1600": {"name": "Trinkwasser", "description": "Wasser-Versorgung"},
                    "1800": {"name": "Abwasser", "description": "Abwasser-Entsorgung"},
                    "2000": {
                        "name": "Regenwasser",
                        "description": "Regenwasser Entsorgung",
                    },
                    "2200": {
                        "name": "Abfallentsorgung",
                        "description": "Abfall-Beseitigung",
                    },
                    "2400": {
                        "name": "Ablagerung",
                        "description": "Ablagerungen, Deponien",
                    },
                    "2600": {
                        "name": "Telekommunikation",
                        "description": "Einrichtungen und Anlagen zur Telekommunikation",
                    },
                    "2800": {
                        "name": "ErneuerbareEnergien",
                        "description": "Anlagen, Einrichtungen oder sonstige Maßnahmen zur dezentralen und zentralen Erzeugung, Verteilung oder Speicherung von Strom, Wärme oder Kälte aus erneuerbaren Energien.",
                    },
                    "3000": {
                        "name": "KraftWaermeKopplung",
                        "description": "Anlagen, Einrichtungen oder sonstige Maßnahmen zur dezentralen und zentralen Erzeugung, Verteilung oder Speicherung von Strom, Wärme oder Kälte aus Kraft-Wärme Kopplung.",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstige Zweckbestimmung",
                    },
                },
                "typename": "XP_ZweckbestimmungVerEntsorgung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung3: Annotated[
        Literal[
            "1000",
            "1200",
            "1300",
            "1400",
            "1600",
            "1800",
            "2000",
            "2200",
            "2400",
            "2600",
            "2800",
            "3000",
            "9999",
        ]
        | None,
        Field(
            description='Weitere allgemeine Zweckbestimmung der Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Elektrizitaet",
                        "description": "Versorgung mit Elektrizität",
                    },
                    "1200": {"name": "Gas", "description": "Gas-Versorgung"},
                    "1300": {"name": "Erdoel"},
                    "1400": {
                        "name": "Waermeversorgung",
                        "description": "Versorgung mit Fernwärme",
                    },
                    "1600": {"name": "Trinkwasser", "description": "Wasser-Versorgung"},
                    "1800": {"name": "Abwasser", "description": "Abwasser-Entsorgung"},
                    "2000": {
                        "name": "Regenwasser",
                        "description": "Regenwasser Entsorgung",
                    },
                    "2200": {
                        "name": "Abfallentsorgung",
                        "description": "Abfall-Beseitigung",
                    },
                    "2400": {
                        "name": "Ablagerung",
                        "description": "Ablagerungen, Deponien",
                    },
                    "2600": {
                        "name": "Telekommunikation",
                        "description": "Einrichtungen und Anlagen zur Telekommunikation",
                    },
                    "2800": {
                        "name": "ErneuerbareEnergien",
                        "description": "Anlagen, Einrichtungen oder sonstige Maßnahmen zur dezentralen und zentralen Erzeugung, Verteilung oder Speicherung von Strom, Wärme oder Kälte aus erneuerbaren Energien.",
                    },
                    "3000": {
                        "name": "KraftWaermeKopplung",
                        "description": "Anlagen, Einrichtungen oder sonstige Maßnahmen zur dezentralen und zentralen Erzeugung, Verteilung oder Speicherung von Strom, Wärme oder Kälte aus Kraft-Wärme Kopplung.",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstige Zweckbestimmung",
                    },
                },
                "typename": "XP_ZweckbestimmungVerEntsorgung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    besondereZweckbestimmung: Annotated[
        list[
            Literal[
                "10000",
                "10001",
                "10002",
                "10003",
                "10004",
                "10005",
                "10006",
                "10007",
                "10008",
                "10009",
                "10010",
                "12000",
                "12001",
                "12002",
                "12003",
                "12004",
                "12005",
                "13000",
                "13001",
                "13002",
                "13003",
                "14000",
                "14001",
                "14002",
                "16000",
                "16001",
                "16002",
                "16003",
                "16004",
                "16005",
                "18000",
                "18001",
                "18002",
                "18003",
                "18004",
                "18005",
                "20000",
                "20001",
                "22000",
                "22001",
                "22002",
                "22003",
                "24000",
                "24001",
                "24002",
                "24003",
                "24004",
                "24005",
                "26000",
                "26001",
                "26002",
                "28000",
                "28001",
                "28002",
                "28003",
                "28004",
                "99990",
            ]
        ]
        | None,
        Field(
            description="Besondere Zweckbestimmungen der Fläche, die die zugehörigen allgemeinen Zweckbestimmungen detaillieren oder ersetzen.",
            json_schema_extra={
                "typename": "XP_BesondereZweckbestimmungVerEntsorgung",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "10000": {"name": "Hochspannungsleitung"},
                    "10001": {"name": "TrafostationUmspannwerk"},
                    "10002": {"name": "Solarkraftwerk"},
                    "10003": {"name": "Windkraftwerk"},
                    "10004": {"name": "Geothermiekraftwerk"},
                    "10005": {"name": "Elektrizitaetswerk"},
                    "10006": {"name": "Wasserkraftwerk"},
                    "10007": {"name": "BiomasseKraftwerk"},
                    "10008": {"name": "Kabelleitung"},
                    "10009": {"name": "Niederspannungsleitung"},
                    "10010": {"name": "Leitungsmast"},
                    "12000": {"name": "Ferngasleitung"},
                    "12001": {"name": "Gaswerk"},
                    "12002": {"name": "Gasbehaelter"},
                    "12003": {"name": "Gasdruckregler"},
                    "12004": {"name": "Gasstation"},
                    "12005": {"name": "Gasleitung"},
                    "13000": {"name": "Erdoelleitung"},
                    "13001": {"name": "Bohrstelle"},
                    "13002": {"name": "Erdoelpumpstation"},
                    "13003": {"name": "Oeltank"},
                    "14000": {"name": "Blockheizkraftwerk"},
                    "14001": {"name": "Fernwaermeleitung"},
                    "14002": {"name": "Fernheizwerk"},
                    "16000": {"name": "Wasserwerk"},
                    "16001": {"name": "Wasserleitung"},
                    "16002": {"name": "Wasserspeicher"},
                    "16003": {"name": "Brunnen"},
                    "16004": {"name": "Pumpwerk"},
                    "16005": {"name": "Quelle"},
                    "18000": {"name": "Abwasserleitung"},
                    "18001": {"name": "Abwasserrueckhaltebecken"},
                    "18002": {"name": "Abwasserpumpwerk"},
                    "18003": {"name": "Klaeranlage"},
                    "18004": {"name": "AnlageKlaerschlamm"},
                    "18005": {"name": "SonstigeAbwasserBehandlungsanlage"},
                    "20000": {"name": "RegenwasserRueckhaltebecken"},
                    "20001": {"name": "Niederschlagswasserleitung"},
                    "22000": {"name": "Muellumladestation"},
                    "22001": {"name": "Muellbeseitigungsanlage"},
                    "22002": {"name": "Muellsortieranlage"},
                    "22003": {"name": "Recyclinghof"},
                    "24000": {"name": "Erdaushubdeponie"},
                    "24001": {"name": "Bauschuttdeponie"},
                    "24002": {"name": "Hausmuelldeponie"},
                    "24003": {"name": "Sondermuelldeponie"},
                    "24004": {"name": "StillgelegteDeponie"},
                    "24005": {"name": "RekultivierteDeponie"},
                    "26000": {"name": "Fernmeldeanlage"},
                    "26001": {"name": "Mobilfunkstrecke"},
                    "26002": {"name": "Fernmeldekabel"},
                    "28000": {"name": "Windenergie"},
                    "28001": {"name": "Photovoltaik"},
                    "28002": {"name": "Biomasse"},
                    "28003": {"name": "Geothermie"},
                    "28004": {"name": "SonstErneuerbareEnergie"},
                    "99990": {"name": "Produktenleitung"},
                },
            },
        ),
    ] = None
    weitereBesondZweckbestimmung1: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "10006",
            "10007",
            "10008",
            "10009",
            "10010",
            "12000",
            "12001",
            "12002",
            "12003",
            "12004",
            "12005",
            "13000",
            "13001",
            "13002",
            "13003",
            "14000",
            "14001",
            "14002",
            "16000",
            "16001",
            "16002",
            "16003",
            "16004",
            "16005",
            "18000",
            "18001",
            "18002",
            "18003",
            "18004",
            "18005",
            "20000",
            "20001",
            "22000",
            "22001",
            "22002",
            "22003",
            "24000",
            "24001",
            "24002",
            "24003",
            "24004",
            "24005",
            "26000",
            "26001",
            "26002",
            "28000",
            "28001",
            "28002",
            "28003",
            "28004",
            "99990",
        ]
        | None,
        Field(
            description='Weitere besondere Zweckbestimmung der Fläche, die die zugehörige allgemeine Zweckbestimmung detailliert oder ersetzt.  Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {"name": "Hochspannungsleitung"},
                    "10001": {"name": "TrafostationUmspannwerk"},
                    "10002": {"name": "Solarkraftwerk"},
                    "10003": {"name": "Windkraftwerk"},
                    "10004": {"name": "Geothermiekraftwerk"},
                    "10005": {"name": "Elektrizitaetswerk"},
                    "10006": {"name": "Wasserkraftwerk"},
                    "10007": {"name": "BiomasseKraftwerk"},
                    "10008": {"name": "Kabelleitung"},
                    "10009": {"name": "Niederspannungsleitung"},
                    "10010": {"name": "Leitungsmast"},
                    "12000": {"name": "Ferngasleitung"},
                    "12001": {"name": "Gaswerk"},
                    "12002": {"name": "Gasbehaelter"},
                    "12003": {"name": "Gasdruckregler"},
                    "12004": {"name": "Gasstation"},
                    "12005": {"name": "Gasleitung"},
                    "13000": {"name": "Erdoelleitung"},
                    "13001": {"name": "Bohrstelle"},
                    "13002": {"name": "Erdoelpumpstation"},
                    "13003": {"name": "Oeltank"},
                    "14000": {"name": "Blockheizkraftwerk"},
                    "14001": {"name": "Fernwaermeleitung"},
                    "14002": {"name": "Fernheizwerk"},
                    "16000": {"name": "Wasserwerk"},
                    "16001": {"name": "Wasserleitung"},
                    "16002": {"name": "Wasserspeicher"},
                    "16003": {"name": "Brunnen"},
                    "16004": {"name": "Pumpwerk"},
                    "16005": {"name": "Quelle"},
                    "18000": {"name": "Abwasserleitung"},
                    "18001": {"name": "Abwasserrueckhaltebecken"},
                    "18002": {"name": "Abwasserpumpwerk"},
                    "18003": {"name": "Klaeranlage"},
                    "18004": {"name": "AnlageKlaerschlamm"},
                    "18005": {"name": "SonstigeAbwasserBehandlungsanlage"},
                    "20000": {"name": "RegenwasserRueckhaltebecken"},
                    "20001": {"name": "Niederschlagswasserleitung"},
                    "22000": {"name": "Muellumladestation"},
                    "22001": {"name": "Muellbeseitigungsanlage"},
                    "22002": {"name": "Muellsortieranlage"},
                    "22003": {"name": "Recyclinghof"},
                    "24000": {"name": "Erdaushubdeponie"},
                    "24001": {"name": "Bauschuttdeponie"},
                    "24002": {"name": "Hausmuelldeponie"},
                    "24003": {"name": "Sondermuelldeponie"},
                    "24004": {"name": "StillgelegteDeponie"},
                    "24005": {"name": "RekultivierteDeponie"},
                    "26000": {"name": "Fernmeldeanlage"},
                    "26001": {"name": "Mobilfunkstrecke"},
                    "26002": {"name": "Fernmeldekabel"},
                    "28000": {"name": "Windenergie"},
                    "28001": {"name": "Photovoltaik"},
                    "28002": {"name": "Biomasse"},
                    "28003": {"name": "Geothermie"},
                    "28004": {"name": "SonstErneuerbareEnergie"},
                    "99990": {"name": "Produktenleitung"},
                },
                "typename": "XP_BesondereZweckbestimmungVerEntsorgung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereBesondZweckbestimmung2: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "10006",
            "10007",
            "10008",
            "10009",
            "10010",
            "12000",
            "12001",
            "12002",
            "12003",
            "12004",
            "12005",
            "13000",
            "13001",
            "13002",
            "13003",
            "14000",
            "14001",
            "14002",
            "16000",
            "16001",
            "16002",
            "16003",
            "16004",
            "16005",
            "18000",
            "18001",
            "18002",
            "18003",
            "18004",
            "18005",
            "20000",
            "20001",
            "22000",
            "22001",
            "22002",
            "22003",
            "24000",
            "24001",
            "24002",
            "24003",
            "24004",
            "24005",
            "26000",
            "26001",
            "26002",
            "28000",
            "28001",
            "28002",
            "28003",
            "28004",
            "99990",
        ]
        | None,
        Field(
            description='Weitere besondere Zweckbestimmung der Fläche, die die zugehörige allgemeine Zweckbestimmung detailliert oder ersetzt. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {"name": "Hochspannungsleitung"},
                    "10001": {"name": "TrafostationUmspannwerk"},
                    "10002": {"name": "Solarkraftwerk"},
                    "10003": {"name": "Windkraftwerk"},
                    "10004": {"name": "Geothermiekraftwerk"},
                    "10005": {"name": "Elektrizitaetswerk"},
                    "10006": {"name": "Wasserkraftwerk"},
                    "10007": {"name": "BiomasseKraftwerk"},
                    "10008": {"name": "Kabelleitung"},
                    "10009": {"name": "Niederspannungsleitung"},
                    "10010": {"name": "Leitungsmast"},
                    "12000": {"name": "Ferngasleitung"},
                    "12001": {"name": "Gaswerk"},
                    "12002": {"name": "Gasbehaelter"},
                    "12003": {"name": "Gasdruckregler"},
                    "12004": {"name": "Gasstation"},
                    "12005": {"name": "Gasleitung"},
                    "13000": {"name": "Erdoelleitung"},
                    "13001": {"name": "Bohrstelle"},
                    "13002": {"name": "Erdoelpumpstation"},
                    "13003": {"name": "Oeltank"},
                    "14000": {"name": "Blockheizkraftwerk"},
                    "14001": {"name": "Fernwaermeleitung"},
                    "14002": {"name": "Fernheizwerk"},
                    "16000": {"name": "Wasserwerk"},
                    "16001": {"name": "Wasserleitung"},
                    "16002": {"name": "Wasserspeicher"},
                    "16003": {"name": "Brunnen"},
                    "16004": {"name": "Pumpwerk"},
                    "16005": {"name": "Quelle"},
                    "18000": {"name": "Abwasserleitung"},
                    "18001": {"name": "Abwasserrueckhaltebecken"},
                    "18002": {"name": "Abwasserpumpwerk"},
                    "18003": {"name": "Klaeranlage"},
                    "18004": {"name": "AnlageKlaerschlamm"},
                    "18005": {"name": "SonstigeAbwasserBehandlungsanlage"},
                    "20000": {"name": "RegenwasserRueckhaltebecken"},
                    "20001": {"name": "Niederschlagswasserleitung"},
                    "22000": {"name": "Muellumladestation"},
                    "22001": {"name": "Muellbeseitigungsanlage"},
                    "22002": {"name": "Muellsortieranlage"},
                    "22003": {"name": "Recyclinghof"},
                    "24000": {"name": "Erdaushubdeponie"},
                    "24001": {"name": "Bauschuttdeponie"},
                    "24002": {"name": "Hausmuelldeponie"},
                    "24003": {"name": "Sondermuelldeponie"},
                    "24004": {"name": "StillgelegteDeponie"},
                    "24005": {"name": "RekultivierteDeponie"},
                    "26000": {"name": "Fernmeldeanlage"},
                    "26001": {"name": "Mobilfunkstrecke"},
                    "26002": {"name": "Fernmeldekabel"},
                    "28000": {"name": "Windenergie"},
                    "28001": {"name": "Photovoltaik"},
                    "28002": {"name": "Biomasse"},
                    "28003": {"name": "Geothermie"},
                    "28004": {"name": "SonstErneuerbareEnergie"},
                    "99990": {"name": "Produktenleitung"},
                },
                "typename": "XP_BesondereZweckbestimmungVerEntsorgung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereBesondZweckbestimmung3: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "10006",
            "10007",
            "10008",
            "10009",
            "10010",
            "12000",
            "12001",
            "12002",
            "12003",
            "12004",
            "12005",
            "13000",
            "13001",
            "13002",
            "13003",
            "14000",
            "14001",
            "14002",
            "16000",
            "16001",
            "16002",
            "16003",
            "16004",
            "16005",
            "18000",
            "18001",
            "18002",
            "18003",
            "18004",
            "18005",
            "20000",
            "20001",
            "22000",
            "22001",
            "22002",
            "22003",
            "24000",
            "24001",
            "24002",
            "24003",
            "24004",
            "24005",
            "26000",
            "26001",
            "26002",
            "28000",
            "28001",
            "28002",
            "28003",
            "28004",
            "99990",
        ]
        | None,
        Field(
            description='Weitere besondere Zweckbestimmung der Fläche, die die zugehörige allgemeine Zweckbestimmung detailliert oder ersetzt. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {"name": "Hochspannungsleitung"},
                    "10001": {"name": "TrafostationUmspannwerk"},
                    "10002": {"name": "Solarkraftwerk"},
                    "10003": {"name": "Windkraftwerk"},
                    "10004": {"name": "Geothermiekraftwerk"},
                    "10005": {"name": "Elektrizitaetswerk"},
                    "10006": {"name": "Wasserkraftwerk"},
                    "10007": {"name": "BiomasseKraftwerk"},
                    "10008": {"name": "Kabelleitung"},
                    "10009": {"name": "Niederspannungsleitung"},
                    "10010": {"name": "Leitungsmast"},
                    "12000": {"name": "Ferngasleitung"},
                    "12001": {"name": "Gaswerk"},
                    "12002": {"name": "Gasbehaelter"},
                    "12003": {"name": "Gasdruckregler"},
                    "12004": {"name": "Gasstation"},
                    "12005": {"name": "Gasleitung"},
                    "13000": {"name": "Erdoelleitung"},
                    "13001": {"name": "Bohrstelle"},
                    "13002": {"name": "Erdoelpumpstation"},
                    "13003": {"name": "Oeltank"},
                    "14000": {"name": "Blockheizkraftwerk"},
                    "14001": {"name": "Fernwaermeleitung"},
                    "14002": {"name": "Fernheizwerk"},
                    "16000": {"name": "Wasserwerk"},
                    "16001": {"name": "Wasserleitung"},
                    "16002": {"name": "Wasserspeicher"},
                    "16003": {"name": "Brunnen"},
                    "16004": {"name": "Pumpwerk"},
                    "16005": {"name": "Quelle"},
                    "18000": {"name": "Abwasserleitung"},
                    "18001": {"name": "Abwasserrueckhaltebecken"},
                    "18002": {"name": "Abwasserpumpwerk"},
                    "18003": {"name": "Klaeranlage"},
                    "18004": {"name": "AnlageKlaerschlamm"},
                    "18005": {"name": "SonstigeAbwasserBehandlungsanlage"},
                    "20000": {"name": "RegenwasserRueckhaltebecken"},
                    "20001": {"name": "Niederschlagswasserleitung"},
                    "22000": {"name": "Muellumladestation"},
                    "22001": {"name": "Muellbeseitigungsanlage"},
                    "22002": {"name": "Muellsortieranlage"},
                    "22003": {"name": "Recyclinghof"},
                    "24000": {"name": "Erdaushubdeponie"},
                    "24001": {"name": "Bauschuttdeponie"},
                    "24002": {"name": "Hausmuelldeponie"},
                    "24003": {"name": "Sondermuelldeponie"},
                    "24004": {"name": "StillgelegteDeponie"},
                    "24005": {"name": "RekultivierteDeponie"},
                    "26000": {"name": "Fernmeldeanlage"},
                    "26001": {"name": "Mobilfunkstrecke"},
                    "26002": {"name": "Fernmeldekabel"},
                    "28000": {"name": "Windenergie"},
                    "28001": {"name": "Photovoltaik"},
                    "28002": {"name": "Biomasse"},
                    "28003": {"name": "Geothermie"},
                    "28004": {"name": "SonstErneuerbareEnergie"},
                    "99990": {"name": "Produktenleitung"},
                },
                "typename": "XP_BesondereZweckbestimmungVerEntsorgung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteZweckbestimmung: Annotated[
        list[AnyUrl] | None,
        Field(
            description="Über eine CodeList definierte zusätzliche Zweckbestimmungen.",
            json_schema_extra={
                "typename": "FP_DetailZweckbestVerEntsorgung",
                "stereotype": "Codelist",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung1: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "FP_DetailZweckbestVerEntsorgung",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung2: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "FP_DetailZweckbestVerEntsorgung",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung3: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "FP_DetailZweckbestVerEntsorgung",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    textlicheErgaenzung: Annotated[
        str | None,
        Field(
            description="Textliche Ergänzung der Flächenazusweisung.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class FPVorbehalteFlaeche(FPFlaechenobjekt):
    """false"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    vorbehalt: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            }
        ),
    ] = None


class FPWaldFlaeche(FPFlaechenschlussobjekt):
    """Darstellung von Waldflächen nach §5, Abs. 2, Nr. 9b,"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    zweckbestimmung: Annotated[
        list[Literal["1000", "1200", "1400", "1600", "1800", "9999"]] | None,
        Field(
            description="Zweckbestimmungen der Waldfläche.",
            json_schema_extra={
                "typename": "XP_ZweckbestimmungWald",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Naturwald"},
                    "1200": {"name": "Nutzwald"},
                    "1400": {"name": "Erholungswald", "description": "Erholungswald"},
                    "1600": {"name": "Schutzwald", "description": "Schutzwald"},
                    "1800": {"name": "FlaecheForstwirtschaft"},
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
            },
        ),
    ] = None
    weitereZweckbestimmung1: Annotated[
        Literal["1000", "1200", "1400", "1600", "1800", "9999"] | None,
        Field(
            description='Weitere Zweckbestimmung der Waldfläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Naturwald"},
                    "1200": {"name": "Nutzwald"},
                    "1400": {"name": "Erholungswald", "description": "Erholungswald"},
                    "1600": {"name": "Schutzwald", "description": "Schutzwald"},
                    "1800": {"name": "FlaecheForstwirtschaft"},
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungWald",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung2: Annotated[
        Literal["1000", "1200", "1400", "1600", "1800", "9999"] | None,
        Field(
            description='Weitere Zweckbestimmung der Waldfläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Naturwald"},
                    "1200": {"name": "Nutzwald"},
                    "1400": {"name": "Erholungswald", "description": "Erholungswald"},
                    "1600": {"name": "Schutzwald", "description": "Schutzwald"},
                    "1800": {"name": "FlaecheForstwirtschaft"},
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungWald",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteZweckbestimmung: Annotated[
        list[AnyUrl] | None,
        Field(
            description="Über eine CodeList definierte zusätzliche Zweckbestimmungen.",
            json_schema_extra={
                "typename": "FP_DetailZweckbestWaldFlaeche",
                "stereotype": "Codelist",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung1: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "FP_DetailZweckbestWaldFlaeche",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung2: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "FP_DetailZweckbestWaldFlaeche",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class FPWasserwirtschaft(FPGeometrieobjekt):
    """Flächen für den vorbeugenden Hochwassersachutz  (§5, Abs. 2, Nr. 7 BauGB)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    zweckbestimmung: Annotated[
        Literal["1000", "1100", "1200", "1300", "9999"] | None,
        Field(
            description="Zweckbestimmung des Objektes",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "HochwasserRueckhaltebecken",
                        "description": "Hochwasser-Rückhaltebecken",
                    },
                    "1100": {
                        "name": "Ueberschwemmgebiet",
                        "description": "Überschwemmungs-gefährdetes Gebiet",
                    },
                    "1200": {"name": "Versickerungsflaeche"},
                    "1300": {"name": "Entwaesserungsgraben"},
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstige Zweckbestimmung",
                    },
                },
                "typename": "XP_ZweckbestimmungWasserwirtschaft",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteZweckbestimmung: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definierte zusätzliche Zweckbestimmung des Objektes.",
            json_schema_extra={
                "typename": "FP_DetailZweckbestWasserwirtschaft",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class FPZentralerVersorgungsbereich(FPUeberlagerungsobjekt):
    """Darstellung nach § 5 Abs. 2 Nr. 2d (Ausstattung des Gemeindegebietes mit zentralen Versorgungsbereichen)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    auspraegung: Annotated[
        AnyUrl | None,
        Field(
            json_schema_extra={
                "typename": "FP_ZentralerVersorgungsbereichAuspraegung",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            }
        ),
    ] = None


class LPFlaechenobjekt(LPObjekt):
    """Basisklasse für alle Objekte eines Landschaftsplans mit flächenhaftem Raumbezug (eine Einzelfläche oder eine Menge von Flächen, die sich nicht überlappen dürfen)."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Polygon | definitions.MultiPolygon,
        Field(
            description="Flächenhafter Raumbezug des Objektes (Eine Einzelfläche oder eine Menge von Flächen, die sich nicht überlappen dürfen). .",
            json_schema_extra={
                "typename": "XP_Flaechengeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class LPGeometrieobjekt(LPObjekt):
    """Basisklasse für alle Objekte eines Landschaftsplans mit variablem Raumbezug. Ein konkretes Objekt muss entweder punktförmigen, linienförmigen oder flächenhaften Raumbezug haben, gemischte Geometrie ist nicht zugelassen."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Point
        | definitions.MultiPoint
        | definitions.Line
        | definitions.MultiLine
        | definitions.Polygon
        | definitions.MultiPolygon,
        Field(
            description="Raumbezug - Entweder punktförmig, linienförmig oder flächenhaft, gemischte Geometrie ist nicht zugelassen.",
            json_schema_extra={
                "typename": "XP_VariableGeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class LPLandschaftsbild(LPGeometrieobjekt):
    """Festlegung, Darstellung bzw. Festsetzung zum Landschaftsbild in einem  landschaftsplanerischen Planwerk."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    massnahme: Annotated[
        AnyUrl | None,
        Field(
            description="Spezifizierung einer Massnahme zum Landschaftsbild.",
            json_schema_extra={
                "typename": "LP_MassnahmeLandschaftsbild",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class LPLinienobjekt(LPObjekt):
    """Basisklasse für alle Objekte eines Landschaftsplans mit linienförmigem Raumbezug (eine einzelne zusammenhängende Kurve, die aus Linienstücken und Kreisbögen zusammengesetzt sein kann, oder eine Menge derartiger Kurven)."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Line | definitions.MultiLine,
        Field(
            description="Linienförmiger Raumbezug (Einzelne zusammenhängende Kurve, die aus Linienstücken und Kreisbögen aufgebaut sit, oder eine Menge derartiger Kurven),",
            json_schema_extra={
                "typename": "XP_Liniengeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class LPNutzungsAusschluss(LPGeometrieobjekt):
    """Flächen und Objekte die bestimmte geplante oder absehbare Nutzungsänderungen nicht erfahren sollen."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    auszuschliessendeNutzungen: Annotated[
        str | None,
        Field(
            description="Auszuschließende Nutzungen (Textform).",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    auszuschliessendeNutzungenKuerzel: Annotated[
        str | None,
        Field(
            description="Auszuschließende Nutzungen (Kürzel).",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    begruendung: Annotated[
        str | None,
        Field(
            description="Begründung des Ausschlusses (Textform).",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    begruendungKuerzel: Annotated[
        str | None,
        Field(
            description="Begründung des Ausschlusses (Kürzel)",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class LPNutzungserfordernisRegelung(LPGeometrieobjekt):
    """Flächen mit Nutzungserfordernissen und Nutzungsregelungen zum Schutz, zur Pflege und zur Entwicklung von Natur und Landschaft."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    ziel: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"] | None,
        Field(
            description='Unterscheidung nach den Zielen "Schutz, Pflege" und "Entwicklung".',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "SchutzPflege"},
                    "2000": {"name": "Entwicklung"},
                    "3000": {"name": "Anlage"},
                    "4000": {"name": "SchutzPflegeEntwicklung"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "XP_SPEZiele",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    regelung: Annotated[
        Literal["1000", "9999"] | None,
        Field(
            description="Nutzungsregelung (Klassifikation).",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Gruenlandumbruchverbot"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "LP_Regelungen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    erfordernisRegelung: Annotated[
        str | None,
        Field(
            description="Nutzungserfordernis oder -Regelung (Textform).",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    erfordernisRegelungKuerzel: Annotated[
        str | None,
        Field(
            description="Nutzungserfordernis oder -Regelung (Kürzel).",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class LPPlanerischeVertiefung(LPGeometrieobjekt):
    """Bereiche, die einer planerischen Vertiefung bedürfen."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    vertiefung: Annotated[
        str | None,
        Field(
            description="Textliche Formulierung der Vertiefung",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class LPSchutzPflegeEntwicklung(LPGeometrieobjekt):
    """Sonstige Flächen und Maßnahmen zum Schutz, zur Pflege und zur Entwicklung von Natur und Landschaft, soweit sie nicht durch die Klasse LP_NutzungserfordernisRegelung modelliert werden."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    ziel: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"] | None,
        Field(
            description='Unterscheidung nach den Zielen "Schutz, Pflege" und "Entwicklung".',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "SchutzPflege"},
                    "2000": {"name": "Entwicklung"},
                    "3000": {"name": "Anlage"},
                    "4000": {"name": "SchutzPflegeEntwicklung"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "XP_SPEZiele",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    massnahme: Annotated[
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
            "2200",
            "2300",
            "9999",
        ]
        | None,
        Field(
            description="Durchzuführende Maßnahme (Klassifikation).",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "ArtentreicherGehoelzbestand"},
                    "1100": {"name": "NaturnaherWald"},
                    "1200": {"name": "ExtensivesGruenland"},
                    "1300": {"name": "Feuchtgruenland"},
                    "1400": {"name": "Obstwiese"},
                    "1500": {"name": "NaturnaherUferbereich"},
                    "1600": {"name": "Roehrichtzone"},
                    "1700": {"name": "Ackerrandstreifen"},
                    "1800": {"name": "Ackerbrache"},
                    "1900": {"name": "Gruenlandbrache"},
                    "2000": {"name": "Sukzessionsflaeche"},
                    "2100": {"name": "Hochstaudenflur"},
                    "2200": {"name": "Trockenrasen"},
                    "2300": {"name": "Heide"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "XP_SPEMassnahmenTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    massnahmeText: Annotated[
        str | None,
        Field(
            description="Durchzuführende Maßnahme (Textform).",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    massnahmeKuerzel: Annotated[
        str | None,
        Field(
            description="Kürzel der durchzuführenden Maßnahme.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    istAusgleich: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob die Maßnahme zum Ausgleich von Eingriffen genutzt wird.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False


class LPSchutzobjektBundesrecht(LPGeometrieobjekt):
    """Schutzgebiete und Schutzobjekte nach Naturschutzrecht im Sinne des 4. Abschnittes des BNatSchG."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    typ: Annotated[
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
        ]
        | None,
        Field(
            description="Typ des Schutzgebietes.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Naturschutzgebiet"},
                    "1100": {"name": "Nationalpark"},
                    "1200": {"name": "Biosphaerenreservat"},
                    "1300": {"name": "Landschaftsschutzgebiet"},
                    "1400": {"name": "Naturpark"},
                    "1500": {"name": "Naturdenkmal"},
                    "1600": {"name": "GeschuetzterLandschaftsBestandteil"},
                    "1700": {"name": "GesetzlichGeschuetztesBiotop"},
                    "1800": {"name": "GebietGemeinschaftlicherBedeutung"},
                    "1900": {"name": "EuropaeischesVogelschutzgebiet"},
                },
                "typename": "LP_ZweckbestimmungSchutzgebiet",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    eigenname: Annotated[
        str | None,
        Field(
            description="Eigennahme des Schutzgebietes.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class LPSchutzobjektInternatRecht(LPGeometrieobjekt):
    """Sonstige Schutzgebiete und Schutzobjekte nach internationalem Recht."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    typ: Annotated[
        Literal["1000", "2000", "9999"] | None,
        Field(
            description="Typ der Schutzgebietes.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Feuchtgebiet"},
                    "2000": {"name": "VogelschutzgebietInternat"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "LP_InternatSchutzobjektTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    sonstTyp: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definierter zusätzlicher Typ des Schutzgebietes",
            json_schema_extra={
                "typename": "LP_InternatSchutzobjektDetailTypen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    eigenname: Annotated[
        str | None,
        Field(
            description="Eigennahme des Schutzgebietes.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class LPSchutzobjektLandesrecht(LPGeometrieobjekt):
    """Sonstige Schutzgebiete und Schutzobjekte nach Landesrecht."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    detailTyp: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definierter Typ des Schutzobjektes.",
            json_schema_extra={
                "typename": "LP_SchutzobjektLandesrechtDetailTypen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class LPSonstigesRecht(LPGeometrieobjekt):
    """Gebiete und Gebietsteile mit rechtlichen Bindungen nach anderen Fachgesetzen (soweit sie für den Schutz, die Pflege und die Entwicklung von Natur und Landschaft bedeutsam sind). Hier: Sonstige Flächen und Gebiete (z.B. nach Jagdrecht)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    typ: Annotated[
        Literal["1000", "2000", "9999"] | None,
        Field(
            description="Typ des Schutzobjektes.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Jagdgesetz"},
                    "2000": {"name": "Fischereigesetz"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "LP_SonstRechtTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detailTyp: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definierter zusätzlicher Typ des Schutzobjektes.",
            json_schema_extra={
                "typename": "LP_SonstRechtDetailTypen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class LPTextlicheFestsetzungsFlaeche(LPFlaechenobjekt):
    """Bereich in dem bestimmte textliche Festsetzungen gültig sind, die über die Relation "refTextInhalt" (Basisklasse XP_Objekt) spezifiziert werden."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class LPWasserrechtGemeingebrEinschraenkungNaturschutz(LPGeometrieobjekt):
    """Gebiete und Gebietsteile mit rechtlichen Bindungen nach anderen Fachgesetzen (soweit sie für den Schutz, die Pflege und die Entwicklung von Natur und Landschaft bedeutsam sind). Hier: Flächen mit Einschränkungen des wasserrechtlichen Gemeingebrauchs aus Gründen des Naturschutzes."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    detailTyp: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definierter Typ des Schutzobjektes.",
            json_schema_extra={
                "typename": "LP_WasserrechtGemeingebrEinschraenkungNaturschutzDetailTypen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class LPWasserrechtSchutzgebiet(LPGeometrieobjekt):
    """false"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    typ: Annotated[
        Literal["1000", "2000", "3000", "9999"] | None,
        Field(
            description="Typ des Schutzobjektes.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "GrundQuellwasser"},
                    "2000": {"name": "Oberflaechengewaesser"},
                    "3000": {"name": "Heilquellen"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "LP_WasserrechtSchutzgebietTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detailTyp: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definierter zusätzlicher Typ des Schutzobjektes.",
            json_schema_extra={
                "typename": "LP_WasserrechtSchutzgebietDetailTypen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    eigenname: Annotated[
        str | None,
        Field(
            description="Eigennahme des Schutzgebietes.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class LPWasserrechtSonstige(LPGeometrieobjekt):
    """Gebiete und Gebietsteile mit rechtlichen Bindungen nach anderen Fachgesetzen (soweit sie für den Schutz, die Pflege und die Entwicklung von Natur und Landschaft bedeutsam sind). Hier: Sonstige wasserrechtliche Flächen."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    typ: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definierter Typ des Schutzobjektes.",
            json_schema_extra={
                "typename": "LP_WasserrechtSonstigeTypen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class LPWasserrechtWirtschaftAbflussHochwSchutz(LPGeometrieobjekt):
    """Gebiete und Gebietsteile mit rechtlichen Bindungen nach anderen Fachgesetzen (soweit sie für den Schutz, die Pflege und die Entwicklung von Natur und Landschaft bedeutsam sind). Hier: Flächen für die Wasserwirtschaft, den Hochwasserschutz und die Regelung des Wasserabflusses nach dem Wasserhaushaltsgesetz."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    typ: Annotated[
        Literal["1000", "2000", "9999"] | None,
        Field(
            description="Typ des Schutzobjektes.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Hochwasserrueckhaltebecken"},
                    "2000": {"name": "UeberschwemmGebiet"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "LP_WasserrechtWirtschaftAbflussHochwSchutzTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detailTyp: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definierter zusätzlicher Typ des Schutzobjektes.",
            json_schema_extra={
                "typename": "LP_WasserrechtWirtschaftAbflussHochwSchutzDetailTypen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class LPZuBegruenendeGrundstueckflaeche(LPFlaechenobjekt):
    """Zu begrünende Grundstücksfläche"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gaertnerischanzulegen: Annotated[
        bool | None,
        Field(
            description="Angabe in wie weit ein Grünfläche gärtnerish anzulegen ist.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gruenflaechenFaktor: Annotated[
        float | None,
        Field(
            description="Angabe des Verhältnisses zwischen einem Flächenanteil Grün und einer bebauten Fläche (auch als Biotopflächenfaktor bekannt)",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class LPZwischennutzung(LPGeometrieobjekt):
    """Flächen und Maßnahmen mit zeitlich befristeten Bindungen zum Schutz, zur Pflege und zur Entwicklung von Natur und Landschaft ("Zwischennutzungsvorgaben")."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    ziel: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"] | None,
        Field(
            description='Unterscheidung nach den Zielen "Schutz, Pflege" und "Entwicklung".',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "SchutzPflege"},
                    "2000": {"name": "Entwicklung"},
                    "3000": {"name": "Anlage"},
                    "4000": {"name": "SchutzPflegeEntwicklung"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "XP_SPEZiele",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    bindung: Annotated[
        str | None,
        Field(
            description="Beschreibung der Bindung (Textform).",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    bindungKuerzel: Annotated[
        str | None,
        Field(
            description="Beschreibung der Bindung (Kürzel).",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class RPFlaechenobjekt(RPObjekt):
    """Basisklasse für alle Objekte eines Regionalplans mit flächenhaftem Raumbezug (eine Einzelfläche oder eine Menge von Flächen, die sich nicht überlappen dürfen)."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Polygon | definitions.MultiPolygon,
        Field(
            description="Flächenförmiger Raumbezug.",
            json_schema_extra={
                "typename": "XP_Flaechengeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class RPGeometrieobjekt(RPObjekt):
    """Basisklasse für alle Objekte eines Regionalplans mit variablem Raumbezug. Ein konkretes Objekt muss entweder punktförmigen, linienförmigen oder flächenhaften Raumbezug haben, gemischte Geometrie ist nicht zugelassen."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Point
        | definitions.MultiPoint
        | definitions.Line
        | definitions.MultiLine
        | definitions.Polygon
        | definitions.MultiPolygon,
        Field(
            description="Variabler Raumbezug.",
            json_schema_extra={
                "typename": "XP_VariableGeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class RPGewaesser(RPGeometrieobjekt):
    """Gewässer"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    istAusgleichsgebiet: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob es sich um ein Ausgleichsgebiet handelt.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False


class RPGrenze(RPGeometrieobjekt):
    """Grenzen"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    typ: Annotated[
        Literal[
            "1000",
            "1100",
            "1200",
            "1250",
            "1300",
            "1400",
            "1450",
            "1500",
            "1510",
            "1550",
            "1600",
            "2000",
            "2100",
            "9999",
        ]
        | None,
        Field(
            description="Typ der Grenze",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Bundesgrenze"},
                    "1100": {"name": "Landesgrenze"},
                    "1200": {"name": "Regierungsbezirksgrenze"},
                    "1250": {"name": "Bezirksgrenze"},
                    "1300": {"name": "Kreisgrenze"},
                    "1400": {"name": "Gemeindegrenze"},
                    "1450": {"name": "Verbandsgemeindegrenze"},
                    "1500": {"name": "Samtgemeindegrenze"},
                    "1510": {"name": "Mitgliedsgemeindegrenze"},
                    "1550": {"name": "Amtsgrenze"},
                    "1600": {"name": "Stadtteilgrenze"},
                    "2000": {
                        "name": "VorgeschlageneGrundstuecksgrenze",
                        "description": "Hinweis auf eine vorgeschlagene Grundstücksgrenze im BPlan.",
                    },
                    "2100": {
                        "name": "GrenzeBestehenderBebauungsplan",
                        "description": "Hinweis auf den Geltungsbereich eines bestehenden BPlan.",
                    },
                    "9999": {"name": "SonstGrenze"},
                },
                "typename": "XP_GrenzeTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    sonstTyp: Annotated[
        AnyUrl | None,
        Field(
            description="ErweiterterTtyp.",
            json_schema_extra={
                "typename": "RP_SonstGrenzeTypen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class RPGruenzugGruenzaesur(RPGeometrieobjekt):
    """Regionaler Grünzug/Grünzäsur"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gebietsTyp: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000"]] | None,
        Field(
            description="Klassifikation des Gebietes nach Bundesraumordnungsgesetz.",
            json_schema_extra={
                "typename": "RP_GebietsTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Vorranggebiet"},
                    "2000": {"name": "Vorbehaltsgebiet"},
                    "3000": {"name": "Eignungsgebiet"},
                    "4000": {"name": "Ausschlussgebiet"},
                    "5000": {"name": "SonstigesGebiet"},
                },
            },
        ),
    ] = None
    istAusgleichsgebiet: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob es sich um ein Ausgleichsgebiet handelt.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False


class RPKlimaschutz(RPGeometrieobjekt):
    """(Siedlungs-) Klimaschutz"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gebietsTyp: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000"]] | None,
        Field(
            description="Klassifikation des Gebietes nach Bundesraumordnungsgesetz.",
            json_schema_extra={
                "typename": "RP_GebietsTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Vorranggebiet"},
                    "2000": {"name": "Vorbehaltsgebiet"},
                    "3000": {"name": "Eignungsgebiet"},
                    "4000": {"name": "Ausschlussgebiet"},
                    "5000": {"name": "SonstigesGebiet"},
                },
            },
        ),
    ] = None
    istAusgleichsgebiet: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob es sich um ein Ausgleichsgebiet handelt.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False


class RPKommunikation(RPGeometrieobjekt):
    """Infrastruktur zur Telekommunikation"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gebietsTyp: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000"]] | None,
        Field(
            description="Klassifikation des Gebietes nach Bundesraumordnungsgesetz.",
            json_schema_extra={
                "typename": "RP_GebietsTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Vorranggebiet"},
                    "2000": {"name": "Vorbehaltsgebiet"},
                    "3000": {"name": "Eignungsgebiet"},
                    "4000": {"name": "Ausschlussgebiet"},
                    "5000": {"name": "SonstigesGebiet"},
                },
            },
        ),
    ] = None


class RPKulturellesSachgut(RPGeometrieobjekt):
    """Kulturelles Sachgut"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gebietsTyp: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000"]] | None,
        Field(
            description="Klassifikation des Gebietes nach Bundesraumordnungsgesetz.",
            json_schema_extra={
                "typename": "RP_GebietsTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Vorranggebiet"},
                    "2000": {"name": "Vorbehaltsgebiet"},
                    "3000": {"name": "Eignungsgebiet"},
                    "4000": {"name": "Ausschlussgebiet"},
                    "5000": {"name": "SonstigesGebiet"},
                },
            },
        ),
    ] = None
    istAusgleichsgebiet: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob es sich um ein Ausgleichsgebiet handelt.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False


class RPLandwirtschaft(RPGeometrieobjekt):
    """Landwirtschaft"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gebietsTyp: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000"]] | None,
        Field(
            description="Klassifikation des Gebietes nach Bundesraumordnungsgesetz.",
            json_schema_extra={
                "typename": "RP_GebietsTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Vorranggebiet"},
                    "2000": {"name": "Vorbehaltsgebiet"},
                    "3000": {"name": "Eignungsgebiet"},
                    "4000": {"name": "Ausschlussgebiet"},
                    "5000": {"name": "SonstigesGebiet"},
                },
            },
        ),
    ] = None
    istAusgleichsgebiet: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob es sich um ein Ausgleichsgebiet handelt.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False


class RPLinienobjekt(RPObjekt):
    """Basisklasse für alle Objekte eines Regionalplans mit linienförmigem Raumbezug (eine einzelne zusammenhängende Kurve, die aus Linienstücken und Kreisbögen zusammengesetzt sein kann, oder eine Menge derartiger Kurven)."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Line | definitions.MultiLine,
        Field(
            description="Linienförmiger Raumbezug.",
            json_schema_extra={
                "typename": "XP_Liniengeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            },
        ),
    ]


class RPNaturLandschaft(RPGeometrieobjekt):
    """Natur und Landschaft"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gebietsTyp: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000"]] | None,
        Field(
            description="Klassifikation des Gebietes nach Bundesraumordnungsgesetz.",
            json_schema_extra={
                "typename": "RP_GebietsTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Vorranggebiet"},
                    "2000": {"name": "Vorbehaltsgebiet"},
                    "3000": {"name": "Eignungsgebiet"},
                    "4000": {"name": "Ausschlussgebiet"},
                    "5000": {"name": "SonstigesGebiet"},
                },
            },
        ),
    ] = None
    istAusgleichsgebiet: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob es sich um ein Ausgleichsgebiet handelt.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False


class RPNaturschutzrechtlichesSchutzgebiet(RPGeometrieobjekt):
    """Schutzgebiet nach Bundes-Naturschutzgesetz"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    zweckbestimmung: Annotated[
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
            "18000",
            "18001",
            "2000",
            "9999",
        ]
        | None,
        Field(
            description="Klassifikation des Naturschutzgebietes.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Naturschutzgebiet",
                        "description": "Naturschutzgebiet",
                    },
                    "1100": {"name": "Nationalpark", "description": "Nationalpark"},
                    "1200": {
                        "name": "Biosphaerenreservat",
                        "description": "Biosphaerenreservate",
                    },
                    "1300": {
                        "name": "Landschaftsschutzgebiet",
                        "description": "Landschaftsschutzgebiet",
                    },
                    "1400": {"name": "Naturpark", "description": "Naturpark"},
                    "1500": {"name": "Naturdenkmal", "description": "Naturdenkmal"},
                    "1600": {
                        "name": "GeschuetzterLandschaftsBestandteil",
                        "description": "Geschützter Bestandteil der Landschaft",
                    },
                    "1700": {
                        "name": "GesetzlichGeschuetztesBiotop",
                        "description": "Gesetzlich geschützte Biotope",
                    },
                    "1800": {
                        "name": "Natura2000",
                        "description": 'Schutzgebiet nach Europäischem Recht. Die umfasst das "Gebiet Gemeinschaftlicher Bedeutung" (FFH-Gebiet) und das "Europäische Vogelschutzgebiet"',
                    },
                    "18000": {
                        "name": "GebietGemeinschaftlicherBedeutung",
                        "description": "Gebiete von gemeinschaftlicher Bedeutung",
                    },
                    "18001": {
                        "name": "EuropaeischesVogelschutzgebiet",
                        "description": "Europäische Vogelschutzgebiete",
                    },
                    "2000": {"name": "NationalesNaturmonument"},
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_KlassifizSchutzgebietNaturschutzrecht",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    istAusgleichsgebiet: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob es sich um ein Ausgleichsgebiet handelt.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False


class RPRaumkategorie(RPGeometrieobjekt):
    """Raumkategorien"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class RPRohstoffsicherung(RPGeometrieobjekt):
    """Rohstoffsicherung"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gebietsTyp: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000"]] | None,
        Field(
            description="Klassifikation des Gebietes nach Bundesraumordnungsgesetz.",
            json_schema_extra={
                "typename": "RP_GebietsTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Vorranggebiet"},
                    "2000": {"name": "Vorbehaltsgebiet"},
                    "3000": {"name": "Eignungsgebiet"},
                    "4000": {"name": "Ausschlussgebiet"},
                    "5000": {"name": "SonstigesGebiet"},
                },
            },
        ),
    ] = None
    abbaugut: Annotated[
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
            "2200",
            "2300",
            "2400",
            "2500",
            "2600",
            "2800",
            "2900",
            "3000",
            "3100",
            "3200",
            "3300",
            "3400",
            "3500",
            "3600",
            "3700",
            "3800",
            "3900",
            "4100",
            "4200",
            "4300",
            "4400",
            "4500",
            "4600",
            "4700",
            "4800",
            "4900",
            "5000",
            "5100",
            "5200",
            "5300",
            "5400",
            "5500",
            "5600",
            "5700",
            "5800",
            "5900",
            "6000",
            "9999",
        ]
        | None,
        Field(
            description="Abgebauter Rohstoff.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Anhydridstein"},
                    "1100": {"name": "Baryt"},
                    "1200": {"name": "BasaltDiabas"},
                    "1300": {"name": "Bentonit"},
                    "1400": {"name": "Blaehton"},
                    "1500": {"name": "Braunkohle"},
                    "1600": {"name": "Bundsandstein"},
                    "1700": {"name": "Diorit"},
                    "1800": {"name": "Dolomitstein"},
                    "1900": {"name": "Erdgas"},
                    "2000": {"name": "Erdoel"},
                    "2100": {"name": "Erz"},
                    "2200": {"name": "Feldspat"},
                    "2300": {"name": "Flussspat"},
                    "2400": {"name": "Gangquarz"},
                    "2500": {"name": "Gipsstein"},
                    "2600": {"name": "Granit"},
                    "2800": {"name": "Grauwacke"},
                    "2900": {"name": "KalkKalktuffKreide"},
                    "3000": {"name": "Kalkmergelstein"},
                    "3100": {"name": "Kalkstein"},
                    "3200": {"name": "Karbonatgestein"},
                    "3300": {"name": "KiesSand"},
                    "3400": {"name": "Kieselgur"},
                    "3500": {"name": "Kristallin"},
                    "3600": {"name": "Kupfer"},
                    "3700": {"name": "Lehm"},
                    "3800": {"name": "Mergel"},
                    "3900": {"name": "Mergelstein"},
                    "4100": {"name": "Muschelkalk"},
                    "4200": {"name": "Naturwerkstein"},
                    "4300": {"name": "Pegmatitsand"},
                    "4400": {"name": "Quarzit"},
                    "4500": {"name": "Quarzsand"},
                    "4600": {"name": "Salz"},
                    "4700": {"name": "Sand"},
                    "4800": {"name": "Sandstein"},
                    "4900": {"name": "Spezialton"},
                    "5000": {"name": "Steinkohle"},
                    "5100": {"name": "Ton"},
                    "5200": {"name": "Tonstein"},
                    "5300": {"name": "Torf"},
                    "5400": {"name": "TuffBimsstein"},
                    "5500": {"name": "Uran"},
                    "5600": {"name": "Vulkanit"},
                    "5700": {"name": "KieshaltigerSand"},
                    "5800": {"name": "Naturstein"},
                    "5900": {"name": "Oelschiefer"},
                    "6000": {"name": "Klei"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "RP_Rohstoff",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    istAusgleichsgebiet: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob es sich um ein Ausgleichsgebiet handelt.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False


class RPSonstigeInfrastruktur(RPGeometrieobjekt):
    """Sonstige Infrastruktur"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gebietsTyp: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000"]] | None,
        Field(
            description="Klassifikation des Gebietes nach Bundesraumordnungsgesetz.",
            json_schema_extra={
                "typename": "RP_GebietsTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Vorranggebiet"},
                    "2000": {"name": "Vorbehaltsgebiet"},
                    "3000": {"name": "Eignungsgebiet"},
                    "4000": {"name": "Ausschlussgebiet"},
                    "5000": {"name": "SonstigesGebiet"},
                },
            },
        ),
    ] = None


class RPSonstigeSiedlungsstruktur(RPGeometrieobjekt):
    """Sonstige Siedlungsstruktur"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gebietsTyp: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000"]] | None,
        Field(
            description="Klassifikation des Gebietes nach Bundesraumordnungsgesetz.",
            json_schema_extra={
                "typename": "RP_GebietsTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Vorranggebiet"},
                    "2000": {"name": "Vorbehaltsgebiet"},
                    "3000": {"name": "Eignungsgebiet"},
                    "4000": {"name": "Ausschlussgebiet"},
                    "5000": {"name": "SonstigesGebiet"},
                },
            },
        ),
    ] = None


class RPSonstigerFreiraumstruktur(RPGeometrieobjekt):
    """Sonstiger Freiraumschutz"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gebietsTyp: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000"]] | None,
        Field(
            description="Klassifikation des Gebietes nach Bundesraumordnungsgesetz.",
            json_schema_extra={
                "typename": "RP_GebietsTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Vorranggebiet"},
                    "2000": {"name": "Vorbehaltsgebiet"},
                    "3000": {"name": "Eignungsgebiet"},
                    "4000": {"name": "Ausschlussgebiet"},
                    "5000": {"name": "SonstigesGebiet"},
                },
            },
        ),
    ] = None
    istAusgleichsgebiet: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob es sich um ein Ausgleichsgebiet handelt.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False


class RPSozialeInfrastruktur(RPGeometrieobjekt):
    """Soziale Infrastruktur"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gebietsTyp: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000"]] | None,
        Field(
            description="Klassifikation des Gebietes nach Bundesraumordnungsgesetz.",
            json_schema_extra={
                "typename": "RP_GebietsTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Vorranggebiet"},
                    "2000": {"name": "Vorbehaltsgebiet"},
                    "3000": {"name": "Eignungsgebiet"},
                    "4000": {"name": "Ausschlussgebiet"},
                    "5000": {"name": "SonstigesGebiet"},
                },
            },
        ),
    ] = None
    typ: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"] | None,
        Field(
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Kultur"},
                    "2000": {"name": "Sozialeinrichtung"},
                    "3000": {"name": "Gesundheit"},
                    "4000": {"name": "Bildung"},
                    "9999": {"name": "SonstigeSozialeInfrastruktur"},
                },
                "typename": "RP_SozialeInfrastrukturTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            }
        ),
    ] = None


class RPSperrgebiet(RPGeometrieobjekt):
    """Sperrgebiet"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class RPVerkehr(RPGeometrieobjekt):
    """Verkehrs-Infrastruktur"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gebietsTyp: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000"]] | None,
        Field(
            description="Klassifikation des Gebietes nach Bundesraumordnungsgesetz.",
            json_schema_extra={
                "typename": "RP_GebietsTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Vorranggebiet"},
                    "2000": {"name": "Vorbehaltsgebiet"},
                    "3000": {"name": "Eignungsgebiet"},
                    "4000": {"name": "Ausschlussgebiet"},
                    "5000": {"name": "SonstigesGebiet"},
                },
            },
        ),
    ] = None
    typ: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"] | None,
        Field(
            description="Klassifikation der Verkehrs-Arten.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Schienenverkehr"},
                    "2000": {"name": "Strassenverkehr"},
                    "3000": {"name": "Luftverkehr"},
                    "4000": {"name": "Wasserverkehr"},
                    "9999": {"name": "SonstigerVerkehr"},
                },
                "typename": "RP_VerkehrTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class RPVorbHochwasserschutz(RPGeometrieobjekt):
    """Vorbeugender Hochwasserschutz"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gebietsTyp: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000"]] | None,
        Field(
            description="Klassifikation des Gebietes nach Bundesraumordnungsgesetz.",
            json_schema_extra={
                "typename": "RP_GebietsTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Vorranggebiet"},
                    "2000": {"name": "Vorbehaltsgebiet"},
                    "3000": {"name": "Eignungsgebiet"},
                    "4000": {"name": "Ausschlussgebiet"},
                    "5000": {"name": "SonstigesGebiet"},
                },
            },
        ),
    ] = None
    istAusgleichsgebiet: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob es sich um ein Ausgleichsgebiet handelt.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False


class RPWasserschutz(RPGeometrieobjekt):
    """Grund- und Oberflächenwasserschutz"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gebietsTyp: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000"]] | None,
        Field(
            description="Klassifikation des Gebietes nach Bundesraumordnungsgesetz.",
            json_schema_extra={
                "typename": "RP_GebietsTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Vorranggebiet"},
                    "2000": {"name": "Vorbehaltsgebiet"},
                    "3000": {"name": "Eignungsgebiet"},
                    "4000": {"name": "Ausschlussgebiet"},
                    "5000": {"name": "SonstigesGebiet"},
                },
            },
        ),
    ] = None
    zone: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Wasserschutzzone",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Zone_1"},
                    "2000": {"name": "Zone_2"},
                    "3000": {"name": "Zone_3"},
                },
                "typename": "RP_WasserschutzZone",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    istAusgleichsgebiet: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob es sich um ein Ausgleichsgebiet handelt.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False


class RPWasserwirtschaft(RPGeometrieobjekt):
    """Wasserwirtschaft"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gebietsTyp: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000"]] | None,
        Field(
            description="Klassifikation des Gebietes nach Bundesraumordnungsgesetz.",
            json_schema_extra={
                "typename": "RP_GebietsTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Vorranggebiet"},
                    "2000": {"name": "Vorbehaltsgebiet"},
                    "3000": {"name": "Eignungsgebiet"},
                    "4000": {"name": "Ausschlussgebiet"},
                    "5000": {"name": "SonstigesGebiet"},
                },
            },
        ),
    ] = None
    typ: Annotated[
        Literal["1000", "2000", "3000", "3500", "4000", "9999"] | None,
        Field(
            description="Klasifikation von Anlagen und EInrichtungen der Wasserwirtschaft",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Wasserleitung"},
                    "2000": {"name": "Wasserwerk"},
                    "3000": {"name": "TalsperreStaudammDeich"},
                    "3500": {"name": "TalsperreSpeicherbecken"},
                    "4000": {"name": "Rückhaltebecken"},
                    "9999": {"name": "SonstigeWasserwirtschaft"},
                },
                "typename": "RP_WasserwirtschaftTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class RPWindenergienutzung(RPGeometrieobjekt):
    """Windenergienutzung"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gebietsTyp: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000"]] | None,
        Field(
            description="Klassifikation des Gebietes nach Bundesraumordnungsgesetz.",
            json_schema_extra={
                "typename": "RP_GebietsTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Vorranggebiet"},
                    "2000": {"name": "Vorbehaltsgebiet"},
                    "3000": {"name": "Eignungsgebiet"},
                    "4000": {"name": "Ausschlussgebiet"},
                    "5000": {"name": "SonstigesGebiet"},
                },
            },
        ),
    ] = None
    istAusgleichsgebiet: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob es sich um ein Ausgleichsgebiet handelt.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False


class RPZentralerOrt(RPGeometrieobjekt):
    """Zentrale Orte"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    funktion: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"] | None,
        Field(
            description="Klassifikation von zentralen Orten.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Oberzentrum"},
                    "2000": {"name": "Mittelzentrum"},
                    "3000": {"name": "Grundzentrum"},
                    "4000": {"name": "Kleinzentrum"},
                    "9999": {"name": "SonstigeFunktion"},
                },
                "typename": "RP_ZentralerOrtFunktionen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class SOFlaechenobjekt(SOObjekt):
    """Basisklasse für alle Objekte mit flächenhaftem Raumbezug (eine Einzelfläche oder eine Menge von Flächen, die sich nicht überlappen dürfen)."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Polygon | definitions.MultiPolygon,
        Field(
            json_schema_extra={
                "typename": "XP_Flaechengeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            }
        ),
    ]
    flaechenschluss: Annotated[
        bool,
        Field(
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "1",
            }
        ),
    ]


class SOGebiet(SOFlaechenobjekt):
    """Umgrenzung eines sonstigen Gebietes nach BauGB"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gemeinde: Annotated[
        XPGemeinde | None,
        Field(
            description="Zuständige Gemeinde",
            json_schema_extra={
                "typename": "XP_Gemeinde",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gebietsArt: Annotated[
        Literal[
            "1000",
            "1100",
            "1200",
            "1300",
            "1400",
            "1500",
            "1600",
            "1999",
            "2000",
            "2100",
            "2200",
            "9999",
        ]
        | None,
        Field(
            description="Klassifikation des Gebietes nach BauGB.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Umlegungsgebiet",
                        "description": "Umlegungsgebiet (§ 45 ff BauGB).",
                    },
                    "1100": {
                        "name": "StaedtebaulicheSanierung",
                        "description": "Gebiet nach § 136 ff BauGB",
                    },
                    "1200": {
                        "name": "StaedtebaulicheEntwicklungsmassnahme",
                        "description": "Gebiet nach § 165 ff BauGB",
                    },
                    "1300": {
                        "name": "Stadtumbaugebiet",
                        "description": "Gebiet nach § 171 a-d BauGB",
                    },
                    "1400": {
                        "name": "SozialeStadt",
                        "description": "Gebiet nach § 171 e BauGB",
                    },
                    "1500": {
                        "name": "BusinessImprovementDestrict",
                        "description": "Gebiet nach §171 f BauGB",
                    },
                    "1600": {
                        "name": "HousingImprovementDestrict",
                        "description": "Gebiet nach §171 f BauGB",
                    },
                    "1999": {
                        "name": "Erhaltungsverordnung",
                        "description": "Allgemeine Erhaltungsverordnung",
                    },
                    "2000": {
                        "name": "ErhaltungsverordnungStaedebaulicheGestalt",
                        "description": "Gebiet einer Satzung nach § 172 Abs. 1.1 BauGB",
                    },
                    "2100": {
                        "name": "ErhaltungsverordnungWohnbevoelkerung",
                        "description": "Gebiet einer Satzung nach § 172 Abs. 1.2 BauGB",
                    },
                    "2200": {
                        "name": "ErhaltungsverordnungUmstrukturierung",
                        "description": "Gebiet einer Satzung nach § 172 Abs. 1.2 BauGB",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstiger Gebietstyp",
                    },
                },
                "typename": "SO_GebietsArt",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    sonstGebietsArt: Annotated[
        AnyUrl | None,
        Field(
            description="Klassifikation einer nicht auf dem BauGB, z.B. länderspezifischen Gebietsausweisung.",
            json_schema_extra={
                "typename": "SO_SonstGebietsArt",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    rechtsstandGebiet: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "9999"] | None,
        Field(
            description="Rechtsstand der Gebietsausweisung",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "VorbereitendeUntersuchung"},
                    "2000": {"name": "Aufstellung"},
                    "3000": {"name": "Festlegung"},
                    "4000": {"name": "Abgeschlossen"},
                    "5000": {"name": "Verstetigung"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "SO_RechtsstandGebietTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    sonstRechtsstandGebiet: Annotated[
        AnyUrl | None,
        Field(
            description="Sonstiger Rechtsstand der Gebietsausweisung, der nicht durch die Liset SO_AusweisungRechtscharakter wiedergegeben werden kann.",
            json_schema_extra={
                "typename": "SO_SonstRechtsstandGebietTyp",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    aufstellungsbeschhlussDatum: Annotated[
        date_aliased | None,
        Field(
            description="Datum des Aufstellungsbeschlusses",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    durchfuehrungStartDatum: Annotated[
        date_aliased | None,
        Field(
            description="Start-Datum der Durchführung",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    durchfuehrungEndDatum: Annotated[
        date_aliased | None,
        Field(
            description="End-Datum der Durchführung",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    traegerMassnahme: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            }
        ),
    ] = None


class SOGeometrieobjekt(SOObjekt):
    """Basisklasse für alle Objekte mit variablem Raumbezug. Ein konkretes Objekt muss entweder punktförmigen, linienförmigen oder flächenhaften Raumbezug haben, gemischte Geometrie ist nicht zugelassen."""

    abstract: ClassVar[bool] = True
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Point
        | definitions.MultiPoint
        | definitions.Line
        | definitions.MultiLine
        | definitions.Polygon
        | definitions.MultiPolygon,
        Field(
            json_schema_extra={
                "typename": "XP_VariableGeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            }
        ),
    ]
    flaechenschluss: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            }
        ),
    ] = False


class SOLinienobjekt(SOObjekt):
    """Basisklasse für Objekte mit linienförmigem Raumbezug (eine einzelne zusammenhängende Kurve, die aus Linienstücken und Kreisbögen zusammengesetzt sein kann, oder eine Menge derartiger Kurven)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    position: Annotated[
        definitions.Line | definitions.MultiLine,
        Field(
            json_schema_extra={
                "typename": "XP_Liniengeometrie",
                "stereotype": "Geometry",
                "multiplicity": "1",
            }
        ),
    ]


class SOLuftverkehrsrecht(SOGeometrieobjekt):
    """Festlegung nach Luftverkehrsrecht."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    artDerFestlegung: Annotated[
        Literal[
            "1000",
            "2000",
            "3000",
            "4000",
            "5000",
            "5200",
            "5400",
            "6000",
            "7000",
            "9999",
        ]
        | None,
        Field(
            description="Aufzählung der möglichen Zweckbestimmungen einer Luftverkehrs-Fläche.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Flughafen"},
                    "2000": {"name": "Landeplatz"},
                    "3000": {"name": "Segelfluggelaende"},
                    "4000": {"name": "HubschrauberLandeplatz"},
                    "5000": {"name": "Ballonstartplatz"},
                    "5200": {"name": "Haengegleiter"},
                    "5400": {"name": "Gleitsegler"},
                    "6000": {
                        "name": "Laermschutzbereich",
                        "description": "Lärmschutzbereich nach LuftVG",
                    },
                    "7000": {
                        "name": "Baubeschraenkungsbereich",
                        "description": "Höhenbeschränkung nach §12 LuftVG",
                    },
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "SO_KlassifizNachLuftverkehrsrecht",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detailArtDerFestlegung: Annotated[
        AnyUrl | None,
        Field(
            json_schema_extra={
                "typename": "SO_DetailKlassifizNachLuftverkehrsrecht",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            }
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            }
        ),
    ] = None
    nummer: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            }
        ),
    ] = None
    laermschutzzone: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Lärmschutzzone nach LuftVG",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "TagZone1"},
                    "2000": {"name": "TagZone2"},
                    "3000": {"name": "Nacht"},
                },
                "typename": "SO_LaermschutzzoneTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class SOSchienenverkehrsrecht(SOGeometrieobjekt):
    """Festlegung nach Schienenverkehrsrecht."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    artDerFestlegung: Annotated[
        Literal["1000", "1200", "1400", "9999"] | None,
        Field(
            description="Aufzählung der Zweckbestimmungen einer BAHNFLÄCHE",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Bahnanlage", "description": "Bahnanlage"},
                    "1200": {"name": "Bahnlinie", "description": "Bahnlinie"},
                    "1400": {
                        "name": "OEPNV",
                        "description": "Öffentlichen Personen Nahverkehr",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstige Zweckbestimmung",
                    },
                },
                "typename": "SO_KlassifizNachSchienenverkehrsrecht",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    besondereArtDerFestlegung: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "12000",
            "12001",
            "12002",
            "12003",
            "12004",
            "12005",
            "14000",
            "14001",
            "14002",
            "14003",
        ]
        | None,
        Field(
            description="Aufzählung der besonderen Zweckbestimmungen einer Bahnfläche ,Bahnlinie oder Bahnanlage.",
            json_schema_extra={
                "enumDescription": {
                    "10000": {"name": "DB_Bahnanlage"},
                    "10001": {"name": "Personenbahnhof"},
                    "10002": {"name": "Fernbahnhof"},
                    "10003": {"name": "Gueterbahnhof"},
                    "12000": {"name": "Personenbahnlinie"},
                    "12001": {"name": "Regionalbahn"},
                    "12002": {"name": "Kleinbahn"},
                    "12003": {"name": "Gueterbahnlinie"},
                    "12004": {"name": "WerksHafenbahn"},
                    "12005": {"name": "Seilbahn"},
                    "14000": {"name": "Strassenbahn"},
                    "14001": {"name": "UBahn"},
                    "14002": {"name": "SBahn"},
                    "14003": {"name": "OEPNV_Haltestelle"},
                },
                "typename": "SO_BesondereKlassifizNachSchienenverkehrsrecht",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detailArtDerFestlegung: Annotated[
        AnyUrl | None,
        Field(
            json_schema_extra={
                "typename": "SO_DetailKlassifizNachSchienenverkehrsrecht",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            }
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            }
        ),
    ] = None
    nummer: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            }
        ),
    ] = None


class SOSchutzgebietNaturschutzrecht(SOGeometrieobjekt):
    """Schutzgebiet nach Naturschutzrecht."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    artDerFestlegung: Annotated[
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
            "18000",
            "18001",
            "2000",
            "9999",
        ]
        | None,
        Field(
            description="Klassizizierung des Naturschutzgebietes",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Naturschutzgebiet",
                        "description": "Naturschutzgebiet",
                    },
                    "1100": {"name": "Nationalpark", "description": "Nationalpark"},
                    "1200": {
                        "name": "Biosphaerenreservat",
                        "description": "Biosphaerenreservate",
                    },
                    "1300": {
                        "name": "Landschaftsschutzgebiet",
                        "description": "Landschaftsschutzgebiet",
                    },
                    "1400": {"name": "Naturpark", "description": "Naturpark"},
                    "1500": {"name": "Naturdenkmal", "description": "Naturdenkmal"},
                    "1600": {
                        "name": "GeschuetzterLandschaftsBestandteil",
                        "description": "Geschützter Bestandteil der Landschaft",
                    },
                    "1700": {
                        "name": "GesetzlichGeschuetztesBiotop",
                        "description": "Gesetzlich geschützte Biotope",
                    },
                    "1800": {
                        "name": "Natura2000",
                        "description": 'Schutzgebiet nach Europäischem Recht. Die umfasst das "Gebiet Gemeinschaftlicher Bedeutung" (FFH-Gebiet) und das "Europäische Vogelschutzgebiet"',
                    },
                    "18000": {
                        "name": "GebietGemeinschaftlicherBedeutung",
                        "description": "Gebiete von gemeinschaftlicher Bedeutung",
                    },
                    "18001": {
                        "name": "EuropaeischesVogelschutzgebiet",
                        "description": "Europäische Vogelschutzgebiete",
                    },
                    "2000": {"name": "NationalesNaturmonument"},
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_KlassifizSchutzgebietNaturschutzrecht",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detailArtDerFestlegung: Annotated[
        AnyUrl | None,
        Field(
            description="Weitere Klassifizierung",
            json_schema_extra={
                "typename": "SO_DetailKlassifizSchutzgebietNaturschutzrecht",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    zone: Annotated[
        Literal["1000", "1100", "1200", "2000", "2100", "2200", "2300"] | None,
        Field(
            description="Klassifizierung der Schutzzone",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Schutzzone_1"},
                    "1100": {"name": "Schutzzone_2"},
                    "1200": {"name": "Schutzzone_3"},
                    "2000": {"name": "Kernzone"},
                    "2100": {"name": "Pflegezone"},
                    "2200": {"name": "Entwicklungszone"},
                    "2300": {"name": "Regenerationszone"},
                },
                "typename": "SO_SchutzzonenNaturschutzrecht",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            description="Informeller Name des Schutzgebiets",
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
            description="Amtlicher Name / Kennziffer des Gebiets.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class SOSchutzgebietSonstigesRecht(SOGeometrieobjekt):
    """Sonstige Schutzgebiete nach unterschiedlichen rechtlichen Bestimmungen."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    artDerFestlegung: Annotated[
        Literal["1000", "2000", "9999"] | None,
        Field(
            description="Klassifizierung des Schutzgebietes oder Schutzbereichs.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Laermschutzbereich",
                        "description": "Lärmschutzbereich nach anderen gesetzlichen Regelungen als dem Luftverkehrsrecht.",
                    },
                    "2000": {
                        "name": "SchutzzoneLeitungstrasse",
                        "description": "Schutzzone um eine Leitungstrasse nach Bundes-Immissionsschutzgesetz.",
                    },
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "SO_KlassifizSchutzgebietSonstRecht",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detailArtDerFestlegung: Annotated[
        AnyUrl | None,
        Field(
            description="Detaillierte Klassifizierung",
            json_schema_extra={
                "typename": "SO_DetailKlassifizSchutzgebietSonstRecht",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    zone: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description='Zugeordnete Schutzzone (wenn artDerFestlegung == 1000). Das Attribut wird als "veraltet" klassifiziert und wird zukünftig wegfallen. Lärmschutbereiche nach LuftVGsollen als SO_Luftverkehrsrecht modelliert werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "TagZone1"},
                    "2000": {"name": "TagZone2"},
                    "3000": {"name": "Nacht"},
                },
                "typename": "SO_LaermschutzzoneTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            description="Informelle Bezeichnung des Gebiets",
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
            description="Amtliche Bezeichnung / Kennziffer des Gebiets",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class SOSchutzgebietWasserrecht(SOGeometrieobjekt):
    """Schutzgebiet nach WasserSchutzGesetz (WSG) bzw. HeilQuellenSchutzGesetz (HQSG)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    artDerFestlegung: Annotated[
        Literal["1000", "10000", "10001", "2000", "9999"] | None,
        Field(
            description="Klassifizierung des Schutzgebietes",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Wasserschutzgebiet"},
                    "10000": {
                        "name": "QuellGrundwasserSchutzgebiet",
                        "description": "Ausgewiesenes Schutzgebiet für Quell- und Grundwasser",
                    },
                    "10001": {
                        "name": "OberflaechengewaesserSchutzgebiet",
                        "description": "Ausgewiesenes Schutzgebiet für Oberflächengewässer",
                    },
                    "2000": {"name": "Heilquellenschutzgebiet"},
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstige Zweckbestimmung",
                    },
                },
                "typename": "SO_KlassifizSchutzgebietWasserrecht",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detailArtDerFestlegung: Annotated[
        AnyUrl | None,
        Field(
            description="Detaillierte Klassifizierung",
            json_schema_extra={
                "typename": "SO_DetailKlassifizSchutzgebietWasserrecht",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    zone: Annotated[
        Literal["1000", "1100", "1200", "1300", "1400", "1500"] | None,
        Field(
            description="Klassifizierung der Schutzzone",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Zone_1"},
                    "1100": {"name": "Zone_2"},
                    "1200": {"name": "Zone_3"},
                    "1300": {
                        "name": "Zone_3a",
                        "description": "Zone 3a existiert nur bei Wasserschutzgebieten.",
                    },
                    "1400": {
                        "name": "Zone_3b",
                        "description": "Zone 3b existiert nur bei Wasserschutzgebieten.",
                    },
                    "1500": {
                        "name": "Zone_4",
                        "description": "Zone 4 existiert nur bei Heilquellen.",
                    },
                },
                "typename": "SO_SchutzzonenWasserrecht",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            description="Informelle Bezeichnung des Gebiets",
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
            description="Amtliche Bezeichnung / Kennziffer des Gebiets.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class SOSonstigesRecht(SOGeometrieobjekt):
    """Sonstige Festlegung."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    nummer: Annotated[
        str | None,
        Field(
            description="Amtliche Bezeichnung / Kennziffer der Festlegung",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    artDerFestlegung: Annotated[
        Literal["1000", "1100", "1200", "1300", "1400", "9999"] | None,
        Field(
            description="Grundlegende rechtliche Klassifizierung der Festlegung",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Bauschutzbereich",
                        "description": "Bauschutzbereich nach anderen Rechtsverordnungen als dem LuftVG",
                    },
                    "1100": {
                        "name": "Berggesetz",
                        "description": "Beschränkung nach Berggesetz",
                    },
                    "1200": {
                        "name": "Richtfunkverbindung",
                        "description": "Baubeschränkungen durch Richtfunkverbindungen",
                    },
                    "1300": {"name": "Truppenuebungsplatz"},
                    "1400": {
                        "name": "VermessungsKatasterrecht",
                        "description": "Beschränkungen nach Vermessungs- und Katasterrecht",
                    },
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "SO_KlassifizNachSonstigemRecht",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detailArtDerFestlegung: Annotated[
        AnyUrl | None,
        Field(
            description="Detaillierte rechtliche Klassifizierung der Festlegung",
            json_schema_extra={
                "typename": "SO_DetailKlassifizNachSonstigemRecht",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            description="Informelle Bezeichnung der Festlegung",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class SOStrassenverkehrsrecht(SOGeometrieobjekt):
    """Festlegung nach Straßenverkehrsrecht."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    artDerFestlegung: Annotated[
        Literal["1000", "1100", "1200", "1300", "9999"] | None,
        Field(
            description="Grobe rechtliche Klassifizierung der Festlegung",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Bundesautobahn"},
                    "1100": {"name": "Bundesstrasse"},
                    "1200": {"name": "LandesStaatsstrasse"},
                    "1300": {"name": "Kreisstrasse"},
                    "9999": {"name": "SonstOeffentlStrasse"},
                },
                "typename": "SO_KlassifizNachStrassenverkehrsrecht",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detailArtDerFestlegung: Annotated[
        AnyUrl | None,
        Field(
            description="Detaillierte rechtliche Klassifizierung der Festlegung.",
            json_schema_extra={
                "typename": "SO_DetailKlassifizNachStrassenverkehrsrecht",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            description="Informelle Bezeichnung der Festlegung.",
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
            description="Amtliche Bezeichnung / Kennziffer der Festlegung.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class SOWasserrecht(SOGeometrieobjekt):
    """Festlegung nach Wasserrecht"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    artDerFestlegung: Annotated[
        Literal["1000", "1100", "1300", "2000", "20000", "20001", "20002", "9999"]
        | None,
        Field(
            description="Grundlegende rechtliche Klassifizierung der Festlegung.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Gewaesser1Ordnung",
                        "description": "Gewässer 1. Ordnung.",
                    },
                    "1100": {
                        "name": "Gewaesser2Ordnung",
                        "description": "Gewässer 2. Ordnung.",
                    },
                    "1300": {
                        "name": "Gewaesser3Ordnung",
                        "description": "Gewässer 3. Ordnung",
                    },
                    "2000": {
                        "name": "Ueberschwemmungsgebiet",
                        "description": "'Überschwemmungsgebiet' nach . § 31b Abs. 1 WHG  ist ein durch Rechtsverordnung festgesetztes oder natürliches Gebiet, das bei Hochwasser überschwemmt werden kann bzw. überschwemmt wird.",
                    },
                    "20000": {
                        "name": "FestgesetztesUeberschwemmungsgebiet",
                        "description": "'Festgesetztes Überschwemmungsgebiet ist ein per Verordnung festgesetzte Überschwemmungsgebiete auf Basis HQ100",
                    },
                    "20001": {
                        "name": "NochNichtFestgesetztesUeberschwemmungsgebiet",
                        "description": "Noch nicht festgesetztes Überschwemmungsgebiet nach §31b Abs. 5 WHG.",
                    },
                    "20002": {
                        "name": "UeberschwemmGefaehrdetesGebiet",
                        "description": "Überschwemmungsgefährdetes Gebiet gemäß §31 c WHG.",
                    },
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "SO_KlassifizNachWasserrecht",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detailArtDerFestlegung: Annotated[
        AnyUrl | None,
        Field(
            description="Detaillierte rechtliche Klassifizierung der Festlegung.",
            json_schema_extra={
                "typename": "SO_DetailKlassifizNachWasserrecht",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    istNatuerlichesUberschwemmungsgebiet: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob es sich bei der Fläche um ein natürliches Überschwemmungsgebiet handelt.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False
    name: Annotated[
        str | None,
        Field(
            description="Informelle Bezeichnung der Festlegung",
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
            description="Amtliche Bezeichnung / Kennziffer der Festlegung",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class XPNutzungsschablone(XPPTO):
    """Modelliert eine Nutzungsschablone. Die darzustellenden Attributwerte werden zeilenweise in die Nutzungsschablone geschrieben."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    spaltenAnz: Annotated[
        int,
        Field(
            description="Anzahl der Spalten in der Nutzungsschablone",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]
    zeilenAnz: Annotated[
        int,
        Field(
            description="Anzahl der Zeilen in der Nutzungsschablone",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "1",
            },
        ),
    ]


class BPAbgrabungsFlaeche(BPFlaechenobjekt):
    """Flächen für Aufschüttungen, Abgrabungen oder für die Gewinnung von Bodenschätzen (§9, Abs. 1, Nr. 17 BauGB)). Hier: Flächen für Abgrabungen."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class BPAbstandsFlaeche(BPUeberlagerungsobjekt):
    """Festsetzung eines vom Bauordnungsrecht abweichenden Maßes der Tiefe der Abstandsfläche gemäß § 9 Abs 1. Nr. 2a BauGB"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    tiefe: Annotated[
        definitions.Length | None,
        Field(
            description="Absolute Angabe derTiefe.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None


class BPAbstandsMass(BPGeometrieobjekt):
    """Darstellung von Maßpfeilen oder Maßkreisen in BPlänen um eine eindeutige Vermassung einzelner Festsetzungen zu erreichen."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    wert: Annotated[
        definitions.Length,
        Field(
            description="Längenangabe des Abstandsmasses.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "1",
                "uom": "m",
            },
        ),
    ]
    startWinkel: Annotated[
        definitions.Angle | None,
        Field(
            description="Startwinkel für Darstellung eines Abstandsmaßes (nur relevant für Maßkeise)",
            json_schema_extra={
                "typename": "Angle",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "grad",
            },
        ),
    ] = None
    endWinkel: Annotated[
        definitions.Angle | None,
        Field(
            description="Endwinkel für Darstellung eines Abstandsmaße (nur relevant für Maßkreise).",
            json_schema_extra={
                "typename": "Angle",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "grad",
            },
        ),
    ] = None


class BPAnpflanzungBindungErhaltung(BPGeometrieobjekt):
    """Für einzelne Flächen oder für ein Bebauungsplangebiet oder Teile davon sowie für Teile baulicher Anlagen mit Ausnahme der für landwirtschaftliche Nutzungen oder Wald festgesetzten Flächen:
    a) Festsetzung des Anpflanzens von Bäumen, Sträuchern und sonstigen Bepflanzungen;
    b) Festsetzung von Bindungen für Bepflanzungen und für die Erhaltung von Bäumen, Sträuchern und sonstigen Bepflanzungen sowie von Gewässern;  (§9 Abs. 1 Nr. 25 und Abs. 4 BauGB)
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    massnahme: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Art der Maßnahme",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "BindungErhaltung",
                        "description": "Bindung und Erhaltung von Bäumen, Sträuchern und sonstigen Bepflanzungen, sowie von Gewässern.",
                    },
                    "2000": {
                        "name": "Anpflanzung",
                        "description": "Anpflanzung von Bäumen, Sträuchern oder sonstigen Bepflanzungen.",
                    },
                    "3000": {"name": "AnpflanzungBindungErhaltung"},
                },
                "typename": "XP_ABEMassnahmenTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gegenstand: Annotated[
        list[
            Literal[
                "1000",
                "1100",
                "1200",
                "2000",
                "2100",
                "2200",
                "3000",
                "4000",
                "5000",
                "6000",
            ]
        ]
        | None,
        Field(
            description="Gegenständ eder Maßnahme",
            json_schema_extra={
                "typename": "XP_AnpflanzungBindungErhaltungsGegenstand",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Baeume", "description": "Bäume"},
                    "1100": {"name": "Kopfbaeume"},
                    "1200": {"name": "Baumreihe"},
                    "2000": {"name": "Straeucher", "description": "Sträucher"},
                    "2100": {"name": "Hecke"},
                    "2200": {"name": "Knick"},
                    "3000": {
                        "name": "SonstBepflanzung",
                        "description": "Sonstige Bepflanzung",
                    },
                    "4000": {
                        "name": "Gewaesser",
                        "description": "Gewässer (nur Erhaltung)",
                    },
                    "5000": {"name": "Fassadenbegruenung"},
                    "6000": {"name": "Dachbegruenung"},
                },
            },
        ),
    ] = None
    kronendurchmesser: Annotated[
        definitions.Length | None,
        Field(
            description="Durchmesser der Baumkrone bei zu erhaltenden Bäumen.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    pflanztiefe: Annotated[
        definitions.Length | None,
        Field(
            description="Pflanztiefe",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    istAusgleich: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob die Fläche oder Maßnahme zum Ausgleich von Eingriffen genutzt wird.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False


class BPAufschuettungsFlaeche(BPFlaechenobjekt):
    """Flächen für Aufschüttungen, Abgrabungen oder für die Gewinnung von Bodenschätzen (§ 9 Abs. 1 Nr. 17 und Abs. 6 BauGB). Hier: Flächen für Aufschüttungen"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class BPAusgleichsFlaeche(BPFlaechenobjekt):
    """Festsetzung einer Fläche zum Ausgleich im Sinne des § 1a Abs.3 und §9 Abs. 1a BauGB."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    ziel: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"] | None,
        Field(
            description='Unterscheidung nach den Zielen "Schutz, Pflege" und "Entwicklung".',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "SchutzPflege"},
                    "2000": {"name": "Entwicklung"},
                    "3000": {"name": "Anlage"},
                    "4000": {"name": "SchutzPflegeEntwicklung"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "XP_SPEZiele",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    massnahme: Annotated[
        list[XPSPEMassnahmenDaten] | None,
        Field(
            description="Auf der Fläche durchzuführende Maßnahmen.",
            json_schema_extra={
                "typename": "XP_SPEMassnahmenDaten",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    weitereMassnahme1: Annotated[
        XPSPEMassnahmenDaten | None,
        Field(
            description='Weitere durchzuführende Massnahme. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen massnahme mehrfach belegt werden.',
            json_schema_extra={
                "typename": "XP_SPEMassnahmenDaten",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereMassnahme2: Annotated[
        XPSPEMassnahmenDaten | None,
        Field(
            description='Weitere durchzuführende Massnahme. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen massnahme mehrfach belegt werden.',
            json_schema_extra={
                "typename": "XP_SPEMassnahmenDaten",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refMassnahmenText: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf ein Dokument, das die durchzuführenden Massnahmen beschreibt.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refLandschaftsplan: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf den Landschaftsplan.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPAusgleichsMassnahme(BPGeometrieobjekt):
    """Festsetzung einer Einzelmaßnahme zum Ausgleich im Sinne des § 1a Abs.3 und §9 Abs. 1a BauGB."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    ziel: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"] | None,
        Field(
            description="Ziel der Ausgleichsmassnahme",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "SchutzPflege"},
                    "2000": {"name": "Entwicklung"},
                    "3000": {"name": "Anlage"},
                    "4000": {"name": "SchutzPflegeEntwicklung"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "XP_SPEZiele",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    massnahme: Annotated[
        list[XPSPEMassnahmenDaten] | None,
        Field(
            description="Durchzuführende Ausgleichsmaßnahmen.",
            json_schema_extra={
                "typename": "XP_SPEMassnahmenDaten",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    weitereMassnahme1: Annotated[
        XPSPEMassnahmenDaten | None,
        Field(
            description='Weitere durchzuführende Massnahme Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen massnahme mehrfach belegt werden.',
            json_schema_extra={
                "typename": "XP_SPEMassnahmenDaten",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereMassnahme2: Annotated[
        XPSPEMassnahmenDaten | None,
        Field(
            description='Weitere durchzuführende Massnahme. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen massnahme mehrfach belegt werden.',
            json_schema_extra={
                "typename": "XP_SPEMassnahmenDaten",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refMassnahmenText: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf ein Dokument, das die durchzuführenden Maßnahmen beschreibt.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refLandschaftsplan: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf den Landschaftsplan.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPBauGrenze(BPLinienobjekt):
    """Festsetzung einer Baugrenze (§9 Abs. 1 Nr. 2 BauGB, §22 und 23 BauNVO). Über die Attribute geschossMin und geschossMax kann die Festsetzung auf einen Bereich von Geschossen beschränkt werden. Wenn eine Einschränkung der Festsetzung durch expliziter Höhenangaben erfolgen soll, ist dazu die Oberklassen-Relation hoehenangabe auf den komplexen Datentyp XP_Hoehenangabe zu verwenden."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    bautiefe: Annotated[
        definitions.Length | None,
        Field(
            description="Angabe einer Bautiefe.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    geschossMin: Annotated[
        int | None,
        Field(
            description="Gibt bei geschossweiser Festsetzung die Nummer des Geschosses an, ab den die Festsetzung gilt. Wenn das Attribut nicht belegt ist, gilt die Festsetzung für alle Geschosse bis einschl. geschossMax.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    geschossMax: Annotated[
        int | None,
        Field(
            description="Gibt bei geschossweiser Feststzung die Nummer des Geschosses an, bis zu der die Festsetzung gilt. Wenn das Attribut nicht belegt ist, gilt die Festsetzung für alle Geschosse ab einschl. geschossMin.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPBauLinie(BPLinienobjekt):
    """Festsetzung einer Baulinie (§9 Abs. 1 Nr. 2 BauGB, §22 und 23 BauNVO). Über die Attribute geschossMin und geschossMax kann die Festsetzung auf einen Bereich von Geschossen beschränkt werden. Wenn eine Einschränkung der Festsetzung durch expliziter Höhenangaben erfolgen soll, ist dazu die Oberklassen-Relation hoehenangabe auf den komplexen Datentyp XP_Hoehenangabe zu verwenden."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    bautiefe: Annotated[
        definitions.Length | None,
        Field(
            description="Angabe einer Bautiefe.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    geschossMin: Annotated[
        int | None,
        Field(
            description="Gibt bei geschossweiser Festsetzung die Nummer des Geschosses an, ab den die Festsetzung gilt. Wenn das Attribut nicht belegt ist, gilt die Festsetzung für alle Geschosse bis einschl. geschossMax.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    geschossMax: Annotated[
        int | None,
        Field(
            description="Gibt bei geschossweiser Feststzung die Nummer des Geschosses an, bis zu der die Festsetzung gilt. Wenn das Attribut nicht belegt ist, gilt die Festsetzung für alle Geschosse ab einschl. geschossMin.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPBaugebietsTeilFlaeche(BPFlaechenschlussobjekt):
    """Teil eines Baugebiets mit einheitlicher Art und Maß der baulichen Nutzung."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    DNmin: Annotated[
        definitions.Angle | None,
        Field(
            description="Minimal zulässige Dachneigung bei einer Bereichsangabe.",
            json_schema_extra={
                "typename": "Angle",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "grad",
            },
        ),
    ] = None
    DNmax: Annotated[
        definitions.Angle | None,
        Field(
            description="Maximal zulässige Dachneigung bei einer Bereichsangabe.",
            json_schema_extra={
                "typename": "Angle",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "grad",
            },
        ),
    ] = None
    DN: Annotated[
        definitions.Angle | None,
        Field(
            description="Maximal zulässige Dachneigung.",
            json_schema_extra={
                "typename": "Angle",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "grad",
            },
        ),
    ] = None
    DNZwingend: Annotated[
        definitions.Angle | None,
        Field(
            description="Zwingend vorgeschriebene Dachneigung.",
            json_schema_extra={
                "typename": "Angle",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "grad",
            },
        ),
    ] = None
    FR: Annotated[
        definitions.Angle | None,
        Field(
            description="Vorgeschriebene Firstrichtung (Gradangabe)",
            json_schema_extra={
                "typename": "Angle",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "grad",
            },
        ),
    ] = None
    dachform: Annotated[
        list[
            Literal[
                "1000",
                "2100",
                "2200",
                "3100",
                "3200",
                "3300",
                "3400",
                "3500",
                "3600",
                "3700",
                "3800",
                "3900",
                "4000",
                "5000",
                "9999",
            ]
        ]
        | None,
        Field(
            description="Vorgeschriebene Dachformen",
            json_schema_extra={
                "typename": "BP_Dachform",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Flachdach"},
                    "2100": {"name": "Pultdach"},
                    "2200": {"name": "Versetztes Pultdach"},
                    "3100": {"name": "Satteldach"},
                    "3200": {"name": "Walmdach"},
                    "3300": {"name": "Krüppelwalmdach"},
                    "3400": {"name": "Mansarddach"},
                    "3500": {"name": "Zeltdach"},
                    "3600": {"name": "Kegeldach"},
                    "3700": {"name": "Kuppeldach"},
                    "3800": {"name": "Sheddach"},
                    "3900": {"name": "Bogendach"},
                    "4000": {"name": "Turmdach"},
                    "5000": {"name": "Mischform"},
                    "9999": {"name": "Sonstiges"},
                },
            },
        ),
    ] = None
    detaillierteDachform: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definierte Dachform.",
            json_schema_extra={
                "typename": "BP_DetailDachform",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    abweichungText: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": [
                    "BP_TextAbschnitt",
                    "FP_TextAbschnitt",
                    "LP_TextAbschnitt",
                    "RP_TextAbschnitt",
                    "SO_TextAbschnitt",
                    "XP_TextAbschnitt",
                ],
                "stereotype": "Association",
                "multiplicity": "0..*",
            }
        ),
    ] = None
    MaxZahlWohnungen: Annotated[
        int | None,
        Field(
            description="Höchstzulässige Zahl der Wohnungen in Wohngebäuden",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Fmin: Annotated[
        definitions.Area | None,
        Field(
            description="Mindestmaß für die Größe (Fläche) eines Baugrundstücks.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Fmax: Annotated[
        definitions.Area | None,
        Field(
            description="Höchstmaß für die Größe (Fläche) eines Baugrundstücks.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Bmin: Annotated[
        definitions.Length | None,
        Field(
            description="Minimale Breite von Baugrundstücken",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Bmax: Annotated[
        definitions.Length | None,
        Field(
            description="Maximale Breite von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Tmin: Annotated[
        definitions.Length | None,
        Field(
            description="Minimale Tiefe von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Tmax: Annotated[
        definitions.Length | None,
        Field(
            description="Maximale Tiefe von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    GFZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Geschossflächenzahl .",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl bei einer Bereichsangabe. Das Attribut GFZmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZ_Ausn: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl als Ausnahme.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFmin: Annotated[
        definitions.Area | None,
        Field(
            description="Minimal zulässige Geschossfläche",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GFmax: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Geschossfläche bei einer Bereichsabgabe. Das Attribut GFmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GF: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Geschossfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GF_Ausn: Annotated[
        definitions.Area | None,
        Field(
            description="Ausnahmsweise maximal zulässige Geschossfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    BMZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Baumassenzahl",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Baumassenzahl bei einer Bereichsangabe. Das Attribut BMZmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Baumassenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZ_Ausn: Annotated[
        float | None,
        Field(
            description="Ausnahmsweise maximal zulässige Baumassenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMmin: Annotated[
        definitions.Volume | None,
        Field(
            description="Minimal zulässinge Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BMmax: Annotated[
        definitions.Volume | None,
        Field(
            description="Maximal zulässinge Baumasse bei einer Bereichsangabe. Das Attribut BMmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BM: Annotated[
        definitions.Volume | None,
        Field(
            description="Maximal zulässige Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BM_Ausn: Annotated[
        definitions.Volume | None,
        Field(
            description="Ausnahmsweise maximal zulässige Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    GRZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Grundflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Grundflächenzahl bei einer Bereichsangabe.  Das Attribut GRZmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Grundflächenzahl",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZ_Ausn: Annotated[
        float | None,
        Field(
            description="Ausnahmsweise maximal zulässige Grundflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRmin: Annotated[
        definitions.Area | None,
        Field(
            description="Minimal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GRmax: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Grundfläche bei einer Bereichsangabe. Das Attribut GRmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GR: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GR_Ausn: Annotated[
        definitions.Area | None,
        Field(
            description="Ausnahmsweise maximal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Zmin: Annotated[
        int | None,
        Field(
            description="Minimal zulässige Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Zmax: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der oberirdischen Vollgeschosse bei einer Bereichsangabe. Das Attribut Zmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Zzwingend: Annotated[
        int | None,
        Field(
            description="Zwingend vorgeschriebene Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z: Annotated[
        int | None,
        Field(
            description="Maximalzahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Ausn: Annotated[
        int | None,
        Field(
            description="Ausnahmsweise maximal zulässige Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Staffel: Annotated[
        int | None,
        Field(
            description="Maximalzahl von oberirdischen zurückgesetzten Vollgeschossen als Staffelgeschoss..",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Dach: Annotated[
        int | None,
        Field(
            description="Maximalzahl der zusätzlich erlaubten Dachgeschosse, die gleichzeitig Vollgeschosse sind.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUmin: Annotated[
        int | None,
        Field(
            description="Minimal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUmax: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der unterirdischen Geschosse bei einer Bereichsangabe. Das Attribut ZUmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUzwingend: Annotated[
        int | None,
        Field(
            description="Zwingend vorgeschriebene Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZU: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZU_Ausn: Annotated[
        int | None,
        Field(
            description="Ausnahmsweise maximal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    allgArtDerBaulNutzung: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"] | None,
        Field(
            description="Spezifikation der allgemeinen Art der baulichen N utzung.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "WohnBauflaeche"},
                    "2000": {"name": "GemischteBauflaeche"},
                    "3000": {"name": "GewerblicheBauflaeche"},
                    "4000": {"name": "SonderBauflaeche"},
                    "9999": {"name": "SonstigeBauflaeche"},
                },
                "typename": "XP_AllgArtDerBaulNutzung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    besondereArtDerBaulNutzung: Annotated[
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
            "2000",
            "2100",
            "3000",
            "4000",
            "9999",
        ]
        | None,
        Field(
            description="Festsetzung der Art der baulichen Nutzung (§9, Abs. 1, Nr. 1 BauGB).",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Kleinsiedlungsgebiet",
                        "description": "Kleinsiedlungsgebiet",
                    },
                    "1100": {
                        "name": "ReinesWohngebiet",
                        "description": "Reines Wohngebiet",
                    },
                    "1200": {
                        "name": "AllgWohngebiet",
                        "description": "Allgemeines Wohngebiet",
                    },
                    "1300": {
                        "name": "BesonderesWohngebiet",
                        "description": "Besonderes Wohngebiet",
                    },
                    "1400": {"name": "Dorfgebiet", "description": "Dorfgebiet"},
                    "1500": {"name": "Mischgebiet"},
                    "1600": {"name": "Kerngebiet", "description": "Kerngebiet"},
                    "1700": {"name": "Gewerbegebiet"},
                    "1800": {
                        "name": "Industriegebiet",
                        "description": "Industriegebiet",
                    },
                    "2000": {
                        "name": "SondergebietErholung",
                        "description": "Sondergebiet, das der Erholung dient (§ 10 BauNVO); z.B. Wochenendhausgebiet",
                    },
                    "2100": {
                        "name": "SondergebietSonst",
                        "description": "Sonstiges Sondergebiet (§ 11 BauNVO); z.B. Klinikgebiet",
                    },
                    "3000": {"name": "Wochenendhausgebiet"},
                    "4000": {"name": "Sondergebiet"},
                    "9999": {
                        "name": "SonstigesGebiet",
                        "description": "Sonstiges Gebiet",
                    },
                },
                "typename": "XP_BesondereArtDerBaulNutzung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    sondernutzung: Annotated[
        Literal[
            "1000",
            "1100",
            "1200",
            "1300",
            "1400",
            "1500",
            "1600",
            "16000",
            "16001",
            "16002",
            "1700",
            "1800",
            "1900",
            "2000",
            "2100",
            "2200",
            "2300",
            "2400",
            "2500",
            "2600",
            "2700",
            "2800",
            "2900",
            "9999",
        ]
        | None,
        Field(
            description='Bei Nutzungsform "Sondergebiet": Spezifische Nutzung der Sonderbaufläche nach §§ 10 und 11 BauNVO.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Wochenendhausgebiet"},
                    "1100": {"name": "Ferienhausgebiet"},
                    "1200": {"name": "Campingplatzgebiet"},
                    "1300": {"name": "Kurgebiet"},
                    "1400": {"name": "SonstSondergebietErholung"},
                    "1500": {"name": "Einzelhandelsgebiet"},
                    "1600": {"name": "GrossflaechigerEinzelhandel"},
                    "16000": {"name": "Ladengebiet"},
                    "16001": {"name": "Einkaufszentrum"},
                    "16002": {"name": "SonstGrossflEinzelhandel"},
                    "1700": {"name": "Verkehrsuebungsplatz"},
                    "1800": {"name": "Hafengebiet"},
                    "1900": {"name": "SondergebietErneuerbareEnergie"},
                    "2000": {"name": "SondergebietMilitaer"},
                    "2100": {"name": "SondergebietLandwirtschaft"},
                    "2200": {"name": "SondergebietSport"},
                    "2300": {"name": "SondergebietGesundheitSoziales"},
                    "2400": {"name": "Golfplatz"},
                    "2500": {"name": "SondergebietKultur"},
                    "2600": {"name": "SondergebietTourismus"},
                    "2700": {"name": "SondergebietBueroUndVerwaltung"},
                    "2800": {"name": "SondergebietHochschuleEinrichtungen"},
                    "2900": {"name": "SondergebietMesse"},
                    "9999": {"name": "SondergebietAndereNutzungen"},
                },
                "typename": "XP_Sondernutzungen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteArtDerBaulNutzung: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definierte Nutzungsart.",
            json_schema_extra={
                "typename": "BP_DetailArtDerBaulNutzung",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    nutzungText: Annotated[
        str | None,
        Field(
            description='Bei Nutzungsform "Sondergebiet": Kurzform der besonderen Art der baulichen Nutzung.',
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    abweichungBauNVO: Annotated[
        Literal["1000", "2000", "3000", "9999"] | None,
        Field(
            description="Art der Abweichung von der BauNVO",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "EinschraenkungNutzung",
                        "description": "Einschränkung einer generell erlaubten Nutzung.",
                    },
                    "2000": {
                        "name": "AusschlussNutzung",
                        "description": "Ausschluss einer generell erlaubten Nutzung.",
                    },
                    "3000": {
                        "name": "AusweitungNutzung",
                        "description": "Eine neu ausnahmsweise zulässige Nutzung wird generell zulässig.",
                    },
                    "9999": {
                        "name": "SonstAbweichung",
                        "description": "Sonstige Abweichung.",
                    },
                },
                "typename": "XP_AbweichungBauNVOTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    bauweise: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Festsetzung der Bauweise  (§9, Abs. 1, Nr. 2 BauGB).",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "OffeneBauweise",
                        "description": "Offene Bauweise",
                    },
                    "2000": {
                        "name": "GeschlosseneBauweise",
                        "description": "Geschlossene Bauweise",
                    },
                    "3000": {
                        "name": "AbweichendeBauweise",
                        "description": "Abweichende Bauweise",
                    },
                },
                "typename": "BP_Bauweise",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    abweichendeBauweise: Annotated[
        AnyUrl | None,
        Field(
            description='Nähere Bezeichnung einer "Abweichenden Bauweise".',
            json_schema_extra={
                "typename": "BP_AbweichendeBauweise",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    vertikaleDifferenzierung: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob eine vertikale Differenzierung des Gebäudes vorgeschrieben ist.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False
    bebauungsArt: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "6000", "7000"] | None,
        Field(
            description="Detaillierte Festsetzung der Bauweise (§9, Abs. 1, Nr. 2 BauGB).",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Einzelhaeuser",
                        "description": "Nur Einzelhäuser zulässig.",
                    },
                    "2000": {
                        "name": "Doppelhaeuser",
                        "description": "Nur Doppelhäuser zulässig.",
                    },
                    "3000": {
                        "name": "Hausgruppen",
                        "description": "Nur Hausgruppen zulässig.",
                    },
                    "4000": {
                        "name": "EinzelDoppelhaeuser",
                        "description": "Nur Einzel- oder Doppelhäuser zulässig.",
                    },
                    "5000": {
                        "name": "EinzelhaeuserHausgruppen",
                        "description": "Nur Einzelhäuser oder Hausgruppen zulässig.",
                    },
                    "6000": {
                        "name": "DoppelhaeuserHausgruppen",
                        "description": "Nur Doppelhäuser oder Hausgruppen zulässig.",
                    },
                    "7000": {"name": "Reihenhaeuser"},
                },
                "typename": "BP_BebauungsArt",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    bebauungVordereGrenze: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Festsetzung der Bebauung der vorderen Grundstücksgrenze (§9, Abs. 1, Nr. 2 BauGB).",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Verboten",
                        "description": "Eine Bebauung der Grenze ist verboten.",
                    },
                    "2000": {
                        "name": "Erlaubt",
                        "description": "Eine Bebauung der Grenze ist erlaubt.",
                    },
                    "3000": {
                        "name": "Erzwungen",
                        "description": "Eine Bebauung der Grenze ist vorgeschrieben.",
                    },
                },
                "typename": "BP_GrenzBebauung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    bebauungRueckwaertigeGrenze: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Festsetzung der Bebauung der rückwärtigen Grundstücksgrenze (§9, Abs. 1, Nr. 2 BauGB).",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Verboten",
                        "description": "Eine Bebauung der Grenze ist verboten.",
                    },
                    "2000": {
                        "name": "Erlaubt",
                        "description": "Eine Bebauung der Grenze ist erlaubt.",
                    },
                    "3000": {
                        "name": "Erzwungen",
                        "description": "Eine Bebauung der Grenze ist vorgeschrieben.",
                    },
                },
                "typename": "BP_GrenzBebauung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    bebauungSeitlicheGrenze: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Festsetzung der Bebauung der seitlichen Grundstücksgrenze (§9, Abs. 1, Nr. 2 BauGB).",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Verboten",
                        "description": "Eine Bebauung der Grenze ist verboten.",
                    },
                    "2000": {
                        "name": "Erlaubt",
                        "description": "Eine Bebauung der Grenze ist erlaubt.",
                    },
                    "3000": {
                        "name": "Erzwungen",
                        "description": "Eine Bebauung der Grenze ist vorgeschrieben.",
                    },
                },
                "typename": "BP_GrenzBebauung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refGebaeudequerschnitt: Annotated[
        list[XPExterneReferenz] | None,
        Field(
            description="Referenz auf ein Dokument mit vorgeschriebenen Gebäudequerschnitten.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    zugunstenVon: Annotated[
        str | None,
        Field(
            description="Angabe des Begünstigten einer Ausweisung.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPBereichOhneEinAusfahrtLinie(BPLinienobjekt):
    """Bereich ohne Ein- und Ausfahrt (§9 Abs. 1 Nr. 11 und Abs. 6 BauGB)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    typ: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Typ der EIn- oder Ausfahrt.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "KeineEinfahrt"},
                    "2000": {"name": "KeineAusfahrt"},
                    "3000": {"name": "KeineEinAusfahrt"},
                },
                "typename": "BP_BereichOhneEinAusfahrtTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPBesondererNutzungszweckFlaeche(BPFlaechenobjekt):
    """Festsetzung einer Fläche mit besonderem Nutzungszweck, der durch besondere städtebauliche Gründe erfordert wird (§9 Abs. 1 Nr. 9 BauGB.)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    DNmin: Annotated[
        definitions.Angle | None,
        Field(
            description="Minimal zulässige Dachneigung bei einer Bereichsangabe.",
            json_schema_extra={
                "typename": "Angle",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "grad",
            },
        ),
    ] = None
    DNmax: Annotated[
        definitions.Angle | None,
        Field(
            description="Maximal zulässige Dachneigung bei einer Bereichsangabe.",
            json_schema_extra={
                "typename": "Angle",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "grad",
            },
        ),
    ] = None
    DN: Annotated[
        definitions.Angle | None,
        Field(
            description="Maximal zulässige Dachneigung.",
            json_schema_extra={
                "typename": "Angle",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "grad",
            },
        ),
    ] = None
    DNZwingend: Annotated[
        definitions.Angle | None,
        Field(
            description="Zwingend vorgeschriebene Dachneigung.",
            json_schema_extra={
                "typename": "Angle",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "grad",
            },
        ),
    ] = None
    FR: Annotated[
        definitions.Angle | None,
        Field(
            description="Vorgeschriebene Firstrichtung (Gradangabe)",
            json_schema_extra={
                "typename": "Angle",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "grad",
            },
        ),
    ] = None
    dachform: Annotated[
        list[
            Literal[
                "1000",
                "2100",
                "2200",
                "3100",
                "3200",
                "3300",
                "3400",
                "3500",
                "3600",
                "3700",
                "3800",
                "3900",
                "4000",
                "5000",
                "9999",
            ]
        ]
        | None,
        Field(
            description="Vorgeschriebene Dachformen",
            json_schema_extra={
                "typename": "BP_Dachform",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Flachdach"},
                    "2100": {"name": "Pultdach"},
                    "2200": {"name": "Versetztes Pultdach"},
                    "3100": {"name": "Satteldach"},
                    "3200": {"name": "Walmdach"},
                    "3300": {"name": "Krüppelwalmdach"},
                    "3400": {"name": "Mansarddach"},
                    "3500": {"name": "Zeltdach"},
                    "3600": {"name": "Kegeldach"},
                    "3700": {"name": "Kuppeldach"},
                    "3800": {"name": "Sheddach"},
                    "3900": {"name": "Bogendach"},
                    "4000": {"name": "Turmdach"},
                    "5000": {"name": "Mischform"},
                    "9999": {"name": "Sonstiges"},
                },
            },
        ),
    ] = None
    detaillierteDachform: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definierte Dachform.",
            json_schema_extra={
                "typename": "BP_DetailDachform",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    MaxZahlWohnungen: Annotated[
        int | None,
        Field(
            description="Höchstzulässige Zahl der Wohnungen in Wohngebäuden",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Fmin: Annotated[
        definitions.Area | None,
        Field(
            description="Mindestmaß für die Größe (Fläche) eines Baugrundstücks.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Fmax: Annotated[
        definitions.Area | None,
        Field(
            description="Höchstmaß für die Größe (Fläche) eines Baugrundstücks.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Bmin: Annotated[
        definitions.Length | None,
        Field(
            description="Minimale Breite von Baugrundstücken",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Bmax: Annotated[
        definitions.Length | None,
        Field(
            description="Maximale Breite von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Tmin: Annotated[
        definitions.Length | None,
        Field(
            description="Minimale Tiefe von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Tmax: Annotated[
        definitions.Length | None,
        Field(
            description="Maximale Tiefe von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    GFZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Geschossflächenzahl .",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl bei einer Bereichsangabe. Das Attribut GFZmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZ_Ausn: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl als Ausnahme.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFmin: Annotated[
        definitions.Area | None,
        Field(
            description="Minimal zulässige Geschossfläche",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GFmax: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Geschossfläche bei einer Bereichsabgabe. Das Attribut GFmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GF: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Geschossfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GF_Ausn: Annotated[
        definitions.Area | None,
        Field(
            description="Ausnahmsweise maximal zulässige Geschossfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    BMZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Baumassenzahl",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Baumassenzahl bei einer Bereichsangabe. Das Attribut BMZmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Baumassenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZ_Ausn: Annotated[
        float | None,
        Field(
            description="Ausnahmsweise maximal zulässige Baumassenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMmin: Annotated[
        definitions.Volume | None,
        Field(
            description="Minimal zulässinge Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BMmax: Annotated[
        definitions.Volume | None,
        Field(
            description="Maximal zulässinge Baumasse bei einer Bereichsangabe. Das Attribut BMmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BM: Annotated[
        definitions.Volume | None,
        Field(
            description="Maximal zulässige Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BM_Ausn: Annotated[
        definitions.Volume | None,
        Field(
            description="Ausnahmsweise maximal zulässige Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    GRZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Grundflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Grundflächenzahl bei einer Bereichsangabe.  Das Attribut GRZmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Grundflächenzahl",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZ_Ausn: Annotated[
        float | None,
        Field(
            description="Ausnahmsweise maximal zulässige Grundflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRmin: Annotated[
        definitions.Area | None,
        Field(
            description="Minimal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GRmax: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Grundfläche bei einer Bereichsangabe. Das Attribut GRmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GR: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GR_Ausn: Annotated[
        definitions.Area | None,
        Field(
            description="Ausnahmsweise maximal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Zmin: Annotated[
        int | None,
        Field(
            description="Minimal zulässige Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Zmax: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der oberirdischen Vollgeschosse bei einer Bereichsangabe. Das Attribut Zmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Zzwingend: Annotated[
        int | None,
        Field(
            description="Zwingend vorgeschriebene Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z: Annotated[
        int | None,
        Field(
            description="Maximalzahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Ausn: Annotated[
        int | None,
        Field(
            description="Ausnahmsweise maximal zulässige Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Staffel: Annotated[
        int | None,
        Field(
            description="Maximalzahl von oberirdischen zurückgesetzten Vollgeschossen als Staffelgeschoss..",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Dach: Annotated[
        int | None,
        Field(
            description="Maximalzahl der zusätzlich erlaubten Dachgeschosse, die gleichzeitig Vollgeschosse sind.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUmin: Annotated[
        int | None,
        Field(
            description="Minimal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUmax: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der unterirdischen Geschosse bei einer Bereichsangabe. Das Attribut ZUmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUzwingend: Annotated[
        int | None,
        Field(
            description="Zwingend vorgeschriebene Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZU: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZU_Ausn: Annotated[
        int | None,
        Field(
            description="Ausnahmsweise maximal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    zweckbestimmung: Annotated[
        str | None,
        Field(
            description="Angabe des besonderen Nutzungszwecks",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPBodenschaetzeFlaeche(BPFlaechenobjekt):
    """Flächen für Aufschüttungen, Abgrabungen oder für die Gewinnung von Bodenschätzen (§ 9 Abs. 1 Nr. 17 und Abs. 6 BauGB). Hier: Flächen für Gewinnung von Bodenschätzen"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    abbaugut: Annotated[
        str | None,
        Field(
            description="Bezeichnung des Abbauguts.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPDenkmalschutzEinzelanlage(BPGeometrieobjekt):
    """Denkmalgeschützte Einzelanlage, sofern es sich um eine Festsetzung des Bebauungsplans handelt (§9 Abs. 4 BauGB - landesrechtliche Regelung)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    denkmal: Annotated[
        str | None,
        Field(
            description="Nähere Bezeichnung des Denkmals.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPDenkmalschutzEnsembleFlaeche(BPUeberlagerungsobjekt):
    """Umgrenzung eines Denkmalgeschützten Ensembles, sofern es sich um eine Festsetzung des Bebauungsplans handelt (§9 Abs. 4 BauGB - landesrechtliche Regelung). Weltkulturerbe kann eigentlich nicht vorkommen."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    denkmal: Annotated[
        str | None,
        Field(
            description="Nähere Bezeichnung des Denkmals.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weltkulturerbe: Annotated[
        bool | None,
        Field(
            description="Angabe, ob das Denkmal zum UNESCO Welkulturerbe gehört. Dies Attribut wird nicht benötigt, da Welterbestätten prinzipiell nur nachrichtlich übernommen werden und nicht festgesetzt werden können. In einer zukünftigen Version des Standards wird das Attribut deshalb wegfallen.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False


class BPEinfahrtsbereichLinie(BPLinienobjekt):
    """Einfahrtsbereich (§9 Abs. 1 Nr. 11 und Abs. 6 BauGB)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class BPEingriffsBereich(BPUeberlagerungsobjekt):
    """Bestimmt einen Bereich, in dem ein Eingriff nach dem Naturschutzrecht zugelassen wird, der durch geeignete Flächen oder Maßnahmen ausgeglichen werden muss."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class BPErhaltungsBereichFlaeche(BPUeberlagerungsobjekt):
    """Fläche, auf denen der Rückbau, die Änderung oder die Nutzungsänderung baulichen Anlagen der Genehmigung durch die Gemeinde bedarf (§172 BauGB)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    grund: Annotated[
        Literal["1000", "2000", "3000"],
        Field(
            description="Erhaltungsgrund",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "StaedtebaulicheGestalt",
                        "description": "Erhaltung der städtebaulichen Eigenart des Gebiets auf Grund seiner städtebaulichen Gestalt",
                    },
                    "2000": {
                        "name": "Wohnbevoelkerung",
                        "description": "Erhaltung der Zusammensetzung der Wohnbevölkerung",
                    },
                    "3000": {
                        "name": "Umstrukturierung",
                        "description": "Erhaltung bei städtebaulichen Umstrukturierungen",
                    },
                },
                "typename": "BP_ErhaltungsGrund",
                "stereotype": "Enumeration",
                "multiplicity": "1",
            },
        ),
    ]


class BPErneuerbareEnergieFlaeche(BPUeberlagerungsobjekt):
    """Festsetzung nach §9 Abs. 1 Nr. 23b: Gebiete in denen bei der Errichtung von Gebäuden bestimmte bauliche Maßnahmen für den Einsatz erneuerbarer Energien wie insbesondere Solarenergie getroffen werden müssen."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    technischeMaßnahme: Annotated[
        str | None,
        Field(
            description="Beschreibung der baulichen oder sonstigen technischen Maßnahme.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPFestsetzungNachLandesrecht(BPGeometrieobjekt):
    """Festsetzung nacvh §9 Nr. (4) BauGB"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    kurzbeschreibung: Annotated[
        str | None,
        Field(
            description="Kurzbeschreibung der Festsetzung",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPFirstRichtungsLinie(BPLinienobjekt):
    """Gestaltungs-Festsetzung der Firstrichtung, beruhend auf Landesrecht, gemäß §9 Abs. 4 BauGB."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class BPFoerderungsFlaeche(BPUeberlagerungsobjekt):
    """Fläche, auf der ganz oder teilweise nur Wohngebäude, die mit Mitteln der sozialen Wohnraumförderung gefördert werden könnten, errichtet werden dürfen (§9, Abs. 1, Nr. 7 BauGB)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class BPFreiFlaeche(BPUeberlagerungsobjekt):
    """Umgrenzung der Flächen, die von der Bebauung freizuhalten sind, und ihre Nutzung (§ 9 Abs. 1 Nr. 10 BauGB)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    nutzung: Annotated[
        str | None,
        Field(
            description="Festgesetzte Nutzung der Freifläche.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPGebaeudeFlaeche(BPUeberlagerungsobjekt):
    """Grundrissfläche eines existierenden Gebäudes"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class BPGemeinschaftsanlagenFlaeche(BPUeberlagerungsobjekt):
    """Fläche für Gemeinschaftsanlagen für bestimmte räumliche Bereiche wie    Kinderspielplätze, Freizeiteinrichtungen, Stellplätze und Garagen (§9 Abs. 22 BauGB)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    zweckbestimmung: Annotated[
        list[
            Literal[
                "1000",
                "2000",
                "3000",
                "3100",
                "3200",
                "3300",
                "3400",
                "3500",
                "3600",
                "3700",
                "3800",
                "3900",
                "4000",
                "9999",
            ]
        ]
        | None,
        Field(
            description="Zweckbestimmung der Fläche",
            json_schema_extra={
                "typename": "BP_ZweckbestimmungGemeinschaftsanlagen",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {
                        "name": "Gemeinschaftsstellplaetze",
                        "description": "Gemeinschaftliche Stellplätze",
                    },
                    "2000": {
                        "name": "Gemeinschaftsgaragen",
                        "description": "Gemeinschaftsgaragen",
                    },
                    "3000": {"name": "Spielplatz", "description": "Spielplatz"},
                    "3100": {"name": "Carport", "description": "Carport"},
                    "3200": {
                        "name": "GemeinschaftsTiefgarage",
                        "description": "Gemeinschafts-Tiefgarage",
                    },
                    "3300": {"name": "Nebengebaeude", "description": "Nebengebäude"},
                    "3400": {
                        "name": "AbfallSammelanlagen",
                        "description": "Abfall-Sammelanlagen",
                    },
                    "3500": {
                        "name": "EnergieVerteilungsanlagen",
                        "description": "Energie-Verteilungsanlagen",
                    },
                    "3600": {
                        "name": "AbfallWertstoffbehaelter",
                        "description": "Abfall-Wertstoffbehälter",
                    },
                    "3700": {
                        "name": "Freizeiteinrichtungen",
                        "description": "Freizeiteinrichtungen",
                    },
                    "3800": {
                        "name": "Laermschutzanlagen",
                        "description": "Lärmschutz-Anlagen",
                    },
                    "3900": {
                        "name": "AbwasserRegenwasser",
                        "description": "Anlagen für Abwasser oder Regenwasser",
                    },
                    "4000": {
                        "name": "Ausgleichsmassnahmen",
                        "description": "Fläche für Ausgleichsmaßnahmen",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstige Zweckbestimmung",
                    },
                },
            },
        ),
    ] = None
    weitereZweckbestimmung1: Annotated[
        Literal[
            "1000",
            "2000",
            "3000",
            "3100",
            "3200",
            "3300",
            "3400",
            "3500",
            "3600",
            "3700",
            "3800",
            "3900",
            "4000",
            "9999",
        ]
        | None,
        Field(
            description='Weitere Zweckbestimmung der Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Gemeinschaftsstellplaetze",
                        "description": "Gemeinschaftliche Stellplätze",
                    },
                    "2000": {
                        "name": "Gemeinschaftsgaragen",
                        "description": "Gemeinschaftsgaragen",
                    },
                    "3000": {"name": "Spielplatz", "description": "Spielplatz"},
                    "3100": {"name": "Carport", "description": "Carport"},
                    "3200": {
                        "name": "GemeinschaftsTiefgarage",
                        "description": "Gemeinschafts-Tiefgarage",
                    },
                    "3300": {"name": "Nebengebaeude", "description": "Nebengebäude"},
                    "3400": {
                        "name": "AbfallSammelanlagen",
                        "description": "Abfall-Sammelanlagen",
                    },
                    "3500": {
                        "name": "EnergieVerteilungsanlagen",
                        "description": "Energie-Verteilungsanlagen",
                    },
                    "3600": {
                        "name": "AbfallWertstoffbehaelter",
                        "description": "Abfall-Wertstoffbehälter",
                    },
                    "3700": {
                        "name": "Freizeiteinrichtungen",
                        "description": "Freizeiteinrichtungen",
                    },
                    "3800": {
                        "name": "Laermschutzanlagen",
                        "description": "Lärmschutz-Anlagen",
                    },
                    "3900": {
                        "name": "AbwasserRegenwasser",
                        "description": "Anlagen für Abwasser oder Regenwasser",
                    },
                    "4000": {
                        "name": "Ausgleichsmassnahmen",
                        "description": "Fläche für Ausgleichsmaßnahmen",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstige Zweckbestimmung",
                    },
                },
                "typename": "BP_ZweckbestimmungGemeinschaftsanlagen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung2: Annotated[
        Literal[
            "1000",
            "2000",
            "3000",
            "3100",
            "3200",
            "3300",
            "3400",
            "3500",
            "3600",
            "3700",
            "3800",
            "3900",
            "4000",
            "9999",
        ]
        | None,
        Field(
            description='Weitere Zweckbestimmung der Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Gemeinschaftsstellplaetze",
                        "description": "Gemeinschaftliche Stellplätze",
                    },
                    "2000": {
                        "name": "Gemeinschaftsgaragen",
                        "description": "Gemeinschaftsgaragen",
                    },
                    "3000": {"name": "Spielplatz", "description": "Spielplatz"},
                    "3100": {"name": "Carport", "description": "Carport"},
                    "3200": {
                        "name": "GemeinschaftsTiefgarage",
                        "description": "Gemeinschafts-Tiefgarage",
                    },
                    "3300": {"name": "Nebengebaeude", "description": "Nebengebäude"},
                    "3400": {
                        "name": "AbfallSammelanlagen",
                        "description": "Abfall-Sammelanlagen",
                    },
                    "3500": {
                        "name": "EnergieVerteilungsanlagen",
                        "description": "Energie-Verteilungsanlagen",
                    },
                    "3600": {
                        "name": "AbfallWertstoffbehaelter",
                        "description": "Abfall-Wertstoffbehälter",
                    },
                    "3700": {
                        "name": "Freizeiteinrichtungen",
                        "description": "Freizeiteinrichtungen",
                    },
                    "3800": {
                        "name": "Laermschutzanlagen",
                        "description": "Lärmschutz-Anlagen",
                    },
                    "3900": {
                        "name": "AbwasserRegenwasser",
                        "description": "Anlagen für Abwasser oder Regenwasser",
                    },
                    "4000": {
                        "name": "Ausgleichsmassnahmen",
                        "description": "Fläche für Ausgleichsmaßnahmen",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstige Zweckbestimmung",
                    },
                },
                "typename": "BP_ZweckbestimmungGemeinschaftsanlagen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung3: Annotated[
        Literal[
            "1000",
            "2000",
            "3000",
            "3100",
            "3200",
            "3300",
            "3400",
            "3500",
            "3600",
            "3700",
            "3800",
            "3900",
            "4000",
            "9999",
        ]
        | None,
        Field(
            description='Weitere Zweckbestimmung der Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Gemeinschaftsstellplaetze",
                        "description": "Gemeinschaftliche Stellplätze",
                    },
                    "2000": {
                        "name": "Gemeinschaftsgaragen",
                        "description": "Gemeinschaftsgaragen",
                    },
                    "3000": {"name": "Spielplatz", "description": "Spielplatz"},
                    "3100": {"name": "Carport", "description": "Carport"},
                    "3200": {
                        "name": "GemeinschaftsTiefgarage",
                        "description": "Gemeinschafts-Tiefgarage",
                    },
                    "3300": {"name": "Nebengebaeude", "description": "Nebengebäude"},
                    "3400": {
                        "name": "AbfallSammelanlagen",
                        "description": "Abfall-Sammelanlagen",
                    },
                    "3500": {
                        "name": "EnergieVerteilungsanlagen",
                        "description": "Energie-Verteilungsanlagen",
                    },
                    "3600": {
                        "name": "AbfallWertstoffbehaelter",
                        "description": "Abfall-Wertstoffbehälter",
                    },
                    "3700": {
                        "name": "Freizeiteinrichtungen",
                        "description": "Freizeiteinrichtungen",
                    },
                    "3800": {
                        "name": "Laermschutzanlagen",
                        "description": "Lärmschutz-Anlagen",
                    },
                    "3900": {
                        "name": "AbwasserRegenwasser",
                        "description": "Anlagen für Abwasser oder Regenwasser",
                    },
                    "4000": {
                        "name": "Ausgleichsmassnahmen",
                        "description": "Fläche für Ausgleichsmaßnahmen",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstige Zweckbestimmung",
                    },
                },
                "typename": "BP_ZweckbestimmungGemeinschaftsanlagen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung4: Annotated[
        Literal[
            "1000",
            "2000",
            "3000",
            "3100",
            "3200",
            "3300",
            "3400",
            "3500",
            "3600",
            "3700",
            "3800",
            "3900",
            "4000",
            "9999",
        ]
        | None,
        Field(
            description='Weitere Zweckbestimmung der Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Gemeinschaftsstellplaetze",
                        "description": "Gemeinschaftliche Stellplätze",
                    },
                    "2000": {
                        "name": "Gemeinschaftsgaragen",
                        "description": "Gemeinschaftsgaragen",
                    },
                    "3000": {"name": "Spielplatz", "description": "Spielplatz"},
                    "3100": {"name": "Carport", "description": "Carport"},
                    "3200": {
                        "name": "GemeinschaftsTiefgarage",
                        "description": "Gemeinschafts-Tiefgarage",
                    },
                    "3300": {"name": "Nebengebaeude", "description": "Nebengebäude"},
                    "3400": {
                        "name": "AbfallSammelanlagen",
                        "description": "Abfall-Sammelanlagen",
                    },
                    "3500": {
                        "name": "EnergieVerteilungsanlagen",
                        "description": "Energie-Verteilungsanlagen",
                    },
                    "3600": {
                        "name": "AbfallWertstoffbehaelter",
                        "description": "Abfall-Wertstoffbehälter",
                    },
                    "3700": {
                        "name": "Freizeiteinrichtungen",
                        "description": "Freizeiteinrichtungen",
                    },
                    "3800": {
                        "name": "Laermschutzanlagen",
                        "description": "Lärmschutz-Anlagen",
                    },
                    "3900": {
                        "name": "AbwasserRegenwasser",
                        "description": "Anlagen für Abwasser oder Regenwasser",
                    },
                    "4000": {
                        "name": "Ausgleichsmassnahmen",
                        "description": "Fläche für Ausgleichsmaßnahmen",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstige Zweckbestimmung",
                    },
                },
                "typename": "BP_ZweckbestimmungGemeinschaftsanlagen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteZweckbestimmung: Annotated[
        list[AnyUrl] | None,
        Field(
            description="Über eine CodeList definierte zusätzliche Zweckbestimmung.",
            json_schema_extra={
                "typename": "BP_DetailZweckbestGemeinschaftsanlagen",
                "stereotype": "Codelist",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung1: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestGemeinschaftsanlagen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung2: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestGemeinschaftsanlagen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung3: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestGemeinschaftsanlagen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung4: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestGemeinschaftsanlagen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Zmax: Annotated[
        int | None,
        Field(
            description="Maximale Anzahl von Garagen-Geschossen",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    eigentuemer: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "BP_BaugebietsTeilFlaeche",
                "stereotype": "Association",
                "multiplicity": "0..*",
            }
        ),
    ] = None


class BPGemeinschaftsanlagenZuordnung(BPGeometrieobjekt):
    """Zuordnung von Gemeinschaftsanlagen zu Grundstücken."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    zuordnung: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            description="Relation auf die zugeordneten Gemeinschaftsanlagen-Flächen, die außerhalb des Baugebiets liegen.",
            json_schema_extra={
                "typename": "BP_GemeinschaftsanlagenFlaeche",
                "stereotype": "Association",
                "multiplicity": "0..*",
            },
        ),
    ] = None


class BPGenerischesObjekt(BPGeometrieobjekt):
    """Klasse zur Modellierung aller Inhalte des BPlans, die keine nachrichtliche Übernahmen aus anderen Rechtsbereichen sind, aber durch keine andere Klasse des BPlan-Fachschemas dargestellt werden können."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    weitereZweckbestimmung2: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte weitere Zweckbestimmung des Objektes. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_ZweckbestimmungGenerischeObjekte",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung3: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte weitere Zweckbestimmung des Objektes. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_ZweckbestimmungGenerischeObjekte",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung4: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte weitere Zweckbestimmung des Objektes. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_ZweckbestimmungGenerischeObjekte",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    zweckbestimmung: Annotated[
        list[AnyUrl] | None,
        Field(
            description="Über eine CodeList definierte Zweckbestimmungen des Objektes.",
            json_schema_extra={
                "typename": "BP_ZweckbestimmungGenerischeObjekte",
                "stereotype": "Codelist",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    weitereZweckbestimmung1: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte weitere Zweckbestimmung des Objektes. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_ZweckbestimmungGenerischeObjekte",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPLuftreinhalteFlaeche(BPUeberlagerungsobjekt):
    """Festsetzung von Gebieten, in denen zum Schutz vor schädlichen Umwelteinwirkungen im Sinne des Bundes-Immissionsschutzgesetzes bestimmte Luft verunreinigende Stoffe nicht oder nur beschränkt verwendet werden dürfen (§9, Abs. 1, Nr. 23a BauGB)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class BPNebenanlagenAusschlussFlaeche(BPUeberlagerungsobjekt):
    """Festsetzung einer Fläche für die Einschränkung oder den Ausschluss von Nebenanlagen."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    typ: Annotated[
        Literal["1000", "2000"] | None,
        Field(
            description="Art des Ausschlusses.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Einschraenkung"},
                    "2000": {"name": "Ausschluss"},
                },
                "typename": "BP_NebenanlagenAusschlussTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    abweichungText: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": [
                    "BP_TextAbschnitt",
                    "FP_TextAbschnitt",
                    "LP_TextAbschnitt",
                    "RP_TextAbschnitt",
                    "SO_TextAbschnitt",
                    "XP_TextAbschnitt",
                ],
                "stereotype": "Association",
                "multiplicity": "0..*",
            }
        ),
    ] = None


class BPNebenanlagenFlaeche(BPUeberlagerungsobjekt):
    """Fläche für Nebenanlagen, die auf Grund anderer Vorschriften für die Nutzung von Grundstücken erforderlich sind, wie Spiel-, Freizeit- und Erholungsflächen sowie die Fläche für Stellplätze und Garagen mit ihren Einfahrten (§9 Abs. 4 BauGB)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    zweckbestimmung: Annotated[
        list[
            Literal[
                "1000",
                "2000",
                "3000",
                "3100",
                "3200",
                "3300",
                "3400",
                "3500",
                "3600",
                "9999",
            ]
        ]
        | None,
        Field(
            description="Zweckbestimmungen der Nebenanlagen-Fläche",
            json_schema_extra={
                "typename": "BP_ZweckbestimmungNebenanlagen",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Stellplaetze", "description": "Stellplätze"},
                    "2000": {"name": "Garagen", "description": "Garagen"},
                    "3000": {"name": "Spielplatz", "description": "Spielplatz"},
                    "3100": {"name": "Carport", "description": "Carport"},
                    "3200": {"name": "Tiefgarage", "description": "Tiefgarage"},
                    "3300": {"name": "Nebengebaeude", "description": "Nebengebäude"},
                    "3400": {
                        "name": "AbfallSammelanlagen",
                        "description": "Sammelanlagen für Abfall.",
                    },
                    "3500": {
                        "name": "EnergieVerteilungsanlagen",
                        "description": "Energie-Verteilungsanlagen",
                    },
                    "3600": {
                        "name": "AbfallWertstoffbehaelter",
                        "description": "Abfall-Wertstoffbehälter",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstige Zweckbestimmung",
                    },
                },
            },
        ),
    ] = None
    weitereZweckbestimmung1: Annotated[
        Literal[
            "1000",
            "2000",
            "3000",
            "3100",
            "3200",
            "3300",
            "3400",
            "3500",
            "3600",
            "9999",
        ]
        | None,
        Field(
            description='Weitere Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Stellplaetze", "description": "Stellplätze"},
                    "2000": {"name": "Garagen", "description": "Garagen"},
                    "3000": {"name": "Spielplatz", "description": "Spielplatz"},
                    "3100": {"name": "Carport", "description": "Carport"},
                    "3200": {"name": "Tiefgarage", "description": "Tiefgarage"},
                    "3300": {"name": "Nebengebaeude", "description": "Nebengebäude"},
                    "3400": {
                        "name": "AbfallSammelanlagen",
                        "description": "Sammelanlagen für Abfall.",
                    },
                    "3500": {
                        "name": "EnergieVerteilungsanlagen",
                        "description": "Energie-Verteilungsanlagen",
                    },
                    "3600": {
                        "name": "AbfallWertstoffbehaelter",
                        "description": "Abfall-Wertstoffbehälter",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstige Zweckbestimmung",
                    },
                },
                "typename": "BP_ZweckbestimmungNebenanlagen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung2: Annotated[
        Literal[
            "1000",
            "2000",
            "3000",
            "3100",
            "3200",
            "3300",
            "3400",
            "3500",
            "3600",
            "9999",
        ]
        | None,
        Field(
            description='Weitere Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Stellplaetze", "description": "Stellplätze"},
                    "2000": {"name": "Garagen", "description": "Garagen"},
                    "3000": {"name": "Spielplatz", "description": "Spielplatz"},
                    "3100": {"name": "Carport", "description": "Carport"},
                    "3200": {"name": "Tiefgarage", "description": "Tiefgarage"},
                    "3300": {"name": "Nebengebaeude", "description": "Nebengebäude"},
                    "3400": {
                        "name": "AbfallSammelanlagen",
                        "description": "Sammelanlagen für Abfall.",
                    },
                    "3500": {
                        "name": "EnergieVerteilungsanlagen",
                        "description": "Energie-Verteilungsanlagen",
                    },
                    "3600": {
                        "name": "AbfallWertstoffbehaelter",
                        "description": "Abfall-Wertstoffbehälter",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstige Zweckbestimmung",
                    },
                },
                "typename": "BP_ZweckbestimmungNebenanlagen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung3: Annotated[
        Literal[
            "1000",
            "2000",
            "3000",
            "3100",
            "3200",
            "3300",
            "3400",
            "3500",
            "3600",
            "9999",
        ]
        | None,
        Field(
            description='Weitere Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Stellplaetze", "description": "Stellplätze"},
                    "2000": {"name": "Garagen", "description": "Garagen"},
                    "3000": {"name": "Spielplatz", "description": "Spielplatz"},
                    "3100": {"name": "Carport", "description": "Carport"},
                    "3200": {"name": "Tiefgarage", "description": "Tiefgarage"},
                    "3300": {"name": "Nebengebaeude", "description": "Nebengebäude"},
                    "3400": {
                        "name": "AbfallSammelanlagen",
                        "description": "Sammelanlagen für Abfall.",
                    },
                    "3500": {
                        "name": "EnergieVerteilungsanlagen",
                        "description": "Energie-Verteilungsanlagen",
                    },
                    "3600": {
                        "name": "AbfallWertstoffbehaelter",
                        "description": "Abfall-Wertstoffbehälter",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstige Zweckbestimmung",
                    },
                },
                "typename": "BP_ZweckbestimmungNebenanlagen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung4: Annotated[
        Literal[
            "1000",
            "2000",
            "3000",
            "3100",
            "3200",
            "3300",
            "3400",
            "3500",
            "3600",
            "9999",
        ]
        | None,
        Field(
            description='Weitere Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Stellplaetze", "description": "Stellplätze"},
                    "2000": {"name": "Garagen", "description": "Garagen"},
                    "3000": {"name": "Spielplatz", "description": "Spielplatz"},
                    "3100": {"name": "Carport", "description": "Carport"},
                    "3200": {"name": "Tiefgarage", "description": "Tiefgarage"},
                    "3300": {"name": "Nebengebaeude", "description": "Nebengebäude"},
                    "3400": {
                        "name": "AbfallSammelanlagen",
                        "description": "Sammelanlagen für Abfall.",
                    },
                    "3500": {
                        "name": "EnergieVerteilungsanlagen",
                        "description": "Energie-Verteilungsanlagen",
                    },
                    "3600": {
                        "name": "AbfallWertstoffbehaelter",
                        "description": "Abfall-Wertstoffbehälter",
                    },
                    "9999": {
                        "name": "Sonstiges",
                        "description": "Sonstige Zweckbestimmung",
                    },
                },
                "typename": "BP_ZweckbestimmungNebenanlagen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteZweckbestimmung: Annotated[
        list[AnyUrl] | None,
        Field(
            description="Über eine CodeList definierte zusätzliche Zweckbestimmung.",
            json_schema_extra={
                "typename": "BP_DetailZweckbestNebenanlagen",
                "stereotype": "Codelist",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung1: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestNebenanlagen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung2: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestNebenanlagen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung3: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestNebenanlagen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung4: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "BP_DetailZweckbestNebenanlagen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Zmax: Annotated[
        int | None,
        Field(
            description="Maximale Anzahl der Garagengeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPPersGruppenBestimmteFlaeche(BPUeberlagerungsobjekt):
    """Fläche, auf denen ganz oder teilweise nur Wohngebäude errichtet werden dürfen, die für Personengruppen mit besonderem Wohnbedarf bestimmt sind (§9, Abs. 1, Nr. 8 BauGB)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class BPRegelungVergnuegungsstaetten(BPUeberlagerungsobjekt):
    """Festsetzung nach §9 Abs. 2b BauGB (Zulässigkeit von Vergnügungsstätten)"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    zulaessigkeit: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Zulässigkeit von Vergnügungsstätten.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Zulaessig",
                        "description": "Vergnügungsstätten sind generell zulässig.",
                    },
                    "2000": {
                        "name": "NichtZulaessig",
                        "description": "Vergnügungsstätten sind generell nicht zulässig.",
                    },
                    "3000": {
                        "name": "AusnahmsweiseZulaessig",
                        "description": "Vergnügungsstätten sind ausnahmsweise zulässig.",
                    },
                },
                "typename": "BP_ZulaessigkeitVergnuegungsstaetten",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class BPSpezielleBauweise(BPUeberlagerungsobjekt):
    """Festsetzung der speziellen Bauweise / baulichen Besonderheit eines Gebäudes oder Bauwerks."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    typ: Annotated[
        Literal["1000", "1100", "1200", "1300", "1400", "1500", "9999"] | None,
        Field(
            description="Typ der speziellen Bauweise.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Durchfahrt"},
                    "1100": {"name": "Durchgang"},
                    "1200": {"name": "DurchfahrtDurchgang"},
                    "1300": {"name": "Auskragung"},
                    "1400": {"name": "Arkade"},
                    "1500": {"name": "Luftgeschoss"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "BP_SpezielleBauweiseTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    sonstTyp: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definierter Typ der speziellen Bauweise.",
            json_schema_extra={
                "typename": "BP_SpezielleBauweiseSonstTypen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Bmin: Annotated[
        definitions.Length | None,
        Field(
            description="Minimale Breite von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Bmax: Annotated[
        definitions.Length | None,
        Field(
            description="Naximale Breite von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Tmin: Annotated[
        definitions.Length | None,
        Field(
            description="Minimale Tiefe von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Tmax: Annotated[
        definitions.Length | None,
        Field(
            description="Maximale Tiefe von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None


class BPTextlicheFestsetzungsFlaeche(BPUeberlagerungsobjekt):
    """Bereich in dem bestimmte Textliche Festsetzungen gültig sind, die über die Relation "refTextInhalt" (Basisklasse XP_Objekt) spezifiziert werden."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class BPUeberbaubareGrundstuecksFlaeche(BPUeberlagerungsobjekt):
    """Festsetzung der überbaubaren Grundstücksfläche (§9, Abs. 1, Nr. 2 BauGB). Über die Attribute geschossMin und geschossMax kann die Festsetzung auf einen Bereich von Geschossen beschränkt werden. Wenn eine Einschränkung der Festsetzung durch expliziter Höhenangaben erfolgen soll, ist dazu die Oberklassen-Relation hoehenangabe auf den komplexen Datentyp XP_Hoehenangabe zu verwenden."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    MaxZahlWohnungen: Annotated[
        int | None,
        Field(
            description="Höchstzulässige Zahl der Wohnungen in Wohngebäuden",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Fmin: Annotated[
        definitions.Area | None,
        Field(
            description="Mindestmaß für die Größe (Fläche) eines Baugrundstücks.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Fmax: Annotated[
        definitions.Area | None,
        Field(
            description="Höchstmaß für die Größe (Fläche) eines Baugrundstücks.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Bmin: Annotated[
        definitions.Length | None,
        Field(
            description="Minimale Breite von Baugrundstücken",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Bmax: Annotated[
        definitions.Length | None,
        Field(
            description="Maximale Breite von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Tmin: Annotated[
        definitions.Length | None,
        Field(
            description="Minimale Tiefe von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    Tmax: Annotated[
        definitions.Length | None,
        Field(
            description="Maximale Tiefe von Baugrundstücken.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    GFZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Geschossflächenzahl .",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl bei einer Bereichsangabe. Das Attribut GFZmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZ_Ausn: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Geschossflächenzahl als Ausnahme.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFmin: Annotated[
        definitions.Area | None,
        Field(
            description="Minimal zulässige Geschossfläche",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GFmax: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Geschossfläche bei einer Bereichsabgabe. Das Attribut GFmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GF: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Geschossfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GF_Ausn: Annotated[
        definitions.Area | None,
        Field(
            description="Ausnahmsweise maximal zulässige Geschossfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    BMZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Baumassenzahl",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Baumassenzahl bei einer Bereichsangabe. Das Attribut BMZmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Baumassenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZ_Ausn: Annotated[
        float | None,
        Field(
            description="Ausnahmsweise maximal zulässige Baumassenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMmin: Annotated[
        definitions.Volume | None,
        Field(
            description="Minimal zulässinge Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BMmax: Annotated[
        definitions.Volume | None,
        Field(
            description="Maximal zulässinge Baumasse bei einer Bereichsangabe. Das Attribut BMmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BM: Annotated[
        definitions.Volume | None,
        Field(
            description="Maximal zulässige Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    BM_Ausn: Annotated[
        definitions.Volume | None,
        Field(
            description="Ausnahmsweise maximal zulässige Baumasse.",
            json_schema_extra={
                "typename": "Volume",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m3",
            },
        ),
    ] = None
    GRZmin: Annotated[
        float | None,
        Field(
            description="Minimal zulässige Grundflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZmax: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Grundflächenzahl bei einer Bereichsangabe.  Das Attribut GRZmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZ: Annotated[
        float | None,
        Field(
            description="Maximal zulässige Grundflächenzahl",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZ_Ausn: Annotated[
        float | None,
        Field(
            description="Ausnahmsweise maximal zulässige Grundflächenzahl.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRmin: Annotated[
        definitions.Area | None,
        Field(
            description="Minimal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GRmax: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Grundfläche bei einer Bereichsangabe. Das Attribut GRmin muss ebenfalls spezifiziert werden.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GR: Annotated[
        definitions.Area | None,
        Field(
            description="Maximal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    GR_Ausn: Annotated[
        definitions.Area | None,
        Field(
            description="Ausnahmsweise maximal zulässige Grundfläche.",
            json_schema_extra={
                "typename": "Area",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m2",
            },
        ),
    ] = None
    Zmin: Annotated[
        int | None,
        Field(
            description="Minimal zulässige Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Zmax: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der oberirdischen Vollgeschosse bei einer Bereichsangabe. Das Attribut Zmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Zzwingend: Annotated[
        int | None,
        Field(
            description="Zwingend vorgeschriebene Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z: Annotated[
        int | None,
        Field(
            description="Maximalzahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Ausn: Annotated[
        int | None,
        Field(
            description="Ausnahmsweise maximal zulässige Zahl der oberirdischen Vollgeschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Staffel: Annotated[
        int | None,
        Field(
            description="Maximalzahl von oberirdischen zurückgesetzten Vollgeschossen als Staffelgeschoss..",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    Z_Dach: Annotated[
        int | None,
        Field(
            description="Maximalzahl der zusätzlich erlaubten Dachgeschosse, die gleichzeitig Vollgeschosse sind.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUmin: Annotated[
        int | None,
        Field(
            description="Minimal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUmax: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der unterirdischen Geschosse bei einer Bereichsangabe. Das Attribut ZUmin muss ebenfalls belegt sein.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZUzwingend: Annotated[
        int | None,
        Field(
            description="Zwingend vorgeschriebene Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZU: Annotated[
        int | None,
        Field(
            description="Maximal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ZU_Ausn: Annotated[
        int | None,
        Field(
            description="Ausnahmsweise maximal zulässige Zahl der unterirdischen Geschosse.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    geschossMin: Annotated[
        int | None,
        Field(
            description="Gibt bei geschossweiser Festsetzung die Nummer des Geschosses an, ab den die Festsetzung gilt. Wenn das Attribut nicht belegt ist, gilt die Festsetzung für alle Geschosse bis einschl. geschossMax.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    geschossMax: Annotated[
        int | None,
        Field(
            description="Gibt bei geschossweiser Feststzung die Nummer des Geschosses an, bis zu der die Festsetzung gilt. Wenn das Attribut nicht belegt ist, gilt die Festsetzung für alle Geschosse ab einschl. geschossMin.",
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    baugrenze: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "BP_BauGrenze",
                "stereotype": "Association",
                "multiplicity": "0..*",
            }
        ),
    ] = None
    baulinie: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            json_schema_extra={
                "typename": "BP_BauLinie",
                "stereotype": "Association",
                "multiplicity": "0..*",
            }
        ),
    ] = None


class FPAbgrabung(FPGeometrieobjekt):
    """Flächen für Aufschüttungen, Abgrabungen oder für die Gewinnung von Bodenschätzen (§5, Abs. 2, Nr. 8 BauGB). Hier: Flächen für Abgrabungen"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class FPAbgrabungsFlaeche(FPFlaechenobjekt):
    """Flächen für Aufschüttungen, Abgrabungen oder für die Gewinnung von Bodenschätzen (§5, Abs. 2, Nr. 8 BauGB). Hier: Flächen für Abgrabungen. Diese Klasse ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen FP_Abgrabung mit Flächengeometrie benutzt werden."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class FPAnpassungKlimawandel(FPGeometrieobjekt):
    """Anlagen, Einrichtungen und sonstige Maßnahmen, die der Anpassung an den Klimawandel dienen."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class FPAufschuettung(FPGeometrieobjekt):
    """Flächen für Aufschüttungen, Abgrabungen oder für die Gewinnung von Bodenschätzen (§5, Abs. 2, Nr. 8 BauGB). Hier: Flächen für Aufschüttungen."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class FPAufschuettungsFlaeche(FPFlaechenobjekt):
    """Flächen für Aufschüttungen, Abgrabungen oder für die Gewinnung von Bodenschätzen (§5, Abs. 2, Nr. 8 BauGB). Hier: Flächen für Aufschüttungen. Diese Klasse ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen FP_Aufschuettung mit Flächengeometrie benutzt werden."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class FPAusgleichsFlaeche(FPFlaechenobjekt):
    """Flächen und Maßnahmen zum Ausgleich gemäß §5, Abs. 2a  BauBG."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    refMassnahmenText: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf ein Dokument in dem die Massnahmen beschrieben werden.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    refLandschaftsplan: Annotated[
        XPExterneReferenz | None,
        Field(
            description="Referenz auf den Landschaftsplan.",
            json_schema_extra={
                "typename": "XP_ExterneReferenz",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ziel: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"] | None,
        Field(
            description='Unterscheidung nach den Zielen "Schutz, Pflege" und "Entwicklung".',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "SchutzPflege"},
                    "2000": {"name": "Entwicklung"},
                    "3000": {"name": "Anlage"},
                    "4000": {"name": "SchutzPflegeEntwicklung"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "XP_SPEZiele",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    massnahme: Annotated[
        list[XPSPEMassnahmenDaten] | None,
        Field(
            description="Auf der Fläche durchzuführende Maßnahmen.",
            json_schema_extra={
                "typename": "XP_SPEMassnahmenDaten",
                "stereotype": "DataType",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    weitereMassnahme1: Annotated[
        XPSPEMassnahmenDaten | None,
        Field(
            description='Weitere durchzuführende Massnahme. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen massnahme mehrfach belegt werden.',
            json_schema_extra={
                "typename": "XP_SPEMassnahmenDaten",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereMassnahme2: Annotated[
        XPSPEMassnahmenDaten | None,
        Field(
            description='Weitere durchzufühende Massnahme. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen massnahme mehrfach belegt werden.',
            json_schema_extra={
                "typename": "XP_SPEMassnahmenDaten",
                "stereotype": "DataType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class FPBebauungsFlaeche(FPFlaechenschlussobjekt):
    """Darstellung der für die Bebauung vorgesehenen Flächen (§5, Abs. 2, Nr. 1 BauGB)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    GFZ: Annotated[
        float | None,
        Field(
            description="Angabe einer maximalen Geschossflächenzahl als Maß der baulichen Nutzung.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZmin: Annotated[
        float | None,
        Field(
            description="Minimale Geschossflächenzahl bei einer Bereichsangabe (GFZmax muss ebenfalls spezifiziert werden).",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GFZmax: Annotated[
        float | None,
        Field(
            description="Maximale Geschossflächenzahl bei einer Bereichsangabe (GFZmin muss ebenfalls spezifiziert werden).",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    BMZ: Annotated[
        float | None,
        Field(
            description="Angabe einermaximalen Baumassenzahl als Maß der baulichen Nutzung.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    GRZ: Annotated[
        float | None,
        Field(
            description="Angabe einer maximalen Grundflächenzahl als Maß der baulichen Nutzung.",
            json_schema_extra={
                "typename": "Decimal",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    allgArtDerBaulNutzung: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"] | None,
        Field(
            description="Angabe der allgemeinen Art der baulichen Nutzung.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "WohnBauflaeche"},
                    "2000": {"name": "GemischteBauflaeche"},
                    "3000": {"name": "GewerblicheBauflaeche"},
                    "4000": {"name": "SonderBauflaeche"},
                    "9999": {"name": "SonstigeBauflaeche"},
                },
                "typename": "XP_AllgArtDerBaulNutzung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    besondereArtDerBaulNutzung: Annotated[
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
            "2000",
            "2100",
            "3000",
            "4000",
            "9999",
        ]
        | None,
        Field(
            description="Angabe der besonderen Art der baulichen Nutzung.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "Kleinsiedlungsgebiet",
                        "description": "Kleinsiedlungsgebiet",
                    },
                    "1100": {
                        "name": "ReinesWohngebiet",
                        "description": "Reines Wohngebiet",
                    },
                    "1200": {
                        "name": "AllgWohngebiet",
                        "description": "Allgemeines Wohngebiet",
                    },
                    "1300": {
                        "name": "BesonderesWohngebiet",
                        "description": "Besonderes Wohngebiet",
                    },
                    "1400": {"name": "Dorfgebiet", "description": "Dorfgebiet"},
                    "1500": {"name": "Mischgebiet"},
                    "1600": {"name": "Kerngebiet", "description": "Kerngebiet"},
                    "1700": {"name": "Gewerbegebiet"},
                    "1800": {
                        "name": "Industriegebiet",
                        "description": "Industriegebiet",
                    },
                    "2000": {
                        "name": "SondergebietErholung",
                        "description": "Sondergebiet, das der Erholung dient (§ 10 BauNVO); z.B. Wochenendhausgebiet",
                    },
                    "2100": {
                        "name": "SondergebietSonst",
                        "description": "Sonstiges Sondergebiet (§ 11 BauNVO); z.B. Klinikgebiet",
                    },
                    "3000": {"name": "Wochenendhausgebiet"},
                    "4000": {"name": "Sondergebiet"},
                    "9999": {
                        "name": "SonstigesGebiet",
                        "description": "Sonstiges Gebiet",
                    },
                },
                "typename": "XP_BesondereArtDerBaulNutzung",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    sonderNutzung: Annotated[
        Literal[
            "1000",
            "1100",
            "1200",
            "1300",
            "1400",
            "1500",
            "1600",
            "16000",
            "16001",
            "16002",
            "1700",
            "1800",
            "1900",
            "2000",
            "2100",
            "2200",
            "2300",
            "2400",
            "2500",
            "2600",
            "2700",
            "2800",
            "2900",
            "9999",
        ]
        | None,
        Field(
            description='Bei Nutzungsform "Sondergebiet": Differenzierung verschiedener Arten von Sondergebieten nach §§ 10 und 11 BauNVO.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Wochenendhausgebiet"},
                    "1100": {"name": "Ferienhausgebiet"},
                    "1200": {"name": "Campingplatzgebiet"},
                    "1300": {"name": "Kurgebiet"},
                    "1400": {"name": "SonstSondergebietErholung"},
                    "1500": {"name": "Einzelhandelsgebiet"},
                    "1600": {"name": "GrossflaechigerEinzelhandel"},
                    "16000": {"name": "Ladengebiet"},
                    "16001": {"name": "Einkaufszentrum"},
                    "16002": {"name": "SonstGrossflEinzelhandel"},
                    "1700": {"name": "Verkehrsuebungsplatz"},
                    "1800": {"name": "Hafengebiet"},
                    "1900": {"name": "SondergebietErneuerbareEnergie"},
                    "2000": {"name": "SondergebietMilitaer"},
                    "2100": {"name": "SondergebietLandwirtschaft"},
                    "2200": {"name": "SondergebietSport"},
                    "2300": {"name": "SondergebietGesundheitSoziales"},
                    "2400": {"name": "Golfplatz"},
                    "2500": {"name": "SondergebietKultur"},
                    "2600": {"name": "SondergebietTourismus"},
                    "2700": {"name": "SondergebietBueroUndVerwaltung"},
                    "2800": {"name": "SondergebietHochschuleEinrichtungen"},
                    "2900": {"name": "SondergebietMesse"},
                    "9999": {"name": "SondergebietAndereNutzungen"},
                },
                "typename": "XP_Sondernutzungen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteArtDerBaulNutzung: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definierte Art der baulichen Nutzung.",
            json_schema_extra={
                "typename": "FP_DetailArtDerBaulNutzung",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    nutzungText: Annotated[
        str | None,
        Field(
            description='Bei Nutzungsform "Sondergebiet": Kurzform der besonderen Art der baulichen Nutzung.',
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class FPBodenschaetze(FPGeometrieobjekt):
    """Flächen für Aufschüttungen, Abgrabungen oder für die Gewinnung von Bodenschätzen (§5, Abs. 2, Nr. 8 BauGB. Hier: Flächen für Bodenschätze."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    abbaugut: Annotated[
        str | None,
        Field(
            description="Bezeichnung des Abbauguts.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class FPBodenschaetzeFlaeche(FPFlaechenobjekt):
    """Flächen für Aufschüttungen, Abgrabungen oder für die Gewinnung von Bodenschätzen (§5, Abs. 2, Nr. 8 BauGB. Hier: Flächen für Bodenschätze. Diese Klasse ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen FP_Bodenschaetze mit Flächengeometrie benutzt werden."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    abbaugut: Annotated[
        str | None,
        Field(
            description="Bezeichnung des Abbauguts.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class FPGemeinbedarf(FPGeometrieobjekt):
    """Darstellung von Flächen für den Gemeinbedarf nach §5,  Abs. 2, Nr. 2 BauGB."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    zweckbestimmung: Annotated[
        list[
            Literal[
                "1000",
                "1200",
                "1400",
                "1600",
                "1800",
                "2000",
                "2200",
                "2400",
                "2600",
                "9999",
            ]
        ]
        | None,
        Field(
            description="Allgemeine Zweckbestimmungen der Fläche",
            json_schema_extra={
                "typename": "XP_ZweckbestimmungGemeinbedarf",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {
                        "name": "OffentlicheVerwaltung",
                        "description": "Einrichtungen und Anlagen für öffentliche Verwaltung",
                    },
                    "1200": {
                        "name": "BildungForschung",
                        "description": "Einrichtungen und Anlagen für Schulen und sonstige Bildungs- und Forschungseinrichtungen.",
                    },
                    "1400": {
                        "name": "Kirche",
                        "description": "Kirchliche Einrichtungen",
                    },
                    "1600": {
                        "name": "Sozial",
                        "description": "Einrichtungen und Anlagen für soziale Zwecke.",
                    },
                    "1800": {
                        "name": "Gesundheit",
                        "description": "Einrichtungen und Anlagen für gesundheitliche Zwecke.",
                    },
                    "2000": {
                        "name": "Kultur",
                        "description": "Einrichtungen und Anlagen für kulturelle Zwecke.",
                    },
                    "2200": {
                        "name": "Sport",
                        "description": "Einrichtungen und Anlagen für sportliche Zwecke.",
                    },
                    "2400": {
                        "name": "SicherheitOrdnung",
                        "description": "Einrichtungen und Anlagen für Sicherheit und Ordnung.",
                    },
                    "2600": {
                        "name": "Infrastruktur",
                        "description": "Einrichtungen und Anlagen der Infrastruktur.",
                    },
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
            },
        ),
    ] = None
    weitereZweckbestimmung1: Annotated[
        Literal[
            "1000",
            "1200",
            "1400",
            "1600",
            "1800",
            "2000",
            "2200",
            "2400",
            "2600",
            "9999",
        ]
        | None,
        Field(
            description='Weitere allgemeine Zweckbestimmung der Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "OffentlicheVerwaltung",
                        "description": "Einrichtungen und Anlagen für öffentliche Verwaltung",
                    },
                    "1200": {
                        "name": "BildungForschung",
                        "description": "Einrichtungen und Anlagen für Schulen und sonstige Bildungs- und Forschungseinrichtungen.",
                    },
                    "1400": {
                        "name": "Kirche",
                        "description": "Kirchliche Einrichtungen",
                    },
                    "1600": {
                        "name": "Sozial",
                        "description": "Einrichtungen und Anlagen für soziale Zwecke.",
                    },
                    "1800": {
                        "name": "Gesundheit",
                        "description": "Einrichtungen und Anlagen für gesundheitliche Zwecke.",
                    },
                    "2000": {
                        "name": "Kultur",
                        "description": "Einrichtungen und Anlagen für kulturelle Zwecke.",
                    },
                    "2200": {
                        "name": "Sport",
                        "description": "Einrichtungen und Anlagen für sportliche Zwecke.",
                    },
                    "2400": {
                        "name": "SicherheitOrdnung",
                        "description": "Einrichtungen und Anlagen für Sicherheit und Ordnung.",
                    },
                    "2600": {
                        "name": "Infrastruktur",
                        "description": "Einrichtungen und Anlagen der Infrastruktur.",
                    },
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungGemeinbedarf",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung2: Annotated[
        Literal[
            "1000",
            "1200",
            "1400",
            "1600",
            "1800",
            "2000",
            "2200",
            "2400",
            "2600",
            "9999",
        ]
        | None,
        Field(
            description='Weitere allgemeine Zweckbestimmung der Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "OffentlicheVerwaltung",
                        "description": "Einrichtungen und Anlagen für öffentliche Verwaltung",
                    },
                    "1200": {
                        "name": "BildungForschung",
                        "description": "Einrichtungen und Anlagen für Schulen und sonstige Bildungs- und Forschungseinrichtungen.",
                    },
                    "1400": {
                        "name": "Kirche",
                        "description": "Kirchliche Einrichtungen",
                    },
                    "1600": {
                        "name": "Sozial",
                        "description": "Einrichtungen und Anlagen für soziale Zwecke.",
                    },
                    "1800": {
                        "name": "Gesundheit",
                        "description": "Einrichtungen und Anlagen für gesundheitliche Zwecke.",
                    },
                    "2000": {
                        "name": "Kultur",
                        "description": "Einrichtungen und Anlagen für kulturelle Zwecke.",
                    },
                    "2200": {
                        "name": "Sport",
                        "description": "Einrichtungen und Anlagen für sportliche Zwecke.",
                    },
                    "2400": {
                        "name": "SicherheitOrdnung",
                        "description": "Einrichtungen und Anlagen für Sicherheit und Ordnung.",
                    },
                    "2600": {
                        "name": "Infrastruktur",
                        "description": "Einrichtungen und Anlagen der Infrastruktur.",
                    },
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungGemeinbedarf",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung3: Annotated[
        Literal[
            "1000",
            "1200",
            "1400",
            "1600",
            "1800",
            "2000",
            "2200",
            "2400",
            "2600",
            "9999",
        ]
        | None,
        Field(
            description='Weitere allgemeine Zweckbestimmung der Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "OffentlicheVerwaltung",
                        "description": "Einrichtungen und Anlagen für öffentliche Verwaltung",
                    },
                    "1200": {
                        "name": "BildungForschung",
                        "description": "Einrichtungen und Anlagen für Schulen und sonstige Bildungs- und Forschungseinrichtungen.",
                    },
                    "1400": {
                        "name": "Kirche",
                        "description": "Kirchliche Einrichtungen",
                    },
                    "1600": {
                        "name": "Sozial",
                        "description": "Einrichtungen und Anlagen für soziale Zwecke.",
                    },
                    "1800": {
                        "name": "Gesundheit",
                        "description": "Einrichtungen und Anlagen für gesundheitliche Zwecke.",
                    },
                    "2000": {
                        "name": "Kultur",
                        "description": "Einrichtungen und Anlagen für kulturelle Zwecke.",
                    },
                    "2200": {
                        "name": "Sport",
                        "description": "Einrichtungen und Anlagen für sportliche Zwecke.",
                    },
                    "2400": {
                        "name": "SicherheitOrdnung",
                        "description": "Einrichtungen und Anlagen für Sicherheit und Ordnung.",
                    },
                    "2600": {
                        "name": "Infrastruktur",
                        "description": "Einrichtungen und Anlagen der Infrastruktur.",
                    },
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungGemeinbedarf",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung4: Annotated[
        Literal[
            "1000",
            "1200",
            "1400",
            "1600",
            "1800",
            "2000",
            "2200",
            "2400",
            "2600",
            "9999",
        ]
        | None,
        Field(
            description='Weitere allgemeine Zweckbestimmung der Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "OffentlicheVerwaltung",
                        "description": "Einrichtungen und Anlagen für öffentliche Verwaltung",
                    },
                    "1200": {
                        "name": "BildungForschung",
                        "description": "Einrichtungen und Anlagen für Schulen und sonstige Bildungs- und Forschungseinrichtungen.",
                    },
                    "1400": {
                        "name": "Kirche",
                        "description": "Kirchliche Einrichtungen",
                    },
                    "1600": {
                        "name": "Sozial",
                        "description": "Einrichtungen und Anlagen für soziale Zwecke.",
                    },
                    "1800": {
                        "name": "Gesundheit",
                        "description": "Einrichtungen und Anlagen für gesundheitliche Zwecke.",
                    },
                    "2000": {
                        "name": "Kultur",
                        "description": "Einrichtungen und Anlagen für kulturelle Zwecke.",
                    },
                    "2200": {
                        "name": "Sport",
                        "description": "Einrichtungen und Anlagen für sportliche Zwecke.",
                    },
                    "2400": {
                        "name": "SicherheitOrdnung",
                        "description": "Einrichtungen und Anlagen für Sicherheit und Ordnung.",
                    },
                    "2600": {
                        "name": "Infrastruktur",
                        "description": "Einrichtungen und Anlagen der Infrastruktur.",
                    },
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungGemeinbedarf",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung5: Annotated[
        Literal[
            "1000",
            "1200",
            "1400",
            "1600",
            "1800",
            "2000",
            "2200",
            "2400",
            "2600",
            "9999",
        ]
        | None,
        Field(
            description='Weitere allgemeine Zweckbestimmung der Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "OffentlicheVerwaltung",
                        "description": "Einrichtungen und Anlagen für öffentliche Verwaltung",
                    },
                    "1200": {
                        "name": "BildungForschung",
                        "description": "Einrichtungen und Anlagen für Schulen und sonstige Bildungs- und Forschungseinrichtungen.",
                    },
                    "1400": {
                        "name": "Kirche",
                        "description": "Kirchliche Einrichtungen",
                    },
                    "1600": {
                        "name": "Sozial",
                        "description": "Einrichtungen und Anlagen für soziale Zwecke.",
                    },
                    "1800": {
                        "name": "Gesundheit",
                        "description": "Einrichtungen und Anlagen für gesundheitliche Zwecke.",
                    },
                    "2000": {
                        "name": "Kultur",
                        "description": "Einrichtungen und Anlagen für kulturelle Zwecke.",
                    },
                    "2200": {
                        "name": "Sport",
                        "description": "Einrichtungen und Anlagen für sportliche Zwecke.",
                    },
                    "2400": {
                        "name": "SicherheitOrdnung",
                        "description": "Einrichtungen und Anlagen für Sicherheit und Ordnung.",
                    },
                    "2600": {
                        "name": "Infrastruktur",
                        "description": "Einrichtungen und Anlagen der Infrastruktur.",
                    },
                    "9999": {"name": "Sonstiges", "description": "Sonstiges"},
                },
                "typename": "XP_ZweckbestimmungGemeinbedarf",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    besondereZweckbestimmung: Annotated[
        list[
            Literal[
                "10000",
                "10001",
                "10002",
                "10003",
                "12000",
                "12001",
                "12002",
                "12003",
                "12004",
                "14000",
                "14001",
                "14002",
                "14003",
                "16000",
                "16001",
                "16002",
                "16003",
                "16004",
                "18000",
                "18001",
                "20000",
                "20001",
                "20002",
                "22000",
                "22001",
                "22002",
                "24000",
                "24001",
                "24002",
                "24003",
                "26000",
                "26001",
            ]
        ]
        | None,
        Field(
            description="Besondere Zweckbestimmungen der Fläche, die die zugehörigen allgemeinen Zweckbestimmungen detaillieren oder ersetzen..",
            json_schema_extra={
                "typename": "XP_BesondereZweckbestGemeinbedarf",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "10000": {
                        "name": "KommunaleEinrichtung",
                        "description": "Kommunale Einrichtung wie z. B. Rathaus, Gesundheitsamt, Gesundheitsfürsorgestelle, Gartenbauamt, Gartenarbeitsstützpunkt, Fuhrpark.",
                    },
                    "10001": {
                        "name": "BetriebOeffentlZweckbestimmung",
                        "description": "Betrieb mit öffentlicher Zweckbestimmung wie z.B. ein Stadtreinigungsbetrieb, Autobusbetriebshof, Omnibusbahnhof.",
                    },
                    "10002": {
                        "name": "AnlageBundLand",
                        "description": "Eine Anlage des Bundes oder eines Bundeslandes wie z. B.  Arbeitsamt, Autobahnmeisterei, Brückenmeisterei, Patentamt, Wasserbauhof, Finanzamt.",
                    },
                    "10003": {
                        "name": "SonstigeOeffentlicheVerwaltung",
                        "description": "Sonstige Einrichtung oder Anlage der öffentlichen Verwaltung wie z. B. die Industrie und Handelskammer oder Handwerkskammer.",
                    },
                    "12000": {
                        "name": "Schule",
                        "description": "Schulische Einrichtung. Darunter fallen u. a. Allgemeinbildende Schule, Oberstufenzentrum, Sonderschule, Fachschule, Volkshochschule,\r\nKonservatorium.",
                    },
                    "12001": {
                        "name": "Hochschule",
                        "description": "Hochschule, Fachhochschule, Berufsakademie, o. Ä.",
                    },
                    "12002": {
                        "name": "BerufsbildendeSchule",
                        "description": "Berufsbildende Schule",
                    },
                    "12003": {
                        "name": "Forschungseinrichtung",
                        "description": "Forschungseinrichtung, Forschungsinstitut.",
                    },
                    "12004": {
                        "name": "SonstigesBildungForschung",
                        "description": "Sonstige Anlage oder Einrichtung aus Bildung und Forschung.",
                    },
                    "14000": {
                        "name": "Sakralgebaeude",
                        "description": "Religiösen Zwecken dienendes Gebäude wie z. B. Kirche, \r\n Kapelle, Moschee, Synagoge, Gebetssaal.",
                    },
                    "14001": {
                        "name": "KirchlicheVerwaltung",
                        "description": "Kirchliches Verwaltungsgebäude, z. B. Pfarramt, Bischöfliches Ordinariat, Konsistorium.",
                    },
                    "14002": {
                        "name": "Kirchengemeinde",
                        "description": "Religiöse Gemeinde- oder Versammlungseinrichtung, z. B. Gemeindehaus, Gemeindezentrum.",
                    },
                    "14003": {
                        "name": "SonstigesKirche",
                        "description": "Sonstige religiösen Zwecken dienende Anlage oder Einrichtung.",
                    },
                    "16000": {
                        "name": "EinrichtungKinder",
                        "description": "Soziale Einrichtung für Kinder, wie z. B. Kinderheim, Kindertagesstätte, Kindergarten.",
                    },
                    "16001": {
                        "name": "EinrichtungJugendliche",
                        "description": "Soziale Einrichtung für Jugendliche, wie z. B. Jugendfreizeitheim/-stätte, Jugendgästehaus, Jugendherberge, Jugendheim.",
                    },
                    "16002": {
                        "name": "EinrichtungFamilienErwachsene",
                        "description": "Soziale Einrichtung für Familien und Erwachsene, wie z. B. Bildungszentrum, Volkshochschule, Kleinkinderfürsorgestelle, Säuglingsfürsorgestelle, Nachbarschaftsheim.",
                    },
                    "16003": {
                        "name": "EinrichtungSenioren",
                        "description": "Soziale Einrichtung für Senioren, wie z. B. Alten-/Seniorentagesstätte, Alten-/Seniorenheim, Alten-/Seniorenwohnheim, Altersheim.",
                    },
                    "16004": {
                        "name": "SonstigeSozialeEinrichtung",
                        "description": "Sonstige soziale Einrichtung, z. B. Pflegeheim, Schwesternwohnheim, Studentendorf, Studentenwohnheim. Tierheim, Übergangsheim.",
                    },
                    "18000": {
                        "name": "Krankenhaus",
                        "description": "Krankenhaus oder vergleichbare Einrichtung (z. B. Klinik, Hospital, Krankenheim, Heil- und Pflegeanstalt),",
                    },
                    "18001": {
                        "name": "SonstigesGesundheit",
                        "description": "Sonstige Gesundheits-Einrichtung, z. B. Sanatorium, Kurklinik, Desinfektionsanstalt.",
                    },
                    "20000": {
                        "name": "MusikTheater",
                        "description": "Kulturelle Einrichtung aus dem Bereich Musik oder Theater (z. B. Theater, Konzerthaus, Musikhalle, Oper).",
                    },
                    "20001": {
                        "name": "Bildung",
                        "description": "Kulturelle Einrichtung mit Bildungsfunktion ( z. B. Museum, Bibliothek, Bücherei, Stadtbücherei, Volksbücherei).",
                    },
                    "20002": {
                        "name": "SonstigeKultur",
                        "description": "Sonstige kulturelle Einrichtung, wie z. B. Archiv, Landesbildstelle, Rundfunk und Fernsehen, Kongress- und Veranstaltungshalle, Mehrzweckhalle..",
                    },
                    "22000": {
                        "name": "Bad",
                        "description": "Schwimmbad, Freibad, Hallenbad, Schwimmhalle o. Ä..",
                    },
                    "22001": {
                        "name": "SportplatzSporthalle",
                        "description": "Sportplatz, Sporthalle, Tennishalle o. Ä.",
                    },
                    "22002": {
                        "name": "SonstigerSport",
                        "description": "Sonstige Sporteinrichtung.",
                    },
                    "24000": {
                        "name": "Feuerwehr",
                        "description": "Einrichtung oder Anlage der Feuerwehr.",
                    },
                    "24001": {"name": "Schutzbauwerk", "description": "Schutzbauwerk"},
                    "24002": {
                        "name": "Justiz",
                        "description": "Einrichtung der Justiz, wie z. B. Justizvollzug, Gericht, Haftanstalt.",
                    },
                    "24003": {
                        "name": "SonstigeSicherheitOrdnung",
                        "description": "Sonstige Anlage oder Einrichtung für Sicherheit und Ordnung, z. B. Polizei, Zoll, Feuerwehr, Zivilschutz, Bundeswehr, Landesverteidigung.",
                    },
                    "26000": {"name": "Post", "description": "Einrichtung der Post."},
                    "26001": {
                        "name": "SonstigeInfrastruktur",
                        "description": "Sonstige Anlage oder Einrichtung der Infrastruktur.",
                    },
                },
            },
        ),
    ] = None
    weitereBesondZweckbestimmung1: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "12000",
            "12001",
            "12002",
            "12003",
            "12004",
            "14000",
            "14001",
            "14002",
            "14003",
            "16000",
            "16001",
            "16002",
            "16003",
            "16004",
            "18000",
            "18001",
            "20000",
            "20001",
            "20002",
            "22000",
            "22001",
            "22002",
            "24000",
            "24001",
            "24002",
            "24003",
            "26000",
            "26001",
        ]
        | None,
        Field(
            description='Weitere besondere Zweckbestimmung der Fläche, die die zugehörige allgemeine Zweckbestimmung detailliert oder ersetzt. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {
                        "name": "KommunaleEinrichtung",
                        "description": "Kommunale Einrichtung wie z. B. Rathaus, Gesundheitsamt, Gesundheitsfürsorgestelle, Gartenbauamt, Gartenarbeitsstützpunkt, Fuhrpark.",
                    },
                    "10001": {
                        "name": "BetriebOeffentlZweckbestimmung",
                        "description": "Betrieb mit öffentlicher Zweckbestimmung wie z.B. ein Stadtreinigungsbetrieb, Autobusbetriebshof, Omnibusbahnhof.",
                    },
                    "10002": {
                        "name": "AnlageBundLand",
                        "description": "Eine Anlage des Bundes oder eines Bundeslandes wie z. B.  Arbeitsamt, Autobahnmeisterei, Brückenmeisterei, Patentamt, Wasserbauhof, Finanzamt.",
                    },
                    "10003": {
                        "name": "SonstigeOeffentlicheVerwaltung",
                        "description": "Sonstige Einrichtung oder Anlage der öffentlichen Verwaltung wie z. B. die Industrie und Handelskammer oder Handwerkskammer.",
                    },
                    "12000": {
                        "name": "Schule",
                        "description": "Schulische Einrichtung. Darunter fallen u. a. Allgemeinbildende Schule, Oberstufenzentrum, Sonderschule, Fachschule, Volkshochschule,\r\nKonservatorium.",
                    },
                    "12001": {
                        "name": "Hochschule",
                        "description": "Hochschule, Fachhochschule, Berufsakademie, o. Ä.",
                    },
                    "12002": {
                        "name": "BerufsbildendeSchule",
                        "description": "Berufsbildende Schule",
                    },
                    "12003": {
                        "name": "Forschungseinrichtung",
                        "description": "Forschungseinrichtung, Forschungsinstitut.",
                    },
                    "12004": {
                        "name": "SonstigesBildungForschung",
                        "description": "Sonstige Anlage oder Einrichtung aus Bildung und Forschung.",
                    },
                    "14000": {
                        "name": "Sakralgebaeude",
                        "description": "Religiösen Zwecken dienendes Gebäude wie z. B. Kirche, \r\n Kapelle, Moschee, Synagoge, Gebetssaal.",
                    },
                    "14001": {
                        "name": "KirchlicheVerwaltung",
                        "description": "Kirchliches Verwaltungsgebäude, z. B. Pfarramt, Bischöfliches Ordinariat, Konsistorium.",
                    },
                    "14002": {
                        "name": "Kirchengemeinde",
                        "description": "Religiöse Gemeinde- oder Versammlungseinrichtung, z. B. Gemeindehaus, Gemeindezentrum.",
                    },
                    "14003": {
                        "name": "SonstigesKirche",
                        "description": "Sonstige religiösen Zwecken dienende Anlage oder Einrichtung.",
                    },
                    "16000": {
                        "name": "EinrichtungKinder",
                        "description": "Soziale Einrichtung für Kinder, wie z. B. Kinderheim, Kindertagesstätte, Kindergarten.",
                    },
                    "16001": {
                        "name": "EinrichtungJugendliche",
                        "description": "Soziale Einrichtung für Jugendliche, wie z. B. Jugendfreizeitheim/-stätte, Jugendgästehaus, Jugendherberge, Jugendheim.",
                    },
                    "16002": {
                        "name": "EinrichtungFamilienErwachsene",
                        "description": "Soziale Einrichtung für Familien und Erwachsene, wie z. B. Bildungszentrum, Volkshochschule, Kleinkinderfürsorgestelle, Säuglingsfürsorgestelle, Nachbarschaftsheim.",
                    },
                    "16003": {
                        "name": "EinrichtungSenioren",
                        "description": "Soziale Einrichtung für Senioren, wie z. B. Alten-/Seniorentagesstätte, Alten-/Seniorenheim, Alten-/Seniorenwohnheim, Altersheim.",
                    },
                    "16004": {
                        "name": "SonstigeSozialeEinrichtung",
                        "description": "Sonstige soziale Einrichtung, z. B. Pflegeheim, Schwesternwohnheim, Studentendorf, Studentenwohnheim. Tierheim, Übergangsheim.",
                    },
                    "18000": {
                        "name": "Krankenhaus",
                        "description": "Krankenhaus oder vergleichbare Einrichtung (z. B. Klinik, Hospital, Krankenheim, Heil- und Pflegeanstalt),",
                    },
                    "18001": {
                        "name": "SonstigesGesundheit",
                        "description": "Sonstige Gesundheits-Einrichtung, z. B. Sanatorium, Kurklinik, Desinfektionsanstalt.",
                    },
                    "20000": {
                        "name": "MusikTheater",
                        "description": "Kulturelle Einrichtung aus dem Bereich Musik oder Theater (z. B. Theater, Konzerthaus, Musikhalle, Oper).",
                    },
                    "20001": {
                        "name": "Bildung",
                        "description": "Kulturelle Einrichtung mit Bildungsfunktion ( z. B. Museum, Bibliothek, Bücherei, Stadtbücherei, Volksbücherei).",
                    },
                    "20002": {
                        "name": "SonstigeKultur",
                        "description": "Sonstige kulturelle Einrichtung, wie z. B. Archiv, Landesbildstelle, Rundfunk und Fernsehen, Kongress- und Veranstaltungshalle, Mehrzweckhalle..",
                    },
                    "22000": {
                        "name": "Bad",
                        "description": "Schwimmbad, Freibad, Hallenbad, Schwimmhalle o. Ä..",
                    },
                    "22001": {
                        "name": "SportplatzSporthalle",
                        "description": "Sportplatz, Sporthalle, Tennishalle o. Ä.",
                    },
                    "22002": {
                        "name": "SonstigerSport",
                        "description": "Sonstige Sporteinrichtung.",
                    },
                    "24000": {
                        "name": "Feuerwehr",
                        "description": "Einrichtung oder Anlage der Feuerwehr.",
                    },
                    "24001": {"name": "Schutzbauwerk", "description": "Schutzbauwerk"},
                    "24002": {
                        "name": "Justiz",
                        "description": "Einrichtung der Justiz, wie z. B. Justizvollzug, Gericht, Haftanstalt.",
                    },
                    "24003": {
                        "name": "SonstigeSicherheitOrdnung",
                        "description": "Sonstige Anlage oder Einrichtung für Sicherheit und Ordnung, z. B. Polizei, Zoll, Feuerwehr, Zivilschutz, Bundeswehr, Landesverteidigung.",
                    },
                    "26000": {"name": "Post", "description": "Einrichtung der Post."},
                    "26001": {
                        "name": "SonstigeInfrastruktur",
                        "description": "Sonstige Anlage oder Einrichtung der Infrastruktur.",
                    },
                },
                "typename": "XP_BesondereZweckbestGemeinbedarf",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereBesondZweckbestimmung2: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "12000",
            "12001",
            "12002",
            "12003",
            "12004",
            "14000",
            "14001",
            "14002",
            "14003",
            "16000",
            "16001",
            "16002",
            "16003",
            "16004",
            "18000",
            "18001",
            "20000",
            "20001",
            "20002",
            "22000",
            "22001",
            "22002",
            "24000",
            "24001",
            "24002",
            "24003",
            "26000",
            "26001",
        ]
        | None,
        Field(
            description='Weitere besondere Zweckbestimmung der Fläche, die die zugehörige allgemeine Zweckbestimmung detailliert oder ersetzt. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {
                        "name": "KommunaleEinrichtung",
                        "description": "Kommunale Einrichtung wie z. B. Rathaus, Gesundheitsamt, Gesundheitsfürsorgestelle, Gartenbauamt, Gartenarbeitsstützpunkt, Fuhrpark.",
                    },
                    "10001": {
                        "name": "BetriebOeffentlZweckbestimmung",
                        "description": "Betrieb mit öffentlicher Zweckbestimmung wie z.B. ein Stadtreinigungsbetrieb, Autobusbetriebshof, Omnibusbahnhof.",
                    },
                    "10002": {
                        "name": "AnlageBundLand",
                        "description": "Eine Anlage des Bundes oder eines Bundeslandes wie z. B.  Arbeitsamt, Autobahnmeisterei, Brückenmeisterei, Patentamt, Wasserbauhof, Finanzamt.",
                    },
                    "10003": {
                        "name": "SonstigeOeffentlicheVerwaltung",
                        "description": "Sonstige Einrichtung oder Anlage der öffentlichen Verwaltung wie z. B. die Industrie und Handelskammer oder Handwerkskammer.",
                    },
                    "12000": {
                        "name": "Schule",
                        "description": "Schulische Einrichtung. Darunter fallen u. a. Allgemeinbildende Schule, Oberstufenzentrum, Sonderschule, Fachschule, Volkshochschule,\r\nKonservatorium.",
                    },
                    "12001": {
                        "name": "Hochschule",
                        "description": "Hochschule, Fachhochschule, Berufsakademie, o. Ä.",
                    },
                    "12002": {
                        "name": "BerufsbildendeSchule",
                        "description": "Berufsbildende Schule",
                    },
                    "12003": {
                        "name": "Forschungseinrichtung",
                        "description": "Forschungseinrichtung, Forschungsinstitut.",
                    },
                    "12004": {
                        "name": "SonstigesBildungForschung",
                        "description": "Sonstige Anlage oder Einrichtung aus Bildung und Forschung.",
                    },
                    "14000": {
                        "name": "Sakralgebaeude",
                        "description": "Religiösen Zwecken dienendes Gebäude wie z. B. Kirche, \r\n Kapelle, Moschee, Synagoge, Gebetssaal.",
                    },
                    "14001": {
                        "name": "KirchlicheVerwaltung",
                        "description": "Kirchliches Verwaltungsgebäude, z. B. Pfarramt, Bischöfliches Ordinariat, Konsistorium.",
                    },
                    "14002": {
                        "name": "Kirchengemeinde",
                        "description": "Religiöse Gemeinde- oder Versammlungseinrichtung, z. B. Gemeindehaus, Gemeindezentrum.",
                    },
                    "14003": {
                        "name": "SonstigesKirche",
                        "description": "Sonstige religiösen Zwecken dienende Anlage oder Einrichtung.",
                    },
                    "16000": {
                        "name": "EinrichtungKinder",
                        "description": "Soziale Einrichtung für Kinder, wie z. B. Kinderheim, Kindertagesstätte, Kindergarten.",
                    },
                    "16001": {
                        "name": "EinrichtungJugendliche",
                        "description": "Soziale Einrichtung für Jugendliche, wie z. B. Jugendfreizeitheim/-stätte, Jugendgästehaus, Jugendherberge, Jugendheim.",
                    },
                    "16002": {
                        "name": "EinrichtungFamilienErwachsene",
                        "description": "Soziale Einrichtung für Familien und Erwachsene, wie z. B. Bildungszentrum, Volkshochschule, Kleinkinderfürsorgestelle, Säuglingsfürsorgestelle, Nachbarschaftsheim.",
                    },
                    "16003": {
                        "name": "EinrichtungSenioren",
                        "description": "Soziale Einrichtung für Senioren, wie z. B. Alten-/Seniorentagesstätte, Alten-/Seniorenheim, Alten-/Seniorenwohnheim, Altersheim.",
                    },
                    "16004": {
                        "name": "SonstigeSozialeEinrichtung",
                        "description": "Sonstige soziale Einrichtung, z. B. Pflegeheim, Schwesternwohnheim, Studentendorf, Studentenwohnheim. Tierheim, Übergangsheim.",
                    },
                    "18000": {
                        "name": "Krankenhaus",
                        "description": "Krankenhaus oder vergleichbare Einrichtung (z. B. Klinik, Hospital, Krankenheim, Heil- und Pflegeanstalt),",
                    },
                    "18001": {
                        "name": "SonstigesGesundheit",
                        "description": "Sonstige Gesundheits-Einrichtung, z. B. Sanatorium, Kurklinik, Desinfektionsanstalt.",
                    },
                    "20000": {
                        "name": "MusikTheater",
                        "description": "Kulturelle Einrichtung aus dem Bereich Musik oder Theater (z. B. Theater, Konzerthaus, Musikhalle, Oper).",
                    },
                    "20001": {
                        "name": "Bildung",
                        "description": "Kulturelle Einrichtung mit Bildungsfunktion ( z. B. Museum, Bibliothek, Bücherei, Stadtbücherei, Volksbücherei).",
                    },
                    "20002": {
                        "name": "SonstigeKultur",
                        "description": "Sonstige kulturelle Einrichtung, wie z. B. Archiv, Landesbildstelle, Rundfunk und Fernsehen, Kongress- und Veranstaltungshalle, Mehrzweckhalle..",
                    },
                    "22000": {
                        "name": "Bad",
                        "description": "Schwimmbad, Freibad, Hallenbad, Schwimmhalle o. Ä..",
                    },
                    "22001": {
                        "name": "SportplatzSporthalle",
                        "description": "Sportplatz, Sporthalle, Tennishalle o. Ä.",
                    },
                    "22002": {
                        "name": "SonstigerSport",
                        "description": "Sonstige Sporteinrichtung.",
                    },
                    "24000": {
                        "name": "Feuerwehr",
                        "description": "Einrichtung oder Anlage der Feuerwehr.",
                    },
                    "24001": {"name": "Schutzbauwerk", "description": "Schutzbauwerk"},
                    "24002": {
                        "name": "Justiz",
                        "description": "Einrichtung der Justiz, wie z. B. Justizvollzug, Gericht, Haftanstalt.",
                    },
                    "24003": {
                        "name": "SonstigeSicherheitOrdnung",
                        "description": "Sonstige Anlage oder Einrichtung für Sicherheit und Ordnung, z. B. Polizei, Zoll, Feuerwehr, Zivilschutz, Bundeswehr, Landesverteidigung.",
                    },
                    "26000": {"name": "Post", "description": "Einrichtung der Post."},
                    "26001": {
                        "name": "SonstigeInfrastruktur",
                        "description": "Sonstige Anlage oder Einrichtung der Infrastruktur.",
                    },
                },
                "typename": "XP_BesondereZweckbestGemeinbedarf",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereBesondZweckbestimmung3: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "12000",
            "12001",
            "12002",
            "12003",
            "12004",
            "14000",
            "14001",
            "14002",
            "14003",
            "16000",
            "16001",
            "16002",
            "16003",
            "16004",
            "18000",
            "18001",
            "20000",
            "20001",
            "20002",
            "22000",
            "22001",
            "22002",
            "24000",
            "24001",
            "24002",
            "24003",
            "26000",
            "26001",
        ]
        | None,
        Field(
            description='Weitere besondere Zweckbestimmung der Fläche, die die zugehörige allgemeine Zweckbestimmung detailliert oder ersetzt. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {
                        "name": "KommunaleEinrichtung",
                        "description": "Kommunale Einrichtung wie z. B. Rathaus, Gesundheitsamt, Gesundheitsfürsorgestelle, Gartenbauamt, Gartenarbeitsstützpunkt, Fuhrpark.",
                    },
                    "10001": {
                        "name": "BetriebOeffentlZweckbestimmung",
                        "description": "Betrieb mit öffentlicher Zweckbestimmung wie z.B. ein Stadtreinigungsbetrieb, Autobusbetriebshof, Omnibusbahnhof.",
                    },
                    "10002": {
                        "name": "AnlageBundLand",
                        "description": "Eine Anlage des Bundes oder eines Bundeslandes wie z. B.  Arbeitsamt, Autobahnmeisterei, Brückenmeisterei, Patentamt, Wasserbauhof, Finanzamt.",
                    },
                    "10003": {
                        "name": "SonstigeOeffentlicheVerwaltung",
                        "description": "Sonstige Einrichtung oder Anlage der öffentlichen Verwaltung wie z. B. die Industrie und Handelskammer oder Handwerkskammer.",
                    },
                    "12000": {
                        "name": "Schule",
                        "description": "Schulische Einrichtung. Darunter fallen u. a. Allgemeinbildende Schule, Oberstufenzentrum, Sonderschule, Fachschule, Volkshochschule,\r\nKonservatorium.",
                    },
                    "12001": {
                        "name": "Hochschule",
                        "description": "Hochschule, Fachhochschule, Berufsakademie, o. Ä.",
                    },
                    "12002": {
                        "name": "BerufsbildendeSchule",
                        "description": "Berufsbildende Schule",
                    },
                    "12003": {
                        "name": "Forschungseinrichtung",
                        "description": "Forschungseinrichtung, Forschungsinstitut.",
                    },
                    "12004": {
                        "name": "SonstigesBildungForschung",
                        "description": "Sonstige Anlage oder Einrichtung aus Bildung und Forschung.",
                    },
                    "14000": {
                        "name": "Sakralgebaeude",
                        "description": "Religiösen Zwecken dienendes Gebäude wie z. B. Kirche, \r\n Kapelle, Moschee, Synagoge, Gebetssaal.",
                    },
                    "14001": {
                        "name": "KirchlicheVerwaltung",
                        "description": "Kirchliches Verwaltungsgebäude, z. B. Pfarramt, Bischöfliches Ordinariat, Konsistorium.",
                    },
                    "14002": {
                        "name": "Kirchengemeinde",
                        "description": "Religiöse Gemeinde- oder Versammlungseinrichtung, z. B. Gemeindehaus, Gemeindezentrum.",
                    },
                    "14003": {
                        "name": "SonstigesKirche",
                        "description": "Sonstige religiösen Zwecken dienende Anlage oder Einrichtung.",
                    },
                    "16000": {
                        "name": "EinrichtungKinder",
                        "description": "Soziale Einrichtung für Kinder, wie z. B. Kinderheim, Kindertagesstätte, Kindergarten.",
                    },
                    "16001": {
                        "name": "EinrichtungJugendliche",
                        "description": "Soziale Einrichtung für Jugendliche, wie z. B. Jugendfreizeitheim/-stätte, Jugendgästehaus, Jugendherberge, Jugendheim.",
                    },
                    "16002": {
                        "name": "EinrichtungFamilienErwachsene",
                        "description": "Soziale Einrichtung für Familien und Erwachsene, wie z. B. Bildungszentrum, Volkshochschule, Kleinkinderfürsorgestelle, Säuglingsfürsorgestelle, Nachbarschaftsheim.",
                    },
                    "16003": {
                        "name": "EinrichtungSenioren",
                        "description": "Soziale Einrichtung für Senioren, wie z. B. Alten-/Seniorentagesstätte, Alten-/Seniorenheim, Alten-/Seniorenwohnheim, Altersheim.",
                    },
                    "16004": {
                        "name": "SonstigeSozialeEinrichtung",
                        "description": "Sonstige soziale Einrichtung, z. B. Pflegeheim, Schwesternwohnheim, Studentendorf, Studentenwohnheim. Tierheim, Übergangsheim.",
                    },
                    "18000": {
                        "name": "Krankenhaus",
                        "description": "Krankenhaus oder vergleichbare Einrichtung (z. B. Klinik, Hospital, Krankenheim, Heil- und Pflegeanstalt),",
                    },
                    "18001": {
                        "name": "SonstigesGesundheit",
                        "description": "Sonstige Gesundheits-Einrichtung, z. B. Sanatorium, Kurklinik, Desinfektionsanstalt.",
                    },
                    "20000": {
                        "name": "MusikTheater",
                        "description": "Kulturelle Einrichtung aus dem Bereich Musik oder Theater (z. B. Theater, Konzerthaus, Musikhalle, Oper).",
                    },
                    "20001": {
                        "name": "Bildung",
                        "description": "Kulturelle Einrichtung mit Bildungsfunktion ( z. B. Museum, Bibliothek, Bücherei, Stadtbücherei, Volksbücherei).",
                    },
                    "20002": {
                        "name": "SonstigeKultur",
                        "description": "Sonstige kulturelle Einrichtung, wie z. B. Archiv, Landesbildstelle, Rundfunk und Fernsehen, Kongress- und Veranstaltungshalle, Mehrzweckhalle..",
                    },
                    "22000": {
                        "name": "Bad",
                        "description": "Schwimmbad, Freibad, Hallenbad, Schwimmhalle o. Ä..",
                    },
                    "22001": {
                        "name": "SportplatzSporthalle",
                        "description": "Sportplatz, Sporthalle, Tennishalle o. Ä.",
                    },
                    "22002": {
                        "name": "SonstigerSport",
                        "description": "Sonstige Sporteinrichtung.",
                    },
                    "24000": {
                        "name": "Feuerwehr",
                        "description": "Einrichtung oder Anlage der Feuerwehr.",
                    },
                    "24001": {"name": "Schutzbauwerk", "description": "Schutzbauwerk"},
                    "24002": {
                        "name": "Justiz",
                        "description": "Einrichtung der Justiz, wie z. B. Justizvollzug, Gericht, Haftanstalt.",
                    },
                    "24003": {
                        "name": "SonstigeSicherheitOrdnung",
                        "description": "Sonstige Anlage oder Einrichtung für Sicherheit und Ordnung, z. B. Polizei, Zoll, Feuerwehr, Zivilschutz, Bundeswehr, Landesverteidigung.",
                    },
                    "26000": {"name": "Post", "description": "Einrichtung der Post."},
                    "26001": {
                        "name": "SonstigeInfrastruktur",
                        "description": "Sonstige Anlage oder Einrichtung der Infrastruktur.",
                    },
                },
                "typename": "XP_BesondereZweckbestGemeinbedarf",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereBesondZweckbestimmung4: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "12000",
            "12001",
            "12002",
            "12003",
            "12004",
            "14000",
            "14001",
            "14002",
            "14003",
            "16000",
            "16001",
            "16002",
            "16003",
            "16004",
            "18000",
            "18001",
            "20000",
            "20001",
            "20002",
            "22000",
            "22001",
            "22002",
            "24000",
            "24001",
            "24002",
            "24003",
            "26000",
            "26001",
        ]
        | None,
        Field(
            description='Weitere besondere Zweckbestimmung der Fläche, die die zugehörige allgemeine Zweckbestimmung detailliert oder ersetzt. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {
                        "name": "KommunaleEinrichtung",
                        "description": "Kommunale Einrichtung wie z. B. Rathaus, Gesundheitsamt, Gesundheitsfürsorgestelle, Gartenbauamt, Gartenarbeitsstützpunkt, Fuhrpark.",
                    },
                    "10001": {
                        "name": "BetriebOeffentlZweckbestimmung",
                        "description": "Betrieb mit öffentlicher Zweckbestimmung wie z.B. ein Stadtreinigungsbetrieb, Autobusbetriebshof, Omnibusbahnhof.",
                    },
                    "10002": {
                        "name": "AnlageBundLand",
                        "description": "Eine Anlage des Bundes oder eines Bundeslandes wie z. B.  Arbeitsamt, Autobahnmeisterei, Brückenmeisterei, Patentamt, Wasserbauhof, Finanzamt.",
                    },
                    "10003": {
                        "name": "SonstigeOeffentlicheVerwaltung",
                        "description": "Sonstige Einrichtung oder Anlage der öffentlichen Verwaltung wie z. B. die Industrie und Handelskammer oder Handwerkskammer.",
                    },
                    "12000": {
                        "name": "Schule",
                        "description": "Schulische Einrichtung. Darunter fallen u. a. Allgemeinbildende Schule, Oberstufenzentrum, Sonderschule, Fachschule, Volkshochschule,\r\nKonservatorium.",
                    },
                    "12001": {
                        "name": "Hochschule",
                        "description": "Hochschule, Fachhochschule, Berufsakademie, o. Ä.",
                    },
                    "12002": {
                        "name": "BerufsbildendeSchule",
                        "description": "Berufsbildende Schule",
                    },
                    "12003": {
                        "name": "Forschungseinrichtung",
                        "description": "Forschungseinrichtung, Forschungsinstitut.",
                    },
                    "12004": {
                        "name": "SonstigesBildungForschung",
                        "description": "Sonstige Anlage oder Einrichtung aus Bildung und Forschung.",
                    },
                    "14000": {
                        "name": "Sakralgebaeude",
                        "description": "Religiösen Zwecken dienendes Gebäude wie z. B. Kirche, \r\n Kapelle, Moschee, Synagoge, Gebetssaal.",
                    },
                    "14001": {
                        "name": "KirchlicheVerwaltung",
                        "description": "Kirchliches Verwaltungsgebäude, z. B. Pfarramt, Bischöfliches Ordinariat, Konsistorium.",
                    },
                    "14002": {
                        "name": "Kirchengemeinde",
                        "description": "Religiöse Gemeinde- oder Versammlungseinrichtung, z. B. Gemeindehaus, Gemeindezentrum.",
                    },
                    "14003": {
                        "name": "SonstigesKirche",
                        "description": "Sonstige religiösen Zwecken dienende Anlage oder Einrichtung.",
                    },
                    "16000": {
                        "name": "EinrichtungKinder",
                        "description": "Soziale Einrichtung für Kinder, wie z. B. Kinderheim, Kindertagesstätte, Kindergarten.",
                    },
                    "16001": {
                        "name": "EinrichtungJugendliche",
                        "description": "Soziale Einrichtung für Jugendliche, wie z. B. Jugendfreizeitheim/-stätte, Jugendgästehaus, Jugendherberge, Jugendheim.",
                    },
                    "16002": {
                        "name": "EinrichtungFamilienErwachsene",
                        "description": "Soziale Einrichtung für Familien und Erwachsene, wie z. B. Bildungszentrum, Volkshochschule, Kleinkinderfürsorgestelle, Säuglingsfürsorgestelle, Nachbarschaftsheim.",
                    },
                    "16003": {
                        "name": "EinrichtungSenioren",
                        "description": "Soziale Einrichtung für Senioren, wie z. B. Alten-/Seniorentagesstätte, Alten-/Seniorenheim, Alten-/Seniorenwohnheim, Altersheim.",
                    },
                    "16004": {
                        "name": "SonstigeSozialeEinrichtung",
                        "description": "Sonstige soziale Einrichtung, z. B. Pflegeheim, Schwesternwohnheim, Studentendorf, Studentenwohnheim. Tierheim, Übergangsheim.",
                    },
                    "18000": {
                        "name": "Krankenhaus",
                        "description": "Krankenhaus oder vergleichbare Einrichtung (z. B. Klinik, Hospital, Krankenheim, Heil- und Pflegeanstalt),",
                    },
                    "18001": {
                        "name": "SonstigesGesundheit",
                        "description": "Sonstige Gesundheits-Einrichtung, z. B. Sanatorium, Kurklinik, Desinfektionsanstalt.",
                    },
                    "20000": {
                        "name": "MusikTheater",
                        "description": "Kulturelle Einrichtung aus dem Bereich Musik oder Theater (z. B. Theater, Konzerthaus, Musikhalle, Oper).",
                    },
                    "20001": {
                        "name": "Bildung",
                        "description": "Kulturelle Einrichtung mit Bildungsfunktion ( z. B. Museum, Bibliothek, Bücherei, Stadtbücherei, Volksbücherei).",
                    },
                    "20002": {
                        "name": "SonstigeKultur",
                        "description": "Sonstige kulturelle Einrichtung, wie z. B. Archiv, Landesbildstelle, Rundfunk und Fernsehen, Kongress- und Veranstaltungshalle, Mehrzweckhalle..",
                    },
                    "22000": {
                        "name": "Bad",
                        "description": "Schwimmbad, Freibad, Hallenbad, Schwimmhalle o. Ä..",
                    },
                    "22001": {
                        "name": "SportplatzSporthalle",
                        "description": "Sportplatz, Sporthalle, Tennishalle o. Ä.",
                    },
                    "22002": {
                        "name": "SonstigerSport",
                        "description": "Sonstige Sporteinrichtung.",
                    },
                    "24000": {
                        "name": "Feuerwehr",
                        "description": "Einrichtung oder Anlage der Feuerwehr.",
                    },
                    "24001": {"name": "Schutzbauwerk", "description": "Schutzbauwerk"},
                    "24002": {
                        "name": "Justiz",
                        "description": "Einrichtung der Justiz, wie z. B. Justizvollzug, Gericht, Haftanstalt.",
                    },
                    "24003": {
                        "name": "SonstigeSicherheitOrdnung",
                        "description": "Sonstige Anlage oder Einrichtung für Sicherheit und Ordnung, z. B. Polizei, Zoll, Feuerwehr, Zivilschutz, Bundeswehr, Landesverteidigung.",
                    },
                    "26000": {"name": "Post", "description": "Einrichtung der Post."},
                    "26001": {
                        "name": "SonstigeInfrastruktur",
                        "description": "Sonstige Anlage oder Einrichtung der Infrastruktur.",
                    },
                },
                "typename": "XP_BesondereZweckbestGemeinbedarf",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereBesondZweckbestimmung5: Annotated[
        Literal[
            "10000",
            "10001",
            "10002",
            "10003",
            "12000",
            "12001",
            "12002",
            "12003",
            "12004",
            "14000",
            "14001",
            "14002",
            "14003",
            "16000",
            "16001",
            "16002",
            "16003",
            "16004",
            "18000",
            "18001",
            "20000",
            "20001",
            "20002",
            "22000",
            "22001",
            "22002",
            "24000",
            "24001",
            "24002",
            "24003",
            "26000",
            "26001",
        ]
        | None,
        Field(
            description='Weitere besondere Zweckbestimmung der Fläche, die die zugehörige allgemeine Zweckbestimmung detailliert oder ersetzt. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen besondereZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "10000": {
                        "name": "KommunaleEinrichtung",
                        "description": "Kommunale Einrichtung wie z. B. Rathaus, Gesundheitsamt, Gesundheitsfürsorgestelle, Gartenbauamt, Gartenarbeitsstützpunkt, Fuhrpark.",
                    },
                    "10001": {
                        "name": "BetriebOeffentlZweckbestimmung",
                        "description": "Betrieb mit öffentlicher Zweckbestimmung wie z.B. ein Stadtreinigungsbetrieb, Autobusbetriebshof, Omnibusbahnhof.",
                    },
                    "10002": {
                        "name": "AnlageBundLand",
                        "description": "Eine Anlage des Bundes oder eines Bundeslandes wie z. B.  Arbeitsamt, Autobahnmeisterei, Brückenmeisterei, Patentamt, Wasserbauhof, Finanzamt.",
                    },
                    "10003": {
                        "name": "SonstigeOeffentlicheVerwaltung",
                        "description": "Sonstige Einrichtung oder Anlage der öffentlichen Verwaltung wie z. B. die Industrie und Handelskammer oder Handwerkskammer.",
                    },
                    "12000": {
                        "name": "Schule",
                        "description": "Schulische Einrichtung. Darunter fallen u. a. Allgemeinbildende Schule, Oberstufenzentrum, Sonderschule, Fachschule, Volkshochschule,\r\nKonservatorium.",
                    },
                    "12001": {
                        "name": "Hochschule",
                        "description": "Hochschule, Fachhochschule, Berufsakademie, o. Ä.",
                    },
                    "12002": {
                        "name": "BerufsbildendeSchule",
                        "description": "Berufsbildende Schule",
                    },
                    "12003": {
                        "name": "Forschungseinrichtung",
                        "description": "Forschungseinrichtung, Forschungsinstitut.",
                    },
                    "12004": {
                        "name": "SonstigesBildungForschung",
                        "description": "Sonstige Anlage oder Einrichtung aus Bildung und Forschung.",
                    },
                    "14000": {
                        "name": "Sakralgebaeude",
                        "description": "Religiösen Zwecken dienendes Gebäude wie z. B. Kirche, \r\n Kapelle, Moschee, Synagoge, Gebetssaal.",
                    },
                    "14001": {
                        "name": "KirchlicheVerwaltung",
                        "description": "Kirchliches Verwaltungsgebäude, z. B. Pfarramt, Bischöfliches Ordinariat, Konsistorium.",
                    },
                    "14002": {
                        "name": "Kirchengemeinde",
                        "description": "Religiöse Gemeinde- oder Versammlungseinrichtung, z. B. Gemeindehaus, Gemeindezentrum.",
                    },
                    "14003": {
                        "name": "SonstigesKirche",
                        "description": "Sonstige religiösen Zwecken dienende Anlage oder Einrichtung.",
                    },
                    "16000": {
                        "name": "EinrichtungKinder",
                        "description": "Soziale Einrichtung für Kinder, wie z. B. Kinderheim, Kindertagesstätte, Kindergarten.",
                    },
                    "16001": {
                        "name": "EinrichtungJugendliche",
                        "description": "Soziale Einrichtung für Jugendliche, wie z. B. Jugendfreizeitheim/-stätte, Jugendgästehaus, Jugendherberge, Jugendheim.",
                    },
                    "16002": {
                        "name": "EinrichtungFamilienErwachsene",
                        "description": "Soziale Einrichtung für Familien und Erwachsene, wie z. B. Bildungszentrum, Volkshochschule, Kleinkinderfürsorgestelle, Säuglingsfürsorgestelle, Nachbarschaftsheim.",
                    },
                    "16003": {
                        "name": "EinrichtungSenioren",
                        "description": "Soziale Einrichtung für Senioren, wie z. B. Alten-/Seniorentagesstätte, Alten-/Seniorenheim, Alten-/Seniorenwohnheim, Altersheim.",
                    },
                    "16004": {
                        "name": "SonstigeSozialeEinrichtung",
                        "description": "Sonstige soziale Einrichtung, z. B. Pflegeheim, Schwesternwohnheim, Studentendorf, Studentenwohnheim. Tierheim, Übergangsheim.",
                    },
                    "18000": {
                        "name": "Krankenhaus",
                        "description": "Krankenhaus oder vergleichbare Einrichtung (z. B. Klinik, Hospital, Krankenheim, Heil- und Pflegeanstalt),",
                    },
                    "18001": {
                        "name": "SonstigesGesundheit",
                        "description": "Sonstige Gesundheits-Einrichtung, z. B. Sanatorium, Kurklinik, Desinfektionsanstalt.",
                    },
                    "20000": {
                        "name": "MusikTheater",
                        "description": "Kulturelle Einrichtung aus dem Bereich Musik oder Theater (z. B. Theater, Konzerthaus, Musikhalle, Oper).",
                    },
                    "20001": {
                        "name": "Bildung",
                        "description": "Kulturelle Einrichtung mit Bildungsfunktion ( z. B. Museum, Bibliothek, Bücherei, Stadtbücherei, Volksbücherei).",
                    },
                    "20002": {
                        "name": "SonstigeKultur",
                        "description": "Sonstige kulturelle Einrichtung, wie z. B. Archiv, Landesbildstelle, Rundfunk und Fernsehen, Kongress- und Veranstaltungshalle, Mehrzweckhalle..",
                    },
                    "22000": {
                        "name": "Bad",
                        "description": "Schwimmbad, Freibad, Hallenbad, Schwimmhalle o. Ä..",
                    },
                    "22001": {
                        "name": "SportplatzSporthalle",
                        "description": "Sportplatz, Sporthalle, Tennishalle o. Ä.",
                    },
                    "22002": {
                        "name": "SonstigerSport",
                        "description": "Sonstige Sporteinrichtung.",
                    },
                    "24000": {
                        "name": "Feuerwehr",
                        "description": "Einrichtung oder Anlage der Feuerwehr.",
                    },
                    "24001": {"name": "Schutzbauwerk", "description": "Schutzbauwerk"},
                    "24002": {
                        "name": "Justiz",
                        "description": "Einrichtung der Justiz, wie z. B. Justizvollzug, Gericht, Haftanstalt.",
                    },
                    "24003": {
                        "name": "SonstigeSicherheitOrdnung",
                        "description": "Sonstige Anlage oder Einrichtung für Sicherheit und Ordnung, z. B. Polizei, Zoll, Feuerwehr, Zivilschutz, Bundeswehr, Landesverteidigung.",
                    },
                    "26000": {"name": "Post", "description": "Einrichtung der Post."},
                    "26001": {
                        "name": "SonstigeInfrastruktur",
                        "description": "Sonstige Anlage oder Einrichtung der Infrastruktur.",
                    },
                },
                "typename": "XP_BesondereZweckbestGemeinbedarf",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteZweckbestimmung: Annotated[
        list[AnyUrl] | None,
        Field(
            description="Über eine ExternalCodeList definierte zusätzliche Zweckbestimmungen.",
            json_schema_extra={
                "typename": "FP_DetailZweckbestGemeinbedarf",
                "stereotype": "Codelist",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung1: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "FP_DetailZweckbestGemeinbedarf",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung2: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "FP_DetailZweckbestGemeinbedarf",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung3: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "FP_DetailZweckbestGemeinbedarf",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung4: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "FP_DetailZweckbestGemeinbedarf",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailZweckbestimmung5: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Zweckbestimmung. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteZweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "FP_DetailZweckbestGemeinbedarf",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class FPGenerischesObjekt(FPGeometrieobjekt):
    """Klasse zur Modellierung aller Inhalte des FPlans, die keine nachrichtliche Übernahmen aus anderen Rechts-bereichen sind, aber durch keine andere Klasse des FPlan-Fachschemas dargestellt werden können."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    zweckbestimmung: Annotated[
        list[AnyUrl] | None,
        Field(
            description="Über eine ExternalCodeList. definierte Zweckbestimmungen des Objekts.",
            json_schema_extra={
                "typename": "FP_ZweckbestimmungGenerischeObjekte",
                "stereotype": "Codelist",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    weitereZweckbestimmung1: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine ExternalCodeList definierte weitere Zweckbestimmung des Objekts. Besondere Zweckbestimmung des Vorhabens, die die spezifizierte allgemeine Zweckbestimmung detaillieren. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "FP_ZweckbestimmungGenerischeObjekte",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung2: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine ExternalCodeList definierte weitere Zweckbestimmung des Objekts. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "FP_ZweckbestimmungGenerischeObjekte",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereZweckbestimmung3: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine ExternalCodeList definierte weitere Zweckbestimmung des Objekts. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen zweckbestimmung mehrfach belegt werden.',
            json_schema_extra={
                "typename": "FP_ZweckbestimmungGenerischeObjekte",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class FPNutzungsbeschraenkungsFlaeche(FPUeberlagerungsobjekt):
    """Umgrenzungen der Flächen für besondere Anlagen und Vorkehrungen zum Schutz vor schädlichen Umwelteinwirkungen im Sinne des Bundes-
    Immissionsschutzgesetzes (§ 5, Abs. 2, Nr. 6 BauGB)
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class FPTextlicheDarstellungsFlaeche(FPUeberlagerungsobjekt):
    """Bereich in dem bestimmte Textliche Darstellungen gültig sind, die über die Relation "refTextInhalt" (Basisklasse XP_Objekt) spezifiziert werden."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class LPAbgrenzung(LPLinienobjekt):
    """Abgrenzungen unterschiedlicher Ziel- und Zweckbestimmungen und Nutzungsarten, Abgrenzungen unterschiedlicher Biotoptypen."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class LPAllgGruenflaeche(LPFlaechenobjekt):
    """Allgemeine Grünflächen."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class LPAnpflanzungBindungErhaltung(LPGeometrieobjekt):
    """Festsetzungen zum Erhalten und Anpflanzen von Bäumen, Sträuchern und sonstigen Bepflanzungen in einem Planwerk mit landschaftplanerischen Festsetzungen. Die Festsetzungen können durch eine Spezifizierung eines Kronendurchmessers (z.B. für Baumpflanzungen), die Pflanztiefe und Mindesthöhe von Anpflanzungen (z.B. bei der Anpflanzung von Hecken) oder durch botanische Spezifizierung differenziert werden."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    massnahme: Annotated[
        Literal["1000", "2000", "3000"] | None,
        Field(
            description="Art der Maßnahme",
            json_schema_extra={
                "enumDescription": {
                    "1000": {
                        "name": "BindungErhaltung",
                        "description": "Bindung und Erhaltung von Bäumen, Sträuchern und sonstigen Bepflanzungen, sowie von Gewässern.",
                    },
                    "2000": {
                        "name": "Anpflanzung",
                        "description": "Anpflanzung von Bäumen, Sträuchern oder sonstigen Bepflanzungen.",
                    },
                    "3000": {"name": "AnpflanzungBindungErhaltung"},
                },
                "typename": "XP_ABEMassnahmenTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    gegenstand: Annotated[
        list[
            Literal[
                "1000",
                "1100",
                "1200",
                "2000",
                "2100",
                "2200",
                "3000",
                "4000",
                "5000",
                "6000",
            ]
        ]
        | None,
        Field(
            description="Gegenständ eder Maßnahme",
            json_schema_extra={
                "typename": "XP_AnpflanzungBindungErhaltungsGegenstand",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Baeume", "description": "Bäume"},
                    "1100": {"name": "Kopfbaeume"},
                    "1200": {"name": "Baumreihe"},
                    "2000": {"name": "Straeucher", "description": "Sträucher"},
                    "2100": {"name": "Hecke"},
                    "2200": {"name": "Knick"},
                    "3000": {
                        "name": "SonstBepflanzung",
                        "description": "Sonstige Bepflanzung",
                    },
                    "4000": {
                        "name": "Gewaesser",
                        "description": "Gewässer (nur Erhaltung)",
                    },
                    "5000": {"name": "Fassadenbegruenung"},
                    "6000": {"name": "Dachbegruenung"},
                },
            },
        ),
    ] = None
    kronendurchmesser: Annotated[
        definitions.Length | None,
        Field(
            description="Durchmesser der Baumkrone bei zu erhaltenden Bäumen.",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    pflanztiefe: Annotated[
        definitions.Length | None,
        Field(
            description="Pflanztiefe",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None
    istAusgleich: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob die Fläche oder Maßnahme zum Ausgleich von Eingriffen genutzt wird.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False
    pflanzart: Annotated[
        list[AnyUrl] | None,
        Field(
            description="Botanische Angabe der zu erhaltenden bzw. der zu pflanzenden Pflanzen.",
            json_schema_extra={
                "typename": "LP_Pflanzart",
                "stereotype": "Codelist",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    mindesthoehe: Annotated[
        definitions.Length | None,
        Field(
            description="Mindesthöhe einer Pflanze (z.B. Mindesthöhe einer zu pflanzenden Hecke)",
            json_schema_extra={
                "typename": "Length",
                "stereotype": "Measure",
                "multiplicity": "0..1",
                "uom": "m",
            },
        ),
    ] = None


class LPAusgleich(LPGeometrieobjekt):
    """Flächen und Maßnahmen zum Ausgleich von Eingriffen im Sinne des §8 und 8A BNatSchG (in Verbindung mit §1a BauGB, Ausgleichs- und Ersatzmaßnahmen)."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    ziel: Annotated[
        Literal["1000", "2000", "3000", "4000", "9999"] | None,
        Field(
            description='Unterscheidung nach den Zielen "Schutz, Pflege" und "Entwicklung".',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "SchutzPflege"},
                    "2000": {"name": "Entwicklung"},
                    "3000": {"name": "Anlage"},
                    "4000": {"name": "SchutzPflegeEntwicklung"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "XP_SPEZiele",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    massnahme: Annotated[
        str | None,
        Field(
            description="Durchzuführende Maßnahme (Textform)",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    massnahmeKuerzel: Annotated[
        str | None,
        Field(
            description="Kürzel der durchzuführenden Maßnahme.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class LPBiotopverbundflaeche(LPGeometrieobjekt):
    """Biotop-Verbundfläche"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"


class LPBodenschutzrecht(LPGeometrieobjekt):
    """Gebiete und Gebietsteile mit rechtlichen Bindungen nach anderen Fachgesetzen (soweit sie für den Schutz, die Pflege und die Entwicklung von Natur und Landschaft bedeutsam sind). Hier: Flächen mit schädlichen Bodenveränderungen nach dem Bodenschutzgesetz."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    typ: Annotated[
        Literal["1000", "9999"] | None,
        Field(
            description="Typ des Schutzobjektes",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Altlastenflaeche"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "LP_BodenschutzrechtTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detailTyp: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definierter zusätzlicher Typ des Schutzobjektes.",
            json_schema_extra={
                "typename": "LP_BodenschutzrechtDetailTypen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class LPDenkmalschutzrecht(LPGeometrieobjekt):
    """Gebiete und Gebietsteile mit rechtlichen Bindungen nach anderen Fachgesetzen (soweit sie für den Schutz, die Pflege und die Entwicklung von Natur und Landschaft bedeutsam sind). Hier: Flächen die dem Denkmalschutz unterliegen."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    detailTyp: Annotated[
        AnyUrl | None,
        Field(
            description="Typ des Schutzobjektes.",
            json_schema_extra={
                "typename": "LP_DenkmalschutzrechtDetailTypen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class LPErholungFreizeit(LPGeometrieobjekt):
    """Sonstige Gebiete, Objekte, Zweckbestimmungen oder Maßnahmen mit besonderen Funktionen für die landschaftsgebundene Erholung und Freizeit."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    funktion: Annotated[
        list[
            Literal[
                "1000",
                "1030",
                "1050",
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
                "2200",
                "2300",
                "2400",
                "2500",
                "2600",
                "2700",
                "2800",
                "2900",
                "3000",
                "3100",
                "3200",
                "3300",
                "3400",
                "3500",
                "3600",
                "3700",
                "3800",
                "3900",
                "4000",
                "4100",
                "5000",
                "9999",
            ]
        ]
        | None,
        Field(
            description="Funktion der Fläche.",
            json_schema_extra={
                "typename": "LP_ErholungFreizeitFunktionen",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Parkanlage"},
                    "1030": {"name": "Dauerkleingaerten"},
                    "1050": {"name": "Sportplatz"},
                    "1100": {"name": "Spielplatz"},
                    "1200": {"name": "Zeltplatz"},
                    "1300": {"name": "BadeplatzFreibad"},
                    "1400": {"name": "Schutzhuette"},
                    "1500": {"name": "Rastplatz"},
                    "1600": {"name": "Informationstafel"},
                    "1700": {"name": "FeuerstelleGrillplatz"},
                    "1800": {"name": "Liegewiese"},
                    "1900": {"name": "Aussichtsturm"},
                    "2000": {"name": "Aussichtspunkt"},
                    "2100": {"name": "Angelteich"},
                    "2200": {"name": "Modellflugplatz"},
                    "2300": {"name": "WildgehegeSchaugatter"},
                    "2400": {"name": "JugendzeltplatzEinzelcamp"},
                    "2500": {"name": "Gleitschirmplatz"},
                    "2600": {"name": "Wandern"},
                    "2700": {"name": "Wanderweg"},
                    "2800": {"name": "Lehrpfad"},
                    "2900": {"name": "Reitweg"},
                    "3000": {"name": "Radweg"},
                    "3100": {"name": "Wintersport"},
                    "3200": {"name": "Skiabfahrt"},
                    "3300": {"name": "Skilanglaufloipe"},
                    "3400": {"name": "RodelbahnBobbahn"},
                    "3500": {"name": "Wassersport"},
                    "3600": {"name": "Wasserwanderweg"},
                    "3700": {"name": "Schifffahrtsroute"},
                    "3800": {"name": "AnlegestelleMitMotorbooten"},
                    "3900": {"name": "AnlegestelleOhneMotorboote"},
                    "4000": {"name": "SesselliftSchlepplift"},
                    "4100": {"name": "Kabinenseilbahn"},
                    "5000": {"name": "Parkplatz"},
                    "9999": {"name": "Sonstiges"},
                },
            },
        ),
    ] = None
    weitereFunktion1: Annotated[
        Literal[
            "1000",
            "1030",
            "1050",
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
            "2200",
            "2300",
            "2400",
            "2500",
            "2600",
            "2700",
            "2800",
            "2900",
            "3000",
            "3100",
            "3200",
            "3300",
            "3400",
            "3500",
            "3600",
            "3700",
            "3800",
            "3900",
            "4000",
            "4100",
            "5000",
            "9999",
        ]
        | None,
        Field(
            description='Weitere Funktion der Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen funktion mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Parkanlage"},
                    "1030": {"name": "Dauerkleingaerten"},
                    "1050": {"name": "Sportplatz"},
                    "1100": {"name": "Spielplatz"},
                    "1200": {"name": "Zeltplatz"},
                    "1300": {"name": "BadeplatzFreibad"},
                    "1400": {"name": "Schutzhuette"},
                    "1500": {"name": "Rastplatz"},
                    "1600": {"name": "Informationstafel"},
                    "1700": {"name": "FeuerstelleGrillplatz"},
                    "1800": {"name": "Liegewiese"},
                    "1900": {"name": "Aussichtsturm"},
                    "2000": {"name": "Aussichtspunkt"},
                    "2100": {"name": "Angelteich"},
                    "2200": {"name": "Modellflugplatz"},
                    "2300": {"name": "WildgehegeSchaugatter"},
                    "2400": {"name": "JugendzeltplatzEinzelcamp"},
                    "2500": {"name": "Gleitschirmplatz"},
                    "2600": {"name": "Wandern"},
                    "2700": {"name": "Wanderweg"},
                    "2800": {"name": "Lehrpfad"},
                    "2900": {"name": "Reitweg"},
                    "3000": {"name": "Radweg"},
                    "3100": {"name": "Wintersport"},
                    "3200": {"name": "Skiabfahrt"},
                    "3300": {"name": "Skilanglaufloipe"},
                    "3400": {"name": "RodelbahnBobbahn"},
                    "3500": {"name": "Wassersport"},
                    "3600": {"name": "Wasserwanderweg"},
                    "3700": {"name": "Schifffahrtsroute"},
                    "3800": {"name": "AnlegestelleMitMotorbooten"},
                    "3900": {"name": "AnlegestelleOhneMotorboote"},
                    "4000": {"name": "SesselliftSchlepplift"},
                    "4100": {"name": "Kabinenseilbahn"},
                    "5000": {"name": "Parkplatz"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "LP_ErholungFreizeitFunktionen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereFunktion2: Annotated[
        Literal[
            "1000",
            "1030",
            "1050",
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
            "2200",
            "2300",
            "2400",
            "2500",
            "2600",
            "2700",
            "2800",
            "2900",
            "3000",
            "3100",
            "3200",
            "3300",
            "3400",
            "3500",
            "3600",
            "3700",
            "3800",
            "3900",
            "4000",
            "4100",
            "5000",
            "9999",
        ]
        | None,
        Field(
            description='Weitere Funktion der Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen funktion mehrfach belegt werden.',
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Parkanlage"},
                    "1030": {"name": "Dauerkleingaerten"},
                    "1050": {"name": "Sportplatz"},
                    "1100": {"name": "Spielplatz"},
                    "1200": {"name": "Zeltplatz"},
                    "1300": {"name": "BadeplatzFreibad"},
                    "1400": {"name": "Schutzhuette"},
                    "1500": {"name": "Rastplatz"},
                    "1600": {"name": "Informationstafel"},
                    "1700": {"name": "FeuerstelleGrillplatz"},
                    "1800": {"name": "Liegewiese"},
                    "1900": {"name": "Aussichtsturm"},
                    "2000": {"name": "Aussichtspunkt"},
                    "2100": {"name": "Angelteich"},
                    "2200": {"name": "Modellflugplatz"},
                    "2300": {"name": "WildgehegeSchaugatter"},
                    "2400": {"name": "JugendzeltplatzEinzelcamp"},
                    "2500": {"name": "Gleitschirmplatz"},
                    "2600": {"name": "Wandern"},
                    "2700": {"name": "Wanderweg"},
                    "2800": {"name": "Lehrpfad"},
                    "2900": {"name": "Reitweg"},
                    "3000": {"name": "Radweg"},
                    "3100": {"name": "Wintersport"},
                    "3200": {"name": "Skiabfahrt"},
                    "3300": {"name": "Skilanglaufloipe"},
                    "3400": {"name": "RodelbahnBobbahn"},
                    "3500": {"name": "Wassersport"},
                    "3600": {"name": "Wasserwanderweg"},
                    "3700": {"name": "Schifffahrtsroute"},
                    "3800": {"name": "AnlegestelleMitMotorbooten"},
                    "3900": {"name": "AnlegestelleOhneMotorboote"},
                    "4000": {"name": "SesselliftSchlepplift"},
                    "4100": {"name": "Kabinenseilbahn"},
                    "5000": {"name": "Parkplatz"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "LP_ErholungFreizeitFunktionen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detaillierteFunktion: Annotated[
        list[AnyUrl] | None,
        Field(
            description="Über eine CodeList definierte zusätzliche Funktion der Fläche.",
            json_schema_extra={
                "typename": "LP_ErholungFreizeitDetailFunktionen",
                "stereotype": "Codelist",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    weitereDetailFunktion1: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Funktion der Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteFunktion mehrfach belegt werden.',
            json_schema_extra={
                "typename": "LP_ErholungFreizeitDetailFunktionen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weitereDetailFunktion2: Annotated[
        AnyUrl | None,
        Field(
            description='Über eine CodeList definierte zusätzliche Funktion der Fläche. Dies Attribut ist ab Version 4.1 als "veraltet" gekennzeichnet, es sollte stattdessen detaillierteFunktion mehrfach belegt werden.',
            json_schema_extra={
                "typename": "LP_ErholungFreizeitDetailFunktionen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class LPForstrecht(LPGeometrieobjekt):
    """Gebiete und Gebietsteile mit rechtlichen Bindungen nach anderen Fachgesetzen (soweit sie für den Schutz, die Pflege und die Entwicklung von Natur und Landschaft bedeutsam sind). Hier: Schutzgebiete und sonstige Flächen nach dem Bundeswaldgesetz."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    typ: Annotated[
        Literal[
            "1000",
            "2000",
            "2100",
            "2200",
            "2300",
            "2400",
            "2500",
            "3000",
            "3100",
            "3200",
            "9999",
        ]
        | None,
        Field(
            description="Typ des Schutzobjektes.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Naturwaldreservat"},
                    "2000": {"name": "SchutzwaldAllgemein"},
                    "2100": {"name": "Lawinenschutzwald"},
                    "2200": {"name": "Bodenschutzwald"},
                    "2300": {"name": "Klimaschutzwald"},
                    "2400": {"name": "Immissionsschutzwald"},
                    "2500": {"name": "Biotopschutzwald"},
                    "3000": {"name": "ErholungswaldAllgemein"},
                    "3100": {"name": "ErholungswaldHeilbaeder"},
                    "3200": {"name": "ErholungswaldBallungsraeume"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "LP_ForstrechtTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detailTyp: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definierter zusätzlicher Typ des Schutzobjektes.",
            json_schema_extra={
                "typename": "LP_WaldschutzDetailTypen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class LPGenerischesObjekt(LPGeometrieobjekt):
    """Klasse zur Modellierung aller Inhalte des Landschaftsplans, die durch keine andere Klasse des LPlan-Fachschemas dargestellt werden können."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    zweckbestimmung: Annotated[
        str | None,
        Field(
            description="Zweckbestimmung",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class RPAchse(RPLinienobjekt):
    """Siedlungsachse"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    achsenTyp: Annotated[
        Literal["1000", "2000", "9999"] | None,
        Field(
            description="Klassifikation verschiedener Achsen.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Siedlungsachse"},
                    "2000": {"name": "GrossraeumigeAchse"},
                    "9999": {"name": "SonstigeAchse"},
                },
                "typename": "RP_AchsenTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class RPBodenschutz(RPGeometrieobjekt):
    """Bodenschutz"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gebietsTyp: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000"]] | None,
        Field(
            description="Klassifikation des Gebietes nach Bundesraumordnungsgesetz.",
            json_schema_extra={
                "typename": "RP_GebietsTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Vorranggebiet"},
                    "2000": {"name": "Vorbehaltsgebiet"},
                    "3000": {"name": "Eignungsgebiet"},
                    "4000": {"name": "Ausschlussgebiet"},
                    "5000": {"name": "SonstigesGebiet"},
                },
            },
        ),
    ] = None
    istAusgleichsgebiet: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob es sich um ein Ausgleichsgebiet handelt.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False


class RPEnergieversorgung(RPGeometrieobjekt):
    """Infrastruktur zur Energieversorgung"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gebietsTyp: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000"]] | None,
        Field(
            description="Klassifikation des Gebietes nach Bundesraumordnungsgesetz.",
            json_schema_extra={
                "typename": "RP_GebietsTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Vorranggebiet"},
                    "2000": {"name": "Vorbehaltsgebiet"},
                    "3000": {"name": "Eignungsgebiet"},
                    "4000": {"name": "Ausschlussgebiet"},
                    "5000": {"name": "SonstigesGebiet"},
                },
            },
        ),
    ] = None
    typ: Annotated[
        Literal["1000", "2000", "3000", "4000", "5000", "9999"] | None,
        Field(
            description="Klassifikation von Energieversorgungs-Einrichtungen.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Hochspannungsleitung"},
                    "2000": {"name": "Pipeline"},
                    "3000": {"name": "Kraftwerk"},
                    "4000": {"name": "EnergieSpeicherung"},
                    "5000": {"name": "Umspannwerk"},
                    "9999": {"name": "SonstigeEnergieversorgung"},
                },
                "typename": "RP_EnergieversorgungTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class RPEntsorgung(RPGeometrieobjekt):
    """Entsorgungs-Infrastruktur"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gebietsTyp: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000"]] | None,
        Field(
            description="Klassifikation des Gebietes nach Bundesraumordnungsgesetz.",
            json_schema_extra={
                "typename": "RP_GebietsTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Vorranggebiet"},
                    "2000": {"name": "Vorbehaltsgebiet"},
                    "3000": {"name": "Eignungsgebiet"},
                    "4000": {"name": "Ausschlussgebiet"},
                    "5000": {"name": "SonstigesGebiet"},
                },
            },
        ),
    ] = None
    typ: Annotated[
        Literal["1000", "2000", "9999"] | None,
        Field(
            description="Klassifikation von ENtsorgungs-Arten.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Abfallwirtschaft"},
                    "2000": {"name": "Abwasserwirtschaft"},
                    "9999": {"name": "SonstigeEntsorgung"},
                },
                "typename": "RP_EntsorgungTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class RPForstwirtschaft(RPGeometrieobjekt):
    """Forstwirtschaft"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gebietsTyp: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000"]] | None,
        Field(
            description="Klassifikation des Gebietes nach Bundesraumordnungsgesetz.",
            json_schema_extra={
                "typename": "RP_GebietsTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Vorranggebiet"},
                    "2000": {"name": "Vorbehaltsgebiet"},
                    "3000": {"name": "Eignungsgebiet"},
                    "4000": {"name": "Ausschlussgebiet"},
                    "5000": {"name": "SonstigesGebiet"},
                },
            },
        ),
    ] = None
    istAusgleichsgebiet: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob es sich um ein Ausgleichsgebiet handelt.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False


class RPFreizeitErholung(RPGeometrieobjekt):
    """Freizeit und Erholung"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gebietsTyp: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000"]] | None,
        Field(
            description="Klassifikation des Gebietes nach Bundesraumordnungsgesetz.",
            json_schema_extra={
                "typename": "RP_GebietsTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Vorranggebiet"},
                    "2000": {"name": "Vorbehaltsgebiet"},
                    "3000": {"name": "Eignungsgebiet"},
                    "4000": {"name": "Ausschlussgebiet"},
                    "5000": {"name": "SonstigesGebiet"},
                },
            },
        ),
    ] = None
    istAusgleichsgebiet: Annotated[
        bool | None,
        Field(
            description="Gibt an, ob es sich um ein Ausgleichsgebiet handelt.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False


class RPGemeindeFunktionSiedlungsentwicklung(RPGeometrieobjekt):
    """Gemeindefunktion"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    gebietsTyp: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000"]] | None,
        Field(
            description="Klassifikation des Gebietes nach Bundesraumordnungsgesetz.",
            json_schema_extra={
                "typename": "RP_GebietsTyp",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Vorranggebiet"},
                    "2000": {"name": "Vorbehaltsgebiet"},
                    "3000": {"name": "Eignungsgebiet"},
                    "4000": {"name": "Ausschlussgebiet"},
                    "5000": {"name": "SonstigesGebiet"},
                },
            },
        ),
    ] = None
    funktion: Annotated[
        list[Literal["1000", "2000", "3000", "4000", "5000", "6000", "9999"]] | None,
        Field(
            description="Klassifikation von Gemeindefunktionen.",
            json_schema_extra={
                "typename": "RP_Gemeindefunktionen",
                "stereotype": "Enumeration",
                "multiplicity": "0..*",
                "enumDescription": {
                    "1000": {"name": "Wohnen"},
                    "2000": {"name": "Arbeiten"},
                    "3000": {"name": "Landwirtschaft"},
                    "4000": {"name": "Einzelhandel"},
                    "5000": {"name": "ErholungFremdenverkehr"},
                    "6000": {"name": "Verteidigung"},
                    "9999": {"name": "SonstigeNutzung"},
                },
            },
        ),
    ] = None


class RPGenerischesObjekt(RPGeometrieobjekt):
    """Klasse zur Modellierung aller Inhalte des Regionalplans, die durch keine andere Klasse des RPlan-Fachschemas dargestellt werden können."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    zweckbestimmung: Annotated[
        AnyUrl | None,
        Field(
            description="Über eine CodeList definierte Zweckbestimmung der Festlegung.",
            json_schema_extra={
                "typename": "RP_ZweckbestimmungGenerischeObjekte",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class SOBodenschutzrecht(SOGeometrieobjekt):
    """Festlegung nach Bodenschutzrecht."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    artDerFestlegung: Annotated[
        Literal["1000", "2000", "20000", "20001", "20002"] | None,
        Field(
            description="Grundlegende Klassifizierung der Festlegung.",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "SchaedlicheBodenveraenderung"},
                    "2000": {"name": "Altlast"},
                    "20000": {"name": "Altablagerung"},
                    "20001": {"name": "Altstandort"},
                    "20002": {"name": "AltstandortAufAltablagerung"},
                },
                "typename": "SO_KlassifizNachBodenschutzrecht",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detailArtDerFestlegung: Annotated[
        AnyUrl | None,
        Field(
            description="Detaillierte Klassifizierung der Festlegung",
            json_schema_extra={
                "typename": "SO_DetailKlassifizNachBodenschutzrecht",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    istVerdachtsflaeche: Annotated[
        bool | None,
        Field(
            description="Angabe ob es sich um eine Verdachtsfläche handelt.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = False
    name: Annotated[
        str | None,
        Field(
            description="Informelle Bezeichnung der Festlegung.",
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
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            }
        ),
    ] = None


class SODenkmalschutzrecht(SOGeometrieobjekt):
    """Festlegung nach Denkmalschutzrecht"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    artDerFestlegung: Annotated[
        Literal["1000", "1100", "1200", "1300", "1400", "9999"] | None,
        Field(
            description="Grundlegende rechtliche Klassifizierung der Festlegung",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "DenkmalschutzEnsemble"},
                    "1100": {"name": "DenkmalschutzEinzelanlage"},
                    "1200": {"name": "Grabungsschutzgebiet"},
                    "1300": {
                        "name": "PufferzoneWeltkulturerbeEnger",
                        "description": "Engere Pufferzone um eine Welterbestätte",
                    },
                    "1400": {
                        "name": "PufferzoneWeltkulturerbeWeiter",
                        "description": "Weitere Pufferzone um eine Welterbestätte",
                    },
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "SO_KlassifizNachDenkmalschutzrecht",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detailArtDerFestlegung: Annotated[
        AnyUrl | None,
        Field(
            description="Detaillierte rechtliche Klassifizierung der Festlegung",
            json_schema_extra={
                "typename": "SO_DetailKlassifizNachDenkmalschutzrecht",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    weltkulturerbe: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            }
        ),
    ] = False
    name: Annotated[
        str | None,
        Field(
            description="Informelle Bezeichnung der Festlegung",
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
            description="Amtliche Bezeichnung / Kennziffer der Festlegung",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class SOForstrecht(SOGeometrieobjekt):
    """Festlegung nach Forstrecht"""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    artDerFestlegung: Annotated[
        Literal["1000", "2000", "9999"] | None,
        Field(
            description="Grundlegende Klassifizierung der Festlegung",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "OeffentlicherWald"},
                    "2000": {"name": "Privatwald"},
                    "9999": {"name": "Sonstiges"},
                },
                "typename": "SO_KlassifizNachForstrecht",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    detailArtDerFestlegung: Annotated[
        AnyUrl | None,
        Field(
            description="Detaillierte Klassifizierung der Festlegung",
            json_schema_extra={
                "typename": "SO_DetailKlassifizNachForstrecht",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            description="Informelle Bezeichnung der Festlegung",
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
            description="Amtliche Bezeichnung / Kennziffer der Festlegung",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "multiplicity": "0..1",
            },
        ),
    ] = None


class SOGrenze(SOLinienobjekt):
    """Grenze einer Verwaltungseinheit oder sonstige Grenze in rambezogenen Plänen.."""

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://www.xplanung.de/xplangml/4/1"
    stereotype: ClassVar[str] = "FeatureType"
    typ: Annotated[
        Literal[
            "1000",
            "1100",
            "1200",
            "1250",
            "1300",
            "1400",
            "1450",
            "1500",
            "1510",
            "1550",
            "1600",
            "2000",
            "2100",
            "9999",
        ]
        | None,
        Field(
            description="Typ der Grenze",
            json_schema_extra={
                "enumDescription": {
                    "1000": {"name": "Bundesgrenze"},
                    "1100": {"name": "Landesgrenze"},
                    "1200": {"name": "Regierungsbezirksgrenze"},
                    "1250": {"name": "Bezirksgrenze"},
                    "1300": {"name": "Kreisgrenze"},
                    "1400": {"name": "Gemeindegrenze"},
                    "1450": {"name": "Verbandsgemeindegrenze"},
                    "1500": {"name": "Samtgemeindegrenze"},
                    "1510": {"name": "Mitgliedsgemeindegrenze"},
                    "1550": {"name": "Amtsgrenze"},
                    "1600": {"name": "Stadtteilgrenze"},
                    "2000": {
                        "name": "VorgeschlageneGrundstuecksgrenze",
                        "description": "Hinweis auf eine vorgeschlagene Grundstücksgrenze im BPlan.",
                    },
                    "2100": {
                        "name": "GrenzeBestehenderBebauungsplan",
                        "description": "Hinweis auf den Geltungsbereich eines bestehenden BPlan.",
                    },
                    "9999": {"name": "SonstGrenze"},
                },
                "typename": "XP_GrenzeTypen",
                "stereotype": "Enumeration",
                "multiplicity": "0..1",
            },
        ),
    ] = None
    sonstTyp: Annotated[
        AnyUrl | None,
        Field(
            json_schema_extra={
                "typename": "SO_SonstGrenzeTypen",
                "stereotype": "Codelist",
                "multiplicity": "0..1",
            }
        ),
    ] = None
