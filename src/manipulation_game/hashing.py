import json
from hashlib import sha256


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


def compute_request_hash(messages: list[dict], params: dict, seed: int) -> str:
    chain_hash = compute_chain_hash(messages, params, seed)
    payload = stable_json(
        {
            "previous_message_hash": chain_hash,
            "parameters": params,
            "seed": seed,
        }
    )
    return sha256(payload.encode("utf-8")).hexdigest()
