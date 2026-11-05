#!/usr/bin/env python3
"""Render JUnit XML files as a Markdown summary for GitHub Actions.

Usage::

    python .github/scripts/junit_summary.py reports/*.xml

The summary is appended to ``$GITHUB_STEP_SUMMARY`` when that variable is set
(i.e. inside GitHub Actions), otherwise it is printed to stdout. The label for
each file is derived from its name, e.g. ``junit-3.11-pyqt5.xml`` becomes
``3.11 / pyqt5``.
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def _label(path: Path) -> str:
    stem = path.stem
    if stem.startswith("junit-"):
        stem = stem[len("junit-") :]
    return stem.replace("-", " / ", 1)


def _parse(path: Path) -> dict:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")

    tests = failures = errors = skipped = 0
    duration = 0.0
    failed_tests: list[str] = []

    for suite in suites:
        tests += int(suite.get("tests", 0) or 0)
        failures += int(suite.get("failures", 0) or 0)
        errors += int(suite.get("errors", 0) or 0)
        skipped += int(suite.get("skipped", 0) or 0)
        duration += float(suite.get("time", 0) or 0)

        for case in suite.iter("testcase"):
            if case.find("failure") is not None or case.find("error") is not None:
                name = case.get("name", "?")
                classname = case.get("classname", "")
                failed_tests.append(f"{classname}::{name}" if classname else name)

    return {
        "tests": tests,
        "passed": tests - failures - errors - skipped,
        "failed": failures + errors,
        "skipped": skipped,
        "duration": duration,
        "failed_tests": failed_tests,
    }


def _render(rows: list[tuple[str, dict]]) -> str:
    lines = [
        "## Test results",
        "",
        "| Job | Tests | Passed | Failed | Skipped | Time |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for label, result in rows:
        lines.append(
            f"| {label} | {result['tests']} | {result['passed']} | "
            f"{result['failed']} | {result['skipped']} | "
            f"{result['duration']:.1f}s |"
        )

    failed = [(label, r["failed_tests"]) for label, r in rows if r["failed_tests"]]
    if failed:
        lines += ["", "### Failed tests", ""]
        for label, names in failed:
            lines.append(f"**{label}**")
            lines += [f"- `{name}`" for name in names]
            lines.append("")

    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    rows = []
    for raw in argv:
        path = Path(raw)
        if path.is_file():
            rows.append((_label(path), _parse(path)))

    text = _render(rows) if rows else "## Test results\n\nNo test results found.\n"

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(text)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
