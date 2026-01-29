"""Tests for data models."""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
from PIL import Image

from visualqe.models import (
    Analysis,
    Change,
    ChangeType,
    ComparisonResult,
    Screenshot,
    Severity,
)


class TestChange:
    """Tests for Change model."""

    def test_create_change(self):
        """Test creating a Change instance."""
        change = Change(
            type=ChangeType.MODIFICATION,
            element="Button",
            location="header",
            severity=Severity.MINOR,
            confidence=0.9,
            description="Button color changed from blue to green",
        )

        assert change.type == ChangeType.MODIFICATION
        assert change.element == "Button"
        assert change.severity == Severity.MINOR
        assert change.confidence == 0.9

    def test_change_to_dict(self):
        """Test Change serialization to dictionary."""
        change = Change(
            type=ChangeType.ADDITION,
            element="Icon",
            location="sidebar",
            severity=Severity.COSMETIC,
            confidence=0.85,
            description="New settings icon added",
        )

        data = change.to_dict()

        assert data["type"] == "addition"
        assert data["element"] == "Icon"
        assert data["severity"] == "cosmetic"

    def test_change_from_dict(self):
        """Test Change deserialization from dictionary."""
        data = {
            "type": "removal",
            "element": "Banner",
            "location": "top",
            "severity": "major",
            "confidence": 0.95,
            "description": "Promotional banner removed",
        }

        change = Change.from_dict(data)

        assert change.type == ChangeType.REMOVAL
        assert change.severity == Severity.MAJOR


class TestScreenshot:
    """Tests for Screenshot model."""

    def test_create_screenshot(self, sample_image: Image.Image):
        """Test creating a Screenshot instance."""
        screenshot = Screenshot(
            image=sample_image,
            url="https://example.com",
            viewport_width=1920,
            viewport_height=1080,
            captured_at=datetime.now(timezone.utc).isoformat(),
        )

        assert screenshot.url == "https://example.com"
        assert screenshot.viewport_width == 1920
        assert screenshot.image.size == (100, 100)

    def test_screenshot_save_and_load(self, sample_image: Image.Image, temp_dir: Path):
        """Test saving and loading a screenshot."""
        screenshot = Screenshot(
            image=sample_image,
            url="https://example.com/page",
            viewport_width=1920,
            viewport_height=1080,
            captured_at="2024-01-01T00:00:00Z",
            metadata={"test": "value"},
        )

        # Save
        save_path = temp_dir / "test.png"
        screenshot.save(save_path)

        # Verify files exist
        assert save_path.exists()
        assert save_path.with_suffix(".json").exists()

        # Load
        loaded = Screenshot.load(save_path)

        assert loaded.url == "https://example.com/page"
        assert loaded.viewport_width == 1920
        assert loaded.metadata.get("test") == "value"

    def test_screenshot_to_bytes(self, sample_image: Image.Image):
        """Test converting screenshot to bytes."""
        screenshot = Screenshot(
            image=sample_image,
            url="https://example.com",
            viewport_width=100,
            viewport_height=100,
            captured_at="2024-01-01T00:00:00Z",
        )

        img_bytes = screenshot.to_bytes()

        assert isinstance(img_bytes, bytes)
        assert len(img_bytes) > 0

    def test_screenshot_from_bytes(self):
        """Test creating screenshot from bytes."""
        # Create a simple image and get its bytes
        img = Image.new("RGB", (50, 50), color="red")
        from io import BytesIO

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_bytes = buffer.getvalue()

        screenshot = Screenshot.from_bytes(
            img_bytes,
            url="https://test.com",
            viewport_width=50,
            viewport_height=50,
        )

        assert screenshot.url == "https://test.com"
        assert screenshot.image.size == (50, 50)


class TestAnalysis:
    """Tests for Analysis model."""

    def test_create_analysis(self):
        """Test creating an Analysis instance."""
        changes = [
            Change(
                type=ChangeType.MODIFICATION,
                element="Header",
                location="top",
                severity=Severity.MINOR,
                confidence=0.9,
                description="Header background changed",
            )
        ]

        analysis = Analysis(
            summary="Minor header styling change detected",
            changes=changes,
            raw_response='{"summary": "..."}',
        )

        assert len(analysis.changes) == 1
        assert "header" in analysis.summary.lower()

    def test_analysis_to_dict(self):
        """Test Analysis serialization."""
        analysis = Analysis(
            summary="No significant changes",
            changes=[],
            raw_response="{}",
        )

        data = analysis.to_dict()

        assert data["summary"] == "No significant changes"
        assert data["changes"] == []


class TestComparisonResult:
    """Tests for ComparisonResult model."""

    def test_create_comparison_result(
        self, sample_image: Image.Image, sample_image_modified: Image.Image
    ):
        """Test creating a ComparisonResult instance."""
        baseline = Screenshot(
            image=sample_image,
            url="https://example.com",
            viewport_width=100,
            viewport_height=100,
            captured_at="2024-01-01T00:00:00Z",
        )

        current = Screenshot(
            image=sample_image_modified,
            url="https://example.com",
            viewport_width=100,
            viewport_height=100,
            captured_at="2024-01-02T00:00:00Z",
        )

        result = ComparisonResult(
            has_changes=True,
            diff_percentage=0.15,
            diff_image=None,
            baseline=baseline,
            current=current,
        )

        assert result.has_changes is True
        assert result.diff_percentage == 0.15
        assert result.passed is False

    def test_comparison_result_to_json(
        self, sample_image: Image.Image, sample_image_modified: Image.Image
    ):
        """Test ComparisonResult JSON serialization."""
        baseline = Screenshot(
            image=sample_image,
            url="https://example.com/baseline",
            viewport_width=100,
            viewport_height=100,
            captured_at="2024-01-01T00:00:00Z",
        )

        current = Screenshot(
            image=sample_image_modified,
            url="https://example.com/current",
            viewport_width=100,
            viewport_height=100,
            captured_at="2024-01-02T00:00:00Z",
        )

        result = ComparisonResult(
            has_changes=False,
            diff_percentage=0.001,
            diff_image=None,
            baseline=baseline,
            current=current,
        )

        json_str = result.to_json()
        data = json.loads(json_str)

        assert data["has_changes"] is False
        assert data["baseline_url"] == "https://example.com/baseline"
