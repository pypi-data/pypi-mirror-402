# Copyright 2026 François TUMUSAVYEYESU.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Command Line Interface for Zenith Analyser.
"""

import argparse
import json
import sys
from typing import Optional

from . import ASTUnparser, Validator, ZenithAnalyser
from .exceptions import (
    ZenithAnalyserError,
    ZenithError,
    ZenithLexerError,
    ZenithParserError,
)


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    try:
        if args.command == "analyze":
            analyze_command(args)
        elif args.command == "validate":
            validate_command(args)
        elif args.command == "unparse":
            unparse_command(args)
        elif args.command == "convert":
            convert_command(args)
        elif args.command == "version":
            version_command()
        else:
            parser.print_help()
            sys.exit(1)

    except ZenithError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description="Zenith Analyser - Analyze structured temporal laws",
        epilog="See https://github.com/frasasu/zenith-analyser for more information.",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze Zenith code")
    analyze_parser.add_argument("input", help="Input file or - for stdin")
    analyze_parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    analyze_parser.add_argument(
        "--format",
        choices=["json", "yaml", "text"],
        default="json",
        help="Output format",
    )
    analyze_parser.add_argument("--law", help="Analyze specific law")
    analyze_parser.add_argument("--target", help="Analyze specific target")
    analyze_parser.add_argument(
        "--population", type=int, default=-1, help="Population level (-1 for max)"
    )
    analyze_parser.add_argument(
        "--pretty", action="store_true", help="Pretty print JSON output"
    )

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate Zenith code")
    validate_parser.add_argument("input", help="Input file or - for stdin")
    validate_parser.add_argument(
        "--strict", action="store_true", help="Treat warnings as errors"
    )

    # Unparse command
    unparse_parser = subparsers.add_parser("unparse", help="Convert AST to Zenith code")
    unparse_parser.add_argument("input", help="Input JSON file")
    unparse_parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    unparse_parser.add_argument(
        "--format", action="store_true", help="Format output code"
    )

    # Convert command
    convert_parser = subparsers.add_parser("convert", help="Convert between formats")
    convert_parser.add_argument("input", help="Input file")
    convert_parser.add_argument("output", help="Output file")
    convert_parser.add_argument(
        "--from",
        dest="from_format",
        choices=["zenith", "json"],
        default="zenith",
        help="Input format",
    )
    convert_parser.add_argument(
        "--to", choices=["zenith", "json"], default="json", help="Output format"
    )

    # Version command
    subparsers.add_parser("version", help="Show version information")

    return parser


def analyze_command(args: argparse.Namespace) -> None:
    """Handle analyze command."""
    code = read_input(args.input)

    try:
        analyser = ZenithAnalyser(code)

        if args.law:
            result = analyser.law_description(args.law, args.population)
        elif args.target:
            result = analyser.target_description(args.target)
        elif args.population != -1:
            result = analyser.population_description(args.population)
        else:
            result = analyser.analyze_corpus()

        output = format_output(result, args.format, args.pretty)
        write_output(output, args.output)

    except (ZenithLexerError, ZenithParserError, ZenithAnalyserError) as e:
        print(f"Analysis error: {e}", file=sys.stderr)
        sys.exit(1)


def validate_command(args: argparse.Namespace) -> None:
    """Handle validate command."""
    code = read_input(args.input)

    validator = Validator()
    errors = validator.validate_code(code)

    if errors:
        print(f"Validation failed with {len(errors)} error(s):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)

        if args.strict:
            sys.exit(1)
    else:
        print("✓ Validation passed", file=sys.stderr)

    warnings = validator.warnings
    if warnings:
        print(f"Found {len(warnings)} warning(s):", file=sys.stderr)
        for warning in warnings:
            print(f"  ⚠ {warning}", file=sys.stderr)


def unparse_command(args: argparse.Namespace) -> None:
    """Handle unparse command."""
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            ast = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Failed to read AST: {e}", file=sys.stderr)
        sys.exit(1)

    unparser = ASTUnparser(ast)
    code = unparser.unparse()

    if args.format:
        code = unparser.format_code(code)

    write_output(code, args.output)


def convert_command(args: argparse.Namespace) -> None:
    """Handle convert command."""
    if args.from_format == "zenith" and args.to == "json":
        code = read_input(args.input)
        analyser = ZenithAnalyser(code)
        result = analyser.analyze_corpus()

        try:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            print(f"✓ Converted to {args.output}", file=sys.stderr)
        except IOError as e:
            print(f"Failed to write output: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.from_format == "json" and args.to == "zenith":
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                ast = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Failed to read JSON: {e}", file=sys.stderr)
            sys.exit(1)

        unparser = ASTUnparser(ast)
        code = unparser.unparse()

        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(code)
            print(f"✓ Converted to {args.output}", file=sys.stderr)
        except IOError as e:
            print(f"Failed to write output: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        print(
            f"Conversion from {args.from_format} to {args.to} not supported",
            file=sys.stderr,
        )
        sys.exit(1)


def version_command() -> None:
    """Handle version command."""
    from . import __author__, __license__, __version__

    print(f"Zenith Analyser v{__version__}")
    print(f"Author: {__author__}")
    print(f"License: {__license__}")
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")


def read_input(input_spec: str) -> str:
    """Read input from file or stdin."""
    if input_spec == "-":
        return sys.stdin.read()
    else:
        try:
            with open(input_spec, "r", encoding="utf-8") as f:
                return f.read()
        except IOError as e:
            print(f"Failed to read input: {e}", file=sys.stderr)
            sys.exit(1)


def write_output(output: str, output_spec: Optional[str]) -> None:
    """Write output to file or stdout."""
    if output_spec:
        try:
            with open(output_spec, "w", encoding="utf-8") as f:
                f.write(output)
        except IOError as e:
            print(f"Failed to write output: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        sys.stdout.write(output)


def format_output(result: dict, format_type: str, pretty: bool) -> str:
    """Format output according to specified format."""
    if format_type == "json":
        indent = 2 if pretty else None
        return json.dumps(result, indent=indent, default=str)
    elif format_type == "yaml":
        try:
            import yaml

            return yaml.dump(result, default_flow_style=False)
        except ImportError:
            print(
                "YAML format requires PyYAML. Install with: pip install pyyaml",
                file=sys.stderr,
            )
            sys.exit(1)
    else:  # text format
        return format_text_output(result)


def format_text_output(result: dict) -> str:
    """Format result as human-readable text."""
    lines = []

    if "name" in result:
        lines.append(f"Name: {result['name']}")
        lines.append(
            f"Start: {result.get('start_datetime', {}).get('date', 'N/A')} "
            f"at {result.get('start_datetime', {}).get('time', 'N/A')}"
        )
        lines.append(f"Duration: {result.get('total_duration_minutes', 0)} minutes")
        lines.append(f"Events: {result.get('event_count', 0)}")
        lines.append("")

        if "simulation" in result:
            lines.append("Event Simulation:")
            for event in result["simulation"]:
                lines.append(
                    f"  {event.get('event_name', 'N/A')}: "
                    f"{event.get('start', {}).get('time', 'N/A')} - "
                    f"{event.get('end', {}).get('time', 'N/A')} "
                    f"({event.get('duration_minutes', 0)} min)"
                )

    elif "corpus_statistics" in result:
        stats = result["corpus_statistics"]
        lines.append("Corpus Statistics:")
        lines.append(f"  Total Laws: {stats.get('total_laws', 0)}")
        lines.append(f"  Total Targets: {stats.get('total_targets', 0)}")
        lines.append(f"  Total Events: {stats.get('total_events', 0)}")
        lines.append(
            f"  Total Duration: {stats.get('total_duration_minutes', 0)} minutes"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    main()
