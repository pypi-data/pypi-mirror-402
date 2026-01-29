import sys
import json
import argparse
import logging
from typing import Any, Iterable

from . import unparse

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("obj2xml-rs")


def json_stream_generator(fp) -> Iterable[Any]:
    """
    Reads a JSON file containing a list or stream of objects
    and yields them one by one.

    If the input is a single JSON object, yields it once.
    If the input is a huge JSON list, it attempts to load it efficiently.
    """
    # Note: For true streaming of huge JSON lists without loading
    # the whole file into RAM, libraries like 'ijson' are required.
    # For a standard CLI without extra deps, we load standard JSON.
    try:
        data = json.load(fp)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON input: {e}")
        sys.exit(1)

    if isinstance(data, list):
        yield from data
    else:
        yield data


def main():
    parser = argparse.ArgumentParser(
        prog="obj2xml_rs",
        description="High-performance JSON to XML converter using Rust.",
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        type=argparse.FileType("r", encoding="utf-8"),
        default=sys.stdin,
        help="Input JSON file (default: stdin)",
    )
    parser.add_argument(
        "-o", "--output", type=str, help="Output XML file path (default: stdout)"
    )
    parser.add_argument("--pretty", action="store_true", help="Indent output")
    parser.add_argument(
        "--indent", default="  ", help="Indentation string (default: 2 spaces)"
    )
    parser.add_argument(
        "--encoding", default="utf-8", help="XML encoding (default: utf-8)"
    )
    parser.add_argument(
        "--no-full-document",
        action="store_true",
        help="Omit XML declaration and root checks",
    )
    parser.add_argument(
        "--compat",
        choices=["native", "legacy"],
        default="native",
        help="Compatibility mode",
    )
    parser.add_argument(
        "--root-attrs", action="store_true", help="Sort attributes alphabetically"
    )
    parser.add_argument(
        "--attr-prefix", default="@", help="Prefix for attribute keys (default: '@')"
    )
    parser.add_argument(
        "--cdata-key", default="#text", help="Key for text content (default: '#text')"
    )
    parser.add_argument(
        "--item-name", default="item", help="Tag name for list items (default: 'item')"
    )
    parser.add_argument(
        "--stream", action="store_true", help="Enable streaming mode (low memory usage)"
    )
    args = parser.parse_args()

    if args.input_file.isatty():
        parser.print_help()
        sys.exit(0)
    if args.stream:
        # If streaming, we treat input as an iterable generator
        data_source = json_stream_generator(args.input_file)
    else:
        try:
            data_source = json.load(args.input_file)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON: {e}")
            sys.exit(1)
    # If output path is given, we pass the path string to Rust
    # If not, we pass sys.stdout.buffer (binary stream) or let Rust return a string
    output_target = args.output
    if args.stream and output_target is None:
        output_target = sys.stdout.buffer
    try:
        result = unparse(
            data_source,
            output=output_target,
            pretty=args.pretty,
            indent=args.indent,
            encoding=args.encoding,
            full_document=not args.no_full_document,
            compat=args.compat,
            attr_prefix=args.attr_prefix,
            cdata_key=args.cdata_key,
            item_name=args.item_name,
            sort_attributes=args.root_attrs,
            streaming=args.stream,
        )
        if args.output is None and not args.stream:
            print(result)
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
