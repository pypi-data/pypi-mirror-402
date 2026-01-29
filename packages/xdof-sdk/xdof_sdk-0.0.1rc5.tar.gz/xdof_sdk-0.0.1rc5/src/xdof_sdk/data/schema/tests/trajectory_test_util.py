"""Test utilities for generating MCAP trajectories."""

import json
import random
from pathlib import Path
from typing import Dict, List

import numpy as np
from google.protobuf.timestamp_pb2 import Timestamp  # noqa: F401
from mcap_protobuf.writer import Writer as ProtobufWriter

from xdof_sdk.data.schema.keys import MCAP_TOPIC_FIELD_TO_KEY, DataKeys, key_filename
from xdof_sdk.data.schema.metadata import Metadata, StationMetadata
from xdof_sdk.data.schema.proto.robot_pb2 import GripperState, RobotState
from xdof_sdk.data.schema.station_metadata import BimanualStationExtrinsicsConfig
from xdof_sdk.data.schema.types import ArmType, DataVersion, Transform3D, WorldFrame


def generate_random_robot_state_data(
    idx: int, n_joints: int = 7
) -> Dict[str, List[float]]:
    """Generate random robot state data."""
    return {
        "position": [random.uniform(-3.14, 3.14) for _ in range(n_joints)],
        "velocity": [random.uniform(-2.0, 2.0) for _ in range(n_joints)],
        "acceleration": [random.uniform(-5.0, 5.0) for _ in range(n_joints)],
        "torque": [random.uniform(-50.0, 50.0) for _ in range(n_joints)],
        "pose": np.eye(4).flatten().tolist(),
    }


def generate_random_gripper_state_data(idx: int) -> Dict[str, List[float]]:
    """Generate random gripper state data."""
    return {
        "position": [random.uniform(0.0, 1.0)],
        "velocity": [random.uniform(-1.0, 1.0)],
        "acceleration": [random.uniform(-2.0, 2.0)],
        "torque": [random.uniform(-10.0, 10.0)],
    }


def create_mcap_file(
    filepath: Path,
    topic_data: Dict[str, List[Dict[str, List[float]]]],
    message_count: int = 100,
) -> None:
    """Create an MCAP file with the given topic data."""

    with open(filepath, "wb") as f:
        writer = ProtobufWriter(f)

        for i in range(message_count):
            for topic, data_list in topic_data.items():
                if "robot-state" in topic:
                    message = RobotState()
                    message.timestamp.FromSeconds(i)
                    data = data_list[i % len(data_list)]
                    message.position.extend(data["position"])
                    message.velocity.extend(data["velocity"])
                    message.acceleration.extend(data["acceleration"])
                    message.torque.extend(data["torque"])
                    message.pose.extend(data["pose"])
                elif "gripper-state" in topic:
                    message = GripperState()
                    message.timestamp.FromSeconds(i)
                    data = data_list[i % len(data_list)]
                    message.position.extend(data["position"])
                    message.velocity.extend(data["velocity"])
                    message.acceleration.extend(data["acceleration"])
                    message.torque.extend(data["torque"])
                else:
                    continue

                writer.write_message(
                    topic=topic, message=message, log_time=i, publish_time=i
                )

        writer.finish()


def create_test_metadata(
    arm_type: ArmType = ArmType.FRANKA, version: DataVersion = DataVersion.V2
) -> Metadata:
    """Create test metadata."""
    station_metadata = StationMetadata(
        arm_type=arm_type,
        data_version=version,
        world_frame=WorldFrame.LEFT_ARM,
        extrinsics=BimanualStationExtrinsicsConfig(
            right_arm=Transform3D(
                position=[0.0, 0.0, -0.61],
                quaternion_wxyz=[1.0, 0.0, 0.0, 0.0],
            ),
        ),
    )

    return Metadata(
        station_metadata=station_metadata,
    )


def create_test_annotations() -> Dict:
    """Create test annotations."""
    return {
        "version": "1.0",
        "annotations": [
            {"type": "segment", "from_frame": 0, "to_frame": 50, "label": "approach"},
            {"type": "segment", "from_frame": 50, "to_frame": 100, "label": "grasp"},
        ],
    }


def generate_test_trajectory_mcap(
    output_dir: Path,
    n_frames: int = 100,
    arm_type: ArmType = ArmType.FRANKA,
    single_mcap: bool = True,
) -> Path:
    """Generate a complete test trajectory with MCAPs, metadata, and annotations."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create metadata
    metadata = create_test_metadata(arm_type=arm_type)
    with open(output_dir / key_filename(DataKeys.TRAJECTORY.METADATA), "w") as f:
        f.write(metadata.model_dump_json(indent=2))

    # Create annotations
    annotations = create_test_annotations()
    with open(output_dir / key_filename(DataKeys.TRAJECTORY.ANNOTATIONS), "w") as f:
        json.dump(annotations, f, indent=2)

    # Get all topics from the mapping
    all_topics = list(MCAP_TOPIC_FIELD_TO_KEY.keys())

    if single_mcap:
        # Create one big MCAP with all topics
        topic_data = {}
        for topic in all_topics:
            if "robot-state" in topic:
                topic_data[topic] = [
                    generate_random_robot_state_data(i) for i in range(n_frames)
                ]
            elif "gripper-state" in topic:
                topic_data[topic] = [
                    generate_random_gripper_state_data(i) for i in range(n_frames)
                ]

        create_mcap_file(output_dir / "trajectory.mcap", topic_data, n_frames)
    else:
        # Create separate MCAP files for each topic
        for i, topic in enumerate(all_topics):
            if "robot-state" in topic:
                topic_data = {
                    topic: [
                        generate_random_robot_state_data(j) for j in range(n_frames)
                    ]
                }
            elif "gripper-state" in topic:
                topic_data = {
                    topic: [
                        generate_random_gripper_state_data(j) for j in range(n_frames)
                    ]
                }
            else:
                continue

            create_mcap_file(
                output_dir / f"trajectory_{i:02d}.mcap", topic_data, n_frames
            )

    return output_dir
