from yt_automation.database import Database, VideoRepository
from yt_automation.schemas import GeneratedContent, VideoIdea


def test_database_tracks_topics_and_content(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'test.db'}")
    db.migrate()
    repo = VideoRepository(db)
    idea = VideoIdea(topic="What if you invested at 18?", angle="age comparison", pillar="Compound Interest Stories")

    video_id = repo.create_requested_video(idea)

    assert repo.topic_exists(idea.topic)

    repo.attach_content(
        video_id,
        GeneratedContent(title="Age 18 Wins", script="Script", description="Description", hashtags=["#money"]),
    )
    assert repo.recent_topics() == [idea.topic]
