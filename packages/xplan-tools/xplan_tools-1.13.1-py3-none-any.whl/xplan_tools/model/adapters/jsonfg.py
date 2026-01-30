"""Module containing the JsonFGAdapter for reading from and writing to jsonfg."""

import logging

from osgeo import ogr, osr
from pydantic import ValidationInfo
from pydantic_core import from_json, to_json

from xplan_tools.util import parse_srs

logger = logging.getLogger(__name__)


class JsonFGAdapter:
    """Class to add JSON-FG transformation methods to XPlan pydantic model via inheritance."""

    def _to_jsonfg(
        self,
        **kwargs,
    ) -> dict:
        """Converts XPlan object to GeoJSON/JSON-FG Feature."""
        properties = self.model_dump(mode="json", exclude=["id"], exclude_none=True)
        geometry = properties.pop(self.get_geom_field(), None)
        data = {
            "type": "Feature",
            "id": self.id,
            "featureType": self.get_name(),
            "properties": properties,
            "time": None,
            "geometry": None,
            "place": None,
        }
        if not kwargs.get("write_featuretype", True):
            data.pop("featureType")
        if geometry is not None:
            ogr_geom = ogr.CreateGeometryFromWkt(
                self.get_geom_wkt()
            ).GetLinearGeometry()
            srid = osr.SpatialReference()
            srid.ImportFromEPSG(self.get_geom_srid())
            ogr_geom.AssignSpatialReference(srid)
            if str(srid.GetAuthorityCode(None)) != "4326":
                data["place"] = from_json(ogr_geom.ExportToJson())
                if kwargs.get("feature_srs", True):
                    data["coordRefSys"] = (
                        f"http://www.opengis.net/def/crs/{srid.GetAuthorityName(None)}/0/{srid.GetAuthorityCode(None)}"
                    )
                if kwargs.get("write_geometry", True):
                    wgs = osr.SpatialReference()
                    wgs.ImportFromEPSG(4326)
                    wgs_geom = ogr_geom.Clone()
                    wgs_geom.TransformTo(wgs)
                    data["geometry"] = from_json(wgs_geom.ExportToJson())
                    if kwargs.get("write_bbox", True):
                        data["bbox"] = wgs_geom.GetEnvelope()
                    wgs_geom = None
                    wgs = None
            else:
                data["geometry"] = from_json(ogr_geom.ExportToJson())
                if kwargs.get("write_bbox", True):
                    data["bbox"] = ogr_geom.GetEnvelope()
            ogr_geom = None
            srid = None
        return data

    @classmethod
    def _from_jsonfg(cls, feature: dict, info: ValidationInfo) -> dict:
        """Creates a XPlan object instance from a GeoJSON/JSON-FG Feature."""
        data = feature["properties"] | {"id": feature["id"]}
        if geom := feature["place"]:
            ogr_geometry = ogr.CreateGeometryFromJson(to_json(geom).decode())
            if srs := feature.get("coordRefSys", None):
                srid = parse_srs(srs)
            elif info:
                srid = info.context.get("srid")
            else:
                raise ValueError("Could not identify SRID")
            data[cls.get_geom_field()] = {
                "srid": srid,
                "wkt": ogr_geometry.ExportToWkt(),
            }
        elif geom := feature["geometry"]:
            ogr_geometry = ogr.CreateGeometryFromJson(to_json(geom).decode())
            data[cls.get_geom_field()] = {
                "srid": 4326,
                "wkt": ogr_geometry.ExportToWkt(),
            }
        return data
