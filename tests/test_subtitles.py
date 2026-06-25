from yt_automation.schemas import Scene
from yt_automation.subtitles import SubtitleGenerator


def test_subtitle_generator_writes_srt(tmp_path):
    path = SubtitleGenerator().write_srt(
        [
            Scene(1, "First line", 2.5, "visual", "hook"),
            Scene(2, "Second line", 3.0, "visual", "build"),
        ],
        tmp_path / "test.srt",
    )

    text = path.read_text(encoding="utf-8")
    assert "00:00:00,000 --> 00:00:02,500" in text
    assert "Second line" in text
