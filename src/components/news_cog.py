import datetime
import json
import discord
from discord.ext import commands, tasks
from discord import app_commands
from .functions.news import NewsFunctions
from .functions.warn_notice import get_new_warn_data
from .utils import log_events, chunk_message, theme_colors
from .database import NewsNotificationDatabase


news_categories = {'business', 'crime', 'domestic', 'education', 'entertainment', 'environment', 'food', 'health',
                   'other', 'politics', 'science', 'sports', 'technology', 'top', 'tourism', 'world'}
news_choices = {
    "sources": [
        discord.app_commands.Choice(name="Fox news", value="foxnews"),
        discord.app_commands.Choice(name="NPR", value="npr"),
        discord.app_commands.Choice(name="ABC News", value="abcnews"),
        discord.app_commands.Choice(name="Sky News", value="skynews"),
        discord.app_commands.Choice(name="Yahoo! News", value="yahoo"),
        discord.app_commands.Choice(name="The BBC", value="bbc"),
        discord.app_commands.Choice(name="NBC News", value="nbcnews"),
        discord.app_commands.Choice(name="ANY", value=""),
    ],
    "categories": [
        discord.app_commands.Choice(name=x.capitalize(), value=x)
        for x in news_categories
    ] + [
        discord.app_commands.Choice(name="Important", value="business,politics,science,technology,world"),
        discord.app_commands.Choice(name="ANY", value=""),
    ],
    "countries": [
        discord.app_commands.Choice(name="United States", value="us"),
        discord.app_commands.Choice(name="United Kingdom", value="gb"),
        discord.app_commands.Choice(name="Australia", value="au"),
        discord.app_commands.Choice(name="Germany", value="de"),
        discord.app_commands.Choice(name="ANY", value=""),
    ]
}
param_descriptions = {
    "q": "Search of news about a specific query, (Default everything)",
    "source": "News Source (Default: NPR, BBC, ABC News, NBC News)",
    "category": "Category of news articles (Default: All)",
    "n": "Number of news articles you want to see (Default 5, Max 6)",
    "country": "The country of the news article's intended audience (Default US, AU, GB)"
}


