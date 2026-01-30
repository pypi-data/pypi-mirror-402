"""Package containing a [`repo_factory`][xplan_tools.interface.repo_factory] that provides an interface to data sources following the repository pattern.

Example:
    A XPlangGML 6.0 file can be loaded like this:
    ```
    repo = repo_factory("xplan.gml", "6.0", "xplan")
    collection = repo.get_all()
    ```
"""

import logging
from pathlib import Path
from pydoc import locate
from typing import TYPE_CHECKING, Literal

from osgeo import gdal

if TYPE_CHECKING:
    from .base import BaseRepository

logger = logging.getLogger(__name__)


def repo_factory(
    datasource: str = "",
    repo_type: Literal["gml", "jsonfg", "shape", "db"] | None = None,
) -> "BaseRepository":
    """Factory method for Repositories.

    Enables retrieving a collection of plan features from and writing to different files and DB Coretables.

    Supported are:

    - GML
    - JSON-FG
    - DB (PostgreSQL, GPKG, SQLite)
    - Shapefiles

    The corresponding wrapper is inferred from the datasource input parameter.
    Currently, only the export to gml functionality of the GMLRepository is supported for INSPIRE data.
    Also, XTrasse is only supported for GMLRepository and DBRepository.

    Args:
        datasource: Name of the input source or output file.
        repo_type: Allows to explicitly select a Repository.
        schema: Schema name for DB repository. If not specified, the default schema is used. Only for PostgreSQL.
        srid: The EPSG code for spatial data.
        with_views: Whether to create geometrytype-specific views. Only for PostgreSQL.

    Raises:
        ValueError: raises error for unknown/unspecified datasource

    Returns:
        BaseRepository: instance of repository class for manipulating a collection of plan features
    """
    if isinstance(datasource, str) and datasource.startswith("postgresql://"):
        repo_type = "db"

    if not repo_type:
        try:
            gdal.PushErrorHandler("CPLQuietErrorHandler")
            gdal.UseExceptions()
            dataset = gdal.OpenEx(
                datasource, gdal.OF_VECTOR, open_options=["WRITE_GFS=NO"]
            )
            if dataset is None:
                raise RuntimeError("GDAL open failed")

            driver = dataset.GetDriver()
            driver_name = getattr(driver, "GetName", lambda: "")().lower()
            if dataset is not None:
                dataset = None
            match driver_name:
                case "postgresql" | "sqlite" | "gpkg":
                    repo_type = "db"
                case "esri shapefile":
                    repo_type = "shape"
                case "gml" | "jsonfg":
                    repo_type = driver_name
                case _:
                    raise NotImplementedError("datasource not implemented")

        except (NotImplementedError, RuntimeError) as e:
            file = Path(datasource)
            match file.suffix:
                case ".gml":
                    repo_type = "gml"
                case ".json":
                    repo_type = "jsonfg"
                case ".gpkg" | ".sqlite":
                    repo_type = "db"
                case _:
                    logger.warning(
                        f"repository type for {datasource} could not be determined: {e}"
                    )
        finally:
            gdal.PopErrorHandler()

    match repo_type:
        case "gml":
            logger.debug("initializing GML repository")
            return locate("xplan_tools.interface.gml.GMLRepository")(datasource)
        case "jsonfg":
            logger.debug("initializing JSON-FG repository")
            return locate("xplan_tools.interface.jsonfg.JsonFGRepository")(datasource)
        case "shape":
            return locate("xplan_tools.interface.shape.ShapeRepository")(datasource)
        case "db":
            logger.debug("initializing DB repository")
            return locate("xplan_tools.interface.db.DBRepository")(
                datasource,
            )
        case _:
            raise ValueError("Unknown datasource")


__all__ = ["repo_factory"]
