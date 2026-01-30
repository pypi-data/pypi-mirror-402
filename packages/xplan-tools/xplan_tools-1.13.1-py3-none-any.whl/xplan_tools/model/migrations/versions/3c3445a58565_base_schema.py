"""Create the base schema.

Revision ID: 3c3445a58565
Revises:
Create Date: 2025-08-20 14:25:40.121999
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from geoalchemy2.types import Geometry
from sqlalchemy.dialects import postgresql

from xplan_tools.settings import get_settings

# revision identifiers, used by Alembic.
revision: str = "3c3445a58565"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

settings = get_settings()
schema = settings.db_schema
srid = settings.db_srid
views = settings.db_views


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "coretable",
        sa.Column(
            "pk",
            sa.Integer(),
            sa.Identity(always=True),
            nullable=False,
        ),
        sa.Column(
            "id",
            sa.Uuid(as_uuid=False),
            nullable=False,
        ),
        sa.Column(
            "featuretype",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "properties",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "geometry",
            Geometry(
                srid=srid,
                spatial_index=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "geometry_type",
            sa.Text(),
            sa.Computed(
                "CASE WHEN (GeometryType(geometry) LIKE '%%POINT') THEN 'point' WHEN (GeometryType(geometry) LIKE '%%STRING' OR GeometryType(geometry) LIKE '%%CURVE' OR GeometryType(geometry) = 'LINEARRING') THEN 'line' WHEN (GeometryType(geometry) LIKE '%%POLYGON' OR GeometryType(geometry) LIKE '%%SURFACE') THEN 'polygon' ELSE 'nogeom' END",
            ),
            nullable=True,
        ),
        sa.Column(
            "appschema",
            sa.String(length=10),
            nullable=False,
        ),
        sa.Column(
            "version",
            sa.String(length=3),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("pk"),
        sa.UniqueConstraint("id"),
        schema=schema,
    )
    op.create_index(
        op.f("ix_coretable_appschema"),
        "coretable",
        ["appschema"],
        schema=schema,
        unique=False,
    )
    op.create_index(
        op.f("ix_coretable_featuretype"),
        "coretable",
        ["featuretype"],
        schema=schema,
        unique=False,
    )
    op.create_index(
        op.f("ix_coretable_geometry_type"),
        "coretable",
        ["geometry_type"],
        schema=schema,
        unique=False,
    )
    op.create_index(
        op.f("ix_coretable_version"),
        "coretable",
        ["version"],
        schema=schema,
        unique=False,
    )
    op.create_index(
        op.f("ix_coretable_geometry"),
        "coretable",
        ["geometry"],
        schema=schema,
        postgresql_using="gist",
    )
    op.create_table(
        "refs",
        sa.Column(
            "pk",
            sa.BigInteger(),
            sa.Identity(always=True),
            nullable=False,
        ),
        sa.Column(
            "base_id",
            sa.Uuid(as_uuid=False),
            nullable=False,
        ),
        sa.Column(
            "related_id",
            sa.Uuid(as_uuid=False),
            nullable=False,
        ),
        sa.Column(
            "rel",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "rel_inv",
            sa.String(length=50),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["base_id"],
            [f"{schema or 'public'}.coretable.id"],
            ondelete="CASCADE",
            initially="DEFERRED",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["related_id"],
            [f"{schema or 'public'}.coretable.id"],
            ondelete="CASCADE",
            initially="DEFERRED",
            deferrable=True,
        ),
        sa.PrimaryKeyConstraint("pk"),
        schema=schema,
    )

    if views:
        view_context = {"schema": schema or "public", "srid": srid}
        op.execute(
            sa.DDL(
                """
                create or replace view %(schema)s.coretable_points as
                select pk, id, featuretype, properties, ST_Multi(geometry)::geometry(MultiPoint, %(srid)s) as geometry, appschema, version
                from %(schema)s.coretable
                where geometry_type = 'point'
                """,
                view_context,
            )
        )
        op.execute(
            sa.DDL(
                """
                create or replace view %(schema)s.coretable_lines as
                select pk, id, featuretype, properties, ST_Multi(ST_ForceCurve(geometry))::geometry(MultiCurve, %(srid)s) as geometry, appschema, version
                from %(schema)s.coretable
                where geometry_type = 'line'
                """,
                view_context,
            )
        )
        op.execute(
            sa.DDL(
                """
                create or replace view %(schema)s.coretable_polygons as
                select pk, id, featuretype, properties, ST_Multi(ST_ForceCurve(geometry))::geometry(MultiSurface, %(srid)s) as geometry, appschema, version
                from %(schema)s.coretable
                where geometry_type = 'polygon'
                """,
                view_context,
            )
        )
        op.execute(
            sa.DDL(
                """
                create or replace view %(schema)s.coretable_nogeoms as
                select pk, id, featuretype, properties, geometry, appschema, version
                from %(schema)s.coretable
                where geometry_type = 'nogeom'
                """,
                view_context,
            ),
        )


def downgrade() -> None:
    """Downgrade schema."""
    view_context = {"schema": schema or "public"}
    op.execute(
        sa.DDL(
            """
            drop view if exists %(schema)s.coretable_nogeoms
            """,
            view_context,
        ),
    )
    op.execute(
        sa.DDL(
            """
            drop view if exists %(schema)s.coretable_polygons
            """,
            view_context,
        ),
    )
    op.execute(
        sa.DDL(
            """
            drop view if exists %(schema)s.coretable_lines
            """,
            view_context,
        ),
    )
    op.execute(
        sa.DDL(
            """
            drop view if exists %(schema)s.coretable_points
            """,
            view_context,
        ),
    )
    op.drop_table(
        "refs",
        schema=schema,
    )
    op.drop_index(
        op.f("ix_coretable_version"),
        table_name="coretable",
        schema=schema,
    )
    op.drop_index(
        op.f("ix_coretable_geometry_type"),
        table_name="coretable",
        schema=schema,
    )
    op.drop_index(
        op.f("ix_coretable_featuretype"),
        table_name="coretable",
        schema=schema,
    )
    op.drop_index(
        op.f("ix_coretable_appschema"),
        table_name="coretable",
        schema=schema,
    )
    op.drop_index(
        op.f("ix_coretable_geometry"),
        table_name="coretable",
        schema=schema,
    )
    op.drop_table(
        "coretable",
        schema=schema,
    )
