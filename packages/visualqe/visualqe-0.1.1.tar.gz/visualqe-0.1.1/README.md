# VisualQE

Visual regression testing with LLM-powered semantic analysis.

VisualQE combines traditional pixel-based visual regression testing with Visual Language Models (VLMs) to provide:

- **Reliable change detection** via SSIM and pixel diff algorithms
- **Semantic analysis** that explains *what* changed in human terms
- **Intent validation** to verify if intended changes were implemented
- **Internal environment testing** via Pixcap VPN connector

## Installation

```bash
pip install visualqe
```

Or with development dependencies:

```bash
pip install visualqe[dev]
```

## Quick Start

### Basic Usage

```python
from visualqe import VisualQE

# Initialize with API keys (or set PIXCAP_API_KEY and GEMINI_API_KEY env vars)
vqe = VisualQE(
    pixcap_api_key="your-pixcap-key",
    gemini_api_key="your-gemini-key",  # Optional, for AI analysis
)

# Capture and save a baseline
screenshot = vqe.capture("https://example.com")
vqe.save_baseline("homepage", screenshot)

# Later, compare against the baseline
new_screenshot = vqe.capture("https://example.com")
result = vqe.compare("homepage", new_screenshot)

# Check results
print(f"Changes detected: {result.has_changes}")
print(f"Diff percentage: {result.diff_percentage:.2%}")

# AI analysis (if Gemini key provided)
if result.analysis:
    print(f"Summary: {result.analysis.summary}")
    for change in result.analysis.changes:
        print(f"  - {change.type.value}: {change.element}")
```

### Intent Validation

Verify that intended changes were implemented:

```python
result = vqe.compare(
    "checkout-page",
    new_screenshot,
    intent="The 'Buy Now' button should now be green instead of blue"
)

if result.intent_validated:
    print("Change implemented correctly!")
else:
    print(f"Issue: {result.intent_explanation}")
```

### Internal/Staging Environments

Use the VPN connector to test internal applications:

```python
# Capture internal dashboard (requires Pixcap VPN connector setup)
screenshot = vqe.capture(
    "https://internal.company.com/dashboard",
    use_vpn_connector=True,
)
```

### pytest Integration

```python
# test_visual.py
def test_homepage_visual(visual_check):
    """Test that homepage hasn't changed visually."""
    visual_check("homepage", "https://example.com")

def test_login_page(visual_check):
    """Test login page with intent validation."""
    visual_check(
        "login",
        "https://example.com/login",
        intent="Login form should show 'Remember me' checkbox",
    )
```

Run tests:

```bash
# Set environment variables
export PIXCAP_API_KEY="your-key"
export GEMINI_API_KEY="your-key"  # Optional

# Run visual tests
pytest tests/visual/ --visual-report=./reports/visual.html

# Update baselines (when changes are intentional)
pytest tests/visual/ --visual-update-baselines
```

### CLI Usage

```bash
# Capture a screenshot
visualqe capture https://example.com -o screenshot.png

# Compare against baseline
visualqe compare homepage https://example.com --report report.html

# List baselines
visualqe list --baseline-dir ./baselines

# Estimate costs
visualqe estimate 100

# Health check
visualqe health
```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `PIXCAP_API_KEY` | Pixcap API key for screenshot capture |
| `GEMINI_API_KEY` | Google Gemini API key for AI analysis |

### pytest Options

| Option | Description |
|--------|-------------|
| `--visual-baseline-dir` | Directory for baselines (default: `./baselines`) |
| `--visual-report` | Path for HTML report |
| `--visual-report-json` | Path for JSON report |
| `--visual-update-baselines` | Update baselines instead of comparing |
| `--visual-threshold` | Diff threshold (default: 0.01 = 1%) |
| `--visual-skip-analysis` | Skip VLM analysis |
| `--visual-branch` | Branch name for baseline versioning |

## Features

### Screenshot Capture

- Public and internal URL support
- Configurable viewport (320-3840px width)
- Full-page capture
- Cookie injection for authenticated pages
- Element blocking via CSS selectors
- Dark mode emulation

### Diff Algorithms

- **Pixel diff**: Fast, precise pixel-by-pixel comparison
- **SSIM**: Perceptual similarity aligned with human vision
- **Combined**: SSIM for detection, pixel for visualization (default)

### VLM Analysis

- Natural language change summaries
- Structured change detection with severity levels
- Intent validation for intentional changes
- Accessibility analysis

### Reporting

- HTML reports with side-by-side comparison
- JSON output for CI/CD integration
- Diff visualization

## API Reference

### VisualQE

Main class for visual regression testing.

```python
vqe = VisualQE(
    pixcap_api_key: str = None,      # Pixcap API key
    gemini_api_key: str = None,      # Gemini API key
    baseline_dir: str = "./baselines",
    diff_threshold: float = 0.01,    # 1% threshold
)
```

#### Methods

- `capture(url, **kwargs)` - Capture a screenshot
- `save_baseline(name, screenshot)` - Save as baseline
- `compare(name, screenshot, **kwargs)` - Compare against baseline
- `capture_and_compare(name, url, **kwargs)` - Capture and compare in one call
- `analyze_accessibility(screenshot)` - Analyze for accessibility issues

### ComparisonResult

Result from a comparison.

```python
result.has_changes        # bool: Whether changes were detected
result.diff_percentage    # float: Percentage of pixels changed
result.diff_image         # PIL.Image: Visual diff
result.analysis           # Analysis: VLM analysis (if enabled)
result.intent_validated   # bool: Whether intent was validated
result.intent_explanation # str: Explanation of validation
result.to_json()          # str: JSON representation
```

## Cost Estimation

Approximate costs per 1,000 comparisons:

| Component | Cost |
|-----------|------|
| Pixcap screenshots (2 per comparison) | ~$10-20 |
| Gemini analysis | ~$2-5 |
| **Total** | **~$12-25** |

Use `VisualQE.estimate_cost(num_comparisons)` or `visualqe estimate <count>` for estimates.

## Architecture

```
visualqe/
├── capture/          # Screenshot providers (Pixcap)
├── diff/             # Diff algorithms (Pixel, SSIM)
├── analysis/         # VLM providers (Gemini)
├── baseline/         # Baseline storage (Local)
├── reporting/        # Report generators (HTML, JSON)
├── core.py           # Main VisualQE class
└── pytest_plugin.py  # pytest integration
```

## Development

```bash
# Clone and install
git clone https://github.com/yourorg/visualqe
cd visualqe
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/visualqe

# Linting
ruff check src/
ruff format src/
```

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- [Pixcap.dev](https://pixcap.dev) for screenshot API
- [Google Gemini](https://ai.google.dev) for VLM capabilities
- Inspired by [Applitools](https://applitools.com) and [Percy](https://percy.io)
