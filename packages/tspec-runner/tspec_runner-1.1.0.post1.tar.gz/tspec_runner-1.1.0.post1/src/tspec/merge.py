from __future__ import annotations

from typing import Any, Dict, List
from .errors import ValidationError

ALLOWED_TOP_KEYS = {"suite", "vars", "fixtures", "cases", "plugins", "meta"}

def merge_blocks(blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "vars": {},
        "fixtures": {"before": [], "after": [], "before_each": [], "after_each": []},
        "cases": [],
        "plugins": {},
        "meta": {},
    }
    suite_seen = False
    case_ids = set()

    for b in blocks:
        if not isinstance(b, dict):
            raise ValidationError("Each tspec block must be a mapping.")

        unknown = set(b.keys()) - ALLOWED_TOP_KEYS
        if unknown:
            raise ValidationError(f"Unknown top-level key(s): {sorted(unknown)}")

        if "suite" in b:
            if suite_seen:
                raise ValidationError("Multiple 'suite' definitions found. Define suite only once.")
            out["suite"] = b["suite"]
            suite_seen = True

        if "vars" in b:
            if not isinstance(b["vars"], dict):
                raise ValidationError("vars must be a mapping.")
            out["vars"].update(b["vars"])

        if "fixtures" in b:
            fx = b["fixtures"]
            if not isinstance(fx, dict):
                raise ValidationError("fixtures must be a mapping.")
            for k in ["before", "after", "before_each", "after_each"]:
                if k in fx:
                    if not isinstance(fx[k], list):
                        raise ValidationError(f"fixtures.{k} must be a list.")
                    out["fixtures"][k].extend(fx[k])

        if "cases" in b:
            cs = b["cases"]
            if not isinstance(cs, list):
                raise ValidationError("cases must be a list.")
            for c in cs:
                if not isinstance(c, dict):
                    raise ValidationError("Each case must be a mapping.")
                cid = c.get("id")
                if not isinstance(cid, str) or not cid:
                    raise ValidationError("Each case must have string 'id'.")
                if cid in case_ids:
                    raise ValidationError(f"Duplicate case id: {cid}")
                case_ids.add(cid)
                out["cases"].append(c)

        if "plugins" in b:
            if not isinstance(b["plugins"], dict):
                raise ValidationError("plugins must be a mapping.")
            out["plugins"].update(b["plugins"])

        if "meta" in b:
            if not isinstance(b["meta"], dict):
                raise ValidationError("meta must be a mapping.")
            out["meta"].update(b["meta"])

    if not suite_seen:
        raise ValidationError("Missing required top-level 'suite'.")
    return out
