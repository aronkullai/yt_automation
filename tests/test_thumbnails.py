from yt_automation.config import Settings
from yt_automation.content import build_animation_instructions, parse_scenes
from yt_automation.thumbnails import ThumbnailGenerator


def test_thumbnail_generator_creates_image(tmp_path):
    settings = Settings(output_dir=tmp_path, video_width=360, video_height=640)
    scenes = [build_animation_instructions(scene) for scene in parse_scenes("Invest $100 and compare the result.")]
    path = ThumbnailGenerator(settings).generate("Test Finance Video", scenes, tmp_path / "thumb.png")

    assert path.exists()
    assert path.stat().st_size > 0
