#!/usr/bin/env python
"""Generate a QA inventory report for all *_testcases.md files."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
import sys


def find_testcase_files(root: Path) -> list[Path]:
    return sorted(root.glob("docs/*_testcases.md"))


def extract_commands(text: str) -> list[str]:
    pattern = re.compile(r"`([^`]+)`")
    return pattern.findall(text)


def build_report(entries: list[tuple[str, int, list[str]]]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = [
        "# QA Testcase Inventory",
        "Skill: docs/skills/qa/skill.en.md",
        "",
        f"Generated: {now}",
        "",
        "## Summary",
        "- QA confirms each testcase document contains at least one actionable tspec command.",
        "- Files with zero commands are marked for follow-up.",
        "",
        "## Files",
    ]
    for name, count, commands in entries:
        status = "✅" if count > 0 else "⚠️"
        lines.append(f"- {status} `{name}` ({count} tspec command{'s' if count != 1 else ''})")
        if commands:
            sample = commands[:2]
            for cmd in sample:
                lines.append(f"  - `{cmd}`")
        else:
            lines.append("  - *No commands found; please add a tspec run/validate entry.*")
    lines.append("")
    lines.append("## Next steps")
    lines.append("- QA agent assigned to monitor these documents; report new failures in `docs/Knowledge.md`.")
    lines.append("- PM to prioritize missing commands before automation.")
    return "\n".join(lines) + "\n"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    files = find_testcase_files(root)
    if not files:
        print("No testcase documents found.", file=sys.stderr)
        sys.exit(1)

    entries = []
    missing = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        commands = extract_commands(text)
        entries.append((path.name, len(commands), commands))
        if not commands:
            missing.append(path.name)

    report_path = root / "docs" / "qa_reports" / "testcase_inventory.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_report(entries), encoding="utf-8")

    if missing:
        print("Files without commands:", ", ".join(missing), file=sys.stderr)
        sys.exit(1)

    print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()
