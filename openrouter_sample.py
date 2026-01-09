"""Sample OpenRouter (OpenAI-compatible) chat + tool-calling loop."""

import json
import os
from datetime import datetime, timezone
from typing import Union

from dotenv import load_dotenv
from openai import OpenAI
import sympy as sp

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY is missing. Add it to your .env file.")

# OpenRouter's OpenAI-compatible endpoint.
client = OpenAI(
    api_key=API_KEY,
    base_url="https://openrouter.ai/api/v1",
    # Optional but recommended by OpenRouter.
    default_headers={
        "HTTP-Referer": "http://localhost",
        "X-Title": "manipulation-game-sample",
    },
)

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


def run_tool(name: str, args: dict) -> dict:
    if name == "get_utc_time":
        return {"utc": datetime.now(timezone.utc).isoformat()}

    if name == "sympy_integrate":
        expr = sp.sympify(args.get("expression", "0"))
        var = sp.Symbol(args.get("variable", "z"))
        integral = sp.integrate(expr, var)
        return {"integral": str(sp.simplify(integral))}

    raise ValueError(f"Unknown tool: {name}")


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
    for _ in range(3):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=current_tool_choice,
            max_tokens=512,
        )

        message = response.choices[0].message
        tool_calls = message.tool_calls or []

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
            args = json.loads(call.function.arguments or "{}")
            result = run_tool(call.function.name, args)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
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
