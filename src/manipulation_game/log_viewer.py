"""Pretty-print OpenRouter run logs saved as JSONL."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


def _summarize_messages(messages: Iterable[dict], limit: int = 160) -> str:
    parts: list[str] = []
    for message in messages:
        role = message.get("role", "?")
        content = message.get("content", "")
        if not isinstance(content, str):
            content = json.dumps(content, ensure_ascii=True)
        snippet = content.replace("\n", "\\n")
        if len(snippet) > limit:
            snippet = snippet[: limit - 3] + "..."
        parts.append(f"{role}: {snippet}")
    return " | ".join(parts)


def format_event(event: dict) -> str:
    kind = event.get("type", "unknown")
    ts = event.get("timestamp", "")
    model = event.get("model", "")
    persona = event.get("persona", "")
    request_hash = event.get("request_hash", "")
    header_bits = [f"[{ts}]", model, "::", kind]
    if persona:
        header_bits.append(f"({persona})")
    if request_hash:
        header_bits.append(f"[{request_hash[:8]}]")
    header = " ".join(bit for bit in header_bits if bit)

    if kind == "request":
        prompt = event.get("prompt", "")
        messages = event.get("messages", [])
        tools = ", ".join(event.get("tools", []))
        tool_choice = event.get("tool_choice", "")
        if messages:
            summary = _summarize_messages(messages)
            return (
                f"{header}\n  tools: {tools or '-'}\n  tool_choice: {tool_choice}\n"
                f"  messages: {summary}\n"
            )
        return f"{header}\n  tools: {tools or '-'}\n  tool_choice: {tool_choice}\n  prompt: {prompt}\n"

    if kind == "response":
        content = event.get("content", "")
        tool_calls = event.get("tool_calls", [])
        calls = []
        for call in tool_calls:
            function = call.get("function", {}) or {}
            name = function.get("name", call.get("name", ""))
            raw_args = function.get("arguments", "")
            if isinstance(raw_args, str) and raw_args:
                args = raw_args
            else:
                args = json.dumps(raw_args, ensure_ascii=True)
            calls.append(f"{name}({args})")
        calls_line = f"  tool_calls: {', '.join(calls)}\n" if tool_calls else ""
        if not content:
            content = "(empty)"
        elif isinstance(content, str) and len(content) > 400:
            content = content[:397] + "..."
        return f"{header}\n{calls_line}  content: {content}\n"

    if kind == "tool_result":
        tool_name = event.get("tool_name", "")
        tool_args = json.dumps(event.get("tool_args", {}), ensure_ascii=True)
        tool_output = json.dumps(event.get("tool_output", {}), ensure_ascii=True)
        return f"{header}\n  tool: {tool_name}\n  args: {tool_args}\n  output: {tool_output}\n"

    if kind == "cache_hit":
        return f"{header}\n  cache: hit\n"

    return f"{header}\n  raw: {json.dumps(event, ensure_ascii=True)}\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="View OpenRouter JSONL logs")
    parser.add_argument("path", help="Path to a JSONL log file")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        raise SystemExit(f"Log file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            event = json.loads(line)
            print(format_event(event))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
