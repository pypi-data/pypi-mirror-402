import io
import json
import logging
import os
import re
from enum import Enum
from pathlib import Path
from typing import Literal
from uuid import UUID

import httpx
import yaml
from osgeo import gdal, ogr
from pydantic import AnyUrl, ValidationError

from xplan_tools.model import model_factory
from xplan_tools.resources.styles import RULES

ogr.UseExceptions()

logger = logging.getLogger(__name__)
logging.getLogger("httpx").propagate = False


def linearize_geom(geom: str) -> str:
    """Returns the linearized WKT string."""
    split_geom = geom.split(";")
    return f"{split_geom[0]};{ogr.CreateGeometryFromWkt(split_geom[1]).GetLinearGeometry().ExportToWkt()}"


def get_geometry_type_from_wkt(geom: str):
    """Derives the geometry type from a WKT string."""
    geom_model_names = [
        "Line",
        "MultiLine",
        "MultiPoint",
        "Point",
        "Polygon",
        "MultiPolygon",
    ]
    for geom_model_name in geom_model_names:
        geom_model = model_factory(geom_model_name, None, "def")
        if re.match(geom_model.model_fields["wkt"].metadata[0].pattern, geom):
            return geom_model


def cast_geom_to_multi(geom: str) -> str:
    """Cast a single geometry to its multi variant."""
    ogr_geom = ogr.CreateGeometryFromWkt(geom)
    geom_type_name = ogr.GeometryTypeToName(ogr_geom.GetGeometryType())
    match geom_type_name:
        case "Polygon" | "Curve Polygon":
            ogr_geom = ogr.ForceToMultiPolygon(ogr_geom)
        case "Line String" | "Circular String" | "Compound Curve":
            ogr_geom = ogr.ForceToMultiLineString(ogr_geom)
        case "Point":
            ogr_geom = ogr.ForceToMultiPoint(ogr_geom)
    wkt = ogr_geom.ExportToWkt()
    ogr_geom = None
    return wkt


def cast_geom_to_single(geom: str) -> str:
    """Cast a multi geometry to its single variant."""
    ogr_geom = ogr.CreateGeometryFromWkt(geom)
    geom_type_name = ogr.GeometryTypeToName(ogr_geom.GetGeometryType())
    match geom_type_name:
        case "Multi Polygon" | "Multi Surface":
            ogr_geom = ogr.ForceToPolygon(ogr_geom)
        case "Multi Line String" | "Multi Curve":
            ogr_geom = ogr.ForceToLineString(ogr_geom)
        case "Multi Point":
            if ogr_geom.GetGeometryCount() == 1:
                ogr_geom = ogr_geom.GetGeometryRef(0)
    wkt = ogr_geom.ExportToWkt()
    ogr_geom = None
    return wkt


def parse_srs(srs: str | None) -> int | None:
    """Returns SRID from a SRS string."""
    if not srs:
        return
    if match := re.match(
        r"^(\[?|http:\/\/www\.opengis\.net\/def\/crs\/)EPSG(:|\/0\/)(?P<srid>\d{4,5})]?$",
        srs,
    ):
        return int(match.group("srid"))
    elif "CRS84" in srs:
        return 4326


def get_envelope(geoms: list[str]) -> tuple[float]:
    """Return a BBOX for a list of geometries.

    Args:
        geoms: A list of WKT strings.

    Returns:
        tuple: The BBOX coordinates in the format min_X, max_X, min_Y, max_Y.
    """
    ogr_geom = ogr.CreateGeometryFromWkt(geoms.pop(0))
    for geom in geoms:
        ogr_geom = ogr_geom.Union(ogr.CreateGeometryFromWkt(geom))
    bbox = ogr_geom.GetEnvelope()
    ogr_geom = None
    return bbox


def get_name(name: str) -> str:
    """Adds underscores to XPlanung class names."""
    if re.match("^([A-Z]P[A-Z]|SO|IP).*$", name):
        return f"{name[:2]}_{name[2:]}"
    elif re.match("^(BRA|BST|ISA|IGP|PFS|PSF|RVP).*$", name):
        return f"{name[:3]}_{name[3:]}"
    else:
        return name


def serialize_style_rules(format: Literal["json", "yaml"]):
    """Serializes the style rules for XPlanung presentational objects in the selected format.

    Args:
        format: The format to serialize to.
    """
    return (
        json.dumps(RULES, indent=2)
        if format == "json"
        else yaml.dump(RULES, allow_unicode=True, sort_keys=False)
    )


def parse_uuid(
    value: str, exact: bool = False, raise_exception: bool = False
) -> str | None:
    """Check if a given string contains a valid UUID."""
    try:
        pattern = (
            "^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[089ab][0-9a-f]{3}-[0-9a-f]{12}$"
        )
        parsed_id = (
            re.search(
                pattern if exact else pattern[1:-1],
                value,
                flags=re.IGNORECASE,
            )
            .group()
            .lower()
        )
        UUID(parsed_id)
        return parsed_id
    except Exception:
        if raise_exception:
            raise ValueError(f"{value} is not a valid UUID")
        return None


