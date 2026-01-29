import numpy as np
import quaternion

from xdof_sdk.data.schema.types import Transform3D

TOL = 1e-7


def test_cycle_consistency():
    q = quaternion.from_rotation_vector([0.3, -0.7, 0.5])
    T = Transform3D(position=[0.4, -1.2, 2.0], quaternion_wxyz=[q.w, q.x, q.y, q.z])
    T_inv = Transform3D(matrix=np.linalg.inv(T.matrix))  # type: ignore
    I1 = (T @ T_inv).matrix
    I2 = (T_inv @ T).matrix
    assert np.allclose(I1, np.eye(4), atol=TOL)
    assert np.allclose(I2, np.eye(4), atol=TOL)


def test_translation_only():
    T1 = Transform3D(position=[1, 2, 3])
    T2 = Transform3D(position=[-4, 5, 0.5])
    T = T1 @ T2
    assert np.allclose(T.position, [-3, 7, 3.5], atol=TOL)
    assert np.allclose((T.matrix)[:3, :3], np.eye(3), atol=TOL)


def test_rotation_only():
    # Compose 90 deg and 45 deg rotations about Z → total 135 deg
    q1 = quaternion.from_rotation_matrix([[0, -1, 0], [1, 0, 0], [0, 0, 1]])  # 90 deg
    th = np.pi / 4  # 45 deg
    q2 = quaternion.from_rotation_matrix(
        [[np.cos(th), -np.sin(th), 0], [np.sin(th), np.cos(th), 0], [0, 0, 1]]
    )
    T = Transform3D(quaternion_wxyz=[q1.w, q1.x, q1.y, q1.z]) @ Transform3D(
        quaternion_wxyz=[q2.w, q2.x, q2.y, q2.z]
    )
    expected_R = [
        [-np.sqrt(2) / 2, -np.sqrt(2) / 2, 0],
        [np.sqrt(2) / 2, -np.sqrt(2) / 2, 0],
        [0, 0, 1],
    ]
    assert np.allclose((T.matrix)[:3, :3], expected_R, atol=TOL)
    assert np.allclose(T.position, [0, 0, 0], atol=TOL)


def test_rotation_and_translation():
    # T1: 90 deg about Z + translate [1,0,0]; T2: 90 deg about X + translate [0,1,0]
    qz = quaternion.from_rotation_matrix([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
    qx = quaternion.from_rotation_matrix([[1, 0, 0], [0, 0, -1], [0, 1, 0]])
    T1 = Transform3D(position=[1, 0, 0], quaternion_wxyz=[qz.w, qz.x, qz.y, qz.z])
    T2 = Transform3D(position=[0, 1, 0], quaternion_wxyz=[qx.w, qx.x, qx.y, qx.z])
    M_expected = T1.matrix @ T2.matrix
    assert np.allclose((T1 @ T2).matrix, M_expected, atol=TOL)
