"""This module contains a method to validate Feature Collections with the official XPlanValidator."""

import io
import logging
from pathlib import Path
from typing import Literal

import httpx
from pydantic_core import from_json, to_json

from xplan_tools.interface.gml import GMLRepository
from xplan_tools.model.base import BaseCollection

logger = logging.getLogger(__name__)
logging.getLogger("httpx").propagate = False


async def xplan_validate(
    collection: BaseCollection,
    input: str = "xplan.gml",
    output: str = "report.json",
    format: Literal["json", "pdf"] = "json",
    single_plans: bool = False,
    validator_url: str = "https://www.xplanungsplattform.de/xplan-api-validator/xvalidator/api/v1/",
):
    """Validate a Feature Collection with the official XPlanValidator.

    Args:
        collection: A BaseCollection instance.
        input: An optional input file name to use in the validation report.
        output: The validation report name. Can be a file path; if it doesn't exist yet, it will be created.
        format: The format of the validation report.
        single_plans: Whether to validate plans in the collection individually.
        validator_url: The base URL of the XPlanValidator instance. Must have a trailing slash.
    """
    input_path = Path(input)
    output_path = Path(output)
    plans = (
        collection.get_single_plans(with_name=True)
        if single_plans
        else [(input_path.stem, collection)]
    )
    success = True
    async with httpx.AsyncClient(timeout=10) as client:
        for plan_name, plan in plans:
            headers = {
                "accept": f"application/{format}",
                "x-filename": f"{plan_name}{input_path.suffix}",
                "content-type": "application/gml+xml",
            }
            params = {"name": f"{output_path.stem}.{format}"}
            with io.BytesIO() as buffer:
                GMLRepository(buffer).save_all(plan)
                logger.debug(
                    f"Sending validation request for plan '{plan_name}' to XPlanValidator API @ {validator_url}"
                )
                try:
                    response = await client.post(
                        validator_url + "validate",
                        headers=headers,
                        params=params,
                        content=buffer.getvalue(),
                    )
                    response.raise_for_status()
                except httpx.HTTPError:
                    logger.exception(
                        f"Error while requesting validation for plan '{plan_name}', skipping"
                    )
                    success = False
                    continue
            data = (
                to_json(from_json(response.content), indent=4)
                if format == "json"
                else response.content
            )
            if len(output_path.parents) > 1:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            report_path = str(
                output_path.parent / f"{output_path.stem}_{plan_name}.{format}"
            )
            with open(
                report_path,
                "wb",
            ) as f:
                f.write(data)
            logger.info(f"Validation report saved as {report_path}")
    return success