class ExternalReferenceUtil:
    """Utility class to validate external references.

    Attributes:
        ref_url (pydantic.AnyUrl): The reference URL stored as an AnyUrl object.
        georef_url (pydantic.AnyUrl): The URL of a georeference sidecar file.

    """

    def __init__(self, ref_url: str, georef_url: str | None = None) -> None:
        self.ref_url = self._parse_url(ref_url)
        self.georef_url = self._parse_url(georef_url)

    def georef_url_valid(self) -> bool:
        return self.georef_content is not None

    def ref_url_valid(self) -> bool:
        return self.ref_content is not None

    @property
    def georef_content(self) -> bytes | None:
        return self._get_content(self.georef_url) if self.georef_url else None

    @property
    def ref_content(self) -> bytes:
        return self._get_content(self.ref_url)

    def _parse_url(self, url: str | None) -> AnyUrl | None:
        if not url:
            return None
        try:
            anyurl = AnyUrl(url)
        except ValidationError as e:
            try:
                return AnyUrl(Path(url).resolve(strict=True).as_uri())
            except (RuntimeError, OSError, ValueError):
                raise e
        if len(anyurl.path) > 1:
            return anyurl
        else:
            return None

    def _get_content(self, url: AnyUrl) -> bytes:
        if url.scheme == "file":
            try:
                with open(url.path, "rb") as f:
                    return f.read()
            except Exception:
                logger.error(f"File {url} could not be read")
        else:
            try:
                response = httpx.get(str(url))
                if response.is_redirect:
                    url_redirect = response.headers["Location"]
                    logger.info(f"Redirecting to {url_redirect!r}")
                    response = httpx.get(str(url_redirect))
                response.raise_for_status()
                return response.read()
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"Error response {e.response.status_code} while requesting {e.request.url!r}."
                )
            except httpx.HTTPError as e:
                logger.error(
                    f"Error while requesting {e.request.url!r}.", exc_info=True
                )
            except httpx.InvalidURL:
                logger.error(f"URL {url} could not be parsed")


class RasterReferenceUtil(ExternalReferenceUtil):
    """Utility class to validate external raster data references.

    Provides the raster_data_valid() method for an in-depth check regarding projection data etc.

    Attributes:
        ref_url (pydantic.AnyUrl): The reference URL.
        georef_url (pydantic.AnyUrl): The URL of a georeference sidecar file.

    """

    def raster_data_valid(self) -> bool:
        r"""Validate raster data referenced via URL.

        The raster file is checked for projection data using GDAL. \n
        If GDAL detects a georeference file that was not initially provided, it is added to the georef_url attribute.

        Returns:
            bool: True if successful, False otherwise.

        """

        def _check_validity(check_url: AnyUrl) -> bool:
            url = (
                check_url.path
                if check_url.scheme == "file"
                else f"/vsicurl/{check_url}"
            )

            try:
                gdal_info = gdal.Info(url, format="json")
                if gdal_info is None:
                    logger.error(f"Failed to open the dataset {self.ref_url}")
                    return False

                elif not gdal_info.get("geoTransform", None):
                    logger.error(f"No projection data found for {self.ref_url}")
                    return False
                if not gdal_info["stac"].get("proj:epsg", None):
                    logger.warning(f"No EPSG code found for for {self.ref_url}")
                if len(gdal_info["files"]) > 1 and not self.georef_url:
                    self.georef_url = self._parse_url(
                        next(
                            filter(
                                lambda x: os.path.splitext(x)[1]
                                in [".tfw", ".tifw", ".jgw", ".pgw", ".wld"],
                                gdal_info["files"],
                            )
                        ).replace("/vsicurl/", "")
                    )
                return True
            except Exception as e:
                logger.error(f"An error occurred while processing {self.ref_url}: {e}")
                return False

        if not self.georef_content:
            return _check_validity(self.ref_url)
        else:
            _, file_ext = os.path.splitext(os.path.basename(str(self.ref_url)))
            if not file_ext:
                logger.error(f"Could not determine file extension of {self.ref_url}")
                return False
            vsimem_path = f"/vsimem/raster{file_ext}"
            gdal.FileFromMemBuffer(vsimem_path, self.ref_content)
            gdal.FileFromMemBuffer(
                "/vsimem/raster.wld", self.georef_content or io.BytesIO().getvalue()
            )
            return _check_validity(AnyUrl(f"file://{vsimem_path}"))


class _Versions(str, Enum):
    _4_1 = "4.1"
    _5_4 = "5.4"
    _6_0 = "6.0"
    _6_1 = "6.1"
    _plu = "plu"


class MigrationPath:
    """Computes migration path between two XPlanung versions."""

    def __init__(self, from_version: _Versions, to_version: _Versions):
        self.from_version = from_version
        self.to_version = to_version

        self.edges = {
            "4": _Versions._5_4,
            "5": _Versions._6_0,
            "60": [_Versions._6_1, _Versions._plu],
            "61": _Versions._plu,
        }

    def _compute_path(self) -> list[_Versions]:
        path = []
        current_version = self.from_version
        while current_version != self.to_version:
            if not (
                next_version := self.edges.get(
                    current_version.replace(".", "")
                    if current_version.startswith("6")
                    else current_version.split(".")[0]
                )
            ):
                raise ValueError(
                    f"Migration from version {self.from_version} to {self.to_version} not yet implemented"
                )
            if isinstance(next_version, list):
                if self.to_version in next_version:
                    next_version = self.to_version
                else:
                    raise ValueError(
                        f"No migration path from {self.from_version} to {self.to_version}."
                    )
            path.append(
                next_version.value
                if isinstance(next_version, _Versions)
                else next_version
            )
            current_version = next_version
        return path

    @property
    def path(self) -> list[_Versions]:
        """Returns migration path, given the initial and the target version of the plan."""
        return self._compute_path()
