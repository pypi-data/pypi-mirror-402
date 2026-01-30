r"""Module, containing the explicit transformation and mapping rules for XPlan 6.* to INSPIRE PLU 4.0.

This module maps, among others, the following XPlan classes to INSPIRE PLU: \n
- BP_Plan    -> SpatialPlan and OfficialDocumentation \n
- FP_Plan    -> SpatialPlan and OfficialDocumentation \n
- RP_Plan    -> SpatialPlan and OfficialDocumentation \n
- SO_Plan    -> SpatialPlan and OfficialDocumentation \n
- BP_Bereich -> OfficialDocumentation (via Reference in SpatialPlan) \n
- FP_Bereich -> OfficialDocumentation (via Reference in SpatialPlan) \n
- RP_Bereich -> OfficialDocumentation (via Reference in SpatialPlan) \n
- SO_Bereich -> OfficialDocumentation (via Reference in SpatialPlan) \n
- BP_Punktobjekt and their sublasses     -> SupplementaryRegulation \n
- FP_Punktobjekt and their sublasses     -> SupplementaryRegulation \n
- SO_Punktobjekt and their sublasses     -> SupplementaryRegulation \n
- BP_Linienobjekt and their sublasses    -> SupplementaryRegulation \n
- FP_Linienobjekt and their sublasses    -> SupplementaryRegulation \n
- SO_Linienobjekt and their sublasses    -> SupplementaryRegulation \n
- BP_Geometrieobjekt and their sublasses -> either SupplementaryRegulation or ZoningElement \n
- FP_Geometrieobjekt and their sublasses -> either SupplementaryRegulation or ZoningElement \n
- RP_Geometrieobjekt and their sublasses -> either SupplementaryRegulation or ZoningElement \n
- SO_Geometrieobjekt and their sublasses -> either SupplementaryRegulation or ZoningElement \n
- BP_Flaechenobjekt and their sublasses  -> either SupplementaryRegulation or ZoningElement \n
- FP_Flaechenobjekt and their sublasses  -> either SupplementaryRegulation or ZoningElement \n
- SO_Flaechenobjekt and their sublasses  -> either SupplementaryRegulation or ZoningElement \n
"""

import logging
import uuid
from datetime import datetime
from typing import Literal, Union

import pytz
from pydantic import AwareDatetime, ValidationError

from xplan_tools.model import model_factory
from xplan_tools.model.appschema.definitions import CIDate

logger = logging.getLogger(__name__)


