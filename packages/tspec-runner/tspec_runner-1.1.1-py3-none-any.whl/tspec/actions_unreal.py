from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from mcp.types import CallToolResult

from .context import RunContext
from .errors import ExecutionError


def _ensure_mcp_client():
    try:
        from mcp.client.stdio import StdioServerParameters, stdio_client
        from mcp import ClientSession
    except Exception as exc:  # pragma: no cover
        raise ExecutionError("Unreal MCP automation requires: pip install -e '.[mcp]'") from exc
    return StdioServerParameters, stdio_client, ClientSession


def _to_float_list(value: Optional[Iterable[Any]], length: int) -> List[float]:
    if value is None:
        return [0.0] * length
    lst = list(value)
    if len(lst) != length:
        raise ExecutionError(f"expected {length} floats for location, got {len(lst)}")
    try:
        return [float(v) for v in lst]
    except ValueError as exc:
        raise ExecutionError(f"location values must be numeric: {exc}") from exc


def _embed_tool_args(args: Dict[str, Any]) -> Dict[str, Any]:
    location = _to_float_list(args.get("location"), 3)
    tool_args: Dict[str, Any] = {
        "castle_size": args.get("castle_size", "small"),
        "location": location,
        "name_prefix": args.get("name_prefix", "Castle"),
        "include_siege_weapons": bool(args.get("include_siege_weapons", True)),
        "include_village": bool(args.get("include_village", True)),
        "architectural_style": args.get("architectural_style", "medieval"),
    }
    return tool_args


def _dump_content_blocks(blocks: Iterable[Any] | None) -> list[Any]:
    values: list[Any] = []
    for block in blocks or []:
        values.append(block.model_dump() if hasattr(block, "model_dump") else block)
    return values


def _parse_content_json(blocks: Iterable[Any] | None) -> Any | None:
    for block in blocks or []:
        text = getattr(block, "text", None)
        if isinstance(text, str):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                continue
    return None


def _normalize_tool_result(result: Any) -> Any:
    if isinstance(result, CallToolResult):
        if result.structuredContent is not None:
            return dict(result.structuredContent)
        parsed = _parse_content_json(result.content)
        if parsed is not None:
            return parsed
        return {"content": _dump_content_blocks(result.content), "_meta": result.meta}
    return result


def _resolve_server_script_path(args: Dict[str, Any]) -> Path:
    script_arg = args.get("server_script")
    script_path = Path(script_arg or "local_notes/unreal-engine-mcp/Python/unreal_mcp_server_advanced.py").resolve()
    if not script_path.exists():
        raise ExecutionError(f"Unreal MCP server script not found at {script_path}")
    return script_path


async def _call_tool_async(
    script: Path,
    tool_name: str,
    tool_args: Dict[str, Any],
) -> Dict[str, Any]:
    StdioServerParameters, stdio_client, ClientSession = _ensure_mcp_client()

    params = StdioServerParameters(
        command="uv",
        args=["run", "--with", "mcp", "python", str(script)],
        env=None,
    )

    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            return await session.call_tool(tool_name, tool_args)


def _run_tool(script: Path, tool_name: str, tool_args: Dict[str, Any], timeout_ms: int) -> Dict[str, Any]:
    timeout_secs = timeout_ms / 1000.0 if timeout_ms else None

    async def _inner():
        return await _call_tool_async(script, tool_name, tool_args)

    try:
        if timeout_secs is None:
            result = asyncio.run(_inner())
        else:
            result = asyncio.run(asyncio.wait_for(_inner(), timeout_secs))
        return _normalize_tool_result(result)
    except asyncio.TimeoutError as exc:
        raise ExecutionError(f"Unreal MCP tool '{tool_name}' timed out after {timeout_ms} ms") from exc
    except Exception as exc:
        raise ExecutionError(f"Unreal MCP tool '{tool_name}' failed: {exc}") from exc


def create_castle(ctx: RunContext, args: Dict[str, Any]) -> Dict[str, Any]:
    script_path = _resolve_server_script_path(args)

    tool_name = args.get("tool", "create_castle_fortress")
    timeout_ms = int(args.get("timeout_ms", 420000) or 420000)
    tool_args = _embed_tool_args(args)

    result = _run_tool(script_path, tool_name, tool_args, timeout_ms)
    return result


def cleanup_prefix(ctx: RunContext, args: Dict[str, Any]) -> Dict[str, Any]:
    script_path = _resolve_server_script_path(args)

    prefixes = args.get("prefixes") or ["FutureCity", "Town"]
    timeout_ms = int(args.get("timeout_ms", 120000) or 120000)
    results: list[Dict[str, Any]] = []

    for prefix in prefixes:
        find_args = {"pattern": f"{prefix}*"}
        find_result = _run_tool(script_path, "find_actors_by_name", find_args, timeout_ms)
        actors = find_result.get("actors") or []
        for actor in actors:
            name = actor.get("name") if isinstance(actor, dict) else actor
            del_result = _run_tool(script_path, "delete_actor", {"name": name}, timeout_ms)
            results.append({"actor": name, "deleted": del_result.get("success", True), "detail": del_result})

    return {"deleted_actors": results}


def _embed_city_args(args: Dict[str, Any]) -> Dict[str, Any]:
    location = _to_float_list(args.get("location"), 3)
    return {
        "town_size": args.get("town_size", "metropolis"),
        "building_density": float(args.get("building_density", 0.85) or 0.85),
        "location": location,
        "name_prefix": args.get("name_prefix", "FutureCity"),
        "include_infrastructure": bool(args.get("include_infrastructure", True)),
        "architectural_style": args.get("architectural_style", "futuristic"),
    }


def create_city(ctx: RunContext, args: Dict[str, Any]) -> Dict[str, Any]:
    script_path = _resolve_server_script_path(args)

    tool_name = args.get("tool", "create_town")
    timeout_ms = int(args.get("timeout_ms", 420000) or 420000)
    tool_args = _embed_city_args(args)

    result = _run_tool(script_path, tool_name, tool_args, timeout_ms)
    return result
