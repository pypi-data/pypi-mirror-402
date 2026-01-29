import asyncio
import logging
from contextlib import contextmanager
from functools import wraps

import sentry_sdk

from bakit import settings
from bakit.utils.metrics import timer

log = logging.getLogger(__name__)


@contextmanager
def _handle_exceptions():
    """
    Decorator to handle ARQ job timeouts and report them to Sentry.

    When ARQ times out a job, it raises asyncio.CancelledError. This decorator
    catches that exception, reports it to Sentry with appropriate tags, and
    re-raises it to maintain the expected behavior.

    This is needed because ARQ's CancelledError also cancels sentry's coroutine that
    would send an error to sentry
    """
    try:
        yield
    except asyncio.CancelledError as e:
        sentry_sdk.capture_exception(e)
        raise
    except Exception:
        raise


def task(name=None):
    """
    Decorator for async task functions

    This decorator wraps async functions to automatically:
    - Track execution time using the timer context manager
    - Handle exceptions (including asyncio.CancelledError) via handle_exceptions
    - Handle enabling/disabling the task via redis

    The decorator is designed for use with background task systems like ARQ, where
    timing and proper exception handling are crucial for monitoring and reliability.

    Args:
        name (str, optional): Custom name for the task. If not provided, uses the
            function's __name__ attribute. This name is used for metrics labeling
            as "task.{name}".

    Returns:
        callable: The decorated async function with timing and exception handling.

    Usage:
        # Without parameters (uses function name)
        @task
        async def my_background_task():
            await some_async_operation()

        # With custom name
        @task(name="custom_task_name")
        async def my_background_task():
            await some_async_operation()
    """

    def decorator(func):
        task_name = name or func.__name__

        @wraps(func)
        async def wrapper(ctx, *args, **kwargs):
            redis = ctx.get("redis")
            if redis:
                task_disabled = await redis.sismember(
                    settings.ARQ_CRON_DISABLED_KEY, task_name
                )
                if task_disabled:
                    log.info(f"Task {task_name} is disabled. Skipping.")
                    return

            with timer(f"task.{task_name}"), _handle_exceptions():
                return await func(ctx, *args, **kwargs)

        return wrapper

    # support both @task and @task("name")
    if callable(name):
        func = name
        name = None
        return decorator(func)

    return decorator
