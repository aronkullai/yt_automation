import asyncio
import math
import wave
from abc import ABC, abstractmethod
from pathlib import Path
from urllib import request

from .config import Settings


class TTSProvider(ABC):
    @abstractmethod
    def generate(self, text: str, output_path: Path) -> Path:
        raise NotImplementedError


class MockTTSProvider(TTSProvider):
    """Creates deterministic silent WAV audio for local tests and dry infrastructure runs."""

    def generate(self, text: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        duration = max(4.0, len(text.split()) / 2.6)
        sample_rate = 44_100
        total_samples = int(duration * sample_rate)
        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            for index in range(total_samples):
                amplitude = int(180 * math.sin(2 * math.pi * 220 * index / sample_rate))
                wav_file.writeframesraw(amplitude.to_bytes(2, "little", signed=True))
        return output_path


class EdgeTTSProvider(TTSProvider):
    def __init__(self, voice: str) -> None:
        self.voice = voice

    def generate(self, text: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        asyncio.run(self._generate(text, output_path))
        return output_path

    async def _generate(self, text: str, output_path: Path) -> None:
        try:
            import edge_tts
        except ImportError as exc:
            raise RuntimeError("Install edge-tts or set TTS_PROVIDER=mock.") from exc

        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(str(output_path))


class ElevenLabsTTSProvider(TTSProvider):
    def __init__(self, api_key: str, voice_id: str) -> None:
        if not api_key or not voice_id:
            raise RuntimeError("ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID are required for ElevenLabs TTS.")
        self.api_key = api_key
        self.voice_id = voice_id

    def generate(self, text: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        payload = (
            '{"text": '
            + __import__("json").dumps(text)
            + ', "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.45, "similarity_boost": 0.75}}'
        ).encode("utf-8")
        req = request.Request(
            url,
            data=payload,
            method="POST",
            headers={"xi-api-key": self.api_key, "content-type": "application/json", "accept": "audio/mpeg"},
        )
        with request.urlopen(req, timeout=120) as response:
            output_path.write_bytes(response.read())
        return output_path


class TTSFactory:
    @staticmethod
    def create(settings: Settings) -> TTSProvider:
        provider = settings.tts_provider.lower()
        if provider == "mock":
            return MockTTSProvider()
        if provider == "edge":
            return EdgeTTSProvider(settings.tts_voice)
        if provider == "elevenlabs":
            return ElevenLabsTTSProvider(settings.elevenlabs_api_key, settings.elevenlabs_voice_id)
        raise ValueError(f"Unsupported TTS_PROVIDER: {settings.tts_provider}")
