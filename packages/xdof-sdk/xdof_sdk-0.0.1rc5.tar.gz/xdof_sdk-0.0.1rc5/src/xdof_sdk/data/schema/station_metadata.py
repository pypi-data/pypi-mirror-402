import copy
from typing import Annotated, Union

from pydantic import AliasChoices, BaseModel, Field, model_validator

from xdof_sdk.data.schema.types import (
    ArmType,
    DataVersion,
    Transform3D,
    WorldFrame,
)


class BimanualStationExtrinsicsConfig(BaseModel):
    """Standard extrinsics for YAM/ARX/Franka arms."""

    right_arm: Annotated[
        Transform3D | None,
        Field(
            default=None,
            validation_alias=AliasChoices("right_arm", "right_arm_extrinsic"),
            description="Right arm extrinsic transform",
        ),
    ] = None
    top_camera: Transform3D | None = Field(
        default=None, description="Top camera extrinsic transform"
    )


class XMIExtrinsicsConfig(BaseModel):
    """XMI-specific extrinsics configuration."""

    top_camera_in_tracker: Transform3D = Field(
        validation_alias=AliasChoices(
            "top_camera_in_tracker", "top_camera_in_quest_head"
        ),
        description="Top camera extrinsic transform in tracker frame",
    )
    gripper_in_left_tracker: Transform3D = Field(
        validation_alias=AliasChoices(
            "gripper_in_left_tracker", "gripper_in_left_controller"
        ),
        description="Gripper extrinsic transform in left tracker frame",
    )
    gripper_in_right_tracker: Transform3D = Field(
        validation_alias=AliasChoices(
            "gripper_in_right_tracker", "gripper_in_right_controller"
        ),
        description="Gripper extrinsic transform in right tracker frame",
    )
    gripper_camera_in_gripper: Transform3D = Field(
        description="Gripper camera extrinsic transform in gripper frame"
    )


class MobileExtrinsicsConfig(BaseModel):
    """Mobile station extrinsics configuration."""

    left_arm_extrinsic: Transform3D = Field(description="Left arm extrinsic transform")
    right_arm_extrinsic: Transform3D = Field(
        description="Right arm extrinsic transform"
    )


# Union of extrinsics configs - discrimination handled by model_validator
ExtrinsicsConfig = Union[
    BimanualStationExtrinsicsConfig, XMIExtrinsicsConfig, MobileExtrinsicsConfig
]


class StationMetadata(BaseModel):
    arm_type: ArmType
    world_frame: WorldFrame

    data_version: DataVersion = DataVersion.V0
    extrinsics: ExtrinsicsConfig

    @model_validator(mode="before")
    @classmethod
    def create_extrinsics_from_arm_type(cls, data):
        """Automatically create the correct ExtrinsicsConfig based on arm_type."""
        if isinstance(data, dict):
            data = copy.deepcopy(data)
            arm_type = data.get("arm_type")
            extrinsics_data = data.get("extrinsics", {})

            # If extrinsics is already a model instance, leave it alone
            if not isinstance(extrinsics_data, dict):
                return data

            if arm_type in [ArmType.XMI, ArmType.YAM_XMI, ArmType.PASSIVE_XMI]:
                data["extrinsics"] = XMIExtrinsicsConfig.model_validate(extrinsics_data)
            elif arm_type in [ArmType.YAM, ArmType.FRANKA, ArmType.ARX]:
                data["extrinsics"] = BimanualStationExtrinsicsConfig.model_validate(
                    extrinsics_data
                )
            elif arm_type == "mobile":  # Future support
                data["extrinsics"] = MobileExtrinsicsConfig.model_validate(
                    extrinsics_data
                )
            else:
                data["extrinsics"] = BimanualStationExtrinsicsConfig.model_validate(
                    extrinsics_data
                )

        return data
