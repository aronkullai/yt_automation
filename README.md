# yt_automation

Production-oriented MVP for a fully automated faceless finance Shorts/TikTok pipeline.

Claude owns all content decisions:

- video ideas
- titles
- scripts
- hooks
- storytelling
- descriptions
- hashtags

The Python system owns orchestration, validation, deduplication, scene parsing, animation instructions, TTS, subtitles, rendering, thumbnails, storage, scheduling, and exports.

## Architecture

```text
CLI / Scheduler
  -> VideoOrchestrator
  -> ClaudeService
  -> SQLite VideoRepository
  -> Scene Parser + Animation Instructions
  -> Configurable TTS Provider
  -> Subtitle Generator
  -> Pillow/FFmpeg Programmatic Renderer
  -> Thumbnail Generator
  -> Final MP4 + Metadata + Database Records
```

The renderer is deliberately programmatic: Python draws minimalist black-and-white stickman finance scenes frame-by-frame with Pillow, then FFmpeg encodes the vertical video and muxes narration/music/subtitles. The rendering boundary is isolated in `yt_automation/renderer.py`, so it can be swapped for Manim or Remotion later without changing Claude, database, scheduler, or TTS layers.

## Folder Structure

```text
yt_automation/
  audio.py          TTS providers: mock, Edge TTS, ElevenLabs
  claude.py         Claude Messages API layer and JSON prompts
  cli.py            init-db, generate-one, generate-batch, schedule, dry-run
  config.py         environment-driven settings
  content.py        scene parser, scene metadata, animation instructions
  database.py       SQLite schema and repository
  orchestrator.py   end-to-end video pipeline
  renderer.py       vertical stickman renderer and FFmpeg export
  scheduler.py      scheduled batch generation
  schemas.py        typed pipeline data objects
  subtitles.py      synced SRT generation
  thumbnails.py     deterministic thumbnail generation
```

## Database

SQLite MVP:

- `videos`
- `scenes`
- `assets`
- `generation_runs`

The app uses a repository layer around `DATABASE_URL`. Today it supports `sqlite:///...`; PostgreSQL can be added behind the same repository boundary with SQLAlchemy or psycopg without changing the orchestration code.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full schema and roadmap.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python -m yt_automation.cli init-db
```

Set `ANTHROPIC_API_KEY` in `.env`.

## Commands

Smoke test without API keys:

```powershell
python -m yt_automation.cli dry-run
```

Generate one complete video:

```powershell
python -m yt_automation.cli generate-one
```

Generate multiple videos:

```powershell
python -m yt_automation.cli generate-batch --count 5
```

Run the scheduler:

```powershell
python -m yt_automation.cli schedule
```

Outputs are stored under:

```text
outputs/videos/
outputs/yt_automation.db
```

## TTS Providers

```env
TTS_PROVIDER=mock
TTS_PROVIDER=edge
TTS_PROVIDER=elevenlabs
```

`mock` is useful for infrastructure tests. Use `edge` or `elevenlabs` for production narration.

## Docker

```powershell
docker compose up --build
```

The container runs the scheduler by default and mounts `outputs/` plus `assets/`.

## Implementation Roadmap

1. Core backend: config, logging, SQLite, repository, CLI.
2. Claude: topic generation, content generation, JSON validation, retry-on-invalid JSON.
3. Content structuring: scene parsing, metadata, animation instructions.
4. Audio/subtitles: configurable TTS, SRT generation, subtitle sync from scene timing.
5. Rendering: vertical 1080x1920 stickman scenes, background music, FFmpeg export.
6. Storage: final MP4, thumbnail, narration, subtitles, scene metadata, DB records.
7. Automation: scheduled generation, batch generation, duplicate prevention.
8. Production upgrades: PostgreSQL repository, job queue, publisher integrations, better TTS alignment, Manim/Remotion renderer option.
