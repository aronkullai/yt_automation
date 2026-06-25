import json
import sqlite3
from pathlib import Path
from typing import Any

from .schemas import GeneratedContent, Scene, VideoIdea, VideoStatus
from .utils import stable_hash, utc_now


SCHEMA = """
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    topic TEXT NOT NULL,
    topic_hash TEXT NOT NULL,
    pillar TEXT NOT NULL,
    angle TEXT NOT NULL,
    script TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    hashtags_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL,
    duration_seconds REAL NOT NULL DEFAULT 0,
    final_video_path TEXT NOT NULL DEFAULT '',
    thumbnail_path TEXT NOT NULL DEFAULT '',
    subtitle_path TEXT NOT NULL DEFAULT '',
    scheduled_for TEXT,
    published_at TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_videos_topic_hash ON videos(topic_hash);

CREATE TABLE IF NOT EXISTS scenes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    scene_index INTEGER NOT NULL,
    narration TEXT NOT NULL,
    visual_description TEXT NOT NULL,
    scene_type TEXT NOT NULL,
    animation_json TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    duration_seconds REAL NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(video_id) REFERENCES videos(id)
);

CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    path TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY(video_id) REFERENCES videos(id)
);

CREATE TABLE IF NOT EXISTS generation_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    logs_json TEXT NOT NULL DEFAULT '[]',
    FOREIGN KEY(video_id) REFERENCES videos(id)
);
"""


def sqlite_path_from_url(database_url: str) -> Path:
    if database_url.startswith("sqlite:///"):
        return Path(database_url.removeprefix("sqlite:///"))
    raise ValueError("Only sqlite:/// DATABASE_URL values are supported in the MVP repository.")


class Database:
    def __init__(self, database_url: str) -> None:
        self.path = sqlite_path_from_url(database_url)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def migrate(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)


class VideoRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def topic_exists(self, topic: str) -> bool:
        topic_hash = stable_hash(topic)
        with self.database.connect() as connection:
            row = connection.execute("SELECT id FROM videos WHERE topic_hash = ?", (topic_hash,)).fetchone()
        return row is not None

    def create_requested_video(self, idea: VideoIdea) -> int:
        now = utc_now()
        topic_hash = stable_hash(idea.topic)
        with self.database.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO videos (
                    title, topic, topic_hash, pillar, angle, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (idea.topic, idea.topic, topic_hash, idea.pillar, idea.angle, VideoStatus.REQUESTED.value, now, now),
            )
            return int(cursor.lastrowid)

    def attach_content(self, video_id: int, content: GeneratedContent) -> None:
        now = utc_now()
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE videos
                SET title = ?, script = ?, description = ?, hashtags_json = ?, status = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    content.title,
                    content.script,
                    content.description,
                    json.dumps(content.hashtags, ensure_ascii=False),
                    VideoStatus.SCRIPTED.value,
                    now,
                    video_id,
                ),
            )

    def replace_scenes(self, video_id: int, scenes: list[Scene]) -> None:
        with self.database.connect() as connection:
            connection.execute("DELETE FROM scenes WHERE video_id = ?", (video_id,))
            connection.executemany(
                """
                INSERT INTO scenes (
                    video_id, scene_index, narration, visual_description, scene_type,
                    animation_json, metadata_json, duration_seconds, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        video_id,
                        scene.index,
                        scene.narration,
                        scene.visual_description,
                        scene.scene_type,
                        json.dumps(scene.animation, ensure_ascii=False),
                        json.dumps(scene.metadata, ensure_ascii=False),
                        scene.duration_seconds,
                        utc_now(),
                    )
                    for scene in scenes
                ],
            )

    def add_asset(self, video_id: int, asset_type: str, path: str, metadata: dict[str, Any] | None = None) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO assets (video_id, type, path, metadata_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (video_id, asset_type, path, json.dumps(metadata or {}, ensure_ascii=False), utc_now()),
            )

    def complete_video(
        self,
        video_id: int,
        final_video_path: str,
        thumbnail_path: str,
        subtitle_path: str,
        duration_seconds: float,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE videos
                SET status = ?, final_video_path = ?, thumbnail_path = ?, subtitle_path = ?,
                    duration_seconds = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    VideoStatus.COMPLETED.value,
                    final_video_path,
                    thumbnail_path,
                    subtitle_path,
                    duration_seconds,
                    utc_now(),
                    video_id,
                ),
            )

    def fail_video(self, video_id: int, error_message: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "UPDATE videos SET status = ?, error_message = ?, updated_at = ? WHERE id = ?",
                (VideoStatus.FAILED.value, error_message, utc_now(), video_id),
            )

    def recent_topics(self, limit: int = 50) -> list[str]:
        with self.database.connect() as connection:
            rows = connection.execute("SELECT topic FROM videos ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [str(row["topic"]) for row in rows]
