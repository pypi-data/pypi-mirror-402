"""Abstract base class for baseline storage."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from visualqe.models import Screenshot


class BaselineStorage(ABC):
    """Abstract base class for baseline image storage."""

    @abstractmethod
    def save(self, name: str, screenshot: Screenshot, branch: Optional[str] = None) -> Path:
        """
        Save a screenshot as a baseline.

        Args:
            name: Unique identifier for this baseline.
            screenshot: The screenshot to save.
            branch: Optional branch/version identifier.

        Returns:
            Path where the baseline was saved.
        """
        pass

    @abstractmethod
    def load(self, name: str, branch: Optional[str] = None) -> Screenshot:
        """
        Load a baseline screenshot.

        Args:
            name: Unique identifier for the baseline.
            branch: Optional branch/version identifier.

        Returns:
            The loaded Screenshot object.

        Raises:
            FileNotFoundError: If baseline doesn't exist.
        """
        pass

    @abstractmethod
    def exists(self, name: str, branch: Optional[str] = None) -> bool:
        """
        Check if a baseline exists.

        Args:
            name: Unique identifier for the baseline.
            branch: Optional branch/version identifier.

        Returns:
            True if baseline exists, False otherwise.
        """
        pass

    @abstractmethod
    def delete(self, name: str, branch: Optional[str] = None) -> None:
        """
        Delete a baseline.

        Args:
            name: Unique identifier for the baseline.
            branch: Optional branch/version identifier.
        """
        pass

    @abstractmethod
    def list_all(self, branch: Optional[str] = None) -> list[str]:
        """
        List all baseline names.

        Args:
            branch: Optional branch/version identifier.

        Returns:
            List of baseline names.
        """
        pass
