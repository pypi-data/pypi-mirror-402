r"""Module, containing the transformation classes.

- Transform_54_60  - version upgrade from XPlan 5.* to XPlan 6.0
- Transform_6x_plu - transforming Xplan 6.* objects to INSPIRE PLU 4.0
- Transform_XPlan_Versions - Base class for shared logic for the migration between XPlanung versions
- Transform_41_54  - version upgrade from XPlan 4.* to XPlan 5.4

Example:
    Transformations for a collection ob XPlan objects can be chained like this \n
    collection = Transform_54_60(collection).transform() \n
    collection = Transform_6x_plu(collection).transform() \n
    Thus, allowing a direct transformation for Xplan 5.* to INSPIRE PLU 4.0 in the
    final collection object
"""

import inspect
import logging
import multiprocessing
import warnings
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Tuple, Union
from uuid import UUID

import pandas as pd
from pydantic import ValidationError

import xplan_tools.model.appschema.xplan60
import xplan_tools.model.appschema.xplan61
from xplan_tools.model import model_factory
from xplan_tools.model.appschema.xplan61 import XPBereich, XPObjekt
from xplan_tools.model.base import BaseCollection, BaseFeature
from xplan_tools.transform.migrate_60_61 import rules_60_61

from .migrate_6x_plu import rules_6x_plu
from .migrate_41_54 import rules_41_54
from .migrate_54_60 import rules_54_60

logger = logging.getLogger(__name__)

warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module="openpyxl.*",
)


