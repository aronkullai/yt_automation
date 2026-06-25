import logging
from pathlib import Path

from .audio import TTSFactory
from .claude import ClaudeService
from .config import Settings
from .content import build_animation_instructions, parse_scenes
from .database import Database, VideoRepository
from .renderer import VideoRenderer
from .schemas import GeneratedVideo
from .subtitles import SubtitleGenerator
from .thumbnails import ThumbnailGenerator
from .utils import slugify, write_json


logger = logging.getLogger(__name__)


class VideoOrchestrator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.database = Database(settings.database_url)
        self.database.migrate()
        self.repository = VideoRepository(self.database)
        self.claude = ClaudeService(settings)
        self.tts = TTSFactory.create(settings)
        self.subtitles = SubtitleGenerator()
        self.renderer = VideoRenderer(settings)
        self.thumbnails = ThumbnailGenerator(settings)

    def generate_one(self) -> GeneratedVideo:
        idea = self._new_unique_idea()
        video_id = self.repository.create_requested_video(idea)
        logger.info("Created requested video %s for topic: %s", video_id, idea.topic)

        try:
            content = self.claude.generate_content(idea)
            self.repository.attach_content(video_id, content)

            scenes = [build_animation_instructions(scene) for scene in parse_scenes(content.script)]
            self.repository.replace_scenes(video_id, scenes)

            video_dir = self.settings.output_dir / "videos" / f"{video_id:06d}-{slugify(content.title)}"
            video_dir.mkdir(parents=True, exist_ok=True)
            write_json(video_dir / "content.json", {"idea": idea.__dict__, "content": content.__dict__})
            write_json(video_dir / "scenes.json", [scene.__dict__ for scene in scenes])

            narration_path = self.tts.generate(content.script, video_dir / "narration.wav")
            subtitle_path = self.subtitles.write_srt(scenes, video_dir / "subtitles.srt")
            thumbnail_path = self.thumbnails.generate(content.title, scenes, video_dir / "thumbnail.png")
            final_video_path = self.renderer.render(content.title, scenes, narration_path, subtitle_path, video_dir)

            duration = sum(scene.duration_seconds for scene in scenes)
            self.repository.add_asset(video_id, "narration", str(narration_path))
            self.repository.add_asset(video_id, "subtitles", str(subtitle_path))
            self.repository.add_asset(video_id, "thumbnail", str(thumbnail_path))
            self.repository.add_asset(video_id, "video", str(final_video_path))
            self.repository.complete_video(video_id, str(final_video_path), str(thumbnail_path), str(subtitle_path), duration)

            return GeneratedVideo(
                video_id=video_id,
                title=content.title,
                topic=idea.topic,
                final_video_path=str(final_video_path),
                thumbnail_path=str(thumbnail_path),
                subtitle_path=str(subtitle_path),
            )
        except Exception as exc:
            self.repository.fail_video(video_id, str(exc))
            raise

    def generate_batch(self, count: int) -> list[GeneratedVideo]:
        return [self.generate_one() for _ in range(count)]

    def _new_unique_idea(self):
        recent_topics = self.repository.recent_topics()
        for attempt in range(self.settings.max_retries):
            idea = self.claude.generate_idea(recent_topics)
            if not self.repository.topic_exists(idea.topic):
                return idea
            logger.info("Claude returned duplicate topic on attempt %s: %s", attempt + 1, idea.topic)
            recent_topics.append(idea.topic)
        raise RuntimeError("Claude returned duplicate topics too many times.")


class DryRunOrchestrator:
    """Dependency-free architecture smoke test for machines without API keys."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def generate_one(self) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / "dry-run.txt"
        path.write_text("Pipeline wiring is importable. Set ANTHROPIC_API_KEY to generate real content.\n", encoding="utf-8")
        return path
