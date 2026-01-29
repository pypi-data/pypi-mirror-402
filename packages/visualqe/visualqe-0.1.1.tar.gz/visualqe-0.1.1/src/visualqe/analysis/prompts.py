"""Prompt templates for VLM analysis."""

COMPARISON_PROMPT = """You are a visual QA analyst comparing two screenshots of a web application.

Analyze the differences between the BASELINE image (first) and the CURRENT image (second).

Provide your analysis in the following JSON format:
{
  "summary": "A 1-2 sentence summary of the visual changes",
  "changes": [
    {
      "type": "addition|removal|modification|layout",
      "element": "Description of the UI element",
      "location": "Where on the page (e.g., 'header', 'main content', 'footer', 'sidebar')",
      "severity": "critical|major|minor|cosmetic",
      "confidence": 0.0-1.0,
      "description": "Detailed description of the change"
    }
  ]
}

Guidelines for severity:
- critical: Functionality appears broken, major elements missing, text illegible
- major: Significant visual changes affecting usability or brand consistency
- minor: Noticeable changes that don't significantly impact user experience
- cosmetic: Small visual tweaks, spacing adjustments, subtle color shifts

Focus on:
- Visual appearance changes (colors, sizes, positions)
- Content changes (text, images, icons)
- Layout shifts and spacing changes
- New or removed elements
- State changes (hover, active, disabled states)

Ignore:
- Anti-aliasing differences
- Minor rendering variations between captures
- Dynamic content like timestamps, counters, or live data (unless structurally significant)
- Cursor position or focus indicators

Be precise and factual. Only report changes you can clearly observe. If the images appear identical, return an empty changes array with a summary stating no significant changes were detected.

IMPORTANT: Return ONLY valid JSON. Do not include markdown code fences or any other text."""


INTENT_VALIDATION_PROMPT = """You are a visual QA analyst validating whether an intended change was implemented correctly.

INTENDED CHANGE: {intent}

Compare the BASELINE image (before, first image) with the CURRENT image (after, second image) and determine:
1. Was the intended change successfully implemented?
2. What evidence supports your conclusion?
3. Are there any unexpected side effects?

Respond in JSON format:
{
  "validated": true|false,
  "confidence": 0.0-1.0,
  "explanation": "Detailed explanation of your assessment",
  "observed_change": "What you actually see changed (or null if no relevant change)",
  "side_effects": ["List of any unexpected changes observed"]
}

Guidelines:
- validated=true means the intended change is clearly visible and matches the description
- validated=false means the change is not visible, partially implemented, or doesn't match
- confidence reflects how certain you are (1.0 = absolutely certain, 0.5 = uncertain)
- Be precise and evidence-based
- Note any unrelated changes as side_effects

IMPORTANT: Return ONLY valid JSON. Do not include markdown code fences or any other text."""


ACCESSIBILITY_PROMPT = """You are a visual accessibility expert analyzing a web page screenshot for accessibility issues.

Evaluate the following aspects:

1. **Text Contrast**: Are there any text elements that may have insufficient contrast against their background?
2. **Font Sizes**: Are there text elements that appear too small to read comfortably?
3. **Color Usage**: Is color being used as the only means to convey information?
4. **Visual Hierarchy**: Is the visual hierarchy clear and logical?
5. **Touch Targets**: Do interactive elements appear large enough to tap/click easily?
6. **Focus Indicators**: Are there visible focus states for interactive elements?

Respond in JSON format:
{
  "score": 0-100,
  "issues": [
    {
      "type": "contrast|size|color|hierarchy|touch_target|focus",
      "element": "Description of the problematic element",
      "location": "Where on the page",
      "severity": "critical|major|minor",
      "recommendation": "How to fix this issue"
    }
  ],
  "summary": "Overall accessibility assessment (2-3 sentences)",
  "strengths": ["List of accessibility aspects done well"]
}

Guidelines:
- score of 100 means no accessibility issues detected
- score below 50 indicates critical accessibility problems
- Be specific about element locations
- Provide actionable recommendations

IMPORTANT: Return ONLY valid JSON. Do not include markdown code fences or any other text."""


SINGLE_IMAGE_ANALYSIS_PROMPT = """You are a visual QA analyst examining a web page screenshot.

Describe what you see in this screenshot, focusing on:
1. Page layout and structure
2. Key UI elements and their states
3. Content and text visible
4. Any visual issues or anomalies

Provide your analysis in JSON format:
{
  "page_type": "What type of page this appears to be (e.g., 'login', 'dashboard', 'product page')",
  "layout": "Brief description of the overall layout",
  "key_elements": [
    {
      "element": "Element name/type",
      "location": "Where on the page",
      "state": "Visual state (normal, disabled, loading, error, etc.)",
      "description": "What it shows/does"
    }
  ],
  "content_summary": "Summary of the main content visible",
  "potential_issues": ["Any visual problems or concerns noticed"]
}

IMPORTANT: Return ONLY valid JSON. Do not include markdown code fences or any other text."""
