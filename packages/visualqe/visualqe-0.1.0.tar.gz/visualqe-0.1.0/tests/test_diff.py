"""Tests for diff algorithms."""

import pytest
from PIL import Image

from visualqe.diff.pixel import PixelDiff
from visualqe.diff.ssim import SSIMDiff, CombinedDiff


class TestPixelDiff:
    """Tests for PixelDiff algorithm."""

    def test_identical_images(self, sample_image: Image.Image):
        """Test that identical images show no difference."""
        diff = PixelDiff(threshold=0.001)
        result = diff.compare(sample_image, sample_image.copy())

        assert result.has_changes is False
        assert result.diff_percentage == 0.0

    def test_different_images(
        self, sample_image: Image.Image, sample_image_modified: Image.Image
    ):
        """Test that different images are detected."""
        diff = PixelDiff(threshold=0.001)
        result = diff.compare(sample_image, sample_image_modified)

        assert result.has_changes is True
        assert result.diff_percentage > 0.0
        assert result.diff_image is not None

    def test_threshold_behavior(
        self, sample_image: Image.Image, sample_image_slightly_different: Image.Image
    ):
        """Test threshold configuration."""
        # High threshold - should pass
        diff_high = PixelDiff(threshold=0.1)
        result_high = diff_high.compare(sample_image, sample_image_slightly_different)

        # The slightly different image has very small changes
        # With high threshold, it should not detect changes
        assert result_high.diff_percentage < 0.1

    def test_tolerance(self, sample_image: Image.Image):
        """Test color tolerance."""
        # Create image with minor color variation
        modified = sample_image.copy()
        for x in range(50):
            for y in range(50):
                r, g, b = modified.getpixel((x, y))
                modified.putpixel((x, y), (min(255, r + 2), g, b))

        # Without tolerance - should detect changes
        diff_no_tolerance = PixelDiff(threshold=0.0, tolerance=0)
        result_no_tol = diff_no_tolerance.compare(sample_image, modified)

        # With tolerance - should ignore minor changes
        diff_with_tolerance = PixelDiff(threshold=0.0, tolerance=5)
        result_with_tol = diff_with_tolerance.compare(sample_image, modified)

        assert result_with_tol.diff_percentage < result_no_tol.diff_percentage

    def test_ignore_regions(self, sample_image: Image.Image):
        """Test ignore regions functionality."""
        # Create image with changes in specific region
        modified = sample_image.copy()
        for x in range(10, 30):
            for y in range(10, 30):
                modified.putpixel((x, y), (255, 0, 0))

        diff = PixelDiff(threshold=0.001)

        # Without ignore - should detect changes
        result_no_ignore = diff.compare(sample_image, modified)
        assert result_no_ignore.has_changes is True

        # With ignore region covering the change
        result_ignore = diff.compare(
            sample_image, modified, ignore_regions=[(10, 10, 30, 30)]
        )
        assert result_ignore.diff_percentage < result_no_ignore.diff_percentage

    def test_different_sizes_handled(self, sample_image: Image.Image):
        """Test that different image sizes are handled."""
        larger = Image.new("RGB", (200, 200), color="white")

        diff = PixelDiff()
        # Should not raise an error
        result = diff.compare(sample_image, larger)

        assert result is not None


class TestSSIMDiff:
    """Tests for SSIM diff algorithm."""

    def test_identical_images(self, sample_image: Image.Image):
        """Test SSIM with identical images."""
        diff = SSIMDiff(threshold=0.95)
        result = diff.compare(sample_image, sample_image.copy())

        assert result.has_changes is False
        assert result.similarity_score is not None
        assert result.similarity_score > 0.99

    def test_different_images(
        self, sample_image: Image.Image, sample_image_modified: Image.Image
    ):
        """Test SSIM detects different images."""
        diff = SSIMDiff(threshold=0.95)
        result = diff.compare(sample_image, sample_image_modified)

        assert result.has_changes is True
        assert result.similarity_score is not None
        assert result.similarity_score < 0.95

    def test_threshold_configuration(self, sample_image: Image.Image):
        """Test SSIM threshold behavior."""
        modified = sample_image.copy()
        # Make small changes
        for x in range(10):
            for y in range(10):
                modified.putpixel((x, y), (128, 128, 128))

        # Low threshold (strict)
        diff_strict = SSIMDiff(threshold=0.999)
        result_strict = diff_strict.compare(sample_image, modified)

        # High threshold (lenient)
        diff_lenient = SSIMDiff(threshold=0.5)
        result_lenient = diff_lenient.compare(sample_image, modified)

        # Same underlying score, different has_changes based on threshold
        assert result_strict.similarity_score == result_lenient.similarity_score

    def test_diff_image_generated(
        self, sample_image: Image.Image, sample_image_modified: Image.Image
    ):
        """Test that SSIM generates a diff image."""
        diff = SSIMDiff()
        result = diff.compare(sample_image, sample_image_modified)

        assert result.diff_image is not None
        assert isinstance(result.diff_image, Image.Image)


class TestCombinedDiff:
    """Tests for combined SSIM + Pixel diff."""

    def test_uses_ssim_for_detection(
        self, sample_image: Image.Image, sample_image_modified: Image.Image
    ):
        """Test that combined diff uses SSIM for change detection."""
        diff = CombinedDiff(ssim_threshold=0.95)
        result = diff.compare(sample_image, sample_image_modified)

        # Should have SSIM similarity score
        assert result.similarity_score is not None

    def test_provides_pixel_visualization(
        self, sample_image: Image.Image, sample_image_modified: Image.Image
    ):
        """Test that combined diff provides pixel-based visualization."""
        diff = CombinedDiff()
        result = diff.compare(sample_image, sample_image_modified)

        # Should have diff image
        assert result.diff_image is not None
