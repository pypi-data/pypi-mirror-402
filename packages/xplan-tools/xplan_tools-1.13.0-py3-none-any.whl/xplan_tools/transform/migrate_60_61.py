"""Module, containing the explicit transformation and mapping rules for XPlan 6.0 to XPlan 6.1."""


class rules_60_61:
    """Base class, containing transformations for all XPlan Data types for version 6.0 to 6.1."""

    def _bpdachgestaltung(self, object: dict) -> None:
        for attr in ["dachform", "detaillierteDachform", "hoehenangabe"]:
            if object.get(attr, None):
                object[attr] = [object[attr]]

    def _sosichtflaeche(self, object: dict) -> None:
        if v := object.get("geschwindigkeit", None):
            object["geschwindigkeit"] = {"value": v.value, "uom": "km/h"}
