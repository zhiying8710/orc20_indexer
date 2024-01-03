import urllib.parse

import aiohttp
from loguru import logger
from environs import Env


env = Env()
env.read_env()
webhook_url = env.str("ALERT_WEBHOOK_URL")
bark_tokens = env.str("BARK_TOKENS")


async def send_alert(message):
    """
    Sends an alert message to the specified webhook URL.

    Args:
        message (str): The message to be sent as an alert.

    Returns:
        None
    """
    if not webhook_url or not bark_tokens:
        return
    for token in bark_tokens.split(','):
        token = token.strip()
        if not token:
            continue
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.day.app/{token}/orc20_indexer/{urllib.parse.quote(message, safe="", encoding="utf-8")}') as response:
                if 200 <= response.status < 300:
                    logger.info("Alert sent successfully")
                else:
                    logger.info("Failed to send alert")
