from pathlib import Path

from .schemas import Scene


class SubtitleGenerator:
    def write_srt(self, scenes: list[Scene], output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        current = 0.0
        blocks = []
        for scene in scenes:
            start = current
            end = current + scene.duration_seconds
            blocks.append(
                f"{scene.index}\n{_format_srt_time(start)} --> {_format_srt_time(end)}\n{scene.narration}\n"
            )
            current = end
        output_path.write_text("\n".join(blocks), encoding="utf-8")
        return output_path

    def cue_ranges(self, scenes: list[Scene]) -> list[tuple[float, float, str]]:
        ranges = []
        current = 0.0
        for scene in scenes:
            end = current + scene.duration_seconds
            ranges.append((current, end, scene.narration))
            current = end
        return ranges


def _format_srt_time(seconds: float) -> str:
    milliseconds = int((seconds - int(seconds)) * 1000)
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
