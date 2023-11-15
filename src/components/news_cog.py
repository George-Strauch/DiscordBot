import asyncio

import discord
from discord.ext import commands, tasks
from discord import app_commands, Interaction
from .utils import log_events, chunk_message, theme_colors
from .database import NewsNotificationDatabase
from .discord_bll.news_bll import NewsBll

news_categories = {
    'business', 'crime', 'domestic', 'education', 'entertainment', 'environment', 'food',
    'other', 'politics', 'science', 'sports', 'technology', 'top', 'tourism', 'world', 'health'
}
news_categories = {x: x for x in news_categories}


sources = {
    "Fox news": "foxnews",
    "NPR": "npr",
    "ABC News": "abcnews",
    "Sky News": "skynews",
    "Yahoo! News": "yahoo",
    "The BBC": "bbc",
    "NBC News": "nbcnews",
    "ANY": "x"
}
param_descriptions = {
    "topic": "Search of news about a specific query, (Default everything)",
    "source": "News Source (Default: NPR, BBC, ABC News, NBC News)",
    "category": "Category of news articles (Default: All)",
    "n": "Number of news articles you want to see (Default 5, Max 6)",
    "country": "The country of the news article's intended audience (Default US, AU, GB)"
}
countries = {
    "United States": "us",
    "United Kingdom": "gb",
    "Germany": "de",
    "Australia": "au",
    "ANY": "x"
}

news_choices = {
    "sources": [
        discord.app_commands.Choice(name=k, value=v)
        for k, v in sources.items()
    ],
    "categories": [
        discord.app_commands.Choice(name=k.capitalize(), value=v)
        for k, v in news_categories.items()
    ] + [
        discord.app_commands.Choice(
            name="Important",
            value="business,politics,science,technology,world"
        )
    ],
    "countries": [
        discord.app_commands.Choice(name=k, value=v)
        for k, v in countries.items()
    ]
}


class News(commands.Cog):
    def __init__(self, bot: commands.Bot, api_key: str, guilds=[]):
        self.bot = bot
        self.log_file = "/opt/bot/data/news.log"
        self.news_bll = NewsBll(api_key=api_key)
        self.db = NewsNotificationDatabase("/opt/bot/data/news_notification.db")
        print("loading tasks from db")
        for g in guilds:
            self.news_bll.load_from_db(g)
        print("done loading tasks from db")


    @commands.hybrid_command(name="news")
    @app_commands.describe(**param_descriptions)
    @app_commands.choices(source=news_choices["sources"])
    @app_commands.choices(category=news_choices["categories"])
    @app_commands.choices(country=news_choices["countries"])
    async def get_news(
            self,
            ctx: commands.Context,
            *,
            topic: str = "",
            n: int = 5,
            source: discord.app_commands.Choice[str] = "",
            category: discord.app_commands.Choice[str] = "",
            country: discord.app_commands.Choice[str] = ""
    ):
        """
        Shows most recent news
        """
        # await interaction.response.send_message("Working on that ...")

        source = source.value if not isinstance(source, str) else ""
        source = "" if source == "x" else source

        category = category.value if not isinstance(category, str) else ""
        category = "" if category == "x" else category

        country = country.value if not isinstance(country, str) else ""
        country = "" if country == "x" else country
        # todo still getting X in news notifications

        try:
            response = self.news_bll.get_news(
                topic=topic,
                n=n,
                source=source,
                category=category,
                country=country
            )
            await ctx.reply(**response)

        except Exception as e:
            await ctx.reply(content="Something went wrong getting news :[")
            log_events(str(e.args), self.log_file)


    @commands.hybrid_command(name="create_news_notification")
    @app_commands.describe(topic="Topic you want to send news notifications to this channel for" )
    @app_commands.describe(frequency="Hours between each notification event [12, 24 or 48] [Default 24]")
    @app_commands.describe(
        empty_update="Receive notification if no news articles are found matching your criteria each event"
    )
    async def start_news_notifications(
            self,
            ctx: commands.Context,
            *,
            topic: str = "",
            frequency: int = 24,
            empty_update: bool = False
    ):
        """
        opens a menu to set up news notifications about a provided topic
        todo delete view
        """
        view_message = None

        async def clear_view():
            try:
                await view_message.edit(view=None)
            except Exception as ex:
                log_events(str(ex.args), log_file=self.log_file)
                await ctx.reply(content="Something weird happened on the back end", ephemeral=True)
        try:
            response = self.news_bll.start_news_notification_with_view(
                ctx=ctx,
                clear_view=clear_view,
                channel=ctx.channel,
                topic=topic,
                frequency=frequency,
                empty_update=empty_update
            )
            view_message = await ctx.reply(
                **response
            )
        except Exception as e:
            await ctx.reply(
                content="Something went wrong trying to set up news notification :["
            )
            log_events(str(e.args), self.log_file)


    @commands.hybrid_command(name="notifications")
    async def get_news_notifications(self, interaction: discord.Interaction,):
        try:
            response = self.news_bll.get_news_notifications(
                guild_id=interaction.guild_id,
            )
            await interaction.response.send_message(
                **response
            )
        except Exception as e:
            await interaction.response.send_message(
                content="Something went wrong getting news notifications"
            )
            log_events(str(e.args), self.log_file)


    @commands.hybrid_command(name="stop_news_notification")
    @app_commands.describe(
        ids="id of news notification loop. Multiple may be provided seperated by space (Use /notifications to get list)"
    )
    async def stop_news_notifications(self, ctx: commands.Context, *, ids: str):
        """
        kills a news notification loop with a provided id(s)
        todo: set permission
        """
        problems = []
        success = []
        for x in ids.split(" "):
            if not x.isalnum():
                problems.append(f"Invalid id {x}")
            else:
                x = int(x)
                try:
                    response = self.news_bll.stop_news_notifications(
                        guild_id=ctx.guild.id,
                        _id=x
                    )
                    success.append(response["content"])
                except Exception as e:
                    problems.append(f"Issue occurred canceling notification loop with id: {x}")
                    log_events(str(e.args), self.log_file)
        success = "\n".join(success)
        problems = "\n".join(problems)
        msg = f"{success}\n{problems}"
        await ctx.reply(
            content=msg,
            ephemeral=True
        )


