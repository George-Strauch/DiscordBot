from bot.config import setup_logging, DISCORD_TOKEN
from bot.client import BasedClient

setup_logging()
bot = BasedClient()
bot.run(DISCORD_TOKEN)
