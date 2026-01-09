"""Sample OpenRouter (OpenAI-compatible) chat + tool-calling loop."""

import json
import os
import sqlite3
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Optional, Union

import sympy as sp
from dotenv import load_dotenv
from openai import OpenAI

_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    global _client
    if _client is not None:
        return _client

    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is missing. Add it to your .env file.")

    # OpenRouter's OpenAI-compatible endpoint.
    _client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        # Optional but recommended by OpenRouter.
        default_headers={
            "HTTP-Referer": "http://localhost",
            "X-Title": "manipulation-game-sample",
        },
    )
    return _client

MODELS = [
    "openai/gpt-5.2",
    "anthropic/claude-opus-4.5",
    "google/gemini-3-pro-preview",
]

TOOLS_BASE = [
    {
        "type": "function",
        "function": {
            "name": "get_utc_time",
            "description": "Return the current UTC time as an ISO-8601 string.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    }
]

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
LOG_FILE = LOG_DIR / f"openrouter_run_{RUN_ID}.jsonl"
CACHE_DB = LOG_DIR / "openrouter_cache.sqlite3"
REQUEST_SEED = 1234


class ResponseCache:
    def __init__(self, path: Path) -> None:
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS response_cache (
                request_hash TEXT PRIMARY KEY,
                response_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def get(self, request_hash: str) -> Optional[dict]:
        cursor = self.conn.execute(
            "SELECT response_json FROM response_cache WHERE request_hash = ?",
            (request_hash,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return json.loads(row[0])

    def set(self, request_hash: str, response: dict) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO response_cache (request_hash, response_json, created_at) VALUES (?, ?, ?)",
            (
                request_hash,
                json.dumps(response, ensure_ascii=True),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()


CACHE = ResponseCache(CACHE_DB)


def run_tool(name: str, args: dict) -> dict:
    if name == "get_utc_time":
        return {"utc": datetime.now(timezone.utc).isoformat()}

    if name == "sympy_integrate":
        expr = sp.sympify(args.get("expression", "0"))
        var = sp.Symbol(args.get("variable", "z"))
        integral = sp.integrate(expr, var)
        return {"integral": str(sp.simplify(integral))}

    raise ValueError(f"Unknown tool: {name}")


def log_event(event: dict) -> None:
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=True) + "\n")


def stable_json(data: dict) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def normalize_tool_calls(tool_calls: list) -> list[dict]:
    normalized = []
    for call in tool_calls:
        if isinstance(call, dict):
            normalized.append(call)
            continue
        normalized.append(
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments or "",
                },
            }
        )
    return normalized


def normalize_message(message: dict) -> dict:
    keep = {
        "role": message.get("role"),
        "content": message.get("content"),
    }
    if "tool_calls" in message:
        keep["tool_calls"] = message["tool_calls"]
    if "tool_call_id" in message:
        keep["tool_call_id"] = message["tool_call_id"]
    return keep


def compute_message_hash(prev_hash: str, message: dict, params: dict, seed: int) -> str:
    payload = stable_json(
        {
            "previous_message_hash": prev_hash,
            "message": message,
            "parameters": params,
            "seed": seed,
        }
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def compute_chain_hash(messages: list[dict], params: dict, seed: int) -> str:
    current = ""
    for message in messages:
        current = compute_message_hash(current, normalize_message(message), params, seed)
    return current


def compute_request_hash(
    messages: list[dict],
    params: dict,
    seed: int,
) -> str:
    chain_hash = compute_chain_hash(messages, params, seed)
    payload = stable_json(
        {
            "previous_message_hash": chain_hash,
            "parameters": params,
            "seed": seed,
        }
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def chat_with_tools(
    model: str,
    prompt: str,
    tools: list[dict],
    tool_choice: Union[str, dict] = "auto",
) -> str:
    messages = [
        {"role": "system", "content": "Provide concise steps; use tools if helpful."},
        {"role": "user", "content": prompt},
    ]

    current_tool_choice = tool_choice
    params = {
        "model": model,
        "tools": tools,
        "tool_choice": current_tool_choice,
        "max_tokens": 256,
    }
    log_event(
        {
            "type": "request",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": RUN_ID,
            "request_hash": compute_request_hash(messages, params, REQUEST_SEED),
            "model": model,
            "prompt": prompt,
            "tool_choice": current_tool_choice,
            "tools": [tool["function"]["name"] for tool in tools],
        }
    )
    for _ in range(3):
        params["tool_choice"] = current_tool_choice
        request_hash = compute_request_hash(messages, params, REQUEST_SEED)
        cached = CACHE.get(request_hash)
        if cached:
            log_event(
                {
                    "type": "cache_hit",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "run_id": RUN_ID,
                    "request_hash": request_hash,
                    "model": model,
                }
            )
            message_content = cached.get("content", "")
            tool_calls = cached.get("tool_calls", [])
            if not tool_calls:
                return message_content or "(empty response)"
            messages.append(
                {
                    "role": "assistant",
                    "content": message_content,
                    "tool_calls": tool_calls,
                }
            )
            for call in tool_calls:
                args = json.loads(call["function"].get("arguments") or "{}")
                result = run_tool(call["function"]["name"], args)
                log_event(
                    {
                        "type": "tool_result",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "run_id": RUN_ID,
                        "model": model,
                        "tool_call_id": call["id"],
                        "tool_name": call["function"]["name"],
                        "tool_args": args,
                        "tool_output": result,
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": json.dumps(result),
                    }
                )
            current_tool_choice = "auto"
            continue

        client = get_client()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=current_tool_choice,
            max_tokens=256,
            seed=REQUEST_SEED,
        )

        message = response.choices[0].message
        tool_calls = normalize_tool_calls(message.tool_calls or [])
        log_event(
            {
                "type": "response",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "run_id": RUN_ID,
                "request_hash": request_hash,
                "model": model,
                "content": message.content or "",
                "tool_calls": tool_calls,
            }
        )
        CACHE.set(
            request_hash,
            {
                "content": message.content or "",
                "tool_calls": tool_calls,
            },
        )

        if not tool_calls:
            return message.content or "(empty response)"

        # Record the assistant's tool call request.
        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": tool_calls,
            }
        )

        for call in tool_calls:
            args = json.loads(call["function"].get("arguments") or "{}")
            result = run_tool(call["function"]["name"], args)
            log_event(
                {
                    "type": "tool_result",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "run_id": RUN_ID,
                    "model": model,
                    "tool_call_id": call["id"],
                    "tool_name": call["function"]["name"],
                    "tool_args": args,
                    "tool_output": result,
                }
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": json.dumps(result),
                }
            )

        current_tool_choice = "auto"

    return "(no response after tool loop)"


