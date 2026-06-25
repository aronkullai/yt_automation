import re

from .schemas import Scene


TIMESTAMP_PATTERN = re.compile(
    r"(?:\(|\[)?(?P<start>\d{1,2}(?::\d{2})?|[0-9]+)s?\s*[-–]\s*(?P<end>\d{1,2}(?::\d{2})?|[0-9]+)s?(?:\)|\])?\s*",
    re.IGNORECASE,
)


def parse_scenes(script: str, target_duration: float = 50.0) -> list[Scene]:
    timestamped = _parse_timestamped(script)
    if timestamped:
        return timestamped
    return _parse_by_sentence(script, target_duration)


def generate_scene_metadata(scene: Scene) -> Scene:
    narration = scene.narration.lower()
    scene_type = scene.scene_type
    if scene.index == 1:
        scene_type = "hook"
    elif any(word in narration for word in ("finally", "by age", "after", "result", "ends with")):
        scene_type = "reveal"
    elif any(word in narration for word in ("subscribe", "follow", "next")):
        scene_type = "cta"

    metadata = {
        "keywords": _extract_keywords(scene.narration),
        "numbers": re.findall(r"\$?\d[\d,]*(?:\.\d+)?%?", scene.narration),
        "estimated_words": len(scene.narration.split()),
    }
    return Scene(
        index=scene.index,
        narration=scene.narration,
        duration_seconds=scene.duration_seconds,
        visual_description=_visual_description(scene.narration, scene_type),
        scene_type=scene_type,
        metadata=metadata,
        animation=scene.animation,
    )


def build_animation_instructions(scene: Scene) -> Scene:
    text = scene.narration
    numbers = scene.metadata.get("numbers", [])
    lowered = text.lower()
    objects = []
    if any(word in lowered for word in ("invest", "compound", "portfolio", "market", "return")):
        objects.append({"type": "line_chart", "label": "Growth", "trend": "up"})
    if any(word in lowered for word in ("house", "rent", "mortgage")):
        objects.append({"type": "house"})
    if any(word in lowered for word in ("car", "payment")):
        objects.append({"type": "car"})
    if any(word in lowered for word in ("debt", "credit", "interest")):
        objects.append({"type": "warning_arrow"})
    if not objects:
        objects.append({"type": "dollar_sign"})

    animation = {
        "background": "white",
        "characters": [{"type": "stickman", "position": "left", "action": _stickman_action(scene.scene_type)}],
        "objects": objects,
        "text": [{"content": number, "position": "top"} for number in numbers[:3]],
        "transition": "draw",
    }
    return Scene(
        index=scene.index,
        narration=scene.narration,
        duration_seconds=scene.duration_seconds,
        visual_description=scene.visual_description,
        scene_type=scene.scene_type,
        metadata=scene.metadata,
        animation=animation,
    )


def _parse_timestamped(script: str) -> list[Scene]:
    matches = list(TIMESTAMP_PATTERN.finditer(script))
    scenes = []
    for index, match in enumerate(matches, start=1):
        start = _timestamp_to_seconds(match.group("start"))
        end = _timestamp_to_seconds(match.group("end"))
        content_start = match.end()
        content_end = matches[index].start() if index < len(matches) else len(script)
        narration = script[content_start:content_end].strip(" \n:-")
        if narration:
            scenes.append(
                Scene(
                    index=index,
                    narration=narration,
                    duration_seconds=max(1.5, end - start),
                    visual_description="",
                    scene_type="build",
                )
            )
    return [generate_scene_metadata(scene) for scene in scenes]


def _parse_by_sentence(script: str, target_duration: float) -> list[Scene]:
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", script) if part.strip()]
    if not sentences:
        sentences = [script.strip()]

    chunks = []
    current = []
    for sentence in sentences:
        current.append(sentence)
        if len(" ".join(current).split()) >= 18:
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))

    total_words = sum(max(1, len(chunk.split())) for chunk in chunks)
    scenes = []
    for index, chunk in enumerate(chunks, start=1):
        duration = target_duration * (len(chunk.split()) / total_words)
        scenes.append(
            generate_scene_metadata(
                Scene(
                    index=index,
                    narration=chunk,
                    duration_seconds=max(2.0, duration),
                    visual_description="",
                    scene_type="build",
                )
            )
        )
    return scenes


def _timestamp_to_seconds(value: str) -> float:
    if ":" in value:
        minutes, seconds = value.split(":", 1)
        return int(minutes) * 60 + float(seconds)
    return float(value)


def _extract_keywords(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z]{4,}", text.lower())
    stop_words = {"this", "that", "with", "your", "what", "when", "then", "they", "into", "from"}
    return [word for word in words if word not in stop_words][:8]


def _visual_description(narration: str, scene_type: str) -> str:
    if scene_type == "hook":
        return "Large hook number, stickman reacting, fast arrow motion."
    if scene_type == "reveal":
        return "Big final number reveal with chart and emphasis lines."
    if scene_type == "cta":
        return "Stickman points to subscribe/follow prompt."
    return f"Minimal stickman finance visual for: {narration[:120]}"


def _stickman_action(scene_type: str) -> str:
    if scene_type == "hook":
        return "surprised"
    if scene_type == "reveal":
        return "pointing"
    if scene_type == "cta":
        return "waving"
    return "walking"
