"""Pixcap screenshot provider implementation."""

import base64
import os
import time
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Optional

import requests
from PIL import Image

from visualqe.capture.base import ScreenshotProvider
from visualqe.exceptions import (
    AuthenticationError,
    CaptureError,
    RateLimitError,
)
from visualqe.models import Screenshot


class PixcapProvider(ScreenshotProvider):
    """Screenshot provider using Pixcap.dev API."""

    BASE_URL = "https://pixcap.dev/api/v1"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0

    def __init__(
        self,
        api_key: str,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ):
        """
        Initialize Pixcap provider.

        Args:
            api_key: Pixcap API key.
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts for transient failures.
        """
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries

    def _make_request(
        self,
        endpoint: str,
        params: dict[str, Any],
        return_raw: bool = False,
    ) -> dict[str, Any] | bytes:
        """Make an API request with retry logic."""
        headers = {
            "X-API-Key": self.api_key,
        }

        url = f"{self.BASE_URL}/{endpoint}"
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                )

                # Handle specific error codes
                if response.status_code == 401:
                    raise AuthenticationError(
                        "Invalid Pixcap API key. Check your PIXCAP_API_KEY."
                    )
                elif response.status_code == 429:
                    # Rate limited - extract retry-after if available
                    retry_after = response.headers.get("Retry-After", "60")
                    raise RateLimitError(
                        f"Pixcap rate limit exceeded. Retry after {retry_after}s."
                    )
                elif response.status_code >= 500:
                    # Server error - retry
                    raise CaptureError(
                        f"Pixcap server error: {response.status_code}"
                    )

                response.raise_for_status()

                if return_raw:
                    return response.content
                return response.json()

            except (requests.Timeout, requests.ConnectionError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                    continue
            except (AuthenticationError, RateLimitError):
                raise
            except requests.RequestException as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                    continue

        raise CaptureError(f"Failed after {self.max_retries} attempts: {last_error}")

    def _make_post_request(
        self,
        endpoint: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Make a POST API request with retry logic."""
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

        url = f"{self.BASE_URL}/{endpoint}"
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout * 3,  # Bulk operations take longer
                )

                if response.status_code == 401:
                    raise AuthenticationError(
                        "Invalid Pixcap API key. Check your PIXCAP_API_KEY."
                    )
                elif response.status_code == 429:
                    retry_after = response.headers.get("Retry-After", "60")
                    raise RateLimitError(
                        f"Pixcap rate limit exceeded. Retry after {retry_after}s."
                    )
                elif response.status_code >= 500:
                    raise CaptureError(
                        f"Pixcap server error: {response.status_code}"
                    )

                response.raise_for_status()
                return response.json()

            except (requests.Timeout, requests.ConnectionError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                    continue
            except (AuthenticationError, RateLimitError):
                raise
            except requests.RequestException as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                    continue

        raise CaptureError(f"Failed after {self.max_retries} attempts: {last_error}")

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
        dark_mode: bool = False,
        image_format: str = "png",
        quality: int = 90,
        **kwargs: Any,
    ) -> Screenshot:
        """
        Capture a screenshot using Pixcap API.

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
            dark_mode: Emulate dark mode.
            image_format: Output format ("png" or "jpeg").
            quality: JPEG quality (1-100).
            **kwargs: Additional Pixcap-specific options.

        Returns:
            Screenshot object containing the captured image and metadata.

        Raises:
            CaptureError: If screenshot capture fails.
            AuthenticationError: If API key is invalid.
            RateLimitError: If rate limit is exceeded.
        """
        # Validate viewport dimensions
        viewport_width = max(320, min(3840, viewport_width))
        viewport_height = max(200, min(2160, viewport_height))

        # Build query params
        params: dict[str, Any] = {
            "url": url,
        }

        # Add optional params only if specified
        if viewport_width != 1920:
            params["viewport_width"] = viewport_width
        if viewport_height != 1080:
            params["viewport_height"] = viewport_height
        if full_page:
            params["full_page"] = "true"
        if image_format != "png":
            params["format"] = image_format
        if image_format == "jpeg" and quality != 90:
            params["quality"] = quality
        if wait_for_selector:
            params["wait_for_selector"] = wait_for_selector
        if delay_ms:
            params["delay_ms"] = delay_ms
        if use_vpn_connector:
            # Check for connector_id in kwargs or environment
            connector_id = kwargs.pop("connector_id", None) or os.environ.get("PIXCAP_CONNECTOR_ID")
            if connector_id:
                params["connector_id"] = connector_id
            else:
                params["use_connector"] = "true"
        if dark_mode:
            params["dark_mode"] = "true"

        # Add any additional kwargs
        params.update(kwargs)

        # Make the request
        start_time = time.time()
        image_data = self._make_request("screenshot", params, return_raw=True)
        response_time = time.time() - start_time

        # Load image from raw bytes
        try:
            image = Image.open(BytesIO(image_data))
        except Exception as e:
            raise CaptureError(f"Failed to decode image from response: {e}")

        return Screenshot(
            image=image,
            url=url,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            captured_at=datetime.now(timezone.utc).isoformat(),
            metadata={
                "provider": "pixcap",
                "response_time_ms": int(response_time * 1000),
                "use_vpn_connector": use_vpn_connector,
                "full_page": full_page,
                "format": image_format,
            },
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
        Capture screenshots from a sitemap URL.

        Args:
            sitemap_url: URL to the sitemap.xml.
            max_pages: Maximum number of pages to capture.
            viewport_width: Viewport width for all captures.
            viewport_height: Viewport height for all captures.
            **kwargs: Additional capture options.

        Returns:
            List of captured screenshots.

        Raises:
            CaptureError: If bulk capture fails.
        """
        payload = {
            "sitemap_url": sitemap_url,
            "max_pages": min(max_pages, 100),
            "viewport_width": viewport_width,
            "viewport_height": viewport_height,
            **kwargs,
        }

        data = self._make_post_request("bulk/sitemap", payload)

        screenshots = []
        for item in data.get("screenshots", []):
            try:
                image_data = base64.b64decode(item["image"])
                image = Image.open(BytesIO(image_data))
                screenshots.append(
                    Screenshot(
                        image=image,
                        url=item["url"],
                        viewport_width=viewport_width,
                        viewport_height=viewport_height,
                        captured_at=datetime.now(timezone.utc).isoformat(),
                        metadata={
                            "provider": "pixcap",
                            "bulk_capture": True,
                            "sitemap_url": sitemap_url,
                        },
                    )
                )
            except (KeyError, ValueError) as e:
                # Log but continue with other screenshots
                continue

        return screenshots

    def health_check(self) -> bool:
        """
        Check if Pixcap API is available and API key is valid.

        Returns:
            True if healthy, False otherwise.
        """
        try:
            # Make a minimal request to verify API key
            headers = {
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
            }
            response = requests.get(
                f"{self.BASE_URL}/health",
                headers=headers,
                timeout=10,
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
