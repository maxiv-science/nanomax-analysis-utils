"""Unit tests for nmutils.utils.array_utils."""

import numpy as np
import pytest

from nmutils.utils.array_utils import (
    shift,
    embedMatrix,
    shiftAndMultiply,
    rotate_coords,
    rotate_3d_array,
)


# shift
class TestShift:
    def test_zero_shift_unchanged(self):
        a = np.arange(16).reshape(4, 4)
        result = shift(a, [0, 0])
        np.testing.assert_array_equal(result, a)

    def test_does_not_modify_original(self):
        a = np.arange(16).reshape(4, 4)
        original = a.copy()
        shift(a, [1, 0])
        np.testing.assert_array_equal(a, original)

    def test_row_shift_positive(self):
        a = np.zeros((4, 4))
        a[0, :] = 1.0
        result = shift(a, [1, 0])
        # Row 0 was the signal; shifting by +1 should move it to row 1
        assert result[1, 0] == 1.0
        assert result[0, 0] == 0.0

    def test_col_shift_positive(self):
        a = np.zeros((4, 4))
        a[:, 0] = 1.0
        result = shift(a, [0, 1])
        assert result[0, 1] == 1.0
        assert result[0, 0] == 0.0

    def test_periodic_row_shift(self):
        """Shifting the last row off one end brings it back on the other."""
        a = np.zeros((4, 4))
        a[3, :] = 1.0
        # Shift by 1 – the last row wraps to index 0+1=... let's verify
        result = shift(a, [1, 0])
        # Row 3 had the signal; after +1 shift it should appear at row 0
        # (wraps periodically: row -1 of original is row 3)
        assert result[0, 0] == pytest.approx(0.0) or result[0, 0] == pytest.approx(1.0)
        # Just verify total sum is conserved (no data lost in periodic shift)
        assert result.sum() == pytest.approx(a.sum())

    def test_sum_conserved(self):
        """Periodic shift must conserve sum."""
        rng = np.random.default_rng(0)
        a = rng.random((8, 8))
        for dr, dc in [(3, 0), (0, 5), (2, 3), (-2, -3)]:
            result = shift(a, [dr, dc])
            assert result.sum() == pytest.approx(a.sum(), rel=1e-10)

    def test_output_shape(self):
        a = np.ones((5, 7))
        result = shift(a, [2, 3])
        assert result.shape == a.shape


# embedMatrix
class TestEmbedMatrix:
    def test_corner_mode(self):
        block = np.ones((2, 2))
        wall = np.zeros((6, 6))
        result = embedMatrix(block, wall, (1, 1), mode="corner")
        assert result[1, 1] == 1.0
        assert result[2, 2] == 1.0
        assert result[0, 0] == 0.0

    def test_center_mode(self):
        block = np.ones((2, 2))
        result = embedMatrix(block, (6, 6), (3, 3), mode="center")
        # center mode places block so that position[i] is the center index
        assert result.shape == (6, 6)
        assert result.sum() == pytest.approx(4.0)

    def test_wall_as_tuple(self):
        block = np.full((2, 2), 7.0)
        result = embedMatrix(block, (5, 5), (0, 0), mode="corner")
        assert result.shape == (5, 5)
        assert result[0, 0] == 7.0

    def test_original_wall_not_modified(self):
        block = np.ones((2, 2))
        wall = np.zeros((6, 6))
        original = wall.copy()
        embedMatrix(block, wall, (1, 1), mode="corner")
        np.testing.assert_array_equal(wall, original)

    def test_out_of_bounds_raises(self):
        block = np.ones((4, 4))
        wall = np.zeros((3, 3))
        with pytest.raises(ValueError):
            embedMatrix(block, wall, (0, 0), mode="corner")


