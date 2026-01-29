#!/usr/bin/env python3
"""CLI entry point for chronically-needs-csv."""

import sys
import json
import argparse
from . import convert, _get_chronis_message, __version__


def main():
    parser = argparse.ArgumentParser(
        prog="chronically-needs-csv",
        description="Convert JSON to CSV. For Konstantinos, with love.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  chronically-needs-csv data.json              # Creates data.csv
  chronically-needs-csv data.json output.csv   # Creates output.csv
  chronically-needs-csv data.json -d "|"       # Use | to join arrays

Dedicated to Konstantinos Chronis, the analyst with mass amounts of Chronos
but mysteriously no time to learn json.load().
        """
    )
    parser.add_argument("input", help="Input JSON file")
    parser.add_argument("output", nargs="?", help="Output CSV file (default: input.csv)")
    parser.add_argument(
        "-d", "--array-delimiter",
        default=", ",
        help="Delimiter for joining array values (default: ', ')"
    )
    parser.add_argument(
        "-s", "--silent",
        action="store_true",
        help="Skip the friendly message (no fun allowed mode)"
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    args = parser.parse_args()

    try:
        output_file = convert(args.input, args.output, args.array_delimiter, args.silent)

        if not args.silent:
            print(f"\n  {_get_chronis_message()}\n")

        print(f"  {args.input} → {output_file}\n")

    except FileNotFoundError:
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON (even Konstantinos could spot this one): {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
