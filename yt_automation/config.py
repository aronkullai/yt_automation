import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    anthropic_version: str = os.getenv("ANTHROPIC_VERSION", "2023-06-01")
    anthropic_max_tokens: int = int(os.getenv("ANTHROPIC_MAX_TOKENS", "3000"))
    anthropic_temperature: float = float(os.getenv("ANTHROPIC_TEMPERATURE", "0.8"))

    database_url: str = os.getenv("DATABASE_URL", "sqlite:///outputs/yt_automation.db")
    output_dir: Path = Path(os.getenv("OUTPUT_DIR", "outputs"))
    assets_dir: Path = Path(os.getenv("ASSETS_DIR", "assets"))

    tts_provider: str = os.getenv("TTS_PROVIDER", "mock")
    tts_voice: str = os.getenv("TTS_VOICE", "en-US-GuyNeural")
    elevenlabs_api_key: str = os.getenv("ELEVENLABS_API_KEY", "")
    elevenlabs_voice_id: str = os.getenv("ELEVENLABS_VOICE_ID", "")

    video_width: int = int(os.getenv("VIDEO_WIDTH", "1080"))
    video_height: int = int(os.getenv("VIDEO_HEIGHT", "1920"))
    video_fps: int = int(os.getenv("VIDEO_FPS", "24"))
    render_draft: bool = os.getenv("RENDER_DRAFT", "0") == "1"

    background_music_path: str = os.getenv("BACKGROUND_MUSIC_PATH", "")
    background_music_volume: float = float(os.getenv("BACKGROUND_MUSIC_VOLUME", "0.12"))
    narration_volume: float = float(os.getenv("NARRATION_VOLUME", "1.0"))

    videos_per_day: int = int(os.getenv("VIDEOS_PER_DAY", "3"))
    generation_times: str = os.getenv("GENERATION_TIMES", "09:00,13:00,17:00")
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))


def get_settings() -> Settings:
    settings = Settings()
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    settings.assets_dir.mkdir(parents=True, exist_ok=True)
    return settings
