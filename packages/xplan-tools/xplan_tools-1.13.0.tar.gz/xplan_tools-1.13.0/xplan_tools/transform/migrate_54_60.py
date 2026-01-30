"""Module, containing the explicit transformation and mapping rules for XPlan 5.* to XPlan 6.0."""

import logging
from uuid import UUID

from xplan_tools.model.appschema.definitions import (
    Line,
    MultiLine,
    MultiPolygon,
    Polygon,
)

logger = logging.getLogger(__name__)


class rules_54_60:
    r"""Base class, containing transformations for all XPlan Data types for version 5.* to 6.0.

    Included are transformations for the abstract base classes,
    explicit XPlan object classes as well as additional helper functions.
    Transformations/Mappings are applied in succesion, allowing for factorization
    of common attribute mappings according to the respeptive (abstract) class.
    Note that the class name indicates the specific version migration from 5.4 to 6.0,
    however it also applies to versions 5.1 and 5.2

    Example:
        In case of the XPlan object FP_FlaecheOhneDarstellung, which is a childclass of
        FP_Flaechenschlussobjekt, which in turn is a childclass of FP_Flaechenobjekt,...
        all the way back to the abstract class XP_Objekt, we would run the following
        transformations in this order \n

        _xpobjekt(object)  \n
        _fpobjekt(object)  \n
        _fpflaechenobjekt(object)  \n
        _fpflaechenschlussobjekt(object)  \n
        _fpflaecheohnedarstellung(object) \n

        Note that this is taken care of automatically in the class, which is inheriting from
        rules_54_60 and which is doing the actual transformation of XPlan data
    """

    def __prop_warn(self, object: dict, property: str):
        if object.get("id", None):
            logger.warning(
                f"Feature {object['id']}: manuelle Prüfung für {property} erforderlich"
            )
        else:
            logger.warning(f"Manuelle Prüfung für {property} erforderlich")

    def __prop_warn_lp(self, object: dict):
        logger.warning(
            f"Feature {object['id']}: LP Objekt {object['featuretype']} kann nicht transformiert werden"
        )

    def __prop_error(self, object: dict, property: str):
        if object.get("id", None):
            logger.error(
                f"Feature {object['id']}: Transformation von {property} nicht möglich"
            )
        else:
            logger.error(f"Transformation von {property} nicht möglich")

    def __remove_reference_from_presentation_obj(self, object: dict):
        if ref_id_list := object.pop("wirdDargestelltDurch", None):
            for ref_id in ref_id_list:
                presententations_obj = self.dict[
                    ref_id
                ]  # order matters! presentation obj already migrated
                presententations_obj.dientZurDarstellungVon.remove(UUID(object["id"]))
                if not presententations_obj.dientZurDarstellungVon:
                    presententations_obj.dientZurDarstellungVon = None
        if ref_id_bereich := object.pop("gehoertZuBereich", None):
            bereich_obj = self.collection.features[
                ref_id_bereich
            ]  # order matters! bereich not yet migrated
            bereich_obj.planinhalt.remove(UUID(object["id"]))
            if not bereich_obj.planinhalt:
                bereich_obj.planinhalt = None

            # needed for lp objects
            if bereich_obj := self.dict.get(ref_id_bereich, None):
                bereich_obj.planinhalt.remove(UUID(object["id"]))
                if not bereich_obj.planinhalt:
                    bereich_obj.planinhalt = None

    def __kompl_zweckbest(self, object: dict) -> None:
        if zweckbestimmungen := object.get("zweckbestimmung", None):
            object["zweckbestimmung"] = []
            details = object.pop("detaillierteZweckbestimmung", [])
            idx = 0
            for zweckbestimmung in zweckbestimmungen:
                object["zweckbestimmung"].append(
                    {
                        "allgemein": zweckbestimmung,
                        "detail": [details[idx]] if len(details) > idx else None,
                    }
                )
                idx += 1

    def __gesetzlgrundlage(self, object: dict) -> None:
        bereiche = [
            self.collection.features[bereich] for bereich in object["bereich"] or []
        ]
        for grundlage in ("BauNVO", "BauGB", "SonstRechtsgrundlage"):
            if any(
                (
                    name := object.pop(f"version{grundlage}Text", None),
                    datum := object.pop(f"version{grundlage}Datum", None),
                )
            ):
                object[f"version{grundlage}"] = (
                    [{"name": name, "datum": datum}]
                    if grundlage == "SonstRechtsgrundlage"
                    else {"name": name, "datum": datum}
                )
            else:
                for bereich in bereiche:
                    if any(
                        (
                            name := getattr(bereich, f"version{grundlage}Text"),
                            datum := getattr(bereich, f"version{grundlage}Datum"),
                        )
                    ):
                        object[f"version{grundlage}"] = {
                            "name": name,
                            "datum": str(datum) if datum else None,
                        }

    def _xpobjekt(self, object: dict) -> None:
        """Implements changes for XP_Objekt."""
        object.setdefault("rechtscharakter", "9998")

        if not object.get("gehoertZuBereich", None):
            self.__prop_error(object, "gehoertZuBereich")

        if grundlage := object.get("gesetzlicheGrundlage", None):
            object["gesetzlicheGrundlage"] = {"name": str(grundlage)}
            self.__prop_warn(object, "gesetzlicheGrundlage")

    def _xpbereich(self, object: dict) -> None:
        """Implements changes for XP_Bereich."""
        if object.get("rasterBasis", None):
            rasterdarstellung = self.collection.features[str(object["rasterBasis"])]
            object.setdefault("refScan", []).extend(
                [self.transform_model(refscan) for refscan in rasterdarstellung.refScan]
            )
            object.pop("rasterBasis")

    def _xpplan(self, object: dict) -> None:
        """Implements changes for XP_Plan.

        Includes CR-033 for copying properties from XP_Rasterdarstellung to XP_Plan.
        """
        object["aendertPlan"] = object.pop("aendert", None)
        object["wurdeGeaendertVonPlan"] = object.pop("wurdeGeaendertVon", None)

        for bereich_id in object["bereich"]:
            bereich = self.collection.features[bereich_id]
            if bereich.rasterBasis:
                rasterdarstellung = self.collection.features[str(bereich.rasterBasis)]
                if rasterdarstellung.refText:
                    object.setdefault("texte", []).append(rasterdarstellung.id)
                if rasterdarstellung.refLegende:
                    for legende in rasterdarstellung.refLegende:
                        object.setdefault("externeReferenz", []).append(
                            self.transform_model(legende) | {"typ": "1020"}
                        )

    def _xpexternereferenz(self, object: dict) -> None:
        """Implements changes for XP_ExterneReferenz."""
        object.pop("georefMimeType", None)
        object.pop("informationssystemURL", None)
        object.setdefault(
            "referenzURL", object.get("referenzName", "file:///Unbekannt")
        )
        object.setdefault("referenzName", "Unbekannt")

    def _xpverbundenerplan(self, object: dict) -> None:
        object["aenderungsArt"] = object.pop("rechtscharakter", None)

    def _xprechtscharakterplanaenderung(self, value: str):
        mapping = {"1100": "10001", "20000": "2000", "20001": "3000"}
        return mapping.get(value, value)

    def _xpzweckbestimmunggemeinbedarf(self, value: str):
        if value in [
            "10003",
            "12004",
            "14003",
            "16004",
            "18001",
            "20002",
            "22002",
            "24003",
            "26001",
        ]:
            return value[:-1]
        else:
            return value

    def _xpzweckbestimmungverentsorgung(self, value: str):
        if value == "18005":
            return value[:-1]
        else:
            return value

    def _xpabstraktespraesentationsobjekt(self, object: dict):
        object.pop("index", None)

    def _xpzweckbestimmunggruen(self, value: str) -> str:
        if value in ["14007", "24002"]:
            return value[:-1]
        else:
            return value

    def _xpzweckbestimmunggewaesser(self, value: str) -> str:
        mapping = {"1000": "4000", "10000": "40000", "1100": "3000", "1200": "2000"}
        return mapping.get(value, value)

    def _xprasterdarstellung(self, object: dict) -> None:
        if object.get("refText", None):
            object.pop("refScan", None)
            object.pop("refLegende", None)
            object["featuretype"] = "XP_TextAbschnitt"
            object.setdefault("rechtscharakter", "9998")
        else:
            object.clear()

    def _xptextabschnitt(self, object: dict) -> None:
        object.setdefault("rechtscharakter", "9998")
        object["featuretype"] = "XP_TextAbschnitt"

    def _bpplan(self, object: dict) -> None:
        object.pop("verfahren", None)
        if object.pop("veraenderungssperre", None):
            self.__prop_warn(object, "veraenderungssperre")

        if all(
            key in object.keys()
            for key in [
                "veraenderungssperreDatum",
                "veraenderungssperreEndDatum",
                "verlaengerungVeraenderungssperre",
            ]
        ):
            object["veraenderungssperre"] = {
                "beschlussDatum": object.pop("veraenderungssperreBeschlussDatum", None),
                "startDatum": object.pop("veraenderungssperreDatum", None),
                "endDatum": object.pop("veraenderungssperreEndDatum", None),
                "verlaengerung": object.pop("verlaengerungVeraenderungssperre", None),
            }
        elif any(
            key in object.keys()
            for key in [
                "veraenderungssperreDatum",
                "veraenderungssperreEndDatum",
                "verlaengerungVeraenderungssperre",
            ]
        ):
            object.pop("veraenderungssperreDatum", None)
            object.pop("veraenderungssperreEndDatum", None)
            object.pop("verlaengerungVeraenderungssperre", None)
            object.pop("veraenderungssperreBeschlussDatum", None)
            self.__prop_warn(object, "veraenderungssperreDatum")
            self.__prop_warn(object, "veraenderungssperreEndDatum")
            self.__prop_warn(object, "verlaengerungVeraenderungssperre")
        self.__gesetzlgrundlage(object)

    def _bpbereich(self, object: dict) -> None:
        for prop in [
            "versionBauNVODatum",
            "versionBauNVOText",
            "versionBauGBDatum",
            "versionBauGBText",
            "versionSonstRechtsgrundlageDatum",
            "versionSonstRechtsgrundlageText",
        ]:
            object.pop(prop, None)
        plan = self.collection.features[object["gehoertZuPlan"]]
        if plan.verfahren:
            object["verfahren"] = plan.verfahren

    def _bprechtscharakter(self, value: str) -> str:
        mapping = {"3000": "6000", "4000": "8000", "5000": "7000"}
        return mapping.get(value, value)

    def _bpbodenschaetzeflaeche(self, object: dict) -> None:
        object["featuretype"] = "BP_AbgrabungsFlaeche"

    def _bprekultivierungsflaeche(self, object: dict) -> None:
        object["artDerFestlegung"] = "1500"
        object["featuretype"] = "SO_SonstigesRecht"

    def _bpfirstrichtungslinie(self, object: dict) -> None:
        object["typ"] = "1000"
        object["featuretype"] = "BP_GebaeudeStellung"

    def _bpnichtueberbaubaregrundstuecksflaeche(self, object: dict) -> None:
        object["featuretype"] = "BP_NichtUeberbaubareGrundstuecksflaeche"

    def _bpbaugebietsteilflaeche(self, object: dict) -> None:
        nutzungText = object.pop("nutzungText", None)
        if sondernutzungen := object.get("sondernutzung", None):
            object["sondernutzung"] = []
            details = object.pop("detaillierteSondernutzung", [])
            idx = 0
            for sondernutzung in sondernutzungen:
                object["sondernutzung"].append(
                    {
                        "allgemein": sondernutzung,
                        "detail": [details[idx]] if len(details) > idx else None,
                    }
                )
                idx += 1
            object["sondernutzung"][0]["nutzungText"] = nutzungText
        self._bpgestaltungbaugebiet(object)

    def _bpgestaltungbaugebiet(self, object: dict) -> None:
        for prop in ("DNmin", "DNmax", "DN", "DNZwingend"):
            if val := object.pop(prop, None):
                object.setdefault("dachgestaltung", [{}])[0].setdefault(
                    "DNzwingend" if prop == "DNZwingend" else prop, val
                )
        if dachformen := object.pop("dachform", None):
            object.setdefault("dachgestaltung", [{}])
            details = object.pop("detaillierteDachform", [])
            idx = 0
            for dachform in dachformen:
                if len(object["dachgestaltung"]) > idx:
                    object["dachgestaltung"][idx].setdefault("dachform", dachform)
                    object["dachgestaltung"][idx].setdefault(
                        "detaillierteDachform",
                        details[idx] if len(details) > idx else None,
                    )
                else:
                    object["dachgestaltung"].append(
                        {
                            "dachform": dachform,
                            "detaillierteDachform": details[idx]
                            if len(details) > idx
                            else None,
                        }
                    )
                idx += 1

    def _bpgemeinschaftsanlagenflaeche(self, object: dict) -> None:
        self.__kompl_zweckbest(object)

    def _bpnebenanlagenflaeche(self, object: dict) -> None:
        self.__kompl_zweckbest(object)

    def _bpueberbaubaregrundstuecksflaeche(self, object: dict) -> None:
        self._bpgestaltungbaugebiet(object)

    def _bpwohngebaeudeflaeche(self, object: dict) -> None:
        self._bpgestaltungbaugebiet(object)

    def _bperhaltungsbereichflaeche(self, object: dict) -> None:
        object["gebietsArt"] = object.pop("grund", None)
        object["featuretype"] = "SO_Gebiet"

    def _bperhaltungsgrund(self, value: str) -> str:
        mapping = {"1000": "17000", "2000": "17001", "3000": "17002"}
        return mapping.get(value)

    def _bpgemeinbedarfsflaeche(self, object: dict) -> None:
        self._bpgestaltungbaugebiet(object)
        self.__kompl_zweckbest(object)

    def _bpspielsportanlagenflaeche(self, object: dict) -> None:
        self.__kompl_zweckbest(object)

    def _bpemissionskontingentlaerm(self, object: dict) -> None:
        for prop in ("pegelTyp", "berechnungsgrundlage"):
            object[prop] = "1000"
            self.__prop_warn(object, prop)

    def _bpwaldflaeche(self, object: dict) -> None:
        self.__kompl_zweckbest(object)

    def _bplandwirtschaftsflaeche(self, object: dict) -> None:
        self.__kompl_zweckbest(object)

    def _bplandwirtschaft(self, object: dict) -> None:
        if isinstance(object["position"], (Polygon, MultiPolygon)):
            object["featuretype"] = "BP_LandwirtschaftsFlaeche"
            self.__kompl_zweckbest(object)
        else:
            self.__prop_error(object, "position")
            self.__remove_reference_from_presentation_obj(object)
            object.clear()

    def _bpgruenflaeche(self, object: dict) -> None:
        self.__kompl_zweckbest(object)

    def _bpanpflanzungbindungerhaltung(self, object: dict) -> None:
        if baumart := object.pop("baumArt", None):
            object["pflanzenArt"] = str(baumart)

    def _bptextlichefestsetzungsflaeche(self, object: dict) -> None:
        object["featuretype"] = "BP_TextAbschnittFlaeche"

    def _bpsichtflaeche(self, object: dict) -> None:
        object["featuretype"] = "SO_Sichtflaeche"

    def _bpveraenderungssperre(self, object: dict) -> None:
        startDatum = object.pop("veraenderungssperreStartDatum", None)
        endDatum = object.pop("gueltigkeitsDatum", None)
        verlaengerung = object.pop("verlaengerung", None)

        if None in (startDatum, endDatum, verlaengerung):
            self.__prop_error(object, "BP_Veraenderungssperre")
            self.__remove_reference_from_presentation_obj(object)
            object.clear()
        else:
            object["daten"] = {
                "beschlussDatum": object.pop("veraenderungssperreBeschlussDatum", None),
                "startDatum": startDatum,
                "endDatum": endDatum,
                "verlaengerung": verlaengerung,
                "refBeschluss": object.pop("refBeschluss", None),
            }

    def _bpabstandsmass(self, object: dict) -> None:
        if not isinstance(object["position"], (Line, MultiLine)):
            self.__prop_error(object, "position")
            self.__remove_reference_from_presentation_obj(object)
            object.clear()
        object.pop("flaechenschluss", None)  # Attribut von BPGeometrieobjekt
        object.pop("flussrichtung", None)  # weiteres Attribut von BPGeometrieobjekt
        object.pop("nordwinkel", None)  # weiteres Attribut von BPGeometrieobjekt

    def _bpwegerecht(self, object: dict) -> None:
        typen = [typ for typ in object.get("typ", [])]
        for typ in typen:
            match typ:
                case "1000":
                    object["typ"].remove(typ)
                    object["typ"].extend(["2000", "2500"])
                case "3000":
                    object["typ"].remove(typ)
                    object["typ"].extend(["1000", "2000"])
                case "4100":
                    object["typ"].remove(typ)
                    object["typ"].extend(["1000", "4000"])
                case "4200":
                    object["typ"].remove(typ)
                    object["typ"].extend(["2000", "4000"])
                case "5000":
                    object["typ"].remove(typ)
                    object["typ"].extend(["1000", "2000", "4000"])

    def _bpverentsorgung(self, object: dict) -> None:
        self.__kompl_zweckbest(object)
        ergaenzung = object.pop("textlicheErgaenzung", None)
        if object.get("zweckbestimmung", None):
            object["zweckbestimmung"][0]["textlicheErgaenzung"] = ergaenzung

    def _bpstrassenverkehrsflaeche(self, object: dict) -> None:
        object["hatDarstellungMitBesondZweckbest"] = False
        object["featuretype"] = "SO_Strassenverkehr"

    def _bpverkehrsflaechebesondererzweckbestimmung(self, object: dict) -> None:
        object["hatDarstellungMitBesondZweckbest"] = True
        self.__kompl_zweckbest(object)
        object["artDerFestlegung"] = object.pop("zweckbestimmung", None)
        object["featuretype"] = "SO_Strassenverkehr"

    def _bpzweckbestimmungstrassenverkehr(self, value: str) -> str:
        mapping = {
            "1000": "16000",
            "1100": "14002",
            "1200": "14000",
            "1300": "14003",
            "1400": "14004",
            "1500": "14005",
            "1550": "14006",
            "1560": "14007",
            "1580": "140012",
            "1600": "16001",
            "1700": "140010",
            "1800": "140011",
            "2000": "16002",
            "2100": "14001",
            "2200": "14014",
            "2300": "140013",
            "2400": "14015",
            "2500": "14008",
            "2600": "14009",
            "3000": "16005",
            "3100": "16006",
            "3200": "16003",
            "3300": "16004",
        }
        return mapping.get(value, value)

    def _bpgewaesserflaeche(self, object: dict) -> None:
        if zweckbestimmung := object.pop("zweckbestimmung", None):
            detailierteZweckbestimmung = object.pop("detaillierteZweckbestimmung", None)
            object["artDerFestlegung"] = [
                {
                    "allgemein": zweckbestimmung,
                    "detail": [detailierteZweckbestimmung]
                    if detailierteZweckbestimmung
                    else None,
                }
            ]
        if (
            isinstance(object["position"], (Polygon, MultiPolygon))
            and object.get("ebene") is not None
        ):
            if int(object["ebene"]) == 0:
                object["flaechenschluss"] = True
        object["featuretype"] = "SO_Gewaesser"

    def _bpwasserwirtschaftsflaeche(self, object: dict) -> None:
        object["artDerFestlegung"] = object.pop("zweckbestimmung", None)
        object["detailArtDerFestlegung"] = object.pop(
            "detaillierteZweckbestimmung", None
        )
        object["featuretype"] = "SO_Wasserwirtschaft"

    def _bpbebauungsart(self, value: str):
        return None if value == "8000" else value

    def _bpbesonderernutzungszweckflaeche(self, object: dict) -> None:
        self._bpgestaltungbaugebiet(object)

    def _bpabweichungvonueberbauberergrundstuecksflaeche(self, object: dict) -> None:
        object["featuretype"] = "BP_AbweichungVonUeberbaubarerGrundstuecksFlaeche"

    def _fpplan(self, object: dict) -> None:
        self.__gesetzlgrundlage(object)

    def _fpbereich(self, object: dict) -> None:
        for prop in [
            "versionBauNVODatum",
            "versionBauNVOText",
            "versionBauGBDatum",
            "versionBauGBText",
            "versionSonstRechtsgrundlageDatum",
            "versionSonstRechtsgrundlageText",
        ]:
            object.pop(prop, None)

    def _fprechtscharakter(self, value: str) -> str:
        mapping = {"1000": "3000", "3000": "6000", "4000": "8000", "5000": "7000"}
        return mapping.get(value, value)

    def _fpbodenschaetze(self, object: dict) -> None:
        object["featuretype"] = "FP_Abgrabung"

    def _fpbebauungsflaeche(self, object: dict) -> None:
        if sondernutzungen := object.pop("sonderNutzung", None):
            object["sondernutzung"] = []
            details = object.pop("detaillierteZweckbestimmung", [])
            details.extend(object.pop("detaillierteSondernutzung", []))
            idx = 0
            for sondernutzung in sondernutzungen:
                object["sondernutzung"].append(
                    {
                        "allgemein": sondernutzung,
                        "detail": [details[idx]] if len(details) > idx else None,
                        "nutzungText": object.pop("nutzungText", None)
                        if idx == 0
                        else None,
                    }
                )
                idx += 1

    def _fpgemeinbedarf(self, object: dict) -> None:
        self.__kompl_zweckbest(object)

    def _fpspielsportanlage(self, object: dict) -> None:
        self.__kompl_zweckbest(object)

    def _fpwaldflaeche(self, object: dict) -> None:
        self.__kompl_zweckbest(object)

    def _fplandwirtschaft(self, object: dict) -> None:
        self.__kompl_zweckbest(object)

    def _fplandwirtschaftsflaeche(self, object: dict) -> None:
        object["featuretype"] = "FP_Landwirtschaft"
        self.__kompl_zweckbest(object)

    def _fpgruen(self, object: dict) -> None:
        self.__kompl_zweckbest(object)

    def _fptextlichedarstellungsflaeche(self, object: dict) -> None:
        object["featuretype"] = "FP_TextAbschnittFlaeche"

    def _fpnutzungsbeschraenkungsflaeche(self, object: dict) -> None:
        object["featuretype"] = "FP_Nutzungsbeschraenkung"

    def _fpverentsorgung(self, object: dict) -> None:
        self._bpverentsorgung(object)

    def _fpstrassenverkehr(self, object: dict) -> None:
        object["hatDarstellungMitBesondZweckbest"] = False
        if "zweckbestimmung" in object and "1300" in object["zweckbestimmung"]:
            # Find correct index to remove
            idx = object["zweckbestimmung"].index("1300")
            object["zweckbestimmung"].pop(idx)
            if "detaillierteZweckbestimmung" in object:
                detaillierte = object["detaillierteZweckbestimmung"]
                # Only remove from detaillierteZweckbestimmung if a corresponding entry exists, because not every zweckbestimmung has one
                if idx < len(detaillierte):
                    detaillierte.pop(idx)
                # Remove key if empty
                if not detaillierte:
                    object.pop("detaillierteZweckbestimmung")

            object["istOrtsdurchfahrt"] = True
        self.__kompl_zweckbest(object)
        object["artDerFestlegung"] = object.pop("zweckbestimmung", None)
        if object.pop("spezifischePraegung", None):
            self.__prop_warn(object, "spezifischePraegung")
        object["featuretype"] = "SO_Strassenverkehr"

    def _fpzweckbestimmungstrassenverkehr(self, value: str) -> str:
        mapping = {
            "3000": "16005",
            "3100": "16006",
            "3200": "16003",
            "3300": "16004",
        }
        return mapping.get(value, value)

    def _fpgewaesser(self, object: dict) -> None:
        if zweckbestimmung := object.pop("zweckbestimmung", None):
            detaillierteZweckbestimmung = object.pop(
                "detaillierteZweckbestimmung", None
            )
            object["artDerFestlegung"] = [
                {
                    "allgemein": zweckbestimmung,
                    "detail": [detaillierteZweckbestimmung]
                    if detaillierteZweckbestimmung
                    else None,
                }
            ]
        if object.pop("spezifischePraegung", None):
            self.__prop_warn(object, "spezifischePraegung")
        object["featuretype"] = "SO_Gewaesser"

    def _fpwasserwirtschaft(self, object: dict) -> None:
        object["artDerFestlegung"] = object.pop("zweckbestimmung", None)
        object["detailArtDerFestlegung"] = object.pop(
            "detaillierteZweckbestimmung", None
        )
        if object.pop("spezifischePraegung", None):
            self.__prop_warn(object, "spezifischePraegung")
        object["featuretype"] = "SO_Wasserwirtschaft"

    def _sorechtscharakter(self, value: str) -> str:
        mapping = {
            "1500": "3000",
            "1800": "5300",
            "3000": "6000",
            "4000": "8000",
            "5000": "7000",
        }
        return mapping.get(value, value)

    def _sostrassenverkehrsrecht(self, object: dict) -> None:
        object["featuretype"] = "SO_Strassenverkehr"
        object["hatDarstellungMitBesondZweckbest"] = False
        object["einteilung"] = object.pop("artDerFestlegung", None)
        object.pop("detailArtDerFestlegung", None)

    def _soluftverkehrsrecht(self, object: dict) -> None:
        if object.get("artDerFestlegung", None) == "7000":
            object["featuretype"] = "SO_Baubeschraenkung"
            object["artDerFestlegung"] = "2000"
            object["rechtlicheGrundlage"] = "1000"
        if object.pop("laermschutzzone", None):
            self.__prop_warn(object, "laermschutzzone")

    def _soklassifiznachwasserrecht(self, value: str) -> str:
        mapping = {"10000": "20000", "10001": "20001", "10002": "20002"}
        return mapping.get(value, value)

    def _sowasserrecht(self, object: dict) -> None:
        object["featuretype"] = "SO_Gewaesser"
        object.pop("istNatuerlichesUberschwemmungsgebiet", None)
        self.__prop_error(object, "istNatuerlichesUberschwemmungsgebiet")
        if art := object.get("artDerFestlegung", None):
            object["artDerFestlegung"] = [
                {
                    "allgemein": art,
                }
            ]
        if (
            isinstance(object["position"], (Polygon, MultiPolygon))
            and object.get("ebene") is not None
        ):
            if int(object["ebene"]) == 0:
                object["flaechenschluss"] = True
        if object.pop("detailArtDerFestlegung", None):
            self.__prop_warn(object, "detailArtDerFestlegung")

    def _soklassifizgewaesser(self, value: str) -> str:
        mapping = {
            "10000": "20000",
            "10001": "20001",
            "10002": "20002",
            "10003": "3000",
            "2000": "4000",
        }
        return mapping.get(value, value)

    def _sogewaesser(self, object: dict) -> None:
        if artderfestlegung := object.pop("artDerFestlegung", None):
            detailartderfestlegung = object.pop("detailArtDerFestlegung", None)
            object["artDerFestlegung"] = [
                {
                    "allgemein": artderfestlegung,
                    "detail": [detailartderfestlegung]
                    if detailartderfestlegung
                    else None,
                }
            ]

    def _sosonstigesrecht(self, object: dict) -> None:
        mapping = {"1000": "9999", "1200": "2000"}
        if (art := object["artDerFestlegung"]) in ["1000", "1200"]:
            object["featuretype"] = "SO_Baubeschraenkung"
            object["artDerFestlegung"] = mapping.get(art)

    def _sobauverbotszone(self, object: dict) -> None:
        object["featuretype"] = "SO_Baubeschraenkung"

    def _soschutzgebietsonstigesrecht(self, object: dict) -> None:
        object["featuretype"] = "SO_SonstigesRecht"

    def _soklassifizschutzgebietsonstrecht(self, value: str) -> str:
        mapping = {"1000": "1700", "2000": "1800"}
        return mapping.get(value, value)

    def _soschutzgebietnaturschutzrecht(self, object: dict) -> None:
        if object.setdefault("artDerFestlegung", "9999") == "9999":
            object["artDerFestlegungText"] = "Unbekannt"
        if (
            object.setdefault("rechtsstandSchG", object.get("rechtsstand", "9999"))
            == "9999"
        ):
            object["rechtsstandSchGText"] = "Unbekannt"
            self.__prop_warn(object, "rechtsstandSchGText")
        if object["artDerFestlegung"] == "1700":
            object["gesetzlGeschBiotop"] = "9999"
            self.__prop_warn(object, "gesetzlGeschBiotop")
            object["gesetzlGeschBiotopText"] = "Unbekannt"
            self.__prop_warn(object, "gesetzlGeschBiotopText")
        object["raumkonkretisierung"] = "9998"
        self.__prop_warn(object, "raumkonkretisierung")
        for attr in ["sonstRechtscharakter", "detailArtDerFestlegung", "zone"]:
            if object.pop(attr, None):
                self.__prop_warn(object, attr)
        object["featuretype"] = "LP_SchutzBestimmterTeileVonNaturUndLandschaft"

    def _sogebietsart(self, value: str) -> str:
        mapping = {"1999": "1700", "2000": "17000", "2100": "17001", "2200": "17002"}
        return mapping.get(value, value)

    def _rprechtscharakter(self, value: str) -> str:
        mapping = {
            "1000": "4000",
            "2000": "4100",
            "3000": "2000",
            "4000": "4200",
            "5000": "4300",
            "6000": "4400",
            "7000": "4500",
            "8000": "4600",
            "9000": "4700",
        }
        return mapping.get(value, value)

    def _rplegendenobjekt(self, object: dict) -> None:
        object.clear()
        self.__prop_error(object, "RP_Legendenobjekt")

    def _rpzentralerort(self, object: dict) -> None:
        if "9999" in object["sonstigerTyp"]:
            self.__remove_reference_from_presentation_obj(object)
            object.clear()
            self.__prop_error(object, "sonstigerTyp")

    def _lpobjekt(self, object: dict) -> None:
        self.__prop_warn_lp(object)
        self.__remove_reference_from_presentation_obj(object)
        object.clear()
