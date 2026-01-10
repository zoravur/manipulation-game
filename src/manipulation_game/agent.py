from typing import Literal
import json

from pydantic import BaseModel

from manipulation_game.game import Game
from manipulation_game.judge import judge_recommendation
from manipulation_game.sample import extend_conversation_with_tools
from manipulation_game.templating import template
from manipulation_game.tools import ExitWithRestaurantDecision

from pathlib import Path



class GameResults(BaseModel):
    recommended_restaurant: str
    chosen_restaurant: str


B_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "make_restaurant_decision",
            "description": "Choose a restaurant to dine at.",
            "parameters": {
                "type": "object",
                "properties": {
                    "restaurant": {
                        "type": "string",   # ideally it would be "oneOf" the restaurant names available
                        "description": "The name of the restaurant chosen.",
                    }
                },
                "required": ["restaurant"],
                "additionalProperties": False,
            },
        },
    }
]


class Agent:
    def __init__(self, player: Literal["A", "B"], model: str, system_prompt: str):
        self.player = player
        self.model = model
        self.system_prompt = system_prompt
        self.messages = [
            {"role": "system", "content": system_prompt}
        ]

    def _add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})

    def _add_assistant_message(self, content: str):
        self.messages.append({"role": "assistant", "content": content})

    def add_user_message_and_respond(self, content: str | None) -> str:
        """May raise ExitWithRestaurantDecision."""
        if content is not None:
            self._add_user_message(content)

        tools = B_TOOLS if self.player == "B" else []
        
        response = extend_conversation_with_tools(
            model=self.model,
            messages=self.messages,
            tools=tools,
            tool_choice="none" if len(tools) == 0 else "auto",
            persona=self.player,
        )
        self._add_assistant_message(response)
        return response
    

def run_agents(
    agent_a: Agent,
    agent_b: Agent,
    max_turns: int,
) -> str:
    try:
        a_message = None
        for turn in range(max_turns):
            print(f"--- Turn {turn + 1} ---")
            print("Agent B's turn:")
            b_message = agent_b.add_user_message_and_respond(a_message)
            print(b_message)
            print("\nAgent A's turn:")
            a_message = agent_a.add_user_message_and_respond(b_message)
            print(a_message)
            print()
        return ""   # no restaurant decision within the given turns
    except ExitWithRestaurantDecision as e:
        print(f"Conversation ended with restaurant decision: {e.decision}")
        return e.decision
    

def run_game(game: Game) -> GameResults:
    with open("restaurant_facts.json") as f:
        restaurant_facts = json.load(f)

    d = {}
    for p in Path(game.realistic_dir, game.realistic_city).glob("*"):
        with open(p) as f:
            restaurant_json = json.load(f)
            d[restaurant_json["id"]] = restaurant_json

    

    agent_a = Agent(
        player="A",
        model=game.a_model,
        system_prompt=template(
            player="A",
            game=game,
            restaurant_facts=restaurant_facts,
            realistic_restaurant_json=d,
        ).sys,
    )
    agent_b = Agent(
        player="B",
        model=game.b_model,
        system_prompt=template(
            player="B",
            game=game,
            restaurant_facts=restaurant_facts,
            realistic_restaurant_json=d,
        ).sys,
    )

    chosen_restaurant = run_agents(
        agent_a=agent_a,
        agent_b=agent_b,
        max_turns=game.max_turns_per_conversation,
    )
    recommended_restaurant = judge_recommendation(
        game=game,
        messages=agent_a.messages,
    ) or ""

    return GameResults(
        recommended_restaurant=recommended_restaurant,
        chosen_restaurant=chosen_restaurant,
    )

if __name__ == "__main__":
    g = Game.model_validate(json.load(open("example_game.json")))
    results = run_game(g)
    print("Game Results:")
    print(results.model_dump_json(indent=2))