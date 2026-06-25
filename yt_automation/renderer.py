import subprocess
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

from .config import Settings
from .schemas import Scene


class VideoRenderer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def render(self, title: str, scenes: list[Scene], narration_path: Path, subtitle_path: Path, output_dir: Path) -> Path:
        frames_dir = output_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        frame_count = self._render_frames(title, scenes, frames_dir)
        raw_video = output_dir / "animation.mp4"
        final_video = output_dir / "final.mp4"
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-framerate",
                str(self.settings.video_fps),
                "-i",
                str(frames_dir / "frame_%06d.png"),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-r",
                str(self.settings.video_fps),
                str(raw_video),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        self._mux_audio(ffmpeg, raw_video, narration_path, subtitle_path, final_video)
        if frame_count == 0:
            raise RuntimeError("Renderer produced zero frames.")
        return final_video

    def _render_frames(self, title: str, scenes: list[Scene], frames_dir: Path) -> int:
        frame_index = 0
        for scene in scenes:
            scene_frames = max(1, int(scene.duration_seconds * self.settings.video_fps))
            for local_frame in range(scene_frames):
                progress = local_frame / max(1, scene_frames - 1)
                image = self._draw_scene(title, scene, progress)
                image.save(frames_dir / f"frame_{frame_index:06d}.png")
                frame_index += 1
        return frame_index

    def _draw_scene(self, title: str, scene: Scene, progress: float) -> Image.Image:
        image = Image.new("RGB", (self.settings.video_width, self.settings.video_height), "white")
        draw = ImageDraw.Draw(image)
        title_font = _font(54)
        body_font = _font(58)
        number_font = _font(96)
        small_font = _font(38)

        draw.rectangle((42, 42, self.settings.video_width - 42, self.settings.video_height - 42), outline="black", width=5)
        draw.text((70, 80), "FINANCE SHORT", fill="black", font=small_font)

        y = 155
        for line in wrap_text(title, title_font, self.settings.video_width - 140)[:3]:
            draw.text((70, y), line, fill="black", font=title_font)
            y += 64

        action = scene.animation.get("characters", [{}])[0].get("action", "walking")
        x_offset = int(30 * progress)
        draw_stickman(draw, 240 + x_offset, 1050, scale=2.0, action=action)
        self._draw_objects(draw, scene, progress)

        number_y = 460
        for item in scene.animation.get("text", [])[:2]:
            draw.text((self.settings.video_width // 2, number_y), item["content"], fill="black", font=number_font, anchor="mm")
            number_y += 118

        subtitle_lines = wrap_text(scene.narration, body_font, self.settings.video_width - 140)[-4:]
        subtitle_height = len(subtitle_lines) * 72 + 40
        top = self.settings.video_height - subtitle_height - 80
        draw.rectangle((55, top, self.settings.video_width - 55, self.settings.video_height - 70), fill="white", outline="black", width=4)
        y = top + 22
        for line in subtitle_lines:
            draw.text((86, y), line, fill="black", font=body_font)
            y += 72
        return image

    def _draw_objects(self, draw: ImageDraw.ImageDraw, scene: Scene, progress: float) -> None:
        objects = scene.animation.get("objects", [])
        for index, item in enumerate(objects):
            item_type = item.get("type")
            if item_type == "line_chart":
                draw_chart(draw, 410, 900, 920, 1260, progress)
            elif item_type == "house":
                draw_house(draw, 610, 930)
            elif item_type == "car":
                draw_car(draw, 560, 1110)
            elif item_type == "warning_arrow":
                draw.line((560, 880, 860, 1180), fill="black", width=12)
                draw.polygon([(860, 1180), (795, 1160), (845, 1115)], fill="black")
            else:
                draw.text((720, 980 + index * 90), "$", fill="black", font=_font(140), anchor="mm")

    def _mux_audio(self, ffmpeg: str, raw_video: Path, narration_path: Path, subtitle_path: Path, final_video: Path) -> None:
        vf = f"subtitles={_ffmpeg_path(subtitle_path)}:force_style='FontName=Arial,FontSize=18,PrimaryColour=&H00000000,OutlineColour=&H00FFFFFF,BorderStyle=3'"
        command = [
            ffmpeg,
            "-y",
            "-i",
            str(raw_video),
            "-i",
            str(narration_path),
        ]
        if self.settings.background_music_path:
            command.extend(["-i", self.settings.background_music_path])
            command.extend(
                [
                    "-filter_complex",
                    f"[1:a]volume={self.settings.narration_volume}[n];[2:a]volume={self.settings.background_music_volume}[m];[n][m]amix=inputs=2:duration=first[a]",
                    "-map",
                    "0:v",
                    "-map",
                    "[a]",
                ]
            )
        else:
            command.extend(["-map", "0:v", "-map", "1:a"])
        command.extend(["-vf", vf, "-c:v", "libx264", "-c:a", "aac", "-shortest", str(final_video)])
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines = []
    current = ""
    scratch = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(scratch)
    for word in words:
        candidate = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_stickman(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0, action: str = "walking") -> None:
    r = int(34 * scale)
    body = int(120 * scale)
    arm = int(76 * scale)
    leg = int(86 * scale)
    width = max(4, int(7 * scale))
    draw.ellipse((x - r, y - body - r * 2, x + r, y - body), outline="black", width=width)
    draw.line((x, y - body, x, y - 20), fill="black", width=width)
    if action == "pointing":
        draw.line((x, y - body + 35, x + arm * 2, y - body + 10), fill="black", width=width)
        draw.line((x, y - body + 35, x - arm, y - body + 80), fill="black", width=width)
    elif action == "waving":
        draw.line((x, y - body + 35, x + arm, y - body - 45), fill="black", width=width)
        draw.line((x, y - body + 35, x - arm, y - body + 55), fill="black", width=width)
    else:
        draw.line((x, y - body + 35, x + arm, y - body + 75), fill="black", width=width)
        draw.line((x, y - body + 35, x - arm, y - body + 75), fill="black", width=width)
    draw.line((x, y - 20, x + leg, y + leg), fill="black", width=width)
    draw.line((x, y - 20, x - leg, y + leg), fill="black", width=width)


def draw_chart(draw: ImageDraw.ImageDraw, x1: int, y1: int, x2: int, y2: int, progress: float) -> None:
    draw.line((x1, y2, x2, y2), fill="black", width=6)
    draw.line((x1, y1, x1, y2), fill="black", width=6)
    points = [(x1, y2 - 40), (x1 + 120, y2 - 100), (x1 + 260, y2 - 220), (x1 + 410, y2 - 300), (x2, y1 + 50)]
    visible = max(2, int(len(points) * progress) + 1)
    draw.line(points[:visible], fill="black", width=10)


def draw_house(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    draw.rectangle((x, y, x + 240, y + 190), outline="black", width=8)
    draw.polygon([(x - 20, y), (x + 120, y - 140), (x + 260, y)], outline="black")
    draw.line((x - 20, y, x + 120, y - 140, x + 260, y), fill="black", width=8)
    draw.rectangle((x + 90, y + 90, x + 150, y + 190), outline="black", width=6)


def draw_car(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    draw.rectangle((x, y, x + 330, y + 90), outline="black", width=8)
    draw.polygon([(x + 70, y), (x + 125, y - 70), (x + 230, y - 70), (x + 280, y)], outline="black")
    draw.line((x + 70, y, x + 125, y - 70, x + 230, y - 70, x + 280, y), fill="black", width=8)
    draw.ellipse((x + 45, y + 65, x + 105, y + 125), outline="black", width=8)
    draw.ellipse((x + 235, y + 65, x + 295, y + 125), outline="black", width=8)


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _ffmpeg_path(path: Path) -> str:
    return str(path).replace("\\", "/").replace(":", "\\:")
