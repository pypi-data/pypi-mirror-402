from __future__ import annotations

import argparse
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Iterable

XML_SUFFIX = ".xml"
WHITESPACE_BETWEEN_TAGS = re.compile(r">\s+<")


def normalize_xml(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = WHITESPACE_BETWEEN_TAGS.sub("><", text)
    return text.strip()


def iter_zip_entries(path: Path) -> dict[str, bytes]:
    entries: dict[str, bytes] = {}
    with zipfile.ZipFile(path, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            entries[info.filename] = zf.read(info.filename)
    return entries


def compare_entries(expected: dict[str, bytes], actual: dict[str, bytes], ignore: set[str]) -> list[str]:
    diffs: list[str] = []

    expected_keys = {k for k in expected.keys() if k not in ignore}
    actual_keys = {k for k in actual.keys() if k not in ignore}

    missing = sorted(expected_keys - actual_keys)
    extra = sorted(actual_keys - expected_keys)

    if missing:
        diffs.append(f"Missing files: {', '.join(missing)}")
    if extra:
        diffs.append(f"Extra files: {', '.join(extra)}")

    for key in sorted(expected_keys & actual_keys):
        exp = expected[key]
        act = actual[key]
        if key.endswith(XML_SUFFIX):
            exp_text = normalize_xml(exp.decode("utf-8", errors="replace"))
            act_text = normalize_xml(act.decode("utf-8", errors="replace"))
            if exp_text != act_text:
                diffs.append(f"XML differs: {key}")
        else:
            if exp != act:
                diffs.append(f"Binary differs: {key}")

    return diffs


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare two PPTX files.")
    parser.add_argument("expected", type=Path, help="Expected PPTX path")
    parser.add_argument("actual", type=Path, help="Actual PPTX path")
    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        help="Zip entry path to ignore (can be repeated)",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)
    if not args.expected.exists():
        print(f"Expected PPTX not found: {args.expected}")
        return 2
    if not args.actual.exists():
        print(f"Actual PPTX not found: {args.actual}")
        return 2

    ignore = set(args.ignore)
    expected_entries = iter_zip_entries(args.expected)
    actual_entries = iter_zip_entries(args.actual)

    diffs = compare_entries(expected_entries, actual_entries, ignore)
    if diffs:
        print("Differences found:")
        for diff in diffs:
            print(f"- {diff}")
        return 1

    print("PPTX files match.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
