from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

ActionFn = Callable[[Any, Dict[str, Any]], Any]

@dataclass
class ActionRegistry:
    actions: Dict[str, ActionFn]

    def __init__(self):
        self.actions = {}

    def register(self, name: str, fn: ActionFn) -> None:
        self.actions[name] = fn

    def get(self, name: str) -> ActionFn:
        return self.actions[name]
