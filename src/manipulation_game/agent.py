from dataclasses import dataclass
from typing import Literal

from manipulation_game.sample import extend_conversation_with_tools


@dataclass
class AgentResponse:
    message: str
    exit: bool


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

    def add_user_message_and_respond(self, content: str | None) -> AgentResponse:
        if content is not None:
            self._add_user_message(content)
        
        response = extend_conversation_with_tools(
            model=self.model,
            messages=self.messages,
            tools=[],
            tool_choice="none",
        )
        self._add_assistant_message(response)
        return AgentResponse(message=response, exit=False)
    

def run_agents(
    agent_a: Agent,
    agent_b: Agent,
    n_turns: int,
) -> None:
    a_message = None
    for turn in range(n_turns):
        print(f"--- Turn {turn + 1} ---")
        print("Agent B's turn:")
        b_response = agent_b.add_user_message_and_respond(a_message)
        if b_response.exit:
            print("Exiting conversation.")
            return
        b_message = b_response.message
        print(b_message)
        print("\nAgent A's turn:")
        a_response = agent_a.add_user_message_and_respond(b_message)
        if a_response.exit:
            print("Exiting conversation. This shouldn't happen")
            return
        a_message = a_response.message
        print(a_message)
        print()