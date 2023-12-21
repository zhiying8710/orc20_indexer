import aiohttp
from loguru import logger
from environs import Env


env = Env()
env.read_env()
webhook_url = env.str("ALERT_WEBHOOK_URL")


async def send_alert(message):
    """
    Sends an alert message to the specified webhook URL.

    Args:
        message (str): The message to be sent as an alert.

    Returns:
        None
    """
    payload = {"content": message}
    async with aiohttp.ClientSession() as session:
        async with session.post(webhook_url, json=payload) as response:
            if 200 <= response.status < 300:
                logger.info("Alert sent successfully")
            else:
                logger.info("Failed to send alert")
