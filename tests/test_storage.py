from yt_automation.storage import TopicCache, topic_fingerprint


def test_topic_fingerprint_is_stable():
    first = topic_fingerprint("Money Mistakes", "Credit card interest")
    second = topic_fingerprint(" money mistakes ", " credit card interest ")

    assert first == second


def test_topic_cache_tracks_seen_topics(tmp_path):
    cache = TopicCache(tmp_path / "topic_cache.json")
    fingerprint = topic_fingerprint("Compound Interest Stories", "$100 per month")

    assert not cache.seen(fingerprint)

    cache.add(fingerprint, {"pillar": "Compound Interest Stories"})

    assert cache.seen(fingerprint)
