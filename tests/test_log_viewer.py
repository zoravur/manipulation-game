from log_viewer import format_event


def test_format_request_event():
    event = {
        "type": "request",
        "timestamp": "2025-01-01T00:00:00Z",
        "model": "openai/gpt-4o-mini",
        "prompt": "Hi",
        "tool_choice": "none",
        "tools": ["sympy_integrate"],
    }
    output = format_event(event)
    assert "request" in output
    assert "sympy_integrate" in output
    assert "Hi" in output


def test_format_response_event():
    event = {
        "type": "response",
        "timestamp": "2025-01-01T00:00:00Z",
        "model": "openai/gpt-4o-mini",
        "content": "Hello",
        "tool_calls": [{"name": "sympy_integrate"}],
    }
    output = format_event(event)
    assert "response" in output
    assert "sympy_integrate" in output
    assert "Hello" in output


def test_format_tool_result_event():
    event = {
        "type": "tool_result",
        "timestamp": "2025-01-01T00:00:00Z",
        "model": "openai/gpt-4o-mini",
        "tool_name": "sympy_integrate",
        "tool_args": {"expression": "x", "variable": "x"},
        "tool_output": {"integral": "x**2/2"},
    }
    output = format_event(event)
    assert "tool_result" in output
    assert "sympy_integrate" in output
    assert "x**2/2" in output
