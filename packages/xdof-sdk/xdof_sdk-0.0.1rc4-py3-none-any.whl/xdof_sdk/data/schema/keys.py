class DataKeys:
    class ACTION:
        class JOINT:
            class POS:
                LEFT = "action-left-pos"
                RIGHT = "action-right-pos"

        class GRIPPER:
            class POS:
                LEFT = "action-left-gripper_pos"
                RIGHT = "action-right-gripper_pos"

        class EE_POSE:
            LEFT = "action-left-pose"
            RIGHT = "action-right-pose"
            HEAD = "action-head-pose"
            LEFT_HEAD = "action-left-head"
            # Kind of unused... but keeping for compatibility.
            RIGHT_HEAD = "action-right-head"

    class OBS:
        class JOINT:
            class POS:
                LEFT = "left-joint_pos"
                RIGHT = "right-joint_pos"

            class VEL:
                LEFT = "left-joint_vel"
                RIGHT = "right-joint_vel"

            class EFFORT:
                LEFT = "left-joint_eff"
                RIGHT = "right-joint_eff"

            class POSE:  # EE pose observations
                LEFT = "left-joint_pose"
                RIGHT = "right-joint_pose"

        class GRIPPER:
            class POS:
                LEFT = "left-gripper_pos"
                RIGHT = "right-gripper_pos"

        class FORCE:
            LEFT = "left-force"
            RIGHT = "right-force"

        class SPEED:
            LEFT = "left-speed"
            RIGHT = "right-speed"

        class OBJECT_DETECTED:
            LEFT = "left-object_detected"
            RIGHT = "right-object_detected"

    class CAMERA:
        class IMAGES:
            TOP = "top_camera-images-rgb"
            # we might have stereo camera, so we need to have left and right camera images when concat_image=False
            TOP_LEFT = "top_camera-images-left_rgb"
            TOP_RIGHT = "top_camera-images-right_rgb"
            RIGHT = "right_camera-images-rgb"
            LEFT = "left_camera-images-rgb"
            SECONDARY_TOP = "secondary_top_camera-images-rgb"

        class TIMESTAMP:
            TOP = "top_camera-timestamp"
            RIGHT = "right_camera-timestamp"
            LEFT = "left_camera-timestamp"
            SECONDARY_TOP = "secondary_top_camera-timestamp"

    class TRAJECTORY:
        GLOBAL_TIMESTAMP = "timestamp"
        METADATA = "metadata.json"
        ANNOTATIONS = "top_camera-images-rgb_annotation.json"
        LOW_RES_VIDEO = "top_camera-images-rgb_low_res.mp4"  # if top camera is stereo camera use left_rgb by default.


# Create the camera to timestamp mapping
CAMERA_TO_TIMESTAMP_KEY = {
    DataKeys.CAMERA.IMAGES.TOP: DataKeys.CAMERA.TIMESTAMP.TOP,
    DataKeys.CAMERA.IMAGES.TOP_LEFT: DataKeys.CAMERA.TIMESTAMP.TOP,
    DataKeys.CAMERA.IMAGES.TOP_RIGHT: DataKeys.CAMERA.TIMESTAMP.TOP,
    DataKeys.CAMERA.IMAGES.RIGHT: DataKeys.CAMERA.TIMESTAMP.RIGHT,
    DataKeys.CAMERA.IMAGES.LEFT: DataKeys.CAMERA.TIMESTAMP.LEFT,
    DataKeys.CAMERA.IMAGES.SECONDARY_TOP: DataKeys.CAMERA.TIMESTAMP.SECONDARY_TOP,
}

MCAP_TOPIC_FIELD_TO_KEY = {
    "/left-robot-state": {
        "position": DataKeys.OBS.JOINT.POS.LEFT,
        "velocity": DataKeys.OBS.JOINT.VEL.LEFT,
        "torque": DataKeys.OBS.JOINT.EFFORT.LEFT,
        "pose": DataKeys.OBS.JOINT.POSE.LEFT,
    },
    "/right-robot-state": {
        "position": DataKeys.OBS.JOINT.POS.RIGHT,
        "velocity": DataKeys.OBS.JOINT.VEL.RIGHT,
        "torque": DataKeys.OBS.JOINT.EFFORT.RIGHT,
        "pose": DataKeys.OBS.JOINT.POSE.RIGHT,
    },
    "/action-left-robot-state": {
        "position": DataKeys.ACTION.JOINT.POS.LEFT,
        "pose": DataKeys.ACTION.EE_POSE.LEFT,
    },
    "/action-right-robot-state": {
        "position": DataKeys.ACTION.JOINT.POS.RIGHT,
        "pose": DataKeys.ACTION.EE_POSE.RIGHT,
    },
    "/left-gripper-state": {
        "position": DataKeys.OBS.GRIPPER.POS.LEFT,
    },
    "/right-gripper-state": {
        "position": DataKeys.OBS.GRIPPER.POS.RIGHT,
    },
    "/action-left-gripper-state": {
        "position": DataKeys.ACTION.GRIPPER.POS.LEFT,
    },
    "/action-right-gripper-state": {
        "position": DataKeys.ACTION.GRIPPER.POS.RIGHT,
    },
    "/action-left-head-robot-state": {
        "pose": DataKeys.ACTION.EE_POSE.LEFT_HEAD,
    },
    "/action-right-head-robot-state": {
        "pose": DataKeys.ACTION.EE_POSE.RIGHT_HEAD,
    },
}

# If it's a camera image key, return .mp4 instead of .npy
_camera_image_keys = [
    getattr(DataKeys.CAMERA.IMAGES, attr)
    for attr in dir(DataKeys.CAMERA.IMAGES)
    if not attr.startswith("_")
]


def key_filename(key: str) -> str:
    if key.endswith((".mp4", ".npy", ".json", ".mcap")):
        return str(key)

    if key in _camera_image_keys:
        return str(key) + ".mp4"
    return str(key) + ".npy"
