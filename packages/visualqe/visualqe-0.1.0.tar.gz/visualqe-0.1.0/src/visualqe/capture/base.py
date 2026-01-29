"""Abstract base class for screenshot providers."""

from abc import ABC, abstractmethod
from typing import Any, Optional

from visualqe.models import Screenshot


class ScreenshotProvider(ABC):
    """Abstract base class for screenshot capture providers."""

    @abstractmethod
    def capture(
        self,
        url: str,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        full_page: bool = False,
        cookies: Optional[list[dict[str, Any]]] = None,
        block_selectors: Optional[list[str]] = None,
        wait_for_selector: Optional[str] = None,
        delay_ms: Optional[int] = None,
        use_vpn_connector: bool = False,
        **kwargs: Any,
    ) -> Screenshot:
        """
        Capture a screenshot of the given URL.

        Args:
            url: The URL to capture.
            viewport_width: Width of the viewport (320-3840).
            viewport_height: Height of the viewport (200-2160).
            full_page: Capture the full scrollable page.
            cookies: List of cookies to set before capture.
            block_selectors: CSS selectors of elements to block/hide.
            wait_for_selector: Wait for this selector before capture.
            delay_ms: Additional delay in milliseconds before capture.
            use_vpn_connector: Use VPN connector for internal URLs.
            **kwargs: Additional provider-specific options.

        Returns:
            Screenshot object containing the captured image and metadata.

        Raises:
            CaptureError: If screenshot capture fails.
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the provider is available and configured correctly.

        Returns:
            True if healthy, False otherwise.
        """
        pass
