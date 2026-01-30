import asyncio
import logging
from enum import Enum
from importlib import metadata
from pathlib import Path
from typing import Annotated, Optional

import typer
from pydantic import ValidationError
from rich import print
from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import Traceback

from xplan_tools.interface import repo_factory
from xplan_tools.settings.settings import get_settings
from xplan_tools.transform import transformer_factory
from xplan_tools.util import MigrationPath, _Versions, serialize_style_rules
from xplan_tools.util.validate import xplan_validate

__version__ = metadata.version("xplan_tools")

console = Console()
error_console = Console(stderr=True, style="bold red")
logger = logging.getLogger(__name__)
# don't propagate alembic logs when using CLI
logging.getLogger("alembic").propagate = False

settings = get_settings()

app = typer.Typer(help=f"XPlan-Tools {__version__}")
db_app = typer.Typer()
app.add_typer(
    db_app,
    name="manage-db",
    help="""Manage a database.

        Supported DBs are PostgreSQL/PostGIS (postgresql://<url>), SQLite/Spatialite (sqlite:///<file>) and GeoPackage (gpkg:///<file>).
        """,
)


class _ValidatorReportFormat(str, Enum):
    JSON = "json"
    PDF = "pdf"


class _StyleSerializationFormats(str, Enum):
    JSON = "json"
    YAML = "yaml"


def version_callback(value: bool):
    if value:
        console.log(f"XPlan-Tools Version: {__version__}")
        raise typer.Exit()


@app.callback()
def init(
    version: Annotated[
        Optional[bool],
        typer.Option("--version", callback=version_callback, is_eager=True),
    ] = None,
    log: Annotated[
        bool,
        typer.Option(help="Disable logging"),
    ] = True,
    log_output: Annotated[
        str,
        typer.Option(help="Log to given file or 'stdout'"),
    ] = "stdout",
    log_level: Annotated[
        str,
        typer.Option(help="Set log level"),
    ] = "INFO",
):
    if log:
        encoding = "utf-8"
        level = getattr(logging, log_level.upper(), logging.INFO)
        if log_output == "stdout":
            logging.basicConfig(
                encoding=encoding,
                level=level,
                format="[cyan]%(name)s[/cyan] %(message)s",
                datefmt="[%X]",
                handlers=[
                    RichHandler(console=console, markup=True, rich_tracebacks=True)
                ],
            )
        else:
            logging.basicConfig(
                encoding=encoding,
                level=level,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                filename=log_output,
                filemode="w",
            )
    else:
        logging.disable()


