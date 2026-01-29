import abc
import json
import os
from collections import defaultdict
from functools import cache
from pathlib import Path
from typing import Dict, List

import cv2
import numpy as np
from mcap.reader import make_reader
from mcap_protobuf.decoder import DecoderFactory as ProtobufDecoderFactory
from mcap_ros2.decoder import DecoderFactory as Ros2DecoderFactory
from numpy.typing import NDArray

from xdof_sdk.data.constants import ArmSide, CameraPerspective, FrameConvention
from xdof_sdk.data.fk import RobotFK
from xdof_sdk.data.schema.annotations import Annotation, Segment
from xdof_sdk.data.schema.keys import MCAP_TOPIC_FIELD_TO_KEY, DataKeys, key_filename
from xdof_sdk.data.schema.metadata import Metadata
from xdof_sdk.data.schema.types import ArmType, DataVersion
from xdof_sdk.data.xmi_helper import XmiHelper, get_average_head_pose_collapose_to_z_up

GRIPPER_FLU_T_GRIPPER_RDF = np.array(
    [
        [0, -1, 0, 0],
        [0, 0, -1, 0],
        [1, 0, 0, 0],
        [0, 0, 0, 1],
    ]
).T

GRIPPER_FLU_T_GRIPPER_URF = np.array(
    [
        [0, 0, 1, 0],
        [0, -1, 0, 0],
        [1, 0, 0, 0],
        [0, 0, 0, 1],
    ]
).T

POSE_KEYS_TO_RESHAPE = {
    DataKeys.ACTION.EE_POSE.LEFT,
    DataKeys.ACTION.EE_POSE.RIGHT,
    DataKeys.ACTION.EE_POSE.HEAD,
    DataKeys.ACTION.EE_POSE.LEFT_HEAD,
    DataKeys.ACTION.EE_POSE.RIGHT_HEAD,
    DataKeys.OBS.JOINT.POSE.LEFT,
    DataKeys.OBS.JOINT.POSE.RIGHT,
}


def _load_video(path: Path):
    """Load video frames as RGB arrays."""
    cap = cv2.VideoCapture(str(path))
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            yield frame[:, :, ::-1]  # BGR to RGB
    finally:
        cap.release()


class AnnotationSegmentLookup:
    """Lookup for segments by frame."""

    def __init__(self, segments: List[Segment]):
        self.segments = segments

    def __getitem__(self, frame: int) -> List[str]:
        """Get labels for a frame."""
        return [
            segment.label
            for segment in self.segments
            if segment.from_frame <= frame < segment.to_frame
        ]


def load_per_frame_segment_annotation(path: Path) -> AnnotationSegmentLookup:
    """Load frame annotations from JSON using proper schema objects."""
    if not path.exists():
        return AnnotationSegmentLookup([])

    with open(path) as f:
        data = json.load(f)

    if not data:
        return AnnotationSegmentLookup([])

    annotation = Annotation.model_validate(data)
    segments = [
        segment for segment in annotation.annotations if segment.type == "segment"
    ]

    return AnnotationSegmentLookup(segments)


