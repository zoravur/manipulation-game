import json
from datetime import datetime, timezone

import sympy as sp


class ExitWithRestaurantDecision(Exception):
    def __init__(self, decision: str):
        self.decision = decision

class ExitWithRecommendation(Exception):
    def __init__(self, recommendation: str):
        self.recommendation = recommendation

def run_tool(name: str, args: dict) -> dict:
    if name == "get_utc_time":
        return {"utc": datetime.now(timezone.utc).isoformat()}
    
    if name == "make_restaurant_decision":
        restaurant = args.get("restaurant", "")
        raise ExitWithRestaurantDecision(restaurant)
    
    if name == "detected_recommendation":
        recommendation = args.get("recommendation", "")
        raise ExitWithRecommendation(recommendation)

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
