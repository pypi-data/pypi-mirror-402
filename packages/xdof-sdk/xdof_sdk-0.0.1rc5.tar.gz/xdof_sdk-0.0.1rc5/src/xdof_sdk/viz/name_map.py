"""Visualization-friendly names for DataKeys (dash-separated for rerun entity paths)."""

from xdof_sdk.data.schema.keys import DataKeys

# Map DataKeys to human-readable names for visualization
DATA_KEY_NAMES = {
    # Action keys
    DataKeys.ACTION.JOINT.POS.LEFT: "left-arm-joint-pos-action",
    DataKeys.ACTION.JOINT.POS.RIGHT: "right-arm-joint-pos-action",
    DataKeys.ACTION.GRIPPER.POS.LEFT: "left-gripper-pos-action",
    DataKeys.ACTION.GRIPPER.POS.RIGHT: "right-gripper-pos-action",
    DataKeys.ACTION.EE_POSE.LEFT: "left-ee-pose-action",
    DataKeys.ACTION.EE_POSE.RIGHT: "right-ee-pose-action",
    DataKeys.ACTION.EE_POSE.HEAD: "head-pose-action",
    # Observation keys - Joint
    DataKeys.OBS.JOINT.POS.LEFT: "left-arm-joint-pos-obs",
    DataKeys.OBS.JOINT.POS.RIGHT: "right-arm-joint-pos-obs",
    DataKeys.OBS.JOINT.VEL.LEFT: "left-arm-joint-vel-obs",
    DataKeys.OBS.JOINT.VEL.RIGHT: "right-arm-joint-vel-obs",
    DataKeys.OBS.JOINT.EFFORT.LEFT: "left-arm-joint-effort-obs",
    DataKeys.OBS.JOINT.EFFORT.RIGHT: "right-arm-joint-effort-obs",
    DataKeys.OBS.JOINT.POSE.LEFT: "left-ee-pose-obs",
    DataKeys.OBS.JOINT.POSE.RIGHT: "right-ee-pose-obs",
    # Observation keys - Gripper
    DataKeys.OBS.GRIPPER.POS.LEFT: "left-gripper-pos-obs",
    DataKeys.OBS.GRIPPER.POS.RIGHT: "right-gripper-pos-obs",
    # Observation keys - Force/Speed/Detection
    DataKeys.OBS.FORCE.LEFT: "left-arm-force-obs",
    DataKeys.OBS.FORCE.RIGHT: "right-arm-force-obs",
    DataKeys.OBS.SPEED.LEFT: "left-arm-speed-obs",
    DataKeys.OBS.SPEED.RIGHT: "right-arm-speed-obs",
    DataKeys.OBS.OBJECT_DETECTED.LEFT: "left-object-detected-obs",
    DataKeys.OBS.OBJECT_DETECTED.RIGHT: "right-object-detected-obs",
    # Camera keys
    DataKeys.CAMERA.IMAGES.TOP: "top-camera-image",
    DataKeys.CAMERA.IMAGES.TOP_LEFT: "top-left-camera-image",
    DataKeys.CAMERA.IMAGES.TOP_RIGHT: "top-right-camera-image",
    DataKeys.CAMERA.IMAGES.LEFT: "left-camera-image",
    DataKeys.CAMERA.IMAGES.RIGHT: "right-camera-image",
    DataKeys.CAMERA.TIMESTAMP.TOP: "top-camera-timestamp",
    DataKeys.CAMERA.TIMESTAMP.LEFT: "left-camera-timestamp",
    DataKeys.CAMERA.TIMESTAMP.RIGHT: "right-camera-timestamp",
    # Trajectory keys
    DataKeys.TRAJECTORY.GLOBAL_TIMESTAMP: "global-timestamp",
    DataKeys.TRAJECTORY.METADATA: "trajectory-metadata",
    DataKeys.TRAJECTORY.ANNOTATIONS: "video-annotations",
}


def get_viz_name(key: str) -> str:
    """Get visualization-friendly name for a data key (dash-separated), fallback to the key itself."""
    return DATA_KEY_NAMES.get(key, key)
