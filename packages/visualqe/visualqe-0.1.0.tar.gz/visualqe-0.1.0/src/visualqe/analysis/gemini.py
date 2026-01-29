"""Google Gemini VLM provider implementation."""

import json
import re
from typing import Any, Optional

from PIL import Image

from visualqe.analysis.base import VLMProvider
from visualqe.analysis.prompts import (
    ACCESSIBILITY_PROMPT,
    COMPARISON_PROMPT,
    INTENT_VALIDATION_PROMPT,
    SINGLE_IMAGE_ANALYSIS_PROMPT,
)
from visualqe.exceptions import AnalysisError, AuthenticationError
from visualqe.models import Analysis, Change, ChangeType, Severity


class GeminiProvider(VLMProvider):
    """VLM provider using Google Gemini API."""

    DEFAULT_MODEL = "gemini-2.0-flash"
    FALLBACK_MODEL = "gemini-1.5-flash"

    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_retries: int = 3,
    ):
        """
        Initialize Gemini provider.

        Args:
            api_key: Google AI API key.
            model: Model to use (defaults to gemini-2.5-flash).
            temperature: Generation temperature (lower = more deterministic).
            max_retries: Maximum retry attempts for transient failures.
        """
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai package is required. "
                "Install with: pip install google-generativeai"
            )

        self._genai = genai
        genai.configure(api_key=api_key)

        self.model_name = model or self.DEFAULT_MODEL
        self.temperature = temperature
        self.max_retries = max_retries

        # Initialize model
        self._model = genai.GenerativeModel(
            self.model_name,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                response_mime_type="application/json",
            ),
        )

    def _parse_json_response(self, text: str) -> dict[str, Any]:
        """Parse JSON from model response, handling common issues."""
        # Remove markdown code fences if present
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        # Try to parse JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            json_match = re.search(r"\{[\s\S]*\}", text)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            raise AnalysisError(f"Failed to parse JSON from response: {text[:500]}")

    def _call_model(
        self,
        prompt: str,
        images: list[Image.Image],
    ) -> dict[str, Any]:
        """Make a model call with retry logic."""
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                # Build content with images
                content = [prompt]
                for img in images:
                    content.append(img)

                response = self._model.generate_content(content)

                # Check for blocked response
                if not response.text:
                    if response.prompt_feedback:
                        raise AnalysisError(
                            f"Response blocked: {response.prompt_feedback}"
                        )
                    raise AnalysisError("Empty response from model")

                return self._parse_json_response(response.text)

            except self._genai.types.BlockedPromptException as e:
                raise AnalysisError(f"Prompt blocked by safety filters: {e}")
            except self._genai.types.StopCandidateException as e:
                raise AnalysisError(f"Generation stopped: {e}")
            except Exception as e:
                error_str = str(e).lower()
                if "api key" in error_str or "authentication" in error_str:
                    raise AuthenticationError(
                        "Invalid Gemini API key. Check your GEMINI_API_KEY."
                    )
                last_error = e
                if attempt < self.max_retries - 1:
                    continue
                raise AnalysisError(
                    f"Gemini API call failed after {self.max_retries} attempts: {e}"
                ) from last_error

        raise AnalysisError(f"Unexpected error: {last_error}")

    def analyze_comparison(
        self,
        baseline: Image.Image,
        current: Image.Image,
    ) -> Analysis:
        """
        Analyze visual differences between two images.

        Args:
            baseline: The baseline/reference image.
            current: The current image to compare.

        Returns:
            Analysis object with summary and detected changes.
        """
        data = self._call_model(
            COMPARISON_PROMPT,
            [baseline, current],
        )

        changes = []
        for c in data.get("changes", []):
            try:
                changes.append(
                    Change(
                        type=ChangeType(c.get("type", "modification")),
                        element=c.get("element", "Unknown element"),
                        location=c.get("location", "Unknown location"),
                        severity=Severity(c.get("severity", "minor")),
                        confidence=float(c.get("confidence", 0.5)),
                        description=c.get("description", ""),
                    )
                )
            except (ValueError, KeyError):
                # Skip malformed changes
                continue

        return Analysis(
            summary=data.get("summary", "Analysis completed."),
            changes=changes,
            raw_response=json.dumps(data),
        )

    def validate_intent(
        self,
        baseline: Image.Image,
        current: Image.Image,
        intent: str,
    ) -> tuple[bool, float, str]:
        """
        Validate whether an intended change was implemented.

        Args:
            baseline: The baseline/reference image (before).
            current: The current image (after).
            intent: Description of the intended change.

        Returns:
            Tuple of (validated: bool, confidence: float, explanation: str).
        """
        prompt = INTENT_VALIDATION_PROMPT.format(intent=intent)

        data = self._call_model(prompt, [baseline, current])

        validated = bool(data.get("validated", False))
        confidence = float(data.get("confidence", 0.5))
        explanation = data.get("explanation", "")

        # Include observed change and side effects in explanation if present
        observed = data.get("observed_change")
        side_effects = data.get("side_effects", [])

        if observed:
            explanation += f"\n\nObserved change: {observed}"
        if side_effects:
            explanation += f"\n\nSide effects: {', '.join(side_effects)}"

        return validated, confidence, explanation

    def analyze_accessibility(
        self,
        image: Image.Image,
    ) -> dict[str, Any]:
        """
        Analyze an image for accessibility issues.

        Args:
            image: The image to analyze.

        Returns:
            Dictionary containing accessibility analysis results.
        """
        return self._call_model(ACCESSIBILITY_PROMPT, [image])

    def analyze_single_image(
        self,
        image: Image.Image,
    ) -> dict[str, Any]:
        """
        Analyze a single image for general understanding.

        Args:
            image: The image to analyze.

        Returns:
            Dictionary containing image analysis results.
        """
        return self._call_model(SINGLE_IMAGE_ANALYSIS_PROMPT, [image])

    def custom_analysis(
        self,
        images: list[Image.Image],
        prompt: str,
    ) -> dict[str, Any]:
        """
        Run a custom analysis with user-provided prompt.

        Args:
            images: List of images to analyze.
            prompt: Custom analysis prompt (should request JSON output).

        Returns:
            Parsed JSON response from the model.
        """
        return self._call_model(prompt, images)

    def health_check(self) -> bool:
        """
        Check if Gemini API is available.

        Returns:
            True if healthy, False otherwise.
        """
        try:
            # Create a simple test image
            test_image = Image.new("RGB", (100, 100), color="white")
            self._model.generate_content(
                ["Respond with just: {\"status\": \"ok\"}", test_image]
            )
            return True
        except Exception:
            return False
