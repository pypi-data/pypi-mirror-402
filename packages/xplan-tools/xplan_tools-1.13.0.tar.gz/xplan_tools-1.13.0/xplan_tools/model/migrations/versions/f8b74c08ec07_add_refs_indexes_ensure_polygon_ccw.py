"""Add refs indexes, ensure polygon CCW.

Revision ID: f8b74c08ec07
Revises: 3c3445a58565
Create Date: 2026-01-08 10:58:26.988690
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from xplan_tools.settings import get_settings

# revision identifiers, used by Alembic.
revision: str = "f8b74c08ec07"
down_revision: Union[str, Sequence[str], None] = "3c3445a58565"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

settings = get_settings()
schema = settings.db_schema


def upgrade() -> None:
    """Upgrade schema.

    Creates indexes on `refs.base_id` and refs.related_id` and normalizes all polygon
    geometries in `coretable.geometry` to counter-clockwise orientation
    using `ST_ForcePolygonCCW` in-place.
    """
    op.create_index(
        op.f("ix_refs_base_id"),
        "refs",
        ["base_id"],
        schema=schema,
        if_not_exists=True,
    )
    op.create_index(
        op.f("ix_refs_related_id"),
        "refs",
        ["related_id"],
        schema=schema,
        if_not_exists=True,
    )
    coretable = sa.Table(
        "coretable",
        sa.MetaData(),
        sa.Column("geometry"),
        sa.Column("geometry_type"),
        schema=schema,
    )
    stmt = (
        sa.update(coretable)
        .values(geometry=sa.func.ST_ForcePolygonCCW(coretable.c.geometry))
        .where(coretable.c.geometry_type == "polygon")
    )
    op.execute(stmt)


def downgrade() -> None:
    """Downgrade schema."""
    schema = op.get_context().config.get_main_option("custom_schema")
    op.drop_index(op.f("ix_refs_related_id"), table_name="refs", schema=schema)
    op.drop_index(op.f("ix_refs_base_id"), table_name="refs", schema=schema)
