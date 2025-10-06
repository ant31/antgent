# pylint: disable=import-outside-toplevel
import logging
import time
from typing import Any

from pydantic import BaseModel, ConfigDict
from temporalio import activity

from antgent.utils.logging import truncate_for_log

logger = logging.getLogger(__name__)


class AnyData(BaseModel):
    model_config = ConfigDict(extra="allow")


@activity.defn
def echo(data: AnyData) -> AnyData:
    activity.heartbeat()
    time.sleep(0.5)
    activity.logger.info("Echoing: %s", truncate_for_log(data.model_dump_json()))
    return data


@activity.defn
async def aecho(data: dict[str, Any]) -> dict[str, Any]:
    activity.logger.info("Echoing: %s", truncate_for_log(data))
    return data
