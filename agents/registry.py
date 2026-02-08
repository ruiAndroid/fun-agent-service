from __future__ import annotations

import importlib
import json
import os
import pkgutil
from typing import Any, Dict, List

from .base import AgentInput, BaseAgent
from .config_agent import ConfigAgent


REGISTRY: Dict[str, BaseAgent] = {}


def _register(agent: BaseAgent):
    if not agent.name:
        raise ValueError("Agent missing name")
    REGISTRY[agent.name] = agent


def _load_python_agents():
    package_dir = os.path.dirname(__file__)
    for mod in pkgutil.iter_modules([package_dir]):
        if mod.name in {"base", "registry", "config_agent"}:
            continue
        module = importlib.import_module(f"{__package__}.{mod.name}")
        agent = getattr(module, "AGENT", None)
        if agent and isinstance(agent, BaseAgent):
            _register(agent)


def _load_config_agents():
    configs_dir = os.path.join(os.path.dirname(__file__), "configs")
    if not os.path.isdir(configs_dir):
        return
    for name in os.listdir(configs_dir):
        if not name.endswith(".json"):
            continue
        path = os.path.join(configs_dir, name)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or not data.get("name"):
            # skip non-agent configs (e.g. llm.json)
            continue
        agent = ConfigAgent(
            name=data["name"],
            description=data.get("description", ""),
            model=data.get("model", "gpt-4o-mini"),
            language=data.get("language", "zh-CN"),
            prompt=data.get("prompt", ""),
            display_name=data.get("display_name", ""),
            handle=data.get("handle", ""),
        )
        _register(agent)


def _ensure_loaded():
    if REGISTRY:
        return
    _load_python_agents()
    _load_config_agents()


def list_agents() -> List[Dict[str, str]]:
    _ensure_loaded()
    return [
        {
            "code": a.name,
            "name": a.name,
            "display_name": a.display_name or a.name,
            "handle": a.handle,
            "description": a.description,
        }
        for a in REGISTRY.values()
    ]


def run_agent(name: str, text: str, context: Dict[str, Any]) -> str:
    _ensure_loaded()
    if not name or name not in REGISTRY:
        raise ValueError(f"Unknown agent: {name}")
    agent = REGISTRY[name]
    return agent.run(
        AgentInput(
            text=text,
            context=context,
            trace_id=context.get("trace_id") if isinstance(context, dict) else None,
        )
    )
