"""Module containing the GMLAdapter for reading from and writing to gml."""

import logging
from uuid import uuid4

from lxml import etree
from osgeo import ogr, osr
from pydantic import AnyUrl, ValidationInfo

from xplan_tools.model import model_factory
from xplan_tools.util import parse_srs, parse_uuid

logger = logging.getLogger(__name__)


class GMLAdapter:
    """Class to add GML transformation methods to XPlan pydantic model via inheritance."""

    def _to_etree(
        self,
        **kwargs,
    ) -> etree._Element:
        """Converts XPlan and INSPIRE PLU object to lxml etree Element."""

        def parse_property(name, value, index: int | None = None):
            gml_name = f"{{{ns}}}{name}"
            if name == "id":
                feature.set("{http://www.opengis.net/gml/3.2}id", f"GML_{value}")
                if self.get_appschema() != "plu":
                    etree.SubElement(
                        feature,
                        "{http://www.opengis.net/gml/3.2}identifier",
                        attrib={"codeSpace": "urn:uuid"},
                    ).text = value
                return
            # Patch for vertikaleDifferenzierung being optional with a default value of False instead of None
            if name == "vertikaleDifferenzierung" and value is False:
                return
            if isinstance(value, dict) and (void := value.get("nilReason")):
                etree.SubElement(
                    feature,
                    gml_name,
                    attrib={
                        "nilReason": str(void),
                        "{http://www.w3.org/2001/XMLSchema-instance}nil": "true",
                    },
                )
                return
            match prop_info["stereotype"]:
                case "BasicType" | "Enumeration" | "Temporal":
                    etree.SubElement(feature, gml_name).text = (
                        str(value).lower() if isinstance(value, bool) else str(value)
                    )
                case "Geometry":
                    geometry = ogr.CreateGeometryFromWkt(self.get_geom_wkt())
                    if geometry:
                        if kwargs.get("feature_srs", True):
                            srid = osr.SpatialReference()
                            srid.ImportFromEPSG(int(self.get_geom_srid()))
                            geometry.AssignSpatialReference(srid)
                        etree.SubElement(feature, name).append(
                            etree.fromstring(
                                geometry.ExportToGML(
                                    options=[
                                        "FORMAT=GML32",
                                        f"GMLID=GML_{uuid4()}",
                                        (
                                            "SRSNAME_FORMAT=OGC_URL"
                                            if self.get_appschema() == "plu"
                                            else "GML3_LONGSRS=NO"
                                        ),
                                        "NAMESPACE_DECL=YES",
                                    ]
                                )
                            )
                        )
                        geometry = None
                        srid = None
                case "Measure":
                    etree.SubElement(
                        feature, gml_name, attrib={"uom": value["uom"]}
                    ).text = str(value["value"])
                case "Codelist":
                    if "inspire" in self.namespace_uri:
                        etree.SubElement(
                            feature,
                            gml_name,
                            attrib={"{http://www.w3.org/1999/xlink}href": str(value)},
                        )
                    else:
                        codevalue = value.split(
                            ":" if value.startswith("urn") else "/"
                        )[-1]
                        codespace = value.replace(codevalue, "")
                        etree.SubElement(
                            feature, gml_name, attrib={"codeSpace": codespace}
                        ).text = codevalue
                case "Association":
                    etree.SubElement(
                        feature,
                        gml_name,
                        attrib={
                            "{http://www.w3.org/1999/xlink}href": f"#GML_{str(value)}"
                        },
                    )
                case "DataType":
                    if prop_info["typename"] == "CI_Date":
                        ci_date = etree.Element(
                            "{http://www.isotc211.org/2005/gmd}CI_Date"
                        )
                        etree.SubElement(
                            etree.SubElement(
                                ci_date, "{http://www.isotc211.org/2005/gmd}date"
                            ),
                            "{http://www.isotc211.org/2005/gco}Date",
                        ).text = str(self.date)
                        etree.SubElement(
                            etree.SubElement(
                                ci_date, "{http://www.isotc211.org/2005/gmd}dateType"
                            ),
                            "{http://www.isotc211.org/2005/gmd}CI_DateTypeCode",
                            attrib={
                                "codeList": "https://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_DateTypeCode",
                                "codeListValue": "creation",
                            },
                        )
                        etree.SubElement(feature, gml_name).append(ci_date)
                    else:
                        model_value = getattr(self, name)
                        if isinstance(model_value, list):
                            value_item = model_value[index]
                            etree.SubElement(feature, gml_name).append(
                                value_item._to_etree()
                            )
                        else:
                            etree.SubElement(feature, gml_name).append(
                                model_value._to_etree()
                            )

        ns = self.namespace_uri.replace("base/4.0", "base/3.3")
        feature = etree.Element(f"{{{ns}}}{self.get_name()}")

        data = self.model_dump(mode="json", exclude_unset=True, exclude_none=True)

        for name, value in data.items():
            prop_info = self.get_property_info(name)
            if isinstance(value, list):
                for index, item in enumerate(value):
                    parse_property(name, item, index)
            else:
                parse_property(name, value)
        return feature

    @classmethod
    def _from_etree(cls, feature: etree._Element, info: ValidationInfo) -> dict:
        """Creates a XPlan object instance from a lxml etree Element."""
        appschema = info.context.get("appschema")
        data = {}
        id = feature.get("{http://www.opengis.net/gml/3.2}id")
        properties = None

        if id:
            data["id"] = parse_uuid(id, raise_exception=True)

            gml_geometry = feature.xpath(
                "./*[namespace-uri() != 'http://www.opengis.net/gml/3.2']/*[namespace-uri() = 'http://www.opengis.net/gml/3.2']"
            )

            if gml_geometry:
                ogr_geometry = (
                    ogr.CreateGeometryFromGML(
                        etree.tostring(gml_geometry[0], encoding="unicode")
                    )
                    if len(gml_geometry) > 0
                    else None
                )
                if ogr_geometry:
                    try:
                        if srs := gml_geometry[0].get("srsName", None):
                            srid = parse_srs(srs)
                        else:
                            srid = info.context.get("srid")
                        data[cls.get_geom_field()] = {
                            "srid": srid,
                            "wkt": ogr_geometry.ExportToWkt(),
                        }

                    except Exception:
                        raise ValueError("SRID could not be determined")

            properties = feature.xpath(
                "./*[namespace-uri() != 'http://www.opengis.net/gml/3.2' and not(namespace-uri(./*) = 'http://www.opengis.net/gml/3.2')]"
            )

        else:
            properties = list(feature)

        for property in properties:
            if (
                (not property.text or property.text.strip() == "")
                and not property.attrib
                and not len(property)
            ):
                continue

            name = etree.QName(property).localname
            prop_info = cls.get_property_info(name)
            value = None
            if list(property):  # Test for child elements -> data type
                value = model_factory(
                    etree.QName(property[0]).localname, cls.__module__[-2:], appschema
                )._from_etree(property[0], info)
            elif (
                id
                and (href := property.get("{http://www.w3.org/1999/xlink}href"))
                and href.startswith("#")
            ):
                value = parse_uuid(href, raise_exception=True)
            elif uom := property.get("uom"):
                value = {"value": property.text, "uom": uom}
            elif prop_info["stereotype"] == "Codelist":
                try:
                    value = AnyUrl((property.get("codeSpace") or "") + property.text)
                except Exception:
                    value = f"urn:{cls.get_appschema()}:{prop_info['typename']}:{property.text}"
            else:
                value = property.text

            if prop_info["list"]:
                data.setdefault(name, []).append(value)
            else:
                data[name] = value
        return data
