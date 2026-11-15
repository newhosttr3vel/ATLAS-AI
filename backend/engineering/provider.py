"""OpenAI-compatible model adapter with an explicit offline mock mode."""
from __future__ import annotations
import os
from typing import Any
import httpx

TOOL_DEFINITIONS = [
    {"type":"function","function":{"name":"list_files","description":"List files in the current project workspace.","parameters":{"type":"object","properties":{},"additionalProperties":False}}},
    {"type":"function","function":{"name":"read_file","description":"Read a UTF-8 text file from the current project workspace.","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"],"additionalProperties":False}}},
    {"type":"function","function":{"name":"write_file","description":"Create or replace a UTF-8 text file in the current project workspace.","parameters":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"],"additionalProperties":False}}},
    {"type":"function","function":{"name":"run_command","description":"Run one safe allowlisted test or inspection command in the workspace. Never use shell syntax.","parameters":{"type":"object","properties":{"argv":{"type":"array","items":{"type":"string"}}},"required":["argv"],"additionalProperties":False}}},
]

class OpenAICompatibleProvider:
    def __init__(self) -> None:
        self.api_key = os.getenv("LLM_API_KEY", "").strip()
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.model = os.getenv("LLM_MODEL", "").strip()

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.model)

    def complete(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        if not self.configured:
            raise RuntimeError("Configure LLM_API_KEY and LLM_MODEL to enable live coding.")
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"model": self.model, "messages": messages, "tools": TOOL_DEFINITIONS, "tool_choice": "auto", "temperature": 0.15},
            timeout=90.0,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]
