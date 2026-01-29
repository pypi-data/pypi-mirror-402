# ruff: noqa: E402
import asyncio
import contextlib
import logging

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from tortoise import Tortoise

from bakit import settings

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    max_breadcrumbs=20,
    integrations=[
        LoggingIntegration(level=logging.INFO, event_level=logging.WARNING),
    ],
)
# Import all bakit stuff after settings and after Sentry has been initialized to
# captcure any errors/warning in sentry if they happen during imports

from bakit.utils import metrics


async def _report_queue_size(ctx):
    redis = ctx["redis"]
    queue = redis.default_queue_name
    sanitized_queue_name = queue.replace(".", "_").replace(":", "_")
    metric_name = f"arq.queue.size.{sanitized_queue_name}"
    while True:
        n = await redis.zcard(queue)  # ARQ stores jobs in a ZSET per queue
        metrics.gauge(metric_name, n)
        await asyncio.sleep(10)


async def on_startup(ctx):
    await Tortoise.init(config=settings.TORTOISE_ORM)
    ctx["metrics_task"] = asyncio.create_task(_report_queue_size(ctx))


async def on_shutdown(ctx):
    await Tortoise.close_connections()

    metrics_task = ctx.get("metrics_task")
    if metrics_task:
        metrics_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await metrics_task


def build_worker(config):
    if not isinstance(config, dict):
        raise TypeError("Config must be a dictionary")

    cfg = {
        "on_startup": on_startup,
        "on_shutdown": on_shutdown,
        # Don't keep result of the job as we use unique job_id on cron jobs to avoid
        # scheduling the same job multiple times at the same time. If keep_result is
        # set, and the job fails, the new job will not be able to be rescheduled until
        # keep_result expires
        "keep_result": 0,
        "max_jobs": 6,
        "queue_read_limit": 12,  # keep at 2x max_jobs
        "job_timeout": 15 * 60,  # max time per job,
        "job_completion_wait": 8 * 60,  # wait 8 minutes for completion
        "graceful_shutdown_timeout": 9 * 60,  # total shutdown time
    }
    cfg.update(config)
    return type("ARQWorker", (), cfg)
