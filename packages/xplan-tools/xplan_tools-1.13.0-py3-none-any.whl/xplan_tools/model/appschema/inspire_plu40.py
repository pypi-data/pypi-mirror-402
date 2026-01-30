# generated from JSON Schema

from __future__ import annotations

from datetime import date as date_aliased
from typing import Annotated, Any, ClassVar
from uuid import UUID

from pydantic import AnyUrl, AwareDatetime, Field, RootModel

from ..base import BaseFeature
from . import definitions, inspire_base, inspire_base2


class Model(RootModel[Any]):
    root: Any


class BackgroundMapValue(BaseFeature):
    """
    Information regarding the map that has been used as a background in the definition of a spatial plan, a zoning element or a supplementary regulation.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://inspire.ec.europa.eu/schemas/plu/4.0"
    backgroundMapDate: Annotated[
        AwareDatetime,
        Field(
            description="Date of the background map used.",
            json_schema_extra={
                "typename": "DateTime",
                "stereotype": "Temporal",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    backgroundMapReference: Annotated[
        str,
        Field(
            description="Reference to the background map that has been used.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    backgroundMapURI: Annotated[
        definitions.VoidReasonValue | AnyUrl,
        Field(
            description="URI referring to service that provides background map.",
            json_schema_extra={
                "typename": "URI",
                "stereotype": "BasicType",
                "voidable": True,
                "multiplicity": "1",
            },
        ),
    ]


class DimensioningIndicationCharacterValue(BaseFeature):
    """
    Dimensioning indication whose value is of type CharacterString.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://inspire.ec.europa.eu/schemas/plu/4.0"
    indicationReference: Annotated[
        str,
        Field(
            description="Description of the dimension indication.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    value: Annotated[
        str,
        Field(
            description="value of the dimension indications.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]


class DimensioningIndicationIntegerValue(BaseFeature):
    """
    Dimensioning indication whose value is of type integer.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://inspire.ec.europa.eu/schemas/plu/4.0"
    indicationReference: Annotated[
        str,
        Field(
            description="Description of the dimension indication.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    value: Annotated[
        int,
        Field(
            json_schema_extra={
                "typename": "Integer",
                "stereotype": "BasicType",
                "voidable": False,
                "multiplicity": "1",
            }
        ),
    ]


class DimensioningIndicationMeasureValue(BaseFeature):
    """
    Dimensioning indication whose value is a measure.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://inspire.ec.europa.eu/schemas/plu/4.0"
    indicationReference: Annotated[
        str,
        Field(
            description="Description of the dimension indication.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    value: Annotated[
        definitions.GenericMeasure,
        Field(
            json_schema_extra={
                "typename": "Measure",
                "stereotype": "Measure",
                "voidable": False,
                "multiplicity": "1",
                "uom": "tbd",
            }
        ),
    ]


class DimensioningIndicationRealValue(BaseFeature):
    """
    Dimensioning indication whose value is a floating point number.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://inspire.ec.europa.eu/schemas/plu/4.0"
    indicationReference: Annotated[
        str,
        Field(
            description="Description of the dimension indication.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    value: Annotated[
        float,
        Field(
            json_schema_extra={
                "typename": "Real",
                "stereotype": "BasicType",
                "voidable": False,
                "multiplicity": "1",
            }
        ),
    ]


class DimensioningIndicationValue(BaseFeature):
    """
    Specifications about the dimensioning of the urban developments.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://inspire.ec.europa.eu/schemas/plu/4.0"
    indicationReference: Annotated[
        str,
        Field(
            description="Description of the dimension indication.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]


class OrdinanceValue(BaseFeature):
    """
    Reference to administrative ordinance. Ordinance is a regulation/rule that is adopted by an authority that is legally mandated to take such ordinance.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://inspire.ec.europa.eu/schemas/plu/4.0"
    ordinanceDate: Annotated[
        AwareDatetime,
        Field(
            description="Date of the relevant administrative ordinance.",
            json_schema_extra={
                "typename": "DateTime",
                "stereotype": "Temporal",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    ordinanceReference: Annotated[
        str,
        Field(
            description="Reference to relevant administrative ordinance.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]


class SpatialPlan(BaseFeature):
    """
    A set of documents that indicates a strategic direction for the development of a given geographic area, states the policies, priorities, programmes and land allocations that will implement the strategic direction and influences the distribution of people and activities in spaces of various scales. Spatial plans may be developed for urban planning, regional planning, environmental planning, landscape planning, national spatial plans, or spatial planning at the Union level.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://inspire.ec.europa.eu/schemas/plu/4.0"
    id: str | None = None
    inspireId: Annotated[
        inspire_base.Identifier,
        Field(
            description="External object identifier of the spatial plan.",
            json_schema_extra={
                "typename": "Identifier",
                "stereotype": "DataType",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    extent: Annotated[
        definitions.MultiPolygon,
        Field(
            description="Geometrical union of all the instances of the spatial objects ZoningElement and SupplementaryRegulation. When a SpatialPlan is only composed of a document, the attribute extent is the border of the cartographic image that contains the land use information (i.e. the land use map extent).",
            json_schema_extra={
                "typename": "GM_MultiSurface",
                "stereotype": "Geometry",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    beginLifespanVersion: Annotated[
        definitions.VoidReasonValue | AwareDatetime,
        Field(
            description="Date and time at which this version of the spatial object was inserted or changed in the spatial data set.",
            json_schema_extra={
                "typename": "DateTime",
                "stereotype": "Temporal",
                "voidable": True,
                "multiplicity": "1",
            },
        ),
    ]
    officialTitle: Annotated[
        str,
        Field(
            description="Official title of the spatial plan.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    levelOfSpatialPlan: Annotated[
        AnyUrl,
        Field(
            description="Level of the administrative units covered by the plan.",
            json_schema_extra={
                "typename": "LevelOfSpatialPlanValue",
                "stereotype": "Codelist",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    endLifespanVersion: Annotated[
        definitions.VoidReasonValue | AwareDatetime | None,
        Field(
            description="Date and time at which this version of the spatial object was superseded or retired in the spatial data set.",
            json_schema_extra={
                "typename": "DateTime",
                "stereotype": "Temporal",
                "voidable": True,
                "multiplicity": "0..1",
            },
        ),
    ] = None
    validFrom: Annotated[
        definitions.VoidReasonValue | date_aliased | None,
        Field(
            description="First date at which this spatial plan is valid in reality.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "voidable": True,
                "multiplicity": "0..1",
            },
        ),
    ] = None
    validTo: Annotated[
        definitions.VoidReasonValue | date_aliased | None,
        Field(
            description="The time from which the spatial plan no longer exists in the real world.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "voidable": True,
                "multiplicity": "0..1",
            },
        ),
    ] = None
    alternativeTitle: Annotated[
        definitions.VoidReasonValue | str,
        Field(
            description="Alternative (unofficial) title of the spatial plan.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": True,
                "multiplicity": "1",
            },
        ),
    ]
    planTypeName: Annotated[
        AnyUrl,
        Field(
            description="Name of the type of plan that the Member State has given to the plan.",
            json_schema_extra={
                "typename": "PlanTypeNameValue",
                "stereotype": "Codelist",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    processStepGeneral: Annotated[
        definitions.VoidReasonValue | AnyUrl,
        Field(
            description="General indication of the step of the planning process that the plan is undergoing.",
            json_schema_extra={
                "typename": "ProcessStepGeneralValue",
                "stereotype": "Codelist",
                "voidable": True,
                "multiplicity": "1",
            },
        ),
    ]
    backgroundMap: Annotated[
        definitions.VoidReasonValue | BackgroundMapValue,
        Field(
            description="Identification of the background map that has been used for constructing this Plan.",
            json_schema_extra={
                "typename": "BackgroundMapValue",
                "stereotype": "DataType",
                "voidable": True,
                "multiplicity": "1",
            },
        ),
    ]
    ordinance: Annotated[
        definitions.VoidReasonValue | list[OrdinanceValue],
        Field(
            description="Reference to relevant administrative ordinance.",
            json_schema_extra={
                "typename": "OrdinanceValue",
                "stereotype": "DataType",
                "voidable": True,
                "multiplicity": "1..*",
            },
        ),
    ]
    officialDocument: Annotated[
        definitions.VoidReasonValue | list[AnyUrl | UUID],
        Field(
            description="Link to the official documents that relate to the spatial plan.",
            json_schema_extra={
                "typename": "OfficialDocumentation",
                "stereotype": "Association",
                "voidable": True,
                "multiplicity": "1..*",
            },
        ),
    ]
    member: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            description="Reference to the ZoningElements which belong to this SpatialPlan.",
            json_schema_extra={
                "typename": "ZoningElement",
                "stereotype": "Association",
                "voidable": False,
                "reverseProperty": "plan",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            },
        ),
    ] = None
    restriction: Annotated[
        list[AnyUrl | UUID] | None,
        Field(
            description="Links to supplementary regulations providing information and/or limitations on the use of land/water that supplements the zoning as part of this spatial plan.",
            json_schema_extra={
                "typename": "SupplementaryRegulation",
                "stereotype": "Association",
                "voidable": False,
                "reverseProperty": "plan",
                "sourceOrTarget": "target",
                "multiplicity": "0..*",
            },
        ),
    ] = None


class ZoningElement(BaseFeature):
    """
    A spatial object which is homogeneous regarding the permitted uses of land based on zoning which separate one set of land uses from another.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://inspire.ec.europa.eu/schemas/plu/4.0"
    id: str | None = None
    inspireId: Annotated[
        inspire_base.Identifier,
        Field(
            description="External object identifier of the spatial object.",
            json_schema_extra={
                "typename": "Identifier",
                "stereotype": "DataType",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    geometry: Annotated[
        definitions.MultiPolygon,
        Field(
            description="Geometry of this zoning element",
            json_schema_extra={
                "typename": "GM_MultiSurface",
                "stereotype": "Geometry",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    validFrom: Annotated[
        definitions.VoidReasonValue | date_aliased | None,
        Field(
            description="The date when the phenomenon started to exist in the real world.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "voidable": True,
                "multiplicity": "0..1",
            },
        ),
    ] = None
    validTo: Annotated[
        definitions.VoidReasonValue | date_aliased | None,
        Field(
            description="The time from which the phenomenon no longer exists in the real world.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "voidable": True,
                "multiplicity": "0..1",
            },
        ),
    ] = None
    hilucsLandUse: Annotated[
        list[AnyUrl],
        Field(
            description="Land use HILUCS class that is dominant in this land use object.",
            json_schema_extra={
                "typename": "HILUCSValue",
                "stereotype": "Codelist",
                "voidable": False,
                "multiplicity": "1..*",
            },
        ),
    ]
    beginLifespanVersion: Annotated[
        definitions.VoidReasonValue | AwareDatetime,
        Field(
            description="Date and time at which this version of the spatial object was inserted or changed in the spatial data set.",
            json_schema_extra={
                "typename": "DateTime",
                "stereotype": "Temporal",
                "voidable": True,
                "multiplicity": "1",
            },
        ),
    ]
    hilucsPresence: Annotated[
        definitions.VoidReasonValue,
        Field(
            description="Actual presence of a land use HILUCS category wihtin the object.",
            json_schema_extra={
                "typename": "HILUCSPresence",
                "voidable": True,
                "multiplicity": "1",
            },
        ),
    ]
    specificLandUse: Annotated[
        definitions.VoidReasonValue | list[AnyUrl],
        Field(
            description="Land Use Category according to the nomenclature specific to this data set.",
            json_schema_extra={
                "typename": "LandUseClassificationValue",
                "stereotype": "Codelist",
                "voidable": True,
                "multiplicity": "1..*",
            },
        ),
    ]
    specificPresence: Annotated[
        definitions.VoidReasonValue,
        Field(
            description="Actual presence of a land use category wihtin the object.",
            json_schema_extra={
                "typename": "SpecificPresence",
                "voidable": True,
                "multiplicity": "1",
            },
        ),
    ]
    regulationNature: Annotated[
        AnyUrl,
        Field(
            description="Legal nature of the land use indication.",
            json_schema_extra={
                "typename": "RegulationNatureValue",
                "stereotype": "Codelist",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    endLifespanVersion: Annotated[
        definitions.VoidReasonValue | AwareDatetime | None,
        Field(
            description="Date and time at which this version of the spatial object was superseded or retired in the spatial data set.",
            json_schema_extra={
                "typename": "DateTime",
                "stereotype": "Temporal",
                "voidable": True,
                "multiplicity": "0..1",
            },
        ),
    ] = None
    processStepGeneral: Annotated[
        definitions.VoidReasonValue | AnyUrl,
        Field(
            description="General indication of the step of the planning process that the zoning element is undergoing.",
            json_schema_extra={
                "typename": "ProcessStepGeneralValue",
                "stereotype": "Codelist",
                "voidable": True,
                "multiplicity": "1",
            },
        ),
    ]
    backgroundMap: Annotated[
        definitions.VoidReasonValue | BackgroundMapValue,
        Field(
            description="Identification of the background map that has been used for constructing this zoning element.",
            json_schema_extra={
                "typename": "BackgroundMapValue",
                "stereotype": "DataType",
                "voidable": True,
                "multiplicity": "1",
            },
        ),
    ]
    dimensioningIndication: Annotated[
        definitions.VoidReasonValue
        | list[
            DimensioningIndicationValue
            | DimensioningIndicationCharacterValue
            | DimensioningIndicationIntegerValue
            | DimensioningIndicationMeasureValue
            | DimensioningIndicationRealValue
        ]
        | None,
        Field(
            description="Specifications about the dimensioning of the urban developments.",
            json_schema_extra={
                "typename": [
                    "DimensioningIndicationCharacterValue",
                    "DimensioningIndicationIntegerValue",
                    "DimensioningIndicationMeasureValue",
                    "DimensioningIndicationRealValue",
                    "DimensioningIndicationValue",
                ],
                "stereotype": "DataType",
                "voidable": True,
                "multiplicity": "0..*",
            },
        ),
    ] = None
    officialDocument: Annotated[
        definitions.VoidReasonValue | list[AnyUrl | UUID],
        Field(
            description="Textual Regulation that is part of this zoning element.",
            json_schema_extra={
                "typename": "OfficialDocumentation",
                "stereotype": "Association",
                "voidable": True,
                "multiplicity": "1..*",
            },
        ),
    ]
    plan: Annotated[
        AnyUrl | UUID,
        Field(
            description="SpatialPlan which this ZoningElement belongs to.",
            json_schema_extra={
                "typename": "SpatialPlan",
                "stereotype": "Association",
                "voidable": False,
                "reverseProperty": "member",
                "sourceOrTarget": "source",
                "multiplicity": "1",
            },
        ),
    ]


class OfficialDocumentation(BaseFeature):
    """
    The official documentation that composes the spatial plan; it may be composed of, the applicable legislation, the regulations, cartographic elements, descriptive elements that may be associated with the complete spatial plan, a zoning element or a supplementary regulation . In some Member States the actual textual regulation will be part of the data set (and can be put in the regulationText attribute), in other Member States the text will not be part of the data set and will be referenced via a reference to a document or a legal act.

    At least one of the three voidable values shall be provided.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://inspire.ec.europa.eu/schemas/plu/4.0"
    id: str | None = None
    inspireId: Annotated[
        inspire_base.Identifier,
        Field(
            description="External object identifier of this spatial textual regulation.",
            json_schema_extra={
                "typename": "Identifier",
                "stereotype": "DataType",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    legislationCitation: Annotated[
        definitions.VoidReasonValue | inspire_base2.LegislationCitation | None,
        Field(
            description="Reference to the document that contains the text of the regulation.",
            json_schema_extra={
                "typename": "LegislationCitation",
                "stereotype": "ObjectType",
                "voidable": True,
                "multiplicity": "0..1",
            },
        ),
    ] = None
    regulationText: Annotated[
        definitions.VoidReasonValue | str | None,
        Field(
            description="Text of the regulation.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": True,
                "multiplicity": "0..1",
            },
        ),
    ] = None
    planDocument: Annotated[
        definitions.VoidReasonValue | inspire_base2.DocumentCitation | None,
        Field(
            description="Citation of scanned plans and structural drawings which may sometimes be geo-referenced or not,. E.g. raster images, vector drawings or scanned text.",
            json_schema_extra={
                "typename": "DocumentCitation",
                "stereotype": "ObjectType",
                "voidable": True,
                "multiplicity": "0..1",
            },
        ),
    ] = None


class SupplementaryRegulation(BaseFeature):
    """
    A spatial object (point, line or polygon) of a spatial plan that provides supplementary information and/or limitation of the use of land/water necessary for spatial planning reasons or to formalise external rules defined in legal text.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://inspire.ec.europa.eu/schemas/plu/4.0"
    id: str | None = None
    validFrom: Annotated[
        definitions.VoidReasonValue | date_aliased | None,
        Field(
            description="First date at which this version of this supplementary regulation is valid in reality.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "voidable": True,
                "multiplicity": "0..1",
            },
        ),
    ] = None
    validTo: Annotated[
        definitions.VoidReasonValue | date_aliased | None,
        Field(
            description="The time from which the supplementary regulation is no longer valid.",
            json_schema_extra={
                "typename": "Date",
                "stereotype": "Temporal",
                "voidable": True,
                "multiplicity": "0..1",
            },
        ),
    ] = None
    specificSupplementaryRegulation: Annotated[
        definitions.VoidReasonValue | list[AnyUrl],
        Field(
            description="Reference to a category of supplementary regulation provided in a specific nomenclature of supplementary regulations provided by the data provider.",
            json_schema_extra={
                "typename": "SpecificSupplementaryRegulationValue",
                "stereotype": "Codelist",
                "voidable": True,
                "multiplicity": "1..*",
            },
        ),
    ]
    processStepGeneral: Annotated[
        definitions.VoidReasonValue | AnyUrl,
        Field(
            description="General indication of the step of the planning process that the supplementary regulation is undergoing.",
            json_schema_extra={
                "typename": "ProcessStepGeneralValue",
                "stereotype": "Codelist",
                "voidable": True,
                "multiplicity": "1",
            },
        ),
    ]
    backgroundMap: Annotated[
        definitions.VoidReasonValue | BackgroundMapValue,
        Field(
            description="Identification of the background map that has been used for constructing the supplementary regulation.",
            json_schema_extra={
                "typename": "BackgroundMapValue",
                "stereotype": "DataType",
                "voidable": True,
                "multiplicity": "1",
            },
        ),
    ]
    beginLifespanVersion: Annotated[
        definitions.VoidReasonValue | AwareDatetime,
        Field(
            description="Date and time at which this version of the spatial object was inserted or changed in the spatial data set.",
            json_schema_extra={
                "typename": "DateTime",
                "stereotype": "Temporal",
                "voidable": True,
                "multiplicity": "1",
            },
        ),
    ]
    dimensioningIndication: Annotated[
        definitions.VoidReasonValue
        | list[
            DimensioningIndicationValue
            | DimensioningIndicationCharacterValue
            | DimensioningIndicationIntegerValue
            | DimensioningIndicationMeasureValue
            | DimensioningIndicationRealValue
        ]
        | None,
        Field(
            description="Specifications about the dimensioning that are added to the dimensioning of the zoning elements that overlap the geometry of the supplementary regulation.",
            json_schema_extra={
                "typename": [
                    "DimensioningIndicationCharacterValue",
                    "DimensioningIndicationIntegerValue",
                    "DimensioningIndicationMeasureValue",
                    "DimensioningIndicationRealValue",
                    "DimensioningIndicationValue",
                ],
                "stereotype": "DataType",
                "voidable": True,
                "multiplicity": "0..*",
            },
        ),
    ] = None
    inspireId: Annotated[
        inspire_base.Identifier,
        Field(
            description="External object identifier of the spatial object.",
            json_schema_extra={
                "typename": "Identifier",
                "stereotype": "DataType",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    endLifespanVersion: Annotated[
        definitions.VoidReasonValue | AwareDatetime | None,
        Field(
            description="Date and time at which this version of the spatial object was superseded or retired in the spatial data set.",
            json_schema_extra={
                "typename": "DateTime",
                "stereotype": "Temporal",
                "voidable": True,
                "multiplicity": "0..1",
            },
        ),
    ] = None
    geometry: Annotated[
        definitions.Point
        | definitions.MultiPoint
        | definitions.Line
        | definitions.MultiLine
        | definitions.Polygon
        | definitions.MultiPolygon,
        Field(
            description="Geometry of the piece of land on which the supplementary regulation applies.",
            json_schema_extra={
                "typename": "GM_Object",
                "stereotype": "Geometry",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    inheritedFromOtherPlans: Annotated[
        definitions.VoidReasonValue | bool,
        Field(
            description="Indication whether the supplementary regulation is inherited from another spatial plan.",
            json_schema_extra={
                "typename": "Boolean",
                "stereotype": "BasicType",
                "voidable": True,
                "multiplicity": "1",
            },
        ),
    ]
    specificRegulationNature: Annotated[
        definitions.VoidReasonValue | str,
        Field(
            description="Legal nature of the land use regulation from a national perspective.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": True,
                "multiplicity": "1",
            },
        ),
    ]
    name: Annotated[
        definitions.VoidReasonValue | list[str] | None,
        Field(
            description="Official name of the supplementary regulation",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": True,
                "multiplicity": "0..*",
            },
        ),
    ] = None
    regulationNature: Annotated[
        AnyUrl,
        Field(
            description="Legal nature of the land use regulation.",
            json_schema_extra={
                "typename": "RegulationNatureValue",
                "stereotype": "Codelist",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    supplementaryRegulation: Annotated[
        list[AnyUrl],
        Field(
            description="Code of the supplementary regulation from the hierarchical supplementary regulation code list agreed at the European level.",
            json_schema_extra={
                "typename": "SupplementaryRegulationValue",
                "stereotype": "Codelist",
                "voidable": False,
                "multiplicity": "1..*",
            },
        ),
    ]
    officialDocument: Annotated[
        definitions.VoidReasonValue | list[AnyUrl | UUID],
        Field(
            description="Link to the Textual regulations that correspond to this supplementary regulation.",
            json_schema_extra={
                "typename": "OfficialDocumentation",
                "stereotype": "Association",
                "voidable": True,
                "multiplicity": "1..*",
            },
        ),
    ]
    plan: Annotated[
        AnyUrl | UUID,
        Field(
            description="Link to the plan this supplementary regulation is part of.",
            json_schema_extra={
                "typename": "SpatialPlan",
                "stereotype": "Association",
                "voidable": False,
                "reverseProperty": "restriction",
                "sourceOrTarget": "source",
                "multiplicity": "1",
            },
        ),
    ]
