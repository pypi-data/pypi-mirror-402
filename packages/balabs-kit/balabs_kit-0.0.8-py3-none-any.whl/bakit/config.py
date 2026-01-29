import re
from copy import deepcopy
from types import SimpleNamespace

_APP_NAME_RE = re.compile(r"^[A-Za-z]+$")


class Settings:
    """
    Settings proxy so it doesn't matter where and how settings are imported
    they still point to the correct settings after they're initialized
    """

    _wrapped = None

    def init(self, real_settings):
        self._wrapped = real_settings

    def __getattr__(self, name):
        if self._wrapped is None:
            raise RuntimeError("Settings not initialized")
        return getattr(self._wrapped, name)


settings = Settings()


def load_settings(env, configure_settings):
    base = _default_settings(env)
    base_copy = deepcopy(base)

    if configure_settings is not None:
        final_dict = configure_settings(base_copy, env)
        if final_dict is None:
            raise RuntimeError("configure_settings must return a dict of settings")
    else:
        final_dict = base_copy

    settings.init(SimpleNamespace(**final_dict))
    return settings


def _default_settings(env):
    app_name = env("APP_NAME")
    if not _APP_NAME_RE.fullmatch(app_name):
        raise RuntimeError(
            "Invalid APP_NAME. Must contain only letters A-Z or a-z, "
            "no spaces, numbers, or symbols."
        )

    default_log_level = env("DEFAULT_LOG_LEVEL", default="WARNING")
    app_log_level = env("APP_LOG_LEVEL", default="INFO")
    tortoise_log_level = env("TORTOISE_LOG_LEVEL", default="WARNING")
    arq_log_level = env("ARQ_LOG_LEVEL", default="INFO")
    generic_log_level = env("GENERIC_LOG_LEVEL", default="WARNING")

    return {
        "APP_NAME": app_name,
        "CORS_ORIGINS": [
            re.compile(r"^http://(localhost|127\.0\.0\.1):\d+$"),
            re.compile(r"^https://(\S+\.)?vercel\.app$"),
            re.compile(r"^https://(\S+\.)?blockanalitica\.com$"),
        ],
        "CORS_METHODS": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "SENTRY_DSN": env("SENTRY_DSN", ""),
        "STATSD_HOST": env("STATSD_HOST", ""),
        "STATSD_PORT": env("STATSD_PORT", default=8125),
        "STATSD_PREFIX": env("STATSD_PREFIX", default=app_name.lower()),
        "REDIS_HOST": env("REDIS_HOST", ""),
        "REDIS_PORT": env.int("REDIS_PORT", 6379),
        "REDIS_DB": env.int("REDIS_DB", 2),
        "CACHE_MIDDLEWARE_SECONDS": 5,
        "CACHE_MIDDLEWARE_ENABLED": env.bool("CACHE_MIDDLEWARE_ENABLED", False),
        "ARQ_CRON_DISABLED_KEY": f"{app_name.lower()}:arq:cron:disabled",
        "DEFAULT_LOG_LEVEL": env("DEFAULT_LOG_LEVEL", default="WARNING"),
        "APP_LOG_LEVEL": env("APP_LOG_LEVEL", default="INFO"),
        "TORTOISE_LOG_LEVEL": env("TORTOISE_LOG_LEVEL", default="WARNING"),
        "ARQ_LOG_LEVEL": env("ARQ_LOG_LEVEL", default="INFO"),
        "GENERIC_LOG_LEVEL": env("GENERIC_LOG_LEVEL", default="WARNING"),
        "LOGGING_CONFIG": {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": (
                        "[%(asctime)s] %(name)s {%(module)s:%(lineno)d} "
                        "PID=%(process)d [%(levelname)s] - %(message)s"
                    ),
                },
            },
            "handlers": {
                "console": {
                    "level": "DEBUG",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "default",
                },
            },
            "root": {
                "level": default_log_level,
                "handlers": ["console"],
            },
            "loggers": {
                "bakit": {
                    "propagate": True,
                    "level": app_log_level,
                },
                "core": {
                    "propagate": True,
                    "level": app_log_level,
                },
                "tortoise": {
                    "propagate": True,
                    "level": tortoise_log_level,
                },
                "arq": {
                    "propagate": True,
                    "level": arq_log_level,
                },
                "asyncio": {
                    "propagate": True,
                    "level": generic_log_level,
                },
            },
        },
    }
