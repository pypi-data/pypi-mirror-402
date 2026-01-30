# generated from JSON Schema

from __future__ import annotations

from datetime import date as date_aliased
from typing import Annotated, Any, ClassVar

from pydantic import AnyUrl, Field, RootModel

from ..base import BaseFeature
from . import definitions


class Model(RootModel[Any]):
    root: Annotated[
        Any,
        Field(description="schema for additional basic types used by multiple themes"),
    ]


class ApplicationSchemaValue(RootModel[AnyUrl]):
    root: Annotated[
        AnyUrl,
        Field(
            description="application schema specified in an INSPIRE data specification"
        ),
    ]


class CFStandardNamesValue(RootModel[AnyUrl]):
    root: Annotated[
        AnyUrl,
        Field(
            description="Definitions of phenomena observed in meteorology and oceanography."
        ),
    ]


class CountryCode(RootModel[AnyUrl]):
    root: Annotated[
        AnyUrl,
        Field(
            description="Country code as defined in the Interinstitutional style guide published by the Publications Office of the European Union."
        ),
    ]


class DocumentCitation(BaseFeature):
    """
    Citation for the purposes of unambiguously referencing a document.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://inspire.ec.europa.eu/schemas/base2/2.0"
    id: str | None = None
    name: Annotated[
        str,
        Field(
            description="Name of the document.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    shortName: Annotated[
        definitions.VoidReasonValue | str | None,
        Field(
            description="Short name or alternative title of the document.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": True,
                "multiplicity": "0..1",
            },
        ),
    ] = None
    date: Annotated[
        definitions.VoidReasonValue | definitions.CIDate,
        Field(
            description="Date of creation, publication or revision of the document.",
            json_schema_extra={
                "typename": "CI_Date",
                "stereotype": "DataType",
                "voidable": True,
                "multiplicity": "1",
            },
        ),
    ]
    link: Annotated[
        definitions.VoidReasonValue | list[AnyUrl],
        Field(
            description="Link to an online version of the document",
            json_schema_extra={
                "typename": "URL",
                "stereotype": "BasicType",
                "voidable": True,
                "multiplicity": "1..*",
            },
        ),
    ]
    specificReference: Annotated[
        definitions.VoidReasonValue | list[str] | None,
        Field(
            description="Reference to a specific part of the document.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": True,
                "multiplicity": "0..*",
            },
        ),
    ] = None


class GenderValue(RootModel[AnyUrl]):
    root: Annotated[
        AnyUrl, Field(description="Gender of a person or group of persons.")
    ]


class OfficialJournalInformation(BaseFeature):
    """
    Full citation of the location of the legislative instrument within the official journal.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://inspire.ec.europa.eu/schemas/base2/2.0"
    officialJournalIdentification: Annotated[
        str,
        Field(
            description="Reference to the location within the official journal within which the legislative instrument was published. This reference shall be comprised of three parts:\r\n\t- the title of the official journal\r\n\t- the volume and/or series number\r\n\t- Page number(s)",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    ISSN: Annotated[
        str | None,
        Field(
            description="The International Standard Serial Number (ISSN) is an eight-digit number that identifies the periodical publication in which the legislative instrument was published.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": False,
                "multiplicity": "0..1",
            },
        ),
    ] = None
    ISBN: Annotated[
        str | None,
        Field(
            description="International Standard Book Number (ISBN) is an nine-digit number that uniquely identifies the book in which the legislative instrument was published.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": False,
                "multiplicity": "0..1",
            },
        ),
    ] = None
    linkToJournal: Annotated[
        AnyUrl | None,
        Field(
            description="Link to an online version of the official journal",
            json_schema_extra={
                "typename": "URL",
                "stereotype": "BasicType",
                "voidable": False,
                "multiplicity": "0..1",
            },
        ),
    ] = None


class PartyRoleValue(RootModel[AnyUrl]):
    root: Annotated[
        AnyUrl,
        Field(description="Roles of parties related to or responsible for a resource."),
    ]


class RelatedPartyRoleValue(RootModel[AnyUrl]):
    root: Annotated[AnyUrl, Field(description="Classification of related party roles.")]


class ThematicIdentifier(BaseFeature):
    """
    Thematic identifier to uniquely identify the spatial object.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://inspire.ec.europa.eu/schemas/base2/2.0"
    identifier: Annotated[
        str,
        Field(
            description="Unique identifier used to identify the spatial object within the specified identification scheme.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    identifierScheme: Annotated[
        str,
        Field(
            description="Identifier defining the scheme used to assign the identifier.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]


class ThemeValue(RootModel[AnyUrl]):
    root: Annotated[
        AnyUrl,
        Field(
            description="grouping of spatial data according to Annex I, II and III of the INSPIRE Directive"
        ),
    ]


class LegislationCitation(DocumentCitation):
    """
    Citation for the purposes of unambiguously referencing a legal act or a specific part of a legal act.
    """

    abstract: ClassVar[bool] = False
    namespace_uri: ClassVar[str] = "http://inspire.ec.europa.eu/schemas/base2/2.0"
    identificationNumber: Annotated[
        str | None,
        Field(
            description="Code used to identify the legislative instrument",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": False,
                "multiplicity": "0..1",
            },
        ),
    ] = None
    officialDocumentNumber: Annotated[
        str | None,
        Field(
            description="Official document number used to uniquely identify the legislative instrument.",
            json_schema_extra={
                "typename": "CharacterString",
                "stereotype": "BasicType",
                "voidable": False,
                "multiplicity": "0..1",
            },
        ),
    ] = None
    dateEnteredIntoForce: Annotated[
        date_aliased | None,
        Field(
            description="Date the legislative instrument entered into force.",
            json_schema_extra={
                "typename": "TM_Position",
                "stereotype": "Temporal",
                "voidable": False,
                "multiplicity": "0..1",
            },
        ),
    ] = None
    dateRepealed: Annotated[
        date_aliased | None,
        Field(
            description="Date the legislative instrument was repealed.",
            json_schema_extra={
                "typename": "TM_Position",
                "stereotype": "Temporal",
                "voidable": False,
                "multiplicity": "0..1",
            },
        ),
    ] = None
    level: Annotated[
        AnyUrl,
        Field(
            description="The level at which the legislative instrument is adopted.",
            json_schema_extra={
                "typename": "LegislationLevelValue",
                "stereotype": "Codelist",
                "voidable": False,
                "multiplicity": "1",
            },
        ),
    ]
    journalCitation: Annotated[
        OfficialJournalInformation | None,
        Field(
            description="Citation of the official journal in which the legislation is published.",
            json_schema_extra={
                "typename": "OfficialJournalInformation",
                "stereotype": "DataType",
                "voidable": False,
                "multiplicity": "0..1",
            },
        ),
    ] = None
