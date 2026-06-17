import asyncio
import logging
from bot.services.api_client import APIClient

logger = logging.getLogger(__name__)

WEEK_SECONDS = 7 * 24 * 3600


async def schedule_generator_loop(api_client: APIClient) -> None:
    """Background task: extend lesson horizon to 8 weeks, runs at startup then weekly."""
    logger.info("Schedule generator started")
    while True:
        try:
            result = await api_client.generate_upcoming_lessons()
            logger.info("Generated %d lessons", result.get("generated", 0))
        except Exception as e:
            logger.error("Schedule generator error: %s", e)
        await asyncio.sleep(WEEK_SECONDS)
