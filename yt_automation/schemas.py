from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class VideoStatus(str, Enum):
    REQUESTED = "requested"
    SCRIPTED = "scripted"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class VideoIdea:
    topic: str
    angle: str
    pillar: str
    why_it_works: str = ""


@dataclass(frozen=True)
class GeneratedContent:
    title: str
    script: str
    description: str
    hashtags: list[str]


@dataclass(frozen=True)
class Scene:
    index: int
    narration: str
    duration_seconds: float
    visual_description: str
    scene_type: str
    metadata: dict[str, Any] = field(default_factory=dict)
    animation: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GeneratedVideo:
    video_id: int
    title: str
    topic: str
    final_video_path: str
    thumbnail_path: str
    subtitle_path: str
