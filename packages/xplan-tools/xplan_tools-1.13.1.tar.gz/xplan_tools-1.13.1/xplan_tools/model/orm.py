import json
from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from geoalchemy2 import Geometry as GeometryBase
from geoalchemy2 import WKTElement
from geoalchemy2.admin.dialects.geopackage import register_gpkg_mapping
from geoalchemy2.admin.dialects.sqlite import register_sqlite_mapping
from sqlalchemy import (
    JSON,
    BigInteger,
    Computed,
    DateTime,
    Dialect,
    ForeignKey,
    Identity,
    Integer,
    String,
    Text,
    Uuid,
    case,
    cast,
    literal,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB, JSONPATH
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
)
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator

from xplan_tools.settings import get_settings
from xplan_tools.util import linearize_geom

register_sqlite_mapping({"ST_AsEWKT": "AsEWKT"})
register_gpkg_mapping({"ST_AsEWKT": "AsEWKT"})


class Base(DeclarativeBase):
    pass


class Geometry(GeometryBase):
    from_text = "ST_GeomFromEWKT"
    as_binary = "ST_AsEWKT"
    ElementType = WKTElement
    cache_ok = True

    def bind_processor(self, dialect):
        def process(bindvalue):
            # Linearize Curve Geometries for compatibility
            if bindvalue is not None and dialect.name in ["geopackage", "sqlite"]:
                return linearize_geom(bindvalue)
            return bindvalue

        return process

    @staticmethod
    def _geometry_type(value):
        return func.GeometryType(value)

    @staticmethod
    def _is_polygon(value):
        geometry_type_name = Geometry._geometry_type(value)
        return geometry_type_name.like("%POLYGON") | geometry_type_name.like("%SURFACE")

    @staticmethod
    def _is_line(value):
        geometry_type_name = Geometry._geometry_type(value)
        return (
            geometry_type_name.like("%STRING")
            | geometry_type_name.like("%CURVE")
            | (geometry_type_name == literal("LINEARRING"))
        )

    @staticmethod
    def _is_point(value):
        geometry_type_name = Geometry._geometry_type(value)
        return geometry_type_name.like("%POINT")

    @staticmethod
    def _geometry_type_case(column):
        point = Geometry._is_point(column)
        line = Geometry._is_line(column)
        polygon = Geometry._is_polygon(column)
        return case(
            (point, literal("point")),
            (line, literal("line")),
            (polygon, literal("polygon")),
            else_=literal("nogeom"),
        )


class PGGeometry(TypeDecorator):
    impl = Geometry
    cache_ok = True

    def bind_expression(self, bindvalue):
        """Transform incoming geometries to the SRID of the DB and force CCW orientation for polygons."""
        is_polygon = Geometry._is_polygon(cast(bindvalue, Geometry))
        case_clause = case(
            (is_polygon, func.ST_ForcePolygonCCW(bindvalue)),
            else_=bindvalue,
        )
        return func.ST_Transform(
            case_clause,
            func.Find_SRID(
                get_settings().db_schema or "public", "coretable", "geometry"
            ),
            type_=self,
        )


class TextJSON(TypeDecorator):
    impl = Text
    cache_ok = True

    def process_bind_param(self, value: dict, _: Dialect) -> Any:
        return json.dumps(value)

    def process_result_value(self, value: str, _: Dialect):
        return json.loads(value)


