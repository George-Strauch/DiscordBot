import datetime
import json
import asyncio
import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.ui import Select, View
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
news_categories = {x: x for x in news_categories}.update({"ANY": ""})


sources = {
    "Fox news": "foxnews",
    "NPR": "npr",
    "ABC News": "abcnews",
    "Sky News": "skynews",
    "Yahoo! News": "yahoo",
    "The BBC": "bbc",
    "NBC News": "nbcnews",
    "ANY": ""
}
param_descriptions = {
    "q": "Search of news about a specific query, (Default everything)",
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
    "ANY": ""
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



class CreatePeriodicNewsNotification(View):
    def __init__(self, original_interaction, notification_creator):
        super().__init__()
        self.add_item(CategorySelect(self.category_callback))
        self.add_item(CategorySelect(self.source_callback))
        self.add_item(CategorySelect(self.country_callback))
        # self.add_item(CategorySelect(self.category_callback))
        self.original_interaction = original_interaction
        self.notification_creator = notification_creator
        self.parameters = {}


    async def category_callback(self, interaction: discord.Interaction):
        pass

    async def source_callback(self, interaction: discord.Interaction):
        pass

    async def country_callback(self, interaction: discord.Interaction):
        pass

    async def finish_button_callback(self, interaction: discord.Interaction):
        pass


class CategorySelect(Select):
    def __init__(self, call_back):
        default = "business,politics,science,technology,world".split(',')
        options = [discord.SelectOption(label=k.capitalize(), value=v, default=v in default) for k, v in news_categories]
        super().__init__(options=options, max_values=len(options), min_values=1, placeholder="Categories")
        self.callback = call_back
    # async def callback(self, interaction: discord.Interaction):
    #     pass


class SourceSelect(Select):
    def __init__(self, call_back):
        default = ["npr"]
        options = [discord.SelectOption(label=k, value=v, default=v in default) for k, v in sources]
        super().__init__(options=options, max_values=len(options), min_values=1, placeholder="Sources")
        self.callback = call_back
    # async def callback(self, interaction: discord.Interaction):
    #     pass


class CountrySelect(Select):
    def __init__(self, call_back):
        default = []
        options = [discord.SelectOption(label=k, value=v, default=v in default) for k, v in countries]
        super().__init__(options=options, max_values=len(options), min_values=1, placeholder="Countries")
        self.callback = call_back
    # async def callback(self, interaction: discord.Interaction):
    #     pass




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
                self.create_article_embed(article=x, color=theme_colors[i])
                for i, x in enumerate(news_articles)
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

