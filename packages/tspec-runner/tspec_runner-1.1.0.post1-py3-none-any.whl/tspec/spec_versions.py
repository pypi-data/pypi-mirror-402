from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from .errors import SpecVersionError

SUPPORTED_SPECS = [Version("0.1.0")]

@dataclass(frozen=True)
class SpecResolution:
    declared: Optional[str]
    resolved: Version
    reason: str

def _generation(v: Version) -> int:
    return v.major if v.major > 0 else v.minor

def supported_window(supported: Iterable[Version], generations_back: int = 3) -> tuple[int, int, Version]:
    s = sorted(supported)
    if not s:
        raise SpecVersionError("No supported spec versions are configured.")
    latest = s[-1]
    g_latest = _generation(latest)
    g_min = g_latest - generations_back
    return g_min, g_latest, latest

def resolve_spec(declared: Optional[str], supported: Iterable[Version] = SUPPORTED_SPECS) -> SpecResolution:
    supported_sorted = sorted(supported)
    g_min, g_latest, latest = supported_window(supported_sorted)

    if declared is None or declared.strip() == "":
        return SpecResolution(None, latest, "No declaration; using latest spec.")

    decl = declared.strip()

    # exact
    try:
        exact = Version(decl)
        if exact in supported_sorted:
            _check_window(exact, g_min, g_latest)
            return SpecResolution(declared, exact, "Exact spec version declared.")
    except Exception:
        pass

    # range
    try:
        spec = SpecifierSet(decl)
    except Exception as e:
        raise SpecVersionError(f"Invalid spec declaration: {decl!r} ({e})") from e

    candidates = [v for v in supported_sorted if v in spec]
    if not candidates:
        raise SpecVersionError(
            f"Spec declaration {decl!r} doesn't match any supported versions: "
            f"{', '.join(str(v) for v in supported_sorted)}"
        )
    chosen = candidates[-1]
    _check_window(chosen, g_min, g_latest)
    return SpecResolution(declared, chosen, "Range declaration; chose highest supported version in range.")

def _check_window(v: Version, g_min: int, g_latest: int) -> None:
    g = _generation(v)
    if g < g_min:
        raise SpecVersionError(
            f"Spec {v} is too old for this runner. Supported generations: {g_min}..{g_latest}. "
            f"Please use an older runner or migrate."
        )
