import json
import discord
from discord.ext import commands
from discord import app_commands
from .functions.news import NewsFunctions
from .functions.warn_notice import get_new_warn_data
from .utils import log_events, chunk_message


news_choices = {
    "sources": [
        discord.app_commands.Choice(name="Fox news", value="foxnews"),
        discord.app_commands.Choice(name="NPR", value="npr"),
        discord.app_commands.Choice(name="ABC News", value="abcnews"),
        discord.app_commands.Choice(name="Sky News", value="skynews"),
        discord.app_commands.Choice(name="Yahoo! News", value="yahoo"),
        discord.app_commands.Choice(name="The BBC", value="bbc"),
        discord.app_commands.Choice(name="NBC News", value="nbcnews"),
    ],
    "categories": [
        discord.app_commands.Choice(name="Business", value="business"),
        discord.app_commands.Choice(name="Politics", value="politics"),
        discord.app_commands.Choice(name="Science", value="science"),
        discord.app_commands.Choice(name="Technology", value="technology"),
        discord.app_commands.Choice(name="World", value="world"),
    ],
    "countries": [
        discord.app_commands.Choice(name="United States", value="us"),
        discord.app_commands.Choice(name="United Kingdom", value="gb"),
        discord.app_commands.Choice(name="Australia", value="au"),
        discord.app_commands.Choice(name="Germany", value="de"),
    ]
}


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
        news_data = self.news_api.get_news(**kwargs)
        print(f"len news data is: {len(news_data)}")
        if len(news_data) == 0:
            news_data = "No news articles found"
        await interaction.edit_original_response(content=news_data[:2000])
