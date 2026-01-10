"""Pretty-print OpenRouter run logs saved as JSONL."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def format_event(event: dict) -> str:
    kind = event.get("type", "unknown")
    ts = event.get("timestamp", "")
    model = event.get("model", "")
    header = f"[{ts}] {model} :: {kind}"

    if kind == "request":
        prompt = event.get("prompt", "")
        tools = ", ".join(event.get("tools", []))
        tool_choice = event.get("tool_choice", "")
        return f"{header}\n  tools: {tools or '-'}\n  tool_choice: {tool_choice}\n  prompt: {prompt}\n"

    if kind == "response":
        content = event.get("content", "")
        tool_calls = event.get("tool_calls", [])
        calls = ", ".join([call.get("name", "") for call in tool_calls])
        calls_line = f"  tool_calls: {calls}\n" if tool_calls else ""
        return f"{header}\n{calls_line}  content: {content}\n"

    if kind == "tool_result":
        tool_name = event.get("tool_name", "")
        tool_args = json.dumps(event.get("tool_args", {}), ensure_ascii=True)
        tool_output = json.dumps(event.get("tool_output", {}), ensure_ascii=True)
        return f"{header}\n  tool: {tool_name}\n  args: {tool_args}\n  output: {tool_output}\n"

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
