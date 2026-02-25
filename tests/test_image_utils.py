"""Unit tests for nmutils.utils.image_utils."""

import numpy as np
import pytest

from nmutils.utils.image_utils import (
    poisson,
    smoothImage,
    noisyImage,
    biggestBlob,
    binPixels,
    fastBinPixels,
    gaussian2D,
    circle,
    pseudoCircle,
)


# gaussian2D
class TestGaussian2D:
    def test_shape(self):
        g = gaussian2D(11, sigma=2.0)
        assert g.shape == (11, 11)

    def test_all_positive(self):
        g = gaussian2D(11, sigma=2.0)
        assert np.all(g >= 0)

    def test_symmetric(self):
        g = gaussian2D(11, sigma=2.0)
        np.testing.assert_array_almost_equal(g, g.T)

    def test_peak_at_center(self):
        n = 11
        g = gaussian2D(n, sigma=2.0)
        center = n // 2
        assert g[center, center] == g.max()

    def test_odd_and_even_sizes(self):
        for n in (5, 6, 9, 10):
            g = gaussian2D(n, sigma=1.5)
            assert g.shape == (n, n)

    def test_narrower_sigma_higher_peak(self):
        g_narrow = gaussian2D(11, sigma=1.0)
        g_wide = gaussian2D(11, sigma=3.0)
        assert g_narrow.max() > g_wide.max()


# circle
class TestCircle:
    def test_shape(self):
        c = circle(10)
        assert c.shape == (10, 10)

    def test_center_is_one(self):
        n = 11
        c = circle(n)
        center = n // 2
        assert c[center, center] == 1.0

    def test_corner_is_zero(self):
        c = circle(20)
        assert c[0, 0] == 0.0

    def test_small_radius_mostly_zeros(self):
        c = circle(20, radius=1)
        # Very small radius; almost all pixels should be 0
        assert c.sum() < 10

    def test_default_dtype_float(self):
        c = circle(10)
        assert c.dtype.kind == "f"

    def test_int_dtype(self):
        c = circle(10, dtype="int")
        assert c.dtype.kind == "i"


# pseudoCircle
class TestPseudoCircle:
    def test_shape(self):
        p = pseudoCircle(10)
        assert p.shape == (10, 10)

    def test_center_is_one(self):
        n = 11
        p = pseudoCircle(n)
        center = n // 2
        assert p[center, center] == 1.0

    def test_high_exponent_approaches_square(self):
        """With a very high exponent the pseudoCircle approaches a square."""
        n = 21
        p = pseudoCircle(n, exponent=20)
        c = circle(n)
        # pseudoCircle with high exponent should cover more pixels than a real circle
        assert p.sum() >= c.sum()

    def test_exponent1_rhomb(self):
        """exponent=1 gives a rhombus (rotated square)."""
        n = 21
        p = pseudoCircle(n, exponent=1)
        # corners should be zero
        assert p[0, 0] == 0.0


# binPixels
class TestBinPixels:
    def test_shape_halved(self):
        img = np.ones((8, 8))
        result = binPixels(img, n=2)
        assert result.shape == (4, 4)

    def test_shape_quartered(self):
        img = np.ones((8, 8))
        result = binPixels(img, n=4)
        assert result.shape == (2, 2)

    def test_uniform_input(self):
        img = np.full((8, 8), 4.0)
        result = binPixels(img, n=2)
        np.testing.assert_array_almost_equal(result, np.full((4, 4), 4.0))

    def test_integer_rounding(self):
        img = np.ones((4, 4), dtype=np.uint8)
        result = binPixels(img, n=2)
        assert result.dtype == np.uint8
        np.testing.assert_array_equal(result, np.ones((2, 2), dtype=np.uint8))

    def test_odd_pixels_discarded(self):
        """Pixels that don't fit into a complete bin are silently discarded."""
        img = np.ones((9, 9))
        result = binPixels(img, n=2)
        assert result.shape == (4, 4)


# fastBinPixels
class TestFastBinPixels:
    def test_shape_halved(self):
        img = np.ones((8, 8))
        result = fastBinPixels(img, n=2)
        assert result.shape == (4, 4)

    def test_uniform_input(self):
        """fastBinPixels sums (not averages) within each bin."""
        img = np.full((8, 8), 1.0)
        result = fastBinPixels(img, n=2)
        np.testing.assert_array_almost_equal(result, np.full((4, 4), 4.0))

    def test_consistent_with_binPixels_sum(self):
        """fastBinPixels sum == binPixels mean * n^2 for uniform arrays."""
        rng = np.random.default_rng(0)
        img = rng.random((8, 8))
        fast = fastBinPixels(img, n=2)
        slow_mean = binPixels(img, n=2)
        # fastBinPixels returns sums, binPixels returns means
        np.testing.assert_array_almost_equal(fast, slow_mean * 4)


