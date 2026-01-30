from __future__ import annotations

import ast
from typing import Dict
from .errors import ValidationError
from .templating import render

ALLOWED_NODES = (
    ast.Expression, ast.BoolOp, ast.UnaryOp, ast.Compare,
    ast.And, ast.Or, ast.Not,
    ast.Eq, ast.NotEq,
    ast.Constant,
)

def eval_when(expr: str, ctx: Dict) -> bool:
    templated = render(expr, ctx)
    try:
        tree = ast.parse(templated, mode="eval")
    except SyntaxError as e:
        raise ValidationError(f"Invalid when expression: {expr!r} (after render: {templated!r})") from e

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            raise ValidationError(f"Bare names are not allowed in when. Use literals or ${...}: {expr!r}")
        if not isinstance(node, ALLOWED_NODES):
            raise ValidationError(f"Disallowed syntax in when: {expr!r}")

    return bool(eval(compile(tree, "<when>", "eval"), {"__builtins__": {}}, {}))
