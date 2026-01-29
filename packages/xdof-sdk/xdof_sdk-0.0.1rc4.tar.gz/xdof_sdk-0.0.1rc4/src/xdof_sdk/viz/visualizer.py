"""
Trajectory Data Visualization Tool

Visualize robot trajectory data and camera feeds using Rerun.
"""

import time
from pathlib import Path
from typing import List

import cv2
import numpy as np
import rerun as rr
import tyro
from rerun.datatypes import Mat3x3

from xdof_sdk.data.schema.keys import DataKeys
from xdof_sdk.data.trajectory import (
    ArmSide,
    ArmTrajectory,
    CameraPerspective,
    FrameConvention,
    Trajectory,
    XmiTrajectory,
    load_trajectory,
)
from xdof_sdk.viz.name_map import get_viz_name

# Constants
FPS = 30
CAM_OFFSET = [0, 0.09, -0.05]
CAM_ANGLE = np.pi / 4

# Camera names using DataKeys and viz name mapping
TOP_CAMERA_NAME = get_viz_name(DataKeys.CAMERA.IMAGES.TOP)
LEFT_CAMERA_NAME = get_viz_name(DataKeys.CAMERA.IMAGES.LEFT)
RIGHT_CAMERA_NAME = get_viz_name(DataKeys.CAMERA.IMAGES.RIGHT)

LEFT_EE_POSE_NAME = get_viz_name(DataKeys.ACTION.EE_POSE.LEFT)
RIGHT_EE_POSE_NAME = get_viz_name(DataKeys.ACTION.EE_POSE.RIGHT)
HEAD_POSE_NAME = get_viz_name(DataKeys.ACTION.EE_POSE.HEAD)

MAX_WIDTH = 1280


def log_transform(name: str, matrix: np.ndarray):
    """Log 4x4 transformation matrix."""
    rr.log(
        name,
        rr.Transform3D(
            axis_length=0.1,
            translation=matrix[:3, 3],
            mat3x3=Mat3x3(matrix[:3, :3].flatten()),
        ),
    )


def log_data_by_key(
    trajectory: Trajectory,
    data_keys: List[str],
    frame: int,
    frame_convention: FrameConvention = FrameConvention.GRIPPER_RDF,
):
    """
    Automatically log data for given keys based on data shape.

    Args:
        trajectory: Trajectory object with get_data_by_key method
        data_keys: List of data key strings to log
        frame: Frame index to visualize
    """
    for key in data_keys:
        try:
            # Get the data using the trajectory's get_data_by_key method
            data = trajectory.get_data_by_key(key, frame_convention)

            if data is None or len(data) == 0:
                continue

            # Get the data for the specific frame
            frame_data = data[frame] if frame < len(data) else data[-1]

            # Get visualization-friendly name
            viz_name = get_viz_name(key)

            # Handle different data shapes
            if frame_data.shape == (4, 4):
                # 4x4 transformation matrix
                log_transform(viz_name, frame_data)

            elif len(frame_data.shape) == 1:
                # 1D array - log each element as scalar
                if len(frame_data) == 1:
                    # Single scalar value
                    rr.log(viz_name, rr.Scalars(frame_data[0]))
                else:
                    # Multiple values - log each individually
                    for i, value in enumerate(frame_data):
                        rr.log(f"{viz_name}/{i}", rr.Scalars(value))

            elif len(frame_data.shape) == 2:
                # 2D array
                if frame_data.shape[0] == 4 and frame_data.shape[1] == 4:
                    # 4x4 matrix
                    log_transform(viz_name, frame_data)
                else:
                    # Other 2D data - log as tensor
                    rr.log(viz_name, rr.Tensor(frame_data))

            else:
                # Higher dimensional data - log as tensor
                rr.log(viz_name, rr.Tensor(frame_data))

        except Exception as e:
            print(f"Warning: Failed to log data for key '{key}': {e}")
            continue


def log_video(name: str, video_path: Path, timestamps: List[int]):
    asset_video = rr.AssetVideo(path=str(video_path))
    # Log video to hierarchical path: name/camera/image
    topic = f"{name}/camera/image"

    rr.log(topic, asset_video, static=True)
    rr.send_columns(
        topic,
        indexes=[rr.TimeColumn("time", timestamp=[t * 1e-9 for t in timestamps])],
        columns=rr.VideoFrameReference.columns_nanos(timestamps),
    )


# Cache for video dimensions and scaled assets
_video_dimensions_cache = {}