if __name__ == "__main__":
    sympy_tool = {
        "type": "function",
        "function": {
            "name": "sympy_integrate",
            "description": "Compute an indefinite integral with SymPy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Expression to integrate, e.g. 4*exp(z) + 15 + 1/(6*z)",
                    },
                    "variable": {
                        "type": "string",
                        "description": "Integration variable, e.g. z",
                    },
                },
                "required": ["expression", "variable"],
                "additionalProperties": False,
            },
        },
    }

    prompt_no_tool = (
        "Compute the indefinite integral of 4e^z + 15 + 1/(6z) with respect to z. "
        "Show the main steps concisely."
    )
    prompt_with_tool = (
        "Compute the indefinite integral of 4e^z + 15 + 1/(6z) with respect to z. "
        "Show the main steps concisely, then call sympy_integrate to verify the final result."
    )
    for model_id in MODELS:
        print(f"\n== {model_id} ==")
        print("-- no tool --")
        print(chat_with_tools(model_id, prompt_no_tool, TOOLS_BASE, tool_choice="none"))
        print("-- with sympy tool --")
        print(
            chat_with_tools(
                model_id,
                prompt_with_tool,
                TOOLS_BASE + [sympy_tool],
                tool_choice={"type": "function", "function": {"name": "sympy_integrate"}},
            )
        )