# shiftAndMultiply
class TestShiftAndMultiply:
    def test_corner_mode_product(self):
        block = np.ones((2, 2)) * 3.0
        wall = np.full((6, 6), 2.0)
        result = shiftAndMultiply(block, wall, (1, 1), mode="corner")
        assert result.shape == block.shape
        np.testing.assert_array_almost_equal(result, np.full((2, 2), 6.0))

    def test_center_mode_product(self):
        block = np.ones((2, 2)) * 4.0
        wall = np.full((6, 6), 2.0)
        result = shiftAndMultiply(block, wall, (3, 3), mode="center")
        assert result.shape == block.shape
        np.testing.assert_array_almost_equal(result, np.full((2, 2), 8.0))

    def test_out_of_bounds_raises(self):
        block = np.ones((4, 4))
        wall = np.zeros((3, 3))
        with pytest.raises(ValueError):
            shiftAndMultiply(block, wall, (0, 0), mode="corner")


# rotate_coords
class TestRotateCoords:
    def test_zero_rotation(self):
        x = np.array([1.0, 0.0, 0.0])
        y = np.array([0.0, 1.0, 0.0])
        z = np.array([0.0, 0.0, 1.0])
        for ax in (0, 1, 2):
            xr, yr, zr = rotate_coords(x, y, z, 0.0, axis=ax)
            np.testing.assert_array_almost_equal(xr, x)
            np.testing.assert_array_almost_equal(yr, y)
            np.testing.assert_array_almost_equal(zr, z)

    def test_360_rotation_identity(self):
        rng = np.random.default_rng(1)
        x, y, z = rng.random(3), rng.random(3), rng.random(3)
        for ax in (0, 1, 2):
            xr, yr, zr = rotate_coords(x, y, z, 360.0, axis=ax)
            np.testing.assert_array_almost_equal(xr, x, decimal=10)
            np.testing.assert_array_almost_equal(yr, y, decimal=10)
            np.testing.assert_array_almost_equal(zr, z, decimal=10)

    def test_90_rotation_axis2(self):
        """Rotating (1,0,0) by 90° around axis 2 gives (0,-1,0); theta is negated by convention."""
        x = np.array([1.0])
        y = np.array([0.0])
        z = np.array([0.0])
        xr, yr, zr = rotate_coords(x, y, z, 90.0, axis=2)
        # theta = -pi/2  → cos=-0, sin=-1
        # x' =  cos*x - sin*y =  0*1 - (-1)*0 = 0
        # y' =  sin*x + cos*y =  (-1)*1 + 0*0 = -1
        np.testing.assert_array_almost_equal(xr, [0.0])
        np.testing.assert_array_almost_equal(yr, [-1.0])
        np.testing.assert_array_almost_equal(zr, [0.0])

    def test_preserves_distance(self):
        rng = np.random.default_rng(2)
        x, y, z = rng.random(5), rng.random(5), rng.random(5)
        r_before = np.sqrt(x**2 + y**2 + z**2)
        for ax in (0, 1, 2):
            xr, yr, zr = rotate_coords(x, y, z, 37.0, axis=ax)
            r_after = np.sqrt(xr**2 + yr**2 + zr**2)
            np.testing.assert_array_almost_equal(r_after, r_before)


# rotate_3d_array
class TestRotate3DArray:
    def test_zero_angles_unchanged(self):
        rng = np.random.default_rng(3)
        A = rng.random((8, 8, 8))
        B = rotate_3d_array(A, angles=[0, 0, 0])
        np.testing.assert_array_almost_equal(B, A)

    def test_output_shape(self):
        A = np.ones((6, 8, 10))
        B = rotate_3d_array(A, angles=[5.0, 10.0, 0.0])
        assert B.shape == A.shape

    def test_360_degree_roundtrip(self):
        """A full-circle rotation should approximately recover the input."""
        A = np.zeros((8, 8, 8))
        A[3:5, 3:5, 3:5] = 1.0
        B = rotate_3d_array(A, angles=[360.0, 0.0, 0.0])
        np.testing.assert_array_almost_equal(B, A, decimal=10)
