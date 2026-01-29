"""Structural Similarity Index (SSIM) image comparison algorithm."""

from typing import Optional

import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity

from visualqe.diff.base import DiffAlgorithm
from visualqe.exceptions import DiffError
from visualqe.models import DiffResult


class SSIMDiff(DiffAlgorithm):
    """
    Structural Similarity Index (SSIM) based comparison.

    SSIM is a perceptual metric that considers changes in structural
    information, luminance, and contrast. It's more aligned with human
    perception than pixel-by-pixel comparison.
    """

    def __init__(
        self,
        threshold: float = 0.95,
        win_size: int = 7,
        multichannel: bool = True,
    ):
        """
        Initialize SSIM diff algorithm.

        Args:
            threshold: SSIM score below which images are considered different.
                      1.0 = identical, 0.0 = completely different.
            win_size: Size of the sliding window for SSIM calculation.
            multichannel: Whether to compute SSIM across color channels.
        """
        self.threshold = threshold
        self.win_size = win_size
        self.multichannel = multichannel

    @property
    def name(self) -> str:
        return "ssim"

    def compare(
        self,
        baseline: Image.Image,
        current: Image.Image,
        ignore_regions: Optional[list[tuple[int, int, int, int]]] = None,
    ) -> DiffResult:
        """
        Compare two images using SSIM.

        Args:
            baseline: The baseline/reference image.
            current: The current image to compare.
            ignore_regions: List of regions to ignore as (x1, y1, x2, y2) tuples.

        Returns:
            DiffResult containing comparison results.
        """
        try:
            # Convert to RGB
            baseline_rgb = baseline.convert("RGB")
            current_rgb = current.convert("RGB")

            # Resize current to match baseline if different sizes
            if baseline_rgb.size != current_rgb.size:
                current_rgb = current_rgb.resize(
                    baseline_rgb.size, Image.Resampling.LANCZOS
                )

            # Convert to numpy arrays
            baseline_arr = np.array(baseline_rgb)
            current_arr = np.array(current_rgb)

            # Apply ignore regions by setting them to identical values
            if ignore_regions:
                for x1, y1, x2, y2 in ignore_regions:
                    x1 = max(0, min(x1, baseline_arr.shape[1]))
                    x2 = max(0, min(x2, baseline_arr.shape[1]))
                    y1 = max(0, min(y1, baseline_arr.shape[0]))
                    y2 = max(0, min(y2, baseline_arr.shape[0]))
                    # Set both to baseline values in ignored regions
                    current_arr[y1:y2, x1:x2] = baseline_arr[y1:y2, x1:x2]

            # Ensure win_size is odd and not larger than image dimensions
            min_dim = min(baseline_arr.shape[0], baseline_arr.shape[1])
            win_size = min(self.win_size, min_dim)
            if win_size % 2 == 0:
                win_size -= 1
            win_size = max(3, win_size)

            # Calculate SSIM
            if self.multichannel:
                score, diff_map = structural_similarity(
                    baseline_arr,
                    current_arr,
                    full=True,
                    channel_axis=2,
                    win_size=win_size,
                    data_range=255,
                )
                # Average diff map across channels
                diff_map = np.mean(diff_map, axis=2)
            else:
                # Convert to grayscale
                baseline_gray = np.array(baseline.convert("L"))
                current_gray = np.array(current.convert("L"))

                if baseline_gray.shape != current_gray.shape:
                    current_gray = np.array(
                        current.convert("L").resize(baseline.size)
                    )

                score, diff_map = structural_similarity(
                    baseline_gray,
                    current_gray,
                    full=True,
                    win_size=win_size,
                    data_range=255,
                )

            # Convert SSIM score to diff percentage
            # SSIM of 1.0 = 0% diff, SSIM of 0.0 = 100% diff
            diff_percentage = 1.0 - score

            has_changes = score < self.threshold

            # Create diff image from SSIM diff map
            # Invert so that differences are bright
            diff_visual = ((1 - diff_map) * 255).astype(np.uint8)
            diff_image = Image.fromarray(diff_visual)

            # Create colored diff image for better visibility
            diff_colored = self._create_colored_diff(diff_map)

            return DiffResult(
                has_changes=has_changes,
                diff_percentage=diff_percentage,
                diff_image=diff_colored,
                highlight_overlay=None,
                similarity_score=score,
            )

        except Exception as e:
            raise DiffError(f"SSIM diff failed: {e}") from e

    def _create_colored_diff(self, diff_map: np.ndarray) -> Image.Image:
        """
        Create a colored diff visualization.

        Uses a heat map: green (similar) -> yellow -> red (different).
        """
        # Invert so high values = more difference
        diff_values = 1 - diff_map

        # Create RGB image
        height, width = diff_values.shape
        colored = np.zeros((height, width, 3), dtype=np.uint8)

        # Green for similar (low diff)
        # Red for different (high diff)
        # Yellow for medium

        colored[:, :, 0] = np.clip(diff_values * 510, 0, 255).astype(np.uint8)  # Red
        colored[:, :, 1] = np.clip((1 - diff_values) * 510, 0, 255).astype(
            np.uint8
        )  # Green
        colored[:, :, 2] = 0  # Blue

        return Image.fromarray(colored)


class CombinedDiff(DiffAlgorithm):
    """
    Combined diff using both pixel and SSIM algorithms.

    Uses SSIM for overall similarity score but generates pixel-level
    diff visualization.
    """

    def __init__(
        self,
        ssim_threshold: float = 0.95,
        pixel_threshold: float = 0.001,
    ):
        """
        Initialize combined diff algorithm.

        Args:
            ssim_threshold: SSIM threshold for detecting changes.
            pixel_threshold: Pixel diff threshold for visualization.
        """
        from visualqe.diff.pixel import PixelDiff

        self.ssim = SSIMDiff(threshold=ssim_threshold)
        self.pixel = PixelDiff(threshold=pixel_threshold)

    @property
    def name(self) -> str:
        return "combined"

    def compare(
        self,
        baseline: Image.Image,
        current: Image.Image,
        ignore_regions: Optional[list[tuple[int, int, int, int]]] = None,
    ) -> DiffResult:
        """
        Compare using SSIM for decision, pixel for visualization.
        """
        # Use SSIM for the primary comparison
        ssim_result = self.ssim.compare(baseline, current, ignore_regions)

        # Use pixel diff for better visualization
        pixel_result = self.pixel.compare(baseline, current, ignore_regions)

        return DiffResult(
            has_changes=ssim_result.has_changes,
            diff_percentage=ssim_result.diff_percentage,
            diff_image=pixel_result.diff_image,
            highlight_overlay=pixel_result.highlight_overlay,
            similarity_score=ssim_result.similarity_score,
        )
