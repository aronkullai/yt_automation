import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .prompts import SYSTEM_PROMPT, build_user_prompt
from .validation import ScriptValidationError, parse_script_response


ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
JSON_RETRY_PROMPT = "Your last response was not valid JSON. Respond with ONLY the JSON object, no other text."


@dataclass(frozen=True)
class ClaudeConfig:
    api_key: str
    model: str = "claude-sonnet-4-6"
    anthropic_version: str = "2023-06-01"
    max_tokens: int = 3000
    temperature: float = 0.7

    @classmethod
    def from_env(cls) -> "ClaudeConfig":
        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required.")

        return cls(
            api_key=api_key,
            model=os.environ.get("ANTHROPIC_MODEL", cls.model).strip() or cls.model,
            anthropic_version=os.environ.get("ANTHROPIC_VERSION", cls.anthropic_version).strip()
            or cls.anthropic_version,
            max_tokens=int(os.environ.get("ANTHROPIC_MAX_TOKENS", cls.max_tokens)),
            temperature=float(os.environ.get("ANTHROPIC_TEMPERATURE", cls.temperature)),
        )


class ClaudeScriptClient:
    def __init__(self, config: ClaudeConfig) -> None:
        self.config = config

    def generate_script_pair(self, pillar: str, angle: str, trend_hook: str | None = None) -> dict[str, Any]:
        messages = [{"role": "user", "content": build_user_prompt(pillar, angle, trend_hook)}]
        raw_text = self._send(messages)

        try:
            return parse_script_response(raw_text)
        except ScriptValidationError:
            retry_messages = [
                *messages,
                {"role": "assistant", "content": raw_text},
                {"role": "user", "content": JSON_RETRY_PROMPT},
            ]
            return parse_script_response(self._send(retry_messages))

    def _send(self, messages: list[dict[str, str]]) -> str:
        body = {
            "model": self.config.model,
            "system": SYSTEM_PROMPT,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }

        request = urllib.request.Request(
            ANTHROPIC_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "x-api-key": self.config.api_key,
                "anthropic-version": self.config.anthropic_version,
                "content-type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                response_body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Claude API request failed with HTTP {exc.code}: {error_body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Claude API request failed: {exc}") from exc

        return _extract_text(response_body)


def _extract_text(response_body: dict[str, Any]) -> str:
    parts = []
    for block in response_body.get("content", []):
        if block.get("type") == "text":
            parts.append(block.get("text", ""))

    text = "".join(parts).strip()
    if not text:
        raise RuntimeError("Claude API response did not contain text content.")
    return text
