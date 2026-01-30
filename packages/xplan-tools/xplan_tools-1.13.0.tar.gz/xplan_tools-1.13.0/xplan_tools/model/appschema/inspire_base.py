# generated from JSON Schema

from __future__ import annotations

from typing import Annotated, Any, ClassVar

from pydantic import AnyUrl, Field, RootModel

from ..base import BaseFeature
from . import definitions


class Model(RootModel[Any]):
    root: Annotated[
        Any, Field(description="schema for basic types used by multiple themes")
    ]


class ConditionOfFacilityValue(RootModel[AnyUrl]):
    root: Annotated[
        AnyUrl,
        Field(
            description="The status of a facility with regards to its completion and use."
        ),
    ]


class Identifier(BaseFeature):
    """
    External unique object identifier published by the responsible body, which may be used by external applications to reference the spatial object.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://inspire.ec.europa.eu/schemas/base/4.0"
    localId: Annotated[
        str,
        Field(
            description="A local identifier, assigned by the data provider. The local identifier is unique within the namespace, that is no other spatial object carries the same unique identifier.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    namespace: Annotated[
        str,
        Field(
            description="Namespace uniquely identifying the data source of the spatial object.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    versionId: Annotated[
        definitions.VoidReasonValue | str | None,
        Field(
            description="The identifier of the particular version of the spatial object, with a maximum length of 25 characters. If the specification of a spatial object type with an external object identifier includes life-cycle information, the version identifier is used to distinguish between the different versions of a spatial object. Within the set of all versions of a spatial object, the version identifier is unique.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": True,
                "multiplicity": "0..1",
            },
        ),
    ] = None


class VerticalPositionValue(RootModel[AnyUrl]):
    root: Annotated[
        AnyUrl, Field(description="The relative vertical position of a spatial object.")
    ]


class VoidReasonValue(RootModel[AnyUrl]):
    root: Annotated[AnyUrl, Field(description="Reasons for void values.")]
