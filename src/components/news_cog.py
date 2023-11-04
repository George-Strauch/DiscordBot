import json
import discord
from discord.ext import commands
from discord import app_commands
from .functions.news import NewsFunctions
from .functions.warn_notice import get_new_warn_data
from .utils import log_events, chunk_message, news_choices


class News(commands.Cog):
    def __init__(self, bot: commands.Bot, api_key: str = ""):
        self.bot = bot
        self.log_file = "data/news.log"
        self.news_api = NewsFunctions(api_key)


    @app_commands.command(name="warn")
    @app_commands.describe(pending="Show ones have not gone into effect yet")
    async def get_warn_data(self, interaction: discord.Interaction, pending: bool=True):
        """
        Pulls warn act data and displays it
        # todo pending
        """
        log_events(f"Sending warn data", self.log_file)
        await interaction.response.send_message("Working on that, one sec ...")
        log_events("Sent warns message", self.log_file)
        warns = get_new_warn_data()
        await interaction.edit_original_response(content=warns)


    @app_commands.command(name="news")
    @app_commands.describe(
        q="Search of news about a specific query, (Default everything)",
        source="News Source (Default: NPR, BBC, ABC News, NBC News)",
        category="Category of news articles (Default: All)",
        n="Number of news articles you want to see (Default 5, Max 6)",
        country="The country of the news article's intended audience (Default US, AU, GB)"
    )
    @app_commands.choices(source=news_choices["sources"])
    @app_commands.choices(category=news_choices["categories"])
    @app_commands.choices(country=news_choices["countries"])
    async def get_news(
            self,
            interaction: discord.Interaction,
            q: str = "",
            n: int = 5,
            source: discord.app_commands.Choice[str] = "",
            category: discord.app_commands.Choice[str] = "",
            country: discord.app_commands.Choice[str] = ""
    ):
        """
        Shows most recent news
        """
        kwargs = {}

        if q != "":
            kwargs["q"] = q
        if n != 0:
            kwargs["size"] = min(n, 5)
        if source != "":
            kwargs["domain"] = source.value
        if category != "":
            kwargs["category"] = category.value
        if country != "":
            kwargs["country"] = country.value

        log_events(f"Sending News:\n{json.dumps(kwargs, indent=4)}", self.log_file)
        await interaction.response.send_message("Working on that, one sec ...")
        news_articles = self.news_api.get_news(**kwargs)
        if len(news_articles) == 0:
            await interaction.edit_original_response(content="No news articles found with the provided query")
        else:
            embeds = [
                discord.Embed(
                    title=x["Title"],
                    url=x["Link"],
                    description=x["Source"],
                    color=0x97acc2
                    # color=0x2e4155
                )
                for x in news_articles
            ]
            await interaction.edit_original_response(embeds=embeds)
