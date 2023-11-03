import json
import discord
from discord.ext import commands, tasks
from discord import app_commands
from .functions.news import NewsFunctions
from .functions.warn_notice import get_new_warn_data
from .utils import log_events, chunk_message, news_choices


class NewsTask(commands.Cog):
    def __init__(self, bot: commands.Bot, api_key: str = "", start_hour: int = 1):
        self.bot = bot
        self.log_file = "data/news.log"
        self.news_api = NewsFunctions(api_key)

        # TODO: load this from data base
        self.active_tasks = {}


    @app_commands.command(name="news_notifications")
    @app_commands.describe(
        q="Search of news about a specific query, (Default everything)",
        source="News Source (Default: NPR, BBC, ABC News, NBC News)",
        category="Category of news articles (Default: All)",
        n="Number of news articles you want to see (Default 5, Max 6)",
        country="The country of the news article's intended audience (Default US, AU, GB)",
        hours="time between each notification",
        start_hour="hour of the day you want to start sending news notification"
    )
    @app_commands.choices(source=news_choices["sources"])
    @app_commands.choices(category=news_choices["categories"])
    @app_commands.choices(country=news_choices["countries"])
    async def start_news_notifications(
            self,
            interaction: discord.Interaction,
            q: str = "",
            n: int = 5,
            source: discord.app_commands.Choice[str] = "",
            category: discord.app_commands.Choice[str] = "",
            country: discord.app_commands.Choice[str] = "",
            hours: int = 12,
            start_hour: int = 9
    ):
        """
        sets a news notification task
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

        kwargs["channel"] = interaction.channel


        run_args = {
            "hours": hours,
            # "start": start_hour
        }

        new_task = tasks.loop(**run_args)(self.news_notification)  # You can also pass a static interval and/or count
        self.active_tasks[interaction.channel.id] = {
            "task": new_task,
            "news_params": kwargs,
            "run_params": run_args
        }
        new_task.start(**kwargs)
        await interaction.response.send_message(
            f"created news notification loop with arguments {kwargs}, and run args: {run_args}",
            ephemeral=True
        )
        print(self.active_tasks)


# async def warn_data():
#     """
#     sends new data from warn act from texas every 12 hours
#     """
#     log_events("Sent warns message", LOG_FILE)
#     warns = get_new_warn_data()
#     for channel in bot_channels:
#         await channel.send(warns)


    async def news_notification(self, channel, **kwargs):
        """
        Sends news notifications every 12 hours
        """
        log_events("news task sending news sending news", self.log_file)
        news_data = self.news_api.get_news(**kwargs)
        await channel.send(news_data)


