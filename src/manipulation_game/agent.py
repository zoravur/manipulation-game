from dataclasses import dataclass
from typing import Literal

from manipulation_game.sample import extend_conversation_with_tools
from manipulation_game.tools import ExitWithRestaurantDecision


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
            tool_choice="none",
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