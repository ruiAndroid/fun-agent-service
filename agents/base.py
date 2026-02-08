from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class AgentInput:
    text: str
    context: Dict[str, Any]
    trace_id: Optional[str] = None


class BaseAgent:
    name: str = "base"
    display_name: str = ""
    handle: str = ""
    description: str = ""
    model: str = "gpt-4o-mini"
    language: str = "zh-CN"

    def run(self, payload: AgentInput) -> str:
        raise NotImplementedError
