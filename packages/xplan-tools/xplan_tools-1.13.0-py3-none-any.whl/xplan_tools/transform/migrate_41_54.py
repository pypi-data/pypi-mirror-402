"""Module, containing the explicit transformation and mapping rules for XPlan 4.* to XPlan 5.4."""

import logging
import sys

from xplan_tools.model.appschema.xplan41 import XPBereich

logger = logging.getLogger(__name__)


class rules_41_54:
    """Migration rules for XPlanung from version 4.1 to 5.4."""

    def __prop_warn(self, object: dict, property: str, message: str | None = None):
        feature_id = object.get("id")
        if message:
            if feature_id:
                logger.warning(f"Feature {feature_id} Attribut {property}: {message}")
            else:
                logger.warning(f"Attribut {property}: {message}")
        else:
            if feature_id:
                logger.warning(
                    f"Feature {feature_id}: manuelle Prüfung für {property} erforderlich"
                )
            else:
                logger.warning(f"Manuelle Prüfung für {property} erforderlich")

    def __prop_warn_rp(self, object: dict, message: str | None = None):
        if message:
            logger.error(f"{object['featuretype']}: {message}")
        else:
            logger.warning(
                f"Feature {object['id']}: {object['featuretype']} kann nicht transformiert werden"
            )

    def __prop_error(self, object: dict, property: str, message: str | None = None):
        feature_id = object.get("id")
        if message:
            if feature_id:
                logger.error(f"Feature {feature_id} Attribut {property}: {message}")
            else:
                logger.error(f"Attribut {property}: {message}")
        else:
            if object.get("id", None):
                logger.error(
                    f"Feature {object['id']}: Transformation von {property} nicht möglich"
                )
            else:
                logger.error(f"Transformation von {property} nicht möglich")

    def __attr_to_externe_referenz(
        self, object: dict, mappings: list[tuple[str, str]]
    ) -> None:
        """Migrate an attribute[0..*] to externeReferenz with required attribute 'typ' and featuretype XP_SpezExterneReferenz."""
        transformed_refs = []
        for old_attr, reftype in mappings:
            value = object.pop(old_attr, None)
            if value is None:
                continue

            # Normalize to list
            refs = value if isinstance(value, list) else [value]

            for ref in refs:
                if ref is not None:
                    ref["typ"] = reftype
                    transformed_refs.append(ref)

        if transformed_refs:
            object.setdefault("externeReferenz", []).extend(transformed_refs)

    def __merge_optional_fields(
        self, object: dict, from_keys: list[str], to_key: str
    ) -> None:
        values = []
        for key in from_keys:
            value = object.pop(key, None)
            if value is not None:
                if isinstance(value, list):
                    values.extend(value)
                else:
                    values.append(value)
        if values:
            object.setdefault(to_key, []).extend(values)

    def __attr_to_list(self, object: dict, attr: str) -> None:
        value = object.pop(attr, None)
        if value is not None:
            object[attr] = [value]

    def __migrate_bereich_ref(self, object: dict, plan_type: str) -> None:
        attr = f"gehoertZu{plan_type}_Bereich"
        bereiche = object.pop(attr, None)
        if bereiche:
            if object.get("gehoertZuBereich") is not None:
                self.__prop_warn(
                    object,
                    attr,
                    "Nachrichtliche Bereiche konnten nicht übernommen werden.",
                )
            object["gehoertZuBereich"] = bereiche[0]
            if len(bereiche) > 1:
                self.__prop_warn(
                    object,
                    attr,
                    "Mehrere Bereiche referenziert, nur der erste übernommen.",
                )

    def _xpobjekt(self, object: dict) -> None:
        bereiche = object.pop("gehoertNachrichtlichZuBereich", None)
        if bereiche:
            object["gehoertZuBereich"] = bereiche[0]
        self.__attr_to_externe_referenz(
            object, [("informell", "9999"), ("rechtsverbindlich", "9998")]
        )
        object.pop("textSchluessel", None)
        object.pop("textSchluesselBegruendung", None)

    def _xpbereich(self, object: dict) -> None:
        object["erstellungsMassstab"] = object.pop("erstellungsMasstab", None)
        """ For each object in nachrichtlich: Move it to planinhalt,
        set its rechtscharakter to the value for "NachrichtlicheUebernahme" """
        nachrichtlich = object.pop("nachrichtlich", [])
        if nachrichtlich:
            object.setdefault("planinhalt", []).extend(nachrichtlich)
            for ref in nachrichtlich:
                inhalt = self.collection.features[ref]
                if inhalt.__class__.__name__.startswith("LP"):
                    inhalt.status = "3000"
                else:
                    inhalt.rechtscharakter = "2000"

        # Map deleted values of 'bedeutung' to 'detaillierteBedeutung', while setting 'bedeutung' to '9999'.
        bedeutung = object.get("bedeutung", None)
        # Override these values
        deleted = {
            "1000",
            "1500",
            "1650",
            "1700",
            "2000",
            "2500",
            "3000",
            "3500",
            "4000",
        }
        if bedeutung in deleted:
            # Get enumDescription from the Pydantic schema
            try:
                field_info = XPBereich.model_fields["bedeutung"].json_schema_extra
                enum_description = field_info.get("enumDescription", {})
                name = enum_description.get(bedeutung, {}).get("name")
            except Exception:
                name = None

            if name:
                object["detaillierteBedeutung"] = name

            object["bedeutung"] = "9999"

    def _xprasterplanbasis(self, object: dict) -> None:
        object["featuretype"] = "XP_Rasterdarstellung"

    def _xpplan(self, object: dict) -> None:
        object.pop("xPlanGMLVersion", None)
        self.__attr_to_externe_referenz(
            object,
            [
                ("informell", "9999"),
                ("rechtsverbindlich", "9998"),
                ("refBeschreibung", "1000"),
                ("refBegruendung", "1010"),
                ("refLegende", "1020"),
                ("refRechtsplan", "1030"),
                ("refPlangrundlage", "1040"),
            ],
        )
        object.pop("refExternalCodeList", None)

        if not object.get("name", None):
            self.__prop_error(object, "name", "name ist ein Pflichtattribut")

        if not object.get("raeumlicherGeltungsbereich", None):
            self.__prop_error(
                object,
                "raeumlicherGeltungsbereich",
                "raeumlicherGeltungsbereich ist ein Pflichtattribut",
            )

    def _xptextabschnitt(self, object: dict) -> None:
        for value in self.collection.features.values():
            # check plan type
            class_name = value.__class__.__name__
            if class_name.endswith("Plan"):
                plantype = class_name[:2]
                break
        new_ftype = f"{plantype}_TextAbschnitt"
        object["featuretype"] = new_ftype
        if object.get("rechtscharakter") in (None, "9999"):
            if plantype in {"BP", "FP"}:
                object["rechtscharakter"] = "1000"
            elif plantype in {"LP", "SO", "RP"}:
                object["rechtscharakter"] = "9998"

    def _xpbesonderezweckbestimmungverentsorgung(self, value: str) -> str:
        mapping = {
            "10010": "100010",
            "28000": "10003",
            "28001": "10002",
            "28002": "10007",
            "28003": "10004",
            "28004": "10005",
        }
        return mapping.get(value, value)

    def _xpexternereferenz(self, object: dict) -> None:
        if object.get("art") is not None and object["art"] not in [
            "Dokument",
            "PlanMitGeoreferenz",
        ]:
            object.pop("art")
            self.__prop_warn(
                object,
                "art",
                "Zulässige Werte für das Attribut XP_ExterneReferenz.art sind 'Dokument' und 'PlanMitGeoreferenz'.",
            )

    def _bpplan(self, object: dict) -> None:
        self.__attr_to_externe_referenz(
            object,
            [
                ("refSatzung", "1060"),
                ("refKoordinatenListe", "2000"),
                ("refGrundstuecksverzeichnis", "2100"),
                ("refPflanzliste", "2200"),
                ("refGruenordnungsplan", "2300"),
                ("refUmweltbericht", "1050"),
            ],
        )
        if not object.get("raeumlicherGeltungsbereich"):
            self.__prop_error(
                object, "raeumlicherGeltungsbereich", "Fehlendes Pflichtattribut."
            )

    def _bpbereich(self, object: dict) -> None:
        object["versionBauGBDatum"] = object.pop("versionBauGB", None)
        # Map known versionBauNVO values to versionBauNVOText; Attribute is then removed.
        version = object.get("versionBauNVO")
        mapping = {
            "1000": "Version_1962",
            "2000": "Version_1968",
            "3000": "Version_1977",
            "4000": "Version_1990",
        }
        if version in mapping:
            object["versionBauNVOText"] = mapping[version]
        object.pop("versionBauNVO", None)

        object.setdefault("planinhalt", [])
        if inhaltBPlan := object.pop("inhaltBPlan", None):
            object["planinhalt"].extend(inhaltBPlan)

        if object.pop("rasterAenderung", None):
            self.__prop_warn(
                object,
                "rasterAenderung",
                "Rasterplan_Aenderung wird nicht mehr unterstützt, das Objekt XP_RasterplanAenderung wird nicht übernommen.",
            )

    def _bpobjekt(self, object: dict) -> None:
        self.__migrate_bereich_ref(object, "BP")

        if not object.get("rechtscharakter"):
            object["rechtscharakter"] = "9998"

    def _bpausgleichsflaeche(self, object: dict) -> None:
        self.__merge_optional_fields(
            object, ["weitereMassnahme1", "weitereMassnahme2"], "massnahme"
        )

    def _bpausgleichsmassnahme(self, object: dict) -> None:
        self.__merge_optional_fields(
            object, ["weitereMassnahme1", "weitereMassnahme2"], "massnahme"
        )

    def _bpschutzpflegeentwicklungsflaeche(self, object: dict) -> None:
        self.__merge_optional_fields(
            object, ["weitereMassnahme1", "weitereMassnahme2"], "massnahme"
        )

    def _bpschutzpflegeentwicklungsmassnahme(self, object: dict) -> None:
        self.__merge_optional_fields(
            object, ["weitereMassnahme1", "weitereMassnahme2"], "massnahme"
        )

    def _bpbaugebiet(self, object: dict) -> None:
        object.clear()

    def _bpeinfahrtpunkt(self, object: dict) -> None:
        object.pop("richtung", None)

    def _bpbaugebietsteilflaeche(self, object: dict) -> None:
        self.__attr_to_list(object, "detaillierteDachform")
        self.__attr_to_list(object, "sondernutzung")

        object.pop("BMZmin", None)
        object.pop("BMZmax", None)
        object.pop("BMmin", None)
        object.pop("BMmax", None)

    def _bpbesonderernutzungszweckflaeche(self, object: dict) -> None:
        self.__attr_to_list(object, "detaillierteDachform")
        object.pop("BMZmin", None)
        object.pop("BMZmax", None)
        object.pop("BMmin", None)
        object.pop("BMmax", None)

    def _bpdenkmalschutzensembleflaeche(self, object: dict) -> None:
        object["featuretype"] = "SO_Denkmalschutzrecht"
        object["artDerFestlegung"] = "1000"
        value = object.pop("denkmal", None)
        if value is not None:
            object["name"] = value
        object.pop("textSchluessel", None)
        object.pop("textSchluesselBegruendung", None)
        object.pop("refBegruendungInhalt", None)
        object.pop("wirdAusgeglichenDurchFlaeche", None)
        object.pop("wirdAusgeglichenDurchABE", None)
        object.pop("wirdAusgeglichenDurchSPEMassnahme", None)
        object.pop("wirdAusgeglichenDurchSPEFlaeche", None)
        object.pop("wirdAusgeglichenDurchMassnahme", None)

    def _bpdenkmalschutzeinzelanlage(self, object: dict) -> None:
        object["featuretype"] = "SO_Denkmalschutzrecht"
        object["artDerFestlegung"] = "1100"
        value = object.pop("denkmal", None)
        if value is not None:
            object["name"] = value
        object.pop("textSchluessel", None)
        object.pop("textSchluesselBegruendung", None)
        object.pop("refBegruendungInhalt", None)
        object.pop("wirdAusgeglichenDurchFlaeche", None)
        object.pop("wirdAusgeglichenDurchABE", None)
        object.pop("wirdAusgeglichenDurchSPEMassnahme", None)
        object.pop("wirdAusgeglichenDurchSPEFlaeche", None)
        object.pop("wirdAusgeglichenDurchMassnahme", None)

    def _bperneuerbareenergieflaeche(self, object: dict) -> None:
        object["featuretype"] = "BP_TechnischeMassnahmenFlaeche"
        object["zweckbestimmung"] = "2000"
        object["technischeMassnahme"] = object.pop("technischeMaßnahme", None)

    def _bpluftreinhalteflaeche(self, object: dict) -> None:
        object["featuretype"] = "BP_TechnischeMassnahmenFlaeche"
        object["zweckbestimmung"] = "1000"

    def _bpgemeinbedarfsflaeche(self, object: dict) -> None:
        self.__merge_optional_fields(
            object,
            [
                "weitereZweckbestimmung1",
                "weitereZweckbestimmung2",
                "weitereZweckbestimmung3",
                "weitereZweckbestimmung4",
                "besondereZweckbestimmung",
                "weitereBesondZweckbestimmung1",
                "weitereBesondZweckbestimmung2",
                "weitereBesondZweckbestimmung3",
                "weitereBesondZweckbestimmung4",
            ],
            "zweckbestimmung",
        )

        self.__merge_optional_fields(
            object,
            [
                "weitereDetailZweckbestimmung1",
                "weitereDetailZweckbestimmung2",
                "weitereDetailZweckbestimmung3",
                "weitereDetailZweckbestimmung4",
            ],
            "detaillierteZweckbestimmung",
        )

        object.pop("BMZmin", None)
        object.pop("BMZmax", None)
        object.pop("BMmin", None)
        object.pop("BMmax", None)

    def _bpgemeinschaftsanlagenflaeche(self, object: dict) -> None:
        self.__merge_optional_fields(
            object,
            [
                "weitereZweckbestimmung1",
                "weitereZweckbestimmung2",
                "weitereZweckbestimmung3",
                "weitereZweckbestimmung4",
            ],
            "zweckbestimmung",
        )
        self.__merge_optional_fields(
            object,
            [
                "weitereDetailZweckbestimmung1",
                "weitereDetailZweckbestimmung2",
                "weitereDetailZweckbestimmung3",
                "weitereDetailZweckbestimmung4",
            ],
            "detaillierteZweckbestimmung",
        )

    def _bpgenerischesobjekt(self, object: dict) -> None:
        self.__merge_optional_fields(
            object,
            [
                "weitereZweckbestimmung1",
                "weitereZweckbestimmung2",
                "weitereZweckbestimmung3",
                "weitereZweckbestimmung4",
            ],
            "zweckbestimmung",
        )

    def _bpgruenflaeche(self, object: dict) -> None:
        self.__merge_optional_fields(
            object,
            [
                "weitereZweckbestimmung1",
                "weitereZweckbestimmung2",
                "weitereZweckbestimmung3",
                "weitereZweckbestimmung4",
                "besondereZweckbestimmung",
                "weitereBesondZweckbestimmung1",
                "weitereBesondZweckbestimmung2",
                "weitereBesondZweckbestimmung3",
                "weitereBesondZweckbestimmung4",
            ],
            "zweckbestimmung",
        )

        self.__merge_optional_fields(
            object,
            [
                "weitereDetailZweckbestimmung1",
                "weitereDetailZweckbestimmung2",
                "weitereDetailZweckbestimmung3",
                "weitereDetailZweckbestimmung4",
            ],
            "detaillierteZweckbestimmung",
        )

        object.pop("BMZmin", None)
        object.pop("BMZmax", None)
        object.pop("BMmin", None)
        object.pop("BMmax", None)

    def _bpkennzeichnungsflaeche(self, object: dict) -> None:
        self.__merge_optional_fields(
            object, ["weitereZweckbestimmung"], "zweckbestimmung"
        )

    def _bplandwirtschaft(self, object: dict) -> None:
        self.__merge_optional_fields(
            object,
            [
                "weitereZweckbestimmung1",
                "weitereZweckbestimmung2",
                "weitereZweckbestimmung3",
            ],
            "zweckbestimmung",
        )
        self.__merge_optional_fields(
            object,
            [
                "weitereDetailZweckbestimmung1",
                "weitereDetailZweckbestimmung2",
                "weitereDetailZweckbestimmung3",
            ],
            "detaillierteZweckbestimmung",
        )

    def _bpnebenanlagenflaeche(self, object: dict) -> None:
        self.__merge_optional_fields(
            object,
            [
                "weitereZweckbestimmung1",
                "weitereZweckbestimmung2",
                "weitereZweckbestimmung3",
                "weitereZweckbestimmung4",
            ],
            "zweckbestimmung",
        )
        self.__merge_optional_fields(
            object,
            [
                "weitereDetailZweckbestimmung1",
                "weitereDetailZweckbestimmung2",
                "weitereDetailZweckbestimmung3",
                "weitereDetailZweckbestimmung4",
            ],
            "detaillierteZweckbestimmung",
        )

    def _bprasterplanaenderung(self, object: dict) -> None:
        object.clear()

    def _bpschutzgebiet(self, object: dict) -> None:
        object["featuretype"] = "SO_SchutzgebietNaturschutzrecht"
        object["artDerFestlegung"] = object.pop("zweckbestimmung", None)
        object["detailArtDerFestlegung"] = object.pop(
            "detaillierteZweckbestimmung", None
        )

        object.pop("textSchluessel", None)
        object.pop("textSchluesselBegruendung", None)
        object.pop("refBegruendungInhalt", None)
        object.pop("wirdAusgeglichenDurchFlaeche", None)
        object.pop("wirdAusgeglichenDurchABE", None)
        object.pop("wirdAusgeglichenDurchSPEMassnahme", None)
        object.pop("wirdAusgeglichenDurchSPEFlaeche", None)
        object.pop("wirdAusgeglichenDurchMassnahme", None)

    def _bpspielsportanlagenflaeche(self, object: dict) -> None:
        self.__merge_optional_fields(
            object, ["weitereZweckbestimmung1"], "zweckbestimmung"
        )
        self.__merge_optional_fields(
            object, ["weitereDetailZweckbestimmung1"], "detaillierteZweckbestimmung"
        )

        object.pop("BMZmin", None)
        object.pop("BMZmax", None)
        object.pop("BMmin", None)
        object.pop("BMmax", None)

    def _bpstrassenverkehrsflaeche(self, object: dict) -> None:
        object.pop("BMZmin", None)
        object.pop("BMZmax", None)
        object.pop("BMmin", None)
        object.pop("BMmax", None)

    def _bpverentsorgung(self, object: dict) -> None:
        self.__merge_optional_fields(
            object,
            [
                "weitereZweckbestimmung1",
                "weitereZweckbestimmung2",
                "weitereZweckbestimmung3",
                "besondereZweckbestimmung",
                "weitereBesondZweckbestimmung1",
                "weitereBesondZweckbestimmung2",
                "weitereBesondZweckbestimmung3",
            ],
            "zweckbestimmung",
        )

        self.__merge_optional_fields(
            object,
            [
                "weitereDetailZweckbestimmung1",
                "weitereDetailZweckbestimmung2",
                "weitereDetailZweckbestimmung3",
            ],
            "detaillierteZweckbestimmung",
        )

        object.pop("BMZmin", None)
        object.pop("BMZmax", None)
        object.pop("BMmin", None)
        object.pop("BMmax", None)

    def _bpwaldflaeche(self, object: dict) -> None:
        self.__merge_optional_fields(
            object,
            [
                "weitereZweckbestimmung1",
                "weitereZweckbestimmung2",
            ],
            "zweckbestimmung",
        )
        self.__merge_optional_fields(
            object,
            [
                "weitereDetailZweckbestimmung1",
                "weitereDetailZweckbestimmung2",
            ],
            "detaillierteZweckbestimmung",
        )

    def _bpausgleichsmassnahme(self, object: dict) -> None:
        self.__merge_optional_fields(
            object,
            [
                "weitereMassnahme1",
                "weitereMassnahme2",
            ],
            "massnahme",
        )

    def _bpschutzpflegeentwicklungsmassnahme(self, object: dict) -> None:
        self.__merge_optional_fields(
            object,
            [
                "weitereMassnahme1",
                "weitereMassnahme2",
            ],
            "massnahme",
        )

    def _bpschutzpflegeentwicklungsflaeche(self, object: dict) -> None:
        self.__merge_optional_fields(
            object,
            [
                "weitereMassnahme1",
                "weitereMassnahme2",
            ],
            "massnahme",
        )

    def _bpausgleichsflaeche(self, object: dict) -> None:
        self.__merge_optional_fields(
            object,
            [
                "weitereMassnahme1",
                "weitereMassnahme2",
            ],
            "massnahme",
        )

    def _bpueberbaubaregrundstuecksflaeche(self, object: dict) -> None:
        object.pop("BMZmin", None)
        object.pop("BMZmax", None)
        object.pop("BMmin", None)
        object.pop("BMmax", None)

    def _bpverkehrsflaechebesondererzweckbestimmung(self, object: dict) -> None:
        if object.get("zweckbestimmung"):
            self.__attr_to_list(object, "zweckbestimmung")
        if object.get("detaillierteZweckbestimmung"):
            self.__attr_to_list(object, "detaillierteZweckbestimmung")
        object.pop("BMZmin", None)
        object.pop("BMZmax", None)
        object.pop("BMmin", None)
        object.pop("BMmax", None)

    def _bpwegerecht(self, object: dict) -> None:
        if object.get("typ") is not None:
            object["typ"] = [object.pop("typ")]

    def _fpplan(self, object: dict) -> None:
        if not object.get("planArt", None):
            self.__prop_error(object, "planArt", "planArt ist ein Pflichtattribut")

        if not object.get("raeumlicherGeltungsbereich"):
            self.__prop_error(
                object, "raeumlicherGeltungsbereich", "Fehlendes Pflichtattribut."
            )

        self.__attr_to_externe_referenz(
            object,
            [
                ("refUmweltbericht", "1050"),
                ("refErlaeuterung", "1080"),
            ],
        )
        self.__attr_to_list(object, "auslegungsStartDatum")
        self.__attr_to_list(object, "auslegungsEndDatum")
        self.__attr_to_list(object, "traegerbeteiligungsStartDatum")
        self.__attr_to_list(object, "traegerbeteiligungsEndDatum")

    def _fpbereich(self, object: dict) -> None:
        object["versionBauGBDatum"] = object.pop("versionBauGB", None)
        version = object.get("versionBauNVO")
        mapping = {
            "1000": "Version_1962",
            "2000": "Version_1968",
            "3000": "Version_1977",
            "4000": "Version_1990",
        }
        if version in mapping:
            object["versionBauNVOText"] = mapping[version]
        object.pop("versionBauNVO", None)

        object.setdefault("planinhalt", []).extend(object.pop("inhaltFPlan", None))

        if object.pop("rasterAenderung", None):
            self.__prop_warn(
                object,
                "rasterAenderung",
                "Rasterplan_Aenderung wird nicht mehr unterstützt, das Objekt XP_RasterplanAenderung wird nicht übernommen.",
            )

    def _fpobjekt(self, object: dict) -> None:
        self.__migrate_bereich_ref(object, "FP")

        if not object.get("rechtscharakter"):
            object["rechtscharakter"] = "9998"

    def _fpbebauungsflaeche(self, object: dict) -> None:
        self.__attr_to_list(object, "sonderNutzung")

    def _fpgemeinbedarf(self, object: dict) -> None:
        self.__merge_optional_fields(
            object,
            [
                "weitereZweckbestimmung1",
                "weitereZweckbestimmung2",
                "weitereZweckbestimmung3",
                "weitereZweckbestimmung4",
                "weitereZweckbestimmung5",
                "besondereZweckbestimmung",
                "weitereBesondZweckbestimmung1",
                "weitereBesondZweckbestimmung2",
                "weitereBesondZweckbestimmung3",
                "weitereBesondZweckbestimmung4",
                "weitereBesondZweckbestimmung5",
            ],
            "zweckbestimmung",
        )

        self.__merge_optional_fields(
            object,
            [
                "weitereDetailZweckbestimmung1",
                "weitereDetailZweckbestimmung2",
                "weitereDetailZweckbestimmung3",
                "weitereDetailZweckbestimmung4",
                "weitereDetailZweckbestimmung5",
            ],
            "detaillierteZweckbestimmung",
        )

    def _fpspielsportanlage(self, object: dict) -> None:
        self.__merge_optional_fields(
            object, ["weitereZweckbestimmung1"], "zweckbestimmung"
        )
        self.__merge_optional_fields(
            object, ["weitereDetailZweckbestimmung1"], "detaillierteZweckbestimmung"
        )

    def _fpwaldflaeche(self, object: dict) -> None:
        self.__merge_optional_fields(
            object,
            [
                "weitereZweckbestimmung1",
                "weitereZweckbestimmung2",
            ],
            "zweckbestimmung",
        )
        self.__merge_optional_fields(
            object,
            [
                "weitereDetailZweckbestimmung1",
                "weitereDetailZweckbestimmung2",
            ],
            "detaillierteZweckbestimmung",
        )

    def _fpgruen(self, object: dict) -> None:
        self.__merge_optional_fields(
            object,
            [
                "weitereZweckbestimmung1",
                "weitereZweckbestimmung2",
                "weitereZweckbestimmung3",
                "weitereZweckbestimmung4",
                "weitereZweckbestimmung5",
                "besondereZweckbestimmung",
                "weitereBesondZweckbestimmung1",
                "weitereBesondZweckbestimmung2",
                "weitereBesondZweckbestimmung3",
                "weitereBesondZweckbestimmung4",
                "weitereBesondZweckbestimmung5",
            ],
            "zweckbestimmung",
        )

        self.__merge_optional_fields(
            object,
            [
                "weitereDetailZweckbestimmung1",
                "weitereDetailZweckbestimmung2",
                "weitereDetailZweckbestimmung3",
                "weitereDetailZweckbestimmung4",
                "weitereDetailZweckbestimmung5",
            ],
            "detaillierteZweckbestimmung",
        )

    def _fplandwirtschaftsflaeche(self, object: dict) -> None:
        self.__merge_optional_fields(
            object,
            [
                "weitereZweckbestimmung1",
                "weitereZweckbestimmung2",
                "weitereZweckbestimmung3",
            ],
            "zweckbestimmung",
        )
        self.__merge_optional_fields(
            object,
            [
                "weitereDetailZweckbestimmung1",
                "weitereDetailZweckbestimmung2",
                "weitereDetailZweckbestimmung3",
            ],
            "detaillierteZweckbestimmung",
        )

    def _fpschutzpflegeentwicklung(self, object: dict) -> None:
        self.__merge_optional_fields(
            object,
            [
                "weitereMassnahme1",
                "weitereMassnahme2",
            ],
            "massnahme",
        )

    def _fpausgleichsflaeche(self, object: dict) -> None:
        self.__merge_optional_fields(
            object,
            [
                "weitereMassnahme1",
                "weitereMassnahme2",
            ],
            "massnahme",
        )
        for key in (
            "refMassnahmenText",
            "refLandschaftsplan",
            "_GenericApplicationPropertyOfFP_AusgleichsFlaeche",
        ):
            value = object.pop(key, None)
            if value is not None:
                object[key] = value

    def _fpgenerischesobjekt(self, object: dict) -> None:
        self.__merge_optional_fields(
            object,
            [
                "weitereZweckbestimmung1",
                "weitereZweckbestimmung2",
                "weitereZweckbestimmung3",
            ],
            "zweckbestimmung",
        )

    def _fpprivilegiertesvorhaben(self, object: dict) -> None:
        self.__merge_optional_fields(
            object,
            [
                "weitereZweckbestimmung1",
                "weitereZweckbestimmung2",
                "besondereZweckbestimmung",
                "weitereBesondZweckbestimmung1",
                "weitereBesondZweckbestimmung2",
            ],
            "zweckbestimmung",
        )

    def _fprasterplanaenderung(self, object: dict) -> None:
        object.clear()

    def _fpverentsorgung(self, object: dict) -> None:
        self.__merge_optional_fields(
            object,
            [
                "weitereZweckbestimmung1",
                "weitereZweckbestimmung2",
                "weitereZweckbestimmung3",
                "besondereZweckbestimmung",
                "weitereBesondZweckbestimmung1",
                "weitereBesondZweckbestimmung2",
                "weitereBesondZweckbestimmung3",
            ],
            "zweckbestimmung",
        )

        self.__merge_optional_fields(
            object,
            [
                "weitereDetailZweckbestimmung1",
                "weitereDetailZweckbestimmung2",
                "weitereDetailZweckbestimmung3",
            ],
            "detaillierteZweckbestimmung",
        )

    def _fpkennzeichnung(self, object: dict) -> None:
        self.__merge_optional_fields(
            object, ["weitereZweckbestimmung1"], "zweckbestimmung"
        )

    def _fpabgrabungsflaeche(self, object: dict) -> None:
        object["featuretype"] = "FP_Abgrabung"

    def _fpaufschuettungsflaeche(self, object: dict) -> None:
        object["featuretype"] = "FP_Aufschuettung"

    def _fpbodenschaetzeflaeche(self, object: dict) -> None:
        object["featuretype"] = "FP_Bodenschaetze"

    def _fpbesonderezweckbestimmungstrassenverkehr(self, value: str) -> str:
        mapping = {
            "14010": "140010",
            "14011": "140011",
        }
        return mapping.get(value, value)

    def _fpstrassenverkehr(self, object: dict) -> None:
        besondereZweckbestimmung = object.pop("besondereZweckbestimmung", None)
        if (
            besondereZweckbestimmung is not None
            and object.get("zweckbestimmung") is None
        ):
            object["zweckbestimmung"] = besondereZweckbestimmung
        else:
            self.__prop_warn(
                object,
                "besondereZweckbestimmung",
                "Attributwert konnte nicht übernommen werden.",
            )
        self.__attr_to_list(object, "zweckbestimmung")
        self.__attr_to_list(object, "detaillierteZweckbestimmung")

    def _soobjekt(self, object: dict) -> None:
        self.__migrate_bereich_ref(object, "SO")
        if not object.get("rechtscharakter"):
            object["rechtscharakter"] = "9998"
        charakter = object.get("sonstRechtscharakter")
        rechtscharakter_map = {
            "FestsetzungBPlan": "1000",
            "DarstellungFPlan": "2000",
        }
        if charakter in rechtscharakter_map:
            if object.get("rechtscharakter") == "9999":
                object["rechtscharakter"] = rechtscharakter_map[charakter]
            else:
                self.__prop_warn(object, "sonstRechtscharakter")

    def _soplan(self, object: dict) -> None:
        if not object.get("raeumlicherGeltungsbereich"):
            self.__prop_error(
                object, "raeumlicherGeltungsbereich", "Fehlendes Pflichtattribut."
            )

        object["planArt"] = object.pop("planTyp")

    def _sobereich(self, object: dict) -> None:
        object.setdefault("planinhalt", []).extend(object.pop("inhaltSoPlan", None))

        if object.pop("rasterAenderung", None):
            self.__prop_warn(
                object,
                "rasterAenderung",
                "Rasterplan_Aenderung wird nicht mehr unterstützt, das Objekt XP_RasterplanAenderung wird nicht übernommen.",
            )

    def _sorasterplanaenderung(self, object: dict) -> None:
        object.clear()

    def _soschienenverkehrsrecht(self, object: dict) -> None:
        besondereArtFestlegung = object.pop("besondereArtDerFestlegung", None)
        if besondereArtFestlegung is not None:
            if object.get("artDerFestlegung") is None:
                object["artDerFestlegung"] = besondereArtFestlegung
            else:
                self.__prop_warn(
                    object,
                    "besondereArtDerFestlegung",
                    "Attributwert konnte nicht übernommen werden.",
                )

    def _soschutzgebietsonstigesrecht(self, object: dict) -> None:
        if (zone := object.pop("zone", None)) is not None:
            object["featuretype"] = "SO_Luftverkehrsrecht"
            object["laermschutzzone"] = zone
            object["artDerFestlegung"] = "6000"

    def _soklassifiznachwasserrecht(self, value: str) -> str:
        mapping = {
            "1000": "10000",
            "1100": "10001",
            "1300": "10002",
        }
        return mapping.get(value, value)

    def _lpplan(self, object: dict) -> None:
        self.__attr_to_list(object, "auslegungsDatum")
        self.__attr_to_list(object, "tOeBbeteiligungsDatum")
        self.__attr_to_list(object, "oeffentlichkeitsbeteiligungDatum")
        if not object.get("raeumlicherGeltungsbereich"):
            self.__prop_error(
                object, "raeumlicherGeltungsbereich", "Fehlendes Pflichtattribut."
            )

    def _lpbereich(self, object: dict) -> None:
        object.setdefault("planinhalt", []).extend(object.pop("inhaltLPlan", None))
        if object.pop("rasterAenderung", None):
            self.__prop_warn(
                object,
                "rasterAenderung",
                "Rasterplan_Aenderung wird nicht mehr unterstützt, das Objekt XP_RasterplanAenderung wird nicht übernommen.",
            )

    def _lpobjekt(self, object: dict) -> None:
        status = object.pop("status", None)
        if status is not None:
            object["rechtscharakter"] = status
        else:
            object["rechtscharakter"] = "9998"

        self.__migrate_bereich_ref(object, "LP")

    def _lperholungfreizeit(self, object: dict) -> None:
        self.__merge_optional_fields(
            object, ["weitereFunktion1", "weitereFunktion2"], "funktion"
        )
        self.__merge_optional_fields(
            object,
            ["weitereDetailFunktion1", "weitereDetailFunktion2"],
            "detaillierteFunktion",
        )

    def _lprasterplanaenderung(self, object: dict) -> None:
        object.clear()

    def _lpschutzobjektbundsrecht(self, object: dict) -> None:
        self.__prop_warn(
            object,
            "LP_SchutzobjektBundsrecht",
            "Klasse wurde in neuer Version eliminiert.",
        )
        object.clear()

    def _lpdenkmalschutzrecht(self, object: dict) -> None:
        object["featuretype"] = "SO_Denkmalschutzrecht"
        value = object.pop("detailTyp", None)
        if value is not None:
            object["name"] = value
        object.pop("textSchluessel", None)
        object.pop("textSchluesselBegruendung", None)
        object.pop("refBegruendungInhalt", None)
        object.pop("konkretisierung", None)
        object["rechtscharakter"] = "9998"
        self.__prop_warn(object, "status", "Bitte rechtscharakter überprüfen.")

    def _lptextabschnitt(self, object: dict) -> None:
        object.pop("status", None)

    def _lpsonstigeabgrenzuung(self, object: dict) -> None:
        object.clear()

    def _rpplan(self, object: dict) -> None:
        self.__prop_warn_rp(object, "Migration von RP-Plan wird nicht unterstützt.")
        object.clear()
        sys.exit(1)

    def _rpbereich(self, object: dict) -> None:
        self.__prop_warn_rp(object, "Migration von RP-Plan wird nicht unterstützt.")
        object.clear()

    def _rpobjekt(self, object: dict) -> None:
        self.__prop_warn_rp(object)
        # self.__remove_reference_from_presentation_obj(object)
        object.clear()

    def _rprasterplanaenderung(self, object: dict) -> None:
        self.__prop_warn_rp(object)
        object.clear()
