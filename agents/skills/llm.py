import json
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional


def _default_config_path() -> str:
    # agents/skills/llm.py -> agents/configs/llm.json
    import os

    here = os.path.dirname(__file__)
    return os.path.normpath(os.path.join(here, "..", "configs", "llm.json"))


def _load_file_config() -> Dict[str, Any]:
    # Only read config from file (do not depend on environment variables).
    import os

    path = _default_config_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


class LLMClient:
    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 30,
    ):
        cfg = _load_file_config()
        self.base_url = (
            (base_url or cfg.get("base_url") or "http://localhost:8000")
        ).rstrip("/")
        self.api_key = api_key or cfg.get("api_key")
        self.model = model or cfg.get("model") or "gpt-4o-mini"
        self.timeout = int(cfg.get("timeout") or timeout)

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float = 0.2,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        if not self.api_key:
            raise ValueError("LLM api_key not set (check agents/configs/llm.json)")

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if extra:
            payload.update(extra)

        url = f"{self.base_url}/v1/chat/completions"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise ValueError(f"LLM HTTP {exc.code}: {body}") from exc

        choices = data.get("choices") or []
        if not choices:
            raise ValueError("LLM response has no choices")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not isinstance(content, str):
            raise ValueError("LLM response missing content")
        return content
