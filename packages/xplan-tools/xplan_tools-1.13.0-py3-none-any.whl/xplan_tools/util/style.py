import logging
import re
from copy import deepcopy
from typing import TYPE_CHECKING, Any

from pydantic import AnyUrl
from roman import toRoman

from xplan_tools.model import model_factory
from xplan_tools.resources.styles import RULES

if TYPE_CHECKING:
    from xplan_tools.model.base import BaseFeature

logger = logging.getLogger(__name__)


def add_style_properties_to_feature(
    obj: "BaseFeature",
    ref_obj: "BaseFeature",
    to_text: bool = False,
    always_populate_schriftinhalt: bool = False,
) -> "BaseFeature":
    """Add styling properties to presentational objects.

    This method parses object (dientZurDarstellungVon) and property (art) references from
    presentational objects and derives styling information (stylesheetId, schriftinhalt)
    based on a set of defined rules.

    Args:
        to_text: Whether to convert symbolic presentational objects to textual ones. Defaults to False.
        always_populate_schriftinhalt: Populate `schriftinhalt` even if a rule has no text template.
    """
    uom_map = {"m2": "m²", "m3": "m³", "grad": "°"}

    def parse_art(ref_obj: "BaseFeature", art: str) -> dict:
        def parse_value(value: Any) -> dict:
            if prop_info["stereotype"] == "Measure":
                value = value.value
            if prop_info["typename"] == "Boolean":
                value = str(value).lower()

            if name.startswith("Z"):
                text = toRoman(value)
            elif prop_info["stereotype"] == "Enumeration":
                text = prop_info["enum_info"][value].get(
                    "token",
                    prop_info["enum_info"][value].get(
                        "alias", prop_info["enum_info"][value]["name"]
                    ),
                )
            elif prop_info["stereotype"] == "Measure":
                text = f"{value:n} {uom_map.get(prop_info['uom'], prop_info['uom'])}"
            else:
                text = value

            return {
                "value": value,
                "text": text,
            }

        remove_subindexes = re.sub(r"(/[:\w]*)(\[\d\])", r"\g<1>", art)
        remove_namespace = re.sub(
            r"xplan:", "", remove_subindexes
        )  # xplan:|(.P_|SO_)[a-zA-Z]*\/
        attr, path_index, datatype, sub_attr = re.match(
            r"^(?P<attr>\w*)\[?(?P<index>\d)?]?/?(?P<datatype>\w{2}_\w*)?/?(?P<sub_attr>\w*)?$",
            remove_namespace,
        ).groups()

        if datatype:
            model = model_factory(datatype, ref_obj.get_version())
        else:
            model = ref_obj

        name = attr
        value = getattr(ref_obj, attr)
        if isinstance(value, list):
            index = 0
            if path_index:
                index = max(int(path_index) - 1, 0)
            value = value[index]
        if sub_attr:
            name = sub_attr
            value = getattr(value, sub_attr)

        prop_info = model.get_property_info(name)

        data = {
            "name": name,
            "data": parse_value(value),
            "type": prop_info["typename"],
        }
        return data

    # TODO use for XPlanung v6.1 with addition attribute massstabFaktor
    # def set_scale(obj):
    #     bereich = self.root.get(str(obj.gehoertZuBereich))
    #     plan = self.root.get(str(bereich.gehoertZuPlan))
    #     default_scale = SCALES.get(plan.get_name(), 1000)
    #     actual_scale = (
    #         bereich.erstellungsMassstab or plan.erstellungsMassstab or default_scale
    #     )
    #     if obj.skalierung <= 3:
    #         obj.skalierung = float(obj.skalierung * actual_scale / 1000)

    obj = deepcopy(obj)
    logger.debug(f"Feature {obj.id}: adding style properties")
    version = obj.get_version()
    if to_text and (old_type := obj.get_name()) == "XP_PPO":
        new_type = "XP_PTO"
        obj = model_factory(
            new_type,
            version,
            "xplan",
        ).model_validate(obj.model_dump())
        logger.info(f"Feature {obj.id}: converted {old_type} to {new_type}")
    # TODO use for XPlanung v6.1 with addition attribute massstabFaktor
    # if hasattr(obj, "skalierung"):
    #     set_scale(obj)

    logger.debug(
        f"parsing properties {obj.art} for referenced feature {ref_obj.get_name()} with ID {ref_obj.id}"
    )
    selectors = {}
    for art in obj.art:
        try:
            parsed_art = parse_art(ref_obj, art)
            selectors[parsed_art.pop("name")] = parsed_art
        except Exception:
            logger.error(f"Feature {obj.id}: art '{art}' could not be parsed")
    valid_rules = []
    for rule_id, rule in RULES.items():
        versioned_rule = rule["versions"].get(version, {"selector": {}})
        if isinstance(
            versioned_rule, str
        ):  # use other versioned rule referenced by string
            versioned_rule = rule["versions"][versioned_rule]
        valid = versioned_rule["selector"].keys() == selectors.keys() and (
            all(
                (
                    filter.get("value", None) == ["*"]
                    or selectors.get(attr, {}).get("data", {}).get("value", None)
                    in filter.get("value", False)
                )
                and (
                    selectors.get(attr, {}).get("type", None)
                    == filter.get("type", False)
                )
                for attr, filter in versioned_rule["selector"].items()
            )
            if versioned_rule.get("selector", None)
            else False
        )
        if valid:
            valid_rules.append(rule_id)
            texts = {attr: data["data"]["text"] for attr, data in selectors.items()}
            obj.stylesheetId = AnyUrl(
                f"https://registry.gdi-de.org/codelist/de.xleitstelle.xplanung/XP_StylesheetListe/{rule_id}"
            )
            if (text := versioned_rule.get("text", None)) and hasattr(
                obj, "schriftinhalt"
            ):
                obj.schriftinhalt = text.format(**texts)
            elif always_populate_schriftinhalt and hasattr(obj, "schriftinhalt"):
                obj.schriftinhalt = " ".join(
                    [str(data["data"]["text"]) for data in selectors.values()]
                ).strip()
    if not valid_rules:
        logger.warning(f"No rule found for feature {obj.id}")
        obj.stylesheetId = None
        if hasattr(obj, "schriftinhalt"):
            obj.schriftinhalt = " ".join(
                [str(data["data"]["text"]) for data in selectors.values()]
            ).strip()
            logger.debug(f"Feature {obj.id}: schriftinhalt set to {obj.schriftinhalt}")
        # if all(
        #     data["type"] in ["CharacterString", "Integer", "Decimal", "Length"]
        #     for data in selectors.values()
        # ):
        #     obj.stylesheetId = "81e52187-a33b-4340-9d6e-f25533e01aa3"
        #     if hasattr(obj, "schriftinhalt"):
        #         obj.schriftinhalt = " ".join(
        #             [str(data["data"]["text"]) for data in selectors.values()]
        #         ).strip()
        #         logger.debug(
        #             f"Feature {obj.id}: schriftinhalt set to {obj.schriftinhalt}"
        #         )
        # else:
        #     logger.warning(f"No rule found for feature {obj.id}")
    if len(valid_rules) > 1:
        raise ValueError(f"More than one rules valid: {', '.join(valid_rules)}")
    else:
        logger.debug(f"Feature {obj.id}: stylesheetId set to {obj.stylesheetId}")
    return obj
