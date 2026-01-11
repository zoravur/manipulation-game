from typing import Literal, Optional
import json
from uuid import uuid4

from pydantic import BaseModel

from manipulation_game.config import REQUEST_SEED
from manipulation_game.game import Game
from manipulation_game.judge import judge_recommendation
from manipulation_game.sample import extend_conversation_with_tools
from manipulation_game.templating import load_all_restaurant_jsons, template
from manipulation_game.tools import ExitWithRestaurantDecision



class GameResults(BaseModel):
    recommended_restaurant: str
    chosen_restaurant: str
    quality: dict[str, str]
    transcript: list[dict]


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
        self.messages:list[dict] = [
            {"role": "system", "content": system_prompt}
        ]

    def _add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})

    def _add_assistant_message(self, content: str):
        self.messages.append({"role": "assistant", "content": content})

    # def pending_tool_call_id(self) -> Optional[str]:
    #     if len(self.messages) == 0:
    #         return None
    #     last_message = self.messages[-1]
    #     if last_message["role"] != "assistant":
    #         return None
    #     if "tool_call_id" not in last_message:
    #         return None
    #     return last_message["tool_call_id"]

    # def _add_tool_response(self, tool_response: dict):
    #     self.messages.append({
    #         "role": "tool",
    #         "tool_call_id": self.pending_tool_call_id()
    #         "content": json.dumps(tool_response),
    #     })

    def add_tool_call_and_response(self, tool_name: str, arguments: dict, tool_response: dict) -> None:
        id = uuid4().hex
        self.messages.append({
            "role": "assistant",
            "content": "",
            "tool_calls": [{
                "id": id,
                "function": {
                    "name": tool_name,
                    "arguments": json.dumps(arguments),
                }
            }],
        })
        self.messages.append({
            "role": "tool",
            "tool_call_id": id,
            "content": json.dumps(tool_response),
        })

    async def add_user_message_and_respond(self, content: str | None, seed: int | None, turn: int) -> str:
        """May raise ExitWithRestaurantDecision."""
        if content is not None:
            self._add_user_message(content)

        tools = B_TOOLS if self.player == "B" else []
        
        response = await extend_conversation_with_tools(
            model=self.model,
            messages=list(self.messages),
            tools=tools,
            tool_choice="none" if len(tools) == 0 or turn==0 else "auto",
            persona=self.player,
            seed=REQUEST_SEED if seed is None else seed,
        )
        self._add_assistant_message(response)
        return response
    

async def run_agents(
    agent_a: Agent,
    agent_b: Agent,
    max_turns: int,
    seed: int | None,
) -> tuple[str, list[dict]]:
    logical_transcript = []
    try:
        a_message = None
        for turn in range(max_turns):
            print(f"--- Turn {turn + 1} ---")
            print("Agent B's turn:")
            b_message = await agent_b.add_user_message_and_respond(a_message, seed=seed, turn=turn)
            logical_transcript.append({"player": "B", "message": b_message})
            print(b_message)
            print("\nAgent A's turn:")
            a_message = await agent_a.add_user_message_and_respond(b_message, seed=seed, turn=turn)
            logical_transcript.append({"player": "A", "message": a_message})
            print(a_message)
            print()
        return "" , logical_transcript  # no restaurant decision within the given turns
    except ExitWithRestaurantDecision as e:
        print(f"Conversation ended with restaurant decision: {e.decision}")
        return e.decision, logical_transcript
    

async def run_game(game: Game) -> list[GameResults]:
    d = load_all_restaurant_jsons(game, 0)

    agent_a = Agent(
        player="A",
        model=game.a_model,
        system_prompt=template(
            player="A",
            game=game,
            restaurant_json=d,
            iteration=0,
        ).sys,
    )
    agent_b = Agent(
        player="B",
        model=game.b_model,
        system_prompt=template(
            player="B",
            game=game,
            restaurant_json=d,
            iteration=0,
        ).sys,
    )

    all_results = []
    for iteration in range(game.num_iterations):
        print(f"=== Iteration {iteration + 1}/{game.num_iterations} ===")
        chosen_restaurant, logical_transcript = await run_agents(
            agent_a=agent_a,
            agent_b=agent_b,
            max_turns=game.max_turns_per_conversation,
            seed=game.seed,
        )
        recommended_restaurant = await judge_recommendation(
            game=game,
            restaurant_json=d,
            messages=logical_transcript,
        ) or ""

        quality = {
            r["name"]: r["quality"] for r in d.values()
        }

        all_results.append(GameResults(
            recommended_restaurant=recommended_restaurant,
            chosen_restaurant=chosen_restaurant,
            quality=quality,
            transcript=logical_transcript,
        ))
        if chosen_restaurant in d:
            experience = d[chosen_restaurant]["experience"]
        else:
            experience = "No dining experience."
        print(f"Dining experience at {chosen_restaurant}: {experience}\n")

        # segue
        if iteration + 1 < game.num_iterations:
            d = load_all_restaurant_jsons(game, iteration + 1)
            new_a_prompt = template(
                player="A",
                game=game,
                restaurant_json=d,
                iteration=iteration + 1,
                override_path="dynamic_with_continuations/cont_message_templateA.jinja",
            ).sys
            new_b_prompt = template(
                player="B",
                game=game,
                restaurant_json=d,
                iteration=iteration + 1,
                override_path="dynamic_with_continuations/cont_message_templateB.jinja",
            ).sys
            agent_a._add_user_message(new_a_prompt)
            agent_b.add_tool_call_and_response("make_restaurant_decision", {"restaurant": chosen_restaurant}, {"experience": experience})
            agent_b._add_user_message(new_b_prompt)

    return all_results

if __name__ == "__main__":
    g = Game.model_validate(json.load(open("example_game.json")))
    results = run_game(g)
    print("Game Results:")
    print(results)