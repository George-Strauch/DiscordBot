import datetime
import json
import asyncio
from typing import Any

import discord
from discord._types import ClientT
from discord.ext import tasks
from discord import Interaction
from discord.ui import Select, View, Button

from src.components.functions.task_manager import TaskManager
from ..functions.news import NewsFunctions
from ..utils import log_events, theme_colors
from ..database import NewsNotificationDatabase
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
            # await self.
            await self.start_func()
            await interaction.response.defer()

    class CancelButton(Button):
        def __init__(self, cancel):
            super().__init__(label="Cancel", style=discord.ButtonStyle.danger, row=4)
            self.cancel = cancel

        async def callback(self, interaction: Interaction[ClientT]) -> Any:
            await self.cancel()
            await interaction.response.defer()


    def __init__(self, channel, ctx, original_params, notification_creator, clear_view):
        super().__init__()
        self.news_parameters = {}
        self.run_parameters = {}
        self.params = original_params
        self.add_item(self.CategorySelect(self.data_passer))
        self.add_item(self.SourceSelect(self.data_passer))
        self.add_item(self.CountrySelect(self.data_passer))
        self.add_item(self.CancelButton(self.cancel))
        self.add_item(self.StartNotificationButton(self.start))

        self.notification_creator = notification_creator
        self.channel = channel
        self.ctx = ctx
        self.clear_view = clear_view

    def data_passer(self, received_data: dict):
        run_params = ["frequency", "empty_update"]
        if any([k in run_params for k in received_data.keys()]):
            self.params["run_args"].update(received_data)
        else:
            self.params["news_args"].update(received_data)


    async def start(self):
        self.notification_creator(
            self.channel,
            self.params
        )
        await self.clear_view()
        await self.ctx.reply(
            view=None,
            content="News notification has been set up.\nUse /notifications to view active notifications",
            ephemeral=True
        )

    async def cancel(self):
        await self.clear_view()
        await self.ctx.reply(
            content="Canceled news notification setup",
            ephemeral=True
        )


