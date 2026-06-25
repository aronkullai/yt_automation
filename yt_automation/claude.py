import json
import time
import urllib.error
import urllib.request
from dataclasses import asdict
from typing import Any

from .config import Settings
from .schemas import GeneratedContent, VideoIdea


ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
JSON_RETRY_PROMPT = "Your last response was not valid JSON. Respond with ONLY the JSON object, no markdown, no preamble."

SYSTEM_PROMPT = """You are the content engine for a faceless finance Shorts and TikTok channel.

You own all content decisions: topics, hooks, storytelling, titles, descriptions, and hashtags.
The software will only validate JSON, deduplicate topics, and render what you provide.

Channel limits:
- Finance only: personal finance, investing, wealth building, economics, money psychology, What If stories, Your Life As stories, rich vs poor comparisons, compound interest simulations, financial life simulations.
- Visual style: minimalist black-and-white stickman animation, simple charts, arrows, dollar signs, houses, cars, investment graphs, clean educational pacing.
- Do not name specific brokerages, funds, or financial products.
- Do not present modeled investment returns as guarantees.
- Do not give individualized financial advice.
- Keep scripts short, punchy, spoken, and visual.
"""


IDEA_PROMPT = """Generate one new video idea for a vertical faceless finance Short.

Avoid these previously used topics:
{recent_topics}

Respond with ONLY valid JSON:
{{
  "topic": "specific finance video topic",
  "angle": "specific storytelling angle",
  "pillar": "one of: What If You Invested, Your Life As, Money Mistakes, Personal Finance Simulations, Compound Interest Stories, Rich vs Poor Comparisons",
  "why_it_works": "short reason this topic should hook viewers"
}}
"""


SCRIPT_PROMPT = """Create the complete content package for this video idea:
{idea_json}

Return ONLY valid JSON:
{{
  "title": "short compelling title",
  "script": "full narrated script for a 35-60 second vertical video. Include scene or timestamp breaks if useful.",
  "description": "platform-ready video description",
  "hashtags": ["finance hashtag", "money hashtag"]
}}

Do not include markdown. Do not include fields outside this schema.
"""


class ClaudeService:
    def __init__(self, settings: Settings) -> None:
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required for Claude content generation.")
        self.settings = settings

    def generate_idea(self, recent_topics: list[str]) -> VideoIdea:
        prompt = IDEA_PROMPT.format(recent_topics=json.dumps(recent_topics, ensure_ascii=False))
        payload = self._request_json([{"role": "user", "content": prompt}])
        return VideoIdea(
            topic=_required_string(payload, "topic"),
            angle=_required_string(payload, "angle"),
            pillar=_required_string(payload, "pillar"),
            why_it_works=str(payload.get("why_it_works", "")),
        )

    def generate_content(self, idea: VideoIdea) -> GeneratedContent:
        prompt = SCRIPT_PROMPT.format(idea_json=json.dumps(asdict(idea), ensure_ascii=False, indent=2))
        payload = self._request_json([{"role": "user", "content": prompt}])
        hashtags = payload.get("hashtags", [])
        if not isinstance(hashtags, list) or not all(isinstance(item, str) for item in hashtags):
            raise ValueError("Claude content response must include `hashtags` as an array of strings.")
        return GeneratedContent(
            title=_required_string(payload, "title"),
            script=_required_string(payload, "script"),
            description=_required_string(payload, "description"),
            hashtags=hashtags,
        )

    def _request_json(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        raw_text = self._send(messages)
        try:
            return _parse_json_object(raw_text)
        except ValueError:
            retry_messages = [
                *messages,
                {"role": "assistant", "content": raw_text},
                {"role": "user", "content": JSON_RETRY_PROMPT},
            ]
            return _parse_json_object(self._send(retry_messages))

    def _send(self, messages: list[dict[str, str]]) -> str:
        body = {
            "model": self.settings.anthropic_model,
            "system": SYSTEM_PROMPT,
            "messages": messages,
            "max_tokens": self.settings.anthropic_max_tokens,
            "temperature": self.settings.anthropic_temperature,
        }
        request = urllib.request.Request(
            ANTHROPIC_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "x-api-key": self.settings.anthropic_api_key,
                "anthropic-version": self.settings.anthropic_version,
                "content-type": "application/json",
            },
            method="POST",
        )
        response_body = self._urlopen_json_with_retry(request)

        text_parts = [block.get("text", "") for block in response_body.get("content", []) if block.get("type") == "text"]
        text = "".join(text_parts).strip()
        if not text:
            raise RuntimeError("Claude API response did not contain text content.")
        return text

    def _urlopen_json_with_retry(self, request: urllib.request.Request) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(1, self.settings.max_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                error_body = exc.read().decode("utf-8", errors="replace")
                if exc.code not in {429, 500, 502, 503, 504} or attempt == self.settings.max_retries:
                    raise RuntimeError(f"Claude API request failed with HTTP {exc.code}: {error_body}") from exc
                last_error = exc
            except urllib.error.URLError as exc:
                if attempt == self.settings.max_retries:
                    raise RuntimeError(f"Claude API request failed: {exc}") from exc
                last_error = exc
            time.sleep(min(2**attempt, 10))
        raise RuntimeError(f"Claude API request failed after retries: {last_error}")


def _parse_json_object(raw_text: str) -> dict[str, Any]:
    payload = json.loads(raw_text)
    if not isinstance(payload, dict):
        raise ValueError("Claude response must be a JSON object.")
    return payload


def _required_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Claude response missing non-empty string field `{field}`.")
    return value.strip()
