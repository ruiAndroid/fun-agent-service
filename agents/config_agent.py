from .base import AgentInput, BaseAgent


class ConfigAgent(BaseAgent):
    def __init__(
        self,
        *,
        name: str,
        description: str,
        model: str,
        language: str,
        prompt: str,
        display_name: str = "",
        handle: str = "",
    ):
        self.name = name
        self.display_name = display_name
        self.handle = handle
        self.description = description
        self.model = model
        self.language = language
        self.prompt = prompt

    def run(self, payload: AgentInput) -> str:
        return (
            f"【{self.name}】model={self.model} lang={self.language}\n"
            f"{self.prompt}\n"
            f"用户输入：{payload.text}"
        )
