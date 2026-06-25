from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .config import Settings
from .renderer import draw_stickman, wrap_text
from .schemas import Scene


class ThumbnailGenerator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate(self, title: str, scenes: list[Scene], output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGB", (self.settings.video_width, self.settings.video_height), "white")
        draw = ImageDraw.Draw(image)
        title_font = _font(86)
        accent_font = _font(120)
        small_font = _font(44)

        draw.rectangle((54, 54, self.settings.video_width - 54, self.settings.video_height - 54), outline="black", width=8)
        draw_stickman(draw, 210, 1120, scale=2.2, action="pointing")
        draw.line((390, 1180, 850, 760), fill="black", width=12)
        draw.polygon([(850, 760), (790, 770), (830, 820)], fill="black")
        draw.text((700, 650), "$", fill="black", font=accent_font, anchor="mm")

        key_number = _first_number(scenes)
        if key_number:
            draw.text((540, 360), key_number, fill="black", font=accent_font, anchor="mm")

        y = 1320
        for line in wrap_text(title.upper(), title_font, self.settings.video_width - 180):
            draw.text((90, y), line, fill="black", font=title_font)
            y += 96
        draw.text((90, self.settings.video_height - 160), "FINANCE SIMULATION", fill="black", font=small_font)
        image.save(output_path)
        return output_path


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _first_number(scenes: list[Scene]) -> str:
    for scene in scenes:
        numbers = scene.metadata.get("numbers", [])
        if numbers:
            return str(numbers[0])
    return ""
