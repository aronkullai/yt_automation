from yt_automation.content import build_animation_instructions, parse_scenes


def test_parse_timestamped_script_into_scenes():
    scenes = parse_scenes("(0-3s) Hook with $100.\n(3-8s) It grows into $500.")

    assert len(scenes) == 2
    assert scenes[0].duration_seconds == 3
    assert "$100" in scenes[0].metadata["numbers"]


def test_animation_instructions_are_generated_from_scene_metadata():
    scene = parse_scenes("Invest $100 and watch compound growth over time.")[0]
    animated = build_animation_instructions(scene)

    assert animated.animation["characters"][0]["type"] == "stickman"
    assert any(item["type"] == "line_chart" for item in animated.animation["objects"])
