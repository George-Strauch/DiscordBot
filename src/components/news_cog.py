import datetime
import json
import asyncio
from typing import Any

import discord
from discord._types import ClientT
from discord.ext import commands, tasks
from discord import app_commands, Interaction
from discord.ui import Select, View, Button
from .functions.news import NewsFunctions
from .functions.warn_notice import get_new_warn_data
from .utils import log_events, chunk_message, theme_colors
from .database import NewsNotificationDatabase
from datetime import datetime as dt
from datetime import timedelta as tdelta


news_categories = {
    'business', 'crime', 'domestic', 'education', 'entertainment', 'environment', 'food',
    'other', 'politics', 'science', 'sports', 'technology', 'top', 'tourism', 'world', 'health'
}
news_categories = {x: x for x in news_categories}
# news_categories = {x: x for x in news_categories}.update({"ANY": ""})


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



class AbstractSelect(Select):
    def __init__(self, data_passer, **kwargs):
        self.data_passer = data_passer
        self.default_values = self.default_values if hasattr(self, "default_values") else []
        self.select_options = self.select_options if hasattr(self, "select_options") else []
        self.param = self.param if hasattr(self, "param") else "_"
        params = {
            "options": self.select_options,
            "max_values": kwargs.get("max_values", len(self.select_options)),
            "min_values": kwargs.get("min_values", 1),
            "placeholder": kwargs.get("placeholder", self.param),
        }
        params.update(kwargs)
        super().__init__(**kwargs)
        self.set_data()

    async def callback(self, interaction: Interaction[ClientT]) -> Any:
        self.set_data()
        await interaction.response.defer()

    def set_data(self):
        if hasattr(self, "default_values") and len(self.default_values) > 0:
            self.data_passer({self.param: ",".join(self.default_values)})
            self.default_values = []
        else:
            self.data_passer({self.param: ",".join(self.values)})


class CreatePeriodicNewsNotification(View):
    class CategorySelect(AbstractSelect):
        def __init__(self, data_passer):
            # self.default_values = "business,politics,science,technology,world".split(',')
            self.default_values = []
            self.select_options = [
                discord.SelectOption(label=k.capitalize(), value=v, default=v in self.default_values)
                for k, v in news_categories.items()
            ]
            self.param = "category"
            super().__init__(
                options=self.select_options,
                max_values=len(self.select_options),
                min_values=1,
                placeholder="Categories",
                data_passer=data_passer
            )

    class SourceSelect(AbstractSelect):
        def __init__(self, data_passer):
            # self.default_values = ["npr"]
            self.default_values = []

            self.select_options = [
                discord.SelectOption(label=k, value=v, default=v in self.default_values)
                for k, v in sources.items()
            ]
            self.param = "source"
            super().__init__(
                options=self.select_options,
                max_values=len(self.select_options),
                min_values=1,
                placeholder="News Source",
                data_passer=data_passer
            )

    class CountrySelect(AbstractSelect):
        def __init__(self, data_passer):
            self.default_values = []
            self.select_options = [
                discord.SelectOption(label=k, value=v, default=v in self.default_values)
                for k, v in countries.items()
            ]
            self.param = "country"
            super().__init__(
                options=self.select_options,
                max_values=len(self.select_options),
                min_values=1,
                placeholder="Country",
                data_passer=data_passer
            )


    class StartNotificationButton(Button):
        def __init__(self, start_func):
            super().__init__(label="Start News Notifications", style=discord.ButtonStyle.primary, row=4)
            self.start_func = start_func

        async def callback(self, interaction: Interaction[ClientT]) -> Any:
            await self.start_func()
            await interaction.response.defer()

    class CancelButton(Button):
        def __init__(self, cancel):
            super().__init__(label="Cancel", style=discord.ButtonStyle.danger, row=4)
            self.cancel = cancel

        async def callback(self, interaction: Interaction[ClientT]) -> Any:
            await self.cancel()
            await interaction.response.defer()


    def __init__(self, original_interaction, original_params, notification_creator):
        super().__init__()
        self.news_parameters = {}
        self.run_parameters = {}
        self.params = original_params
        self.add_item(self.CategorySelect(self.data_passer))
        self.add_item(self.SourceSelect(self.data_passer))
        self.add_item(self.CountrySelect(self.data_passer))
        self.add_item(self.CancelButton(self.cancel))
        self.add_item(self.StartNotificationButton(self.start))

        self.original_interaction = original_interaction
        self.notification_creator = notification_creator

    def data_passer(self, received_data: dict):
        run_params = ["frequency", "no_news_update"]
        if any([k in run_params for k in received_data.keys()]):
            self.params["run_args"].update(received_data)
        else:
            self.params["news_args"].update(received_data)

    async def start(self):
        # print(json.dumps(self.params, indent=4))
        await self.notification_creator(self.original_interaction, self.params)

    async def cancel(self):
        await self.original_interaction.edit_original_response(
            content="Canceled news notification setup",
            view=None
        )


