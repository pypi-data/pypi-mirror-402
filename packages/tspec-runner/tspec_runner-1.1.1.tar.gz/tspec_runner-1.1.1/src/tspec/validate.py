from __future__ import annotations

from pathlib import Path
from typing import Tuple, Any

from pydantic import ValidationError as PydanticValidationError

from .errors import ValidationError
from .merge import merge_blocks
from .model import Document
from .parser import load_tspec_file

def load_and_validate(path: Path) -> Tuple[Document, Any]:
    parsed = load_tspec_file(path)
    merged = merge_blocks(parsed.blocks)
    try:
        doc = Document.model_validate(merged)
    except PydanticValidationError as e:
        raise ValidationError(str(e)) from e

    if not doc.cases:
        raise ValidationError("No cases found.")
    return doc, parsed.spec