class NewsBll:
    def __init__(self, api_key: str = ""):
        self.log_file = "/opt/bot/data/news.log"
        self.news_api = NewsFunctions(api_key)
        self.task_manager = TaskManager()
        self.db = NewsNotificationDatabase("/opt/bot/data/news_notification.db")


    def get_full_raw_news(
            self,
            topic: str = "",
            n: int = 5,
            source: str = "",
            category: str = "",
            country: str = ""
    ):
        kwargs = {}
        if topic != "":
            kwargs["q"] = topic
        if n != 0:
            kwargs["size"] = min(n, 5)
        if source != "":
            kwargs["domain"] = source
        if category != "":
            kwargs["category"] = category
        if country != "":
            kwargs["country"] = country
        return self.news_api.get_news_raw(**kwargs).get("results", [])


    def get_news(
            self,
            topic: str = "",
            n: int = 5,
            source: str = "",
            category: str = "",
            country: str = "us"
    ) -> dict:
        """
        Shows most recent news
        """
        kwargs = {}
        if topic != "":
            kwargs["q"] = topic
        if n != 0:
            kwargs["size"] = min(n, 5)
        if source != "":
            kwargs["domain"] = source
        if category != "":
            kwargs["category"] = category
        if country != "":
            kwargs["country"] = country

        log_events(f"Sending News:\n{json.dumps(kwargs, indent=4)}", self.log_file)
        news_response = self.news_api.get_news(**kwargs)
        if len(news_response) == 0:
            return {"content": "No news articles found with the provided query"}
        else:
            if isinstance(news_response, str):
                return {"content": "An error occurred getting news articles, sorry"}
            else:
                embeds = [
                    self.create_article_embed(article=x, color=theme_colors[i])
                    for i, x in enumerate(news_response)
                ]
                return {"embeds": embeds}


    def _create_periodic_notification_loop(
            self,
            channel,
            params
    ) -> dict:

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

        news_args["channel"] = channel
        news_args["empty_update"] = params["news_args"].get("empty_update", False)

        run_args = {
            "hours": params["run_args"].get("hours", 24),
        }
        print(0)

        new_task = tasks.loop(**run_args)(self._news_notification)
        print(1)

        if channel.guild.id not in self.task_manager.news_notifications:
            self.task_manager.news_notifications[channel.guild.id] = {}
        existing_ids = list(self.task_manager.news_notifications[channel.guild.id].keys()) + [0]
        new_id = max(existing_ids) + 1

        self.task_manager.news_notifications[channel.guild.id][new_id] = {
            "task": new_task,
            "news_params": news_args,
            "run_params": run_args,
            "started": str(datetime.datetime.now()).split('.')[0].replace(' ', ': ')[:-3]
        }
        new_task.start(task=new_task, **news_args)
        self.db.write_news_notification_to_db(
            guild_id=channel.guild.id,
            notification_id=new_id,
            data_dict=self.task_manager.news_notifications[channel.guild.id][new_id]
        )
        embed = self._create_news_notification_loop_embed(
            guild_id=channel.guild.id, _id=new_id, color=theme_colors[0]
        )

        return {
            "content": "Created News Notification",
            "embed": embed,
        }


    def start_news_notification_with_view(
            self,
            ctx,
            clear_view,
            channel,
            topic: str = "",
            frequency: int = 24,
            empty_update: bool = False
    ) -> dict:
        """
        opens a menu to set up news notifications about a provided topic
        # todo this might be broken
        """
        params = {
            "news_args": {
                "size": 5,
                "topic": topic,
                "empty_update": empty_update
            },
            "run_args": {
                "hours": frequency if frequency in [12, 24, 48] else 24  # todo enumerate parameter

            }
        }
        view = CreatePeriodicNewsNotification(
            channel=channel,
            original_params=params,
            ctx=ctx,
            notification_creator=self._create_periodic_notification_loop,
            clear_view=clear_view
        )
        return {
            "content": "Select categories, sources, countries",
            "view": view,
            "ephemeral": True
        }


    def get_news_notifications(self, guild_id):
        if guild_id not in self.task_manager.news_notifications:
            return {
                "content": "No news notifications have been set up for this guild",
                "ephemeral": True
            }
        else:
            embeds = [
                self._create_news_notification_loop_embed(
                    guild_id=guild_id,
                    _id=x,
                    color=theme_colors[i % len(theme_colors)]
                )
                for i, x in enumerate(self.task_manager.news_notifications[guild_id])
            ]
            return {
                "embeds": embeds,
                "ephemeral": True
            }


    def stop_news_notifications(self, guild_id, _id: int) -> dict:
        """
        kills a news notification loop with a provided id
        """
        if _id not in self.task_manager.news_notifications[guild_id]:
            return {
                "content": f"No news notification loop found with id {_id}. "
                           "Use /get_news_notifications to get list of currently running news notification loops",
                "ephemeral": True
            }
        else:
            self.task_manager.news_notifications[guild_id][_id]["task"].cancel()
            self.db.delete_news_notification_from_db(
                guild_id=guild_id,
                notification_id=_id
            )
            del self.task_manager.news_notifications[guild_id][_id]
            return {
                "content": f"Successfully stopped news notification loop {_id}",
                "ephemeral": True
            }


    async def _news_notification(
            self,
            channel,
            hours=24,
            started="",
            empty_update=False,
            quiet_start=False,
            task=None,
            loop_id=None,
            **kwargs
    ):
        """
        this method is the task object definition for each news notification runner
        Sends news notifications in a provided time interval
        """
        # print(f"args: {kwargs}")
        # print("loop iteration: ", task.current_loop)
        # print(f"next occurring at {task.next_iteration}")
        if quiet_start and task:
            if task.current_loop == 0:

                # loop_data = self.task_manager.news_notifications[channel.guild.id][loop_id]
                t = started.split(": ")[1].split(":")
                now = dt.now()
                start = dt(
                    year=now.year,
                    month=now.month,
                    day=now.day,
                    hour=int(t[0]),
                    minute=int(t[1]),
                    second=0
                )
                start = start - tdelta(days=1)
                while now > start:
                    start = start + tdelta(hours=hours)
                seconds = start - now
                seconds = seconds.seconds
                print(f"waiting {seconds} seconds to start tasks at {start}")
                await asyncio.sleep(seconds)
                # todo, make sure this resets the thing
                task.restart(
                    channel=channel,
                    empty_update=empty_update,
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
            if empty_update or (task and task.current_loop == 0):
                await channel.send(content="No news articles found with the provided query")
        else:
            embeds = [
                self.create_article_embed(article=x, color=theme_colors[i])
                for i, x in enumerate(news_articles)
            ]
            await channel.send(embeds=embeds)


    def _create_news_notification_loop_embed(self, guild_id, _id, color):
        if _id not in self.task_manager.news_notifications[guild_id]:
            return None
        x = self.task_manager.news_notifications[guild_id][_id]

        # todo: create a field map for human friendly filed names
        desc = {
            k: v
            for k, v in x["news_params"].items() if k != 'channel'
        }
        desc.update({
            k: v
            for k, v in x["run_params"].items()
        })
        desc["started"] = x['started']
        desc["channel"] = x['news_params']['channel'].name

        e = discord.Embed(
            title=f"id:\t{_id}",
            color=int(color.replace("#", ""), base=16)
        )

        for i, (k, v) in enumerate(desc.items()):
            e.insert_field_at(
                index=i,
                name=k,
                value=f"```{v}```",
                inline=len(str(v)) < 14
            )
        return e



    def create_article_embed(self, article: dict, color=theme_colors[0]):
        print(article)
        e = discord.Embed(
            title=article["Title"],
            url=article["Link"],
            description=article["description"],
            color=int(color.replace("#", ""), base=16),
            type="article"
        )
        e.set_footer(text=article["footer"])
        if "img_url" in article and article["img_url"] not in ["", None]:
            print(f"setting url: {article['img_url']}")
            e.set_thumbnail(url=article["img_url"])
        else:
            print(f"not setting url")
            print(json.dumps(article, indent=5))
        return e

    def create_brief_article_embed(self, articles: list, title: str = "", color=theme_colors[0]):
        fields = ["title", "description", "link"]
        articles = [
            {
                k: x[k]
                for k in fields
            }
            for x in articles
        ]
        e = discord.Embed(
            title=title if title != "" else None,
            # url=article["Link"],
            # description=article["description"],
            color=int(color.replace("#", ""), base=16),
            # type="article"
        )
        for x in articles:
            e.add_field(
                name=x["title"],
                value=f"{x['description']}\n{x['link']}",
                inline=False
            )
        return e


    def load_from_db(self, guild):
        tasks_for_guild = self.db.read_news_notification_to_db(guild.id)
        if tasks_for_guild == {}:
            return
        for k, v in tasks_for_guild.items():
            channel = guild.get_channel(v["news_params"]["channel"])
            if not channel:
                print("cannot find channel")
                continue
            tasks_for_guild[k]["news_params"]["channel"] = channel
            new_task = tasks.loop(**v["run_params"])(self._news_notification)
            new_task.start(
                hours=v["run_params"]["hours"],
                started=v["started"],
                task=new_task,
                quiet_start=True,
                loop_id=k,
                **v["news_params"]
            )
            tasks_for_guild[k]["task"] = new_task
        self.task_manager.news_notifications[guild.id] = tasks_for_guild

if __name__ == '__main__':
    pass