class News(commands.Cog):
    def __init__(self, bot: commands.Bot, api_key: str = "", guilds=[]):
        self.bot = bot
        self.log_file = "data/news.log"
        self.news_api = NewsFunctions(api_key)
        self.active_tasks = {}
        self.db = NewsNotificationDatabase("data/news_notification.db")
        print("loading tasks from db")
        for g in guilds:
            self.load_from_db(g)
        print("done loading tasks from db")


    @app_commands.command(name="news")
    @app_commands.describe(**param_descriptions)
    @app_commands.choices(source=news_choices["sources"])
    @app_commands.choices(category=news_choices["categories"])
    @app_commands.choices(country=news_choices["countries"])
    async def get_news(
            self,
            interaction: discord.Interaction,
            topic: str = "",
            n: int = 5,
            source: discord.app_commands.Choice[str] = "",
            category: discord.app_commands.Choice[str] = "",
            country: discord.app_commands.Choice[str] = ""
    ):
        """
        Shows most recent news
        """
        kwargs = {}

        if topic != "":
            kwargs["q"] = topic
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
        news_response = self.news_api.get_news(**kwargs)
        if len(news_response) == 0:
            await interaction.edit_original_response(content="No news articles found with the provided query")
        else:
            if isinstance(news_response, str):
                await interaction.edit_original_response(content="An error occurred getting news articles, sorry")
            else:
                embeds = [
                    self.create_article_embed(article=x, color=theme_colors[i])
                    for i, x in enumerate(news_response)
                ]
                await interaction.edit_original_response(embeds=embeds)


    async def create_periodic_notification_loop(self, interaction, params):
        news_args = {}
        # run_args = {}
        if params["news_args"]["topic"] != "":
            news_args["q"] = params["news_args"]["topic"]
        if params["news_args"]["size"] != 0:
            news_args["size"] = min(5, params["news_args"]["size"])
        if params["news_args"]["source"] != "":
            news_args["domain"] = params["news_args"]["source"]
        if params["news_args"]["category"] != "":
            news_args["category"] = params["news_args"]["category"]
        if params["news_args"]["country"] != "":
            news_args["country"] = params["news_args"]["country"]

        news_args["channel"] = interaction.channel
        news_args["no_news_update"] = params["news_args"].get("no_news_update", False)

        run_args = {
            "hours": params["run_args"].get("hours", 24),
        }
        new_task = tasks.loop(**run_args)(self.news_notification)

        if interaction.guild.id not in self.active_tasks:
            self.active_tasks[interaction.guild.id] = {}
        existing_ids = list(self.active_tasks[interaction.guild.id].keys()) + [0]
        new_id = max(existing_ids) + 1

        self.active_tasks[interaction.guild.id][new_id] = {
            "task": new_task,
            "news_params": news_args,
            "run_params": run_args,
            "started": str(datetime.datetime.now()).split('.')[0].replace(' ', ': ')[:-3]
            # "no_news_update": no_news_update
        }
        new_task.start(task=new_task, **news_args)
        self.db.write_news_notification_to_db(
            guild_id=interaction.guild_id,
            notification_id=new_id,
            data_dict=self.active_tasks[interaction.guild.id][new_id]
        )
        embed = self.create_news_notification_loop_embed(
            guild_id=interaction.guild.id, _id=new_id, color=theme_colors[0]
        )
        await interaction.edit_original_response(
            content="Created News Notification",
            embed=embed,
            # ephemeral=True
        )


    @app_commands.command(name="set_news_notification")
    @app_commands.describe(topic="Topic you want to send news notifications to this channel for. (blank for any)")
    async def start_news_notifications(
            self,
            interaction: discord.Interaction,
            topic: str = "",
    ):
        """
        opens a menu to set up news notifications about a provided topic
        """
        params = {
            "news_args": {
                "size": 5,
                "topic": topic
            },
            "run_args": {
                "hours": 24
            }
        }
        view = CreatePeriodicNewsNotification(
            original_interaction=interaction,
            original_params=params,
            notification_creator=self.create_periodic_notification_loop
        )
        await interaction.response.send_message(
            content="Select categories, sources, countries",
            view=view,
            ephemeral=True
        )
        return


    @app_commands.command(name="get_news_notifications")
    async def get_news_notifications(self, interaction: discord.Interaction,):
        if interaction.guild.id not in self.active_tasks:
            await interaction.response.send_message(
                content="No news notifications have been set up for this guild",
                ephemeral=True
            )
        else:
            embeds = [
                self.create_news_notification_loop_embed(
                    guild_id=interaction.guild.id,
                    _id=x,
                    color=theme_colors[i % len(theme_colors)])
                for i, x in enumerate(self.active_tasks[interaction.guild.id])
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
            self.active_tasks[interaction.guild.id][id]["task"].cancel()
            del self.active_tasks[interaction.guild.id][id]
            self.db.delete_news_notification_from_db(
                guild_id=interaction.guild_id,
                notification_id=id
            )

            await interaction.response.send_message(
                content=f"Successfully stopped news notification loop {id}",
                ephemeral=True
            )


    async def news_notification(self, channel, no_news_update, quiet_start=False, task=None, loop_id=None, **kwargs):
        """
        Sends news notifications in a provided time interval
        """
        print("loop iteration: ", task.current_loop)
        print(f"next occurring at {task.next_iteration}")
        if quiet_start and task:
            if task.current_loop == 0:
                loop_data = self.active_tasks[channel.guild.id][loop_id]
                t = loop_data["started"].split(": ")[1].split(":")
                now = dt.now()
                print(f"now = {now}")
                start = dt(
                    year=now.year,
                    month=now.month,
                    day=now.day,
                    hour=int(t[0]),
                    minute=int(t[1]),
                    second=0
                )
                start = start - tdelta(days=1)
                hours = loop_data["run_params"]["hours"]
                print(hours)
                while now > start:
                    start = start + tdelta(hours=hours)
                seconds = start - now
                seconds = seconds.seconds
                print(f"waiting {seconds} seconds to start tasks at {start}")
                await asyncio.sleep(seconds)
                # todo, make sure this resets the thing
                task.restart(
                    channel=channel,
                    no_news_update=no_news_update,
                    task=task,
                    quiet_start=False,
                    loop_id=loop_id,
                    **kwargs
                )
                return

                # return
        log_events("news task sending news sending news", self.log_file)
        news_articles = self.news_api.get_news(**kwargs)
        if len(news_articles) == 0:
            if no_news_update or (task and task.current_loop == 0):
                await channel.send(content="No news articles found with the provided query")
        else:
            embeds = [
                self.create_article_embed(article=x, color=theme_colors[i])
                for i, x in enumerate(news_articles)
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


    def create_article_embed(self, article: dict, color=theme_colors[0]):
        wsp = "\u200b\t"
        print(article)
        e = discord.Embed(
            title=article["Title"],
            url=article["Link"],
            description=article["description"],
            color=int(color.replace("#", ""), base=16),
            type="article"
        )

        # e.set_footer(text=f"{wsp*20} Source: News")
        e.set_footer(text=article["footer"])


        if "img_url" in article and article["img_url"] not in ["", None]:
            print(f"setting url: {article['img_url']}")
            e.set_thumbnail(url=article["img_url"])
        else:
            print(f"not setting url")
            print(json.dumps(article, indent=5))
        return e


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
            new_task.start(task=new_task, quiet_start=True, loop_id=k, **v["news_params"])
            tasks_for_guild[k]["task"] = new_task
        self.active_tasks[guild.id] = tasks_for_guild

