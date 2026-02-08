import logging

from bot.services.trends_client import get_trending_searches

logger = logging.getLogger(__name__)


class Trends:
    def __init__(self):
        pass

    async def trending(self):
        trends = get_trending_searches()
        return trends
