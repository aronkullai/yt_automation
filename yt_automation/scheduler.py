import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from .config import Settings
from .orchestrator import VideoOrchestrator


logger = logging.getLogger(__name__)


def run_scheduler(settings: Settings) -> None:
    scheduler = BlockingScheduler()
    times = [item.strip() for item in settings.generation_times.split(",") if item.strip()]
    orchestrator = VideoOrchestrator(settings)

    def job() -> None:
        logger.info("Scheduled generation started: count=%s", settings.videos_per_day)
        orchestrator.generate_batch(settings.videos_per_day)

    for time_value in times:
        hour, minute = [int(part) for part in time_value.split(":", 1)]
        scheduler.add_job(job, "cron", hour=hour, minute=minute)
        logger.info("Scheduled batch generation at %02d:%02d", hour, minute)

    scheduler.start()