@app.command()
def convert(
    input: Annotated[
        str,
        typer.Argument(help="Input file path or DB connection string."),
    ],
    output: Annotated[
        str,
        typer.Argument(help="Output file path or DB connection string."),
    ] = "stdout",
    to_version: Annotated[
        Optional[_Versions],
        typer.Option(help="Convert input to specified XPlanung or INSPIRE version"),
    ] = None,
    id: Annotated[
        Optional[str], typer.Option(help="UUID of a plan if input is DB")
    ] = None,
    single_collection: Annotated[
        bool,
        typer.Option(
            help="Write heterogenous JSON-FG FeatureCollection or fan out by FeatureType"
        ),
    ] = True,
    single_plans: Annotated[
        bool,
        typer.Option(help="Write one output file per plan element"),
    ] = False,
    xplan_validator: Annotated[
        bool,
        typer.Option(help="Validate the result with the official XPlanValidator API"),
    ] = False,
    validator_report_name: Annotated[
        str,
        typer.Option(
            help="Under which name to save the validation report; may be a path"
        ),
    ] = "report.json",
    validator_report_format: Annotated[
        _ValidatorReportFormat,
        typer.Option(help="The report return format for the XPlanValidator API"),
    ] = "json",
    write_geometry: Annotated[
        bool, typer.Option(help="Write geometry member for JSON-FG Feature")
    ] = True,
    write_bbox: Annotated[
        bool, typer.Option(help="Write BBOX for JSON-FG Feature")
    ] = True,
    raster_as_refscan: Annotated[
        bool,
        typer.Option(
            help="Map raster data references to XP_Bereich::refScan if true, otherwise it is mapped to XP_Plan::externeReferenz (Shapefile input only)"
        ),
    ] = True,
    name_field: Annotated[
        str,  # should be Literal once https://github.com/fastapi/typer/pull/429 is merged
        typer.Option(
            help="Which field to use for the plan name (Shapefile input only)"
        ),
    ] = "PLANID",
    add_style_properties: Annotated[
        bool,
        typer.Option(
            help="Add style properties like stylesheetId to presentation objects"
        ),
    ] = False,
    ppo_to_pto: Annotated[
        bool, typer.Option(help="Convert XP_PPO to XP_PTO objects")
    ] = False,
    populate_schriftinhalt: Annotated[
        bool,
        typer.Option(
            help="Populate 'schriftinhalt' even if a given rule does not provide a text template"
        ),
    ] = False,
    ref_check: Annotated[
        bool,
        typer.Option(help="Validate referenced files"),
    ] = True,
    generate_ids: Annotated[
        bool,
        typer.Option(help="Generate new IDs for GML Features"),
    ] = False,
    feature_srs: Annotated[
        bool, typer.Option(help="Set SRID for each relevant feature")
    ] = True,
    inspire_id_ns: Annotated[
        str,
        typer.Option(help="The INSPIRE Identifier namespace"),
    ] = "https://registry.gdi-de.org/id/de.hh/0a2b2809-dd93-45e6-bc0e-26093eb1122a",
):
    """Convert XPlanung data between formats, versions and transform to INSPIRE PLU.

    Converts input data to ouput target, either of which can be a GML file or a DB Coretable. Optionally migrates XPlanung version
    and transforms to INSPIRE PLU 4.0. INSPIRE transformation currently supports only GML as output target.

    Supported DBs are PostgreSQL/PostGIS (postgresql://<url>), SQLite/Spatialite (sqlite:///<file>) and GeoPackage (gpkg:///<file>).
    """

    def dump_features(input: str, output: str):
        if (".gml" not in output and output != "stdout") and to_version == "plu":
            error_console.log(
                "INSPIRE transformation currently supports only GML as output target"
            )
            return

        repo = repo_factory(input)

        collection = (
            repo.get_all(
                raster_as_refscan=raster_as_refscan,
                name_field=name_field,
                ref_check=ref_check,
                always_generate_ids=generate_ids,
            )
            if not id
            else repo.get_plan_by_id(id)
        )

        version = collection.version

        if to_version:
            try:
                path = MigrationPath(version, to_version).path
            except ValueError as e:
                error_console.log(str(e))
                return
            for step in path:
                console.log(f"Migrating from version {version} to {step}")
                collection = transformer_factory(
                    collection, step, inspire_id_ns
                ).transform()
                version = step
            if to_version == "6.1":
                collection = transformer_factory(collection, "6.1").set_associations()

        if add_style_properties:
            if version != "6.0":
                error_console.log("Styles for versions != 6.0 not yet implemented")
            else:
                collection.add_style_properties(
                    to_text=ppo_to_pto,
                    always_populate_schriftinhalt=populate_schriftinhalt,
                )

        if xplan_validator:
            success = asyncio.run(
                xplan_validate(
                    collection,
                    input=output,
                    output=validator_report_name,
                    format=validator_report_format.value,
                    single_plans=single_plans,
                )
            )
            if not success:
                error_console.log(
                    "Error during validation with XPlanValidator API, please see log for details"
                )

        if output == "stdout":
            for feature in collection.get_features():
                print(feature)

        else:
            if single_plans and output[:4] not in ["post", "gpkg", "sqli"]:
                path = Path(output)
                for plan_name, plan in collection.get_single_plans(with_name=True):
                    repo_factory(
                        str(path.parent / f"{plan_name}{path.suffix}"),
                    ).save_all(
                        plan,
                        write_geometry=write_geometry,
                        write_bbox=write_bbox,
                        feature_srs=feature_srs,
                    )
            else:
                repo_factory(output).save_all(
                    collection,
                    write_geometry=write_geometry,
                    write_bbox=write_bbox,
                    single_collection=single_collection,
                    feature_srs=feature_srs,
                )

    try:
        console.log(f"Converting [green]{input}[/green] to [blue]{output}[/blue].")
        with console.status("Working..."):
            dump_features(input, output)
        console.log("Done.")
    except ValidationError as e:
        logger.exception(e)
        raise e
    except (OSError, FileNotFoundError) as e:
        error_console.log("File not found, please see log for details")
        logger.exception(e)
        raise RuntimeError("File operation failed") from None
    except Exception as e:
        if logger.getEffectiveLevel() == logging.DEBUG:
            tb = Traceback.from_exception(type(e), e, e.__traceback__, show_locals=True)
            error_console.print(tb)
        else:
            error_console.log("An error occurred, please see log for details")
        logger.exception(e)
        raise RuntimeError("An unexpected error occurred") from None


@app.command()
def serialize_styles(
    output: Annotated[
        str,
        typer.Argument(help="Output file path or stdout"),
    ] = "stdout",
    format: Annotated[
        _StyleSerializationFormats,
        typer.Option(help="Supported formats are JSON and YAML"),
    ] = "json",
):
    """Serialize the style rules for XPlanung presentational objects in the selected format to the provided output."""
    serialized_string = serialize_style_rules(format)
    if output == "stdout":
        print(serialized_string)
    else:
        with open(output, "w") as f:
            f.write(serialized_string)


@db_app.command()
def create_schema(
    connection_string: Annotated[
        str,
        typer.Argument(help="DB connection string."),
    ],
    srid: Annotated[
        int, typer.Option(help="Spatial reference identifier of the geometry column.")
    ] = 25832,
    views: Annotated[
        bool, typer.Option(help="Whether to create views for geometry types.")
    ] = True,
    schema: Annotated[
        str | None, typer.Option(help="Whether to specify a schema.")
    ] = None,
):
    """Create Coretable schema in the given DB."""
    settings.db_schema = schema
    settings.db_srid = srid
    settings.db_views = views
    repo_factory(connection_string)
    console.log("Schema created.")


@db_app.command()
def drop_schema(
    connection_string: Annotated[
        str, typer.Argument(help="postgres connection string")
    ],
    schema: Annotated[
        str | None, typer.Option(help="Whether to specify a schema.")
    ] = None,
):
    """Drop Coretable schema in the given DB."""
    settings.db_schema = schema
    repo_factory(connection_string).delete_tables()
    console.log("Schema dropped.")


@db_app.command()
def delete_plan(
    connection_string: Annotated[
        str,
        typer.Argument(help="DB connection string."),
    ],
    id: Annotated[str, typer.Option(help="UUID of a plan")],
):
    """Delete a plan by id."""
    repo_factory(connection_string).delete_plan_by_id(id)
    console.log(f"Plan with id {id} deleted.")


if __name__ == "__main__":
    app()
