"""Module containing the CoretableAdapter for reading from and writing to coretable feature object."""

from uuid import UUID

from xplan_tools.model.orm import Feature, Refs


class CoretableAdapter:
    """Class to add ORM model - i.e. coretable - transformation methods to XPlan pydantic model via inheritance."""

    def _to_coretable(
        self, bulk_mode: bool = False
    ) -> Feature | tuple[dict, list[dict]]:
        """Converts a BaseFeature to a Coretable Feature object."""
        properties = self.model_dump(mode="json", exclude_none=True)
        id = properties.pop("id")
        geometry = None
        if geom := properties.pop(self.get_geom_field(), None):
            geometry = f"SRID={geom['srid']};{geom['wkt']}"
        refs = []
        refs_inv = []
        for a, b in self:
            if isinstance(b, UUID):
                prop_info = self.get_property_info(a)
                assoc_info = prop_info["assoc_info"]
                # special treatment for FP_Plan <-> FP_Bereich due to inconsistent association ends
                if (
                    prop_info["typename"] == "FP_Plan" and float(self.get_version()) < 7
                ) or assoc_info["source_or_target"] == "source":
                    refs_inv.append(
                        {
                            "base_id": str(b),
                            "related_id": self.id,
                            "rel": assoc_info["reverse"],
                            "rel_inv": a,
                        }
                    )
                elif assoc_info["source_or_target"] == "target":
                    refs.append(
                        {
                            "base_id": self.id,
                            "related_id": str(b),
                            "rel": a,
                            "rel_inv": assoc_info["reverse"],
                        }
                    )
                else:
                    refs.append(
                        {
                            "base_id": self.id,
                            "related_id": str(b),
                            "rel": a,
                            "rel_inv": None,
                        }
                    )
                properties.pop(a)
            elif isinstance(b, list):
                for item in b:
                    if isinstance(item, UUID):
                        prop_info = self.get_property_info(a)
                        assoc_info = prop_info["assoc_info"]
                        if (
                            prop_info["typename"] == "FP_Bereich"
                            and float(self.get_version()) < 7
                        ) or assoc_info["source_or_target"] == "target":
                            refs.append(
                                {
                                    "base_id": self.id,
                                    "related_id": str(item),
                                    "rel": a,
                                    "rel_inv": assoc_info["reverse"],
                                }
                            )
                        elif assoc_info["source_or_target"] == "source":
                            refs_inv.append(
                                {
                                    "base_id": str(item),
                                    "related_id": self.id,
                                    "rel": assoc_info["reverse"],
                                    "rel_inv": a,
                                }
                            )
                        else:
                            refs.append(
                                {
                                    "base_id": self.id,
                                    "related_id": str(item),
                                    "rel": a,
                                    "rel_inv": None,
                                }
                            )
                        properties.pop(a, None)
            if a == "hatGenerAttribut" and b is not None:
                properties["hatGenerAttribut"] = []
                for item in b:
                    gener_att = item.model_dump(mode="json")
                    gener_att[f"wert_{item.get_name()}"] = gener_att.pop("wert")
                    gener_att["datatype"] = item.get_name()
                    properties["hatGenerAttribut"].append(gener_att)
        feature = {
            "id": id,
            "featuretype": self.get_name(),
            "properties": properties,
            "geometry": geometry,
            "appschema": self.get_appschema(),
            "version": self.get_version(),
        }
        if bulk_mode:
            return feature, [*refs, *refs_inv]
        else:
            orm_feature = Feature(**feature)
            if refs:
                orm_feature.refs = [Refs(**ref) for ref in refs]
            if refs_inv:
                orm_feature.refs_inv = [Refs(**ref) for ref in refs_inv]
            return orm_feature

    @classmethod
    def _from_coretable(cls, feature: Feature) -> dict:
        """Returns the data from a coretable Feature object."""
        data = feature.properties | {"id": str(feature.id)}
        if feature.geometry:
            geom = str(feature.geometry).split(";")
            data[cls.get_geom_field()] = {
                "srid": int(geom[0].replace("SRID=", "")),
                "wkt": geom[1],
            }
        for ref in feature.refs:
            if cls.get_property_info(ref.rel)["list"]:
                data.setdefault(ref.rel, []).append(ref.related_id)
            else:
                data[ref.rel] = ref.related_id
        for ref in feature.refs_inv:
            if ref.rel_inv:
                if cls.get_property_info(ref.rel_inv)["list"]:
                    data.setdefault(ref.rel_inv, []).append(ref.base_id)
                else:
                    data[ref.rel_inv] = ref.base_id
        if gener_atts := data.get("hatGenerAttribut", None):
            updates = []
            for gener_att in gener_atts:
                update = {}
                for key, value in gener_att.items():
                    if key == "name":
                        update[key] = value
                    elif "wert" in key:
                        update["wert"] = value
                updates.append(update)
            data["hatGenerAttribut"] = updates
        return data
