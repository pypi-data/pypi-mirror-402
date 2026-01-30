"""Module containing the class for extracting plans from and writing to databases."""

# import json
import logging
from pathlib import Path
from typing import Iterable, Literal

from alembic import command, config, script
from geoalchemy2 import load_spatialite_gpkg
from geoalchemy2.admin.dialects.sqlite import load_spatialite_driver
from sqlalchemy import (
    Column,
    Engine,
    MetaData,
    Table,
    create_engine,
    delete,
    insert,
    inspect,
    select,
    text,
)
from sqlalchemy.engine import URL, make_url

# from sqlalchemy.dialects.sqlite.base import SQLiteCompiler
from sqlalchemy.event import listen, listens_for, remove

# from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

# from sqlalchemy.sql.expression import BindParameter
from xplan_tools.model import model_factory
from xplan_tools.model.base import BaseCollection, BaseFeature
from xplan_tools.model.orm import Base, Feature, Geometry, Refs
from xplan_tools.settings import get_settings

# from xplan_tools.util import linearize_geom
from .base import BaseRepository

logger = logging.getLogger(__name__)


class DBRepository(BaseRepository):
    """Repository class for loading from and writing to databases."""

    def __init__(
        self,
        datasource: str = "",
    ) -> None:
        """Initializes the DB Repository.

        During initialization, a connection is established and the existence of required tables is tested.
        If an alembic revision is found, automatic migration is executed for PostgreSQL DBs.
        For other DBs, an Exception is raised if the revision does not correspond to the current model.
        If no revision and tables are found, they are automatically created.

        Args:
            datasource: A connection string which will be transformed to a URL instance.
        """
        settings = get_settings()
        self.datasource: URL = make_url(datasource)
        self.content = None
        self.schema = settings.db_schema
        self.srid = settings.db_srid
        self.dialect = self.datasource.get_dialect().name
        self.Session = sessionmaker(bind=self._engine)

        self.alembic_cfg = config.Config()
        self.alembic_cfg.set_main_option(
            "script_location", "xplan_tools:model:migrations"
        )
        self.alembic_cfg.set_main_option(
            "sqlalchemy.url",
            datasource.replace("gpkg:", "sqlite:").replace(
                "postgresql:", "postgresql+psycopg:"
            ),
        )
        self._ensure_repo()

    def _ensure_repo(self) -> None:
        """Runs initial connection/schema tests and ensures DB revision."""

        def _check_schema_accessibility(privilege: Literal["USAGE", "CREATE"]) -> None:
            """Raises an exception if the schema does not exist or is not accessible to the current user."""
            # Check if the schema exists and is accessible
            user = conn.execute(text("SELECT current_user")).scalar()
            result = conn.execute(
                text("""
                    SELECT has_schema_privilege(:user, :schema, :privilege)
                """),
                {
                    "user": user,
                    "schema": self.schema,
                    "privilege": privilege,
                },
            )
            if not result.scalar():
                raise RuntimeError(
                    f"User {user} lacks {privilege} on schema '{self.schema}'"
                )

        def _check_db_srid() -> None:
            """Raises an exception if the DB SRID differs from the one of the repo."""
            if self.dialect == "geopackage":
                geometry_columns = Table(
                    "gpkg_geometry_columns",
                    MetaData(),
                    Column("table_name"),
                    Column("srs_id"),
                )
                stmt = select(geometry_columns.c.srs_id).where(
                    geometry_columns.c.table_name == "coretable"
                )
            else:
                geometry_columns = Table(
                    "geometry_columns",
                    MetaData(),
                    Column("f_table_name"),
                    Column("srid"),
                )
                stmt = select(geometry_columns.c.srid).where(
                    geometry_columns.c.f_table_name == "coretable"
                )
                if self.dialect == "postgresql":
                    geometry_columns.append_column(Column("f_table_schema"))
                    stmt = stmt.where(
                        geometry_columns.c.f_table_schema == (self.schema or "public")
                    )
            srid = conn.execute(stmt).scalar_one()
            if srid != self.srid:
                raise RuntimeError(
                    f"DB SRID '{srid}' and configured SRID '{self.srid}' must identical"
                )

        current_version = script.ScriptDirectory.from_config(
            self.alembic_cfg
        ).get_heads()
        # test for tables and revision
        with self._engine.connect() as conn:
            if self.schema and self.dialect == "postgresql":
                _check_schema_accessibility("USAGE")
            inspector = inspect(conn)
            tables = inspector.get_table_names(schema=self.schema)
            is_coretable = {"coretable", "refs"}.issubset(set(tables))
            if "alembic_version" in tables:
                alembic_table = Table(
                    "alembic_version",
                    MetaData(schema=self.schema),
                    Column("version_num"),
                )
                stmt = select(alembic_table.c.version_num)
                db_version = conn.execute(stmt).scalars().all()
            else:
                db_version = []
            if db_version:
                _check_db_srid()
            is_current_version = set(db_version) == set(current_version)
            if is_current_version:
                logger.info("Database is at current revision")
                return
            elif self.schema and self.dialect == "postgresql":
                _check_schema_accessibility("CREATE")
        # handle schema upgrade or table creation
        if is_coretable and not db_version:
            e = RuntimeError("Coretable with no revision found in database")
            e.add_note(
                "it is likely that the database was set up with an older version of this library which didn't use revisions yet"
            )
            e.add_note(
                "please set up a new database or add a revision corresponding to the current model manually"
            )
            raise e
        # if postgresql, run alembic and return
        elif self.dialect == "postgresql":
            logger.info(
                "Running database migrations"
                if db_version
                else "Creating new database schema"
            )
            command.upgrade(self.alembic_cfg, "head")
            return
        elif db_version:
            e = NotImplementedError(
                f"Incompatible database revision and automatic migration not implemented for {self.dialect}"
            )
            e.add_note(
                "please set up a new database with the current version of this library"
            )
            raise e
        else:
            # create tables if it's a fresh file-based DB and set it to current revision
            logger.info("Creating new database schema")
            self.create_tables()
            command.stamp(self.alembic_cfg, "head")

    @property
    def _engine(self) -> Engine:
        url = (
            self.datasource.set(drivername="postgresql+psycopg")
            if self.dialect == "postgresql"
            else self.datasource
        )
        connect_args: dict[str, str] = {}
        if self.dialect == "postgresql":
            connect_args["connect_timeout"] = 5
            if self.schema:
                connect_args["options"] = f"-csearch_path={self.schema},public"
        engine = create_engine(url, connect_args=connect_args)
        if self.dialect == "geopackage":
            listen(engine, "connect", load_spatialite_gpkg)
        elif self.dialect == "sqlite":
            listen(
                engine,
                "connect",
                load_spatialite_driver,
            )
        return engine

    def get_plan_by_id(self, id: str) -> BaseCollection:
        logger.debug(f"retrieving plan with id {id}")
        with self.Session() as session:
            plan_feature = session.get(Feature, id)
            if not plan_feature:
                raise ValueError(f"no feature found with id {id}")
            elif "Plan" not in plan_feature.featuretype:
                raise ValueError(f"{plan_feature.featuretype} is not a plan object")
            else:
                plan_model = model_factory(
                    plan_feature.featuretype,
                    plan_feature.version,
                    plan_feature.appschema,
                ).model_validate(plan_feature)
                collection = {id: plan_model}
                srid = plan_model.get_geom_srid()
                # iterate related features with depth=2: plan -> section -> features
                for feature in plan_feature.related_features(session, depth=2):
                    collection[str(feature.id)] = model_factory(
                        feature.featuretype, feature.version, feature.appschema
                    ).model_validate(feature)
                return BaseCollection(
                    features=collection,
                    srid=srid,
                    version=plan_feature.version,
                    appschema=plan_feature.appschema,
                )

    def get(self, id: str) -> BaseFeature:
        logger.debug(f"retrieving feature with id {id}")
        with self.Session() as session:
            feature = session.get(Feature, id)
            if not feature:
                raise ValueError(f"no feature found with id {id}")
            else:
                return model_factory(
                    feature.featuretype, feature.version, feature.appschema
                ).model_validate(feature)

    def save(self, feature: BaseFeature) -> None:
        logger.debug(f"saving feature with id {id}")
        with self.Session() as session:
            feature = feature.model_dump_coretable()
            if session.get(Feature, feature.id):
                raise ValueError(f"feature with id {feature.id} already exists")
            session.merge(feature)
            session.commit()

    def delete_plan_by_id(self, id: str) -> BaseFeature:
        logger.debug(f"deleting plan with id {id}")
        with self.Session() as session:
            plan_feature = session.get(Feature, id)
            if not plan_feature:
                raise ValueError(f"no feature found with id {id}")
            elif "Plan" not in plan_feature.featuretype:
                raise ValueError(f"{plan_feature.featuretype} is not a plan object")
            else:
                plan_model = model_factory(
                    plan_feature.featuretype,
                    plan_feature.version,
                    plan_feature.appschema,
                ).model_validate(plan_feature)
                ids = [plan_feature.id]
                ids += [
                    feature.id for feature in plan_feature.related_features(session)
                ]
                stmt = delete(Feature).where(Feature.id.in_(ids))
                session.execute(stmt)
                session.commit()
                return plan_model

    def delete(self, id: str) -> BaseFeature:
        logger.debug(f"deleting feature with id {id}")
        with self.Session() as session:
            feature = session.get(Feature, id)
            if not feature:
                raise ValueError(f"no feature found with id {id}")
            else:
                session.delete(feature)
                session.commit()
                return model_factory(
                    feature.featuretype, feature.version, feature.appschema
                ).model_validate(feature)

    def save_all(
        self, features: BaseCollection | Iterable[BaseFeature], **kwargs
    ) -> None:
        logger.debug("saving collection")
        with self.Session() as session:
            feature_list = []
            refs_list = []
            for feature in (
                features.get_features()
                if isinstance(features, BaseCollection)
                else features
            ):
                feature, refs = feature.model_dump_coretable_bulk()
                feature_list.append(feature)
                refs_list.extend([ref for ref in refs if ref not in refs_list])
            if feature_list:
                session.execute(insert(Feature), feature_list)
            if refs_list:
                session.execute(insert(Refs), refs_list)
            session.commit()

    def update_all(
        self, features: BaseCollection | Iterable[BaseFeature], **kwargs
    ) -> None:
        logger.debug("updating collection")
        with self.Session() as session:
            for feature in (
                features.get_features()
                if isinstance(features, BaseCollection)
                else features
            ):
                feature = feature.model_dump_coretable()
                session.merge(feature)
            session.commit()

    def update(self, id: str, feature: BaseFeature) -> BaseFeature:
        logger.debug(f"updating feature with id {id}")
        with self.Session() as session:
            db_feature = session.get(Feature, id)
            if db_feature:
                session.merge(feature.model_dump_coretable())
                session.commit()
                return feature
            else:
                raise ValueError(f"no feature found with id {id}")

    def patch(self, id: str, partial_update: dict) -> BaseFeature:
        logger.debug(f"patching feature with id {id}: {partial_update}")
        with self.Session() as session:
            db_feature = session.get(Feature, id)
            if db_feature:
                feature_dict = (
                    model_factory(
                        db_feature.featuretype, db_feature.version, db_feature.appschema
                    )
                    .model_validate(db_feature)
                    .model_dump()
                )
                feature = model_factory(
                    db_feature.featuretype, db_feature.version, db_feature.appschema
                ).model_validate(feature_dict | partial_update)
                session.merge(feature.model_dump_coretable())
                session.commit()
                return feature
            else:
                raise ValueError(f"no feature found with id {id}")

    def create_tables(self) -> None:
        """Creates coretable and related/spatial tables in the database.

        Args:
            srid: the EPSG code for spatial data
        """

        @listens_for(Base.metadata, "before_create")
        def pre_creation(_, conn, **kwargs):
            if self.dialect == "sqlite":
                conn.execute(text("SELECT InitSpatialMetaData('EMPTY')"))
                conn.execute(text("SELECT InsertEpsgSrid(:srid)"), {"srid": self.srid})

        @listens_for(Base.metadata, "after_create")
        def post_creation(_, conn, **kwargs):
            if self.dialect == "geopackage":
                conn.execute(
                    text(
                        """
                        INSERT INTO gpkg_extensions (table_name, extension_name, definition, scope)
                        VALUES
                            ('gpkg_data_columns', 'gpkg_schema', 'http://www.geopackage.org/spec/#extension_schema', 'read-write'),
                            ('gpkg_data_column_constraints', 'gpkg_schema', 'http://www.geopackage.org/spec/#extension_schema', 'read-write'),
                            ('gpkgext_relations', 'related_tables', 'http://www.opengis.net/doc/IS/gpkg-rte/1.0', 'read-write'),
                            ('refs', 'related_tables', 'http://www.opengis.net/doc/IS/gpkg-rte/1.0', 'read-write')
                        """
                    )
                )
                conn.execute(
                    text(
                        """
                        INSERT INTO gpkgext_relations (base_table_name, base_primary_column, related_table_name, related_primary_column, relation_name, mapping_table_name)
                        VALUES
                            ('coretable', 'id', 'coretable', 'id', 'features', 'refs')
                        """
                    )
                )
                conn.execute(
                    text(
                        """
                        INSERT INTO gpkg_data_columns (table_name, column_name, mime_type)
                        VALUES
                            ('coretable', 'properties', 'application/json')
                        """
                    )
                )

        logger.debug(f"creating tables with srid {self.srid}")
        tables = Base.metadata.sorted_tables
        if not self.dialect == "geopackage":
            tables.pop(1)
        tables[0].append_column(
            Column(
                "geometry",
                Geometry(
                    srid=self.srid,
                    spatial_index=True,
                ),
                nullable=True,
            ),
            replace_existing=True,
        )

        try:
            Base.metadata.create_all(self._engine, tables)
            remove(Base.metadata, "before_create", pre_creation)
            remove(Base.metadata, "after_create", post_creation)

        except Exception as e:
            if self.dialect in ["sqlite", "geopackage"]:
                file = self._engine.url.database
                Path(file).unlink(missing_ok=True)
            raise e

    def delete_tables(self) -> None:
        """Deletes coretable and related/spatial tables from the database."""
        logger.debug("deleting tables")
        if self.dialect == "postgresql":
            command.downgrade(self.alembic_cfg, "base")
        else:
            Base.metadata.drop_all(self._engine)
