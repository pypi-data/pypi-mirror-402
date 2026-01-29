"""Command-line interface for marc-lint."""

import json
import sys
from pathlib import Path
from typing import List

from pymarc import MARCReader

from .linter import MarcLint, RecordResult


def main() -> None:
    """Main CLI entry point for marc-lint.

    Exit codes:
        0 - No warnings found
        1 - Warnings found or usage error
        2 - Error reading file
    """
    # Parse arguments manually for simplicity (no external dependencies)
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        _print_usage()
        sys.exit(0 if args else 1)

    # Parse options
    output_format = "text"
    quiet = False
    use_index = False
    filepath = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("-f", "--format"):
            if i + 1 >= len(args):
                print(
                    "Error: --format requires an argument (text or json)",
                    file=sys.stderr,
                )
                sys.exit(1)
            output_format = args[i + 1]
            if output_format not in ("text", "json"):
                print(
                    f"Error: Invalid format '{output_format}'. Use 'text' or 'json'.",
                    file=sys.stderr,
                )
                sys.exit(1)
            i += 2
        elif arg in ("-q", "--quiet"):
            quiet = True
            i += 1
        elif arg in ("-i", "--use-index"):
            use_index = True
            i += 1
        elif arg.startswith("-"):
            print(f"Error: Unknown option '{arg}'", file=sys.stderr)
            _print_usage()
            sys.exit(1)
        else:
            filepath = Path(arg)
            i += 1

    if filepath is None:
        print("Error: No file specified.", file=sys.stderr)
        _print_usage()
        sys.exit(1)

    if not filepath.exists():
        print(f"Error: File '{filepath}' not found.", file=sys.stderr)
        sys.exit(2)

    # Read and process records
    try:
        with open(filepath, "rb") as fh:
            reader = MARCReader(fh)
            records = list(reader)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(2)

    if not records:
        if output_format == "json":
            print("[]")
        elif not quiet:
            print("No records found in file.")
        sys.exit(0)

    # Lint all records
    linter = MarcLint()
    results = linter.check_records(records, use_index_as_id=use_index)

    total_warnings = sum(len(r.warnings) for r in results)
    records_with_warnings = sum(1 for r in results if not r.is_valid)

    # Output results
    if output_format == "json":
        _output_json(results)
    else:
        _output_text(results)
        if not quiet:
            print("=" * 60)
            print(f"Processed {len(results)} record(s)")
            print(
                f"Found {total_warnings} warning(s) in {records_with_warnings} record(s)"
            )
            if total_warnings == 0:
                print("\n✓ No validation warnings found!")

    sys.exit(1 if total_warnings > 0 else 0)


def _print_usage() -> None:
    """Print usage information."""
    print("Usage: marc-lint [OPTIONS] <file.mrc>")
    print("\nLint MARC21 records and report validation warnings.")
    print("\nOptions:")
    print("  -f, --format FORMAT   Output format: text (default) or json")
    print("  -q, --quiet           Only output warnings, no summary")
    print("  -i, --use-index       Use record index as ID when 001 field is missing")
    print("  -h, --help            Show this help message")
    print("\nExit codes:")
    print("  0  No warnings found")
    print("  1  Warnings found")
    print("  2  Error reading file")


def _output_text(results: List[RecordResult]) -> None:
    """Output results in text format."""
    for result in results:
        if result.warnings:
            print(f"\n--- Record {result.record_id} ---")
            for warning in result.warnings:
                # Format: field (position if applicable): message
                field_str = warning.field
                if warning.position is not None:
                    field_str = f"{field_str} (occurrence {warning.position + 1})"
                if warning.subfield:
                    print(
                        f"  {field_str}: Subfield {warning.subfield} {warning.message}"
                    )
                else:
                    print(f"  {field_str}: {warning.message}")


def _output_json(results: List[RecordResult]) -> None:
    """Output results in JSON format."""
    output = []
    for result in results:
        record_data = {
            "record_id": result.record_id,
            "is_valid": result.is_valid,
            "warnings": [w.to_dict() for w in result.warnings],
        }
        output.append(record_data)

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
