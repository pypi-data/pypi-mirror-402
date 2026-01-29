import numpy as np
import pytest
from pydantic import ValidationError

from xdof_sdk.data.schema.camera_info import (
    CameraExtrinsics,
    CameraInfoList,
    SingleCameraIntrinsicData,
)
from xdof_sdk.data.schema.types import Transform3D

LEGACY_CAMERA_INFO = """
{
    "top_camera": {
      "camera_type": "ZED_X",
      "device_id": "40880670",
      "width": 960,
      "height": 600,
      "polling_fps": 60,
      "name": "zed_camera",
      "image_transfer_time_offset_ms": 70,
      "exposure_us": null,
      "auto_exposure": null,
      "intrinsic_data": {
        "cameras": {
          "left_rgb": {
            "intrinsics_matrix": [
              [368.19866943359375, 0.0, 498.9993896484375],
              [0.0, 368.19866943359375, 286.62054443359375],
              [0.0, 0.0, 1.0]
            ],
            "distortion": {
              "distortion_coefficients": [
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
              ],
              "distortion_model": "zed_rectified"
            }
          },
          "right_rgb": {
            "intrinsics_matrix": [
              [368.19866943359375, 0.0, 498.9993896484375],
              [0.0, 368.19866943359375, 286.62054443359375],
              [0.0, 0.0, 1.0]
            ],
            "distortion": {
              "distortion_coefficients": [
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
              ],
              "distortion_model": "zed_rectified"
            }
          }
        }
      },
      "extrinsics": {
        "world": "left_rgb",
        "extrinsics": {
          "right_rgb": [
            [1.0, 0.0, 0.0, 120.1217],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
          ]
        }
      },
      "concat_image": true
    },
    "left_camera": {
      "camera_type": "Intel RealSense D405",
      "device_id": "218622271397",
      "width": 640,
      "height": 480,
      "polling_fps": 60,
      "name": "left_camera",
      "image_transfer_time_offset_ms": 80.0,
      "exposure_us": null,
      "auto_exposure": true,
      "intrinsic_data": {
        "cameras": {
          "rgb": {
            "intrinsics_matrix": [
              [433.8301086425781, 0.0, 322.1812744140625],
              [0.0, 433.3424987792969, 242.0836181640625],
              [0.0, 0.0, 1.0]
            ],
            "distortion": {
              "distortion_coefficients": [
                -0.05174887180328369, 0.0627809464931488, 0.0004916912293992937,
                0.0009648163104429841, -0.02126472257077694
              ],
              "distortion_model": "inverse_brown_conrady"
            }
          }
        }
      },
      "extrinsics": null,
      "concat_image": false
    },
    "right_camera": {
      "camera_type": "Intel RealSense D405",
      "device_id": "218622275957",
      "width": 640,
      "height": 480,
      "polling_fps": 60,
      "name": "right_camera",
      "image_transfer_time_offset_ms": 80.0,
      "exposure_us": null,
      "auto_exposure": true,
      "intrinsic_data": {
        "cameras": {
          "rgb": {
            "intrinsics_matrix": [
              [434.3958740234375, 0.0, 324.7766418457031],
              [0.0, 433.8780517578125, 243.3731231689453],
              [0.0, 0.0, 1.0]
            ],
            "distortion": {
              "distortion_coefficients": [
                -0.05293123796582222, 0.05821342393755913, 7.488654227927327e-5,
                0.0002381689555477351, -0.019112564623355865
              ],
              "distortion_model": "inverse_brown_conrady"
            }
          }
        }
      },
      "extrinsics": null,
      "concat_image": false
    }
}
"""


def test_load_valid_legacy_camera_info():
    camera_info = CameraInfoList.model_validate_json(LEGACY_CAMERA_INFO)
    assert camera_info.top_camera.extrinsics
    assert camera_info.top_camera.extrinsics.world == "left_rgb"
    assert camera_info.top_camera.extrinsics.right_rgb.matrix.shape == (4, 4)
    assert camera_info.top_camera.extrinsics.right_rgb == Transform3D(
        position=[0.1201217, 0.0, 0.0],
    )

    assert camera_info.left_camera.extrinsics is None

    print(camera_info.model_dump_json(indent=2, exclude_unset=True))


def test_fails_invalid():
    with pytest.raises(ValidationError):
        SingleCameraIntrinsicData(
            # incorrectly formatted intrinsics
            intrinsics_matrix=np.array(
                [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [0.0, 0.0, 0.0]]
            ),
            distortion_coefficients=[0.0, 0.0, 0.0, 0.0, 0.0],
            distortion_model="inverse_brown_conrady",
        )

    with pytest.raises(ValidationError):
        CameraExtrinsics(
            world="left_rgb",
            right_rgb=Transform3D(
                matrix=np.array(
                    [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [0.0, 0.0, 0.0]]
                )
            ),
        )


def test_reasonable_settings():
    intrinsics = SingleCameraIntrinsicData(
        # incorrectly formatted intrinsics
        intrinsics_matrix=np.array(
            [[1.0, 40.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        ),
        distortion_coefficients=[0.0, 0.0, 0.0, 0.0, 0.0],
        distortion_model="inverse_brown_conrady",
    )
    assert intrinsics.model_dump() == {
        "intrinsics_matrix": [[1.0, 40.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        "distortion_coefficients": [0.0, 0.0, 0.0, 0.0, 0.0],
        "distortion_model": "inverse_brown_conrady",
    }


def test_new_camera_intrinsics():
    """Tests that we deserialize the extrinsics correctly from a dict."""
    extrinsics = CameraExtrinsics(
        world="left_rgb",
        right_rgb=Transform3D(
            matrix=np.array(
                [
                    [1.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0],
                ]
            )
        ),
    )
    assert extrinsics.model_dump() == {
        "world": "left_rgb",
        "right_rgb": {
            "matrix": [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
        },
    }
    assert (
        CameraExtrinsics.model_validate_json(extrinsics.model_dump_json()) == extrinsics
    )
