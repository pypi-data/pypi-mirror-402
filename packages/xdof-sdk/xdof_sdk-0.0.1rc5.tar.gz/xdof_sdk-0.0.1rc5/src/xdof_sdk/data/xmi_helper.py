import numpy as np
import numpy.typing as npt

from xdof_sdk.data.constants import ArmSide
from xdof_sdk.data.schema.metadata import Metadata
from xdof_sdk.data.schema.station_metadata import XMIExtrinsicsConfig
from xdof_sdk.data.schema.types import ArmType, Transform3D

# --- Constants and Helper Functions

# see from the back of the camera lens                     / z
#       z                                                 /
#       ^    x                                            /
#       |   ^                                            |------> x
#       |  /   -> pin whole camera convention            |
#       | /                                              |
#    y--|/                                               |y
CAMERA_LOCAL_FRAME_WORLD_TO_CAMERA_CONVENTION = np.array(
    [[0, -1, 0, 0], [0, 0, -1, 0], [1, 0, 0, 0], [0, 0, 0, 1]]
)

# see quest_coordinate_sys.png the handle's local frame
QUEST_CALIB_FRAME_TO_WORLD_FRAME = np.array(
    [[0, 0, 1, 0], [-1, 0, 0, 0], [0, -1, 0, 0], [0, 0, 0, 1]]
)


