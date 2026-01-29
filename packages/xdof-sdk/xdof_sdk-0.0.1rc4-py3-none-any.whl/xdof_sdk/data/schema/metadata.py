from typing import Optional
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from xdof_sdk.data.schema.camera_info import CameraInfoList
from xdof_sdk.data.schema.station_metadata import (
    StationMetadata,
)


class Metadata(BaseModel):
    model_config = ConfigDict(extra="ignore")

    # Following fields are from the database, not written at save time.
    id: Optional[UUID] = None  # Delivered upon customer request
    operator_id: Optional[UUID] = None  # Delivered upon customer request

    task_name: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("task_name", "task_type_name")
    )

    duration: Optional[float] = None
    """ Duration of the trajectory in seconds. """

    env_loop_frequency: Optional[float] = None

    station_metadata: Optional[StationMetadata] = None
    camera_info: Optional[CameraInfoList] = None

    start_datetime: Optional[str] = None
    """ E.g. 20250725_182559 """
    end_datetime: Optional[str] = None
    """ E.g. 20250725_182559 """