class rules_6x_plu:
    r"""Base class, containing transformations for all XPlan Data types to INSPIRE PLU.

    Included are transformations for the abstract base classes,
    methods for creating and managing additional objects, needed in INSPIRE,
    as well as additional helper functions.
    Transformations/Mappings are applied in succesion, allowing for factorization
    of common attribute mappings according to the respeptive (abstract) class.

    Example:
        In case of the XPlan object FP_Flaecheohnedarstellung, which is a childclass of
        FP_Fflaechenschlussobjekt, which in turn is a childclass of FP_Flaechenobjekt,...
        all the way back to the abstract class XP_Objekt, we would run the following
        transformations in this order \n

        _xpobjekt(object)  \n
        _fpobjekt(object)  \n
        _fpflaechenobjekt(object)  \n
        _fpflaechenschlussobjekt(object)  \n
        _fpflaecheohnedarstellung(object) \n

        Note that this is taken care of automatically in the class, which is inheriting from
        rules_6x_plu and which is doing the actual transformation of XPlan data
    """

    def __init__(
        self, inspire_id_ns: str, xplan_appschema: Literal["6.0", "6.1"] = "6.0"
    ):
        """Initialize the rules class with namespace and appschema version."""
        self.namespace = inspire_id_ns
        self.voidreasonvalue = {
            "nilReason": "http://inspire.ec.europa.eu/codelist/VoidReasonValue/Unpopulated"
        }
        self.xplan_appschema = xplan_appschema

    def __create_uuid(self, namespace_id: str, wert: str) -> uuid.UUID:
        """Take the namespace id and a string of the document for idnentification to create a new reference.

        The method creates reference id's for additional documents.

        Args:
            namespace_id (str): namespace id of base object
            wert (str): string of document to be referenced

        Returns:
            uuid.UUID: new reference id
        """
        namespace_uuid = uuid.UUID(namespace_id)

        return str(uuid.uuid5(namespace_uuid, str(wert)))

    def __validate_model(self, model_class: str, data: dict) -> bool:
        """Check if data in dict format is instance of certain XPlan class.

        Args:
            model_class (str): model to check against
            data (dict): data in dict format

        Returns:
            bool: if data belongs to certain XPlan class or not
        """
        model = model_factory(model_class, self.xplan_appschema, "xplan")

        try:
            model.model_validate(data)
            return True
        except ValidationError:
            # logger.info(e)
            return False

    def __add_XPURL_to_officialDocument(self, object: dict, attr: dict) -> None:
        """Maps XP_URL Attribute to corresponding attribute of officialDocument and references it in SpatialPlan.

        A new officialDocument is created, with emphasis on the XP_URL class
        It is then temporarily stored and referenced in the existing plan.

        Args:
            object (dict): plan
            attr (dict): XP_URL Attribute
        """
        ref_uuid = self.__create_uuid(
            object["inspireId"]["localId"], str(attr.get("wert"))
        )
        document = {
            "id": ref_uuid,
            "inspireId": {
                "localId": ref_uuid,
                "namespace": self.namespace,
            },
            "legislationCitation": self.voidreasonvalue,
            "regulationText": self.voidreasonvalue,
            "planDocument": {
                "name": attr.get("name"),
                "link": [attr.get("wert")],
                # shortname = URLAttribut?
                "date": self.voidreasonvalue,
            },
        }
        self.__set_VoidReasonValue_fromlist(document, type="OfficialDocument")
        object.setdefault("officialDocument", []).append(ref_uuid)
        object.setdefault("officialDocument_list", []).append(document)

    def __add_XP_ExterneReferenz_to_officialDocument(
        self,
        ref_uuid,
        refText: dict,
        shortName: Union[str, None] = None,
    ) -> dict:
        """Maps XP_ExterneReferenz to DocumentCitation attribute of officialDocument.

        This method is called within other wrapper methods to specifically populate the
        planDocument attribute of the new officialDocument.

        Args:
            ref_uuid: uuid of the reference
            refText (dict): reference text
            shortName (Union[str, None], optional): shortname of the reference. Defaults to None.

        Returns:
            dict: dictionary of DocumentCitation attributes
        """
        link_list = []
        for link in ["georefURL", "referenzURL"]:
            if refText.get(link, None):
                link_list.append(refText.get(link))

        date = (
            CIDate(
                date=refText.get("datum", None),
                dateType="https://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#CI_DateTypeCode_creation",
            )
            if refText.get("datum")
            else self.voidreasonvalue
        )

        refText_dict = {
            "id": f"{ref_uuid}.0",
            "date": date,
            "link": link_list if link_list else self.voidreasonvalue,
            "name": refText.get("referenzName"),
            "shortName": shortName,
        }

        return refText_dict

    def __wrapper_XP_ExterneReferenz(
        self, object: dict, refText: dict, shortName: Union[str, None] = None
    ) -> None:
        """Maps XP_ExterneReferenz to DocumentCitation attribute of officialDocument and references it in SpatialPlan.

        A new officialDocument is created, with emphasis on the XP_ExterneReferenz class,
        which gets mapped to the planDocument attribute.
        It is then temporarily stored and referenced in the existing plan.

        Args:
            object (dict): plan
            refText (dict): reference text attributes
            shortName (Union[str, None], optional): document shortname/section type. Defaults to None.
        """
        ref_uuid = self.__create_uuid(
            object["inspireId"]["localId"], str(refText.get("referenzURL"))
        )
        document = {
            "id": ref_uuid,
            "inspireId": {
                "localId": ref_uuid,
                "namespace": self.namespace,
            },
            "legislationCitation": self.voidreasonvalue,
            "regulationText": self.voidreasonvalue,
            "planDocument": self.__add_XP_ExterneReferenz_to_officialDocument(
                ref_uuid, refText, shortName
            ),
        }

        self.__set_VoidReasonValue_fromlist(document, type="OfficialDocument")
        object.setdefault("officialDocument", []).append(ref_uuid)
        object.setdefault("officialDocument_list", []).append(document)

    def __add_XPText_to_officialDocument(
        self,
        object: dict,
        text_id: str,
        text: dict,
        abschnitt_type: Literal["texte", "begruendungsTexte"],
    ) -> None:
        """Maps XP_Text attribute to corresponding attribute of officialDocument and references it in SpatialPlan.

        A new officialDocument is created, with emphasis on the XP_Text class
        Textual conternt gets mapped onto regulation text, while additional
        information gets mapped onto planDocument, with the distinction made between
        the section types Textabschnitt and BegruendungAbschnitt.
        The document is then temporarily stored and referenced in the existing plan.

        Args:
            object (dict): plan
            text_id (str): id of XP_Text
            text (dict): XP_Text
            abschnitt_type (Literal["texte", "begruendungsTexte"]): section type
        """
        ref_uuid = self.__create_uuid(object["inspireId"]["localId"], text_id)

        document = {
            "id": ref_uuid,
            "inspireId": {
                "localId": ref_uuid,
                "namespace": self.namespace,
            },
            "legislationCitation": self.voidreasonvalue,
            "regulationText": text.get("text", self.voidreasonvalue),  # text_id,
            "planDocument": self.voidreasonvalue,
        }

        if text.get("refText", None):
            if abschnitt_type == "texte":
                document["planDocument"] = (
                    self.__add_XP_ExterneReferenz_to_officialDocument(
                        ref_uuid, dict(text.get("refText")), shortName="Textabschnitt"
                    )
                )
            if abschnitt_type == "begruendungsTexte":
                document["planDocument"] = (
                    self.__add_XP_ExterneReferenz_to_officialDocument(
                        ref_uuid,
                        dict(text.get("refText")),
                        shortName="BegruendungAbschnitt",
                    )
                )

        self.__set_VoidReasonValue_fromlist(document, type="OfficialDocument")
        object.setdefault("officialDocument", []).append(ref_uuid)
        object.setdefault("officialDocument_list", []).append(document)

    def __add_XP_SpezExterneReferenz_to_officialDocument(
        self, object: dict, attr: dict
    ) -> None:
        """Maps XP_SpezExterneReferenz to DocumentCitation attribute of officialDocument and references it in SpatialPlan.

        A new officialDocument is created, with emphasis on the XP_SpezExterneReferenz class,
        which gets mapped to the planDocument attribute.
        The document is then temporarily stored and referenced in the existing plan.

        Args:
            object (dict): plan
            attr (dict): XP_SpezExterneReferenz
        """
        ref_uuid = self.__create_uuid(
            object["inspireId"]["localId"], attr.get("referenzURL")
        )

        link_list = []
        for link in ["georefURL", "referenzURL"]:
            if attr.get(link, None):
                link_list.append(attr.get(link))

        date = (
            {
                "date": attr.get("datum", None),
                "dateType": "https://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#CI_DateTypeCode_creation",
            }
            if attr.get("datum")
            else self.voidreasonvalue
        )

        document = {
            "id": ref_uuid,
            "inspireId": {
                "localId": ref_uuid,
                "namespace": self.namespace,
            },
            "legislationCitation": self.voidreasonvalue,
            "regulationText": self.voidreasonvalue,
            "planDocument": {
                "id": f"{ref_uuid}.0",
                "link": link_list if link_list else self.voidreasonvalue,
                "name": attr.get("referenzName"),
                "date": date,
                "shortName": attr.get("typ"),
            },
        }
        self.__set_VoidReasonValue_fromlist(document, type="OfficialDocument")
        object.setdefault("officialDocument", []).append(ref_uuid)
        object.setdefault("officialDocument_list", []).append(document)

    def __set_LegislationCitation(
        self,
        object: dict,
        attr: dict | str,
        level: Literal["national", "sub-national"],
    ) -> None:
        """Maps plan attribute onto LegislationCitation attribute of officialDocument and references it in SpatialPlan.

        A new officialDocument is created, with emphasis on data that gets
        mapped to the legislationCitation attribute, given a legislation level.
        The document is then temporarily stored and referenced in the existing plan.

        Args:
            object (dict): plan
            attr (dict): attribute
            level (Literal["national", "sub): legislation level
        """
        level_ref = {
            "national": "https://inspire.ec.europa.eu/codelist/LegislationLevelValue/national",
            "sub-national": "https://inspire.ec.europa.eu/codelist/LegislationLevelValue/sub-national",
        }
        date_check = isinstance(attr, str)
        ref_uuid = self.__create_uuid(
            object["inspireId"]["localId"],
            attr if date_check else attr.get("name"),
        )

        date = (
            {
                "date": attr if date_check else attr.get("datum", None),
                "dateType": "https://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#CI_DateTypeCode_creation",
            }
            if date_check or attr.get("datum")
            else self.voidreasonvalue
        )

        document = {
            "id": ref_uuid,
            "inspireId": {
                "localId": ref_uuid,
                "namespace": self.namespace,
            },
            "legislationCitation": {
                "id": f"{ref_uuid}.0",
                "date": date,
                "name": attr if date_check else attr.get("name"),
                "level": level_ref[level],
                "link": self.voidreasonvalue,
            },
            "regulationText": self.voidreasonvalue,
            "planDocument": self.voidreasonvalue,
        }
        self.__set_VoidReasonValue_fromlist(document, type="OfficialDocument")
        object.setdefault("officialDocument", []).append(ref_uuid)
        object.setdefault("officialDocument_list", []).append(document)

    def __set_AwareDatetime(self, date_str: str) -> AwareDatetime:
        """Convert datetime string to AwareDatetime object.

        This is needed for the validation of certain attributes to pass.

        Args:
            date_str (str): date of certain attribute

        Returns:
            AwareDatetime: converted date
        """
        date_object = datetime.strptime(date_str, "%Y-%m-%d")
        timezone = pytz.timezone("Europe/Berlin")

        return timezone.localize(datetime.combine(date_object, datetime.min.time()))

    def __set_ordinanceDate(self, object: dict, attr: str) -> None:
        """Maps datetimes in XP_Plan to attribute ordinanceDate in SpatialPlan.

        ordinanceDate is a list of dates and corresponding references.
        If none exists, a new list is created, otherwise attributes get appended
        to the existing list.

        Args:
            object (dict): plan
            attr (str): datetime attribute
        """
        if isinstance(object.get(attr), list):
            for list_elem in object.get(attr):
                object.setdefault("ordinance", []).append(
                    {
                        "ordinanceDate": self.__set_AwareDatetime(
                            list_elem
                        ).isoformat(),
                        "ordinanceReference": attr,
                    }
                )
            object.pop(attr)
        else:
            if object.get(attr, None):
                object.setdefault("ordinance", []).append(
                    {
                        "ordinanceDate": self.__set_AwareDatetime(
                            object.pop(attr)
                        ).isoformat(),
                        "ordinanceReference": attr,
                    }
                )

    def __set_VoidReasonValue_fromlist(
        self,
        object: dict,
        type: Literal[
            "SpatialPlan",
            "OfficialDocument",
            "SupplementaryRegulation",
            "ZoningElement",
        ] = "SpatialPlan",
    ) -> None:
        r"""Sets and polulates voidable attributes for.

        - SpatialPlan \n
        - OfficialDocument \n
        - SupplementaryRegulation \n
        - ZoningElement \n
        that are not or can't be mapped from XPlan.

        In addition, it checks if certain attributes exist
        that are mapped but are empty, i.e. set to None.

        Args:
            object (dict): plan
            type (Literal[ "SpatialPlan", "OfficialDocument", "SupplementaryRegulation", "ZoningElement", ], optional): Specification for the concrete PLU object. Defaults to "SpatialPlan".
        """
        match type:
            case "SpatialPlan":
                attr_nil = [
                    "beginLifespanVersion",
                    "endLifespanVersion",
                    "validFrom",
                    "validTo",
                    "alternativeTitle",
                    "processStepGeneral",
                    "backgroundMap",
                    "ordinance",
                    "officialDocument",
                ]
            case "OfficialDocument":
                attr_nil = [
                    "legislationCitation",
                    "regulationText",
                    "planDocument",
                ]
            case "SupplementaryRegulation":
                attr_nil = [
                    "validFrom",
                    "validTo",
                    "dimensioningIndication",
                    "specificSupplementaryRegulation",
                    "processStepGeneral",
                    "backgroundMap",
                    "beginLifespanVersion",
                    "endLifespanVersion",
                    "inheritedFromOtherPlans",
                    "specificRegulationNature",
                    "name",
                    "officialDocument",
                ]
            case "ZoningElement":
                attr_nil = [
                    "validFrom",
                    "validTo",
                    "beginLifespanVersion",
                    "specificLandUse",
                    "endLifespanVersion",
                    "processStepGeneral",
                    "backgroundMap",
                    "dimensioningIndication",
                    "officialDocument",
                ]

        for attr in attr_nil:
            if attr not in object.keys() or (
                (attr in object.keys()) and (object[attr] is None)
            ):
                if attr == "processStepGeneral":
                    object[attr] = (
                        "http://inspire.ec.europa.eu/codelist/VoidReasonValue/Unpopulated"
                    )
                else:
                    object[attr] = {
                        "nilReason": "http://inspire.ec.europa.eu/codelist/VoidReasonValue/Unpopulated"
                    }

        if type == "ZoningElement":
            # Die als voidable gekennzeichneten ZoningElement Attribute
            # hilucsPresence und specificPresence müssen
            # folgendermaßen spezifiziert werden
            for attr in ["hilucsPresence", "specificPresence"]:
                object[attr] = {
                    "nilReason": "http://inspire.ec.europa.eu/codelist/VoidReasonValue/Unknown"
                }

    # TODO: still used for some tests
    def __set_VoidReasonValue_for_OfficialDocumenntation(self, object) -> None:
        """Safety function.

        In case certain attributes exist that are mapped onto OfficialDocumentation
        but are empty, i.e. set to None
        """
        attr_nil = [
            "legislationCitation",
            "regulationText",
            "planDocument",
        ]

        for attr in attr_nil:
            if (attr not in object.keys()) | (
                (attr in object.keys()) and (object[attr] is None)
            ):
                object[attr] = {
                    "nilReason": "http://inspire.ec.europa.eu/codelist/VoidReasonValue/Unpopulated"
                }

    def __xpobject_decision_rule(self, object: dict) -> None:
        """Decision Rule for mapping XP_Object on either ZoningElement or SupplementaryRegulation.

        A temporary attribute mapping is created which in turn, contains
        the XPlan attributes ebene and flaechenschluss from which
        the output class is derived

        Args:
            object (dict): plan containing the temporary mapping attribute
        """
        if object.get("mapping")["flaechenschluss"] and (
            float(object.get("mapping")["ebene"]) == 0.0
        ):
            object["featuretype"] = "ZoningElement"
        else:
            object["featuretype"] = "SupplementaryRegulation"

    def __get_nested_attribute(self, object: dict, attr: str) -> Union[dict, str, None]:
        """Get the value of a nested attribute specified by a dot-separated string.

        Helper function for setting the attributes supplementaryRegulation
        and specificSupplementaryRegulation of the class
        SupplementaryRegulation and respectively hilucsLandUse and
        specificLandUse of class ZoningElement, based on mapping tables.
        For each specific XPlan class, the required attribute for the
        mapping varies: some require a nested attribute, which - if present -
        gets identified by the logic of this method in a recursive way
        and its value is returned.

        Args:
            object (dict): plan
            attr (str): possible nested attribute name, dot-separated

        Returns:
            Union[dict, str, None]: value of the inner-most attribute
        """
        filter_attr = (
            [attr_list[0], attr_list[2]]
            if len(attr_list := attr.split(".")) == 3
            else [attr_list[0]]
        )

        for key in filter_attr:
            if isinstance(object, dict):
                object = object.get(key)
                if isinstance(object, list):
                    if isinstance(object[0], dict):
                        object = next(iter(object[0].values()))
            if object is None:
                break
        return object

    def __set_supplementaryRegulation(self, object: dict) -> None:
        """Sets the attributes supplementaryRegulation and specificSupplementaryRegulation.

        Based on the mapping table for the specific XPlan object during mapping
        onto the class SupplementaryRegulation

        The attributes are mapped, based on individual code lists for each XPlan class.

        Args:
            object (dict): plan
        """
        codelist_supplementaryR = (
            "https://inspire.ec.europa.eu/codelist/SupplementaryRegulationValue/"
        )
        codelist_specificSR = (
            "https://registry.gdi-de.org/codelist/de.xleitstelle.inspire_plu/LandUse/"
        )

        df_filter = object.get("mapping_table_SR")
        if len(df_attr_list := df_filter[["XPlanungAttribut"]].dropna()) == 0:
            object["supplementaryRegulation"] = (
                codelist_supplementaryR + df_filter.iloc[[0]]["supplementaryRegulation"]
            ).to_list()
            object["specificSupplementaryRegulation"] = (
                codelist_specificSR
                + df_filter.iloc[[0]]["specificSupplementaryRegulation"]
            ).to_list()
        else:
            object["supplementaryRegulation"] = []
            object["specificSupplementaryRegulation"] = []
            found_non_none_value = False
            # first, check for multiple attributes and iterate through them
            for attr in df_attr_list["XPlanungAttribut"].unique():
                attr_value = self.__get_nested_attribute(object, attr)

                if attr_value:
                    found_non_none_value = True
                    if isinstance(object.get(attr), list):
                        condition = (df_filter["XPlanungAttribut"] == attr) & (
                            df_filter["Code"].isin(attr_value)
                        )
                    else:
                        condition = (df_filter["XPlanungAttribut"] == attr) & (
                            df_filter["Code"] == attr_value
                        )
                    object["supplementaryRegulation"] += (
                        codelist_supplementaryR
                        + df_filter.loc[condition, "supplementaryRegulation"]
                    ).to_list()
                    object["specificSupplementaryRegulation"] += (
                        codelist_specificSR
                        + df_filter.loc[condition, "specificSupplementaryRegulation"]
                    ).to_list()
                    # check if code is not present in mapping list
                    if (~condition).all():
                        found_non_none_value = False
            # default case, if no attribute is set at all
            if not found_non_none_value:
                logger.warning(
                    f"No attribute or matching code found for mapping onto supplementaryRegulation and specificSupplementaryRegulation for object {object.get('id', 'unknown')}: set default values"
                )
                object["supplementaryRegulation"] = (
                    codelist_supplementaryR
                    + df_filter.iloc[[0]]["supplementaryRegulation"]
                ).to_list()
                object["specificSupplementaryRegulation"] = (
                    codelist_specificSR
                    + df_filter.iloc[[0]]["specificSupplementaryRegulation"]
                ).to_list()

    def __set_hilucsLandUse(self, object: dict) -> None:
        """Sets the attributes hilucsLandUse and specificLandUse.

        Based on the mapping table for the specific XPlan objectSets during mapping
        onto the class ZoningElement

        The attributes are mapped, based on individual code lists for each XPlan class.

        Args:
            object (dict): plan
        """
        codelist_HILUCS = "https://inspire.ec.europa.eu/codelist/HILUCSValue/"
        codelist_LandUse = (
            "https://registry.gdi-de.org/codelist/de.xleitstelle.inspire_plu/LandUse/"
        )

        df_filter = object.get("mapping_table_ZE")
        if len(df_attr_list := df_filter[["XPlanungAttribut"]].dropna()) == 0:
            object["hilucsLandUse"] = (
                codelist_HILUCS + df_filter.iloc[[0]]["hilucsLandUse"]
            ).to_list()
            object["specificLandUse"] = (
                codelist_LandUse + df_filter.iloc[[0]]["specificLandUse"]
            ).to_list()
        else:
            object["hilucsLandUse"] = []
            object["specificLandUse"] = []
            found_non_none_value = False
            # first, check for multiple attributes and iterate through them
            for attr in df_attr_list["XPlanungAttribut"].unique():
                attr_value = self.__get_nested_attribute(object, attr)

                if attr_value:
                    found_non_none_value = True
                    if isinstance(object.get(attr), list):
                        condition = (df_filter["XPlanungAttribut"] == attr) & (
                            df_filter["Code"].isin(attr_value)
                        )
                    else:
                        condition = (df_filter["XPlanungAttribut"] == attr) & (
                            df_filter["Code"] == attr_value
                        )
                    object["hilucsLandUse"] += (
                        codelist_HILUCS + df_filter.loc[condition, "hilucsLandUse"]
                    ).to_list()
                    object["specificLandUse"] += (
                        codelist_LandUse + df_filter.loc[condition, "specificLandUse"]
                    ).to_list()
                    # check if code is not present in mapping list
                    if (~condition).all():
                        found_non_none_value = False
            # default case, if no attribute is set at all
            if not found_non_none_value:
                logger.warning(
                    f"No attribute or matching code found for mapping onto supplementaryRegulation and specificSupplementaryRegulation for object {object.get('id', 'unknown')}: set default values"
                )
                object["hilucsLandUse"] = (
                    codelist_HILUCS + df_filter.iloc[[0]]["hilucsLandUse"]
                ).to_list()
                object["specificLandUse"] = (
                    codelist_LandUse + df_filter.iloc[[0]]["specificLandUse"]
                ).to_list()

    def __wrapper_set_based_on_decision_rule(self, object: dict) -> None:
        """Maps the class specific attributes for SupplementaryRegulation and ZoningElement.

        Based on the temporary attribute mapping, which
        in turn contains, the mapping logic

        Args:
            object (dict): plan, containing the temporary attribute mapping
        """
        if object["featuretype"] == "SupplementaryRegulation":
            self.__set_supplementaryRegulation(object)
        if object["featuretype"] == "ZoningElement":
            self.__set_hilucsLandUse(object)

    # TODO: write tests
    def __set_dimensioningIndication_for_bpfestsetzungenbaugebiet(
        self,
        object: dict,
        list_int: list = [
            "MaxAnzahlWohnungen",
            "Zmin",
            "Zmax",
            "Zzwingend",
            "Z",
            "Z_Ausn",
            "Z_Staffel",
            "Z_Dach",
            "Zumin",
            "Zumax",
            "Zuzwingend",
            "ZU",
            "ZU_Ausn",
        ],
        list_real: list = [
            "GFZmin",
            "GFZmax",
            "GFZ",
            "GFZ_Ausn",
            "BMZ",
            "BMZ_Ausn",
            "GRZmin",
            "GRZmax",
            "GRZ",
            "GRZ_Ausn",
        ],
        list_measure: list = [
            ("MinGRWohneinheit", "m2"),
            ("Fmin", "m2"),
            ("Fmax", "m2"),
            ("Bmin", "m"),
            ("Bmax", "m"),
            ("Tmin", "m"),
            ("Tmax", "m"),
            ("Gfmin", "m2"),
            ("Gfmax", "m2"),
            ("GF", "m2"),
            ("GF_Ausn", "m2"),
            ("BM", "m3"),
            ("BM_Ausn", "m3"),
            ("Grmin", "m2"),
            ("Grmax", "m2"),
            ("GR", "m2"),
            ("GR_Ausn", "m2"),
        ],
    ) -> None:
        r"""Maps attributes, used in specifications on the extent of building use, to dimensioningIndication.

        The attributes aggregated in the data type
        BP_FestsetzungenBaugebiet are used in the
        following XPlanung classes: \n
        - BP_BaugebietsTeilFlaeche \n
        - BP_BesondererNutzungszweckFlaeche \n
        - BP_UeberbaubareGrundstuecksFlaeche \n
        - BP_GemeinbedarfFlaeche \n
        - BP_SpielSportanlagenFlaeche \n
        - BP_GruenFlaeche \n
        - BP_VerEntsorgung \n
        - SO_Strassenverkehr \n

        Args:
            object (dict): plan
            list_int (list, optional): List of possible integer attributes. Defaults to [ "MaxAnzahlWohnungen", "Zmin", "Zmax", "Zzwingend", "Z", "Z_Ausn", "Z_Staffel", "Z_Dach", "Zumin", "Zumax", "Zuzwingend", "ZU", "ZU_Ausn", ].
            list_real (list, optional): List of possible float attributes. Defaults to [ "GFZmin", "GFZmax", "GFZ", "GFZ_Ausn", "BMZ", "BMZ_Ausn", "GRZmin", "GRZmax", "GRZ", "GRZ_Ausn", ].
            list_measure (list, optional): List of pssible measure attributes. Defaults to [ ("MinGRWohneinheit", "m2"), ("Fmin", "m2"), ("Fmax", "m2"), ("Bmin", "m"), ("Bmax", "m"), ("Tmin", "m"), ("Tmax", "m"), ("Gfmin", "m2"), ("Gfmax", "m2"), ("GF", "m2"), ("GF_Ausn", "m2"), ("BM", "m3"), ("BM_Ausn", "m3"), ("Grmin", "m2"), ("Grmax", "m2"), ("GR", "m2"), ("GR_Ausn", "m2"), ].
        """
        object.setdefault("dimensioningIndication", [])
        if isinstance(object.get("dimensioningIndication"), type(self.voidreasonvalue)):
            object["dimensioningIndication"] = []

        for l_int in list_int:
            if object.get(l_int, None):
                object.get("dimensioningIndication").append(
                    {
                        "indicationReference": l_int,
                        "value": int(object.get(l_int)),
                    }
                )
                object.pop(l_int)
        for l_real in list_real:
            if object.get(l_real, None):
                object.get("dimensioningIndication").append(
                    {
                        "indicationReference": l_real,
                        "value": float(object.get(l_real)),
                    }
                )
                object.pop(l_real)
        for l_measure in list_measure:
            if object.get(l_measure, None):
                object.get("dimensioningIndication").append(
                    {
                        "indicationReference": l_measure[0],
                        "value": {
                            "uom": l_measure[1],
                            "value": float(object.get(l_measure)),
                        },
                    }
                )
                object.pop(l_measure)

        if not object["dimensioningIndication"]:
            object["dimensioningIndication"] = {
                "nilReason": "http://inspire.ec.europa.eu/codelist/VoidReasonValue/Unpopulated"
            }

    # TODO: write tests
    def __set_dimensioningIndication_for_bpgestaltungbaugebiet(
        self,
        object: dict,
        list_measure: list = [
            ("dachgestaltung.DNmin", "deg"),
            ("dachgestaltung.DNmax", "deg"),
            ("dachgestaltung.DN ", "deg"),
            ("dachgestaltung.DNZwingend ", "deg"),
            ("FR", "deg"),
        ],
        mapping_dachform: dict = {
            "1000": ("Flachdach", "Dachform"),
            "2100": ("Pultdach", "Dachform"),
            "2200": ("VersetztesPultdach", "Dachform"),
            "3000": ("GeneigtesDach", "Dachform"),
            "3100": ("Satteldach", "Dachform"),
            "3200": ("Walmdach", "Dachform"),
            "3300": ("Krueppelwalmdach", "Dachform"),
            "3400": ("Mansardendach", "Dachform"),
            "3500": ("Zeltdach", "Dachform"),
            "3600": ("Kegeldach", "Dachform"),
            "3700": ("Kuppeldach", "Dachform"),
            "3800": ("Sheddach", "Dachform"),
            "3900": ("Bogendach", "Dachform"),
            "4000": ("Turmdach", "Dachform"),
            "4100": ("Tonnendach", "Dachform"),
            "5000": ("Mischform", "Dachform"),
            "9999": ("Sonstiges", "Dachform"),
        },
        mapping_ausschlussDachform: dict = {
            "1000": ("Flachdach", "AusschlussDachform"),
            "2100": ("Pultdach", "AusschlussDachform"),
            "2200": ("VersetztesPultdach", "AusschlussDachform"),
            "3000": ("GeneigtesDach", "AusschlussDachform"),
            "3100": ("Satteldach", "AusschlussDachform"),
            "3200": ("Walmdach", "AusschlussDachform"),
            "3300": ("Krueppelwalmdach", "AusschlussDachform"),
            "3400": ("Mansardendach", "AusschlussDachform"),
            "3500": ("Zeltdach", "AusschlussDachform"),
            "3600": ("Kegeldach", "AusschlussDachform"),
            "3700": ("Kuppeldach", "AusschlussDachform"),
            "3800": ("Sheddach", "AusschlussDachform"),
            "3900": ("Bogendach", "AusschlussDachform"),
            "4000": ("Turmdach", "AusschlussDachform"),
            "4100": ("Tonnendach", "AusschlussDachform"),
            "5000": ("Mischform", "AusschlussDachform"),
            "9999": ("Sonstiges", "AusschlussDachform"),
        },
    ) -> None:
        r"""Maps attributes, used in specifications on the extent of building use, to dimensioningIndication.

        The attributes aggregated in the data type
        BP_GestaltungBaugebiet are used in the
        following XPlanung classes:
        - BP_BaugebietsTeilFlaeche \n
        - BP_BesondererNutzungszweckFlaeche \n
        - BP_UeberbaubareGrundstuecksFlaeche \n
        - BP_GemeinbedarfsFlaeche \n

        Args:
            object (dict): plan
            list_measure (list, optional): List of possible measure attributes. Defaults to [ ("dachgestaltung.DNmin", "deg"), ("dachgestaltung.DNmax", "deg"), ("dachgestaltung.DN ", "deg"), ("dachgestaltung.DNZwingend ", "deg"), ("FR", "deg"), ].
            mapping_dachform (_type_, optional): Dictionary for mapping the dachgestaltung attribute. Defaults to { "1000": ("Flachdach", "Dachform"), "2100": ("Pultdach", "Dachform"), "2200": ("VersetztesPultdach", "Dachform"), "3000": ("GeneigtesDach", "Dachform"), "3100": ("Satteldach", "Dachform"), "3200": ("Walmdach", "Dachform"), "3300": ("Krueppelwalmdach", "Dachform"), "3400": ("Mansardendach", "Dachform"), "3500": ("Zeltdach", "Dachform"), "3600": ("Kegeldach", "Dachform"), "3700": ("Kuppeldach", "Dachform"), "3800": ("Sheddach", "Dachform"), "3900": ("Bogendach", "Dachform"), "4000": ("Turmdach", "Dachform"), "4100": ("Tonnendach", "Dachform"), "5000": ("Mischform", "Dachform"), "9999": ("Sonstiges", "Dachform"), }.
            mapping_ausschlussDachform (_type_, optional): Dictionary for mapping the dachgestaltung attribute. Defaults to { "1000": ("Flachdach", "AusschlussDachform"), "2100": ("Pultdach", "AusschlussDachform"), "2200": ("VersetztesPultdach", "AusschlussDachform"), "3000": ("GeneigtesDach", "AusschlussDachform"), "3100": ("Satteldach", "AusschlussDachform"), "3200": ("Walmdach", "AusschlussDachform"), "3300": ("Krueppelwalmdach", "AusschlussDachform"), "3400": ("Mansardendach", "AusschlussDachform"), "3500": ("Zeltdach", "AusschlussDachform"), "3600": ("Kegeldach", "AusschlussDachform"), "3700": ("Kuppeldach", "AusschlussDachform"), "3800": ("Sheddach", "AusschlussDachform"), "3900": ("Bogendach", "AusschlussDachform"), "4000": ("Turmdach", "AusschlussDachform"), "4100": ("Tonnendach", "AusschlussDachform"), "5000": ("Mischform", "AusschlussDachform"), "9999": ("Sonstiges", "AusschlussDachform"), }.
        """
        object.setdefault("dimensioningIndication", [])
        if isinstance(object.get("dimensioningIndication"), type(self.voidreasonvalue)):
            object["dimensioningIndication"] = []

        for l_measure in list_measure:
            if len(l_mn := l_measure[0].split(".")) > 1:
                # i.e. dachgestaltung.DNmin
                if object.get(l_mn[0], None):
                    if attr := object[l_mn[0]][0].get("DN"):
                        object.get("dimensioningIndication").append(
                            {
                                "indicationReference": l_measure[0].split(".")[1],
                                "value": {
                                    "uom": l_measure[1],
                                    "value": float(attr.get("value")),
                                },
                            }
                        )
                    # remove dachgestaltung in the last if statement

            else:
                if object.get(l_measure, None):
                    object.get("dimensioningIndication").append(
                        {
                            "indicationReference": l_measure[0],
                            "value": {
                                "uom": l_measure[1],
                                "value": float(object.get(l_measure)),
                            },
                        }
                    )
                    object.pop(l_measure)

        if object.get("dachgestaltung", None):
            for dachgestaltung_obj in object.get("dachgestaltung"):
                if dach_obj := dict(dachgestaltung_obj).get("dachform", None):
                    if isinstance(dach_obj, list):
                        for dach in dach_obj:
                            dimInd = mapping_dachform[dach]
                            object.get("dimensioningIndication").append(
                                {
                                    "indicationReference": dimInd[1],
                                    "value": dimInd[0],
                                }
                            )
                    else:
                        dimInd = mapping_dachform[dach_obj]
                        object.get("dimensioningIndication").append(
                            {
                                "indicationReference": dimInd[1],
                                "value": dimInd[0],
                            }
                        )
                if dach_obj := dict(dachgestaltung_obj).get("ausschlussDachform", None):
                    dimInd = mapping_ausschlussDachform[dach_obj]
                    object.get("dimensioningIndication").append(
                        {
                            "indicationReference": dimInd[1],
                            "value": dimInd[0],
                        }
                    )
            object.pop("dachgestaltung", None)

        if not object["dimensioningIndication"]:
            object["dimensioningIndication"] = {
                "nilReason": "http://inspire.ec.europa.eu/codelist/VoidReasonValue/Unpopulated"
            }

    # TODO: write tests
    def __set_dimensioningIndication_for_BP_ZusaetzlicheFestsetzungen(
        self,
        object: dict,
        list_int: list = ["Zwohn"],
        list_measure: list = [
            ("GFAntWohnen", "scale"),
            ("GFWohnen", "m2"),
            ("GFAntGewerbe", "scale"),
            ("GFGewerbe", "m2"),
            ("VF", "m2"),
        ],
        dict_enum: dict = {
            "1000": ("Zulaessig", "wohnnutzungEGStrasse"),
            "2000": ("NichtZulaessig", "wohnnutzungEGStrasse"),
            "3000": ("Ausnahmsweise", "wohnnutzungEGStrasse"),
        },
    ) -> None:
        r"""The attributes aggregated in the data type BP_ZusaetzlicheFestsetzungen are used in the following XPlanung classes.

        - BP_BaugebietsTeilFlaeche \n
        - BP_UeberbaubareGrundstuecksFlaeche \n
        and get mapped onto dimensioningIndication \n.

        Args:
            object (dict): plan
            list_int (list, optional): List of possible integer attributes. Defaults to ["Zwohn"].
            list_measure (list, optional): List of possible measure attributes. Defaults to [ ("GFAntWohnen", "scale"), ("GFWohnen", "m2"), ("GFAntGewerbe", "scale"), ("GFGewerbe", "m2"), ("VF", "m2"), ].
            dict_enum (_type_, optional): Dictionary for mapping of wohnnutzungEGStrasse attribute. Defaults to { "1000": ("Zulaessig", "wohnnutzungEGStrasse"), "2000": ("NichtZulaessig", "wohnnutzungEGStrasse"), "3000": ("Ausnahmsweise", "wohnnutzungEGStrasse"), }.
        """
        object.setdefault("dimensioningIndication", [])
        if isinstance(object.get("dimensioningIndication"), type(self.voidreasonvalue)):
            object["dimensioningIndication"] = []

        for l_int in list_int:
            if object.get(l_int, None):
                object.get("dimensioningIndication").append(
                    {
                        "indicationReference": l_int,
                        "value": int(object.get(l_int)),
                    }
                )
                object.pop(l_int)

        for l_measure in list_measure:
            if object.get(l_measure, None):
                object.get("dimensioningIndication").append(
                    {
                        "indicationReference": l_measure[0],
                        "value": {
                            "uom": l_measure[1],
                            "value": float(object.get(l_measure)),
                        },
                    }
                )
                object.pop(l_measure)

        if object.get("wohnnutzungEGStrasse", None):
            object.get("dimensioningIndication").append(
                {
                    "indicationReference": dict_enum[
                        object.get("wohnnutzungEGStrasse")
                    ][1],
                    "value": dict_enum[object.get("wohnnutzungEGStrasse")][0],
                }
            )
            object.pop("wohnnutzungEGStrasse")

    # TODO: write tests
    def __set_dimensioningIndication_for_miscellaneous(
        self,
        object: dict,
        dict_bauweise: dict = {
            "1000": ("OffeneBauweise", "Bauweise"),
            "2000": ("Geschlossene", "Bauweise"),
            "3000": ("Abweichende", "Bauweise"),
        },
        dict_bebauungsArt: dict = {
            "1000": ("Einzelhaeuser", "BebauungsArt"),
            "2000": ("Doppelhaeuser", "BebauungsArt"),
            "3000": ("Hausgruppen", "BebauungsArt"),
            "4000": ("EinzelDoppelhaeuser", "BebauungsArt"),
            "5000": ("Einzelhaeuser", "BebauungsArt"),
            "6000": ("Doppelhaeuser", "BebauungsArt"),
            "7000": ("Reihenhaeuser", "BebauungsArt"),
        },
    ) -> None:
        r"""Sets miscellaneous attributes.

        Used in the following XPlanung classes: \n
        - BP_BaugebietsTeilFlaeche \n
        - BP_UeberbaubareGrundstuecksFlaeche \n
        - BP_BesondererNutzungszweckFlaeche \n
        - BP_GemeinbedarfFlaeche \n
        - BP_WohngebaeudeFlaeche \n
        and get mapped onto dimensioningIndication \n

        Args:
            object (dict): plan
            dict_bauweise (_type_, optional): dictionary for mapping bauweise attribute. Defaults to { "1000": ("OffeneBauweise", "Bauweise"), "2000": ("Geschlossene", "Bauweise"), "3000": ("Abweichende", "Bauweise"), }.
            dict_bebauungsArt (_type_, optional): dicitionary for mapping bebauungsArt attribute. Defaults to { "1000": ("Einzelhaeuser", "BebauungsArt"), "2000": ("Doppelhaeuser", "BebauungsArt"), "3000": ("Hausgruppen", "BebauungsArt"), "4000": ("EinzelDoppelhaeuser", "BebauungsArt"), "5000": ("Einzelhaeuser", "BebauungsArt"), "6000": ("Doppelhaeuser", "BebauungsArt"), "7000": ("Reihenhaeuser", "BebauungsArt"), }.
        """
        object.setdefault("dimensioningIndication", [])
        if isinstance(object.get("dimensioningIndication"), type(self.voidreasonvalue)):
            object["dimensioningIndication"] = []

        if object.get("bauweise", None):
            object.get("dimensioningIndication").append(
                {
                    "indicationReference": dict_bauweise[object.get("bauweise")][1],
                    "value": dict_bauweise[object.get("bauweise")][0],
                }
            )
            object.pop("bauweise")

        if object.get("bebauungsArt", None):
            object.get("dimensioningIndication").append(
                {
                    "indicationReference": dict_bebauungsArt[
                        object.get("bebauungsArt")
                    ][1],
                    "value": dict_bebauungsArt[object.get("bebauungsArt")][0],
                }
            )
            object.pop("bebauungsArt")

        if not object["dimensioningIndication"]:
            object["dimensioningIndication"] = {
                "nilReason": "http://inspire.ec.europa.eu/codelist/VoidReasonValue/Unpopulated"
            }

    # TODO: write tests
    def __set_dimensioningIndication_for_FP_BebauungsFlaeche(
        self, object: dict, list_real: list = ["GFZmin", "GFZmax", "GFZ", "BMZ", "GRZ"]
    ) -> None:
        """Sets miscellaneous attributes.

        Used in the following XPlanung class FP_BebauungsFlaeche that get mapped onto dimensioningIndication

        Args:
            object (dict): plan
            list_real (list, optional): List of possible float attributes. Defaults to ["GFZmin", "GFZmax", "GFZ", "BMZ", "GRZ"].
        """
        object.setdefault("dimensioningIndication", [])
        if isinstance(object.get("dimensioningIndication"), type(self.voidreasonvalue)):
            object["dimensioningIndication"] = []

        for l_real in list_real:
            if object.get(l_real, None):
                object.get("dimensioningIndication").append(
                    {
                        "indicationReference": l_real,
                        "value": float(object.get(l_real)),
                    }
                )
                object.pop(l_real)

        if not object["dimensioningIndication"]:
            object["dimensioningIndication"] = {
                "nilReason": "http://inspire.ec.europa.eu/codelist/VoidReasonValue/Unpopulated"
            }

    def _xptextabschnitt(self, object: dict) -> None:
        """Maps the standalone XP_Textabschnitt onto OfficialDocumentation.

        This method populates the regulationText attribute and planDocument,
        in case of a reference text, marked as Textabschnitt.

        Args:
            object (dict): XP_Textabschnitt
        """
        # voidable attribute
        if object.get("id", None):
            ref_uuid = object.pop("id")
        else:
            ref_uuid = str(uuid.uuid4())

        object["id"] = ref_uuid
        object["inspireId"] = {
            "localId": ref_uuid,
            "namespace": self.namespace,
        }

        object["regulationText"] = object.pop("text", self.voidreasonvalue)

        object.setdefault("legislationCitation", self.voidreasonvalue)
        object.setdefault("planDocument", self.voidreasonvalue)

        if object.get("refText", None):
            object["planDocument"] = self.__add_XP_ExterneReferenz_to_officialDocument(
                ref_uuid, dict(object.get("refText")), shortName="Textabschnitt"
            )

        # temporäre attribute
        object["featuretype"] = "OfficialDocumentation"

    def _xpbegruendungabschnitt(self, object: dict) -> None:
        """Maps the standalone XP_BegruendungAbschnitt onto OfficialDocumentation.

        This method populates the regulationText attribute and planDocument,
        in case of a reference text, marked as Textabschnitt.

        Args:
            object (dict): XP_BegruendungAbschnitt
        """
        # voidable attribute
        if object.get("id", None):
            ref_uuid = object.pop("id")
        else:
            ref_uuid = str(uuid.uuid4())

        object["id"] = ref_uuid
        object["inspireId"] = {
            "localId": ref_uuid,
            "namespace": self.namespace,
        }

        object["regulationText"] = object.pop("text", self.voidreasonvalue)

        object.setdefault("legislationCitation", self.voidreasonvalue)
        object.setdefault("planDocument", self.voidreasonvalue)

        if object.get("refText", None):
            object["planDocument"] = self.__add_XP_ExterneReferenz_to_officialDocument(
                ref_uuid,
                dict(object.get("refText")),
                shortName="BegruendungAbschnitt",
            )

        # temporäre attribute
        object["featuretype"] = "OfficialDocumentation"

    def _xpplan(self, object: dict) -> None:
        r"""Maps attributes of the parent class XP_Plan onto SpatialPlan.

        Gets called, before the plan specific transformations for BP_Plan, FP_Plan,
        RP_Plan and SO_Plan are applied.
        The transformation includes the mappings: \n
        - id to inspireId \n
        - name to officialTitle \n
        - raeumlicherGeltungsbereich to extent \n
        - nummer to alternativeTitle \n
        - technHerstellDatum, genehmigungsDatum to ordinance \n
        - untergangsDatum to validTo \n
        - hatGenerAttribut to ordinance for XP_DatumAttribut and to officialDocumentation for XP_URLAttribut \n
        - externeReferenz to backgroundMap for typ=1040 and to officialDocumentation otherwise \n
        - texte, begruendungsTexte to officialDocumentation \n
        The officialDocument attribute contains the references for the newly created officialDocumentation objects.
        They are listed in the temporary attribute officialDocument_list.

        Args:
            object (dict): plan
        """
        # pflichtattribute
        object["inspireId"] = {
            "localId": object.get("id"),
            "namespace": self.namespace,
        }

        object["officialTitle"] = object.pop("name")

        object["extent"] = object.pop("raeumlicherGeltungsbereich")

        # voidable attribute
        if object.get("nummer", None):
            object["alternativeTitle"] = object.pop("nummer")

        for attr in ["technHerstellDatum", "genehmigungsDatum"]:
            if object.get(attr, None):
                if object.get(attr) is not None:
                    self.__set_ordinanceDate(object, attr)

        if object.get("untergangsDatum", None):
            object["validTo"] = object.pop("untergangsDatum")

        if object.get("hatGenerAttribut", None):
            for attr in object["hatGenerAttribut"]:
                if self.__validate_model("XPDatumAttribut", attr):
                    # if isinstance(attr, XPDatumAttribut):
                    object.setdefault("ordinance", []).append(
                        {
                            "ordinanceDate": self.__set_AwareDatetime(attr.get("wert")),
                            "ordinanceReference": attr.get("name"),
                        }
                    )
                if self.__validate_model("XPURLAttribut", attr):
                    # if isinstance(attr, XPURLAttribut):
                    self.__add_XPURL_to_officialDocument(object, attr)
            object.pop("hatGenerAttribut")

        if object.get("externeReferenz", None):
            for attr in object.get("externeReferenz"):
                if attr.get("typ") == "1040":
                    object["backgroundMap"] = {
                        "backgroundMapReference": attr.get("referenzName"),
                        "backgroundMapURI": attr.get(
                            "referenzURL",
                            {
                                "nilReason": "http://inspire.ec.europa.eu/codelist/VoidReasonValue/Unpopulated"
                            },
                        ),
                        "backgroundMapDate": self.__set_AwareDatetime(
                            attr.get("datum")
                        ),
                    }

                else:
                    self.__add_XP_SpezExterneReferenz_to_officialDocument(object, attr)
            object.pop("externeReferenz")

        for attr in ["texte", "begruendungsTexte"]:
            if object.get(attr, None):
                for text_id in object.get(attr):
                    text = dict(self.collection.features[text_id])
                    self.__add_XPText_to_officialDocument(
                        object, text_id, text, abschnitt_type=attr
                    )
                object.pop(attr)

        # temporäre attribute
        object["featuretype"] = "SpatialPlan"

    def _xpbereich(self, object: dict) -> None:
        """Applies transformation for parent class XP_Bereich.

        There are no INSPIRE objects equivalent to XP_Bereich
        The specific classes BP_Bereich, FP_Bereich, RP_Bereich
        and SO_Bereich are considered in their respective plan
        mappings

        Args:
            object (dict): XP_Bereich
        """
        object.clear()

    def _bpplan(self, object: dict) -> None:
        r"""Maps attributes of the specific class BP_Plan onto SpatialPlan.

        This mapping is applied in succesion to _xpplan, i.e.

        Example:
            _xpplan(object) \n
            _bpplan(object) \n

        The transformation includes the mappings: \n
        - planArt to levelOfSpatialPlan and planTypeName \n
        - rechtsstand to processStepGeneral \n
        - aenderungenBisDatum, aufstellungsbeschlussDatum, auslegungsStartDatum, auslegungsEndDatum, traegerbeteiligungsStartDatum, traegerbeteiligungsEndDatum, satzungsbeschlussDatum, rechtsverordnungsDatum, ausfertigungsDatum, fruehzeitigeOeffentlichkeitsbeteiligungsStartDatum, fruehzeitigeOeffentlichkeitsbeteiligungsEndDatum, fruehzeitigeTraegerbeteiligungsStartDatum, fruehzeitigeTraegerbeteiligungsEndDatum to ordinance \n
        - inkrafttretensDatum to validFrom \n
        - versionBauNVO, versionBauGB to LegislationCitation in OfficialDocumentation \n
        - attributes of referenced BP_Bereich objects, namely: refScan and texte to OfficialDocumentation \n
        The officialDocument attribute contains the references for the newly created officialDocumentation objects.
        They are listed in the temporary attribute officialDocument_list.

        Args:
            object (dict): plan
        """
        # pflichtattribute

        # Da die INSPIRE Attribute planTypeName und levelOfSpatialPlan nur einmal belegt werden können, sollte das
        # XPlanung-Attribut planArt auch nur einmal belegt werden. Ansonsten wird nur der erste spezifizierte Attributwert
        # von planArt in das INSPIRE Dokument übernommen
        planArt = object.pop("planArt")[0]

        plantypenamevalue_codespace = "https://registry.gdi-de.org/codelist/de.xleitstelle.inspire_plu/PlanTypeNameValue#"

        planArt_mapping = {
            "1000": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/infraLocal",
                plantypenamevalue_codespace + "6_Bebauungsplan",
            ],
            "10000": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/infraLocal",
                plantypenamevalue_codespace + "6_3_EinfacherBPlan",
            ],
            "10001": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/infraLocal",
                plantypenamevalue_codespace + "6_1_QualifizierterBPlan",
            ],
            "10002": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/infraLocal",
                plantypenamevalue_codespace + "6_6_BebauungsplanZurWohnraumversorgung",
            ],
            "3000": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/infraLocal",
                plantypenamevalue_codespace + "6_2_VorhabenbezogenerBPlan",
            ],
            "3100": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/infraLocal",
                plantypenamevalue_codespace + "6_5_VorhabenUndErschliessungsplan",
            ],
            "4000": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/infraLocal",
                plantypenamevalue_codespace + "7_InnenbereichsSatzung",
            ],
            "40000": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/infraLocal",
                plantypenamevalue_codespace + "7_1_KlarstellungsSatzung",
            ],
            "40001": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/infraLocal",
                plantypenamevalue_codespace + "7_2_EntwicklungsSatzung",
            ],
            "40002": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/infraLocal",
                plantypenamevalue_codespace + "7_3_ErgaenzungsSatzung",
            ],
            "5000": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/infraLocal",
                plantypenamevalue_codespace + "8_AussenbereichsSatzung",
            ],
            "7000": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/infraLocal",
                plantypenamevalue_codespace + "9_2_SonstigesPlanwerkStaedtebaurecht",
            ],
            "9999": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/other",
                plantypenamevalue_codespace + "9_2_SonstigesPlanwerkStaedtebaurecht",
            ],
        }

        object["levelOfSpatialPlan"] = planArt_mapping[planArt][0]
        object["planTypeName"] = planArt_mapping[planArt][1]

        # voidable attribute
        if object.get("rechtsstand", None):
            rechtsstand_mapping = {
                "1000": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/elaboration",
                "1500": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/obsolete",
                "2000": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/elaboration",
                "2050": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/elaboration",
                "2100": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/elaboration",
                "2200": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/elaboration",
                "2250": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/elaboration",
                "2260": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/elaboration",
                "2300": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/elaboration",
                "2400": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/elaboration",
                "3000": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/adoption",
                "4000": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/legalForce",
                "4500": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/obsolete",
                "45000": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/obsolete",
                "45001": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/obsolete",
                "5000": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/obsolete",
                "50000": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/obsolete",
                "50001": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/obsolete",
            }

            rechtsstand = object.pop("rechtsstand")
            object["processStepGeneral"] = rechtsstand_mapping[rechtsstand]

        for attr in [
            "aenderungenBisDatum",
            "aufstellungsbeschlussDatum",
            "auslegungsStartDatum",
            "auslegungsEndDatum",
            "traegerbeteiligungsStartDatum",
            "traegerbeteiligungsEndDatum",
            "satzungsbeschlussDatum",
            "rechtsverordnungsDatum",
            "ausfertigungsDatum",
            "fruehzeitigeOeffentlichkeitsbeteiligungsStartDatum",
            "fruehzeitigeOeffentlichkeitsbeteiligungsEndDatum",
            "fruehzeitigeTraegerbeteiligungsStartDatum",
            "fruehzeitigeTraegerbeteiligungsEndDatum",
        ]:
            if object.get(attr, None):
                if object.get(attr) is not None:
                    self.__set_ordinanceDate(object, attr)

        if object.get("inkrafttretensDatum", None):
            if object.get("inkrafttretensDatum") is not None:
                object["validFrom"] = object.pop("inkrafttretensDatum")

        for attr in ["versionBauNVO", "versionBauGB"]:
            if object.get(attr, None):
                versionBau = object.pop(attr)
                if versionBau.get("name") or versionBau.get("datum"):
                    self.__set_LegislationCitation(object, versionBau, level="national")

        if object.get("bereich", None):
            for bereich_id in object["bereich"]:
                bereich = dict(
                    self.collection.features[bereich_id]
                )  # TODO use classes directly instead of dicts or use model.model_dump() to create dict

                if bereich.get("refScan", None):
                    for refScan in bereich.get("refScan"):
                        self.__wrapper_XP_ExterneReferenz(object, dict(refScan))

                if bereich.get("refPlangrundlage", None):
                    for refPlangrundlage in bereich.get("refPlangrundlage"):
                        self.__wrapper_XP_ExterneReferenz(
                            object, dict(refPlangrundlage)
                        )

                if bereich.get("texte", None):
                    for text_id in bereich.get("texte"):
                        text = dict(self.collection.features[str(text_id)])
                        self.__add_XPText_to_officialDocument(
                            object, text_id, text, abschnitt_type="texte"
                        )

        # benötigte INSPRE attrribute
        self.__set_VoidReasonValue_fromlist(object)

    def _bpbereich(self, object: dict) -> None:
        """Applies transformation for BP_Bereich.

        There are no INSPIRE objects equivalent to BP_Bereich.
        It's attributes get mapped through reference in their respective BP_Plan
        onto SPatialPlan.

        Args:
            object (dict): BP_Bereich
        """
        object.clear()

    def _fpplan(self, object: dict) -> None:
        r"""Maps attributes of the specific class FP_Plan onto SpatialPlan.

        This mapping is applied in succesion to _xpplan, i.e. \n

        Example:
            _xpplan(object) \n
            _fpplan(object) \n

        The transformation includes the mappings: \n
        - planArt to levelOfSpatialPlan and planTypeName \n
        - rechtsstand to processStepGeneral \n
        - aufstellungsbeschlussDatum, auslegungsStartDatum, auslegungsEndDatum, traegerbeteiligungsStartDatum, traegerbeteiligungsEndDatum, aenderungenBisDatum, entwurfsbeschlussDatum, planbeschlussDatum, fruehzeitigeOeffentlichkeitsbeteiligungsStartDatum, fruehzeitigeOeffentlichkeitsbeteiligungsEndDatum, fruehzeitigeTraegerbeteiligungsStartDatum, fruehzeitigeTraegerbeteiligungsEndDatum to ordinance \n
        - wirksamkeitsDatum to validFrom \n
        - versionBauNVO, versionBauGB to LegislationCitation in OfficialDocumentation \n
        - attributes of referenced FP_Bereich objects, namely: refScan and texte to OfficialDocumentation \n
        The officialDocument attribute contains the references for the newly created officialDocumentation objects.
        They are listed in the temporary attribute officialDocument_list.

        Args:
            object (dict): plan
        """
        # pflichtattribute

        # Da die INSPIRE Attribute planTypeName und levelOfSpatialPlan nur einmal belegt werden können, sollte das
        # XPlanung-Attribut planArt auch nur einmal belegt werden. Ansonsten wird nur der erste spezifizierte Attributwert
        # von planArt in das INSPIRE Dokument übernommen
        planArt = object.pop("planArt")

        plantypenamevalue_codespace = "https://registry.gdi-de.org/codelist/de.xleitstelle.inspire_plu/PlanTypeNameValue#"

        planArt_mapping = {
            "1000": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/local",
                plantypenamevalue_codespace + "5_2_Fplan",
            ],
            "2000": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/supraLocal",
                plantypenamevalue_codespace + "4_2_GemeinsamerFPlan",
            ],
            "3000": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/infraRegional",
                plantypenamevalue_codespace + "4_1_RegFPlan",
            ],
            "4000": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/local",
                plantypenamevalue_codespace + "5_1_FplanRegPlan",
            ],
            "5000": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/local",
                plantypenamevalue_codespace + "5_3_SachlicherTeilplan",
            ],
            "9999": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/other",
                plantypenamevalue_codespace + "9_2_SonstigesPlanwerkStaedtebaurecht",
            ],
        }

        object["levelOfSpatialPlan"] = planArt_mapping[planArt][0]
        object["planTypeName"] = planArt_mapping[planArt][1]

        # voidable attribute
        if object.get("rechtsstand", None):
            rechtsstand_mapping = {
                "1000": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/elaboration",
                "2000": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/obsolete",
                "2100": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/obsolete",
                "2200": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/obsolete",
                "2250": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/obsolete",
                "2300": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/obsolete",
                "2400": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/obsolete",
                "3000": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/adoption",
                "4000": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/legalForce",
                "5000": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/obsolete",
                "50000": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/obsolete",
                "50001": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/obsolete",
            }

            rechtsstand = object.pop("rechtsstand")
            object["processStepGeneral"] = rechtsstand_mapping[rechtsstand]

        for attr in [
            "aufstellungsbeschlussDatum",
            "auslegungsStartDatum",
            "auslegungsEndDatum",
            "traegerbeteiligungsStartDatum",
            "traegerbeteiligungsEndDatum",
            "aenderungenBisDatum",
            "entwurfsbeschlussDatum",
            "planbeschlussDatum",
            "fruehzeitigeOeffentlichkeitsbeteiligungsStartDatum",
            "fruehzeitigeOeffentlichkeitsbeteiligungsEndDatum",
            "fruehzeitigeTraegerbeteiligungsStartDatum",
            "fruehzeitigeTraegerbeteiligungsEndDatum",
        ]:
            if object.get(attr, None):
                if object.get(attr) is not None:
                    self.__set_ordinanceDate(object, attr)

        if object.get("wirksamkeitsDatum", None):
            object["validFrom"] = object.pop("wirksamkeitsDatum")

        for attr in ["versionBauNVO", "versionBauGB"]:
            if object.get(attr, None):
                versionBau = object.pop(attr)
                self.__set_LegislationCitation(object, versionBau, level="national")

        if object.get("bereich", None):
            for bereich_id in object["bereich"]:
                bereich = dict(self.collection.features[bereich_id])

                if bereich.get("refScan", None):
                    for refScan in bereich.get("refScan"):
                        self.__wrapper_XP_ExterneReferenz(object, dict(refScan))

                if bereich.get("texte", None):
                    for text_id in bereich.get("texte"):
                        text = dict(self.collection.features[str(text_id)])
                        self.__add_XPText_to_officialDocument(
                            object, text_id, text, abschnitt_type="texte"
                        )

        # benötigte INSPRE attrribute
        self.__set_VoidReasonValue_fromlist(object)

    def _fpbereich(self, object: dict) -> None:
        """Applies transformation for FP_Bereich.

        There are no INSPIRE objects equivalent to FP_Bereich.
        It's attributes get mapped through reference in their respective FP_Plan
        onto SPatialPlan.

        Args:
            object (dict): FP_Bereich
        """
        object.clear()

    def _rpplan(self, object: dict) -> None:
        r"""Maps attributes of the specific class RP_Plan onto SpatialPlan.

        This mapping is applied in succesion to _xpplan, i.e. \n

        Example:
            _xpplan(object) \n
            _rpplan(object) \n

        The transformation includes the mappings:
        - planArt to levelOfSpatialPlan and planTypeName \n
        - rechtsstand to processStepGeneral \n
        - aufstellungsbeschlussDatum, auslegungsStartDatum, auslegungsEndDatum, traegerbeteiligungsStartDatum, traegerbeteiligungsEndDatum, aenderungenBisDatum, entwurfsbeschlussDatum, planbeschlussDatum to ordinance \n
        - datumDesInkrafttretens to validFrom \n
        - versionBROG, versionLPLG to LegislationCitation in OfficialDocumentation \n
        - attributes of referenced RP_Bereich objects, namely: refScan and texte to OfficialDocumentation \n
        The officialDocument attribute contains the references for the newly created officialDocumentation objects.
        They are listed in the temporary attribute officialDocument_list.

        Args:
            object (dict): plan
        """
        # pflichtattribute

        # Da die INSPIRE Attribute planTypeName und levelOfSpatialPlan nur einmal belegt werden können, sollte das
        # XPlanung-Attribut planArt auch nur einmal belegt werden. Ansonsten wird nur der erste spezifizierte Attributwert
        # von planArt in das INSPIRE Dokument übernommen
        planArt = object.pop("planArt")

        plantypenamevalue_codespace = "https://registry.gdi-de.org/codelist/de.xleitstelle.inspire_plu/PlanTypeNameValue#"

        planArt_mapping = {
            "1000": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/regional",
                plantypenamevalue_codespace + "3_1_Regionalplan",
            ],
            "2000": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/regional",
                plantypenamevalue_codespace + "3_3_SachlicherTeilplanRegionalebene",
            ],
            "2001": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/supraRegional",
                plantypenamevalue_codespace + "2_2_SachlicherTeilplanLandesebene",
            ],
            "3000": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/supraRegional",
                plantypenamevalue_codespace + "2_3_Braunkohlenplan",
            ],
            "4000": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/supraRegional",
                plantypenamevalue_codespace + "2_1_LandesweiterRaumordnungsplan",
            ],
            "5000": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/national",
                plantypenamevalue_codespace + "1_1_StandortkonzeptBund",
            ],
            "5001": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/national",
                plantypenamevalue_codespace + "1_2_AWZPlan",
            ],
            "6000": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/infraRegional",
                plantypenamevalue_codespace + "3_2_RaeumlicherTeilplan",
            ],
            "9999": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/other",
                plantypenamevalue_codespace + "9_2_SonstigesPlanwerkStaedtebaurecht",
            ],
        }

        object["levelOfSpatialPlan"] = planArt_mapping[planArt][0]
        object["planTypeName"] = planArt_mapping[planArt][1]

        # voidable attribute
        if object.get("rechtsstand", None):
            rechtsstand_mapping = {
                "1000": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/elaboration",
                "2000": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/elaboration",
                "2001": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/elaboration",
                "2002": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/elaboration",
                "2003": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/obsolete",
                "2004": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/elaboration",
                "3000": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/adoption",
                "4000": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/legalForce",
                "5000": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/elaboration",
                "6000": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/obsolete",
                "7000": "https://inspire.ec.europa.eu/codelist/ProcessStepGeneralValue/obsolete",
            }

            rechtsstand = object.pop("rechtsstand")
            object["processStepGeneral"] = rechtsstand_mapping[rechtsstand]

        for attr in [
            "aufstellungsbeschlussDatum",
            "auslegungsStartDatum",
            "auslegungsEndDatum",
            "traegerbeteiligungsStartDatum",
            "traegerbeteiligungsEndDatum",
            "aenderungenBisDatum",
            "entwurfsbeschlussDatum",
            "planbeschlussDatum",
        ]:
            if object.get(attr, None):
                if object.get(attr) is not None:
                    self.__set_ordinanceDate(object, attr)

        if object.get("datumDesInkrafttretens", None):
            object["validFrom"] = object.pop("datumDesInkrafttretens")

        if object.get("bereich", None):
            for bereich_id in object["bereich"]:
                bereich = dict(self.collection.features[bereich_id])

                if bereich.get("refScan", None):
                    for refScan in bereich.get("refScan"):
                        self.__wrapper_XP_ExterneReferenz(object, dict(refScan))

                if bereich.get("texte", None):
                    for text_id in bereich.get("texte"):
                        text = dict(self.collection.features[str(text_id)])
                        self.__add_XPText_to_officialDocument(
                            object, text_id, text, abschnitt_type="texte"
                        )

                # pflicht/voidable attribute
                if bereich.get("versionBROG", None):
                    versionBROG = bereich.pop("versionBROG")
                    self.__set_LegislationCitation(
                        object, str(versionBROG), level="national"
                    )

                if bereich.get("versionLPLG", None):
                    versionLPLG = bereich.pop("versionLPLG")
                    self.__set_LegislationCitation(
                        object, str(versionLPLG), level="sub-national"
                    )

        # benötigte INSPRE attrribute
        self.__set_VoidReasonValue_fromlist(object)

    def _rpbereich(self, object: dict) -> None:
        """Applies transformation for RP_Bereich.

        There are no INSPIRE objects equivalent to RP_Bereich.
        It's attributes get mapped through reference in their respective RP_Plan
        onto SPatialPlan.

        Args:
            object (dict): RP_Bereich
        """
        object.clear()

    def _soplan(self, object: dict) -> None:
        r"""Maps attributes of the specific class SO_Plan onto SpatialPlan.

        This mapping is applied in succesion to _xpplan, i.e. \n

        Example:
            _xpplan(object) \n
            _soplan(object) \n

        The transformation includes the mappings: \n
        - planArt to levelOfSpatialPlan and planTypeName \n
        - rechtsstand to processStepGeneral \n
        - versionBauGBText to LegislationCitation in OfficialDocumentation \n
        - attributes of referenced SO_Bereich objects, namely: refScan and texte to OfficialDocumentation \n
        The officialDocument attribute contains the references for the newly created officialDocumentation objects.
        They are listed in the temporary attribute officialDocument_list.

        Args:
            object (dict): plan
        """
        # pflichtattribute

        # Da die INSPIRE Attribute planTypeName und levelOfSpatialPlan nur einmal belegt werden können, sollte das
        # XPlanung-Attribut planArt auch nur einmal belegt werden. Ansonsten wird nur der erste spezifizierte Attributwert
        # von planArt in das INSPIRE Dokument übernommen

        # Für die Planarten der Klasse SO_Plan wird ausnahmsweise auf eine externe Codeliste verwiesen, die über
        # den URL https://registry.gdi-de.org/codelist/de.xleitstelle.xplanung/SO_PlanArt veröffentlicht ist.
        planArt = object.pop("planArt").split("/")[-1]

        plantypenamevalue_codespace = "https://registry.gdi-de.org/codelist/de.xleitstelle.inspire_plu/PlanTypeNameValue#"

        planArt_mapping = {
            "01": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/infraLocal",
                plantypenamevalue_codespace
                + "9_4_ErhaltungssatzungVerordnungStaedtebaulicheGestalt",
            ],
            "02": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/infraLocal",
                plantypenamevalue_codespace
                + "9_5_ErhaltungssatzungVerordnungWohnbevoelkerung",
            ],
            "03": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/infraLocal",
                plantypenamevalue_codespace
                + "9_6_ErhaltungssatzungVerordnungUmstrukturierung",
            ],
            "4": [
                "https://inspire.ec.europa.eu/codelist/LevelOfSpatialPlanValue/supraRegional",
                plantypenamevalue_codespace
                + "9_7_VerordnungGebietMitAngespanntemWohnungsmarkt",
            ],
        }

        object["levelOfSpatialPlan"] = planArt_mapping[planArt][0]
        object["planTypeName"] = planArt_mapping[planArt][1]

        # voidable attribute
        if object.get("versionBauGBText", None):
            versionBauGB = {}
            versionBauGB["name"] = object.pop("versionBauGBText")
            versionBauGB["datum"] = object.pop("versionBauGBDatum", None)
            self.__set_LegislationCitation(object, versionBauGB, level="national")

        if object.get("versionBauGB", None):
            versionBau = object.pop("versionBauGB")
            self.__set_LegislationCitation(object, versionBau, level="national")

        if object.get("bereich", None):
            for bereich_id in object["bereich"]:
                bereich = dict(self.collection.features[bereich_id])

                if bereich.get("refScan", None):
                    for refScan in bereich.get("refScan"):
                        self.__wrapper_XP_ExterneReferenz(object, dict(refScan))

                if bereich.get("texte", None):
                    for text_id in bereich.get("texte"):
                        text = dict(self.collection.features[str(text_id)])
                        self.__add_XPText_to_officialDocument(
                            object, text_id, text, abschnitt_type="texte"
                        )

        # benötigte INSPRE attrribute
        self.__set_VoidReasonValue_fromlist(object)

    def _sobereich(self, object: dict) -> None:
        """Applies transformation for SO_Bereich.

        There are no INSPIRE objects equivalent to SO_Bereich.
        It's attributes get mapped through reference in their respective SO_Plan
        onto SPatialPlan.

        Args:
            object (dict): SO_Bereich
        """
        object.clear()

    def _xpobjekt(self, object: dict) -> None:
        r"""Maps attributes of the parent class XP_Objekt onto attributes that are needed in both SupplementaryRegulation and ZoningElement.

        Gets called, before the plan specific transformations for BP_Objekt, FP_Objekt,
        RP_Objekt, SO_Objekt are applied.
        The transformation includes the mappings:  \n
        - id to inspireId \n
        - reference ids from gehoertZuBereich to plan \n
        - hatGenerAttribut to OfficialDocumentation for XP_URLAttribut, otherwise dimensioningIndication \n
        - hoehenangabe to dimensioningIndication \n
        - externeReferenz, refBegruendungInhalt, refTextInhalt to OfficialDocumentation \n
        - startBedingung to validFrom \n
        - endBedingung to validTo \n
        The officialDocument attribute contains the references for the newly created officialDocumentation objects \n
        They are listed in the temporary attribute officialDocument_list \n
        The temporary dictionary mapping is created, with the atrribute ebene from XP_Objekt \n
        The plan is skipped for underground plans, i.e. ebene<0 \n

        Args:
            object (dict): plan
        """
        # pflichtattribute
        object["inspireId"] = {
            "localId": object.get("id"),
            "namespace": self.namespace,
        }

        # voidable attribute
        object.setdefault("mapping", {})
        object.get("mapping")["ebene"] = float(object.pop("ebene", None))
        if object.get("mapping")["ebene"] < 0.0:
            # „Unterirdische“ Planinhalte (XPlanung-Attribut ebene < 0)
            # werden generell ignoriert
            object.clear()

        if object.get("gehoertZuBereich", None):
            plan_id = dict(
                self.collection.features[object.get("gehoertZuBereich")]
            ).get("gehoertZuPlan", None)
            object["plan"] = plan_id

        if object.get("hatGenerAttribut", None):
            for attr in object["hatGenerAttribut"]:
                if self.__validate_model("XPURLAttribut", attr):
                    self.__add_XPURL_to_officialDocument(object, attr)
                else:
                    object.setdefault("dimensioningIndication", []).append(
                        {
                            "indicationReference": attr["name"],
                            "value": attr["wert"],
                        }
                    )
            object.pop("hatGenerAttribut")

        if object.get("hoehenangabe", None):
            hoehenbezug_mapping = {
                "1000": "absolutNHM",
                "1100": "absolutNN",
                "1200": "absolutDHHN",
                "2000": "relativGelaendeoberkante",
                "2500": "relativGehwegOberkante",
                "3000": "relativBezugshoehe ",
                "3500": "relativStrasse",
                "4000": "relativEFH",
            }

            bezugspunkt_mapping = {
                "1000": "TH",
                "2000": "FH",
                "3000": "OK",
                "3500": "LH",
                "4000": "SH",
                "4500": "EFH",
                "5000": "HBA",
                "5500": "UK",
                "6000": "GBH",
                "6500": "WH",
                "6600": "GOK",
            }

            for attr in object["hoehenangabe"]:
                str1 = (
                    hoehenbezug_mapping[attr["hoehenbezug"]]
                    if attr.get("hoehenbezug", None)
                    else attr.get("abweichenderHoehenbezug", None)
                )  # TODO: assuming one attribute is not None, otherwhise
                str1 = "" if not str1 else str1
                str2 = (
                    bezugspunkt_mapping[attr["bezugspunkt"]]
                    if attr.get("bezugspunkt", None)
                    else attr.get("abweichenderBezugspunkt", None)
                )  # TODO: assuming one attribute is not None, otherwhise
                str2 = "" if not str2 else str2

                if attr.get("hMin", None):
                    indicationref_str_hMin = str1 + "&" + str2 + "&" + "hMin"
                    object.setdefault("dimensioningIndication", []).append(
                        {
                            "indicationReference": indicationref_str_hMin,
                            "value": attr.get("hMin", "m"),
                        }
                    )
                if attr.get("hMax", None):
                    indicationref_str_hMax = str1 + "&" + str2 + "&" + "hMax"
                    object.setdefault("dimensioningIndication", []).append(
                        {
                            "indicationReference": indicationref_str_hMax,
                            "value": attr.get("hMax", "m"),
                        }
                    )
                if attr.get("hZwingend", None):
                    str3 = "hZwingend"
                    indicationref_str = str1 + "&" + str2 + "&" + str3
                    value = attr.get("hZwingend", "m")
                    object.setdefault("dimensioningIndication", []).append(
                        {
                            "indicationReference": indicationref_str,
                            "value": value,
                        }
                    )
                if attr.get("h", None):
                    str3 = "h"
                    indicationref_str = str1 + "&" + str2 + "&" + str3
                    value = attr.get("h", "m")
                    object.setdefault("dimensioningIndication", []).append(
                        {
                            "indicationReference": indicationref_str,
                            "value": value,
                        }
                    )
            object.pop("hoehenangabe")

        if object.get("externeReferenz", None):
            for ref in object.get("externeReferenz"):
                self.__add_XP_SpezExterneReferenz_to_officialDocument(object, ref)
            object.pop("externeReferenz")

        if object.get("refBegruendungInhalt", None):
            for ref_id in object.get("refBegruendungInhalt"):
                text = dict(self.collection.features[ref_id])
                self.__add_XPText_to_officialDocument(
                    object, ref_id, text, abschnitt_type="begruendungsTexte"
                )
            object.pop("refBegruendungInhalt")

        if object.get("startBedingung", None):
            object["validFrom"] = object["startBedingung"].get("datumAbsolut", None)
            object.pop("startBedingung")

        if object.get("endeBedingung", None):
            object["validTo"] = object["endeBedingung"].get("datumAbsolut", None)
            object.pop("endeBedingung")

        if object.get("refTextInhalt", None):
            for ref_id in object.get("refTextInhalt"):
                text = dict(self.collection.features[ref_id])
                self.__add_XPText_to_officialDocument(
                    object, ref_id, text, abschnitt_type="texte"
                )
            object.pop("refTextInhalt")

    def _bpobjekt(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Objekt onto attributes that are needed in both SupplementaryRegulation and ZoningElement.

        Gets called, before the plan specific transformations for BP_Punktobjekt, BP_Linienobjekt,
        BP_Geometrieobjekt, BP_Flaechenobjekt are applied.
        This mapping is applied in succesion to _xpobjekt, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n

        The transformation includes the mappings: \n
        - rechtscharakter to regulationNature

        Args:
            object (dict): plan
        """
        # pflichtattribute

        rechtscharakter = object.pop("rechtscharakter")
        regulationNature_mapping = {
            "1000": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/generallyBinding",
            "2000": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/generallyBinding",
            "6000": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/nonBinding",
            "7000": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/definedInLegislation",
            "8000": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/definedInLegislation",
            "9998": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/nonBinding",
        }
        object["regulationNature"] = regulationNature_mapping[rechtscharakter]

    def _bppunktobjekt(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Punktobjekt onto SupplementaryRegulation.

        Gets called, before the plan specific transformations are applied.
        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bppunktobjekt(object) \n

        The transformation includes the mappings: \n
        - position to geometry \n
        BP_Punktobjekt gets mapped onto SupplementaryRegulation by definition,
        no further consideration required.

        Args:
            object (dict): plan
        """
        # pflichtattribute
        object["geometry"] = object.pop("position")

        # voidable attribute
        object.setdefault("mapping", {})
        object.get("mapping")["flaechenschluss"] = object.pop("flaechenschluss", False)
        object["featuretype"] = "SupplementaryRegulation"

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bpzusatzkontingentlaerm(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Zsatzkontingentlaerm onto SupplementaryRegulation.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bppunktobjekt(object) \n
            _bpzusatzkontingentlaerm(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation

        Args:
            object (dict): plan
        """
        self.__set_supplementaryRegulation(object)

    def _bpeinfahrtpunkt(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Einfahrtpunkt onto SupplementaryRegulation.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bppunktobjekt(object) \n
            _bpeinfahrtpunkt(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation

        Args:
            object (dict): plan
        """
        self.__set_supplementaryRegulation(object)

    def _bpimmissionsortlaerm(self, object: dict) -> None:
        r"""Maps attributes of the class BP_ImmissionsortLaerm onto SupplementaryRegulation.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bppunktobjekt(object) \n
            _bpimmissionsortlaerm(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation

        Args:
            object (dict): plan
        """
        self.__set_supplementaryRegulation(object)

    def _bplinienobjekt(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Linienobjekt onto SupplementaryRegulation.

        Gets called, before the plan specific transformations are applied.
        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bplinienobjekt(object) \n

        The transformation includes the mappings: \n
        - position to geometry \n
        BP_Linienobjekt gets mapped onto SupplementaryRegulation by definition,
        no further consideration required.

        Args:
            object (dict): plan
        """
        # pflichtattribute
        object["geometry"] = object.pop("position")

        # voidable attribute
        object.setdefault("mapping", {})
        object.get("mapping")["flaechenschluss"] = object.pop("flaechenschluss", False)
        object["featuretype"] = "SupplementaryRegulation"

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bpnutzungsartengrenze(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Nutzungsartengrenze onto SupplementaryRegulation.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bplinienobjekt(object) \n
            _bpnutzungsartengrenze(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation

        Args:
            object (dict): plan
        """
        self.__set_supplementaryRegulation(object)

    def _bprichtungssektorgrenze(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Richtungssektorgrenze onto SupplementaryRegulation.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bplinienobjekt(object) \n
            _bprichtungssektorgrenze(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation

        Args:
            object (dict): plan
        """
        self.__set_supplementaryRegulation(object)

    def _bpstrassenbegrenzungslinie(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Strassenbegrenzungslinie onto SupplementaryRegulation.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bplinienobjekt(object) \n
            _bpstrassenbegrenzungslinie(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation

        Args:
            object (dict): plan
        """
        self.__set_supplementaryRegulation(object)

    def _bpabstandsmass(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Abstandsmass onto SupplementaryRegulation.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bplinienobjekt(object) \n
            _bpabstandsmass(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation

        Args:
            object (dict): plan
        """
        self.__set_supplementaryRegulation(object)

    def _bpabweichungvonbaugrenze(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Abweichungvonbaugrenze onto SupplementaryRegulation.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bplinienobjekt(object) \n
            _bpabweichungvonbaugrenze(object) \n

        The transformation includes the mappings:
        - supplementaryRegulation and specificSupplementaryRegulation

        Args:
            object (dict): plan
        """
        self.__set_supplementaryRegulation(object)

    def _bpbaugrenze(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Baugrenze onto SupplementaryRegulation.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bplinienobjekt(object) \n
            _bpbaugrenze(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation

        Args:
            object (dict): plan
        """
        self.__set_supplementaryRegulation(object)

    def _bpbaulinie(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Baulinie onto SupplementaryRegulation.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bplinienobjekt(object) \n
            _bpbaulinie(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation

        Args:
            object (dict): plan
        """
        self.__set_supplementaryRegulation(object)

    def _bpbereichohneeinausfahrtlinie(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Bereichohneeinausfahrtlinie onto SupplementaryRegulation.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bplinienobjekt(object) \n
            _bpbereichohneeinausfahrtlinie(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation

        Args:
            object (dict): plan
        """
        self.__set_supplementaryRegulation(object)

    def _bpeinfahrtsbereichlinie(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Einfahrtsbereichlinie onto SupplementaryRegulation.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bplinienobjekt(object) \n
            _bpeinfahrtsbereichlinie(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation

        Args:
            object (dict): plan
        """
        self.__set_supplementaryRegulation(object)

    def _bpgebaeudestellung(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Gebaeudestellung onto SupplementaryRegulation.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bplinienobjekt(object) \n
            _bpgebaeudestellung(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation

        Args:
            object (dict): plan
        """
        self.__set_supplementaryRegulation(object)

    def _bpgeometrieobjekt(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Geometrieobjekt onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpgeometrieobjekt(object) \n

        The transformation includes the mappings: \n
        - position to geometry \n
        Based on the value of flaechenschluss, which gets mapped to the temporary dictionary
        mapping, together with the value ebene, it is determined wether the class object
        gets mapped to SupplementaryRegulation or ZoningElement.

        Args:
            object (dict): plan
        """
        # pflichtattribute
        object["geometry"] = object.pop("position")

        # voidable attribute
        object.setdefault("mapping", {})
        object.get("mapping")["flaechenschluss"] = object.pop("flaechenschluss")
        self.__xpobject_decision_rule(object)

    def _bphoehenmass(self, object) -> None:
        r"""Maps attributes of the class BP_Hoehenmass onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpgeometrieobjekt(object) \n
            _bphoehenmass(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bpimmissionsschutz(self, object) -> None:
        r"""Maps attributes of the class BP_Immissionsschutz onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpgeometrieobjekt(object) \n
            _bpimmissionsschutz(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bpschutzpflegeentwicklungsmassnahme(self, object) -> None:
        r"""Maps attributes of the class BP_Schutzpflegeentwicklungsmassnahme onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpgeometrieobjekt(object) \n
            _bpschutzpflegeentwicklungsmassnahme(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement \n
        - refMassnahmenText, refLandschaftsplan to OfficialDocumentation \n
        The officialDocument attribute contains the references for the newly created officialDocumentation objects.
        They are listed in the temporary attribute officialDocument_list.

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # voidable attribute
        if object.get("refMassnahmenText", None):
            self.__wrapper_XP_ExterneReferenz(
                object,
                object.get("refMassnahmenText"),
                shortName="BP_SchutzPflegeEntwicklungs_MassnahmerefMassnahmenText",
            )
            object.pop("refMassnahmenText")

        if object.get("refLandschaftsplan", None):
            self.__wrapper_XP_ExterneReferenz(
                object,
                object.get("refLandschaftsplan"),
                shortName="BP_SchutzPflegeEntwicklungs_MassnahmerefLandschaftsplan",
            )
            object.pop("refLandschaftsplan")

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bpstrassenkoerper(self, object) -> None:
        r"""Maps attributes of the class BP_Strassenkoerper onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpgeometrieobjekt(object) \n
            _bpstrassenkoerper(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bpunverbindlichevormerkung(self, object) -> None:
        r"""Maps attributes of the class BP_Unverbindlichevormerkung onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpgeometrieobjekt(object) \n
            _bpunverbindlichevormerkung(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bpverentsorgung(self, object) -> None:
        r"""Maps attributes of the class BP_Verentsorgung onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpgeometrieobjekt(object) \n
            _bpverentsorgung(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement \n
        - additional attributes to dimensioningIndication

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        self.__set_dimensioningIndication_for_bpfestsetzungenbaugebiet(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bpwegerecht(self, object) -> None:
        r"""Maps attributes of the class BP_Wegerecht onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpgeometrieobjekt(object) \n
            _bpwegerecht(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bpanpflanzungbindungerhaltung(self, object) -> None:
        r"""Maps attributes of the class BP_Anpflanzungbindungerhaltung onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpgeometrieobjekt(object) \n
            _bpanpflanzungbindungerhaltung(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bpausgleichsmassnahme(self, object) -> None:
        r"""Maps attributes of the class BP_Ausgleichsmassnahme onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpgeometrieobjekt(object) \n
            _bpausgleichsmassnahme(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement \n
        - refMassnahmenText, refLandschaftsplan to OfficialDocumentation \n
        The officialDocument attribute contains the references for the newly created officialDocumentation objects.
        They are listed in the temporary attribute officialDocument_list.

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # voidable attribute
        if object.get("refMassnahmenText", None):
            self.__wrapper_XP_ExterneReferenz(
                object,
                object.get("refMassnahmenText"),
                shortName="BP_AusgleichsMassnahme_refMassnahmenText",
            )
            object.pop("refMassnahmenText")

        if object.get("refLandschaftsplan", None):
            self.__wrapper_XP_ExterneReferenz(
                object,
                object.get("refLandschaftsplan"),
                shortName="BP_AusgleichsMassnahme_refLandschaftsplan",
            )
            object.pop("refLandschaftsplan")

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bpfestsetzungnachlandesrecht(self, object) -> None:
        r"""Maps attributes of the class BP_Festsetzungnachlandesrecht onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpgeometrieobjekt(object) \n
            _bpfestsetzungnachlandesrecht(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bpgemeinschaftsanlagenzuordnung(self, object) -> None:
        r"""Maps attributes of the class BP_Gemeinschaftsanlagenzuordnung onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpgeometrieobjekt(object) \n
            _bpgemeinschaftsanlagenzuordnung(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bpgenerischesobjekt(self, object) -> None:
        r"""Maps attributes of the class BP_Generischesobjekt onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpgeometrieobjekt(object) \n
            _bpgenerischesobjekt(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bpnatuerlicherklimaschutz(self, object) -> None:
        r"""Maps attributes of the class BP_NatuerlicherKlimaschutz onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpgeometrieobjekt(object) \n
            _bpnatuerlicherklimaschutz(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bphoehenfestsetzung(self, object) -> None:
        r"""Maps attributes of the class BP_HoehenFestsetzung onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpgeometrieobjekt(object) \n
            _bphoehenfestsetzung(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bpflaechenobjekt(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Flaechenobjekt onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n

        The transformation includes the mappings: \n
        - position to geometry \n
        Based on the value of flaechenschluss, which gets mapped to the temporary dictionary
        mapping, together with the value ebene, it is determined wether the class object
        gets mapped to SupplementaryRegulation or ZoningElement.

        Args:
            object (dict): plan
        """
        # pflichtattribute
        object["geometry"] = object.pop("position")

        # voidable attribute
        object.setdefault("mapping", {})
        object.get("mapping")["flaechenschluss"] = object.pop("flaechenschluss")
        self.__xpobject_decision_rule(object)

    def _bpflaechenschlussobjekt(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Fflaechenschlussobjekt onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpflaechenschlussobjekt(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bpgemeinbedarfsflaeche(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Gemeindebedarfsflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpflaechenschlussobjekt(object) \n
            _bpgemeinbedarfsflaeche(object) \n

        The transformation includes the mappings: \n
        - miscellaneous attributes to dimensioningIndication

        Args:
            object (dict): plan
        """
        self.__set_dimensioningIndication_for_bpfestsetzungenbaugebiet(object)
        self.__set_dimensioningIndication_for_bpgestaltungbaugebiet(object)
        self.__set_dimensioningIndication_for_miscellaneous(object)

    def _bpgruenflaeche(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Ggruenflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpflaechenschlussobjekt(object) \n
            _bpgruenflaeche(object) \n

        The transformation includes the mappings: \n
        - miscellaneous attributes to dimensioningIndication

        Args:
            object (dict): plan
        """
        self.__set_dimensioningIndication_for_bpfestsetzungenbaugebiet(object)

    def _bpkleintierhaltungflaeche(self, object: dict) -> None:
        r"""Maps the class BP_Kleintierhaltungflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpflaechenschlussobjekt(object) \n
            _bpkleintierhaltungflaeche(object) \n

        Args:
            object (dict): plan
        """
        pass

    def _bplandwirtschaftsflaeche(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Landwirtschaftsflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpflaechenschlussobjekt(object) \n
            _bplandwirtschaftsflaeche(object) \n

        Args:
            object (dict): plan
        """

    def _bpspielsportanlagenflaeche(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Spielsportanlagenflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpflaechenschlussobjekt(object) \n
            _bpspielsportanlagenflaeche(object) \n

        The transformation includes the mappings:
        - miscellaneous attributes to dimensioningIndication

        Args:
            object (dict): plan
        """
        self.__set_dimensioningIndication_for_bpfestsetzungenbaugebiet(object)

    def _bpwaldflaeche(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Waldflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpflaechenschlussobjekt(object) \n
            _bpwaldflaeche(object) \n

        Args:
            object (dict): plan
        """

    def _bpwohngebaeudeflaeche(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Wohngebaeudeflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpflaechenschlussobjekt(object) \n
            _bpwohngebaeudeflaeche(object) \n

        Args:
            object (dict): plan
        """

    def _bpbaugebietsteilflaeche(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Wohngebaeudeflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpflaechenschlussobjekt(object) \n
            _bpwohngebaeudeflaeche(object) \n

        The transformation includes the mappings: \n
        - refGebaeudequerschnitt to OfficialDocumentation \n
        - miscellaneous attributes to dimensioningIndication \n
        The officialDocument attribute contains the references for the newly created officialDocumentation objects.
        They are listed in the temporary attribute officialDocument_list.

        Args:
            object (dict): plan
        """
        # voidable attribute
        if object.get("refGebaeudequerschnitt", None):
            for refText in object.get("refGebaeudequerschnitt"):
                self.__wrapper_XP_ExterneReferenz(
                    object,
                    refText,
                    shortName="BP_BaugebietsTeilFlaeche_refGebaeudequerschnitt",
                )
            object.pop("refGebaeudequerschnitt")

        self.__set_dimensioningIndication_for_bpfestsetzungenbaugebiet(object)
        self.__set_dimensioningIndication_for_bpgestaltungbaugebiet(object)
        self.__set_dimensioningIndication_for_BP_ZusaetzlicheFestsetzungen(object)
        self.__set_dimensioningIndication_for_miscellaneous(object)

    def _bpflaecheohnefestsetzung(self, object: dict) -> None:
        r"""Maps the class BP_Flaecheohnefestsetzung onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpflaechenschlussobjekt(object) \n
            _bpflaecheohnefestsetzung(object) \n

        Args:
            object (dict): plan
        """
        pass

    def _bpfreiflaeche(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Freiflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpflaechenschlussobjekt(object) \n
            _bpfreiflaeche(object) \n

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bpkennzeichnungsflaeche(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Kennzeichnungsflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpflaechenschlussobjekt(object) \n
            _bpkennzeichnungsflaeche(object) \n

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bpschutzpflegeentwicklungsflaeche(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Schutzpflegeentwicklungsflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpflaechenschlussobjekt(object) \n
            _bpschutzpflegeentwicklungsflaeche(object) \n

        The transformation includes the mappings: \n
        - refMassnahmenText, refLandschaftsplan to OfficialDocumentation \n
        The officialDocument attribute contains the references for the newly created officialDocumentation objects.
        They are listed in the temporary attribute officialDocument_list.

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        if object.get("refMassnahmenText", None):
            self.__wrapper_XP_ExterneReferenz(
                object,
                object.get("refMassnahmenText"),
                shortName="BP_SchutzPflegeEntwicklungsFlaeche_refMassnahmenText",
            )
            object.pop("refMassnahmenText")

        if object.get("refLandschaftsplan", None):
            self.__wrapper_XP_ExterneReferenz(
                object,
                object.get("refLandschaftsplan"),
                shortName="BP_SchutzPflegeEntwicklungsFlaeche_refLandschaftsplan",
            )
            object.pop("refLandschaftsplan")

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bpueberlagerungsobjekt(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Ueberlagerungsobjekt onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpueberlagerungsobjekt(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bpveraenderungssperre(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Veraenderungssperre onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpueberlagerungsobjekt(object) \n
            _bpveraenderungssperre(object) \n

        Args:
            object (dict): plan
        """

    def _bpzentralerversorgungsbereich(self, object: dict) -> None:
        r"""Maps the class BP_Zentralerversorgungsbereich onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpueberlagerungsobjekt(object) \n
            _bpzentralerversorgungsbereich(object) \n

        Args:
            object (dict): plan
        """
        pass

    def _bpzusatzkontingentlaermflaeche(self, object: dict) -> None:
        r"""Maps the class BP_Zusatzkontingentlaermflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpueberlagerungsobjekt(object) \n
            _bpzusatzkontingentlaermflaeche(object) \n

        Args:
            object (dict): plan
        """
        pass

    def _bpabstandsflaeche(self, object: dict) -> None:
        r"""Maps the class BP_Abstandsflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpueberlagerungsobjekt(object) \n
            _bpabstandsflaeche(object) \n

        Args:
            object (dict): plan
        """

    def _bpabweichungvonueberbaubarergrundstuecksflaeche(self, object: dict) -> None:
        r"""Maps the class BP_Abweichungvonueberbaubarergrundstuecksflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpueberlagerungsobjekt(object) \n
            _bpabweichungvonueberbaubarergrundstuecksflaeche(object) \n

        Args:
            object (dict): plan
        """
        pass

    def _bpeingriffsbereich(self, object: dict) -> None:
        r"""Maps the class BP_Eingriffsbereich onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpueberlagerungsobjekt(object) \n
            _bpeingriffsbereich(object) \n

        Args:
            object (dict): plan
        """
        pass

    def _bpfoerderungsflaeche(self, object: dict) -> None:
        r"""Maps the class BP_Foerderungsflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpueberlagerungsobjekt(object) \n
            _bpfoerderungsflaeche(object) \n

        Args:
            object (dict): plan
        """
        pass

    def _bpgebaeudeflaeche(self, object: dict) -> None:
        r"""Maps the class BP_Gebaeudeflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpueberlagerungsobjekt(object) \n
            _bpgebaeudeflaeche(object) \n

        Args:
            object (dict): plan
        """
        pass

    def _bpgemeinschaftsanlagenflaeche(self, object: dict) -> None:
        r"""Maps the class BP_Gemeinschaftsanlagenflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpueberlagerungsobjekt(object) \n
            _bpgemeinschaftsanlagenflaeche(object) \n

        Args:
            object (dict): plan
        """

    def _bpnebenanlagenausschlussflaeche(self, object: dict) -> None:
        r"""Maps the class BP_Nebenanlagenausschlussflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpueberlagerungsobjekt(object) \n
            _bpnebenanlagenausschlussflaeche(object) \n

        Args:
            object (dict): plan
        """

    def _bpnebenanlagenflaeche(self, object: dict) -> None:
        r"""Maps the class BP_Nebenanlagenflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpueberlagerungsobjekt(object) \n
            _bpnebenanlagenflaeche(object) \n

        Args:
            object (dict): plan
        """

    def _bpnichtueberbaubaregrundstuecksflaeche(self, object: dict) -> None:
        r"""Maps the class BP_Nichtueberbaubaregrundstuecksflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpueberlagerungsobjekt(object) \n
            _bpnichtueberbaubaregrundstuecksflaeche(object) \n

        Args:
            object (dict): plan
        """

    def _bppersgruppenbestimmteflaeche(self, object: dict) -> None:
        r"""Maps the class BP_Persgruppenbestimmteflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpueberlagerungsobjekt(object) \n
            _bppersgruppenbestimmteflaeche(object) \n

        Args:
            object (dict): plan
        """
        pass

    def _bpregelungvergnuegungsstaetten(self, object: dict) -> None:
        r"""Maps the class BP_Regelungvergnuegungsstaetten onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpueberlagerungsobjekt(object) \n
            _bpregelungvergnuegungsstaetten(object) \n

        Args:
            object (dict): plan
        """

    def _bpspeziellebauweise(self, object: dict) -> None:
        r"""Maps the class BP_Speziellebauweise onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpueberlagerungsobjekt(object) \n
            _bpspeziellebauweise(object) \n

        Args:
            object (dict): plan
        """

    def _bptechnischemassnahmenflaeche(self, object: dict) -> None:
        r"""Maps the class BP_Technischemassnahmenflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpueberlagerungsobjekt(object) \n
            _bptechnischemassnahmenflaeche(object) \n

        Args:
            object (dict): plan
        """

    def _bptextabschnittflaeche(self, object: dict) -> None:
        r"""Maps the class BP_Textabschnittflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpueberlagerungsobjekt(object) \n
            _bptextabschnittflaeche(object) \n

        Args:
            object (dict): plan
        """
        pass

    def _bpueberbaubaregrundstuecksflaeche(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Textabschnittflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpueberlagerungsobjekt(object) \n
            _bptextabschnittflaeche(object) \n

        The transformation includes the mappings: \n
        - refMassnahmenText to OfficialDocumentation \n
        - miscellaneous attributes to dimensioningIndication \n
        The officialDocument attribute contains the references for the newly created officialDocumentation objects.
        They are listed in the temporary attribute officialDocument_list.

        Args:
            object (dict): plan
        """
        # voidable attribute
        if object.get("refGebaeudequerschnitt", None):
            for refText in object.get("refGebaeudequerschnitt"):
                self.__wrapper_XP_ExterneReferenz(
                    object,
                    refText,
                    shortName="BP_UeberbaubareGrundstuecks_FlaecherefGebaeudequerschnitt",
                )
            object.pop("refGebaeudequerschnitt")

        self.__set_dimensioningIndication_for_bpfestsetzungenbaugebiet(object)
        self.__set_dimensioningIndication_for_bpgestaltungbaugebiet(object)
        self.__set_dimensioningIndication_for_BP_ZusaetzlicheFestsetzungen(object)
        self.__set_dimensioningIndication_for_miscellaneous(object)

    def _bpabgrabungsflaeche(self, object: dict) -> None:
        r"""Maps the class BP_Abgrabungsflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpueberlagerungsobjekt(object) \n
            _bpabgrabungsflaeche(object) \n

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bpaufschuettungsflaeche(self, object: dict) -> None:
        r"""Maps the class BP_Aufschuettungsflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpueberlagerungsobjekt(object) \n
            _bpaufschuettungsflaeche(object) \n

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bpausgleichsflaeche(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Ausgleichsflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpueberlagerungsobjekt(object) \n
            _bpausgleichsflaeche(object) \n

        The transformation includes the mappings: \n
        - refMassnahmenText, refMassnahmenText to OfficialDocumentation \n
        The officialDocument attribute contains the references for the newly created officialDocumentation objects.
        They are listed in the temporary attribute officialDocument_list.

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # voidable attribute
        if object.get("refMassnahmenText", None):
            self.__wrapper_XP_ExterneReferenz(
                object,
                object.get("refMassnahmenText"),
                shortName="BP_AusgleichsFlaeche_refMassnahmenText",
            )
            object.pop("refMassnahmenText")

        if object.get("refLandschaftsplan", None):
            self.__wrapper_XP_ExterneReferenz(
                object,
                object.get("refLandschaftsplan"),
                shortName="BP_AusgleichsFlaeche_refLandschaftsplan",
            )
            object.pop("refLandschaftsplan")

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bpbesonderernutzungszweckflaeche(self, object: dict) -> None:
        r"""Maps attributes of the class BP_Besonderernutzungszweckflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpbesonderernutzungszweckflaeche(object) \n

        The transformation includes the mappings: \n
        - miscellaneous attributes to dimensioningIndication

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        self.__set_dimensioningIndication_for_bpfestsetzungenbaugebiet(object)
        self.__set_dimensioningIndication_for_bpgestaltungbaugebiet(object)
        self.__set_dimensioningIndication_for_miscellaneous(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _bpwohngebaeudeflaeche(self, object: dict) -> None:
        r"""Maps attributes of the class BP_WohngebaeudeFlaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _bpobjekt(object) \n
            _bpflaechenobjekt(object) \n
            _bpfflaechenschlussobjekt(object) \n
            _bpwohngebaeudeflaeche(object) \n

        The transformation includes the mappings: \n
        - miscellaneous attributes to dimensioningIndication

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        self.__set_dimensioningIndication_for_bpfestsetzungenbaugebiet(object)
        self.__set_dimensioningIndication_for_bpgestaltungbaugebiet(object)
        self.__set_dimensioningIndication_for_miscellaneous(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _fpobjekt(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Objekt onto attributes that are needed in both SupplementaryRegulation and ZoningElement.

        Gets called, before the plan specific transformations for FP_Punktobjekt, FP_Linienobjekt,
        FP_Geometrieobjekt, FP_Flaechenobjekt are applied.
        This mapping is applied in succesion to _xpobjekt, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n

        The transformation includes the mappings: \n
        - rechtscharakter to regulationNature

        Args:
            object (dict): plan
        """
        # pflichtattribute

        rechtscharakter = object.pop("rechtscharakter")
        regulationNature_mapping = {
            "2000": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/definedInLegislation",
            "3000": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/bindingOnlyForAuthorities",
            "6000": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/nonBinding",
            "7000": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/definedInLegislation",
            "8000": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/definedInLegislation",
            "9998": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/nonBinding",
        }
        object["regulationNature"] = regulationNature_mapping[rechtscharakter]

    def _fppunktobjekt(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Punktobjekt onto SupplementaryRegulation.

        Gets called, before the plan specific transformations are applied
        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fppunktobjekt(object) \n

        The transformation includes the mappings: \n
        - position to geometry \n
        FP_Punktobjekt gets mapped onto SupplementaryRegulation by definition,
        no further consideration required.

        Args:
            object (dict): plan
        """
        # pflichtattribute
        object["geometry"] = object.pop("position")

        # voidable attribute
        object.setdefault("mapping", {})
        object.get("mapping")["flaechenschluss"] = object.pop("flaechenschluss", False)
        object["featuretype"] = "SupplementaryRegulation"

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _fplinienobjekt(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Linienobjekt onto SupplementaryRegulation.

        Gets called, before the plan specific transformations are applied
        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fplinienobjekt(object) \n

        The transformation includes the mappings: \n
        - position to geometry \n
        FP_Linienobjekt gets mapped onto SupplementaryRegulation by definition,
        no further consideration required.

        Args:
            object (dict): plan
        """
        # pflichtattribute
        object["geometry"] = object.pop("position")

        # voidable attribute
        object.setdefault("mapping", {})
        object.get("mapping")["flaechenschluss"] = object.pop("flaechenschluss", False)
        object["featuretype"] = "SupplementaryRegulation"

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _fpgeometrieobjekt(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Geometrieobjekt onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpgeometrieobjekt(object) \n

        The transformation includes the mappings: \n
        - position to geometry \n
        Based on the value of flaechenschluss, which gets mapped to the temporary dictionary
        mapping, together with the value ebene, it is determined wether the class object
        gets mapped to SupplementaryRegulation or ZoningElement.

        Args:
            object (dict): plan
        """
        # pflichtattribute
        object["geometry"] = object.pop("position")

        # voidable attribute
        object.setdefault("mapping", {})
        object.get("mapping")["flaechenschluss"] = object.pop("flaechenschluss")
        self.__xpobject_decision_rule(object)

    def _fpgruen(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Gruen onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpgeometrieobjekt(object) \n
            _fpgruen(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _fpkennzeichnung(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Kennzeichnung onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpgeometrieobjekt(object) \n
            _fpkennzeichnung(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _fplandwirtschaft(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Landwirtschaft onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpgeometrieobjekt(object) \n
            _fplandwirtschaft(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _fpnutzungsbeschraenkung(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Nutzungsbeschraenkung onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpgeometrieobjekt(object) \n
            _fpnutzungsbeschraenkung(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _fpprivilegiertesvorhaben(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Privilegiertesvorhaben onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpgeometrieobjekt(object) \n
            _fpprivilegiertesvorhaben(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _fpschutzpflegeentwicklung(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Schutzpflegeentwicklung onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpgeometrieobjekt(object) \n
            _fpschutzpflegeentwicklung(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _fpspielsportanlage(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Spielsportanlage onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpgeometrieobjekt(object) \n
            _fpspielsportanlage(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _fpunverbindlichevormerkung(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Unverbindlichevormerkung onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpgeometrieobjekt(object) \n
            _fpunverbindlichevormerkung(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _fpverentsorgung(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Verentsorgung onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpgeometrieobjekt(object) \n
            _fpverentsorgung(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _fpabgrabung(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Abgrabung onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpgeometrieobjekt(object) \n
            _fpabgrabung(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _fpanpassungklimawandel(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Anpassungklimawandel onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpgeometrieobjekt(object) \n
            _fpanpassungklimawandel(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _fpaufschuettung(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Aufschuettung onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpgeometrieobjekt(object) \n
            _fpaufschuettung(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _fpdarstellungnachlandesrecht(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Darstellungnachlandesrecht onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpgeometrieobjekt(object) \n
            _fpdarstellungnachlandesrecht(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _fpgemeinbedarf(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Gemeinbedarf onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpgeometrieobjekt(object) \n
            _fpgemeinbedarf(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _fpgenerischesobjekt(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Generischesobjekt onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpgeometrieobjekt(object) \n
            _fpgenerischesobjekt(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _fpnatuerlicherklimaschutz(self, object: dict) -> None:
        r"""Maps attributes of the class FP_NatuerlicherKlimaschutz onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpgeometrieobjekt(object) \n
            _fpnatuerlicherklimaschutz(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _fpflaechenobjekt(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Flaechenobjekt onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpflaechenobjekt(object) \n

        The transformation includes the mappings: \n
        - position to geometry \n
        Based on the value of flaechenschluss, which gets mapped to the temporary dictionary
        mapping, together with the value ebene, it is determined wether the class object
        gets mapped to SupplementaryRegulation or ZoningElement.

        Args:
            object (dict): plan
        """
        # pflichtattribute
        object["geometry"] = object.pop("position")

        # voidable attribute
        object.setdefault("mapping", {})
        object.get("mapping")["flaechenschluss"] = object.pop("flaechenschluss")
        self.__xpobject_decision_rule(object)

    def _fpflaechenschlussobjekt(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Flaechenschlussobjekt onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpflaechenobjekt(object) \n
            _fpflaechenschlussobjekt(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _fpwaldflaeche(self, object: dict) -> None:
        r"""Maps the class FP_Waldflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpflaechenobjekt(object) \n
            _fpflaechenschlussobjekt(object) \n
            _fpwaldflaeche(object) \n

        Args:
            object (dict): plan
        """

    def _fpbebauungsflaeche(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Bebauungsflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpflaechenobjekt(object) \n
            _fpflaechenschlussobjekt(object) \n
            _fpbebauungsflaeche(object) \n

        The transformation includes the mappings: \n
        - miscellaneous attributes to dimensioningIndication

        Args:
            object (dict): plan
        """
        self.__set_dimensioningIndication_for_FP_BebauungsFlaeche(object)

    def _fpflaecheohnedarstellung(self, object: dict) -> None:
        r"""Maps the class FP_Flaecheohnedarstellung onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpflaechenobjekt(object) \n
            _fpflaechenschlussobjekt(object) \n
            _fpflaecheohnedarstellung(object) \n

        Args:
            object (dict): plan
        """
        pass

    def _fpkeinezentrabwasserbeseitigungflaeche(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Keinezentrabwasserbeseitigungflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpflaechenobjekt(object) \n
            _fpkeinezentrabwasserbeseitigungflaeche(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _fpueberlagerungsobjekt(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Ueberlagerungsobjekt onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpflaechenobjekt(object) \n
            _fpueberlagerungsobjekt(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _fpzentralerversorgungsbereich(self, object: dict) -> None:
        r"""Maps the class FP_Zentralerversorgungsbereich onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpflaechenobjekt(object) \n
            _fpueberlagerungsobjekt(object) \n
            _fpzentralerversorgungsbereich(object) \n

        Args:
            object (dict): plan
        """

    def _fptextabschnittflaeche(self, object: dict) -> None:
        r"""Maps the class FP_Textabschnittflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpflaechenobjekt(object) \n
            _fpueberlagerungsobjekt(object) \n
            _fptextabschnittflaeche(object) \n

        Args:
            object (dict): plan
        """
        pass

    def _fpvorbehalteflaeche(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Vorbehalteflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpflaechenobjekt(object) \n
            _fpvorbehalteflaeche(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _fpausgleichsflaeche(self, object: dict) -> None:
        r"""Maps attributes of the class FP_Ausgleichsflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _fpobjekt(object) \n
            _fpflaechenobjekt(object) \n
            _fpausgleichsflaeche(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement \n
        - refMassnahmenText, refLandschaftsplan to OfficialDocumentation \n
        The officialDocument attribute contains the references for the newly created officialDocumentation objects.
        They are listed in the temporary attribute officialDocument_list.

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # voidable attribute
        if object.get("refMassnahmenText", None):
            self.__wrapper_XP_ExterneReferenz(
                object,
                object.get("refMassnahmenText"),
                shortName="FP_AusgleichsMassnahme_refMassnahmenText",
            )
            object.pop("refMassnahmenText")

        if object.get("refLandschaftsplan", None):
            self.__wrapper_XP_ExterneReferenz(
                object,
                object.get("refLandschaftsplan"),
                shortName="FP_AusgleichsMassnahme_refLandschaftsplan",
            )
            object.pop("refLandschaftsplan")

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _rpobjekt(self, object: dict) -> None:
        r"""Maps attributes of the class RP_Objekt onto attributes that are needed in both SupplementaryRegulation and ZoningElement.

        Gets called, before the plan specific transformations for RP_Geometrieobjekt
        are applied.
        This mapping is applied in succesion to _xpobjekt, i.e.

        Example:
            _xpobjekt(object) \n
            _rpobjekt(object) \n

        The transformation includes the mappings: \n
        - rechtscharakter to regulationNature

        Args:
            object (dict): plan
        """
        # pflichtattribute

        rechtscharakter = object.pop("rechtscharakter")
        regulationNature_mapping = {
            "2000": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/bindingForDevelopers",
            "4000": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/generallyBinding",
            "4100": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/generallyBinding",
            "4200": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/bindingForDevelopers",
            "4300": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/bindingForDevelopers",
            "4400": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/nonBinding",
            "4500": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/generallyBinding",
            "4600": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/generallyBinding",
            "4700": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/nonBinding",
            "9998": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/nonBinding",
        }
        object["regulationNature"] = regulationNature_mapping[rechtscharakter]

    def _rpgeometrieobjekt(self, object: dict) -> None:
        r"""Maps attributes of the class RP_Geometrieobjekt onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _rpobjekt(object) \n
            _rpgeometrieobjekt(object) \n

        The transformation includes the mappings: \n
        - position to geometry \n
        Based on the value of flaechenschluss, which gets mapped to the temporary dictionary
        mapping, together with the value ebene, it is determined wether the class object
        gets mapped to SupplementaryRegulation or ZoningElement.

        Args:
            object (dict): plan
        """
        # pflichtattribute
        object["geometry"] = object.pop("position")

        # voidable attribute
        object.setdefault("mapping", {})
        object.get("mapping")["flaechenschluss"] = object.pop("flaechenschluss")
        self.__xpobject_decision_rule(object)

    def _rpgrenze(self, object: dict) -> None:
        r"""Maps attributes of the class RP_Grenze onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _rpobjekt(object) \n
            _rpgeometrieobjekt(object) \n
            _rpgrenze(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _rpkommunikation(self, object: dict) -> None:
        r"""Maps attributes of the class RP_Kommunikation onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _rpobjekt(object) \n
            _rpgeometrieobjekt(object) \n
            _rpkommunikation(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _rplaermschutzbauschutz(self, object: dict) -> None:
        r"""Maps attributes of the class RP_Laermschutzbauschutz onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _rpobjekt(object) \n
            _rpgeometrieobjekt(object) \n
            _rplaermschutzbauschutz(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _rpplanungsraum(self, object: dict) -> None:
        r"""Maps attributes of the class RP_Planungsraum onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _rpobjekt(object) \n
            _rpgeometrieobjekt(object) \n
            _rpplanungsraum(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _rpraumkategorie(self, object: dict) -> None:
        r"""Maps attributes of the class RP_Raumkategorie onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _rpobjekt(object) \n
            _rpgeometrieobjekt(object) \n
            _rpraumkategorie(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _rpsiedlung(self, object: dict) -> None:
        r"""Maps attributes of the class RP_Siedlung onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _rpobjekt(object) \n
            _rpgeometrieobjekt(object) \n
            _rpsiedlung(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _rpsonstigeinfrastruktur(self, object: dict) -> None:
        r"""Maps attributes of the class RP_Sonstigeinfrastruktur onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _rpobjekt(object) \n
            _rpgeometrieobjekt(object) \n
            _rpsonstigeinfrastruktur(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _rpsozialeinfrastruktur(self, object: dict) -> None:
        r"""Maps attributes of the class RP_Sozialeinfrastruktur onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _rpobjekt(object) \n
            _rpgeometrieobjekt(object) \n
            _rpsozialeinfrastruktur(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _rpsperrgebiet(self, object: dict) -> None:
        r"""Maps attributes of the class RP_Sperrgebiet onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _rpobjekt(object) \n
            _rpgeometrieobjekt(object) \n
            _rpsperrgebiet(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _rpverkehr(self, object: dict) -> None:
        r"""Maps attributes of the class RP_Verkehr onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _rpobjekt(object) \n
            _rpgeometrieobjekt(object) \n
            _rpverkehr(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _rpwasserwirtschaft(self, object: dict) -> None:
        r"""Maps attributes of the class RP_Wasserwirtschaft onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _rpobjekt(object) \n
            _rpgeometrieobjekt(object) \n
            _rpwasserwirtschaft(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _rpzentralerort(self, object: dict) -> None:
        r"""Maps attributes of the class RP_Zentralerort onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _rpobjekt(object) \n
            _rpgeometrieobjekt(object) \n
            _rpzentralerort(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _rpachse(self, object: dict) -> None:
        r"""Maps attributes of the class RP_Achse onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _rpobjekt(object) \n
            _rpgeometrieobjekt(object) \n
            _rpachse(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _rpenergieversorgung(self, object: dict) -> None:
        r"""Maps attributes of the class RP_Energieversorgung onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _rpobjekt(object) \n
            _rpgeometrieobjekt(object) \n
            _rpenergieversorgung(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _rpentsorgung(self, object: dict) -> None:
        r"""Maps attributes of the class RP_Entsorgung onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _rpobjekt(object) \n
            _rpgeometrieobjekt(object) \n
            _rpentsorgung(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _rpfreiraum(self, object: dict) -> None:
        r"""Maps attributes of the class RP_Freiraum onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _rpobjekt(object) \n
            _rpgeometrieobjekt(object) \n
            _rpfreiraum(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _rpfunktionszuweisung(self, object: dict) -> None:
        r"""Maps attributes of the class RP_Funktionszuweisung onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _rpobjekt(object) \n
            _rpgeometrieobjekt(object) \n
            _rpfunktionszuweisung(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _rpgenerischesobjekt(self, object: dict) -> None:
        r"""Maps attributes of the class RP_Generischesobjekt onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _rpobjekt(object) \n
            _rpgeometrieobjekt(object) \n
            _rpgenerischesobjekt(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _rptextabschnittobjekt(self, object: dict) -> None:
        r"""Maps attributes of the class RP_TextAbschnittObjekt onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _rpobjekt(object) \n
            _rpgeometrieobjekt(object) \n
            _rptextabschnittobjekt(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _soobjekt(self, object: dict) -> None:
        r"""Maps attributes of the class SO_Objekt onto attributes that are needed in both SupplementaryRegulation and ZoningElement.

        Gets called, before the plan specific transformations for SO_Punktobjekt, SO_Linienobjekt,
        SO_Geometrieobjekt, SO_Flaechenobjekt are applied.
        This mapping is applied in succesion to _xpobjekt, i.e.

        Example:
            _xpobjekt(object) \n
            _soobjekt(object) \n

        The transformation includes the mappings: \n
        - rechtscharakter to regulationNature

        Args:
            object (dict): plan
        """
        # pflichtattribute

        rechtscharakter = object.pop("rechtscharakter")
        regulationNature_mapping = {
            "1000": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/generallyBinding",
            "2000": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/definedInLegislation",
            "3000": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/bindingOnlyForAuthorities",
            "5300": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/generallyBinding",
            "6000": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/nonBinding",
            "7000": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/definedInLegislation",
            "8000": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/definedInLegislation",
            "9998": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/nonBinding",
            "9999": "https://inspire.ec.europa.eu/codelist/RegulationNatureValue/nonBinding",
        }
        object["regulationNature"] = regulationNature_mapping[rechtscharakter]

    def _sopunktobjekt(self, object: dict) -> None:
        r"""Maps attributes of the class SO_Punktobjekt onto SupplementaryRegulation.

        Gets called, before the plan specific transformations are applied
        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _soobjekt(object) \n
            _sopunktobjekt(object) \n

        The transformation includes the mappings: \n
        - position to geometry \n
        SO_Punktobjekt gets mapped onto SupplementaryRegulation by definition,
        no further consideration required.

        Args:
            object (dict): plan
        """
        # pflichtattribute
        object["geometry"] = object.pop("position")

        # voidable attribute
        object.setdefault("mapping", {})
        object.get("mapping")["flaechenschluss"] = object.pop("flaechenschluss", False)
        object["featuretype"] = "SupplementaryRegulation"

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _solinienobjekt(self, object: dict) -> None:
        r"""Maps attributes of the class SO_Linienobjekt onto SupplementaryRegulation.

        Gets called, before the plan specific transformations are applied
        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _soobjekt(object) \n
            _solinienobjekt(object) \n

        The transformation includes the mappings: \n
        - position to geometry \n
        SO_Linienobjekt gets mapped onto SupplementaryRegulation by definition,
        no further consideration required.

        Args:
            object (dict): plan
        """
        # pflichtattribute
        object["geometry"] = object.pop("position")

        # voidable attribute
        object.setdefault("mapping", {})
        object.get("mapping")["flaechenschluss"] = object.pop("flaechenschluss", False)
        object["featuretype"] = "SupplementaryRegulation"

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _sogrenze(self, object: dict) -> None:
        r"""Maps attributes of the class SO_Grenze onto SupplementaryRegulation.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _soobjekt(object) \n
            _sopunktobjekt(object) \n
            _sogrenze(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation

        Args:
            object (dict): plan
        """
        self.__set_supplementaryRegulation(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _sofestpunkt(self, object: dict) -> None:
        r"""Maps attributes of the class SO_Festpunkt onto SupplementaryRegulation.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _soobjekt(object) \n
            _sopunktobjekt(object) \n
            _sofestpunkt(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation

        Args:
            object (dict): plan
        """
        self.__set_supplementaryRegulation(object)

    def _sogeometrieobjekt(self, object: dict) -> None:
        r"""Maps attributes of the class SO_Geometrieobjekt onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _soobjekt(object) \n
            _sogeometrieobjekt(object) \n

        The transformation includes the mappings: \n
        - position to geometry \n
        Based on the value of flaechenschluss, which gets mapped to the temporary dictionary
        mapping, together with the value ebene, it is determined wether the class object
        gets mapped to SupplementaryRegulation or ZoningElement.

        Args:
            object (dict): plan
        """
        # pflichtattribute
        object["geometry"] = object.pop("position")

        # voidable attribute
        object.setdefault("mapping", {})
        object.get("mapping")["flaechenschluss"] = object.pop("flaechenschluss")
        self.__xpobject_decision_rule(object)

    def _sogewaesser(self, object: dict) -> None:
        r"""Maps attributes of the class SO_Gewaesser onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _soobjekt(object) \n
            _sogeometrieobjekt(object) \n
            _sogewaesser(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # avoid collisison with name attribute of SupplementaryRegulation
        object.pop("name", None)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _soluftverkehrsrecht(self, object: dict) -> None:
        r"""Maps attributes of the class SO_Luftverkehrsrecht onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _soobjekt(object) \n
            _sogeometrieobjekt(object) \n
            _soluftverkehrsrecht(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # avoid collisison with name attribute of SupplementaryRegulation
        object.pop("name", None)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _soschienenverkehrsrecht(self, object: dict) -> None:
        r"""Maps attributes of the class SO_Schienenverkehrsrecht onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _soobjekt(object) \n
            _sogeometrieobjekt(object) \n
            _soschienenverkehrsrecht(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # avoid collisison with name attribute of SupplementaryRegulation
        object.pop("name", None)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _soschutzgebietwasserrecht(self, object: dict) -> None:
        r"""Maps attributes of the class SO_Schutzgebietwasserrecht onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _soobjekt(object) \n
            _sogeometrieobjekt(object) \n
            _soschutzgebietwasserrecht(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # avoid collisison with name attribute of SupplementaryRegulation
        object.pop("name", None)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _sosonstigesrecht(self, object: dict) -> None:
        r"""Maps attributes of the class SO_Sonstigesrecht onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _soobjekt(object) \n
            _sogeometrieobjekt(object) \n
            _sosonstigesrecht(object) \n

        The transformation includes the mappings:
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # avoid collisison with name attribute of SupplementaryRegulation
        object.pop("name", None)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _sostrassenverkehr(self, object: dict) -> None:
        r"""Maps attributes of the class SO_Strassenverkehr onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _soobjekt(object) \n
            _sogeometrieobjekt(object) \n
            _sostrassenverkehr(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement \n
        - additional attributes to dimensioningIndication

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        self.__set_dimensioningIndication_for_bpfestsetzungenbaugebiet(object)

        # avoid collisison with name attribute of SupplementaryRegulation
        object.pop("name", None)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _sowasserrecht(self, object: dict) -> None:
        r"""Maps attributes of the class SO_Wasserrecht onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _soobjekt(object) \n
            _sogeometrieobjekt(object) \n
            _sowasserrecht(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # avoid collisison with name attribute of SupplementaryRegulation
        object.pop("name", None)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _sowasserwirtschaft(self, object: dict) -> None:
        r"""Maps attributes of the class SO_Wasserwirtschaft onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _soobjekt(object) \n
            _sogeometrieobjekt(object) \n
            _sowasserwirtschaft(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # avoid collisison with name attribute of SupplementaryRegulation
        object.pop("name", None)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _sobaubeschraenkung(self, object: dict) -> None:
        r"""Maps attributes of the class SO_Baubeschraenkung onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _soobjekt(object) \n
            _sogeometrieobjekt(object) \n
            _sobaubeschraenkung(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # avoid collisison with name attribute of SupplementaryRegulation
        object.pop("name", None)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _sobodenschutzrecht(self, object: dict) -> None:
        r"""Maps attributes of the class SO_Bodenschutzrecht onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _soobjekt(object) \n
            _sogeometrieobjekt(object) \n
            _sobodenschutzrecht(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # avoid collisison with name attribute of SupplementaryRegulation
        object.pop("name", None)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _sodenkmalschutzrecht(self, object: dict) -> None:
        r"""Maps attributes of the class SO_Denkmalschutzrecht onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _soobjekt(object) \n
            _sogeometrieobjekt(object) \n
            _sodenkmalschutzrecht(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # avoid collisison with name attribute of SupplementaryRegulation
        object.pop("name", None)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _soforstrecht(self, object: dict) -> None:
        r"""Maps attributes of the class SO_Forstrecht onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _soobjekt(object) \n
            _sogeometrieobjekt(object) \n
            _soforstrecht(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # avoid collisison with name attribute of SupplementaryRegulation
        object.pop("name", None)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _sogelaendemorphologie(self, object: dict) -> None:
        r"""Maps attributes of the class SO_Gelaendemorphologie onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _soobjekt(object) \n
            _sogeometrieobjekt(object) \n
            _sogelaendemorphologie(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # avoid collisison with name attribute of SupplementaryRegulation
        object.pop("name", None)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _soflaechenobjekt(self, object: dict) -> None:
        r"""Maps attributes of the class SO_Flaechenobjekt onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _soobjekt(object) \n
            _soflaechenobjekt(object) \n

        The transformation includes the mappings: \n
        - position to geometry \n
        Based on the value of flaechenschluss, which gets mapped to the temporary dictionary
        mapping, together with the value ebene, it is determined wether the class object
        gets mapped to SupplementaryRegulation or ZoningElement.

        Args:
            object (dict): plan
        """
        # pflichtattribute
        object["geometry"] = object.pop("position")

        # voidable attribute
        object.setdefault("mapping", {})
        object.get("mapping")["flaechenschluss"] = object.pop("flaechenschluss")
        self.__xpobject_decision_rule(object)

    def _sogebiet(self, object: dict) -> None:
        r"""Maps attributes of the class SO_Gebiet onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _soobjekt(object) \n
            _soflaechenobjekt(object) \n
            _sogebiet(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _sosichtflaeche(self, object: dict) -> None:
        r"""Maps attributes of the class SO_Sichtflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _soobjekt(object) \n
            _soflaechenobjekt(object) \n
            _sosichtflaeche(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _sotextabschnittflaeche(self, object: dict) -> None:
        r"""Maps attributes of the class SO_Textabschnittflaeche onto either SupplementaryRegulation or ZoningElement.

        This mapping is applied in succesion, i.e.

        Example:
            _xpobjekt(object) \n
            _soobjekt(object) \n
            _soflaechenobjekt(object) \n
            _sotextabschnittflaeche(object) \n

        The transformation includes the mappings: \n
        - supplementaryRegulation and specificSupplementaryRegulation in case of SupplementaryRegulation \n
        - hilucsLandUse and specificLandUse in case of ZoningElement

        Args:
            object (dict): plan
        """
        self.__wrapper_set_based_on_decision_rule(object)

        # benötigte INSPIRE attribute
        self.__set_VoidReasonValue_fromlist(object, object["featuretype"])

    def _xppraesentationsobjekt(self, object: dict) -> None:
        """Applies transformation for XP_Praesentationsobjekt.

        There are no INSPIRE objects equivalent to XP_Praesentationsobjekt,
        so it is ignored.

        Args:
            object (dict): XP_Praesentationsobjekt
        """
        # no INSPIRE mapping possible: skip
        object.clear()

    def _xpppo(self, object: dict) -> None:
        """Applies transformation for XP_PPPO.

        There are no INSPIRE objects equivalent to XP_PPPO,
        so it is ignored.

        Args:
            object (dict): XP_PPPO
        """
        # no INSPIRE mapping possible: skip
        object.clear()

    def _xplpo(self, object: dict) -> None:
        """Applies transformation for XP_PLPO.

        There are no INSPIRE objects equivalent to XP_PLPO,
        so it is ignored.

        Args:
            object (dict): XP_PLPO
        """
        # no INSPIRE mapping possible: skip
        object.clear()

    def _xpfpo(self, object: dict) -> None:
        """Applies transformation for XP_PFPO.

        There are no INSPIRE objects equivalent to XP_PFPO,
        so it is ignored.

        Args:
            object (dict): XP_PFPO
        """
        # no INSPIRE mapping possible: skip
        object.clear()

    def _xppto(self, object: dict) -> None:
        """Applies transformation for XP_PPTO.

        There are no INSPIRE objects equivalent to XP_PPTO,
        so it is ignored.

        Args:
            object (dict): XP_PPTO
        """
        # no INSPIRE mapping possible: skip
        object.clear()

    def _xplto(self, object: dict) -> None:
        """Applies transformation for XP_PLTO.

        There are no INSPIRE objects equivalent to XP_PLTO,
        so it is ignored.

        Args:
            object (dict): XP_PLTO
        """
        # no INSPIRE mapping possible: skip
        object.clear()

    def _xpnutzungsschablone(self, object: dict) -> None:
        """Applies transformation for XP_Nutzungsschablone.

        There are no INSPIRE objects equivalent to XP_Nutzungsschablone,
        so it is ignored.

        Args:
            object (dict): XP_Nutzungsschablone
        """
        # no INSPIRE mapping possible: skip
        object.clear()
