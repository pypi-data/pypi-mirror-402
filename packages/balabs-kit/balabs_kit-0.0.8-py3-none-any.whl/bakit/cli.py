import importlib
import pkgutil
import time
from datetime import UTC, datetime
from pathlib import Path

import asyncclick as click
from discord import Color, Embed
from tortoise import Tortoise

from bakit import settings
from bakit.utils.discord import send_webhook_embed

__all__ = ["BakitCommand", "BakitGroup", "autodiscover_and_attach"]


async def _send_discord_embed(embed):
    embed.set_footer(text=f"{settings.APP_NAME} one-off tasks")
    await send_webhook_embed(settings.WATCHTOWER_WEBHOOK_URL, embed)


async def _run_one_off_with_notifications(ctx, invoke_fn):
    cmd = "{} {}".format(
        ctx.command_path,
        " ".join(f"--{k}={v}" for k, v in ctx.params.items()) if ctx.params else "",
    )
    click.echo(cmd)

    def _make_embed(text, color):
        description = f"{text} - `{cmd}`"
        return Embed(description=description, color=color, timestamp=datetime.now(UTC))

    await _send_discord_embed(_make_embed("🟣 Task starting", Color.purple()))
    started = time.monotonic()
    try:
        result = await invoke_fn(ctx)
    except Exception as e:
        await _send_discord_embed(_make_embed(f"🔴 Task failed: {e}", Color.red()))
        raise
    else:
        elapsed = time.monotonic() - started
        await _send_discord_embed(
            _make_embed(f"🟢 Task done in {elapsed:.1f}s", Color.green())
        )
    return result


class BakitCommand(click.Command):
    async def invoke(self, ctx):
        await Tortoise.init(config=settings.TORTOISE_ORM)

        try:
            if settings.IS_ONE_OFF_CMD:
                return await _run_one_off_with_notifications(ctx, super().invoke)

            else:
                return await super().invoke(ctx)
        finally:
            await Tortoise.close_connections()


class BakitGroup(click.Group):
    command_class = BakitCommand


def _wrap_tree(cmd):
    # If it's already wrapped, return as-is
    if isinstance(cmd, (BakitCommand, BakitGroup)):
        return cmd

    # Wrap groups by rebuilding them as BakitGroup
    if isinstance(cmd, click.Group):
        new_grp = BakitGroup(
            name=cmd.name,
            commands={},
            callback=cmd.callback,
            params=list(cmd.params),
            help=cmd.help,
            epilog=cmd.epilog,
            short_help=cmd.short_help,
            options_metavar=cmd.options_metavar,
            add_help_option=cmd.add_help_option,
            no_args_is_help=cmd.no_args_is_help,
            hidden=getattr(cmd, "hidden", False),
            deprecated=getattr(cmd, "deprecated", False),
            invoke_without_command=getattr(cmd, "invoke_without_command", False),
            context_settings=getattr(cmd, "context_settings", None),
        )

        for name, sub in cmd.commands.items():
            new_grp.add_command(_wrap_tree(sub), name=name)

        return new_grp

    # Wrap leaf commands by rebuilding them as BakitCommand (preserves args/options)
    if isinstance(cmd, click.Command):
        return BakitCommand(
            name=cmd.name,
            callback=cmd.callback,
            params=list(cmd.params),
            help=cmd.help,
            epilog=cmd.epilog,
            short_help=cmd.short_help,
            options_metavar=cmd.options_metavar,
            add_help_option=cmd.add_help_option,
            no_args_is_help=cmd.no_args_is_help,
            hidden=getattr(cmd, "hidden", False),
            deprecated=getattr(cmd, "deprecated", False),
            context_settings=getattr(cmd, "context_settings", None),
        )

    return cmd


def _make_wrapper_command(mod, cmd_name):
    cmd = getattr(mod, "cmd", None)

    if not cmd:
        return

    if not isinstance(cmd, click.core.BaseCommand):
        raise TypeError(
            f"Invalid `cmd` in module '{mod.__name__}': expected a Click command/group "
            f"instance, got {type(cmd).__name__}.\n"
            "Fix: define `cmd` using @click.command() or @click.group()."
        )

    # Ensure the command has a stable name when mounted under the scripts group
    if not getattr(cmd, "name", None):
        cmd.name = cmd_name

    return _wrap_tree(cmd)


def _load_scripts_group(pkg_name):
    # Create the group from package name`myproject package`
    grp = click.Group(name=pkg_name)

    scripts_pkg = f"{pkg_name}.scripts"
    try:
        scripts_mod = importlib.import_module(scripts_pkg)
    except ModuleNotFoundError:
        # package exists but no scripts package
        return None

    # Discover script modules under <package>/scripts/*.py
    for m in pkgutil.iter_modules(scripts_mod.__path__):
        if m.ispkg or m.name.startswith("_"):
            continue

        full_name = f"{scripts_pkg}.{m.name}"
        mod = importlib.import_module(full_name)
        cmd = _make_wrapper_command(mod, cmd_name=m.name)
        if cmd:
            grp.add_command(cmd, name=m.name)

    return grp


def _iter_immediate_packages(root_dir):
    # Find immediate subfolders of the package containing cli.py
    for p in root_dir.iterdir():
        if not p.is_dir():
            continue
        if p.name.startswith(("_", ".")):
            continue
        if (p / "__init__.py").exists() and (p / "scripts/").exists():
            yield p.name


def autodiscover_and_attach(base_file, cli):
    root_dir = Path(base_file).resolve().parent

    for pkg_name in _iter_immediate_packages(root_dir):
        grp = _load_scripts_group(pkg_name)
        if grp:
            cli.add_command(grp, name=pkg_name)
