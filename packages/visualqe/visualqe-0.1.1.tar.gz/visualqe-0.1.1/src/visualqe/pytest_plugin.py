"""pytest plugin for VisualQE visual regression testing."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Generator, Optional

import pytest

from visualqe.core import VisualQE
from visualqe.models import ComparisonResult
from visualqe.reporting.html import HTMLReporter
from visualqe.reporting.json import JSONReporter


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add VisualQE command line options."""
    group = parser.getgroup("visualqe", "Visual regression testing options")

    group.addoption(
        "--visual-baseline-dir",
        action="store",
        default="./baselines",
        help="Directory for storing visual baselines (default: ./baselines)",
    )

    group.addoption(
        "--visual-report",
        action="store",
        default=None,
        help="Path for HTML report output (e.g., ./reports/visual.html)",
    )

    group.addoption(
        "--visual-report-json",
        action="store",
        default=None,
        help="Path for JSON report output",
    )

    group.addoption(
        "--visual-update-baselines",
        action="store_true",
        default=False,
        help="Update baselines instead of comparing (use to regenerate baselines)",
    )

    group.addoption(
        "--visual-threshold",
        action="store",
        default=0.01,
        type=float,
        help="Diff threshold for detecting changes (default: 0.01 = 1%%)",
    )

    group.addoption(
        "--visual-skip-analysis",
        action="store_true",
        default=False,
        help="Skip VLM analysis (useful for faster CI runs)",
    )

    group.addoption(
        "--visual-branch",
        action="store",
        default=None,
        help="Branch name for baseline versioning",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "visual: mark test as a visual regression test",
    )
    config.addinivalue_line(
        "markers",
        "visual_baseline(name): specify baseline name for visual test",
    )


class VisualTestSession:
    """Manages visual test state across a pytest session."""

    def __init__(self, config: pytest.Config):
        self.config = config
        self.results: list[ComparisonResult] = []
        self._vqe: Optional[VisualQE] = None

    @property
    def vqe(self) -> VisualQE:
        """Lazy initialization of VisualQE instance."""
        if self._vqe is None:
            baseline_dir = self.config.getoption("--visual-baseline-dir")
            threshold = self.config.getoption("--visual-threshold")

            self._vqe = VisualQE(
                pixcap_api_key=os.environ.get("PIXCAP_API_KEY"),
                gemini_api_key=os.environ.get("GEMINI_API_KEY"),
                baseline_dir=baseline_dir,
                diff_threshold=threshold,
            )
        return self._vqe

    @property
    def update_mode(self) -> bool:
        """Check if we're in baseline update mode."""
        return bool(self.config.getoption("--visual-update-baselines"))

    @property
    def skip_analysis(self) -> bool:
        """Check if VLM analysis should be skipped."""
        return bool(self.config.getoption("--visual-skip-analysis"))

    @property
    def branch(self) -> Optional[str]:
        """Get the branch name for baseline versioning."""
        return self.config.getoption("--visual-branch")

    def add_result(self, result: ComparisonResult) -> None:
        """Add a comparison result to the session."""
        self.results.append(result)


@pytest.fixture(scope="session")
def _visual_session(request: pytest.FixtureRequest) -> VisualTestSession:
    """Session-scoped fixture for managing visual test state."""
    return VisualTestSession(request.config)


@pytest.fixture
def visualqe(_visual_session: VisualTestSession) -> VisualQE:
    """
    Fixture providing a configured VisualQE instance.

    Usage:
        def test_example(visualqe):
            screenshot = visualqe.capture("https://example.com")
            visualqe.save_baseline("example", screenshot)
    """
    return _visual_session.vqe


@pytest.fixture
def visual_check(
    _visual_session: VisualTestSession,
    request: pytest.FixtureRequest,
) -> Generator[VisualCheckHelper, None, None]:
    """
    Fixture for visual regression assertions.

    Usage:
        def test_homepage(visual_check):
            visual_check("homepage", "https://example.com")
    """
    helper = VisualCheckHelper(_visual_session, request)
    yield helper


