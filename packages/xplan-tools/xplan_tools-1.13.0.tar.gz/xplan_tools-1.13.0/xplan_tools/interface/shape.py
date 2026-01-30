"""Module containing the class for extracting plans from shape files."""

import logging
from uuid import uuid4

import shapely as s
from dateutil.parser import parse
from osgeo import gdal
from pydantic import ValidationError

from xplan_tools.model import model_factory
from xplan_tools.util import ExternalReferenceUtil, RasterReferenceUtil

from .base import BaseCollection, BaseRepository

gdal.SetConfigOption("OGR_ORGANIZE_POLYGONS", "DEFAULT")

logger = logging.getLogger(__name__)


class ShapeRepository(BaseRepository):
    """Repository class for collecting plans from shape files.

    Given a shape file conforming to the format described
    [here](https://www.digitale.planung.bayern.de/assets/stmi/miniwebs/digitale_planung/26_leitfaden_bauleitplaene_im_internet.pdf) (Appendix 2),
    plan data is read to XPlanung classes. Only reading is supported.
    """

    def __init__(
        self,
        datasource: str = "",
    ) -> None:
        self.datasource = datasource
        self.appschema = "xplan"
        self.version = "6.0"

    def get_all(self, **kwargs) -> BaseCollection:
        def _get_date(date_field: str):
            try:
                value = ft.GetField(date_field)
                return str(parse(value).date())
            except Exception:
                return None

        def _get_field(entry: str):
            try:
                return ft.GetField(entry)
            except Exception:
                return None

        def _add_ref(external_ref: ExternalReferenceUtil, typ: str) -> None:
            ref = {
                "referenzName": "Unbekannt",
                "referenzURL": str(external_ref.ref_url),
                "typ": typ,
            }
            if external_ref.georef_url:
                if not kwargs.get("ref_check", None) or external_ref.georef_url_valid():
                    ref["georefURL"] = str(external_ref.georef_url)
                else:
                    logger.warning(
                        "Skipping invalid georefURL: %s", external_ref.georef_url
                    )

            if not kwargs.get("ref_check", None) or external_ref.ref_url_valid():
                data.setdefault("externeReferenz", []).append(ref)
            else:
                raise FileNotFoundError(
                    f"File {external_ref.ref_url} could not be added."
                )

        planart_mapping = {
            "BP": {
                "1000": "10000",
                "2000": "10001",
                "3000": "3000",
                "4000": "40001",
                "5000": "40002",
                "6000": "1000",
                "7000": "5000",
                "8000": "40000",
            },
            "FP": {
                "1000": "1000",
                "2000": "2000",
                "3000": "3000",
                "4000": "4000",
            },
        }

        typ_mapping = {
            "BESCHRURL": "1000",
            "BEGRURL": "1010",
            "LEGENDEURL": "1020",
            "RECHTSURL": "1030",
            "LIEGURL": "1040",
            "UMWELTBERI": "1050",
            "TEXTURL": "9998",
        }

        if not kwargs.get("raster_as_refscan", None):
            typ_mapping["SCANURL"] = "1070"

        collection = {}

        with gdal.OpenEx(self.datasource, allowed_drivers=["ESRI Shapefile"]) as ds:
            lyr = ds.GetLayer(0)
            srid = lyr.GetSpatialRef().GetAuthorityCode(None)

            for ft in lyr:
                try:
                    if not srid:
                        srid = (
                            ft.geometry().GetSpatialReference().GetAuthorityCode(None)
                        )

                    geom = s.from_wkb(bytes(ft.geometry().ExportToWkb())).reverse()
                    data = {
                        "id": str(uuid4()),
                        "name": _get_field(kwargs.get("name_field", "PLANID")),
                        "nummer": _get_field("NUMMER"),
                        "beschreibung": _get_field("BESCHR"),
                        "kommentar": _get_field("KOMMENTAR"),
                        "aufstellungsbeschlussDatum": _get_date("AUFSTELLUN"),
                        "aenderungenBisDatum": _get_date("AENDERUNGE"),
                        "technHerstellDatum": _get_date("DATHERST"),
                        "untergangsDatum": _get_date("DATUNTER"),
                        "auslegungsStartDatum": [date]
                        if (date := _get_date("AUSLEGUNGS"))
                        else None,
                        "traegerbeteiligungsStartDatum": [date]
                        if (date := _get_date("TRAEGERBET"))
                        else None,
                        "rechtsstand": str(_get_field("RECHTSSTA")),
                        "erstellungsMassstab": _get_field("ERSTELLUNG"),
                        "gemeinde": [
                            {
                                "ags": f"0{_get_field('GKZ')}",
                                "gemeindeName": _get_field("STADT"),
                            }
                        ],
                        "raeumlicherGeltungsbereich": {
                            "srid": ft.geometry()
                            .GetSpatialReference()
                            .GetAuthorityCode(None),
                            "wkt": s.to_wkt(geom),
                        },
                        "hoehenbezug": _get_field("HOEHENBEZU"),
                    }
                except AttributeError as e:
                    logger.error(
                        f"GEOM could not be parsed for {ft}: {e}", exc_info=True
                    )
                    raise e
                except KeyError as e:
                    logger.error(f"Missing Field for {ft}: {e}", exc_info=True)
                    raise e

                for field in ["NAME", "PLANID", "ROKNR"]:
                    if value := _get_field(field):
                        data.setdefault("hatGenerAttribut", []).append(
                            {
                                "name": f"shp:{field}",
                                "wert": str(value),
                            }
                        )

                # Set the plan_type to BP or FP, depending on which of the two date attributes
                # INKRAFTTRE or WIRKSAMKEI is found in ft
                if inkraft := _get_date("INKRAFTTRE"):
                    data["inkrafttretensDatum"] = inkraft
                    data["rechtsverordnungsDatum"] = _get_date("RECHTSVERO")
                    data["satzungsbeschlussDatum"] = _get_date("SATZUNGSBE")
                    plan_type = "BP"
                elif wirksam := _get_date("WIRKSAMKEI"):
                    data["wirksamkeitsDatum"] = wirksam
                    data["planbeschlussDatum"] = _get_date("PLANBESCHL")
                    data["entwurfsbeschlussDatum"] = _get_date("ENTWURFBES")
                    plan_type = "FP"
                else:
                    error_message = "Required dates 'INKRAFTTRE' (BP) or 'WIRKSAMKEI' (FP) are missing"
                    logger.error(error_message)
                    raise KeyError(error_message)

                plan_art_entry = planart_mapping.get(plan_type).get(
                    str(_get_field("PLANART")), None
                )
                if not plan_art_entry:
                    error_message = "No mapping found for required attribute 'PLANART'"
                    logger.error(error_message)
                    raise KeyError(error_message)
                data["planArt"] = (
                    [plan_art_entry] if plan_type == "BP" else plan_art_entry
                )

                if aendert := _get_field("AENDERID"):
                    data["aendertPlan"] = [
                        {"planName": aendert, "aenderungsArt": "1000"}
                    ]

                for field, typ in typ_mapping.items():
                    if url := _get_field(field):
                        try:
                            _add_ref(
                                ExternalReferenceUtil(
                                    url,
                                    _get_field("LIEGGEOREF") if typ == "1040" else None,
                                ),
                                typ,
                            )
                        except ValidationError:
                            logger.warning(
                                f"URL {url} for field {field} not valid: skipping"
                            )
                        except FileNotFoundError:
                            logger.warning(
                                f"URL {url} for field {field} of plan {data['name']} could not be added: skipping"
                            )

                if kwargs.get("raster_as_refscan", None):
                    if ref_url := _get_field("SCANURL"):
                        try:
                            raster_ref = RasterReferenceUtil(
                                ref_url, _get_field("GEOREFURL")
                            )
                        except ValidationError:
                            logger.info(f"Raster URL {url} not valid: skip")
                        else:
                            if (
                                not kwargs.get("ref_check", None)
                                or raster_ref.raster_data_valid()
                            ):
                                bereich_data = {
                                    "id": str(uuid4()),
                                    "nummer": 0,
                                    "gehoertZuPlan": data.get("id"),
                                    "refScan": [
                                        {
                                            "referenzName": "Unbekannt",
                                            "referenzURL": str(raster_ref.ref_url),
                                            "art": "PlanMitGeoreferenz",
                                            "georefURL": str(raster_ref.georef_url)
                                            if raster_ref.georef_url
                                            else None,
                                        }
                                    ],
                                }
                                bereich = model_factory(
                                    f"{plan_type}_Bereich", "6.0"
                                ).model_validate(bereich_data)
                                data.setdefault("bereich", [])
                                data["bereich"].append(bereich_data["id"])
                                collection[bereich.id] = bereich
                            else:
                                logger.warning(
                                    f"URL {url} for field SCANURL of plan {data['name']} could not be added: skipping"
                                )

                plan = model_factory(f"{plan_type}_Plan", "6.0").model_validate(data)
                collection[plan.id] = plan

            if not srid:
                raise ValueError("Could not identify SRID")

        return BaseCollection(
            features=collection,
            srid=int(srid),
            version=self.version,
            appschema=self.appschema,
        )
