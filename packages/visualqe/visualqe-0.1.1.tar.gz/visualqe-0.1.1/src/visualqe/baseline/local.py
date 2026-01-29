"""Local filesystem baseline storage."""

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from PIL import Image

from visualqe.baseline.base import BaselineStorage
from visualqe.models import Screenshot


class LocalBaselineStorage(BaselineStorage):
    """
    Local filesystem storage for baseline images.

    Stores baselines as PNG files with accompanying JSON metadata.
    Supports branch-based organization for git workflow integration.
    """

    def __init__(self, base_dir: Path | str):
        """
        Initialize local storage.

        Args:
            base_dir: Base directory for storing baselines.
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_name(self, name: str) -> str:
        """Convert name to safe filename."""
        # Replace path separators and special chars with underscores
        safe = re.sub(r"[/\\:*?\"<>|]", "_", name)
        # Remove leading/trailing whitespace and dots
        safe = safe.strip(". ")
        # Ensure not empty
        return safe or "unnamed"

    def _get_branch_dir(self, branch: Optional[str] = None) -> Path:
        """Get the directory for a branch."""
        if branch:
            branch_safe = self._sanitize_name(branch)
            return self.base_dir / "branches" / branch_safe
        return self.base_dir / "main"

    def _get_paths(
        self, name: str, branch: Optional[str] = None
    ) -> tuple[Path, Path]:
        """Get image and metadata paths for a baseline."""
        branch_dir = self._get_branch_dir(branch)
        branch_dir.mkdir(parents=True, exist_ok=True)

        safe_name = self._sanitize_name(name)
        image_path = branch_dir / f"{safe_name}.png"
        meta_path = branch_dir / f"{safe_name}.json"

        return image_path, meta_path

    def save(
        self, name: str, screenshot: Screenshot, branch: Optional[str] = None
    ) -> Path:
        """
        Save a screenshot as a baseline.

        Args:
            name: Unique identifier for this baseline.
            screenshot: The screenshot to save.
            branch: Optional branch/version identifier.

        Returns:
            Path where the baseline was saved.
        """
        image_path, meta_path = self._get_paths(name, branch)

        # Save image
        screenshot.image.save(image_path, "PNG")

        # Save metadata
        metadata = {
            "name": name,
            "url": screenshot.url,
            "viewport_width": screenshot.viewport_width,
            "viewport_height": screenshot.viewport_height,
            "captured_at": screenshot.captured_at,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "metadata": screenshot.metadata,
            "branch": branch,
        }
        meta_path.write_text(json.dumps(metadata, indent=2))

        return image_path

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
        image_path, meta_path = self._get_paths(name, branch)

        if not image_path.exists():
            # Try to find in main if branch-specific not found
            if branch:
                main_image, main_meta = self._get_paths(name, None)
                if main_image.exists():
                    image_path, meta_path = main_image, main_meta
                else:
                    raise FileNotFoundError(
                        f"Baseline '{name}' not found in branch '{branch}' or main"
                    )
            else:
                raise FileNotFoundError(f"Baseline '{name}' not found")

        # Load image
        image = Image.open(image_path)

        # Load metadata
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
        else:
            # Minimal metadata if JSON is missing
            meta = {
                "url": "unknown",
                "viewport_width": image.width,
                "viewport_height": image.height,
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "metadata": {},
            }

        return Screenshot(
            image=image,
            url=meta.get("url", "unknown"),
            viewport_width=meta.get("viewport_width", image.width),
            viewport_height=meta.get("viewport_height", image.height),
            captured_at=meta.get("captured_at", ""),
            metadata=meta.get("metadata", {}),
        )

    def exists(self, name: str, branch: Optional[str] = None) -> bool:
        """
        Check if a baseline exists.

        Args:
            name: Unique identifier for the baseline.
            branch: Optional branch/version identifier.

        Returns:
            True if baseline exists, False otherwise.
        """
        image_path, _ = self._get_paths(name, branch)
        return image_path.exists()

    def delete(self, name: str, branch: Optional[str] = None) -> None:
        """
        Delete a baseline.

        Args:
            name: Unique identifier for the baseline.
            branch: Optional branch/version identifier.
        """
        image_path, meta_path = self._get_paths(name, branch)
        image_path.unlink(missing_ok=True)
        meta_path.unlink(missing_ok=True)

    def list_all(self, branch: Optional[str] = None) -> list[str]:
        """
        List all baseline names.

        Args:
            branch: Optional branch/version identifier.

        Returns:
            List of baseline names.
        """
        branch_dir = self._get_branch_dir(branch)
        if not branch_dir.exists():
            return []

        return sorted([p.stem for p in branch_dir.glob("*.png")])

    def list_branches(self) -> list[str]:
        """
        List all branches.

        Returns:
            List of branch names.
        """
        branches_dir = self.base_dir / "branches"
        if not branches_dir.exists():
            return []

        return sorted([d.name for d in branches_dir.iterdir() if d.is_dir()])

    def copy_branch(self, source: Optional[str], target: str) -> None:
        """
        Copy all baselines from one branch to another.

        Args:
            source: Source branch (None for main).
            target: Target branch name.
        """
        source_dir = self._get_branch_dir(source)
        target_dir = self._get_branch_dir(target)

        if not source_dir.exists():
            raise FileNotFoundError(f"Source branch '{source}' not found")

        target_dir.mkdir(parents=True, exist_ok=True)

        for file in source_dir.iterdir():
            if file.is_file():
                shutil.copy2(file, target_dir / file.name)

    def delete_branch(self, branch: str) -> None:
        """
        Delete an entire branch.

        Args:
            branch: Branch name to delete.
        """
        branch_dir = self._get_branch_dir(branch)
        if branch_dir.exists():
            shutil.rmtree(branch_dir)

    def get_metadata(self, name: str, branch: Optional[str] = None) -> dict:
        """
        Get metadata for a baseline without loading the image.

        Args:
            name: Baseline name.
            branch: Optional branch name.

        Returns:
            Metadata dictionary.

        Raises:
            FileNotFoundError: If baseline doesn't exist.
        """
        _, meta_path = self._get_paths(name, branch)

        if not meta_path.exists():
            raise FileNotFoundError(f"Baseline metadata not found: {name}")

        return json.loads(meta_path.read_text())