class VisualCheckHelper:
    """Helper class for visual regression checks."""

    def __init__(
        self,
        session: VisualTestSession,
        request: pytest.FixtureRequest,
    ):
        self.session = session
        self.request = request

    def __call__(
        self,
        name: str,
        url: str,
        intent: Optional[str] = None,
        ignore_regions: Optional[list[tuple[int, int, int, int]]] = None,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        full_page: bool = False,
        use_vpn_connector: bool = False,
        fail_on_diff: bool = True,
        **capture_kwargs: Any,
    ) -> Optional[ComparisonResult]:
        """
        Capture a screenshot and compare against baseline.

        Args:
            name: Unique baseline name.
            url: URL to capture.
            intent: Optional description of intended change.
            ignore_regions: Regions to ignore in comparison.
            viewport_width: Viewport width.
            viewport_height: Viewport height.
            full_page: Capture full page.
            use_vpn_connector: Use VPN connector.
            fail_on_diff: Whether to fail the test on diff detection.
            **capture_kwargs: Additional capture options.

        Returns:
            ComparisonResult if not in update mode, None otherwise.

        Raises:
            pytest.fail: If changes detected and fail_on_diff is True.
        """
        vqe = self.session.vqe

        # Capture screenshot
        screenshot = vqe.capture(
            url=url,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            full_page=full_page,
            use_vpn_connector=use_vpn_connector,
            **capture_kwargs,
        )

        # Update mode - just save and skip comparison
        if self.session.update_mode:
            vqe.save_baseline(name, screenshot, self.session.branch)
            return None

        # Check if baseline exists
        if not vqe.baseline_exists(name, self.session.branch):
            # Create baseline on first run
            vqe.save_baseline(name, screenshot, self.session.branch)
            pytest.skip(f"Created new baseline: {name}")
            return None

        # Compare against baseline
        result = vqe.compare(
            name=name,
            current=screenshot,
            analyze=not self.session.skip_analysis,
            intent=intent,
            ignore_regions=ignore_regions,
            branch=self.session.branch,
        )

        # Store result for reporting
        self.session.add_result(result)

        # Fail if changes detected
        if result.has_changes and fail_on_diff:
            message = f"Visual regression detected for '{name}': {result.diff_percentage:.2%} difference"
            if result.analysis:
                message += f"\n\nAnalysis: {result.analysis.summary}"
            pytest.fail(message)

        return result

    def capture(
        self,
        url: str,
        **kwargs: Any,
    ):
        """Capture a screenshot without comparison."""
        return self.session.vqe.capture(url, **kwargs)

    def save_baseline(self, name: str, screenshot: Any) -> None:
        """Save a screenshot as baseline."""
        self.session.vqe.save_baseline(name, screenshot, self.session.branch)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Generate reports at the end of the test session."""
    # Get the visual session if it was used
    visual_session = getattr(session, "_visual_session_instance", None)

    # Try to get from plugin manager
    if visual_session is None:
        try:
            for item in session.items:
                if hasattr(item, "_visual_session"):
                    visual_session = item._visual_session
                    break
        except Exception:
            pass

    # Alternative: check if we have results stored
    if visual_session is None:
        return

    if not visual_session.results:
        return

    config = session.config

    # Generate HTML report
    html_path = config.getoption("--visual-report")
    if html_path:
        reporter = HTMLReporter(title="Visual Regression Report")
        reporter.generate(visual_session.results, Path(html_path))

    # Generate JSON report
    json_path = config.getoption("--visual-report-json")
    if json_path:
        reporter = JSONReporter(title="Visual Regression Report")
        reporter.generate(visual_session.results, Path(json_path))


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item: pytest.Item) -> None:
    """Store visual session reference on test items."""
    # Check if the test uses visual fixtures
    if "visual_check" in item.fixturenames or "visualqe" in item.fixturenames:
        session = item.session
        if not hasattr(session, "_visual_session_instance"):
            session._visual_session_instance = VisualTestSession(item.config)
        item._visual_session = session._visual_session_instance
