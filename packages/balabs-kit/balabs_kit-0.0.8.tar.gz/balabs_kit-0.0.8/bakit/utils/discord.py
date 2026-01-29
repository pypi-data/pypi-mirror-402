import datetime

import aiohttp
from discord import Webhook
from discord.embeds import Embed


async def send_webhook_embed(webhook_url, embed):
    """
    Send an embed to a Discord webhook (async).

    Args:
        webhook_url (str): The Discord webhook URL.
        embed (discord.Embed): Title of the embed.
    """

    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(webhook_url, session=session)
        await webhook.send(embed=embed)


def make_embed(description, color):
    return Embed(
        description=description,
        color=color,
        timestamp=datetime.datetime.now(datetime.UTC),
    )