#         z                                y
#         ^    x                           |
#         |   ^                            |
#         |  /   <- in world frame  z <-- /  (vive world frame)
#         | /                            /
#   y-----|/                            x
# since we only care about the relative position, we only want to make sure it is Z-up
VIVE_CALIB_FRAME_TO_WORLD_FRAME = np.array(
    [[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]
)


def convert_left_handed_to_right_handed(
    quest_matrix: npt.NDArray[np.float64],
) -> npt.NDArray[np.float64]:
    y_flip_transform = np.array(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, -1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    intermediate_result = y_flip_transform @ quest_matrix
    final_result = intermediate_result @ y_flip_transform.T
    return final_result


def pre_process_tracker_coordinates(
    pose_mat: np.ndarray, arm_type: ArmType
) -> np.ndarray:
    """
    Similar transformation if necessary (to flip left-handed to right-handed).
    """
    if arm_type == ArmType.PASSIVE_XMI:
        return pose_mat
    if arm_type in [ArmType.XMI, ArmType.YAM_XMI]:
        return convert_left_handed_to_right_handed(pose_mat)
    raise ValueError(f"Unknown arm type: {arm_type}")


def load_pose_from_transform3d(transform: Transform3D) -> np.ndarray:
    """Convert Transform3D object to 4x4 transformation matrix."""
    return transform.matrix


def calib_frame_to_plot_world_frame(
    pose_in_calib_frame: np.ndarray,
    arm_type: ArmType,
) -> np.ndarray:
    # change or coordinate.
    if arm_type in [ArmType.XMI, ArmType.YAM_XMI]:
        matrix = QUEST_CALIB_FRAME_TO_WORLD_FRAME
    elif arm_type == ArmType.PASSIVE_XMI:
        matrix = VIVE_CALIB_FRAME_TO_WORLD_FRAME
    else:
        raise ValueError(f"Unknown arm type: {arm_type}")
    return matrix @ pose_in_calib_frame


def get_average_head_pose_collapose_to_z_up(
    head_poses_mat: np.ndarray, arm_type: ArmType
) -> np.ndarray:
    Z_AXIS_OFFSET = -1.7
    head_poses_mat_in_calibration_frame = pre_process_tracker_coordinates(
        head_poses_mat, arm_type
    )

    head_poses_mat_in_world_frame = calib_frame_to_plot_world_frame(
        head_poses_mat_in_calibration_frame, arm_type
    )
    head_poses_mat_in_world_frame_average = np.mean(
        head_poses_mat_in_world_frame, axis=0
    )
    plot_world_frame = head_poses_mat_in_world_frame_average.copy()
    plot_world_frame[:3, 3] += np.array([0, 0, Z_AXIS_OFFSET])
    plot_world_frame[:3, 2] = np.array([0, 0, 1])
    x_axis = plot_world_frame[:3, 0]
    x_axis[2] = 0
    x_axis = x_axis / np.linalg.norm(x_axis)
    y_axis = -np.cross(x_axis, np.array([0, 0, 1]))
    plot_world_frame[:3, 1] = y_axis
    plot_world_frame[:3, 0] = x_axis
    return plot_world_frame


class XmiHelper:
    """
    This class manages the XMI episode: maintaining a fixed 'world frame' and converting the raw
    data stream and camera calibration data into that world frame.

    World frame: z-up, x-forward, y-left
    Camera/Gripper convention: z-forward, x-right, y-down
    """

    def __init__(self, metadata: Metadata, final_world_frame: np.ndarray):
        # Ensure we have XMI station metadata and extrinsics
        if not metadata.station_metadata:
            raise ValueError("station_metadata is required for XMI helper")

        if not isinstance(metadata.station_metadata.extrinsics, XMIExtrinsicsConfig):
            raise ValueError("XMI extrinsics configuration is required")

        extrinsics = metadata.station_metadata.extrinsics
        self.arm_type = ArmType(metadata.station_metadata.arm_type)
        # Load raw extrinsic matrices from metadata, in calibration frame (tracker's frame)
        self.head_T_top_camera = load_pose_from_transform3d(
            extrinsics.top_camera_in_tracker
        )
        self.left_tracker_T_left_gripper = load_pose_from_transform3d(
            extrinsics.gripper_in_left_tracker
        )
        self.right_tracker_T_right_gripper = load_pose_from_transform3d(
            extrinsics.gripper_in_right_tracker
        )
        self.wrist_camera_in_gripper_flange = load_pose_from_transform3d(
            extrinsics.gripper_camera_in_gripper
        )

        # Load camera intrinsics if available
        if (
            metadata.camera_info
            and metadata.camera_info.top_camera
            and metadata.camera_info.top_camera.intrinsics
        ):
            if metadata.camera_info.top_camera.intrinsics.rgb:
                self.intrinsics = (
                    metadata.camera_info.top_camera.intrinsics.rgb.intrinsics_matrix
                )
            elif metadata.camera_info.top_camera.intrinsics.left_rgb:
                self.intrinsics = metadata.camera_info.top_camera.intrinsics.left_rgb.intrinsics_matrix
            else:
                self.intrinsics = None
        else:
            self.intrinsics = None

        # Establish the final, stable world frame based on average head pose
        assert final_world_frame.shape == (4, 4), (
            "Final world frame must be a 4x4 matrix"
        )
        self.final_world_frame = final_world_frame
        self.to_final_world_frame = np.linalg.inv(self.final_world_frame)

        # 3. Wrist cameras relative to their controllers (Hand -> Gripper -> Camera)
        # gripper frame is our standard gripper frame in the final world coordinate system
        self.left_tracker_T_left_wrist_camera = (
            self.left_tracker_T_left_gripper @ self.wrist_camera_in_gripper_flange
        )
        self.right_tracker_T_right_wrist_camera = (
            self.right_tracker_T_right_gripper @ self.wrist_camera_in_gripper_flange
        )

    def get_head_data(
        self, head_poses_mat_quest_world_frame: np.ndarray
    ) -> npt.NDArray[np.float64]:
        """
        Gets the head pose in the final world frame and the constant transform from the
        head to its camera.

        Returns:
            head_poses_in_world_frame: Head poses in the final world frame. Shape (N, 4, 4).
        """
        head_poses_in_calibration_frame = pre_process_tracker_coordinates(
            head_poses_mat_quest_world_frame, self.arm_type
        )
        head_poses_in_plot_world_frame = calib_frame_to_plot_world_frame(
            head_poses_in_calibration_frame, self.arm_type
        )
        head_poses_in_world_frame = (
            self.to_final_world_frame @ head_poses_in_plot_world_frame
        )

        return head_poses_in_world_frame

    def get_controller_data(
        self, hand_poses_mat_quest_world_frame: np.ndarray, arm_side: ArmSide
    ) -> npt.NDArray[np.float64]:
        """
        Gets controller poses in the final world frame.

        Returns:
            controller_poses_in_world_frame: Controller poses in the final world frame. Shape (N, 4, 4).
        """
        hand_poses_in_calibration_frame = pre_process_tracker_coordinates(
            hand_poses_mat_quest_world_frame, self.arm_type
        )
        hand_poses_in_plot_world_frame = calib_frame_to_plot_world_frame(
            hand_poses_in_calibration_frame, self.arm_type
        )

        hand_poses_in_world_frame = (
            self.to_final_world_frame @ hand_poses_in_plot_world_frame
        )

        return hand_poses_in_world_frame
