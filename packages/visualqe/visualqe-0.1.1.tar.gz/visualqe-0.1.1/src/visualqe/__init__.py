"""VisualQE - Visual regression testing with LLM-powered semantic analysis."""

from visualqe.core import VisualQE
from visualqe.models import (
    Analysis,
    Change,
    ChangeType,
    ComparisonResult,
    Screenshot,
    Severity,
)
from visualqe.exceptions import (
    VisualQEError,
    CaptureError,
    BaselineNotFoundError,
    AnalysisError,
    ConfigurationError,
)

__version__ = "0.1.0"

__all__ = [
    "VisualQE",
    "Analysis",
    "Change",
    "ChangeType",
    "ComparisonResult",
    "Screenshot",
    "Severity",
    "VisualQEError",
    "CaptureError",
    "BaselineNotFoundError",
    "AnalysisError",
    "ConfigurationError",
]
