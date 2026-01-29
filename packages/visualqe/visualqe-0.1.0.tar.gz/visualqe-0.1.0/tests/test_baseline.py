"""Tests for baseline storage."""

from datetime import datetime, timezone
from pathlib import Path

import pytest
from PIL import Image

from visualqe.baseline.local import LocalBaselineStorage
from visualqe.models import Screenshot


class TestLocalBaselineStorage:
    """Tests for LocalBaselineStorage."""

    def test_save_and_load(self, sample_image: Image.Image, temp_dir: Path):
        """Test saving and loading a baseline."""
        storage = LocalBaselineStorage(temp_dir)

        screenshot = Screenshot(
            image=sample_image,
            url="https://example.com",
            viewport_width=100,
            viewport_height=100,
            captured_at=datetime.now(timezone.utc).isoformat(),
            metadata={"key": "value"},
        )

        # Save
        path = storage.save("test-baseline", screenshot)
        assert path.exists()

        # Load
        loaded = storage.load("test-baseline")
        assert loaded.url == "https://example.com"
        assert loaded.metadata.get("key") == "value"

    def test_exists(self, sample_image: Image.Image, temp_dir: Path):
        """Test existence check."""
        storage = LocalBaselineStorage(temp_dir)

        screenshot = Screenshot(
            image=sample_image,
            url="https://example.com",
            viewport_width=100,
            viewport_height=100,
            captured_at=datetime.now(timezone.utc).isoformat(),
        )

        assert storage.exists("test") is False

        storage.save("test", screenshot)

        assert storage.exists("test") is True

    def test_delete(self, sample_image: Image.Image, temp_dir: Path):
        """Test baseline deletion."""
        storage = LocalBaselineStorage(temp_dir)

        screenshot = Screenshot(
            image=sample_image,
            url="https://example.com",
            viewport_width=100,
            viewport_height=100,
            captured_at=datetime.now(timezone.utc).isoformat(),
        )

        storage.save("to-delete", screenshot)
        assert storage.exists("to-delete") is True

        storage.delete("to-delete")
        assert storage.exists("to-delete") is False

    def test_list_all(self, sample_image: Image.Image, temp_dir: Path):
        """Test listing all baselines."""
        storage = LocalBaselineStorage(temp_dir)

        screenshot = Screenshot(
            image=sample_image,
            url="https://example.com",
            viewport_width=100,
            viewport_height=100,
            captured_at=datetime.now(timezone.utc).isoformat(),
        )

        assert storage.list_all() == []

        storage.save("baseline-a", screenshot)
        storage.save("baseline-b", screenshot)
        storage.save("baseline-c", screenshot)

        baselines = storage.list_all()
        assert len(baselines) == 3
        assert "baseline-a" in baselines
        assert "baseline-b" in baselines

    def test_branch_support(self, sample_image: Image.Image, temp_dir: Path):
        """Test branch-based baseline versioning."""
        storage = LocalBaselineStorage(temp_dir)

        screenshot_main = Screenshot(
            image=sample_image,
            url="https://example.com/main",
            viewport_width=100,
            viewport_height=100,
            captured_at=datetime.now(timezone.utc).isoformat(),
        )

        screenshot_feature = Screenshot(
            image=sample_image,
            url="https://example.com/feature",
            viewport_width=100,
            viewport_height=100,
            captured_at=datetime.now(timezone.utc).isoformat(),
        )

        # Save to main
        storage.save("page", screenshot_main, branch=None)

        # Save to feature branch
        storage.save("page", screenshot_feature, branch="feature/new-ui")

        # Load from main
        loaded_main = storage.load("page", branch=None)
        assert loaded_main.url == "https://example.com/main"

        # Load from feature branch
        loaded_feature = storage.load("page", branch="feature/new-ui")
        assert loaded_feature.url == "https://example.com/feature"

    def test_branch_fallback_to_main(
        self, sample_image: Image.Image, temp_dir: Path
    ):
        """Test that branch loading falls back to main if not found."""
        storage = LocalBaselineStorage(temp_dir)

        screenshot = Screenshot(
            image=sample_image,
            url="https://example.com",
            viewport_width=100,
            viewport_height=100,
            captured_at=datetime.now(timezone.utc).isoformat(),
        )

        # Save only to main
        storage.save("fallback-test", screenshot)

        # Load from non-existent branch should fall back to main
        loaded = storage.load("fallback-test", branch="non-existent")
        assert loaded.url == "https://example.com"

    def test_sanitize_name(self, sample_image: Image.Image, temp_dir: Path):
        """Test that special characters in names are handled."""
        storage = LocalBaselineStorage(temp_dir)

        screenshot = Screenshot(
            image=sample_image,
            url="https://example.com",
            viewport_width=100,
            viewport_height=100,
            captured_at=datetime.now(timezone.utc).isoformat(),
        )

        # Names with special characters
        storage.save("page/with/slashes", screenshot)
        storage.save("page:with:colons", screenshot)
        storage.save("page with spaces", screenshot)

        assert storage.exists("page/with/slashes")
        assert storage.exists("page:with:colons")
        assert storage.exists("page with spaces")

    def test_not_found_error(self, temp_dir: Path):
        """Test error when baseline not found."""
        storage = LocalBaselineStorage(temp_dir)

        with pytest.raises(FileNotFoundError):
            storage.load("non-existent")

    def test_list_branches(self, sample_image: Image.Image, temp_dir: Path):
        """Test listing all branches."""
        storage = LocalBaselineStorage(temp_dir)

        screenshot = Screenshot(
            image=sample_image,
            url="https://example.com",
            viewport_width=100,
            viewport_height=100,
            captured_at=datetime.now(timezone.utc).isoformat(),
        )

        storage.save("test", screenshot, branch="branch-a")
        storage.save("test", screenshot, branch="branch-b")

        branches = storage.list_branches()
        assert "branch-a" in branches
        assert "branch-b" in branches

    def test_get_metadata(self, sample_image: Image.Image, temp_dir: Path):
        """Test getting metadata without loading image."""
        storage = LocalBaselineStorage(temp_dir)

        screenshot = Screenshot(
            image=sample_image,
            url="https://example.com/metadata-test",
            viewport_width=1920,
            viewport_height=1080,
            captured_at="2024-01-01T00:00:00Z",
            metadata={"custom": "data"},
        )

        storage.save("meta-test", screenshot)

        meta = storage.get_metadata("meta-test")

        assert meta["url"] == "https://example.com/metadata-test"
        assert meta["viewport_width"] == 1920
        assert meta["metadata"]["custom"] == "data"