# biggestBlob
class TestBiggestBlob:
    def test_returns_biggest(self):
        img = np.zeros((10, 10))
        img[1:4, 1:4] = 1   # 9-pixel blob
        img[7:9, 7:9] = 1   # 4-pixel blob
        result = biggestBlob(img)
        # The result should contain only the 9-pixel blob
        assert result[2, 2] == 1
        assert result[8, 8] == 0

    def test_all_zeros_returns_zero(self):
        """All-zeros input has no blobs; should return an all-False/zero array."""
        img = np.zeros((5, 5))
        result = biggestBlob(img)
        assert result.sum() == 0
        assert result.shape == img.shape

    def test_single_blob(self):
        img = np.zeros((8, 8))
        img[3:5, 3:5] = 1
        result = biggestBlob(img)
        assert result.sum() == img.sum()

    def test_output_is_binary(self):
        img = np.zeros((10, 10))
        img[2:5, 2:5] = 3.0
        result = biggestBlob(img)
        assert set(np.unique(result)) <= {0, 1, True, False}


# smoothImage
class TestSmoothImage:
    def test_shape_preserved(self):
        img = np.random.rand(20, 20)
        result = smoothImage(img, sigma=2)
        assert result.shape == img.shape

    def test_does_not_modify_input(self):
        img = np.random.rand(20, 20)
        original = img.copy()
        smoothImage(img, sigma=2)
        np.testing.assert_array_equal(img, original)

    def test_uniform_image_stays_uniform(self):
        """A uniform image stays spatially uniform after smoothing (absolute value may shift due to normalization)."""
        img = np.full((20, 20), 5.0)
        result = smoothImage(img, sigma=2)
        interior = result[5:-5, 5:-5]
        # All interior values should be identical to each other
        assert interior.max() - interior.min() == pytest.approx(0.0, abs=1e-10)

    def test_smoothing_reduces_peak(self):
        """A spike image should have a reduced peak after smoothing."""
        img = np.zeros((21, 21))
        img[10, 10] = 1.0
        result = smoothImage(img, sigma=2)
        assert result.max() < img.max()

    def test_sigma_1_less_smooth_than_sigma_3(self):
        img = np.zeros((21, 21))
        img[10, 10] = 1.0
        r1 = smoothImage(img, sigma=1)
        r3 = smoothImage(img, sigma=3)
        # With larger sigma the peak is more spread out (lower peak)
        assert r1.max() > r3.max()


# poisson
class TestPoisson:
    def test_scalar_k(self):
        p = poisson(5.0, 5)
        assert isinstance(p, float)
        assert 0 < p <= 1

    def test_k_zero_mean_one(self):
        """P(k=0 | mean=1) = e^-1 ≈ 0.368."""
        p = poisson(1.0, 0)
        assert p == pytest.approx(np.exp(-1.0), rel=1e-6)

    def test_array_k(self):
        ks = [0, 1, 2, 3]
        result = poisson(2.0, ks)
        assert isinstance(result, np.ndarray)
        assert result.shape == (4,)
        assert np.all(result >= 0)

    def test_array_sums_to_approx_one(self):
        """Sum over a wide range of k should approach 1."""
        mean = 3.0
        ks = list(range(20))
        result = poisson(mean, ks)
        assert result.sum() == pytest.approx(1.0, abs=1e-4)


# noisyImage
class TestNoisyImage:
    def test_shape_preserved(self):
        rng = np.random.default_rng(4)
        img = rng.random((10, 10)) + 0.1
        result = noisyImage(img, photonsPerPixel=100)
        assert result.shape == img.shape

    def test_non_negative_output(self):
        rng = np.random.default_rng(5)
        img = rng.random((10, 10)) + 0.1
        result = noisyImage(img, photonsPerPixel=100)
        assert np.all(result >= 0)

    def test_ambiguous_args_raises(self):
        img = np.ones((5, 5))
        with pytest.raises(ValueError):
            noisyImage(img, photonsPerPixel=100, photonsAtMax=200)

    def test_no_args_raises(self):
        img = np.ones((5, 5))
        with pytest.raises((ValueError, TypeError)):
            noisyImage(img)

    def test_dtype_preserved(self):
        img = np.ones((5, 5), dtype=np.float32)
        result = noisyImage(img, photonsPerPixel=10)
        assert result.dtype == img.dtype