class News(commands.Cog):
    def __init__(self, bot: commands.Bot, api_key: str = "", guilds=[]):
        self.bot = bot
        self.log_file = "data/news.log"
        self.news_api = NewsFunctions(api_key)
        self.active_tasks = {}
        self.db = NewsNotificationDatabase("data/news_notification2.db")
        print("loading tasks from db")
        for g in guilds:
            self.load_from_db(g)
        print("done loading tasks from db")
        print("----------------")
        print(self.active_tasks)
        print("----------------")



    # @app_commands.command(name="warn")
    # @app_commands.describe(pending="Show ones have not gone into effect yet")
    # async def get_warn_data(self, interaction: discord.Interaction, pending: bool=True):
    #     """
    #     Pulls warn act data and displays it
    #     # todo pending
    #     """
    #     log_events(f"Sending warn data", self.log_file)
    #     await interaction.response.send_message("Working on that, one sec ...")
    #     log_events("Sent warns message", self.log_file)
    #     warns = get_new_warn_data()
    #     await interaction.edit_original_response(content=warns)


    @app_commands.command(name="news")
    @app_commands.describe(**param_descriptions)
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
                    color=0x97acc2,
                    type="article"
                    # color=0x2e4155
                )
                for x in news_articles
            ]
            await interaction.edit_original_response(embeds=embeds)

    @app_commands.command(name="set_news_notification")
    @app_commands.describe(
        **param_descriptions,
        hours="time between each notification",
        no_news_update="Still Send an update if there were no news articles found "
                       "with the provided query each time interval"
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
            no_news_update: bool = False
            # start_hour: int = 9
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
        kwargs["no_news_update"] = no_news_update
        run_args = {
            "hours": hours,
        }

        new_task = tasks.loop(**run_args)(self.news_notification)
        if interaction.guild.id not in self.active_tasks:
            self.active_tasks[interaction.guild.id] = {}
        existing_ids = list(self.active_tasks[interaction.guild.id].keys()) + [0]
        new_id = max(existing_ids)+1

        self.active_tasks[interaction.guild.id][new_id] = {
            "task": new_task,
            "news_params": kwargs,
            "run_params": run_args,
            "started": str(datetime.datetime.now()).split('.')[0].replace(' ', ': ')[:-3]
            # "no_news_update": no_news_update
        }
        new_task.start(task=new_task, **kwargs)
        self.db.write_news_notification_to_db(
            guild_id=interaction.guild_id,
            notification_id=new_id,
            data_dict=self.active_tasks[interaction.guild.id][new_id]
        )
        # print(self.active_tasks)
        embed = self.create_news_notification_loop_embed(
            guild_id=interaction.guild.id, _id=new_id, color=theme_colors[0]
        )
        await interaction.response.send_message(
            f"Created new news notification loop",
            embed=embed,
            ephemeral=True
        )

    @app_commands.command(name="get_news_notifications")
    async def get_news_notifications(self, interaction: discord.Interaction,):
        str_adjust = 18
        if interaction.guild.id not in self.active_tasks:
            await interaction.response.send_message(
                content="No news notifications have been set up for this guild",
                ephemeral=True
            )
        else:
            embeds = [
                self.create_news_notification_loop_embed(guild_id=interaction.guild.id, _id=x, color=theme_colors[0])
                for x in self.active_tasks[interaction.guild.id]
            ]
            await interaction.response.send_message(embeds=embeds, ephemeral=True)


    @app_commands.command(name="stop_news_notification")
    @app_commands.describe(id="id of news notification loop (Use /get_news_notifications to get list)")
    async def stop_news_notifications(self, interaction: discord.Interaction, id: int):
        """
        kills a news notification loop with a provided id
        """
        if id not in self.active_tasks[interaction.guild.id]:
            await interaction.response.send_message(
                content=f"No news notification loop found with id {id}. "
                        f"Use /get_news_notifications to get list of currently running news notification loops",
                ephemeral=True
            )
        else:
            self.active_tasks[interaction.guild.id][id]["task"].stop()
            del self.active_tasks[interaction.guild.id][id]
            self.db.delete_news_notification_from_db(
                guild_id=interaction.guild_id,
                notification_id=id
            )

            await interaction.response.send_message(
                content=f"Successfully stopped news notification loop {id}",
                ephemeral=True
            )


    async def news_notification(self, channel, no_news_update, quiet_start=False, task=None, **kwargs):
        """
        Sends news notifications in a provided time interval
        """
        if quiet_start and task:
            if task.current_loop == 0:
                # now = dt.now()
                # start = dt(
                #     year=now.year,
                #     month=now.month,
                #     day=now.day,
                #     hour=hr_start,
                #     minute=0,
                #     second=0
                # )
                # while now > start:
                #     start = start + tdelta(hours=delta_hours)
                #
                # seconds = start - now
                # seconds = seconds.seconds
                # print(f"waiting {seconds} seconds to start tasks at {start}")
                # # log_events(f"waiting {seconds} seconds to start tasks at {start}", LOG_FILE)
                # await asyncio.sleep(seconds)
                return
        log_events("news task sending news sending news", self.log_file)
        news_articles = self.news_api.get_news(**kwargs)
        if len(news_articles) == 0:
            if no_news_update:
                await channel.send(content="No news articles found with the provided query")
        else:
            embeds = [
                discord.Embed(
                    title=x["Title"],
                    url=x["Link"],
                    description=x["Source"],
                    color=int(theme_colors[0].replace("#", ""), base=16)
                    # color=0x2e4155
                )
                for x in news_articles
            ]
            await channel.send(embeds=embeds)


    def create_news_notification_loop_embed(self, guild_id, _id, color):
        if _id not in self.active_tasks[guild_id]:
            return None
        x = self.active_tasks[guild_id][_id]
        str_adjust = 18
        desc = [
            f"{str(k).ljust(str_adjust, ' ')}{str(v if v != '' else 'ANY').ljust(str_adjust, ' ')}"
            for k, v in x["news_params"].items() if k != 'channel'
        ]
        desc = desc + [
            f"{str(k).ljust(str_adjust, ' ')}{str(v).ljust(str_adjust, ' ')}"
            for k, v in x["run_params"].items()
        ]
        desc = desc + [f"{'started'.ljust(str_adjust, ' ')}{x['started'].ljust(str_adjust, ' ')}"]
        desc = desc + [f"{'channel'.ljust(str_adjust, ' ')}{x['news_params']['channel'].name.ljust(str_adjust, ' ')}"]

        desc = "\n".join(desc)
        desc = f"``{desc}``"
        return discord.Embed(
            title=f"id:\t{_id}",
            description=desc,
            color=int(color.replace("#", ""), base=16)
        )


    def load_from_db(self, guild):
        tasks_for_guild = self.db.read_news_notification_to_db(guild.id)
        if tasks_for_guild == {}:
            return
        for k, v in tasks_for_guild.items():
            channel = guild.get_channel(v["news_params"]["channel"])
            if not channel:
                print("cannot find channel")
                return
            tasks_for_guild[k]["news_params"]["channel"] = channel
            new_task = tasks.loop(**v["run_params"])(self.news_notification)
            new_task.start(task=new_task, quiet_start=True, **v["news_params"])
            tasks_for_guild[k]["task"] = new_task
        self.active_tasks[guild.id] = tasks_for_guild

