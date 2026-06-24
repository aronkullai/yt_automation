import argparse
import json
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is declared, fallback keeps CLI diagnosable.
    load_dotenv = None

from .claude_client import ClaudeConfig, ClaudeScriptClient
from .prompts import build_user_prompt
from .storage import TopicCache, save_script_response, topic_fingerprint


DEFAULT_OUTPUT_DIR = Path("outputs/scripts")
DEFAULT_CACHE_PATH = Path("outputs/topic_cache.json")


def main() -> None:
    if load_dotenv:
        load_dotenv()

    parser = argparse.ArgumentParser(description="Generate stickman finance YouTube scripts with Claude.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="Generate one script pair.")
    _add_generation_args(generate_parser)

    batch_parser = subparsers.add_parser("batch", help="Generate script pairs from a JSON topic file.")
    batch_parser.add_argument("--topics", required=True, type=Path, help="Path to a JSON array of topic objects.")
    batch_parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path)
    batch_parser.add_argument("--cache-path", default=DEFAULT_CACHE_PATH, type=Path)
    batch_parser.add_argument("--allow-duplicates", action="store_true")

    args = parser.parse_args()

    if args.command == "generate" and args.dry_run:
        print(build_user_prompt(args.pillar, args.angle, args.trend_hook))
        return

    client = ClaudeScriptClient(ClaudeConfig.from_env())

    if args.command == "generate":
        path = _generate_one(client, args)
        print(path)
        return

    topics = json.loads(args.topics.read_text(encoding="utf-8"))
    if not isinstance(topics, list):
        raise SystemExit("--topics must point to a JSON array.")

    written = []
    for topic in topics:
        topic_args = argparse.Namespace(
            pillar=topic["pillar"],
            angle=topic["angle"],
            trend_hook=topic.get("trend_hook"),
            output_dir=args.output_dir,
            cache_path=args.cache_path,
            allow_duplicates=args.allow_duplicates,
        )
        written.append(str(_generate_one(client, topic_args)))

    print(json.dumps(written, indent=2))


def _add_generation_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--pillar", required=True)
    parser.add_argument("--angle", required=True)
    parser.add_argument("--trend-hook")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path)
    parser.add_argument("--cache-path", default=DEFAULT_CACHE_PATH, type=Path)
    parser.add_argument("--allow-duplicates", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Print the user prompt without calling Claude.")


def _generate_one(client: ClaudeScriptClient, args: argparse.Namespace) -> Path:
    fingerprint = topic_fingerprint(args.pillar, args.angle, args.trend_hook)
    cache = TopicCache(args.cache_path)
    if cache.seen(fingerprint) and not args.allow_duplicates:
        raise SystemExit(f"Topic already generated: {args.pillar} / {args.angle}")

    payload = client.generate_script_pair(args.pillar, args.angle, args.trend_hook)
    path = save_script_response(payload, args.output_dir)
    cache.add(
        fingerprint,
        {
            "pillar": args.pillar,
            "angle": args.angle,
            "trend_hook": args.trend_hook,
            "output_path": str(path),
        },
    )
    return path


if __name__ == "__main__":
    main()