def log_coordinate_with_video(
    pose, camera_relative_pose, video_path, pose_entity_path, focal_length=20
):
    """
    Log pose in world frame and camera with hierarchical structure.

    Args:
        pose: 4x4 transformation matrix for the coordinate frame
        camera_relative_pose: 4x4 camera pose relative to the coordinate frame
        video_path: Path to video file (for dimensions)
        pose_entity_path: Rerun entity path (should match log_video name)
        focal_length: Camera focal length for visualization
    """
    width, height, scale = 640, 480, 1
    if video_path.exists():
        video_key = str(video_path)
        if video_key not in _video_dimensions_cache:
            cap = cv2.VideoCapture(str(video_path))
            if cap.isOpened():
                orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                if orig_width > MAX_WIDTH or orig_height > MAX_WIDTH:
                    scale = min(MAX_WIDTH / orig_width, MAX_WIDTH / orig_height)
                else:
                    scale = 1
                cap.release()
                _video_dimensions_cache[video_key] = (orig_width, orig_height, scale)
            else:
                raise ValueError(f"Failed to open video at {video_path}")

        width, height, scale = _video_dimensions_cache[video_key]

    # Log main coordinate frame with smaller axis for better spacing
    rr.log(
        pose_entity_path,
        rr.Transform3D(
            axis_length=0.15,
            translation=pose[:3, 3],
            mat3x3=Mat3x3(pose[:3, :3].flatten()),
        ),
    )

    # Log up arrow for visual reference
    rr.log(
        f"{pose_entity_path}-arrow-up",
        rr.Arrows3D(
            origins=pose[:3, 3],
            vectors=np.array([0, 0, 0.02]),
            colors=[[0, 0, 255]],
        ),
    )

    # Log camera as child entity with relative transform
    camera_entity_path = f"{pose_entity_path}/camera"
    rr.log(
        camera_entity_path,
        rr.Transform3D(
            axis_length=0.15,
            translation=camera_relative_pose[:3, 3],
            mat3x3=Mat3x3(camera_relative_pose[:3, :3].flatten()),
            scale=scale,
        ),
    )

    # Log camera pinhole model at camera entity (matches video location)
    rr.log(
        camera_entity_path,
        rr.Pinhole(focal_length=focal_length, width=width, height=height),
    )


def visualize_robot(
    trajectory: ArmTrajectory,
    frame: int,
    frame_convention: FrameConvention = FrameConvention.GRIPPER_RDF,
    extra_data_keys: List[str] | None = None,
):
    """Visualize robot trajectory data."""
    extra_data_keys = extra_data_keys or []

    rr.log("world-coordinate", rr.Transform3D(axis_length=0.1, translation=np.zeros(3)))

    data_keys: List[str] = [
        DataKeys.OBS.JOINT.POS.LEFT,
        DataKeys.OBS.JOINT.POS.RIGHT,
        DataKeys.OBS.JOINT.POSE.LEFT,
        DataKeys.OBS.JOINT.POSE.RIGHT,
        DataKeys.OBS.GRIPPER.POS.LEFT,
        DataKeys.OBS.GRIPPER.POS.RIGHT,
    ] + extra_data_keys

    log_data_by_key(trajectory, data_keys, frame, frame_convention)


def visualize_xmi(
    trajectory: XmiTrajectory,
    frame: int,
    frame_convention: FrameConvention = FrameConvention.GRIPPER_RDF,
    extra_data_keys: List[str] | None = None,
):
    """Visualize XMI trajectory data."""

    extra_data_keys = extra_data_keys or []

    data_keys: List[str] = [
        DataKeys.OBS.GRIPPER.POS.LEFT,
        DataKeys.OBS.GRIPPER.POS.RIGHT,
        DataKeys.ACTION.GRIPPER.POS.LEFT,
        DataKeys.ACTION.GRIPPER.POS.RIGHT,
    ] + extra_data_keys

    log_data_by_key(trajectory, data_keys, frame, frame_convention)

    # Head camera (camera pose directly, no relative transform needed)
    head_camera_pose = trajectory.get_head_camera_pose_action()[frame]
    log_coordinate_with_video(
        head_camera_pose,
        np.eye(4),  # Camera pose is already the camera, no relative transform
        # head_camera_pose,
        trajectory.get_video_path(CameraPerspective.TOP),
        HEAD_POSE_NAME,
        focal_length=70,
    )

    # Left gripper and wrist camera
    left_ee_pose = trajectory.get_ee_pose_action(ArmSide.LEFT, frame_convention)[frame]
    left_camera_pose = trajectory.get_wrist_camera_pose_action(ArmSide.LEFT)[frame]
    # Calculate camera pose relative to gripper
    left_camera_relative = np.linalg.inv(left_ee_pose) @ left_camera_pose

    log_coordinate_with_video(
        left_ee_pose,
        left_camera_relative,
        trajectory.get_video_path(CameraPerspective.LEFT),
        LEFT_EE_POSE_NAME,
        focal_length=70,
    )

    # Right gripper and wrist camera
    right_ee_pose = trajectory.get_ee_pose_action(ArmSide.RIGHT, frame_convention)[
        frame
    ]
    right_camera_pose = trajectory.get_wrist_camera_pose_action(ArmSide.RIGHT)[frame]
    # Calculate camera pose relative to gripper
    right_camera_relative = np.linalg.inv(right_ee_pose) @ right_camera_pose

    log_coordinate_with_video(
        right_ee_pose,
        right_camera_relative,
        trajectory.get_video_path(CameraPerspective.RIGHT),
        RIGHT_EE_POSE_NAME,
        focal_length=70,
    )


