"""Abstract base class for VLM providers."""

from abc import ABC, abstractmethod
from typing import Optional

from PIL import Image

from visualqe.models import Analysis


class VLMProvider(ABC):
    """Abstract base class for Visual Language Model providers."""

    @abstractmethod
    def analyze_comparison(
        self,
        baseline: Image.Image,
        current: Image.Image,
    ) -> Analysis:
        """
        Analyze visual differences between two images.

        Args:
            baseline: The baseline/reference image.
            current: The current image to compare.

        Returns:
            Analysis object with summary and detected changes.

        Raises:
            AnalysisError: If analysis fails.
        """
        pass

    @abstractmethod
    def validate_intent(
        self,
        baseline: Image.Image,
        current: Image.Image,
        intent: str,
    ) -> tuple[bool, float, str]:
        """
        Validate whether an intended change was implemented.

        Args:
            baseline: The baseline/reference image (before).
            current: The current image (after).
            intent: Description of the intended change.

        Returns:
            Tuple of (validated: bool, confidence: float, explanation: str).

        Raises:
            AnalysisError: If validation fails.
        """
        pass

    @abstractmethod
    def analyze_accessibility(
        self,
        image: Image.Image,
    ) -> dict:
        """
        Analyze an image for accessibility issues.

        Args:
            image: The image to analyze.

        Returns:
            Dictionary containing accessibility analysis results.

        Raises:
            AnalysisError: If analysis fails.
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the VLM provider is available.

        Returns:
            True if healthy, False otherwise.
        """
        pass
