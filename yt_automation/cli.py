import argparse
import json

from .config import get_settings
from .database import Database
from .logging_config import configure_logging
from .orchestrator import DryRunOrchestrator, VideoOrchestrator
from .scheduler import run_scheduler


def main() -> None:
    parser = argparse.ArgumentParser(description="Fully automated faceless finance Shorts/TikTok generator.")
    parser.add_argument("--log-level", default="INFO")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Create or update database schema.")
    subparsers.add_parser("generate-one", help="Generate one complete video.")

    batch = subparsers.add_parser("generate-batch", help="Generate multiple complete videos.")
    batch.add_argument("--count", type=int, required=True)

    subparsers.add_parser("schedule", help="Run scheduled batch generation.")
    subparsers.add_parser("dry-run", help="Write a dependency-free smoke-test output file.")

    args = parser.parse_args()
    configure_logging(args.log_level)
    settings = get_settings()

    if args.command == "init-db":
        Database(settings.database_url).migrate()
        print(settings.database_url)
        return

    if args.command == "dry-run":
        path = DryRunOrchestrator(settings.output_dir).generate_one()
        print(path)
        return

    if args.command == "schedule":
        run_scheduler(settings)
        return

    orchestrator = VideoOrchestrator(settings)
    if args.command == "generate-one":
        video = orchestrator.generate_one()
        print(json.dumps(video.__dict__, indent=2))
        return

    if args.command == "generate-batch":
        videos = orchestrator.generate_batch(args.count)
        print(json.dumps([video.__dict__ for video in videos], indent=2))


if __name__ == "__main__":
    main()
