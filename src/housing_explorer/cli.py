"""Command-line entry point: ``housing-explorer clean`` and ``housing-explorer summary``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .ingest import SchemaError, load_sales
from .stats import summarize_by_zip


def _cmd_clean(args: argparse.Namespace) -> int:
    df, report = load_sales(args.input)
    print(f"rows in: {report.rows_in}  rows kept: {report.rows_out}")
    for reason, count in sorted(report.dropped.items()):
        print(f"  dropped {count:>6}  {reason}")
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(args.output, index=False)
        print(f"wrote {args.output}")
    return 0


def _cmd_summary(args: argparse.Namespace) -> int:
    df, _ = load_sales(args.input)
    print(summarize_by_zip(df, min_sales=args.min_sales).to_string())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="housing-explorer")
    sub = parser.add_subparsers(dest="command", required=True)

    clean = sub.add_parser("clean", help="clean a raw sales CSV")
    clean.add_argument("input", help="path to raw CSV")
    clean.add_argument("-o", "--output", help="where to write the cleaned CSV")
    clean.set_defaults(func=_cmd_clean)

    summary = sub.add_parser("summary", help="median prices by ZIP code")
    summary.add_argument("input", help="path to raw CSV")
    summary.add_argument("--min-sales", type=int, default=3)
    summary.set_defaults(func=_cmd_summary)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, SchemaError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
