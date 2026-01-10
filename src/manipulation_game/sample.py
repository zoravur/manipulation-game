"""Sample OpenRouter (OpenAI-compatible) chat + tool-calling loop."""

import json
from typing import Union

from .cache import ResponseCache
from .client import get_client
from .config import CACHE_DB, LOG_FILE, MAX_TOKENS, REQUEST_SEED, RUN_ID
from .hashing import compute_request_hash, normalize_tool_calls
from .logging_utils import log_event as _log_event
from .tools import get_sympy_tool, run_tool

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

CACHE = ResponseCache(CACHE_DB)


def log_event(event: dict) -> None:
    _log_event(event, LOG_FILE)


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

    return extend_conversation_with_tools(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice=tool_choice,
    )

def extend_conversation_with_tools(
    model: str,
    messages: list[dict],
    tools: list[dict],
    tool_choice: Union[str, dict] = "auto",
    n_tools_loop: int = 3,
) -> str:
    

    current_tool_choice = tool_choice
    params = {
        "model": model,
        "tools": tools,
        "tool_choice": current_tool_choice,
        "max_tokens": MAX_TOKENS,
    }
    log_event(
        {
            "type": "request",
            "timestamp": datetime_now_iso(),
            "run_id": RUN_ID,
            "request_hash": compute_request_hash(messages, params, REQUEST_SEED),
            "model": model,
            "messages": messages,
            "tool_choice": current_tool_choice,
            "tools": [tool["function"]["name"] for tool in tools],
        }
    )
    for _ in range(n_tools_loop):
        params["tool_choice"] = current_tool_choice
        request_hash = compute_request_hash(messages, params, REQUEST_SEED)
        cached = CACHE.get(request_hash)
        if cached:
            log_event(
                {
                    "type": "cache_hit",
                    "timestamp": datetime_now_iso(),
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
                        "timestamp": datetime_now_iso(),
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
            max_tokens=MAX_TOKENS,
            seed=REQUEST_SEED,
        )

        message = response.choices[0].message
        tool_calls = normalize_tool_calls(message.tool_calls or [])
        log_event(
            {
                "type": "response",
                "timestamp": datetime_now_iso(),
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
                    "timestamp": datetime_now_iso(),
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


def datetime_now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def main() -> None:
    sympy_tool = get_sympy_tool()

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


if __name__ == "__main__":
    main()
