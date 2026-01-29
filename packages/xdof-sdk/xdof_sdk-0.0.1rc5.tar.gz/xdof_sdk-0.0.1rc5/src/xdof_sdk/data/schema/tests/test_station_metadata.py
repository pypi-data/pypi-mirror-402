import numpy as np

from xdof_sdk.data.schema.station_metadata import StationMetadata
from xdof_sdk.data.schema.types import ArmType, WorldFrame

LEGACY_STATION_METADATA = """
  {
    "world_frame": "left_arm",
    "extrinsics": {
      "right_arm": {
        "position": [-0.00186023478, -0.797904739, 0.0026400628],
        "rotation": [0.999917494, -0.0125952832, 0.00252057239, -0.000101003439]
      },
      "top_camera": {
        "position": [-0.0650164545, -0.326595742, 0.994067611],
        "rotation": [0.21509806, -0.67355936, 0.67092827, -0.22339623]
      }
    },
    "arm_type": "franka"
  }
"""


def test_legacy_station_metadata():
    station_metadata = StationMetadata.model_validate_json(LEGACY_STATION_METADATA)

    assert station_metadata.arm_type == ArmType.FRANKA
    assert station_metadata.world_frame == WorldFrame.LEFT_ARM
    assert station_metadata.extrinsics.right_arm
    assert station_metadata.extrinsics.right_arm.position == [
        -0.00186023478,
        -0.797904739,
        0.0026400628,
    ]


LEGACY_XMI_STATION_METADATA = """
  {
    "world_frame": "NA",
    "extrinsics": {
      "top_camera_in_quest_head": {
        "position": [
          -0.06422473,
          -0.05830567,
          0.083002
        ],
        "rotation": [
          0.92969391,
          -0.36830551,
          0.0016577,
          -0.00418725
        ]
      },
      "gripper_in_left_controller": {
        "position": [
          -4.181e-05,
          0.07813787,
          0.01732262
        ],
        "rotation": [
          0.69958233,
          -0.71081816,
          0.04289986,
          0.05900601
        ]
      },
      "gripper_in_right_controller": {
        "position": [
          -0.00825025,
          0.07254365,
          0.03051299
        ],
        "rotation": [
          -0.71866291,
          0.69326912,
          0.04311067,
          0.03229579
        ]
      },
      "gripper_camera_in_gripper": {
        "position": [
          0,
          -0.086465,
          -0.01125
        ],
        "rotation": [
          -0.99939083,
          0.0348995,
          -0.0,
          -0.0
        ]
      }
    },
    "arm_type": "xmi"
  }
"""


def test_legacy_xmi_station_metadata():
    station_metadata = StationMetadata.model_validate_json(LEGACY_XMI_STATION_METADATA)

    assert station_metadata.arm_type == ArmType.XMI
    assert station_metadata.world_frame == WorldFrame.NA
    assert station_metadata.extrinsics.top_camera_in_tracker

    assert np.allclose(
        station_metadata.extrinsics.top_camera_in_tracker.quaternion_wxyz,
        [
            0.92969391,
            -0.36830551,
            0.0016577,
            -0.00418725,
        ],
    )
    assert station_metadata.extrinsics.gripper_in_left_tracker
    assert station_metadata.extrinsics.gripper_in_right_tracker
    assert station_metadata.extrinsics.gripper_camera_in_gripper