class Trajectory(abc.ABC):
    def __init__(self, path: Path, load_videos: bool = False):
        self.path = path

        with open(path / key_filename(DataKeys.TRAJECTORY.METADATA)) as f:
            self.metadata = Metadata.model_validate_json(f.read())

        self._annotations = load_per_frame_segment_annotation(
            path / key_filename(DataKeys.TRAJECTORY.ANNOTATIONS)
        )

        # Ensure we have station metadata
        if not self.metadata.station_metadata:
            raise ValueError("station_metadata is required")

        if self.metadata.station_metadata.data_version >= DataVersion.V2:
            self._trajectory_data = self._load_data_mcap(path)
        else:
            self._trajectory_data = self._load_data(path, load_videos)

        arm_type = self.metadata.station_metadata.arm_type
        if arm_type in (ArmType.YAM, ArmType.ARX):
            self._n_dof_arm = 6
        elif arm_type == ArmType.FRANKA:
            self._n_dof_arm = 7
        elif arm_type in [ArmType.XMI, ArmType.YAM_XMI, ArmType.PASSIVE_XMI]:
            self._n_dof_arm = 0
        else:
            raise ValueError(f"Arm type {arm_type} not supported")

        # Get data version
        if self.metadata.station_metadata.data_version:
            self.data_version = self.metadata.station_metadata.data_version
        else:
            self.data_version = DataVersion.V0

    def _load_data(
        self, path: Path, load_videos: bool = False
    ) -> Dict[str, NDArray[np.float64]]:
        """Load trajectory data from .npy and .mp4 files."""

        if not path.exists():
            print(f"Path {path} does not exist")
            return {}

        data = {}

        npy_files = path.glob("*.npy")
        for file in npy_files:
            key = os.path.basename(file).split(".")[0]
            loaded_data = np.load(file, allow_pickle=True)
            # Makes it easy to splice later if everything is 2D
            data[key] = (
                loaded_data[:, np.newaxis] if loaded_data.ndim == 1 else loaded_data
            )

        if load_videos:
            mp4_files = path.glob("*.mp4")
            for file in mp4_files:
                key = os.path.basename(file).split(".")[0]
                data[key] = np.array(list(_load_video(file)))

        return data

    def _load_data_mcap(self, path: Path) -> Dict[str, NDArray[np.float64]]:
        """Load trajectory data from .mcap files."""
        data = defaultdict(list)
        ts_map = defaultdict(lambda: -1)

        # MacOS creates .hidden files sometimes?
        if path.is_dir():
            mcap_files = set(path.glob("*.mcap")) - set(path.glob(".*"))
        else:
            mcap_files = [path]

        for file in mcap_files:
            self._load_mcap_file(file, data, ts_map)

        data = {k: np.array(v) for k, v in data.items()}

        for key, value in data.items():
            if key in POSE_KEYS_TO_RESHAPE and value.ndim == 2 and value.shape[1] == 16:
                # mcap protocol stores the pose in 1x16 matrix, we need to reshape it to 4x4 matrix.
                data[key] = value.reshape(-1, 4, 4)

        return data

    def _load_mcap_file(
        self, file: Path, data: dict[str, list[list]], ts_map: dict[str, int]
    ) -> None:
        with open(os.path.join(file), "rb") as f:
            reader = make_reader(
                f, decoder_factories=[ProtobufDecoderFactory(), Ros2DecoderFactory()]
            )
            for _schema, channel, message, proto_msg in reader.iter_decoded_messages():
                topic = channel.topic

                if topic not in MCAP_TOPIC_FIELD_TO_KEY:
                    continue

                # Check timestamp monotonicity per topic
                if ts_map[topic] > message.log_time:
                    raise ValueError(
                        f"Timestamp is not monotonically increasing for topic {topic}"
                    )
                ts_map[topic] = message.log_time

                # Extract fields from proto message and map to DataKeys
                field_mappings = MCAP_TOPIC_FIELD_TO_KEY[topic]
                for field_name, data_key in field_mappings.items():
                    if not hasattr(proto_msg, field_name):
                        continue

                    field_value = getattr(proto_msg, field_name)
                    data[data_key].append(field_value)

    # TODO: mluogh: this doesn't make that much sense for async data
    @property
    def n_frames(self) -> int:
        if DataKeys.TRAJECTORY.GLOBAL_TIMESTAMP in self._trajectory_data:
            return len(self._trajectory_data[DataKeys.TRAJECTORY.GLOBAL_TIMESTAMP])
        elif DataKeys.CAMERA.TIMESTAMP.TOP in self._trajectory_data:
            return len(self._trajectory_data[DataKeys.CAMERA.TIMESTAMP.TOP])

        raise ValueError(
            "No reasonable way to determine number of frames if global timestamp is not found"
        )

    def get_joint_pos_obs(self, arm_side: ArmSide) -> NDArray[np.float64]:
        raise NotImplementedError("Implement in subclass")

    def get_joint_pos_action(self, arm_side: ArmSide) -> NDArray[np.float64]:
        raise NotImplementedError("Implement in subclass")

    @abc.abstractmethod
    @cache
    def get_ee_pose_obs(
        self,
        arm_side: ArmSide,
        frame_convention: FrameConvention = FrameConvention.GRIPPER_RDF,
    ) -> NDArray[np.float64]:
        raise NotImplementedError("Implement in subclass")

    @abc.abstractmethod
    @cache
    def get_ee_pose_action(
        self,
        arm_side: ArmSide,
        frame_convention: FrameConvention = FrameConvention.GRIPPER_RDF,
    ) -> NDArray[np.float64]:
        raise NotImplementedError("Implement in subclass")

    def get_gripper_pos_obs(self, arm_side: ArmSide) -> NDArray[np.float64]:
        """Returns the gripper position where 0 is closed, 1 is open."""
        if f"{arm_side.value}-gripper_pos" in self._trajectory_data:
            return self._trajectory_data[f"{arm_side.value}-gripper_pos"]
        else:
            return self._trajectory_data[f"{arm_side.value}-joint_pos"][
                :, self._n_dof_arm :
            ]

    def get_gripper_pos_action(self, arm_side: ArmSide) -> NDArray[np.float64]:
        return self._trajectory_data[f"action-{arm_side.value}-pos"][
            :, self._n_dof_arm :
        ]

    def get_video(self, camera_perspective: CameraPerspective) -> NDArray[np.float64]:
        if f"{camera_perspective.value}_camera-images-rgb" in self._trajectory_data:
            return self._trajectory_data[
                f"{camera_perspective.value}_camera-images-rgb"
            ]
        else:
            raise ValueError(f"Video {camera_perspective.value} not loaded")

    def get_video_path(self, camera_perspective: CameraPerspective) -> Path:
        return self.path / f"{camera_perspective.value}_camera-images-rgb.mp4"

    @property
    def annotation_map(self) -> AnnotationSegmentLookup:
        return self._annotations

    @cache
    def get_data_by_key(
        self, key: str, frame_convention: FrameConvention = FrameConvention.GRIPPER_RDF
    ) -> NDArray[np.float64]:
        """Get data by key, using existing methods when available, otherwise loading from file."""
        # Check if data is already loaded in trajectory_data
        if key in self._trajectory_data:
            return self._trajectory_data[key]

        # Dictionary dispatch for specialized methods
        key_handlers = {
            # Joint position observations
            DataKeys.OBS.JOINT.POS.LEFT: lambda: self.get_joint_pos_obs(ArmSide.LEFT),
            DataKeys.OBS.JOINT.POS.RIGHT: lambda: self.get_joint_pos_obs(ArmSide.RIGHT),
            # Joint position actions
            DataKeys.ACTION.JOINT.POS.LEFT: lambda: self.get_joint_pos_action(
                ArmSide.LEFT
            ),
            DataKeys.ACTION.JOINT.POS.RIGHT: lambda: self.get_joint_pos_action(
                ArmSide.RIGHT
            ),
            # Gripper position observations
            DataKeys.OBS.GRIPPER.POS.LEFT: lambda: self.get_gripper_pos_obs(
                ArmSide.LEFT
            ),
            DataKeys.OBS.GRIPPER.POS.RIGHT: lambda: self.get_gripper_pos_obs(
                ArmSide.RIGHT
            ),
            # Gripper position actions
            DataKeys.ACTION.GRIPPER.POS.LEFT: lambda: self.get_gripper_pos_action(
                ArmSide.LEFT
            ),
            DataKeys.ACTION.GRIPPER.POS.RIGHT: lambda: self.get_gripper_pos_action(
                ArmSide.RIGHT
            ),
            # EE pose methods need frame_convention parameter
            DataKeys.OBS.JOINT.POSE.LEFT: lambda: self.get_ee_pose_obs(
                ArmSide.LEFT, frame_convention
            ),
            DataKeys.OBS.JOINT.POSE.RIGHT: lambda: self.get_ee_pose_obs(
                ArmSide.RIGHT, frame_convention
            ),
            DataKeys.ACTION.EE_POSE.LEFT: lambda: self.get_ee_pose_action(
                ArmSide.LEFT, frame_convention
            ),
            DataKeys.ACTION.EE_POSE.RIGHT: lambda: self.get_ee_pose_action(
                ArmSide.RIGHT, frame_convention
            ),
            # Video data
            DataKeys.CAMERA.IMAGES.TOP: lambda: self.get_video(CameraPerspective.TOP),
            DataKeys.CAMERA.IMAGES.LEFT: lambda: self.get_video(CameraPerspective.LEFT),
            DataKeys.CAMERA.IMAGES.RIGHT: lambda: self.get_video(
                CameraPerspective.RIGHT
            ),
        }

        # Try to use specialized method
        try:
            if key in key_handlers:
                return key_handlers[key]()
        except (NotImplementedError, ValueError, KeyError):
            # If specialized method fails, fall through to file loading
            pass

        file_path = self.path / key_filename(key)
        if file_path.exists():
            if file_path.suffix == ".mp4":
                # Handle video files (would need cv2 or similar)
                raise NotImplementedError(
                    "Video loading from get_data_by_key not implemented yet"
                )
            else:
                # Load numpy file
                return np.load(file_path)
        else:
            raise FileNotFoundError(
                f"No data found for key '{key}' - file {file_path} does not exist"
            )


