"""Tests for reporting functionality."""

import json
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
from visualqe.reporting.html import HTMLReporter
from visualqe.reporting.json import JSONReporter


@pytest.fixture
def sample_results(sample_image: Image.Image, sample_image_modified: Image.Image):
    """Create sample comparison results for testing."""
    baseline = Screenshot(
        image=sample_image,
        url="https://example.com/page1",
        viewport_width=100,
        viewport_height=100,
        captured_at=datetime.now(timezone.utc).isoformat(),
    )

    current = Screenshot(
        image=sample_image_modified,
        url="https://example.com/page1",
        viewport_width=100,
        viewport_height=100,
        captured_at=datetime.now(timezone.utc).isoformat(),
    )

    analysis = Analysis(
        summary="Button color changed from blue to orange",
        changes=[
            Change(
                type=ChangeType.MODIFICATION,
                element="Primary Button",
                location="main content",
                severity=Severity.MINOR,
                confidence=0.92,
                description="Button background color changed from #0064C8 to #C86400",
            )
        ],
        raw_response="{}",
    )

    result_with_changes = ComparisonResult(
        has_changes=True,
        diff_percentage=0.25,
        diff_image=sample_image,
        baseline=baseline,
        current=current,
        analysis=analysis,
    )

    result_no_changes = ComparisonResult(
        has_changes=False,
        diff_percentage=0.001,
        diff_image=None,
        baseline=baseline,
        current=Screenshot(
            image=sample_image.copy(),
            url="https://example.com/page2",
            viewport_width=100,
            viewport_height=100,
            captured_at=datetime.now(timezone.utc).isoformat(),
        ),
    )

    return [result_with_changes, result_no_changes]


class TestHTMLReporter:
    """Tests for HTML report generation."""

    def test_generate_report(self, sample_results, temp_dir: Path):
        """Test basic HTML report generation."""
        reporter = HTMLReporter(title="Test Report")
        output_path = temp_dir / "report.html"

        result_path = reporter.generate(sample_results, output_path)

        assert result_path.exists()
        content = result_path.read_text()

        # Check basic structure
        assert "<!DOCTYPE html>" in content
        assert "Test Report" in content
        assert "VisualQE Report" in content

    def test_report_contains_results(self, sample_results, temp_dir: Path):
        """Test that report contains result information."""
        reporter = HTMLReporter()
        output_path = temp_dir / "report.html"

        reporter.generate(sample_results, output_path)
        content = output_path.read_text()

        # Check for status badges
        assert "Passed" in content or "passed" in content
        assert "Changes Detected" in content or "failed" in content

        # Check for URLs
        assert "example.com" in content

    def test_report_contains_analysis(self, sample_results, temp_dir: Path):
        """Test that report includes AI analysis."""
        reporter = HTMLReporter()
        output_path = temp_dir / "report.html"

        reporter.generate(sample_results, output_path)
        content = output_path.read_text()

        # Check for analysis content
        assert "Button color changed" in content
        assert "Primary Button" in content

    def test_report_summary(self, sample_results, temp_dir: Path):
        """Test that report has correct summary counts."""
        reporter = HTMLReporter()
        output_path = temp_dir / "report.html"

        reporter.generate(sample_results, output_path)
        content = output_path.read_text()

        # Should show 2 total, 1 passed, 1 failed
        assert ">2<" in content  # Total
        assert ">1<" in content  # Passed/Failed counts

    def test_empty_results(self, temp_dir: Path):
        """Test report generation with empty results."""
        reporter = HTMLReporter()
        output_path = temp_dir / "empty_report.html"

        reporter.generate([], output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert ">0<" in content  # Total should be 0


class TestJSONReporter:
    """Tests for JSON report generation."""

    def test_generate_report(self, sample_results, temp_dir: Path):
        """Test basic JSON report generation."""
        reporter = JSONReporter(title="Test Report")
        output_path = temp_dir / "report.json"

        result_path = reporter.generate(sample_results, output_path)

        assert result_path.exists()

        data = json.loads(result_path.read_text())
        assert data["title"] == "Test Report"
        assert "generated_at" in data
        assert "summary" in data
        assert "results" in data

    def test_report_summary(self, sample_results, temp_dir: Path):
        """Test JSON report summary calculations."""
        reporter = JSONReporter()
        output_path = temp_dir / "report.json"

        reporter.generate(sample_results, output_path)

        data = json.loads(output_path.read_text())
        summary = data["summary"]

        assert summary["total"] == 2
        assert summary["passed"] == 1
        assert summary["failed"] == 1
        assert summary["pass_rate"] == 0.5

    def test_report_results_structure(self, sample_results, temp_dir: Path):
        """Test JSON report results structure."""
        reporter = JSONReporter()
        output_path = temp_dir / "report.json"

        reporter.generate(sample_results, output_path)

        data = json.loads(output_path.read_text())
        results = data["results"]

        assert len(results) == 2

        # Check first result (with changes)
        result_with_changes = results[0]
        assert result_with_changes["has_changes"] is True
        assert "analysis" in result_with_changes
        assert result_with_changes["analysis"]["summary"] is not None

    def test_to_dict(self, sample_results):
        """Test to_dict method."""
        reporter = JSONReporter(title="Dict Test")

        data = reporter.to_dict(sample_results)

        assert data["title"] == "Dict Test"
        assert len(data["results"]) == 2

    def test_to_json(self, sample_results):
        """Test to_json method."""
        reporter = JSONReporter()

        json_str = reporter.to_json(sample_results)

        # Should be valid JSON
        data = json.loads(json_str)
        assert "summary" in data

    def test_empty_results(self, temp_dir: Path):
        """Test JSON report with empty results."""
        reporter = JSONReporter()
        output_path = temp_dir / "empty_report.json"

        reporter.generate([], output_path)

        data = json.loads(output_path.read_text())
        assert data["summary"]["total"] == 0
        assert data["summary"]["pass_rate"] == 0
