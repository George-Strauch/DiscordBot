import datetime
import json
import asyncio
from typing import Any

import discord
from discord._types import ClientT
from discord.ext import tasks
from discord import Interaction
from discord.ui import Select, View, Button

from ..functions.task_manager import TaskManager
from ..functions.news import News
from ..utils import log_events, theme_colors
from ..database import NewsNotificationDatabase
from datetime import datetime as dt
from datetime import timedelta as tdelta
from ..utils import read_file

news_sources = News.source_map.keys()

param_descriptions = {
    "text": "Search of news about a specific topic, (Default everything)",
    "source": "News Sources (Default: AP, NPR, BBC, ABC News, NBC News)",
    "n": "Number of news articles you want to see (Default 5, Max 6)",
}

news_choices = {
    "sources": [
        discord.app_commands.Choice(name=x, value=x)
        for x in news_sources
    ],
}


class NewsBll:
    def __init__(self,):
        self.log_file = "/opt/bot/data/newsbll.log"
        cred_file = "/opt/bot/data/creds.json"
        self.news_api = News(read_file(cred_file)["WORLDNEWSAPIKEY"])
        self.task_manager = TaskManager()
        self.db = NewsNotificationDatabase("/opt/bot/data/news_notification.db")


    def get_news_raw(
            self,
            text: str = "",
            n: int = 5,
            sources: list = None,
    ):
        kwargs = {}
        if text not in [None, ""]:
            kwargs["text"] = text
        if sources not in [None, "", []]:
            kwargs["sources"] = sources
        news = self.news_api.search_news(
            **kwargs
        )
        if "error" in news:
            msg = f"failed to get news with params: {kwargs}\nmessage: {news['error']}"
            log_events([msg], log_file=self.log_file)
            return []
        else:
            data = news["articles"][:n]
            print(data)
        for i in range(len(data)):
            data[i]["text"] = data[i]["text"].replace(r"\u2014", "-").replace(r"\u2019", "'")
            desc = data[i]["text"].split(" ")[:15] + ["..."]
            desc = " ".join(desc)
            data[i]["description"] = desc
            data[i]["source"] = ""
            for k, v in News.source_map.items():
                if v in data[i]["url"]:
                    data[i]["source"] = k
                    break
            if data[i]["source"] == "":
                x = data[i]["url"].split("//")[1]
                x = data[i]["url"].split("/")[0]
                data[i]["source"] = x
        return data


    def get_news(
            self,
            text: str = "",
            n: int = 5,
            sources: list = None,
    ) -> dict:
        """
        Shows most recent news
        """
        kwargs = {"n": n}
        if text != "":
            kwargs["text"] = text
        if sources is not None:
            kwargs["sources"] = sources
        log_events(f"Sending News:\n{json.dumps(kwargs, indent=4)}", self.log_file)
        news_response = self.get_news_raw(**kwargs)
        if len(news_response) == 0:
            return {"content": "No news articles found with the provided query"}
        else:
            print(len(news_response))
            embeds = [
                self.create_article_embed(article=x, color=theme_colors[i])
                for i, x in enumerate(news_response)
            ]
            return {"embeds": embeds}



    # def _create_periodic_notification_loop(
    #         self,
    #         channel,
    #         params
    # ) -> dict:
    #
    #     news_args = {}
    #     # run_args = {}
    #     if params["news_args"]["topic"] != "":
    #         news_args["q"] = params["news_args"]["topic"]
    #     if params["news_args"]["size"] != 0:
    #         news_args["size"] = min(5, params["news_args"]["size"])
    #     if params["news_args"]["source"] != "":
    #         news_args["domain"] = params["news_args"]["source"]
    #     if params["news_args"]["category"] != "":
    #         news_args["category"] = params["news_args"]["category"]
    #     if params["news_args"]["country"] != "":
    #         news_args["country"] = params["news_args"]["country"]
    #
    #     news_args["channel"] = channel
    #     news_args["empty_update"] = params["news_args"].get("empty_update", False)
    #
    #     run_args = {
    #         "hours": params["run_args"].get("hours", 24),
    #     }
    #     print(0)
    #
    #     new_task = tasks.loop(**run_args)(self._news_notification)
    #     print(1)
    #
    #     if channel.guild.id not in self.task_manager.news_notifications:
    #         self.task_manager.news_notifications[channel.guild.id] = {}
    #     existing_ids = list(self.task_manager.news_notifications[channel.guild.id].keys()) + [0]
    #     new_id = max(existing_ids) + 1
    #
    #     self.task_manager.news_notifications[channel.guild.id][new_id] = {
    #         "task": new_task,
    #         "news_params": news_args,
    #         "run_params": run_args,
    #         "started": str(datetime.datetime.now()).split('.')[0].replace(' ', ': ')[:-3]
    #     }
    #     new_task.start(task=new_task, **news_args)
    #     self.db.write_news_notification_to_db(
    #         guild_id=channel.guild.id,
    #         notification_id=new_id,
    #         data_dict=self.task_manager.news_notifications[channel.guild.id][new_id]
    #     )
    #     embed = self._create_news_notification_loop_embed(
    #         guild_id=channel.guild.id, _id=new_id, color=theme_colors[0]
    #     )
    #
    #     return {
    #         "content": "Created News Notification",
    #         "embed": embed,
    #     }
    #
    #
    # def start_news_notification_with_view(
    #         self,
    #         ctx,
    #         clear_view,
    #         channel,
    #         topic: str = "",
    #         frequency: int = 24,
    #         empty_update: bool = False
    # ) -> dict:
    #     """
    #     opens a menu to set up news notifications about a provided topic
    #     # todo this might be broken
    #     """
    #     params = {
    #         "news_args": {
    #             "size": 5,
    #             "topic": topic,
    #             "empty_update": empty_update
    #         },
    #         "run_args": {
    #             "hours": frequency if frequency in [12, 24, 48] else 24  # todo enumerate parameter
    #
    #         }
    #     }
    #     view = CreatePeriodicNewsNotification(
    #         channel=channel,
    #         original_params=params,
    #         ctx=ctx,
    #         notification_creator=self._create_periodic_notification_loop,
    #         clear_view=clear_view
    #     )
    #     return {
    #         "content": "Select categories, sources, countries",
    #         "view": view,
    #         "ephemeral": True
    #     }


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


    # async def _news_notification(
    #         self,
    #         channel,
    #         hours=24,
    #         started="",
    #         empty_update=False,
    #         quiet_start=False,
    #         task=None,
    #         loop_id=None,
    #         **kwargs
    # ):
    #     """
    #     this method is the task object definition for each news notification runner
    #     Sends news notifications in a provided time interval
    #     """
    #     # print(f"args: {kwargs}")
    #     # print("loop iteration: ", task.current_loop)
    #     # print(f"next occurring at {task.next_iteration}")
    #     if quiet_start and task:
    #         if task.current_loop == 0:
    #
    #             # loop_data = self.task_manager.news_notifications[channel.guild.id][loop_id]
    #             t = started.split(": ")[1].split(":")
    #             now = dt.now()
    #             start = dt(
    #                 year=now.year,
    #                 month=now.month,
    #                 day=now.day,
    #                 hour=int(t[0]),
    #                 minute=int(t[1]),
    #                 second=0
    #             )
    #             start = start - tdelta(days=1)
    #             while now > start:
    #                 start = start + tdelta(hours=hours)
    #             seconds = start - now
    #             seconds = seconds.seconds
    #             print(f"waiting {seconds} seconds to start tasks at {start}")
    #             await asyncio.sleep(seconds)
    #             # todo, make sure this resets the thing
    #             task.restart(
    #                 channel=channel,
    #                 empty_update=empty_update,
    #                 task=task,
    #                 quiet_start=False,
    #                 loop_id=loop_id,
    #                 **kwargs
    #             )
    #             return
    #
    #             # return
    #     log_events("news task sending news sending news", self.log_file)
    #     news_articles = self.news_api.get_news(**kwargs)
    #     if len(news_articles) == 0:
    #         if empty_update or (task and task.current_loop == 0):
    #             await channel.send(content="No news articles found with the provided query")
    #     else:
    #         embeds = [
    #             self.create_article_embed(article=x, color=theme_colors[i])
    #             for i, x in enumerate(news_articles)
    #         ]
    #         await channel.send(embeds=embeds)


    # def _create_news_notification_loop_embed(self, guild_id, _id, color):
    #     if _id not in self.task_manager.news_notifications[guild_id]:
    #         return None
    #     x = self.task_manager.news_notifications[guild_id][_id]
    #
    #     # todo: create a field map for human friendly filed names
    #     desc = {
    #         k: v
    #         for k, v in x["news_params"].items() if k != 'channel'
    #     }
    #     desc.update({
    #         k: v
    #         for k, v in x["run_params"].items()
    #     })
    #     desc["started"] = x['started']
    #     desc["channel"] = x['news_params']['channel'].name
    #
    #     e = discord.Embed(
    #         title=f"id:\t{_id}",
    #         color=int(color.replace("#", ""), base=16)
    #     )
    #
    #     for i, (k, v) in enumerate(desc.items()):
    #         e.insert_field_at(
    #             index=i,
    #             name=k,
    #             value=f"```{v}```",
    #             inline=len(str(v)) < 14
    #         )
    #     return e


    def create_article_embed(self, article: dict, color=theme_colors[0]):
        e = discord.Embed(
            title=article["title"],
            url=article["url"],
            description=article["description"],
            color=int(color.replace("#", ""), base=16),
            type="article"
        )
        sep = "  |  "
        footer = f"{article['source']}{sep}{article['publish_date']}{sep}API Source: `[worldnewsapi](https://worldnewsapi.com/)`"
        e.set_footer(text=footer)
        if "image" in article and article["image"] not in ["", None]:
            e.set_thumbnail(url=article["image"])
        return e

    def create_brief_article_embed(self, articles: list, title: str = "", color=theme_colors[0]):
        fields = ["title", "description", "url"]
        articles = [
            {
                k: x[k]
                for k in fields
            }
            for x in articles
        ]
        e = discord.Embed(
            title=title if title != "" else None,
            color=int(color.replace("#", ""), base=16),
        )
        for x in articles:
            e.add_field(
                name=f'[{x["title"]({x["url"]})}]',
                value=x['description'],
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
