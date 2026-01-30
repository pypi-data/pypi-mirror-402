from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel, Field, ConfigDict

class ManualStep(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    body: str = ""

class ManualDoc(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    title: str
    tags: List[str] = Field(default_factory=list)
    summary: str = ""
    prerequisites: List[str] = Field(default_factory=list)
    steps: List[ManualStep] = Field(default_factory=list)
    troubleshooting: List[ManualStep] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)

class ManualFile(BaseModel):
    """Root object inside a ```tspec block for manuals."""
    model_config = ConfigDict(extra="forbid")
    manual: ManualDoc
    meta: Dict[str, Any] = Field(default_factory=dict)
