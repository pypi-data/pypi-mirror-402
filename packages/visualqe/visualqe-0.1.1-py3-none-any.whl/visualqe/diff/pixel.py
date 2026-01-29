"""Pixel-by-pixel image comparison algorithm."""

from typing import Optional

import numpy as np
from PIL import Image, ImageDraw

from visualqe.diff.base import DiffAlgorithm
from visualqe.exceptions import DiffError
from visualqe.models import DiffResult


class PixelDiff(DiffAlgorithm):
    """
    Pixel-by-pixel image comparison.

    Compares images by calculating the absolute difference between
    corresponding pixels. Supports configurable threshold and tolerance.
    """

    def __init__(
        self,
        threshold: float = 0.001,
        tolerance: int = 0,
        anti_aliasing_tolerance: int = 2,
    ):
        """
        Initialize pixel diff algorithm.

        Args:
            threshold: Minimum diff percentage to consider as changed (0.0-1.0).
            tolerance: Per-channel color tolerance (0-255).
            anti_aliasing_tolerance: Tolerance for anti-aliasing artifacts.
        """
        self.threshold = threshold
        self.tolerance = tolerance
        self.anti_aliasing_tolerance = anti_aliasing_tolerance

    @property
    def name(self) -> str:
        return "pixel"

    def compare(
        self,
        baseline: Image.Image,
        current: Image.Image,
        ignore_regions: Optional[list[tuple[int, int, int, int]]] = None,
    ) -> DiffResult:
        """
        Compare two images pixel by pixel.

        Args:
            baseline: The baseline/reference image.
            current: The current image to compare.
            ignore_regions: List of regions to ignore as (x1, y1, x2, y2) tuples.

        Returns:
            DiffResult containing comparison results.
        """
        try:
            # Ensure both images are in RGB mode
            baseline_rgb = baseline.convert("RGB")
            current_rgb = current.convert("RGB")

            # Resize current to match baseline if different sizes
            if baseline_rgb.size != current_rgb.size:
                current_rgb = current_rgb.resize(
                    baseline_rgb.size, Image.Resampling.LANCZOS
                )

            # Convert to numpy arrays
            baseline_arr = np.array(baseline_rgb, dtype=np.int16)
            current_arr = np.array(current_rgb, dtype=np.int16)

            # Calculate absolute difference
            diff_arr = np.abs(baseline_arr - current_arr)

            # Apply tolerance
            if self.tolerance > 0:
                diff_arr = np.where(
                    diff_arr <= self.tolerance,
                    0,
                    diff_arr - self.tolerance,
                )

            # Apply ignore regions
            mask = np.ones(baseline_arr.shape[:2], dtype=bool)
            if ignore_regions:
                for x1, y1, x2, y2 in ignore_regions:
                    # Clamp to image bounds
                    x1 = max(0, min(x1, baseline_arr.shape[1]))
                    x2 = max(0, min(x2, baseline_arr.shape[1]))
                    y1 = max(0, min(y1, baseline_arr.shape[0]))
                    y2 = max(0, min(y2, baseline_arr.shape[0]))
                    mask[y1:y2, x1:x2] = False

            # Apply mask
            masked_diff = diff_arr * mask[:, :, np.newaxis]

            # Detect anti-aliasing and reduce its impact
            if self.anti_aliasing_tolerance > 0:
                masked_diff = self._reduce_anti_aliasing(
                    masked_diff, self.anti_aliasing_tolerance
                )

            # Calculate diff percentage
            # A pixel is "changed" if any channel has a non-zero diff
            changed_pixels = np.any(masked_diff > 0, axis=2)
            total_pixels = mask.sum()  # Only count non-ignored pixels

            if total_pixels == 0:
                diff_percentage = 0.0
            else:
                diff_percentage = changed_pixels.sum() / total_pixels

            has_changes = diff_percentage > self.threshold

            # Generate diff image
            # Normalize and enhance for visibility
            diff_enhanced = np.clip(masked_diff * 3, 0, 255).astype(np.uint8)
            diff_image = Image.fromarray(diff_enhanced)

            # Generate highlight overlay
            highlight = self._create_highlight_overlay(
                baseline_rgb.size, changed_pixels
            )

            return DiffResult(
                has_changes=has_changes,
                diff_percentage=diff_percentage,
                diff_image=diff_image,
                highlight_overlay=highlight,
            )

        except Exception as e:
            raise DiffError(f"Pixel diff failed: {e}") from e

    def _reduce_anti_aliasing(
        self, diff_arr: np.ndarray, tolerance: int
    ) -> np.ndarray:
        """
        Reduce anti-aliasing artifacts in the diff.

        Anti-aliasing typically shows up as small differences at edges.
        This method identifies likely anti-aliasing and reduces its impact.
        """
        # Calculate the magnitude of change per pixel
        magnitude = np.sqrt(np.sum(diff_arr.astype(float) ** 2, axis=2))

        # Create a mask of small changes (likely anti-aliasing)
        small_changes = (magnitude > 0) & (magnitude < tolerance * 3)

        try:
            # Use scipy for more sophisticated anti-aliasing detection if available
            from scipy import ndimage

            # Dilate to find isolated pixels (not part of larger regions)
            dilated = ndimage.binary_dilation(small_changes, iterations=1)
            large_regions = ndimage.binary_erosion(dilated, iterations=2)

            # Isolated small changes are likely anti-aliasing
            anti_aliasing_mask = small_changes & ~large_regions
        except ImportError:
            # Fallback: simple threshold-based approach without morphological ops
            # Just remove very small isolated changes
            anti_aliasing_mask = small_changes & (magnitude < tolerance)

        # Zero out anti-aliasing pixels
        result = diff_arr.copy()
        result[anti_aliasing_mask] = 0

        return result

    def _create_highlight_overlay(
        self, size: tuple[int, int], changed_mask: np.ndarray
    ) -> Image.Image:
        """Create a red highlight overlay for changed regions."""
        overlay = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Find changed pixel coordinates
        coords = np.argwhere(changed_mask)

        # Draw semi-transparent red rectangles over changed regions
        # Group nearby pixels for efficiency
        if len(coords) > 0:
            # Sample for performance on large diffs
            sample_rate = max(1, len(coords) // 10000)
            for y, x in coords[::sample_rate]:
                draw.rectangle(
                    [x - 1, y - 1, x + 1, y + 1],
                    fill=(255, 0, 0, 100),
                )

        return overlay
