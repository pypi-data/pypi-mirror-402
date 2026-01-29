"""Abstract base class for diff algorithms."""

from abc import ABC, abstractmethod
from typing import Optional

from PIL import Image

from visualqe.models import DiffResult


class DiffAlgorithm(ABC):
    """Abstract base class for image comparison algorithms."""

    @abstractmethod
    def compare(
        self,
        baseline: Image.Image,
        current: Image.Image,
        ignore_regions: Optional[list[tuple[int, int, int, int]]] = None,
    ) -> DiffResult:
        """
        Compare two images and return the diff result.

        Args:
            baseline: The baseline/reference image.
            current: The current image to compare.
            ignore_regions: List of regions to ignore as (x1, y1, x2, y2) tuples.

        Returns:
            DiffResult containing comparison results.

        Raises:
            DiffError: If comparison fails.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this algorithm."""
        pass
