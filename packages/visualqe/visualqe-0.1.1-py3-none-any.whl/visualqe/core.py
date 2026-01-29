"""Main VisualQE class - the primary interface for visual regression testing."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional, Union

from visualqe.analysis.gemini import GeminiProvider
from visualqe.baseline.local import LocalBaselineStorage
from visualqe.capture.pixcap import PixcapProvider
from visualqe.diff.ssim import CombinedDiff, SSIMDiff
from visualqe.exceptions import (
    BaselineNotFoundError,
    ConfigurationError,
)
from visualqe.models import (
    BatchResult,
    ComparisonResult,
    Screenshot,
)


class VisualQE:
    """
    Main interface for visual regression testing.

    Combines screenshot capture, baseline management, diff algorithms,
    and VLM-powered semantic analysis.

    Example:
        ```python
        from visualqe import VisualQE

        vqe = VisualQE(
            pixcap_api_key="your-pixcap-key",
            gemini_api_key="your-gemini-key",
        )

        # Capture and save baseline
        screenshot = vqe.capture("https://example.com")
        vqe.save_baseline("homepage", screenshot)

        # Later, compare against baseline
        new_screenshot = vqe.capture("https://example.com")
        result = vqe.compare("homepage", new_screenshot)

        print(result.has_changes)
        if result.analysis:
            print(result.analysis.summary)
        ```
    """

    def __init__(
        self,
        pixcap_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        baseline_dir: Union[str, Path] = "./baselines",
        diff_threshold: float = 0.01,
        use_combined_diff: bool = True,
    ):
        """
        Initialize VisualQE.

        Args:
            pixcap_api_key: Pixcap API key. Falls back to PIXCAP_API_KEY env var.
            gemini_api_key: Gemini API key. Falls back to GEMINI_API_KEY env var.
            baseline_dir: Directory for storing baseline images.
            diff_threshold: Minimum diff percentage to consider as changed (0.0-1.0).
            use_combined_diff: Use combined SSIM+pixel diff (recommended).
        """
        # Get API keys from env if not provided
        self._pixcap_key = pixcap_api_key or os.environ.get("PIXCAP_API_KEY")
        self._gemini_key = gemini_api_key or os.environ.get("GEMINI_API_KEY")

        # Initialize capture provider
        if self._pixcap_key:
            self._capture: Optional[PixcapProvider] = PixcapProvider(self._pixcap_key)
        else:
            self._capture = None

        # Initialize VLM provider
        if self._gemini_key:
            self._vlm: Optional[GeminiProvider] = GeminiProvider(self._gemini_key)
        else:
            self._vlm = None

        # Initialize diff algorithm
        ssim_threshold = 1.0 - diff_threshold
        if use_combined_diff:
            self._diff = CombinedDiff(
                ssim_threshold=ssim_threshold,
                pixel_threshold=diff_threshold / 10,
            )
        else:
            self._diff = SSIMDiff(threshold=ssim_threshold)

        # Initialize baseline storage
        self._baseline = LocalBaselineStorage(Path(baseline_dir))

        # Store config
        self._diff_threshold = diff_threshold

    # =========================================================================
    # Screenshot Capture
    # =========================================================================

    def capture(
        self,
        url: str,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        full_page: bool = False,
        use_vpn_connector: bool = False,
        cookies: Optional[list[dict[str, Any]]] = None,
        block_selectors: Optional[list[str]] = None,
        wait_for_selector: Optional[str] = None,
        delay_ms: Optional[int] = None,
        **kwargs: Any,
    ) -> Screenshot:
        """
        Capture a screenshot of the given URL.

        Args:
            url: The URL to capture.
            viewport_width: Width of the viewport (320-3840).
            viewport_height: Height of the viewport (200-2160).
            full_page: Capture the full scrollable page.
            use_vpn_connector: Use VPN connector for internal URLs.
            cookies: List of cookies to set before capture.
            block_selectors: CSS selectors of elements to block/hide.
            wait_for_selector: Wait for this selector before capture.
            delay_ms: Additional delay in milliseconds before capture.
            **kwargs: Additional provider-specific options.

        Returns:
            Screenshot object containing the captured image and metadata.

        Raises:
            ConfigurationError: If no screenshot provider is configured.
            CaptureError: If screenshot capture fails.
        """
        if not self._capture:
            raise ConfigurationError(
                "No screenshot provider configured. "
                "Provide pixcap_api_key or set PIXCAP_API_KEY environment variable."
            )

        return self._capture.capture(
            url=url,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            full_page=full_page,
            use_vpn_connector=use_vpn_connector,
            cookies=cookies,
            block_selectors=block_selectors,
            wait_for_selector=wait_for_selector,
            delay_ms=delay_ms,
            **kwargs,
        )

    def capture_bulk(
        self,
        sitemap_url: str,
        max_pages: int = 100,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        **kwargs: Any,
    ) -> list[Screenshot]:
        """
        Capture screenshots from all URLs in a sitemap.

        Args:
            sitemap_url: URL to the sitemap.xml file.
            max_pages: Maximum number of pages to capture (up to 100).
            viewport_width: Viewport width for all captures.
            viewport_height: Viewport height for all captures.
            **kwargs: Additional capture options.

        Returns:
            List of Screenshot objects for each captured page.

        Raises:
            ConfigurationError: If no screenshot provider is configured.
            CaptureError: If bulk capture fails.
        """
        if not self._capture:
            raise ConfigurationError(
                "No screenshot provider configured. "
                "Provide pixcap_api_key or set PIXCAP_API_KEY environment variable."
            )

        return self._capture.capture_bulk(
            sitemap_url=sitemap_url,
            max_pages=max_pages,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            **kwargs,
        )

    # =========================================================================
    # Baseline Management
    # =========================================================================

    def save_baseline(
        self,
        name: str,
        screenshot: Screenshot,
        branch: Optional[str] = None,
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
        return self._baseline.save(name, screenshot, branch)

    def get_baseline(self, name: str, branch: Optional[str] = None) -> Screenshot:
        """
        Retrieve a saved baseline.

        Args:
            name: Unique identifier for the baseline.
            branch: Optional branch/version identifier.

        Returns:
            The loaded Screenshot object.

        Raises:
            BaselineNotFoundError: If baseline doesn't exist.
        """
        try:
            return self._baseline.load(name, branch)
        except FileNotFoundError as e:
            raise BaselineNotFoundError(
                f"Baseline '{name}' not found. Use save_baseline() to create one."
            ) from e

    def baseline_exists(self, name: str, branch: Optional[str] = None) -> bool:
        """
        Check if a baseline exists.

        Args:
            name: Unique identifier for the baseline.
            branch: Optional branch/version identifier.

        Returns:
            True if baseline exists, False otherwise.
        """
        return self._baseline.exists(name, branch)

    def list_baselines(self, branch: Optional[str] = None) -> list[str]:
        """
        List all saved baselines.

        Args:
            branch: Optional branch/version identifier.

        Returns:
            List of baseline names.
        """
        return self._baseline.list_all(branch)

    def delete_baseline(self, name: str, branch: Optional[str] = None) -> None:
        """
        Delete a baseline.

        Args:
            name: Unique identifier for the baseline.
            branch: Optional branch/version identifier.
        """
        self._baseline.delete(name, branch)

    def update_baseline(
        self,
        name: str,
        screenshot: Screenshot,
        branch: Optional[str] = None,
    ) -> Path:
        """
        Update an existing baseline (alias for save_baseline).

        Args:
            name: Unique identifier for the baseline.
            screenshot: The new screenshot to save.
            branch: Optional branch/version identifier.

        Returns:
            Path where the baseline was saved.
        """
        return self.save_baseline(name, screenshot, branch)

    # =========================================================================
    # Comparison
    # =========================================================================

    def compare(
        self,
        name: str,
        current: Screenshot,
        analyze: bool = True,
        intent: Optional[str] = None,
        ignore_regions: Optional[list[tuple[int, int, int, int]]] = None,
        branch: Optional[str] = None,
    ) -> ComparisonResult:
        """
        Compare a screenshot against its baseline.

        Args:
            name: Unique identifier for the baseline to compare against.
            current: The current screenshot to compare.
            analyze: Whether to run VLM analysis (requires Gemini API key).
            intent: Optional description of intended change for validation.
            ignore_regions: List of regions to ignore as (x1, y1, x2, y2) tuples.
            branch: Optional branch/version identifier for baseline.

        Returns:
            ComparisonResult with diff information and optional analysis.

        Raises:
            BaselineNotFoundError: If baseline doesn't exist.
        """
        # Load baseline
        baseline = self.get_baseline(name, branch)

        # Run diff algorithm
        diff_result = self._diff.compare(
            baseline.image,
            current.image,
            ignore_regions=ignore_regions,
        )

        # Initialize analysis results
        analysis = None
        intent_validated = None
        intent_explanation = None

        # Run VLM analysis if requested and available
        if analyze and self._vlm and diff_result.has_changes:
            try:
                analysis = self._vlm.analyze_comparison(
                    baseline.image,
                    current.image,
                )

                # Validate intent if provided
                if intent:
                    (
                        intent_validated,
                        _confidence,
                        intent_explanation,
                    ) = self._vlm.validate_intent(
                        baseline.image,
                        current.image,
                        intent,
                    )
            except Exception:
                # VLM analysis is optional - don't fail the comparison
                pass

        return ComparisonResult(
            has_changes=diff_result.has_changes,
            diff_percentage=diff_result.diff_percentage,
            diff_image=diff_result.diff_image,
            baseline=baseline,
            current=current,
            analysis=analysis,
            intent_validated=intent_validated,
            intent_explanation=intent_explanation,
        )

    def compare_images(
        self,
        baseline_image: Screenshot,
        current_image: Screenshot,
        analyze: bool = True,
        intent: Optional[str] = None,
        ignore_regions: Optional[list[tuple[int, int, int, int]]] = None,
    ) -> ComparisonResult:
        """
        Compare two screenshots directly without baseline storage.

        Args:
            baseline_image: The baseline/reference screenshot.
            current_image: The current screenshot to compare.
            analyze: Whether to run VLM analysis.
            intent: Optional description of intended change for validation.
            ignore_regions: List of regions to ignore.

        Returns:
            ComparisonResult with diff information and optional analysis.
        """
        diff_result = self._diff.compare(
            baseline_image.image,
            current_image.image,
            ignore_regions=ignore_regions,
        )

        analysis = None
        intent_validated = None
        intent_explanation = None

        if analyze and self._vlm and diff_result.has_changes:
            try:
                analysis = self._vlm.analyze_comparison(
                    baseline_image.image,
                    current_image.image,
                )

                if intent:
                    (
                        intent_validated,
                        _,
                        intent_explanation,
                    ) = self._vlm.validate_intent(
                        baseline_image.image,
                        current_image.image,
                        intent,
                    )
            except Exception:
                pass

        return ComparisonResult(
            has_changes=diff_result.has_changes,
            diff_percentage=diff_result.diff_percentage,
            diff_image=diff_result.diff_image,
            baseline=baseline_image,
            current=current_image,
            analysis=analysis,
            intent_validated=intent_validated,
            intent_explanation=intent_explanation,
        )

    # =========================================================================
    # Batch Operations
    # =========================================================================

    def compare_all(
        self,
        url_map: dict[str, str],
        analyze: bool = True,
        branch: Optional[str] = None,
        **capture_kwargs: Any,
    ) -> BatchResult:
        """
        Compare multiple URLs against their baselines.

        Args:
            url_map: Dictionary mapping baseline names to URLs.
            analyze: Whether to run VLM analysis.
            branch: Optional branch for baselines.
            **capture_kwargs: Additional arguments passed to capture().

        Returns:
            BatchResult with all comparison results.
        """
        results: list[ComparisonResult] = []
        errors = 0

        for name, url in url_map.items():
            try:
                screenshot = self.capture(url, **capture_kwargs)
                result = self.compare(name, screenshot, analyze=analyze, branch=branch)
                results.append(result)
            except Exception:
                errors += 1

        return BatchResult.from_results(results, errors)

    def capture_and_compare(
        self,
        name: str,
        url: str,
        analyze: bool = True,
        intent: Optional[str] = None,
        ignore_regions: Optional[list[tuple[int, int, int, int]]] = None,
        branch: Optional[str] = None,
        create_baseline: bool = False,
        **capture_kwargs: Any,
    ) -> ComparisonResult:
        """
        Capture a screenshot and compare against baseline in one call.

        Args:
            name: Baseline name.
            url: URL to capture.
            analyze: Whether to run VLM analysis.
            intent: Optional description of intended change.
            ignore_regions: Regions to ignore in comparison.
            branch: Optional branch for baseline.
            create_baseline: If True and baseline doesn't exist, create it.
            **capture_kwargs: Additional capture arguments.

        Returns:
            ComparisonResult.

        Raises:
            BaselineNotFoundError: If baseline doesn't exist and create_baseline is False.
        """
        screenshot = self.capture(url, **capture_kwargs)

        if create_baseline and not self.baseline_exists(name, branch):
            self.save_baseline(name, screenshot, branch)
            # Return a result indicating no changes (comparing to itself)
            return ComparisonResult(
                has_changes=False,
                diff_percentage=0.0,
                diff_image=None,
                baseline=screenshot,
                current=screenshot,
                analysis=None,
                intent_validated=None,
                intent_explanation="Baseline created (first capture).",
            )

        return self.compare(
            name,
            screenshot,
            analyze=analyze,
            intent=intent,
            ignore_regions=ignore_regions,
            branch=branch,
        )

    # =========================================================================
    # VLM Analysis
    # =========================================================================

    def analyze_accessibility(self, screenshot: Screenshot) -> dict[str, Any]:
        """
        Analyze a screenshot for accessibility issues.

        Args:
            screenshot: The screenshot to analyze.

        Returns:
            Dictionary with accessibility analysis results.

        Raises:
            ConfigurationError: If no VLM provider is configured.
            AnalysisError: If analysis fails.
        """
        if not self._vlm:
            raise ConfigurationError(
                "No VLM provider configured. "
                "Provide gemini_api_key or set GEMINI_API_KEY environment variable."
            )

        return self._vlm.analyze_accessibility(screenshot.image)

    def analyze_image(self, screenshot: Screenshot) -> dict[str, Any]:
        """
        Analyze a single screenshot for general understanding.

        Args:
            screenshot: The screenshot to analyze.

        Returns:
            Dictionary with image analysis results.

        Raises:
            ConfigurationError: If no VLM provider is configured.
        """
        if not self._vlm:
            raise ConfigurationError(
                "No VLM provider configured. "
                "Provide gemini_api_key or set GEMINI_API_KEY environment variable."
            )

        return self._vlm.analyze_single_image(screenshot.image)

    # =========================================================================
    # Health Check
    # =========================================================================

    def health_check(self) -> dict[str, bool]:
        """
        Check the health of all configured providers.

        Returns:
            Dictionary with health status of each component.
        """
        status = {
            "capture_configured": self._capture is not None,
            "vlm_configured": self._vlm is not None,
            "baseline_storage": True,  # Local storage is always available
        }

        if self._capture:
            status["capture_healthy"] = self._capture.health_check()

        if self._vlm:
            status["vlm_healthy"] = self._vlm.health_check()

        return status

    # =========================================================================
    # Cost Estimation
    # =========================================================================

    @staticmethod
    def estimate_cost(
        num_comparisons: int,
        include_analysis: bool = True,
        screenshots_per_comparison: int = 2,
    ) -> dict[str, float]:
        """
        Estimate the cost for a number of comparisons.

        Args:
            num_comparisons: Number of comparisons to run.
            include_analysis: Whether VLM analysis will be used.
            screenshots_per_comparison: Screenshots needed per comparison.

        Returns:
            Dictionary with cost breakdown.
        """
        # Pixcap pricing: ~$0.01 per screenshot at standard tier
        pixcap_cost = num_comparisons * screenshots_per_comparison * 0.01

        # Gemini 2.5 Flash pricing: ~$0.003 per analysis
        gemini_cost = num_comparisons * 0.003 if include_analysis else 0

        return {
            "pixcap_screenshots": pixcap_cost,
            "gemini_analysis": gemini_cost,
            "total": pixcap_cost + gemini_cost,
            "num_comparisons": num_comparisons,
        }