class Transform_6x_plu(rules_6x_plu):
    """Transformer class for Xplan 6.* to INSPIRE PLU 4.0.

    This class applies the methods, inherited from rules_6x_plu, in succession
    to map and transform attributes from XPlan to one or more INSPIRE PLU objects
    """

    def __init__(self, collection: BaseCollection, inspire_id_ns: str) -> None:
        """__init__ Initialization of transformer.

        Args:
            collection (BaseCollection): collection of XPlan objects
            inspire_id_ns: the namespace uri to use in the INSPIRE Identifier
        """
        super().__init__(inspire_id_ns)

        def __load_mapping_table(
            feature_type: Literal["BP", "FP", "RP", "SO", "XP"],
            plu_class: Literal["SupplementaryRegulation", "ZoningElement"],
        ) -> pd.DataFrame:
            """Loads mapping tables, used for attributes specific to either SupplementaryRegulation or ZoningElement.

            SupplementaryRegulation and ZoningElement have some mandatory attributes,
            that depend on individuall attributes, specific to each XPlan class under
            consideration. These attributes are listed in mapping tables, which are set
            during instanciation of this class, trough this method.

            Args:
                feature_type (Literal["BP", "FP", "RP", "SO"]): specifies the input type of XPlan
                plu_class (Literal["SupplementaryRegulation", "ZoningElement"]): specifies the output INSPIRE PLU type

            Returns:
                pd.DataFrame: mapping table from feature type to plu_class for the attributes under consideration
            """
            script_dir = Path(__file__).parent

            match plu_class:
                case "SupplementaryRegulation":
                    file_path = f"{script_dir}/mappingtables/XPlanToINSPIRE-SupplementaryRegulation_2_6_2025-10-08.xlsx"
                case "ZoningElement":
                    file_path = f"{script_dir}//mappingtables/XPlanToINSPIRE-ZoningElement_2_6_2025-10-08.xlsx"

            if feature_type == "XP":
                return None
            else:
                sheetname_map = {
                    "BP": "BPlanToINSPIRE",
                    "FP": "FPlanToINSPIRE",
                    "RP": "RPlanToINSPIRE",
                    "SO": "SoPlanToINSPIRE",
                }
                df = pd.read_excel(
                    file_path,
                    dtype="str",
                    index_col="XPlanung Klasse",
                    sheet_name=sheetname_map.get(feature_type),
                )
                df.index = df.index.str.lower()
                df.index = df.index.str.replace("_", "")
                df.index.name = "XPlanungKlasse"
                df = df.rename(columns={"XPlanung Attribut": "XPlanungAttribut"})
                return df

        def __get_mappable_features(version: Literal["6.0", "6.1"]) -> list:
            """Returns a list of all xplan classes that can be transformed to INSPIRE PLU.

            The basis for extraction of classes are
            - the module xplan_tools.model.xplan60 or xplan_tools.model.xplan61 for the classes inhering from base classes XPPlan, XPBereich, XPAbstraktesPraesentationsobjekt
            - the official mapping table https://xleitstelle.de/xplanung/transformation-inspire/releases?fid=1731#block-bootstrap-xleitstelle-page-title for classes inheriting from base class XPObjekt

            Returns:
                list: list of mappable xplan classes
            """
            if version == "6.0":
                base_classes = [
                    xplan_tools.model.appschema.xplan60.XPPlan,
                    xplan_tools.model.appschema.xplan60.XPBereich,
                    xplan_tools.model.appschema.xplan60.XPAbstraktesPraesentationsobjekt,
                ]
                model_appschema = xplan_tools.model.appschema.xplan60
            elif version == "6.1":
                base_classes = [
                    xplan_tools.model.appschema.xplan61.XPPlan,
                    xplan_tools.model.appschema.xplan61.XPBereich,
                    xplan_tools.model.appschema.xplan61.XPAbstraktesPraesentationsobjekt,
                ]
                model_appschema = xplan_tools.model.appschema.xplan61

            all_classes = inspect.getmembers(
                model_appschema,
                inspect.isclass,
            )

            derived_classes = [
                name
                for name, cls in all_classes
                if any(issubclass(cls, base) for base in base_classes)
                and cls not in base_classes
                and not name.startswith("LP")
            ]

            script_dir = Path(__file__).parent
            file_path = (
                f"{script_dir}/mappingtables/XPlanToINSPIREFeatures_2_6_2025-10-08.xlsx"
            )
            xpobject_list = pd.read_excel(
                file_path, index_col="XPlanung Feature", sheet_name="FeatureListe"
            ).index.to_list()

            derived_classes.append("XPTextAbschnitt")
            derived_classes.append("XPBegruendungAbschnitt")
            derived_classes.extend([xpo.replace("_", "") for xpo in xpobject_list])

            return derived_classes

        self.collection = collection
        self.from_version = self.collection.version
        self.to_version = "plu"

        self.voidreasonvalue = {
            "nilReason": "http://inspire.ec.europa.eu/codelist/VoidReasonValue/Unpopulated"
        }

        mapping_tables_SR = {}
        mapping_tables_ZE = {}
        for type in ["BP", "FP", "RP", "SO"]:
            mapping_tables_SR[type] = __load_mapping_table(
                type, "SupplementaryRegulation"
            )
            mapping_tables_ZE[type] = __load_mapping_table(type, "ZoningElement")
        self.mapping_tables_SR = mapping_tables_SR
        self.mapping_tables_ZE = mapping_tables_ZE

        self.mappable_features = __get_mappable_features(self.from_version)

        self.dict = {}
        self.member_restriction_dict = {}

    def transform_model(
        self,
        model: BaseFeature,
        mapping_table_SR: Union[pd.DataFrame, None] = None,
        mapping_table_ZE: Union[pd.DataFrame, None] = None,
    ) -> dict:
        """Recursively applies all possible transformations for an Xplan object.

        Based on the underlying model, this method extracts all parent classes
        and goes recursively through all available mappings and transformations
        in order, starting from the most abstract base class

        Args:
            model (BaseFeature): feature to be transformed
            mapping_table_SR (Union[pd.DataFrame, None], optional): Mapping table for attributes specific to SupplementaryRegulation. Defaults to None.
            mapping_table_ZE (Union[pd.DataFrame, None], optional): Mapping table for attrobutes specific to ZoningElement. Defaults to None.

        Returns:
            dict: transformed feature
        """

        def transform_base(model: BaseFeature, object: dict) -> None:
            for base in filter(
                lambda x: issubclass(x, BaseFeature), reversed(model.__class__.__mro__)
            ):
                if transformer := getattr(self, f"_{base.__name__.lower()}", None):
                    transformer(object)
                    if not object:
                        return

        def transform_property(value: Any) -> Any:
            match value:
                case BaseFeature():
                    return self.transform_model(value)
                case Enum():
                    if transformer := getattr(
                        self, f"_{value.__class__.__name__.lower()}", None
                    ):
                        return transformer(value.value)
                    else:
                        return value.value
                case bool():
                    return value
                case _:
                    return str(value)

        object = {}

        if isinstance(mapping_table_SR, pd.Series) | isinstance(
            mapping_table_SR, pd.DataFrame
        ):
            object["mapping_table_SR"] = mapping_table_SR
        if isinstance(mapping_table_ZE, pd.Series) | isinstance(
            mapping_table_ZE, pd.DataFrame
        ):
            object["mapping_table_ZE"] = mapping_table_ZE

        for name, value in model:
            match value:
                case None:
                    continue
                case list():
                    object[name] = [transform_property(item) for item in value]
                case _:
                    object[name] = transform_property(value)
            if isinstance(value, BaseFeature):
                transform_base(value, object[name])

        transform_base(model, object)

        # TODO find better solution for nan values
        if object.get("specificLandUse", None):
            object["specificLandUse"] = [
                item for item in object["specificLandUse"] if str(item) != "nan"
            ] or None

        return object

    def __get_mapping_tables(
        self, mapping_idx: str, mapping_type: str
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Returns potential mappings for attributes specific to SupplementaryRegulation and/or ZoningElement.

        Args:
            mapping_idx (str): index for mapping tables, derived from the respective XPlan class name
            mapping_type (str): type of XPlan object

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: mapping tables for the specified object, for both SupplementaryRegulation and ZoningElement (if available)
        """
        if mapping_type == "XP":
            return (None, None)
        mapping_table_SR = (
            self.mapping_tables_SR[mapping_type].loc[[mapping_idx]]
            if mapping_idx in self.mapping_tables_SR[mapping_type].index
            else None
        )
        mapping_table_ZE = (
            self.mapping_tables_ZE[mapping_type].loc[[mapping_idx]]
            if mapping_idx in self.mapping_tables_ZE[mapping_type].index
            else None
        )

        return (mapping_table_SR, mapping_table_ZE)

    def feature_transform(self, feature) -> None:
        """Performs transformation on each individual feature by applying all (Feature-/Data-Enum-)Type-specific changes to the FeatureCollection.

        The method checks if the input object is inside a list of transformable objects
        (to be changed in later versions). If so, it sets the mapping tables, needed for class
        specific attributes of SupplementaryRegulation and ZoningElement
        The actual transformation takes place. Also, the method checks if an object is to be
        skipped (in case the object is not mappable to INSPIRE).
        If a mapping occured to OfficialDocumentation, the newly created documents are removed from
        the transformed object. Both are added individually to the output dict after a
        pydantic model validation.

        Args:
            feature (_type_): concrete XPlan object
        """
        if feature.get_name().replace("_", "") in self.mappable_features:
            logger.debug(
                f"Map feature type {feature.get_name()} with id {feature.id}..."
            )

            mapping_idx = feature.get_name().replace("_", "").lower()
            mapping_type = feature.get_name()[:2].upper()
            mapping_table_SR, mapping_table_ZE = self.__get_mapping_tables(
                mapping_idx, mapping_type
            )

            object = self.transform_model(feature, mapping_table_SR, mapping_table_ZE)

            if not object:
                if "_Bereich" in feature.get_name():
                    logger.info(
                        f"Bereich object {feature.get_name()} with id {feature.id} is accounted for in its respective plan: skip"
                    )
                else:
                    logger.info(
                        f"No transformation for {feature.get_name()} with id {feature.id}: skip"
                    )
                return

            object.pop("mapping", None)
            object.pop("mapping_table_SR", None)
            object.pop("mapping_table_ZE", None)

            if object.get("officialDocument_list", None):
                for document in object["officialDocument_list"]:
                    try:
                        self.dict[document["id"]] = model_factory(
                            "OfficialDocumentation", "4.0", "plu"
                        ).model_validate(document)
                    except ValidationError:
                        logger.error(ValidationError, exc_info=True)
                object.pop("officialDocument_list")

            map_featuretype = object.pop("featuretype", None)

            if map_featuretype == "SupplementaryRegulation":
                plan_id = object.get("plan")
                if plan_id not in self.member_restriction_dict.keys():
                    self.member_restriction_dict[plan_id] = {
                        "member": [],
                        "restriction": [],
                    }
                self.member_restriction_dict[plan_id]["restriction"].append(
                    UUID(feature.id)
                )
            if map_featuretype == "ZoningElement":
                plan_id = object.get("plan")
                if plan_id not in self.member_restriction_dict.keys():
                    self.member_restriction_dict[plan_id] = {
                        "member": [],
                        "restriction": [],
                    }
                self.member_restriction_dict[plan_id]["member"].append(UUID(feature.id))
            try:
                self.dict[feature.id] = model_factory(
                    map_featuretype, "4.0", "plu"
                ).model_validate(object)
            except ValidationError:
                logger.error(ValidationError, exc_info=True)
            logger.debug(f"...onto {map_featuretype}")

        else:
            logger.warning(
                f"Transformation for {feature.get_name()} not yet implemented: Skip"
            )

    def parallel_transform(self, features) -> None:
        """Option for parallel execution via multiprocessing library.

        Args:
            features (_type_): collection of features to be transformed
        """
        with multiprocessing.Pool() as pool:
            pool.map(self.feature_transform, features)

    def transform(self) -> BaseCollection:
        """Performs transformation by applying all (Feature-/Data-Enum-)Type-specific changes to the FeatureCollection.

        Returns:
            BaseCollection: collection of transformed INSPIRE PLU objects
        """
        logger.info("Transformation XPlanung 6.0 -> INSPIRE PLU started")

        features = self.collection.features.values()

        for feature in features:
            logger.debug(f"Current feature: {feature.get_name()} with id {feature.id}")
            self.feature_transform(feature)

        logger.debug(
            "Map ZoningElements and SupplementaryRegulations to their respective plans"
        )
        for plan_id in self.member_restriction_dict.keys():
            member_list = self.member_restriction_dict.get(plan_id).get("member")
            restriction_list = self.member_restriction_dict.get(plan_id).get(
                "restriction"
            )

            self.dict[str(plan_id)].member = member_list if member_list else None
            self.dict[str(plan_id)].restriction = (
                (restriction_list) if restriction_list else None
            )

        logger.info("Transformation XPlanung 6.0 -> INSPIRE PLU complete")

        return BaseCollection(
            features=dict(self.dict),
            srid=self.collection.srid,
            version="4.0",
            appschema="plu",
        )


class Transform_XPlan_Versions:
    """Base class for shared logic for the migration between XPlanung versions. Should be subclassed along with the version specific 'rules_*'."""

    def __init__(self, collection: BaseCollection, to_version: str):
        """Initialize the base class for migration.

        Args:
            collection (BaseCollection): Collection of XPlan objects
            to_version (str): The destination version.
        """
        self.collection = collection
        self.to_version = to_version
        self.dict = {}

    def transform_model(self, model: BaseFeature) -> dict:
        """Recursively applies all possible transformations for an XPlan object.

        Based on the underlying model, this method extracts all parent classes
        and goes recursively through all available mappings and transformations
        in order, starting from the most abstract base class

        Args:
            model (BaseFeature): feature to be transformed

        Returns:
            dict: transformed feature
        """
        object = {}
        if getattr(model, "id", None):
            object["featuretype"] = model.get_name()

        for name, value in model:
            if value is None:
                continue
            prop_info = model.get_property_info(name)
            match prop_info["stereotype"]:
                case "DataType":
                    transformer = self.transform_model
                case "Enumeration":
                    transformer = getattr(
                        self, f"_{prop_info['typename'].replace('_', '').lower()}", None
                    )
                case "Association":
                    transformer = str
                case _:
                    transformer = None
            if transformer:
                object[name] = (
                    [transformer(item) for item in value]
                    if prop_info["list"]
                    else transformer(value)
                )
            else:
                object[name] = value

        for base in filter(
            lambda x: issubclass(x, BaseFeature), reversed(model.__class__.__mro__)
        ):
            if transformer := getattr(self, f"_{base.__name__.lower()}", None):
                transformer(object)

        return object

    def transform(self) -> BaseCollection:
        """Performs transformation by applying all (Feature-/Data-Enum-)Type-specific changes to the FeatureCollection.

        Returns:
            BaseCollection: collection of transformed INSPIRE PLU objects
        """
        logger.info(f"Transformation to XPlanung {self.to_version} started")

        for feature in self.collection.features.values():
            logger.debug(f"Current feature: {feature.get_name()} with id {feature.id}")
            if object := self.transform_model(feature):
                self.dict[feature.id] = model_factory(
                    object.pop("featuretype"), self.to_version, "xplan"
                ).model_validate(object)

        transformed_collection = BaseCollection(
            features=self.dict,
            srid=self.collection.srid,
            version=self.to_version,
            appschema=self.collection.appschema,
        )
        logger.info(f"Transformation to XPlanung {self.to_version} complete")

        return transformed_collection


class Transform_41_54(rules_41_54, Transform_XPlan_Versions):
    """Class for the migration from XPlanung version 4.x to 5.4."""

    def __init__(self, collection):
        """Initialize the class for migration from XPlanung 4.x to 5.4.

        Args:
            collection (BaseCollection): Collection of XPlan objects
        """
        super().__init__(collection, to_version="5.4")


class Transform_54_60(rules_54_60, Transform_XPlan_Versions):
    """Class for the migration from XPlanung version 5.x to 6.0."""

    def __init__(self, collection):
        """Initialize the class for migration from XPlanung 5.x to 6.0.

        Args:
            collection (BaseCollection): Collection of XPlan objects
        """
        super().__init__(collection, to_version="6.0")


class Transform_60_61(rules_60_61, Transform_XPlan_Versions):
    """Class for the migration from XPlanung version 6.0 to 6.1."""

    def __init__(self, collection):
        """Initialize the class for migration from XPlanung 6.0 to 6.1.

        Args:
            collection (BaseCollection): Collection of XPlan objects
        """
        super().__init__(collection, to_version="6.1")

    def set_associations(self) -> BaseCollection:
        """Infers associations for XP_TextAbschnitt and XP_BegruendungAbschnitt form Plan, Bereich, Fachobjekte.

        XP_TextAbschnitt and XP_BegruendungAbschnitt have attributes of stereotype association in v6.1 that can be inferred
        from their parent objects Plan, Bereich and Fachobjekte. This method goes through all objects in the collection
        and sets the associations accordingly, if available.

        Args:
            collection (BaseCollection): Collection of XPlan objects
        """
        for plan in filter(
            lambda x: x.get_name().endswith("Plan"), self.collection.features.values()
        ):
            if plan.texte is not None:
                for text_id in plan.texte:
                    self.collection.features[str(text_id)].gehoertZuPlan = UUID(plan.id)
            if plan.begruendungsTexte is not None:
                for begruendung_id in plan.begruendungsTexte:
                    self.collection.features[str(begruendung_id)].gehoertZuPlan = UUID(
                        plan.id
                    )

        for bereich in filter(
            lambda x: issubclass(x.__class__, XPBereich),
            self.collection.features.values(),
        ):
            if bereich.texte is not None:
                for text_id in bereich.texte:
                    if self.collection.features[str(text_id)].gehoertZuBereich is None:
                        self.collection.features[str(text_id)].gehoertZuBereich = [
                            UUID(bereich.id)
                        ]
                    elif (
                        UUID(bereich.id)
                        not in self.collection.features[str(text_id)].gehoertZuBereich
                    ):
                        self.collection.features[str(text_id)].gehoertZuBereich.append(
                            UUID(bereich.id)
                        )

        for object in filter(
            lambda x: issubclass(x.__class__, XPObjekt),
            self.collection.features.values(),
        ):
            if object.refTextInhalt is not None:
                for text_id in object.refTextInhalt:
                    if self.collection.features[str(text_id)].gehoertZuObjekt is None:
                        self.collection.features[str(text_id)].gehoertZuObjekt = [
                            UUID(object.id)
                        ]
                    elif (
                        UUID(object.id)
                        not in self.collection.features[str(text_id)].gehoertZuObjekt
                    ):
                        self.collection.features[str(text_id)].gehoertZuObjekt.append(
                            UUID(object.id)
                        )
            if object.refBegruendungInhalt is not None:
                for begruendung_id in object.refBegruendungInhalt:
                    if (
                        self.collection.features[str(begruendung_id)].gehoertZuObjekt
                        is None
                    ):
                        self.collection.features[
                            str(begruendung_id)
                        ].gehoertZuObjekt = [UUID(object.id)]
                    elif (
                        UUID(object.id)
                        not in self.collection.features[
                            str(begruendung_id)
                        ].gehoertZuObjekt
                    ):
                        self.collection.features[
                            str(begruendung_id)
                        ].gehoertZuObjekt.append(UUID(object.id))

        return self.collection
