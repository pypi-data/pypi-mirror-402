"""HTML report generation."""

import base64
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image

from visualqe.models import BatchResult, ComparisonResult


def _image_to_data_uri(img: Image.Image, max_width: int = 800) -> str:
    """Convert PIL Image to base64 data URI."""
    # Resize if too large
    if img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    buffered = BytesIO()
    img.save(buffered, format="PNG", optimize=True)
    encoded = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{encoded}"


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VisualQE Report - {title}</title>
    <style>
        :root {{
            --color-pass: #22c55e;
            --color-fail: #ef4444;
            --color-warning: #f59e0b;
            --color-bg: #f8fafc;
            --color-card: #ffffff;
            --color-border: #e2e8f0;
            --color-text: #1e293b;
            --color-text-muted: #64748b;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            margin: 0;
            padding: 2rem;
            background: var(--color-bg);
            color: var(--color-text);
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        h1, h2, h3, h4 {{
            margin: 0 0 1rem 0;
        }}

        .header {{
            background: var(--color-card);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}

        .header h1 {{
            margin-bottom: 0.5rem;
        }}

        .header .meta {{
            color: var(--color-text-muted);
            font-size: 0.9rem;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-top: 1.5rem;
        }}

        .stat {{
            text-align: center;
            padding: 1rem;
            background: var(--color-bg);
            border-radius: 8px;
        }}

        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
        }}

        .stat-label {{
            font-size: 0.85rem;
            color: var(--color-text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .stat.passed .stat-value {{ color: var(--color-pass); }}
        .stat.failed .stat-value {{ color: var(--color-fail); }}

        .comparison {{
            background: var(--color-card);
            border-radius: 12px;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .comparison-header {{
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--color-border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .comparison-header h3 {{
            margin: 0;
            font-size: 1rem;
        }}

        .comparison.passed {{
            border-left: 4px solid var(--color-pass);
        }}

        .comparison.failed {{
            border-left: 4px solid var(--color-fail);
        }}

        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .badge.passed {{
            background: #dcfce7;
            color: #166534;
        }}

        .badge.failed {{
            background: #fee2e2;
            color: #991b1b;
        }}

        .comparison-body {{
            padding: 1.5rem;
        }}

        .images {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}

        .image-card {{
            border: 1px solid var(--color-border);
            border-radius: 8px;
            overflow: hidden;
        }}

        .image-card h4 {{
            margin: 0;
            padding: 0.75rem 1rem;
            background: var(--color-bg);
            font-size: 0.85rem;
            border-bottom: 1px solid var(--color-border);
        }}

        .image-card img {{
            width: 100%;
            height: auto;
            display: block;
        }}

        .analysis {{
            background: var(--color-bg);
            border-radius: 8px;
            padding: 1rem;
            margin-top: 1rem;
        }}

        .analysis h4 {{
            margin: 0 0 0.75rem 0;
            font-size: 0.9rem;
        }}

        .analysis p {{
            margin: 0 0 1rem 0;
        }}

        .changes-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}

        .change-item {{
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            background: var(--color-card);
            border-radius: 6px;
            border-left: 3px solid var(--color-border);
        }}

        .change-item.critical {{ border-left-color: var(--color-fail); }}
        .change-item.major {{ border-left-color: #f97316; }}
        .change-item.minor {{ border-left-color: var(--color-warning); }}
        .change-item.cosmetic {{ border-left-color: var(--color-text-muted); }}

        .change-type {{
            font-weight: 600;
            text-transform: capitalize;
        }}

        .change-meta {{
            font-size: 0.85rem;
            color: var(--color-text-muted);
            margin-top: 0.25rem;
        }}

        .intent-validation {{
            background: var(--color-bg);
            border-radius: 8px;
            padding: 1rem;
            margin-top: 1rem;
        }}

        .intent-validation.validated {{
            border-left: 4px solid var(--color-pass);
        }}

        .intent-validation.not-validated {{
            border-left: 4px solid var(--color-fail);
        }}

        .diff-percentage {{
            font-size: 0.85rem;
            color: var(--color-text-muted);
        }}

        @media (max-width: 768px) {{
            body {{
                padding: 1rem;
            }}

            .images {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>VisualQE Report</h1>
            <p class="meta">Generated: {timestamp}</p>
            <div class="summary">
                <div class="stat">
                    <div class="stat-value">{total}</div>
                    <div class="stat-label">Total</div>
                </div>
                <div class="stat passed">
                    <div class="stat-value">{passed}</div>
                    <div class="stat-label">Passed</div>
                </div>
                <div class="stat failed">
                    <div class="stat-value">{failed}</div>
                    <div class="stat-label">Failed</div>
                </div>
            </div>
        </div>

        {comparisons}
    </div>
</body>
</html>"""


COMPARISON_TEMPLATE = """
<div class="comparison {status_class}">
    <div class="comparison-header">
        <h3>{name}</h3>
        <div>
            <span class="diff-percentage">{diff_pct:.2f}% diff</span>
            <span class="badge {status_class}">{status_text}</span>
        </div>
    </div>
    <div class="comparison-body">
        <div class="images">
            <div class="image-card">
                <h4>Baseline</h4>
                <img src="{baseline_img}" alt="Baseline" loading="lazy" />
            </div>
            <div class="image-card">
                <h4>Current</h4>
                <img src="{current_img}" alt="Current" loading="lazy" />
            </div>
            {diff_img_html}
        </div>
        {analysis_html}
        {intent_html}
    </div>
</div>
"""


class HTMLReporter:
    """Generate HTML reports from comparison results."""

    def __init__(self, title: str = "Visual Regression Test"):
        """
        Initialize HTML reporter.

        Args:
            title: Title for the report.
        """
        self.title = title

    def generate(
        self,
        results: list[ComparisonResult],
        output_path: Path,
    ) -> Path:
        """
        Generate an HTML report from comparison results.

        Args:
            results: List of comparison results.
            output_path: Path to write the HTML report.

        Returns:
            Path to the generated report.
        """
        comparisons_html = []

        for result in results:
            comparisons_html.append(self._render_comparison(result))

        passed = sum(1 for r in results if not r.has_changes)
        failed = len(results) - passed

        html = HTML_TEMPLATE.format(
            title=self.title,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            total=len(results),
            passed=passed,
            failed=failed,
            comparisons="\n".join(comparisons_html),
        )

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html)

        return output_path

    def generate_from_batch(
        self,
        batch_result: BatchResult,
        output_path: Path,
    ) -> Path:
        """
        Generate an HTML report from a batch result.

        Args:
            batch_result: BatchResult containing multiple comparisons.
            output_path: Path to write the HTML report.

        Returns:
            Path to the generated report.
        """
        return self.generate(batch_result.results, output_path)

    def _render_comparison(self, result: ComparisonResult) -> str:
        """Render a single comparison result."""
        status_class = "failed" if result.has_changes else "passed"
        status_text = "Changes Detected" if result.has_changes else "Passed"

        # Render images
        baseline_img = _image_to_data_uri(result.baseline.image)
        current_img = _image_to_data_uri(result.current.image)

        diff_img_html = ""
        if result.diff_image and result.has_changes:
            diff_img = _image_to_data_uri(result.diff_image)
            diff_img_html = f"""
            <div class="image-card">
                <h4>Diff</h4>
                <img src="{diff_img}" alt="Diff" loading="lazy" />
            </div>
            """

        # Render analysis
        analysis_html = ""
        if result.analysis:
            changes_html = ""
            if result.analysis.changes:
                changes_items = []
                for change in result.analysis.changes:
                    changes_items.append(f"""
                    <li class="change-item {change.severity.value}">
                        <div class="change-type">{change.type.value}: {change.element}</div>
                        <div>{change.description}</div>
                        <div class="change-meta">Location: {change.location} | Severity: {change.severity.value} | Confidence: {change.confidence:.0%}</div>
                    </li>
                    """)
                changes_html = f'<ul class="changes-list">{"".join(changes_items)}</ul>'

            analysis_html = f"""
            <div class="analysis">
                <h4>AI Analysis</h4>
                <p>{result.analysis.summary}</p>
                {changes_html}
            </div>
            """

        # Render intent validation
        intent_html = ""
        if result.intent_explanation:
            validated_class = "validated" if result.intent_validated else "not-validated"
            validated_text = "Validated" if result.intent_validated else "Not Validated"
            intent_html = f"""
            <div class="intent-validation {validated_class}">
                <h4>Intent Validation: {validated_text}</h4>
                <p>{result.intent_explanation}</p>
            </div>
            """

        # Get name from URL or use a default
        name = result.baseline.url or "Comparison"

        return COMPARISON_TEMPLATE.format(
            name=name,
            status_class=status_class,
            status_text=status_text,
            diff_pct=result.diff_percentage * 100,
            baseline_img=baseline_img,
            current_img=current_img,
            diff_img_html=diff_img_html,
            analysis_html=analysis_html,
            intent_html=intent_html,
        )