def _visualize_trajectory(
    trajectory: Trajectory,
    frame_convention: FrameConvention = FrameConvention.GRIPPER_RDF,
):
    """Core visualization logic without rerun initialization."""
    frames = trajectory.n_frames
    timestamps = [int(t * (1e9 // FPS)) for t in range(frames)]

    print(f"Visualizing {frames} frames of {type(trajectory).__name__} trajectory")
    if isinstance(trajectory, XmiTrajectory):
        top_camera_name = HEAD_POSE_NAME
        left_camera_name = LEFT_EE_POSE_NAME
        right_camera_name = RIGHT_EE_POSE_NAME
    elif isinstance(trajectory, ArmTrajectory):
        top_camera_name = TOP_CAMERA_NAME
        left_camera_name = LEFT_CAMERA_NAME
        right_camera_name = RIGHT_CAMERA_NAME
    else:
        raise ValueError(f"Unsupported trajectory type: {type(trajectory).__name__}")
    log_video(
        top_camera_name,
        trajectory.get_video_path(CameraPerspective.TOP),
        timestamps,
    )

    log_video(
        left_camera_name,
        trajectory.get_video_path(CameraPerspective.LEFT),
        timestamps,
    )
    log_video(
        right_camera_name,
        trajectory.get_video_path(CameraPerspective.RIGHT),
        timestamps,
    )

    # Visualize
    for frame, timestamp in enumerate(timestamps):
        rr.set_time("time", timestamp=1e-9 * timestamp)

        for label in trajectory.annotation_map[frame]:
            rr.log("annotations", rr.TextLog(label, level=rr.TextLogLevel.INFO))

        # Visualize data
        if isinstance(trajectory, XmiTrajectory):
            visualize_xmi(trajectory, frame, frame_convention)
        elif isinstance(trajectory, ArmTrajectory):
            visualize_robot(trajectory, frame, frame_convention)


def visualize_trajectory_local(
    trajectory: Trajectory,
    frame_convention: FrameConvention = FrameConvention.GRIPPER_RDF,
):
    """Visualize trajectory with local GUI."""
    rr.init("trajectory-viz", spawn=True)
    _visualize_trajectory(trajectory, frame_convention)


def visualize_trajectory_headless(
    trajectory: Trajectory,
    frame_convention: FrameConvention = FrameConvention.GRIPPER_RDF,
    web_port: int = 9090,
    grpc_port: int = 9876,
    open_browser: bool = False,
) -> str:
    """Visualize trajectory in headless mode and return the web URL"""
    rr.init("trajectory-viz", spawn=False)

    # Start headless server
    grpc_url = rr.serve_grpc()
    rr.serve_web_viewer(
        open_browser=open_browser, web_port=web_port, connect_to=grpc_url
    )

    web_url = f"http://localhost:{web_port}/?url=rerun%2Bhttp://localhost:{grpc_port}/proxy&renderer=webgl"
    print("🌐 Rerun web viewer started!")
    print("⚠️  Click or copy this URL. ")
    print(
        "⚠️ ⚠️  Note: Make sure to copy the URL exactly with `%2B`, not `+`!!! Some terminals will try to be clever and convert `+` to `%2B`."
    )
    print(f"   <{web_url}>")
    _visualize_trajectory(trajectory, frame_convention)

    return web_url


def visualize_trajectory(
    trajectory: Trajectory,
    frame_convention: FrameConvention = FrameConvention.GRIPPER_RDF,
):
    """Main visualization function (backwards compatibility)."""
    visualize_trajectory_local(trajectory, frame_convention)


def main(
    data_path: str,
    frame_convention: FrameConvention = FrameConvention.GRIPPER_RDF,
    headless: bool = False,
    web_port: int = 9090,
    grpc_port: int = 9876,
    open_browser: bool = False,
):
    trajectory = load_trajectory(Path(data_path))

    if not headless:
        return visualize_trajectory_local(trajectory, frame_convention)

    visualize_trajectory_headless(
        trajectory, frame_convention, web_port, grpc_port, open_browser
    )
    # Keep server running until Ctrl+C
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Ctrl-C received. Exiting.")


if __name__ == "__main__":
    tyro.cli(main)
