"""Data models for VisualQE."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

from PIL import Image


class ChangeType(Enum):
    """Type of visual change detected."""

    ADDITION = "addition"
    REMOVAL = "removal"
    MODIFICATION = "modification"
    LAYOUT = "layout"


class Severity(Enum):
    """Severity level of a detected change."""

    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    COSMETIC = "cosmetic"


@dataclass
class Change:
    """A single detected visual change."""

    type: ChangeType
    element: str
    location: str
    severity: Severity
    confidence: float
    description: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "type": self.type.value,
            "element": self.element,
            "location": self.location,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Change:
        """Create from dictionary representation."""
        return cls(
            type=ChangeType(data["type"]),
            element=data["element"],
            location=data["location"],
            severity=Severity(data["severity"]),
            confidence=data["confidence"],
            description=data["description"],
        )


@dataclass
class Analysis:
    """VLM analysis result."""

    summary: str
    changes: list[Change]
    raw_response: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "summary": self.summary,
            "changes": [c.to_dict() for c in self.changes],
            "raw_response": self.raw_response,
        }


@dataclass
class Screenshot:
    """A captured screenshot with metadata."""

    image: Image.Image
    url: str
    viewport_width: int
    viewport_height: int
    captured_at: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def save(self, path: Path) -> None:
        """Save screenshot and metadata to files."""
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Save image
        self.image.save(path)

        # Save metadata
        meta_path = path.with_suffix(".json")
        meta_path.write_text(
            json.dumps(
                {
                    "url": self.url,
                    "viewport_width": self.viewport_width,
                    "viewport_height": self.viewport_height,
                    "captured_at": self.captured_at,
                    "metadata": self.metadata,
                },
                indent=2,
            )
        )

    @classmethod
    def load(cls, path: Path) -> Screenshot:
        """Load screenshot and metadata from files."""
        image = Image.open(path)
        meta_path = path.with_suffix(".json")
        meta = json.loads(meta_path.read_text())

        return cls(
            image=image,
            url=meta["url"],
            viewport_width=meta["viewport_width"],
            viewport_height=meta["viewport_height"],
            captured_at=meta["captured_at"],
            metadata=meta.get("metadata", {}),
        )

    @classmethod
    def from_bytes(
        cls,
        image_bytes: bytes,
        url: str,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Screenshot:
        """Create screenshot from raw image bytes."""
        image = Image.open(BytesIO(image_bytes))
        return cls(
            image=image,
            url=url,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            captured_at=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        )

    def to_bytes(self, format: str = "PNG") -> bytes:
        """Convert image to bytes."""
        buffer = BytesIO()
        self.image.save(buffer, format=format)
        return buffer.getvalue()


@dataclass
class DiffResult:
    """Result from image comparison algorithm."""

    has_changes: bool
    diff_percentage: float
    diff_image: Optional[Image.Image]
    highlight_overlay: Optional[Image.Image] = None
    similarity_score: Optional[float] = None


@dataclass
class ComparisonResult:
    """Complete comparison result with optional analysis."""

    has_changes: bool
    diff_percentage: float
    diff_image: Optional[Image.Image]
    baseline: Screenshot
    current: Screenshot
    analysis: Optional[Analysis] = None
    intent_validated: Optional[bool] = None
    intent_explanation: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result: dict[str, Any] = {
            "has_changes": self.has_changes,
            "diff_percentage": self.diff_percentage,
            "baseline_url": self.baseline.url,
            "current_url": self.current.url,
            "baseline_captured_at": self.baseline.captured_at,
            "current_captured_at": self.current.captured_at,
        }

        if self.analysis:
            result["analysis"] = self.analysis.to_dict()

        if self.intent_validated is not None:
            result["intent_validated"] = self.intent_validated
            result["intent_explanation"] = self.intent_explanation

        return result

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @property
    def passed(self) -> bool:
        """Check if comparison passed (no changes detected)."""
        return not self.has_changes


@dataclass
class BatchResult:
    """Result from batch comparison."""

    results: list[ComparisonResult]
    total_comparisons: int
    passed_count: int
    failed_count: int
    error_count: int

    @classmethod
    def from_results(
        cls, results: list[ComparisonResult], errors: int = 0
    ) -> BatchResult:
        """Create batch result from list of comparison results."""
        passed = sum(1 for r in results if not r.has_changes)
        failed = sum(1 for r in results if r.has_changes)

        return cls(
            results=results,
            total_comparisons=len(results) + errors,
            passed_count=passed,
            failed_count=failed,
            error_count=errors,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "total_comparisons": self.total_comparisons,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "error_count": self.error_count,
            "results": [r.to_dict() for r in self.results],
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
