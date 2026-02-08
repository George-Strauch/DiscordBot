import asyncio
import datetime
import json
import logging

import discord
from discord.ext import tasks
from datetime import datetime as dt
from datetime import timedelta as tdelta

from bot import config
from bot.services.task_manager import TaskManager
from bot.services.news_client import News
from bot.utils import theme_colors
from bot.database.news_db import NewsNotificationDatabase

logger = logging.getLogger(__name__)

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
    def __init__(self):
        self.news_api = News(config.WORLD_NEWS_API_KEY)
        self.task_manager = TaskManager()
        self.db = NewsNotificationDatabase(config.DB_PATH)

    def get_news_raw(self, text: str = "", n: int = 5, sources: list = None) -> dict:
        kwargs = {}
        if text not in [None, ""]:
            kwargs["text"] = text
        if sources not in [None, "", []]:
            kwargs["sources"] = sources
        logger.debug("RAW NEWS KWARGS: %s", json.dumps(kwargs))
        news = self.news_api.search_news(**kwargs)
        if "error" in news:
            msg = f"failed to get news with params: {kwargs}\nmessage: {news['error']}"
            logger.warning(msg)
            return {"error": "An API error occurred"}
        elif len(news["articles"]) == 0:
            logger.info("no news articles found with query")
            return {"error": "No news articles found with query"}
        else:
            data = news["articles"][:n]
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
                data[i]["source"] = x.upper()
        return {"news": data}

    def get_news(self, text: str = "", n: int = 5, sources: list = None) -> dict:
        kwargs = {"n": n}
        if text != "":
            kwargs["text"] = text
        if sources is not None:
            kwargs["sources"] = sources
        logger.info("Sending News: %s", json.dumps(kwargs, indent=4))
        news_response = self.get_news_raw(**kwargs)
        if "error" in news_response:
            return {"content": news_response}
        news_response = news_response["news"]
        embeds = [
            self.create_article_embed(article=x, color=theme_colors[i])
            for i, x in enumerate(news_response)
        ]
        return {"embeds": embeds}

    def get_news_notifications(self, guild_id):
        if guild_id not in self.task_manager.news_notifications:
            return {
                "content": "No news notifications have been set up for this guild",
                "ephemeral": True,
            }
        else:
            embeds = [
                self._create_news_notification_loop_embed(
                    guild_id=guild_id,
                    _id=x,
                    color=theme_colors[i % len(theme_colors)],
                )
                for i, x in enumerate(self.task_manager.news_notifications[guild_id])
            ]
            return {"embeds": embeds, "ephemeral": True}

    def stop_news_notifications(self, guild_id, _id: int) -> dict:
        if _id not in self.task_manager.news_notifications[guild_id]:
            return {
                "content": f"No news notification loop found with id {_id}. "
                           "Use /get_news_notifications to get list of currently running news notification loops",
                "ephemeral": True,
            }
        else:
            self.task_manager.news_notifications[guild_id][_id]["task"].cancel()
            self.db.delete_news_notification_from_db(guild_id=guild_id, notification_id=_id)
            del self.task_manager.news_notifications[guild_id][_id]
            return {
                "content": f"Successfully stopped news notification loop {_id}",
                "ephemeral": True,
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
        **kwargs,
    ):
        if quiet_start and task:
            if task.current_loop == 0:
                t = started.split(": ")[1].split(":")
                now = dt.now()
                start = dt(
                    year=now.year,
                    month=now.month,
                    day=now.day,
                    hour=int(t[0]),
                    minute=int(t[1]),
                    second=0,
                )
                start = start - tdelta(days=1)
                while now > start:
                    start = start + tdelta(hours=hours)
                seconds = start - now
                seconds = seconds.seconds
                logger.info("waiting %d seconds to start tasks at %s", seconds, start)
                await asyncio.sleep(seconds)
                task.restart(
                    channel=channel,
                    empty_update=empty_update,
                    task=task,
                    quiet_start=False,
                    loop_id=loop_id,
                    **kwargs,
                )
                return

        logger.info("news task sending news")
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
        desc = {k: v for k, v in x["news_params"].items() if k != "channel"}
        desc.update({k: v for k, v in x["run_params"].items()})
        desc["started"] = x["started"]
        desc["channel"] = x["news_params"]["channel"].name

        e = discord.Embed(
            title=f"id:\t{_id}",
            color=int(color.replace("#", ""), base=16),
        )
        for i, (k, v) in enumerate(desc.items()):
            e.insert_field_at(
                index=i,
                name=k,
                value=f"```{v}```",
                inline=len(str(v)) < 14,
            )
        return e

    def create_article_embed(self, article: dict, color=theme_colors[0]):
        e = discord.Embed(
            title=article["title"],
            url=article["url"],
            description=article["description"],
            color=int(color.replace("#", ""), base=16),
            type="article",
        )
        sep = "  |  "
        footer = f"{article['source']}{sep}{article['publish_date']}{sep}API Source: `[worldnewsapi](https://worldnewsapi.com/)`"
        e.set_footer(text=footer)
        if "image" in article and article["image"] not in ["", None]:
            e.set_thumbnail(url=article["image"])
        return e

    def create_brief_article_embed(self, articles: list, title: str = "", color=theme_colors[0]):
        fields = ["title", "description", "url"]
        articles = [{k: x[k] for k in fields} for x in articles]
        e = discord.Embed(
            title=title if title != "" else None,
            color=int(color.replace("#", ""), base=16),
        )
        for x in articles:
            e.add_field(name=x["title"], value=x["url"], inline=False)
        return e

    def load_from_db(self, guild):
        tasks_for_guild = self.db.read_news_notification_to_db(guild.id)
        if tasks_for_guild == {}:
            return
        for k, v in tasks_for_guild.items():
            channel = guild.get_channel(v["news_params"]["channel"])
            if not channel:
                logger.warning("cannot find channel")
                continue
            tasks_for_guild[k]["news_params"]["channel"] = channel
            new_task = tasks.loop(**v["run_params"])(self._news_notification)
            new_task.start(
                hours=v["run_params"]["hours"],
                started=v["started"],
                task=new_task,
                quiet_start=True,
                loop_id=k,
                **v["news_params"],
            )
            tasks_for_guild[k]["task"] = new_task
        self.task_manager.news_notifications[guild.id] = tasks_for_guild
