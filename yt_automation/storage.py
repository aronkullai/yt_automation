import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def topic_fingerprint(pillar: str, angle: str, trend_hook: str | None = None) -> str:
    normalized = " ".join(part.strip().lower() for part in (pillar, angle, trend_hook or "") if part.strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


class TopicCache:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._items = self._load()

    def seen(self, fingerprint: str) -> bool:
        return fingerprint in self._items

    def add(self, fingerprint: str, metadata: dict[str, Any]) -> None:
        self._items[fingerprint] = {
            **metadata,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.path.write_text(json.dumps(self._items, indent=2, ensure_ascii=False), encoding="utf-8")

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))


def save_script_response(payload: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = _slugify(payload["short"]["title"])[:80] or "script"
    path = output_dir / f"{timestamp}-{slug}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return re.sub(r"-{2,}", "-", slug)
