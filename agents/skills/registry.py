from typing import Optional

from .llm import LLMClient


class SkillRegistry:
    def __init__(self) -> None:
        self._llm: Optional[LLMClient] = None

    def llm(self) -> LLMClient:
        if self._llm is None:
            self._llm = LLMClient()
        return self._llm


registry = SkillRegistry()
