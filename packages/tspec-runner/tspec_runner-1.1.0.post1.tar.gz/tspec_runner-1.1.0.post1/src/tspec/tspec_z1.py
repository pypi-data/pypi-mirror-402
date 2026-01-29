from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class Z1Section:
    tag: str
    body: str


@dataclass
class Z1Doc:
    dictionary: Dict[str, str]
    sections: List[Z1Section]


def _split_escaped(text: str, sep: str) -> List[str]:
    parts: List[str] = []
    buf: List[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            buf.append(text[i + 1])
            i += 2
            continue
        if ch == sep:
            parts.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    parts.append("".join(buf))
    return parts


def _read_block(text: str, start: int) -> tuple[str, int]:
    if start >= len(text) or text[start] != "{":
        raise ValueError("block start must be '{'")
    depth = 0
    i = start
    while i < len(text):
        ch = text[i]
        if ch == "\\":
            i += 2
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1 : i], i + 1
        i += 1
    raise ValueError("unterminated block")


def _parse_dict(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for entry in _split_escaped(text, ";"):
        if not entry.strip():
            continue
        if "=" not in entry:
            raise ValueError(f"invalid dict entry: {entry!r}")
        key, value = entry.split("=", 1)
        out[key.strip()] = value.strip()
    return out


def _parse_sections(text: str) -> List[Z1Section]:
    sections: List[Z1Section] = []
    for part in _split_escaped(text, "|"):
        if not part.strip():
            continue
        tag, body = part.split(":", 1) if ":" in part else ("", part)
        sections.append(Z1Section(tag.strip(), body.strip()))
    return sections


def decode_z1_text(text: str) -> Z1Doc:
    raw = (text or "").strip()
    if not raw.startswith("Z1|"):
        raise ValueError("TSPEC-Z1 must start with 'Z1|'")
    i = len("Z1|")
    dct: Dict[str, str] = {}
    sections: List[Z1Section] = []

    while i < len(raw):
        if raw.startswith("D{", i):
            content, i = _read_block(raw, i + 1)
            dct = _parse_dict(content)
            continue
        if raw.startswith("P{", i):
            content, i = _read_block(raw, i + 1)
            sections = _parse_sections(content)
            continue
        if raw[i].isspace():
            i += 1
            continue
        raise ValueError(f"unexpected token at {i}: {raw[i:i+8]!r}")

    return Z1Doc(dictionary=dct, sections=sections)


def decode_z1_file(path: Path) -> Z1Doc:
    return decode_z1_text(path.read_text(encoding="utf-8", errors="replace"))


def _expand_refs(text: str, dictionary: Dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        return dictionary.get(key, match.group(0))

    return re.sub(r"@([A-Za-z0-9_-]+)", repl, text)


def decompile_z1_text(text: str) -> str:
    doc = decode_z1_text(text)
    lines: List[str] = ["TSPEC-Z1 DECOMPILED"]
    for sec in doc.sections:
        lines.append(f"[{sec.tag}]")
        body = _expand_refs(sec.body, doc.dictionary)
        lines.append(body)
        lines.append("")
    return "\n".join(lines).rstrip()


def expand_z1_sections(doc: Z1Doc) -> List[Z1Section]:
    expanded: List[Z1Section] = []
    for sec in doc.sections:
        expanded.append(Z1Section(sec.tag, _expand_refs(sec.body, doc.dictionary)))
    return expanded


def decompile_z1_file(path: Path) -> str:
    return decompile_z1_text(path.read_text(encoding="utf-8", errors="replace"))
