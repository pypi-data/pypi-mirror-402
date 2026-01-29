import logging.config
import os
from decimal import getcontext
from pathlib import Path

from environs import Env

from bakit.config import load_settings


def init_bakit(configure_settings=None, env_overrides=None):
    """
    Initialize the bakit runtime for the current process.

    This function is the single required entrypoint for all projects using bakit.
    It must be called exactly once, and as early as possible, from each
    executable entrypoint (e.g. server, worker, CLI).
    """

    env = Env()
    # Need to pass in a path, otherwise it doesn't detect the correct path
    env.read_env(Path(os.getcwd()) / ".env")

    # Enable overriding env variables after they've been read from .env file
    if env_overrides and isinstance(env_overrides, dict):
        for key, value in env_overrides.items():
            os.environ[key] = value

    # Increase global Decimal precision to avoid InvalidOperation errors during
    # quantize(). The default context precision (28 digits) is too low for our values
    # which can exceed 28 significant digits (e.g., 14 integer + 18 fractional).
    getcontext().prec = 60

    # Load settings from env
    settings = load_settings(env, configure_settings)

    # Set up logging config
    logging.config.dictConfig(settings.LOGGING_CONFIG)
