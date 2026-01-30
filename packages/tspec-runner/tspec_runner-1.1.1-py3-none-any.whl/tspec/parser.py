from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from .errors import ParseError, SpecVersionError
from .spec_versions import resolve_spec, SpecResolution

TSPEC_DECL_RE = re.compile(r"^\s*!\s*tspec\s+(?P<decl>.+?)\s*$")
FENCE_RE = re.compile(r"^```tspec\s*\n(?P<body>.*?)(?:\n```\s*$)", re.MULTILINE | re.DOTALL)
INCLUDE_RE = re.compile(r"^\s*@include\s*:\s*(?P<path>.+?)\s*$", re.MULTILINE)

BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT_RE = re.compile(r"(^|\s)//.*?$", re.MULTILINE)
HASH_COMMENT_RE = re.compile(r"(^|\s)#.*?$", re.MULTILINE)

@dataclass
class ParsedDoc:
    path: Path
    spec: SpecResolution
    blocks: list[dict]
    raw_blocks: list[str]

def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError as e:
        raise ParseError(f"File not found: {path} (hint: run from project root or pass an absolute path)") from e

def extract_declared_spec(text: str) -> Optional[str]:
    for line in text.splitlines():
        m = TSPEC_DECL_RE.match(line)
        if m:
            return m.group("decl").strip()
    return None

def extract_tspec_blocks(text: str) -> list[str]:
    return [m.group("body") for m in FENCE_RE.finditer(text)]

def strip_comments(tspec_body: str) -> str:
    s = BLOCK_COMMENT_RE.sub("", tspec_body)
    s = LINE_COMMENT_RE.sub("", s)
    s = HASH_COMMENT_RE.sub("", s)
    return s

def parse_yaml_mapping(body: str) -> dict:
    try:
        obj = yaml.safe_load(body) or {}
    except Exception as e:
        raise ParseError(f"YAML parse failed: {e}") from e
    if not isinstance(obj, dict):
        raise ParseError("tspec block must be a mapping (YAML object).")
    return obj

def _parse_includes(raw_block: str) -> list[str]:
    includes: list[str] = []
    for m in INCLUDE_RE.finditer(raw_block):
        inc = m.group("path").strip()
        if (inc.startswith('"') and inc.endswith('"')) or (inc.startswith("'") and inc.endswith("'")):
            inc = inc[1:-1]
        includes.append(inc)
    return includes

def load_tspec_file(
    path: Path,
    *,
    parent_spec: Optional[SpecResolution] = None,
    _stack: Optional[list[Path]] = None,
) -> ParsedDoc:
    path = path.resolve()
    _stack = _stack or []
    if path in _stack:
        raise ParseError(f"Include cycle detected: {' -> '.join(str(p) for p in _stack + [path])}")

    text = _read_text(path)
    declared = extract_declared_spec(text)

    if parent_spec is None:
        spec = resolve_spec(declared)
    else:
        if declared:
            resolved_here = resolve_spec(declared)
            if resolved_here.resolved != parent_spec.resolved:
                raise SpecVersionError(
                    f"Included file {path} declares spec {resolved_here.resolved}, but parent resolved {parent_spec.resolved}. "
                    "Mixing spec versions is not allowed."
                )
        spec = parent_spec

    blocks_raw = extract_tspec_blocks(text)
    if not blocks_raw:
        raise ParseError(f"No ```tspec blocks found in {path}")

    blocks: list[dict] = []
    all_raw: list[str] = []

    for raw in blocks_raw:
        includes = _parse_includes(raw)
        body_wo_includes = INCLUDE_RE.sub("", raw)

        cleaned = strip_comments(body_wo_includes)
        mapping = parse_yaml_mapping(cleaned)
        blocks.append(mapping)
        all_raw.append(raw)

        for inc in includes:
            inc_path = (path.parent / inc).resolve()
            inc_doc = load_tspec_file(inc_path, parent_spec=spec, _stack=_stack + [path])
            blocks.extend(inc_doc.blocks)
            all_raw.extend(inc_doc.raw_blocks)

    return ParsedDoc(path=path, spec=spec, blocks=blocks, raw_blocks=all_raw)
