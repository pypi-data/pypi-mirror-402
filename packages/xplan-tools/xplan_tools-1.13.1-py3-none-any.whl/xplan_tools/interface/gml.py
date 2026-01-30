"""Module containing the class for extracting plans from and writing to GML datasources."""

import datetime
import io
import logging
import re
from typing import IO
from uuid import uuid4

import lxml.etree as etree

from xplan_tools.model import model_factory
from xplan_tools.model.base import BaseCollection
from xplan_tools.util import get_envelope, parse_srs, parse_uuid

from .base import BaseRepository

logger = logging.getLogger(__name__)


class GMLRepository(BaseRepository):
    """Repository class for loading from and writing to GML files or file-like objects.

    Given a plan, either xplan or INSPIRE PLU, the data is saved as GML with according namespaces
    and structure. Reading data from datasource and retrieving the data version is currently only
    supported for xplan data.
    """

    def __init__(
        self,
        datasource: str | IO = "",
    ) -> None:
        """Initializes the GML Repository.

        Args:
            datasource: A file path as a String or a file-like object.
        """
        self.datasource = datasource
        self.appschema = None
        self.version = None

    @property
    def content(self):
        """The parsed XML tree."""
        return etree.parse(self.datasource).getroot()

    def _get_appschema(self):
        """Returns application schema of data."""
        xsi = self.content.nsmap.get("xsi", self.content.nsmap.get(None, ""))
        self.content.attrib.get(f"{{{xsi}}}schemaLocation")

        if re.search(
            "http://www[.]xtrasse[.]de/[0-9][.][0-9]",
            self.content.get(
                f"{{{xsi}}}schemaLocation", self.content.nsmap.get(None, "")
            ),
        ):
            return "xtrasse"
        elif re.search(
            "http://www[.]xwaermeplan[.]de/[0-9]/[0-9]",
            self.content.get(
                f"{{{xsi}}}schemaLocation", self.content.nsmap.get(None, "")
            ),
        ):
            return "xwp"
        elif self.content.nsmap.get(
            "xplan", self.content.nsmap.get(None, "")
        ) or re.search(
            "http://www[.]xplanung[.]de/xplangml/[0-9]/[0-9]",
            self.content.get(
                f"{{{xsi}}}schemaLocation", self.content.nsmap.get(None, "")
            ),
        ):
            return "xplan"
        else:
            raise ValueError("No supported application schema found.")

    def _get_version(self):
        """Returns version of xplan or xtrasse data."""
        if self.appschema == "xtrasse":
            uri = self.content.nsmap.get("xtrasse", self.content.nsmap.get(None, ""))
            return uri.split("http://www.xtrasse.de/")[1].replace("/", ".")
        elif self.appschema == "xwp":
            uri = self.content.nsmap.get(
                "xwaermeplan", self.content.nsmap.get(None, "")
            )
            return uri.split("http://www.xwaermeplan.de/")[1].replace("/", ".")
        else:
            uri = self.content.nsmap.get("xplan", self.content.nsmap.get(None, ""))
            if "xplan" not in uri:
                if not (
                    match := re.search(
                        "http://www[.]xplanung[.]de/xplangml/[0-9]/[0-9]",
                        self.content.get(
                            "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation"
                        ),
                    )
                ):
                    raise ValueError(
                        "No xplan-Namespace found in namespace bindings and schemaLocation"
                    )
                else:
                    uri = match.group(0)
            return uri.split("http://www.xplanung.de/xplangml/")[1].replace("/", ".")

    def _write_to_datasource(self, tree: etree._ElementTree):
        xml_string = etree.tostring(
            tree, pretty_print=True, xml_declaration=True, encoding="UTF-8"
        )
        match self.datasource:
            case io.StringIO():
                self.datasource.write(xml_string.decode())
            case io.BytesIO():
                self.datasource.write(xml_string)
            case str():
                with open(self.datasource, "wb") as f:
                    f.write(xml_string)
            case _:
                raise NotImplementedError("Unsupported datasource.")

    def save_all(self, features: BaseCollection, **kwargs: dict) -> None:
        """Saves a Feature Collection to the datasource.

        Args:
            features: A BaseCollection instance.
            **kwargs: Not used in this repository.
        """
        self.appschema = features.appschema
        self.version = features.version

        if self.appschema == "xplan":
            nsmap = {
                None: f"http://www.xplanung.de/xplangml/{self.version.replace('.', '/')}",
                "gml": "http://www.opengis.net/gml/3.2",
                "xlink": "http://www.w3.org/1999/xlink",
                "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            }
            root = etree.Element(
                "XPlanAuszug",
                attrib={
                    "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation": f"{nsmap[None]} https://repository.gdi-de.org/schemas/de.xleitstelle.xplanung/{self.version}/XPlanung-Operationen.xsd",
                    "{http://www.opengis.net/gml/3.2}id": f"GML_{uuid4()}",
                },
                nsmap=nsmap,
            )
        elif self.appschema == "xtrasse":
            nsmap = {
                None: f"http://www.xtrasse.de/{self.version}",
                "gml": "http://www.opengis.net/gml/3.2",
                "xml": "http://www.w3.org/XML/1998/namespace",
                "xlink": "http://www.w3.org/1999/xlink",
                "xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "sf": "http://www.opengis.net/ogcapi-features-1/1.0/sf",
            }

            root = etree.Element(
                "{http://www.opengis.net/ogcapi-features-1/1.0/sf}FeatureCollection",
                attrib={
                    "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation": f"{nsmap[None]} https://repository.gdi-de.org/schemas/de.xleitstelle.xtrasse/2.0/XML/XTrasse.xsd {nsmap['sf']} http://schemas.opengis.net/ogcapi/features/part1/1.0/xml/core-sf.xsd {nsmap['gml']} https://schemas.opengis.net/gml/3.2.1/gml.xsd",
                    "{http://www.opengis.net/gml/3.2}id": f"GML_{uuid4()}",
                },
                nsmap=nsmap,
            )
        elif self.appschema == "xwp":
            nsmap = {
                None: f"http://www.xwaermeplan.de/{self.version.replace('.', '/')}",
                "gml": "http://www.opengis.net/gml/3.2",
                "xml": "http://www.w3.org/XML/1998/namespace",
                "xlink": "http://www.w3.org/1999/xlink",
                "xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "sf": "http://www.opengis.net/ogcapi-features-1/1.0/sf",
            }

            root = etree.Element(
                "{http://www.opengis.net/ogcapi-features-1/1.0/sf}FeatureCollection",
                attrib={
                    "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation": f"{nsmap[None]} https://gitlab.opencode.de/xleitstelle/xwaermeplan/spezifikation/-/raw/main/xsd/waermeplan.xsd {nsmap['sf']} http://schemas.opengis.net/ogcapi/features/part1/1.0/xml/core-sf.xsd {nsmap['gml']} https://schemas.opengis.net/gml/3.2.1/gml.xsd",
                    "{http://www.opengis.net/gml/3.2}id": f"GML_{uuid4()}",
                },
                nsmap=nsmap,
            )

        elif self.appschema == "plu":
            nsmap = {
                None: "http://inspire.ec.europa.eu/schemas/plu/4.0",
                "gss": "http://www.isotc211.org/2005/gss",
                "xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "gco": "http://www.isotc211.org/2005/gco",
                "gml": "http://www.opengis.net/gml/3.2",
                "base": "http://inspire.ec.europa.eu/schemas/base/3.3",
                "lunom": "http://inspire.ec.europa.eu/schemas/lunom/4.0",
                "base2": "http://inspire.ec.europa.eu/schemas/base2/2.0",
                "gmd": "http://www.isotc211.org/2005/gmd",
                "xlink": "http://www.w3.org/1999/xlink",
                "wfs": "http://www.opengis.net/wfs/2.0",
            }

            root = etree.Element(
                "{http://www.opengis.net/wfs/2.0}FeatureCollection",
                attrib={
                    "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation": f"{nsmap[None]} https://inspire.ec.europa.eu/schemas/plu/4.0/PlannedLandUse.xsd {nsmap['wfs']} https://schemas.opengis.net/wfs/2.0/wfs.xsd {nsmap['gml']} https://schemas.opengis.net/gml/3.2.1/gml.xsd"
                },
                nsmap=nsmap,
            )

        if self.appschema not in ["xtrasse", "xwp"]:
            bounds = etree.SubElement(
                root,
                (
                    "{http://www.opengis.net/gml/3.2}boundedBy"
                    if self.appschema == "xplan"
                    else "{http://www.opengis.net/wfs/2.0}boundedBy"
                ),
            )

        geoms = []
        feature_number = 0
        for feature in features.get_features():
            if feature:
                feature_number += 1
                if (geom_wkt := feature.get_geom_wkt()) and (
                    "Plan" in feature.get_name()
                ):
                    geoms.append(geom_wkt)
                    srs = feature.get_geom_srid()
                etree.SubElement(
                    root,
                    (
                        "{http://www.opengis.net/gml/3.2}featureMember"
                        if self.appschema == "xplan"
                        else (
                            "{http://www.opengis.net/ogcapi-features-1/1.0/sf}featureMember"
                            if self.appschema in ["xtrasse", "xwp"]
                            else "{http://www.opengis.net/wfs/2.0}member"
                        )
                    ),
                ).append(
                    feature.model_dump_gml(feature_srs=kwargs.get("feature_srs", True))
                )
        bbox = get_envelope(geoms)
        attrib = (
            {
                "srsName": f"http://www.opengis.net/def/crs/EPSG/0/{srs}"
            }  # TODO: Anpassung für Fälle abseits von crs?
            if self.appschema == "plu"
            else {"srsName": f"EPSG:{srs}"}
        )

        if self.appschema not in ["xtrasse", "xwp"]:
            envelope = etree.SubElement(
                bounds,
                "{http://www.opengis.net/gml/3.2}Envelope",
                attrib=attrib,
            )
            etree.SubElement(
                envelope, "{http://www.opengis.net/gml/3.2}lowerCorner"
            ).text = f"{bbox[0]} {bbox[2]}"
            etree.SubElement(
                envelope, "{http://www.opengis.net/gml/3.2}upperCorner"
            ).text = f"{bbox[1]} {bbox[3]}"

        if self.appschema == "plu":
            root.set("numberMatched", str(feature_number))
            root.set("numberReturned", str(feature_number))
            root.set("timeStamp", str(datetime.datetime.now().isoformat()))

        tree = etree.ElementTree(root)
        # tree.write(
        #     self.datasource, pretty_print=True, xml_declaration=True, encoding="UTF-8"
        # )
        self._write_to_datasource(tree)

    def get_all(
        self, always_generate_ids: bool = False, **kwargs: dict
    ) -> BaseCollection:
        """Retrieves a Feature Collection to the datasource.

        Args:
            always_generate_ids: Generate new Feature IDs even if GML IDs can be parsed to UUIDs.
        """
        self.appschema = self._get_appschema()
        self.version = self._get_version()

        def update_related_features():
            for xlink in root.findall(".//*[@{http://www.w3.org/1999/xlink}href]"):
                href = xlink.get("{http://www.w3.org/1999/xlink}href")
                if new_id := id_mapping.get(href[1:], None):
                    xlink.set("{http://www.w3.org/1999/xlink}href", f"#{new_id}")

        def validate_gml_id(feature: etree._Element):
            gml_id = feature.get("{http://www.opengis.net/gml/3.2}id")
            uuid = parse_uuid(gml_id)
            if (
                not uuid
                or (uuid and collection.get(uuid, None) == "placeholder")
                or always_generate_ids
            ):
                new_id = f"GML_{uuid4()}"
                feature.set("{http://www.opengis.net/gml/3.2}id", new_id)
                id_mapping[gml_id] = new_id
                logger.info(f"GML ID '{gml_id}' replaced with UUIDv4 '{new_id}'")
            else:
                collection[uuid] = "placeholder"

        root: etree._ElementTree = self.content

        try:
            if etree.QName(root).namespace in [
                "http://www.opengis.net/wfs/2.0",
                "http://www.opengis.net/ogcapi-features-1/1.0/sf",
            ]:
                elem = root.find(
                    "./{http://www.opengis.net/gml/3.2}boundedBy/{http://www.opengis.net/gml/3.2}Envelope"
                ) or next(root.iterfind(".//*[@srsName]"))
                srs = elem.get("srsName")
            else:
                srs = root.find(
                    "./{http://www.opengis.net/gml/3.2}boundedBy/{http://www.opengis.net/gml/3.2}Envelope"
                ).get("srsName")
        except (AttributeError, StopIteration, KeyError):
            raise ValueError("No SRS could be found")
        else:
            srid = parse_srs(srs)

        collection = {}
        id_mapping = {}

        for feature in root.iterfind("./*/*"):
            if etree.QName(feature).namespace == "http://www.opengis.net/gml/3.2":
                continue
            elif etree.QName(feature).namespace == "http://www.opengis.net/wfs/2.0":
                for additional_object in feature.iterfind("./*/*"):
                    validate_gml_id(additional_object)
            else:
                validate_gml_id(feature)

        if id_mapping:
            update_related_features()

        for feature in root.iterfind("./*/*"):
            if etree.QName(feature).namespace == "http://www.opengis.net/gml/3.2":
                continue
            elif etree.QName(feature).namespace == "http://www.opengis.net/wfs/2.0":
                for additional_object in feature.iterfind("./*/*"):
                    # set_srid_for_geom_feature(additional_object)
                    model = model_factory(
                        etree.QName(additional_object).localname,
                        self.version,
                        self.appschema,
                    ).model_validate(
                        additional_object,
                        context={"srid": srid, "appschema": self.appschema},
                    )
                    collection[model.id] = model
            else:
                # set_srid_for_geom_feature(feature)
                model = model_factory(
                    etree.QName(feature).localname, self.version, self.appschema
                ).model_validate(
                    feature, context={"srid": srid, "appschema": self.appschema}
                )
                collection[model.id] = model
        return BaseCollection(
            features=collection,
            srid=srid,
            version=self.version,
            appschema=self.appschema,
        )
