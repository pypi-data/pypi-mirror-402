# ruff: noqa: T100
import os

from IPython.core.async_helpers import get_asyncio_loop
from IPython.terminal.embed import InteractiveShellEmbed
from tortoise import Tortoise

from bakit import settings


def start_ipython_shell(extra_ns=None, banner=None):
    """
    Async shell helper:
    - starts IPython if available (with top-level await support)
    - falls back to stdlib interactive shell otherwise
    - always closes DB connections when done
    """

    if banner is None:
        banner = "Tortoise shell. If IPython is installed, top-level await should work."

    loop = get_asyncio_loop()

    ns = {
        "Tortoise": Tortoise,
        "os": os,
    }
    if extra_ns:
        ns.update(extra_ns)

    try:
        loop.run_until_complete(Tortoise.init(config=settings.TORTOISE_ORM))
        shell = InteractiveShellEmbed(banner2=banner)
        shell(local_ns=ns, global_ns=ns)
    finally:
        loop.run_until_complete(Tortoise.close_connections())