class ArmTrajectory(Trajectory):
    def __init__(self, path: Path, load_videos: bool = False):
        super().__init__(path, load_videos)

        # We know station_metadata exists from parent validation
        assert self.metadata.station_metadata is not None
        arm_type = self.metadata.station_metadata.arm_type
        if arm_type in (ArmType.YAM, ArmType.ARX):
            self._ROBOT_CONVENTION_T_GRIPPER_FLU = np.array(
                [
                    [0, 0, 1, 0],
                    [0, 1, 0, 0],
                    [-1, 0, 0, 0],
                    [0, 0, 0, 1],
                ]
            ).T

        elif arm_type == ArmType.FRANKA:
            self._ROBOT_CONVENTION_T_GRIPPER_FLU = np.array(
                [
                    [0, 0, 1, 0],
                    [0, -1, 0, 0],
                    [1, 0, 0, 0],
                    [0, 0, 0, 1],
                ]
            ).T

        self._robot_fk = RobotFK(self.metadata)
        self._ee_left_action = self._robot_fk.fk(
            self.get_joint_pos_action(ArmSide.LEFT)
        )
        self._ee_right_action = self._robot_fk.fk(
            self.get_joint_pos_action(ArmSide.RIGHT),
            extrinsics=self._robot_fk.right_T_left,
        )
        self._ee_left_obs = self._robot_fk.fk(self.get_joint_pos_obs(ArmSide.LEFT))
        self._ee_right_obs = self._robot_fk.fk(
            self.get_joint_pos_obs(ArmSide.RIGHT),
            extrinsics=self._robot_fk.right_T_left,
        )

    def get_joint_pos_obs(self, arm_side: ArmSide) -> NDArray[np.float64]:
        return self._trajectory_data[f"{arm_side.value}-joint_pos"][
            :, : self._n_dof_arm
        ]

    def get_joint_pos_action(self, arm_side: ArmSide) -> NDArray[np.float64]:
        return self._trajectory_data[f"action-{arm_side.value}-pos"][
            :, : self._n_dof_arm
        ]

    @cache
    def get_ee_pose_obs(
        self,
        arm_side: ArmSide,
        frame_convention: FrameConvention = FrameConvention.GRIPPER_RDF,
    ) -> NDArray[np.float64]:
        base_obs = self._ee_left_obs if arm_side == ArmSide.LEFT else self._ee_right_obs

        base_obs = base_obs @ self._ROBOT_CONVENTION_T_GRIPPER_FLU

        if frame_convention == FrameConvention.GRIPPER_RDF:
            return base_obs @ GRIPPER_FLU_T_GRIPPER_RDF
        elif frame_convention == FrameConvention.GRIPPER_URF:
            return base_obs @ GRIPPER_FLU_T_GRIPPER_URF

        return base_obs

    @cache
    def get_ee_pose_action(
        self,
        arm_side: ArmSide,
        frame_convention: FrameConvention = FrameConvention.GRIPPER_RDF,
    ) -> NDArray[np.float64]:
        base_action = (
            self._ee_left_action if arm_side == ArmSide.LEFT else self._ee_right_action
        )

        base_action = base_action @ self._ROBOT_CONVENTION_T_GRIPPER_FLU

        if frame_convention == FrameConvention.GRIPPER_RDF:
            return base_action @ GRIPPER_FLU_T_GRIPPER_RDF
        elif frame_convention == FrameConvention.GRIPPER_URF:
            return base_action @ GRIPPER_FLU_T_GRIPPER_URF

        return base_action

    @cache
    def fk_for_arm(
        self,
        arm_side: ArmSide,
        extrinsics: NDArray[np.float64] | None = None,
        site_name: str | None = None,
        body_name: str | None = None,
    ):
        q = self.get_joint_pos_obs(arm_side)
        return self._robot_fk.fk(
            q, extrinsics=extrinsics, site_name=site_name, body_name=body_name
        )