class Feature(Base):
    __tablename__ = "coretable"
    __table_args__ = {"schema": get_settings().db_schema}
    pk: Mapped[int] = mapped_column(
        Integer().with_variant(BigInteger, "postgresql"),
        Identity(always=True),
        primary_key=True,
    )
    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=False).with_variant(Text, "geopackage"),
        unique=True,
    )
    featuretype: Mapped[str] = mapped_column(
        String(50).with_variant(Text, "geopackage"), index=True
    )
    properties: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql").with_variant(TextJSON, "geopackage")
    )
    geometry: Mapped[Optional[str]] = mapped_column(
        Geometry(spatial_index=False).with_variant(
            PGGeometry(spatial_index=False), "postgresql"
        )
    )
    geometry_type: Mapped[Optional[str]] = mapped_column(
        Text,
        Computed(Geometry._geometry_type_case(geometry)),
        index=True,
    )
    appschema: Mapped[str] = mapped_column(
        String(10).with_variant(Text, "geopackage"), index=True
    )
    version: Mapped[str] = mapped_column(
        String(3).with_variant(Text, "geopackage"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now()
    )
    refs: Mapped[list["Refs"]] = relationship(
        back_populates="feature",
        cascade="all, delete-orphan",
        primaryjoin="Feature.id==Refs.base_id",
        lazy="selectin",
        passive_deletes=True,
    )
    refs_inv: Mapped[list["Refs"]] = relationship(
        back_populates="feature_inv",
        cascade="all, delete-orphan",
        primaryjoin="Feature.id==Refs.related_id",
        lazy="selectin",
        passive_deletes=True,
    )

    __mapper_args__ = {"primary_key": [id]}

    def __repr__(self) -> str:
        return f"Feature(id={self.id!r}, featuretype={self.featuretype!r}, properties={self.properties!r}, version={self.version!r}, refs={self.refs!r}, refs_inv={self.refs_inv!r})"

    def related_features(
        self,
        session: Session,
        *,
        direction: Literal["children", "parents", "both"] = "both",
        depth: int = 0,
        featuretypes: set[str] = set(),
        featuretype_regex: str = "",
        exclude_ids: set[str] = set(),
        regex_op: Literal["~", "~*", "!~", "!~*"] = "~",
        property_jsonpath: str = "",
    ) -> list["Feature"]:
        """Return all Features related to this Feature via Refs.

        Performs a cycle-safe breadth-first traversal of the feature graph,
        issuing batched edge queries per depth level. Results are identical
        regardless of the starting node.

        Args:
            session: SQLAlchemy session.
            direction: children, parents, or both.
            depth: Optional max traversal depth (0 = unbounded).
            featuretypes: Optional set of featuretype names to include.
            featuretype_regex: Optional regex applied to featuretype. Only supported with PostgreSQL.
            exclude_ids: Optional set of Feature IDs to exclude.
            regex_op: PostgreSQL regex operator.
            property_jsonpath: Optional JSONPath filter on Feature.properties. Only supported with PostgreSQL.
        """
        dialect = session.get_bind().dialect.name
        if dialect != "postgresql":
            if featuretype_regex:
                raise NotImplementedError(
                    f"regex expressions not supported by {dialect}"
                )
            if property_jsonpath:
                raise InvalidRequestError(
                    f"jsonpath expressions not supported by {dialect}"
                )

        if depth < 0:
            return []

        walk_children = direction in ("children", "both")
        walk_parents = direction in ("parents", "both")

        visited: set[UUID] = {self.id}
        related_ids: set[UUID] = set()
        frontier: set[UUID] = {self.id}
        depth_level = 0

        while frontier:
            if depth and depth_level >= depth:
                break

            next_frontier: set[UUID] = set()
            frontier_tuple = tuple(frontier)

            if walk_children and frontier_tuple:
                child_query = select(Refs.related_id).where(
                    Refs.base_id.in_(frontier_tuple)
                )
                for child_id in session.scalars(child_query):
                    if child_id in visited:
                        continue
                    visited.add(child_id)
                    next_frontier.add(child_id)
                    if child_id not in exclude_ids:
                        related_ids.add(child_id)

            if walk_parents and frontier_tuple:
                parent_query = select(Refs.base_id).where(
                    Refs.related_id.in_(frontier_tuple)
                )
                for parent_id in session.scalars(parent_query):
                    if parent_id in visited:
                        continue
                    visited.add(parent_id)
                    next_frontier.add(parent_id)
                    if parent_id not in exclude_ids:
                        related_ids.add(parent_id)

            frontier = next_frontier
            depth_level += 1

        if not related_ids:
            return []

        stmt = select(Feature).where(Feature.id.in_(tuple(related_ids)))

        if featuretypes:
            stmt = stmt.where(Feature.featuretype.in_(featuretypes))

        if featuretype_regex:
            stmt = stmt.where(Feature.featuretype.op(regex_op)(featuretype_regex))

        if exclude_ids:
            stmt = stmt.where(Feature.id.not_in(exclude_ids))

        if property_jsonpath:
            stmt = stmt.where(
                func.jsonb_path_exists(
                    Feature.properties,
                    literal(property_jsonpath).cast(JSONPATH),
                )
            )

        return session.scalars(stmt).all()


class Refs(Base):
    __tablename__ = "refs"
    __table_args__ = {"schema": get_settings().db_schema}
    pk: Mapped[int] = mapped_column(
        Integer().with_variant(BigInteger, "postgresql"),
        Identity(always=True),
        primary_key=True,
    )
    base_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            Feature.id, ondelete="CASCADE", deferrable=True, initially="DEFERRED"
        ),
        index=True,
    )
    related_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            Feature.id, ondelete="CASCADE", deferrable=True, initially="DEFERRED"
        ),
        index=True,
    )
    rel: Mapped[str] = mapped_column(String(50).with_variant(Text, "geopackage"))
    rel_inv: Mapped[Optional[str]] = mapped_column(
        String(50).with_variant(Text, "geopackage")
    )
    feature: Mapped[Feature] = relationship(
        back_populates="refs",
        primaryjoin="Feature.id==Refs.base_id",
        viewonly=True,
    )
    feature_inv: Mapped[Feature] = relationship(
        back_populates="refs_inv",
        primaryjoin="Feature.id==Refs.related_id",
        viewonly=True,
    )

    __mapper_args__ = {
        "primary_key": [base_id, related_id],
    }

    def __repr__(self) -> str:
        return f"Refs(base_id={self.base_id!r}, related_id={self.related_id!r}, rel={self.rel!r}, rel_inv={self.rel_inv!r})"


class GPKGEXT_Relations(Base):
    __tablename__ = "gpkgext_relations"
    id: Mapped[int] = mapped_column(
        Integer(),
        primary_key=True,
    )
    base_table_name: Mapped[str] = mapped_column(Text())
    base_primary_column: Mapped[str] = mapped_column(Text())
    related_table_name: Mapped[str] = mapped_column(Text())
    related_primary_column: Mapped[str] = mapped_column(Text())
    relation_name: Mapped[str] = mapped_column(Text())
    mapping_table_name: Mapped[str] = mapped_column(Text(), unique=True)
