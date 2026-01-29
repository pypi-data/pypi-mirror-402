import argparse
import json
from pathlib import Path

from .checker import Checker
from .reporter import Reporter


def main():
    parser = argparse.ArgumentParser(
        description="EnvHealth – Python Environment Health Diagnostics"
    )

    parser.add_argument("--json", action="store_true", help="Save JSON report")
    parser.add_argument("--html", action="store_true", help="Save HTML report")
    parser.add_argument("--pdf", action="store_true", help="Save PDF report")
    parser.add_argument("--path", help="Custom path to save reports")
    parser.add_argument("--fail-on", choices=["minor", "major"], help="CI exit control")

    args = parser.parse_args()

    checker = Checker()
    data = checker.full_report()
    reporter = Reporter(data)

    save_path = Path(args.path) if args.path else None

    if args.json:
        reporter.save_json(save_path)
        print(json.dumps(data, indent=2))

    if args.html:
        reporter.save_html(save_path)

    if args.pdf:
        reporter.save_pdf(save_path)

    if not args.json and not args.html and not args.pdf:
        print(reporter.pretty_text())

    raise SystemExit(checker.exit_code(args.fail_on))
