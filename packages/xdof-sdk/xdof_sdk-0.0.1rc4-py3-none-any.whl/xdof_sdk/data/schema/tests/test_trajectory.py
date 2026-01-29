"""Tests for trajectory loading from MCAP files."""

import tempfile
from pathlib import Path

from xdof_sdk.data.schema.keys import DataKeys
from xdof_sdk.data.schema.tests.trajectory_test_util import (
    generate_test_trajectory_mcap,
)
from xdof_sdk.data.schema.types import ArmType, DataVersion
from xdof_sdk.data.trajectory import load_trajectory


def test_load_single_large_mcap():
    """Test loading from a single MCAP file containing all topics."""
    with tempfile.TemporaryDirectory() as temp_dir:
        trajectory_dir = generate_test_trajectory_mcap(
            Path(temp_dir) / "test_trajectory",
            n_frames=50,
            arm_type=ArmType.YAM,
            single_mcap=True,
        )

        trajectory = load_trajectory(trajectory_dir)

        # Verify trajectory loaded successfully
        assert trajectory is not None
        assert trajectory.metadata.station_metadata
        assert (
            trajectory.metadata.station_metadata.data_version.value >= DataVersion.V2
        )  # Should be V2 for MCAP

        # Test that we can access data through get_data_by_key
        left_joint_pos = trajectory.get_data_by_key(DataKeys.OBS.JOINT.POS.LEFT)
        assert left_joint_pos.shape == (50, 7)  # 50 frames, 7 joints for Franka

        right_joint_pos = trajectory.get_data_by_key(DataKeys.OBS.JOINT.POS.RIGHT)
        assert right_joint_pos.shape == (50, 7)

        left_joint_vel = trajectory.get_data_by_key(DataKeys.OBS.JOINT.VEL.LEFT)
        assert left_joint_vel.shape == (50, 7)

        left_gripper_pos = trajectory.get_data_by_key(DataKeys.OBS.GRIPPER.POS.LEFT)
        assert left_gripper_pos.shape == (50, 1)  # 1 gripper DOF

        # Test action data
        action_left_pos = trajectory.get_data_by_key(DataKeys.ACTION.JOINT.POS.LEFT)
        assert action_left_pos.shape == (50, 7)

        action_left_pose = trajectory.get_data_by_key(DataKeys.ACTION.EE_POSE.LEFT)
        assert action_left_pose.shape == (50, 4, 4)


def test_load_multiple_small_mcaps():
    """Test loading from multiple MCAP files, each containing one topic."""
    with tempfile.TemporaryDirectory() as temp_dir:
        trajectory_dir = generate_test_trajectory_mcap(
            Path(temp_dir) / "test_trajectory_multi",
            n_frames=30,
            arm_type=ArmType.YAM,
            single_mcap=False,
        )

        trajectory = load_trajectory(trajectory_dir)

        # Verify trajectory loaded successfully
        assert trajectory is not None
        assert trajectory.metadata.station_metadata
        assert trajectory.metadata.station_metadata.data_version.value >= DataVersion.V2

        # Test that we can access the same data as single MCAP test
        left_joint_pos = trajectory.get_data_by_key(DataKeys.OBS.JOINT.POS.LEFT)
        assert left_joint_pos.shape == (30, 7)

        right_joint_vel = trajectory.get_data_by_key(DataKeys.OBS.JOINT.VEL.RIGHT)
        assert right_joint_vel.shape == (30, 7)

        # Test gripper data from separate files
        left_gripper_pos = trajectory.get_data_by_key(DataKeys.OBS.GRIPPER.POS.LEFT)
        assert left_gripper_pos.shape == (30, 1)

        right_gripper_pos = trajectory.get_data_by_key(DataKeys.OBS.GRIPPER.POS.RIGHT)
        assert right_gripper_pos.shape == (30, 1)
