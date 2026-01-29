"""JSON report generation."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visualqe.models import BatchResult, ComparisonResult


class JSONReporter:
    """Generate JSON reports from comparison results."""

    def __init__(self, title: str = "Visual Regression Test"):
        """
        Initialize JSON reporter.

        Args:
            title: Title for the report.
        """
        self.title = title

    def generate(
        self,
        results: list[ComparisonResult],
        output_path: Path,
        indent: int = 2,
    ) -> Path:
        """
        Generate a JSON report from comparison results.

        Args:
            results: List of comparison results.
            output_path: Path to write the JSON report.
            indent: JSON indentation level.

        Returns:
            Path to the generated report.
        """
        passed = sum(1 for r in results if not r.has_changes)
        failed = len(results) - passed

        report: dict[str, Any] = {
            "title": self.title,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total": len(results),
                "passed": passed,
                "failed": failed,
                "pass_rate": passed / len(results) if results else 0,
            },
            "results": [r.to_dict() for r in results],
        }

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=indent))

        return output_path

    def generate_from_batch(
        self,
        batch_result: BatchResult,
        output_path: Path,
        indent: int = 2,
    ) -> Path:
        """
        Generate a JSON report from a batch result.

        Args:
            batch_result: BatchResult containing multiple comparisons.
            output_path: Path to write the JSON report.
            indent: JSON indentation level.

        Returns:
            Path to the generated report.
        """
        report: dict[str, Any] = {
            "title": self.title,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total": batch_result.total_comparisons,
                "passed": batch_result.passed_count,
                "failed": batch_result.failed_count,
                "errors": batch_result.error_count,
                "pass_rate": (
                    batch_result.passed_count / batch_result.total_comparisons
                    if batch_result.total_comparisons > 0
                    else 0
                ),
            },
            "results": [r.to_dict() for r in batch_result.results],
        }

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=indent))

        return output_path

    def to_dict(self, results: list[ComparisonResult]) -> dict[str, Any]:
        """
        Convert results to dictionary without writing to file.

        Args:
            results: List of comparison results.

        Returns:
            Dictionary representation of the report.
        """
        passed = sum(1 for r in results if not r.has_changes)
        failed = len(results) - passed

        return {
            "title": self.title,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total": len(results),
                "passed": passed,
                "failed": failed,
                "pass_rate": passed / len(results) if results else 0,
            },
            "results": [r.to_dict() for r in results],
        }

    def to_json(self, results: list[ComparisonResult], indent: int = 2) -> str:
        """
        Convert results to JSON string without writing to file.

        Args:
            results: List of comparison results.
            indent: JSON indentation level.

        Returns:
            JSON string representation of the report.
        """
        return json.dumps(self.to_dict(results), indent=indent)
