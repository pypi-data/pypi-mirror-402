from enum import Enum
from functools import total_ordering
from typing import Annotated, Any, Optional

import numpy as np
import quaternion
from numpy.typing import NDArray
from pydantic import (
    AliasChoices,
    BaseModel,
    Field,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    field_validator,
    model_serializer,
    model_validator,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema

Position3D = Annotated[
    list[float], Field(min_length=3, max_length=3, description="3D position [x, y, z]")
]
Quaternion = Annotated[
    list[float],
    Field(min_length=4, max_length=4, description="Quaternion [w, x, y, z]"),
]


class LengthUnit(str, Enum):
    """Enumeration of supported length units for spatial transformations."""

    M = "m"
    CM = "cm"
    MM = "mm"


class _NumpyMatrixType:
    """Custom type for numpy matrices that works with Pydantic and FastAPI OpenAPI."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls._serialize, info_arg=False
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {
            "type": "array",
            "items": {"type": "array", "items": {"type": "number"}},
        }

    @staticmethod
    def _validate(value: Any) -> NDArray[np.float64]:
        if isinstance(value, list):
            return np.array(value, dtype=np.float64)
        if isinstance(value, np.ndarray):
            return value.astype(np.float64)
        raise ValueError(f"Expected list or numpy array, got {type(value)}")

    @staticmethod
    def _serialize(value: NDArray[np.float64]) -> list[list[float]]:
        return value.tolist()


TransformMatrix = Annotated[NDArray[np.float64], _NumpyMatrixType]


class Transform3D(BaseModel):
    """Represents a 3D transformation with position and rotation. By default, will transform all units to meters.
    Provide either position and quaternion_wxyz or 4x4 matrix.
    e.g.
    Transform3D(position=[1.0, 2.0, 3.0], quaternion_wxyz=[1.0, 0.0, 0.0, 0.0])
    Transform3D(matrix=np.array(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ]))
    )
    """

    model_config = {"frozen": True, "arbitrary_types_allowed": True}

    position: Position3D = [0.0, 0.0, 0.0]
    quaternion_wxyz: Annotated[
        Quaternion, Field(validation_alias=AliasChoices("quaternion_wxyz", "rotation"))
    ] = [1.0, 0.0, 0.0, 0.0]
    matrix: TransformMatrix = Field(default=...)
    units: LengthUnit = LengthUnit.M
    was_matrix_input: bool = Field(default=False, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def convert_inputs(cls, values):
        """Populate both representations from either input format and handle units conversion."""
        if not isinstance(values, dict):
            return values

        # Get units, default to meters
        units = values.get("units", LengthUnit.M)

        if "matrix" in values:
            # Matrix input - extract pos/quat and keep matrix
            matrix = values["matrix"]
            if isinstance(matrix, list):
                matrix = np.array(matrix, dtype=np.float64)

            if matrix.shape != (4, 4):
                raise ValueError(f"Expected 4x4 matrix, got {matrix.shape}")

            # Convert to meters if needed
            if units != LengthUnit.M:
                scale_factor = 1.0
                if units == LengthUnit.CM:
                    scale_factor = 0.01
                elif units == LengthUnit.MM:
                    scale_factor = 0.001
                matrix = matrix.copy()
                matrix[:3, 3] *= scale_factor

            values["position"] = matrix[:3, 3].tolist()
            rotation_matrix = matrix[:3, :3]
            quat = quaternion.from_rotation_matrix(rotation_matrix)
            values["quaternion_wxyz"] = [quat.w, quat.x, quat.y, quat.z]
            values["matrix"] = matrix
            values["was_matrix_input"] = True
        else:
            # Position/quaternion input - create matrix
            pos = values.get("position", [0.0, 0.0, 0.0])
            if "quaternion_wxyz" in values:
                quat_wxyz = values.get("quaternion_wxyz", [1.0, 0.0, 0.0, 0.0])
            else:
                quat_wxyz = values.get("rotation", [1.0, 0.0, 0.0, 0.0])

            # Convert position to meters if needed
            if units != LengthUnit.M:
                scale_factor = 1.0
                if units == LengthUnit.CM:
                    scale_factor = 0.01
                elif units == LengthUnit.MM:
                    scale_factor = 0.001
                pos = [p * scale_factor for p in pos]
                values["position"] = pos

            transform_matrix = np.eye(4)
            transform_matrix[:3, 3] = pos
            quat = quaternion.from_float_array(quat_wxyz)
            transform_matrix[:3, :3] = quaternion.as_rotation_matrix(quat)
            values["matrix"] = transform_matrix

        # Always store as meters
        values["units"] = LengthUnit.M
        return values

    @field_validator("quaternion_wxyz")
    @classmethod
    def validate_quaternion_normalization(
        cls, v: Optional[list[float]]
    ) -> Optional[list[float]]:
        """Normalize quaternion to unit length."""
        if v is None:
            return v

        quat_array = np.array(v)
        quat_norm = np.linalg.norm(quat_array)

        # Check for zero quaternion (invalid)
        if quat_norm < 1e-8:
            raise ValueError("Quaternion cannot be zero vector")

        # Normalize the quaternion
        normalized_quat = quat_array / quat_norm
        return normalized_quat.tolist()

    @model_serializer
    def serialize_model(self):
        """Serialize based on original input format to preserve precision."""
        if self.was_matrix_input:
            ret_dict = {"matrix": self.matrix.tolist()}
        else:
            ret_dict: dict[str, Any] = {
                "position": self.position,
                "quaternion_wxyz": self.quaternion_wxyz,
            }

        if self.units != LengthUnit.M:
            ret_dict["units"] = self.units.value

        return ret_dict

    def __eq__(self, other):
        return np.allclose(self.matrix, other.matrix) and self.units == other.units

    def __matmul__(self, other: "Transform3D") -> "Transform3D":
        if not isinstance(other, Transform3D):
            return NotImplemented

        return Transform3D(matrix=self.matrix @ other.matrix)


@total_ordering
class DataVersion(str, Enum):
    """The version of the data format."""

    # Future versions should just start as V2 = "2", otherwise requires SemVer dependency
    # xdof employees: see xdof/data/CHANGELOG.md for details of changes.

    V3 = "3.0"  # Version 3.0 - mocap saving format. see https://xdofai.slack.com/archives/C08LTV9F5QS/p1758078178422119
    V2 = "0.2"
    ###################MCAP ABOVE THIS LINE################### see packages/sdk/src/xdof_sdk/data/trajectory.py/Trajectory class for details.

    V1_1 = "0.1.1"  # Version 0.1.1 - VIVE XMI station with passive gripper, we use DataKeys.ACTION.EE_POSE.HEAD to replace DataKeys.ACTION.EE_POSE.LEFT_HEAD.
    V1 = "0.1"  # Version 0.1 - XMI stations running after https://github.com/xdofai/lab42/pull/662
    V0 = "0.0"  # Version 0.0 - supported by all stations


class ArmType(str, Enum):
    """Enumeration of supported arm types in the robotics system.

    This enum defines the different types of robotic arms that can be used
    within the system, including physical arms and simulated variants.
    """

    YAM = "yam"  # Yet Another Manipulator
    ARX = "arx"  # ARX series robotic arm
    XMI = "xmi"  # Quest XMI robotic arm, with drive by wire gripper
    FRANKA = "franka"  # Franka Emika robotic arm
    PIPER = "piper"  # Piper robotic arm
    SIM_YAM = "sim_yam"  # Simulated YAM arm
    YAM_XMI = (
        "yam_xmi"  # quest xmi with dm4310 linear gripper, with drive by wire gripper
    )
    PASSIVE_XMI = "passive_xmi"  # vive with passive xmi gripper, that means the gripper only has action, no state.
    TEST = "test"  # Test arm for pytest purposes
    HUMAN_EGOCENTRIC = "human_egocentric"  # Human egocentric station


class WorldFrame(Enum):
    """Enumeration of coordinate frame references in the world.

    This enum defines the different reference frames that can be used
    for coordinate transformations and spatial reasoning in the robotic system.
    """

    LEFT_ARM = "left_arm"  # Coordinate frame relative to the left arm base
    NA = "NA"  # Not applicable, this usually applies to VR stations where the world frame is dynamically changing
    BASE = "base"  # This usually applies to the mobile station or single arm stations
