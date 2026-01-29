"""Command-line interface for VisualQE."""

import argparse
import os
import sys
from pathlib import Path


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="visualqe",
        description="Visual regression testing with LLM-powered analysis",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # capture command
    capture_parser = subparsers.add_parser(
        "capture", help="Capture a screenshot"
    )
    capture_parser.add_argument("url", help="URL to capture")
    capture_parser.add_argument(
        "-o", "--output", default="screenshot.png", help="Output file path"
    )
    capture_parser.add_argument(
        "--width", type=int, default=1920, help="Viewport width"
    )
    capture_parser.add_argument(
        "--height", type=int, default=1080, help="Viewport height"
    )
    capture_parser.add_argument(
        "--full-page", action="store_true", help="Capture full page"
    )
    capture_parser.add_argument(
        "--vpn", action="store_true", help="Use VPN connector"
    )

    # compare command
    compare_parser = subparsers.add_parser(
        "compare", help="Compare a screenshot against baseline"
    )
    compare_parser.add_argument("name", help="Baseline name")
    compare_parser.add_argument("url", help="URL to capture and compare")
    compare_parser.add_argument(
        "--baseline-dir", default="./baselines", help="Baseline directory"
    )
    compare_parser.add_argument(
        "--report", default=None, help="Output HTML report path"
    )
    compare_parser.add_argument(
        "--no-analysis", action="store_true", help="Skip VLM analysis"
    )

    # list command
    list_parser = subparsers.add_parser(
        "list", help="List saved baselines"
    )
    list_parser.add_argument(
        "--baseline-dir", default="./baselines", help="Baseline directory"
    )
    list_parser.add_argument(
        "--branch", default=None, help="Branch name"
    )

    # estimate command
    estimate_parser = subparsers.add_parser(
        "estimate", help="Estimate costs for comparisons"
    )
    estimate_parser.add_argument(
        "count", type=int, help="Number of comparisons"
    )
    estimate_parser.add_argument(
        "--no-analysis", action="store_true", help="Without VLM analysis"
    )

    # health command
    subparsers.add_parser("health", help="Check service health")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "capture":
        return cmd_capture(args)
    elif args.command == "compare":
        return cmd_compare(args)
    elif args.command == "list":
        return cmd_list(args)
    elif args.command == "estimate":
        return cmd_estimate(args)
    elif args.command == "health":
        return cmd_health()

    return 0


def cmd_capture(args: argparse.Namespace) -> int:
    """Handle capture command."""
    from visualqe import VisualQE

    api_key = os.environ.get("PIXCAP_API_KEY")
    if not api_key:
        print("Error: PIXCAP_API_KEY environment variable not set", file=sys.stderr)
        return 1

    vqe = VisualQE(pixcap_api_key=api_key)

    print(f"Capturing {args.url}...")
    try:
        screenshot = vqe.capture(
            url=args.url,
            viewport_width=args.width,
            viewport_height=args.height,
            full_page=args.full_page,
            use_vpn_connector=args.vpn,
        )

        output_path = Path(args.output)
        screenshot.save(output_path)
        print(f"Saved to {output_path}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_compare(args: argparse.Namespace) -> int:
    """Handle compare command."""
    from visualqe import VisualQE
    from visualqe.reporting.html import HTMLReporter

    pixcap_key = os.environ.get("PIXCAP_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    if not pixcap_key:
        print("Error: PIXCAP_API_KEY environment variable not set", file=sys.stderr)
        return 1

    vqe = VisualQE(
        pixcap_api_key=pixcap_key,
        gemini_api_key=gemini_key,
        baseline_dir=args.baseline_dir,
    )

    print(f"Capturing {args.url}...")
    try:
        screenshot = vqe.capture(args.url)

        if not vqe.baseline_exists(args.name):
            print(f"Baseline '{args.name}' not found. Creating it...")
            vqe.save_baseline(args.name, screenshot)
            print(f"Baseline saved. Run again to compare.")
            return 0

        print(f"Comparing against baseline '{args.name}'...")
        result = vqe.compare(
            args.name,
            screenshot,
            analyze=not args.no_analysis and gemini_key is not None,
        )

        # Print results
        if result.has_changes:
            print(f"\n❌ CHANGES DETECTED ({result.diff_percentage:.2%} diff)")
            if result.analysis:
                print(f"\nAnalysis: {result.analysis.summary}")
                for change in result.analysis.changes:
                    print(f"  - [{change.severity.value}] {change.type.value}: {change.element}")
        else:
            print(f"\n✅ NO CHANGES ({result.diff_percentage:.4%} diff)")

        # Generate report if requested
        if args.report:
            reporter = HTMLReporter()
            reporter.generate([result], Path(args.report))
            print(f"\nReport saved to {args.report}")

        return 1 if result.has_changes else 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_list(args: argparse.Namespace) -> int:
    """Handle list command."""
    from visualqe.baseline.local import LocalBaselineStorage

    storage = LocalBaselineStorage(args.baseline_dir)

    baselines = storage.list_all(args.branch)

    if not baselines:
        print("No baselines found.")
        return 0

    print(f"Baselines in {args.baseline_dir}:")
    for name in baselines:
        try:
            meta = storage.get_metadata(name, args.branch)
            print(f"  - {name}")
            print(f"      URL: {meta.get('url', 'unknown')}")
            print(f"      Captured: {meta.get('captured_at', 'unknown')}")
        except Exception:
            print(f"  - {name} (metadata unavailable)")

    return 0


def cmd_estimate(args: argparse.Namespace) -> int:
    """Handle estimate command."""
    from visualqe import VisualQE

    costs = VisualQE.estimate_cost(
        num_comparisons=args.count,
        include_analysis=not args.no_analysis,
    )

    print(f"Cost estimate for {args.count} comparisons:")
    print(f"  Pixcap screenshots: ${costs['pixcap_screenshots']:.2f}")
    print(f"  Gemini analysis:    ${costs['gemini_analysis']:.2f}")
    print(f"  ─────────────────────────")
    print(f"  Total:              ${costs['total']:.2f}")

    return 0


def cmd_health() -> int:
    """Handle health command."""
    from visualqe import VisualQE

    pixcap_key = os.environ.get("PIXCAP_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    vqe = VisualQE(
        pixcap_api_key=pixcap_key,
        gemini_api_key=gemini_key,
    )

    status = vqe.health_check()

    print("VisualQE Health Check")
    print("─" * 30)

    for key, value in status.items():
        icon = "✅" if value else "❌"
        print(f"  {icon} {key}: {value}")

    all_healthy = all(status.values())
    return 0 if all_healthy else 1


if __name__ == "__main__":
    sys.exit(main())