class XmiTrajectory(Trajectory):
    def __init__(self, path: Path, arm_type: ArmType, load_videos: bool = False):
        super().__init__(path, load_videos)
        self.arm_type = arm_type

        final_world_frame = get_average_head_pose_collapose_to_z_up(
            self._trajectory_data[self._get_head_key()], self.arm_type
        )

        self._xmi_helper = XmiHelper(self.metadata, final_world_frame)

    def _get_head_key(self) -> str:
        if DataKeys.ACTION.EE_POSE.HEAD in self._trajectory_data:
            return DataKeys.ACTION.EE_POSE.HEAD
        elif DataKeys.ACTION.EE_POSE.LEFT_HEAD in self._trajectory_data:
            return DataKeys.ACTION.EE_POSE.LEFT_HEAD
        elif DataKeys.ACTION.EE_POSE.RIGHT_HEAD in self._trajectory_data:
            return DataKeys.ACTION.EE_POSE.RIGHT_HEAD

        raise ValueError(
            f"No head key for arm type {self.arm_type} with data version {self.data_version}"
        )

    @cache
    def get_ee_pose_action(
        self,
        arm_side: ArmSide,
        frame_convention: FrameConvention = FrameConvention.GRIPPER_RDF,
    ) -> NDArray[np.float64]:
        if arm_side == ArmSide.LEFT:
            return (
                self.get_controller_pose_action(ArmSide.LEFT)
                @ self._xmi_helper.left_tracker_T_left_gripper
            )
        else:
            return (
                self.get_controller_pose_action(ArmSide.RIGHT)
                @ self._xmi_helper.right_tracker_T_right_gripper
            )

    @cache
    def get_controller_pose_action(self, arm_side: ArmSide) -> NDArray[np.float64]:
        hand_poses_mat = self._load_hand_poses_tracker_world_frame(arm_side)
        return self._xmi_helper.get_controller_data(hand_poses_mat, arm_side)

    @cache
    def get_wrist_camera_pose_action(self, arm_side: ArmSide) -> NDArray[np.float64]:
        if arm_side == ArmSide.LEFT:
            return (
                self.get_controller_pose_action(ArmSide.LEFT)
                @ self._xmi_helper.left_tracker_T_left_wrist_camera
            )
        else:
            return (
                self.get_controller_pose_action(ArmSide.RIGHT)
                @ self._xmi_helper.right_tracker_T_right_wrist_camera
            )

    @cache
    def get_head_pose_action(self) -> NDArray[np.float64]:
        head_poses_mat = self._trajectory_data[self._get_head_key()]
        return self._xmi_helper.get_head_data(head_poses_mat)

    @cache
    def get_head_camera_pose_action(self) -> NDArray[np.float64]:
        return self.get_head_pose_action() @ self._xmi_helper.head_T_top_camera

    @cache
    def _load_hand_poses_tracker_world_frame(self, arm_side: ArmSide) -> np.ndarray:
        if self.data_version == DataVersion.V1_1:
            if arm_side == ArmSide.LEFT:
                return self._trajectory_data[DataKeys.ACTION.EE_POSE.LEFT]
            elif arm_side == ArmSide.RIGHT:
                return self._trajectory_data[DataKeys.ACTION.EE_POSE.RIGHT]
            else:
                raise ValueError(f"Unknown arm side: {arm_side}")

        elif self.data_version == DataVersion.V1:
            return self._trajectory_data[f"action-{arm_side.value}-hand"]

        elif self.data_version == DataVersion.V0:
            moving_quest_world_frame = self._trajectory_data[
                f"action-{arm_side.value}-quest_world_frame"
            ]
            hand_pose_in_quest_moving_world_frame = self._trajectory_data[
                f"action-{arm_side.value}-hand_in_quest_world_frame"
            ]
            # in quest world frame
            return moving_quest_world_frame @ hand_pose_in_quest_moving_world_frame
        else:
            raise ValueError(f"Unknown data version: {self.data_version}")

    def get_joint_pos_obs(
        self, arm_side: ArmSide, include_gripper: bool = True
    ) -> NDArray[np.float64]:
        raise ValueError("XMI has no joint positions")

    def get_joint_pos_action(
        self, arm_side: ArmSide, include_gripper: bool = True
    ) -> NDArray[np.float64]:
        raise ValueError("XMI has no joint positions")

    @cache
    def get_ee_pose_obs(self, arm_side: ArmSide) -> NDArray[np.float64]:
        raise ValueError("XMI has no EE pose obs, use get_ee_pose_action()")


def load_trajectory(path: Path | str, load_videos: bool = False) -> Trajectory:
    if isinstance(path, str):
        path = Path(path)

    metadata = Metadata.model_validate_json(
        open(path / key_filename(DataKeys.TRAJECTORY.METADATA)).read()
    )
    if metadata.station_metadata is None:
        raise ValueError("station_metadata is required")

    arm_type = ArmType(metadata.station_metadata.arm_type)
    if arm_type in [ArmType.XMI, ArmType.YAM_XMI, ArmType.PASSIVE_XMI]:
        return XmiTrajectory(path, arm_type, load_videos)
    else:
        return ArmTrajectory(path, load_videos)


if __name__ == "__main__":
    trajectory = load_trajectory(
        Path("standard/yam/fold_napkin_utensils/episode_64b69550")
    )
    print(trajectory._trajectory_data.keys())
