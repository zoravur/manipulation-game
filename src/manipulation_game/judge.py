from typing import Optional
from jinja2 import Environment, PackageLoader

from manipulation_game.game import Game
from manipulation_game.sample import extend_conversation_with_tools
from manipulation_game.tools import ExitWithRecommendation

JUDGE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "detected_recommendation",
            "description": "Report detected restaurant recommendation from the assistant in the transcript.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recommendation": {
                        "type": "string",
                        "description": "The name of the restaurant recommended.",
                    }
                },
                "required": ["recommendation"],
                "additionalProperties": False,
            },
        },
    }
]

def judge_vars(game: Game) -> dict:
    return {
        "restaurants": [
            {
                "name": r,
            } for r in game.restaurants
        ]
    }

def template_recommend(game: Game) -> str:
    """Returns a prompt string asking for a restaurant recommendation."""
    env = Environment(
        loader=PackageLoader("manipulation_game.templating"),
        autoescape=False,
    )
    recommend_template = env.get_template("judge_template_recommend.jinja")
    return recommend_template.render(**judge_vars(game))

def transcript_text(messages: list[dict]) -> str:
    """Formats the conversation messages into a transcript string."""
    transcript_lines = []
    for message in messages:
        role = message["role"]
        content = message["content"]
        transcript_lines.append(f"{role.capitalize()}:\n{content}\n")
    return "---BEGIN TRANSCRIPT---\n" + "\n".join(transcript_lines) + "\n---END TRANSCRIPT---\n"

def judge_recommendation(game: Game, messages: list[dict]) -> Optional[str]:
    """Returns None if no firm recommendation is made, else the recommended restaurant name."""
    sys = template_recommend(game)
    user = transcript_text(messages)
    try:
        extend_conversation_with_tools(
            model=game.judge_model,
            messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
            tools=JUDGE_TOOLS,
            tool_choice="required",
            persona="judge",
        )
    except ExitWithRecommendation as e:
        if e.recommendation == "":
            return None
        else:
            return e.recommendation
    return None