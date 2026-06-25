# Architecture

## Responsibility Split

Claude is the only content brain. The software never hardcodes video ideas, hooks, titles, stories, descriptions, or hashtags.

The software handles:

- requesting a new idea from Claude
- requesting a complete content package from Claude
- JSON validation and retry-on-invalid JSON
- duplicate topic prevention
- scene parsing
- scene metadata extraction
- animation instruction generation
- TTS
- subtitle timing
- vertical video rendering
- thumbnail generation
- background music muxing
- database persistence
- batch/scheduled generation

## Pipeline

```text
yt_automation.cli
  -> VideoOrchestrator
  -> ClaudeService.generate_idea()
  -> VideoRepository.topic_exists()
  -> ClaudeService.generate_content()
  -> parse_scenes()
  -> generate_scene_metadata()
  -> build_animation_instructions()
  -> TTSProvider.generate()
  -> SubtitleGenerator.write_srt()
  -> ThumbnailGenerator.generate()
  -> VideoRenderer.render()
  -> VideoRepository.complete_video()
```

## Database Schema

SQLite MVP, stored at `sqlite:///outputs/yt_automation.db` by default.

### videos

- `id`
- `title`
- `topic`
- `topic_hash`
- `pillar`
- `angle`
- `script`
- `description`
- `hashtags_json`
- `status`
- `duration_seconds`
- `final_video_path`
- `thumbnail_path`
- `subtitle_path`
- `scheduled_for`
- `published_at`
- `error_message`
- `created_at`
- `updated_at`

### scenes

- `id`
- `video_id`
- `scene_index`
- `narration`
- `visual_description`
- `scene_type`
- `animation_json`
- `metadata_json`
- `duration_seconds`
- `created_at`

### assets

- `id`
- `video_id`
- `type`
- `path`
- `metadata_json`
- `created_at`

### generation_runs

- `id`
- `video_id`
- `status`
- `started_at`
- `finished_at`
- `logs_json`

## Upgrade Path

The current repository layer is intentionally narrow. PostgreSQL can be added by replacing `yt_automation.database.Database` and `VideoRepository` with a SQLAlchemy implementation while leaving the orchestrator and media modules intact.

The renderer is also isolated. The MVP renderer uses Pillow plus FFmpeg for deterministic stickman scenes. Manim or Remotion can be added as a second implementation behind the same `VideoRenderer.render(...)` boundary.

## Production Roadmap

1. Add a queue worker with Celery/RQ for parallel video generation.
2. Add PostgreSQL support via SQLAlchemy.
3. Add word-level subtitle alignment using Whisper or forced alignment.
4. Add a Manim renderer for richer finance graphs and animated math.
5. Add publishing integrations for YouTube Shorts and TikTok.
6. Add moderation/compliance review states before publishing.
7. Add dashboard/API for reviewing generated videos and retrying failed jobs.
