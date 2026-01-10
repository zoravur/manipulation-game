import json
from datetime import datetime, timezone

import sympy as sp


def run_tool(name: str, args: dict) -> dict:
    if name == "get_utc_time":
        return {"utc": datetime.now(timezone.utc).isoformat()}

    if name == "sympy_integrate":
        expr = sp.sympify(args.get("expression", "0"))
        var = sp.Symbol(args.get("variable", "z"))
        integral = sp.integrate(expr, var)
        return {"integral": str(sp.simplify(integral))}

    raise ValueError(f"Unknown tool: {name}")


def get_sympy_tool() -> dict:
    return {
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
