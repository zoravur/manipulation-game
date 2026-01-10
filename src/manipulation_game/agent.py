from typing import Literal

from manipulation_game.sample import extend_conversation_with_tools


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

    def add_user_message_and_respond(self, content: str) -> str:
        self._add_user_message(content)
        
        response = extend_conversation_with_tools(
            model=self.model,
            messages=self.messages,
            tools=[],
            tool_choice="none",
        )
        self._add_assistant_message(response)
        return response