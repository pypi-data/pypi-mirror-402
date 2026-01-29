import numpy as np
import pytest
from pydantic import ValidationError

from xdof_sdk.data.schema.types import LengthUnit, Transform3D


def test_transform3d_legacy_json():
    """Tests that we deserialize the transform3d correctly from json."""
    old_json = """
    {
        "position": [-0.00186023478, -0.797904739, 0.0026400628],
        "rotation": [0.70710678, 0, 0.70710678, 0]
    }
    """

    transform = Transform3D.model_validate_json(old_json)
    assert transform.matrix.shape == (4, 4)
    assert transform.units == LengthUnit.M
    assert transform.position == [-0.00186023478, -0.797904739, 0.0026400628]
    assert np.allclose(transform.quaternion_wxyz, [0.70710678, 0, 0.70710678, 0])
    assert np.allclose(
        transform.matrix[:3, 3], [-0.00186023478, -0.797904739, 0.0026400628]
    )

    # Check that we go to new naming convention
    assert transform.model_dump() == {
        "position": transform.position,
        "quaternion_wxyz": transform.quaternion_wxyz,
    }

    t = Transform3D(
        position=[-0.00186023478, -0.797904739, 0.0026400628],
        quaternion_wxyz=[0.70710678, 0, 0.70710678, 0],
    )
    assert t == transform


def test_transform3d_quat_json():
    """Tests that we deserialize the transform3d correctly from json."""
    transform_json = """
    {
        "position": [120.0, 0.0, 0.0],
        "quaternion_wxyz": [0.70710678, 0, 0.70710678, 0],
        "units": "mm"
    }
    """

    transform = Transform3D.model_validate_json(transform_json)
    assert transform.matrix.shape == (4, 4)
    assert transform.units == LengthUnit.M
    assert transform.position == [0.120, 0.0, 0.0]
    assert np.allclose(transform.quaternion_wxyz, [0.70710678, 0, 0.70710678, 0])
    assert np.allclose(transform.matrix[:3, 3], [0.120, 0.0, 0.0])

    assert transform.model_dump() == {
        "position": [0.120, 0.0, 0.0],
        "quaternion_wxyz": transform.quaternion_wxyz,
    }

    t = Transform3D(
        position=[120.0, 0.0, 0.0],
        quaternion_wxyz=[0.70710678, 0, 0.70710678, 0],
        units=LengthUnit.MM,
    )
    assert t == transform


def test_transform3d_matrix_json():
    """Tests that we deserialize the transform3d correctly from a legacy dict."""
    transform_json = """
    {
        "matrix": [[1.0, 0.0, 0.0, 120.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]],
        "units": "cm"
    }
    """

    transform = Transform3D.model_validate_json(transform_json)
    assert transform.matrix.shape == (4, 4)
    assert transform.units == LengthUnit.M
    assert transform.position == [1.2, 0.0, 0.0]
    assert np.allclose(transform.quaternion_wxyz, [1.0, 0, 0, 0])

    assert transform.model_dump() == {
        "matrix": transform.matrix.tolist(),
    }

    t = Transform3D(
        matrix=np.array(
            [
                [1.0, 0.0, 0.0, 120.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        ),
        units=LengthUnit.CM,
    )
    assert t == transform


def test_raises_validator_error_matrix():
    with pytest.raises(ValidationError):
        Transform3D(
            matrix=np.array(
                [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0]]
            ),
        )
