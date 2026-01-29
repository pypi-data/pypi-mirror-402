from pathlib import Path
import argparse
import re

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"

READ_RE = re.compile(
    r'^(?P<key>readme\s*=\s*\{\s*file\s*=\s*")(?P<file>[^"]+)("\s*,\s*content-type\s*=\s*"(?P<ctype>[^"]+)"\s*\}\s*)$'
)


def update_readme(lang: str) -> None:
    if lang == "en":
        target = "README.rst"
    elif lang in {"jp", "ja"}:
        target = "README.ja.rst"
    else:
        raise SystemExit(f"Unknown lang: {lang!r} (use en or jp)")

    text = PYPROJECT.read_text(encoding="utf-8")
    lines = text.splitlines()
    updated = False
    for i, line in enumerate(lines):
        m = READ_RE.match(line)
        if not m:
            continue
        lines[i] = f"{m.group('key')}{target}{m.group(3)}"
        updated = True
        break
    if not updated:
        raise SystemExit("readme entry not found in pyproject.toml")
    PYPROJECT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"pyproject.toml: readme file set to {target}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Switch PyPI long_description readme between English/Japanese.",
    )
    parser.add_argument("--lang", required=True, help="en or jp")
    args = parser.parse_args()
    update_readme(args.lang.strip().lower())


if __name__ == "__main__":
    main()
