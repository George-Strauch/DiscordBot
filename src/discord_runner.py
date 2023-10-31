import datetime
import time
import discord
from discord.ext import tasks
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime as dt
from datetime import timedelta as tdelta
import os
import json

# functions
from functions.warn_notice import get_new_warn_data
from functions.ai import OpenAIwrapper
from functions.trends import *
from functions.news import News


def get_creds():
    f_name = "data/creds.json"
    # f_name = "~/Documents/dev-creds.json"
    if not os.path.exists(f_name):
        raise Exception(f"please add a file with private tokens for discord and OpenAI [{f_name}]")
    with open(f_name, 'r') as fp:
        return json.load(fp)
CREDS = get_creds()


# log info
LOG_FILE = "data/discord_runner.log"


# ----------------------------------------------------------------------------------
# channels for the bot and news, TODO: save these to a json file
bot_channels = []
news_channels = []

# initialize the discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
# ----------------------------------------------------------------------------------


# initialize libraries with the credentials
ai = OpenAIwrapper(CREDS["OPENAI_TOKEN"])
news = News(CREDS["NEWSDATAIO_TOKEN"])


def log_events(events):
    """
    logs a string or list of string events to the log file
    """
    print(events)
    now = datetime.datetime.now()
    if len(events) == 0:
        return
    if not isinstance(events, list):
        events = [events]
    events = [f"[{now}] {x}\n" for x in events]
    if not os.path.exists(LOG_FILE):
        print("crating log file")
        with open(LOG_FILE, "w") as fp:
            fp.writelines(events)
    else:
        with open(LOG_FILE, "a") as fp:
            fp.writelines(events)


# ------------------------ Utilities------------------------
def clean_message(s: str=""):
    return s



# ------------------------ APPLICATION COMMANDS ------------------------
@bot.tree.command(name="gpt", description="use chat GPT")
@app_commands.describe(prompt="Prompt for GPT4")
async def ask4(interaction: discord.Interaction, prompt:str):
    """
    Query GPT4 with command
    """
    # todo remove mention instructions from context

    log_events(f"[{interaction.user.name}] ASKED GPT: {prompt}")
    reply = ai.generate_response_gpt4(prompt)
    index = 0
    while index < len(reply):
        msg = reply[index: index + 2000]
        index = index+2000
        await interaction.response.send_message(msg)
        time.sleep(1)


@bot.tree.command(name="imgen")
@app_commands.describe(prompt="Thing you want an image of")
async def image_generator(interaction: discord.Interaction, prompt:str):
    """
    Generate an image using from Open AI
    """
    log_events(f"[{interaction.user.name}] WANTS TO GENERATE IMAGE: {prompt}")
    await interaction.response.send_message("Working on that, one sec ...")
    reply = ai.image_generator(prompt)
    log_events(f"Reply is {reply}")
    await interaction.edit_original_response(content=reply)


@bot.tree.command(name="trending")
async def trending(interaction: discord.Interaction):
    """
    Get a list of trending google searches with command !trending
    """
    log_events(f"[{interaction.user.name}] QUERIED TRENDING")
    trends = get_trending_searches()
    await interaction.response.send_message(trends[:2000])


@bot.tree.command(name="log")
async def get_log_data(interaction: discord.Interaction):
    """
    display log data in case of unexpected behavior
    """
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "NT buddy, but that's only for admins. Just for that you are now breathing manually and "
            "aware there is no comfortable spot in your mouth for your tongue",
            ephemeral=True
        )
        return
    with open(LOG_FILE, 'r') as fp:
        txt = fp.readlines()
        txt = "".join(txt)
    await interaction.response.send_message(txt[-2000:], ephemeral=True)
    time.sleep(1)
    with open("data/log.txt", 'r') as fp:
        txt = fp.readlines()
        txt = "".join(txt)
    await interaction.response.send_message(txt[-2000:], ephemeral=True)


# @bot.tree.command(name="warn")
# @app_commands.describe(pending="Show ones have not gone into effect yet")
# async def get_warn_data(interaction: discord.Interaction, pending: bool=True):
#     """
#     Pulls warn act data and displays it
#     """
#     log_events("Sent warns message")
#     warns = get_new_warn_data()
#     await interaction.response.send_message(warns)


@bot.tree.command(name="news")
@app_commands.describe(q="Query", domain="News Source", n="Number of news articles you want to see (Max 6)")
@app_commands.choices(domain=[
    discord.app_commands.Choice(name="Fox news", value="foxnews"),
    discord.app_commands.Choice(name="NPR", value="npr"),
    discord.app_commands.Choice(name="ABC News", value="abcnews")

])
async def get_news(interaction: discord.Interaction, q: str="", n: int=5, domain: discord.app_commands.Choice[str]=""):
    """
    Shows most recent news
    """
    kwargs = {}
    if q != "":
        kwargs["q"] = q
    if n != 0:
        kwargs["size"] = min(n, 5)
    if domain != "":
        kwargs["doamin"] = domain.value

    log_events(f"Sending News:\n{json.dumps(kwargs, indent=4)}")
    news_data = news.get_news(**kwargs)
    print(f"len news data is: {len(news_data)}")
    if len(news_data) == 0:
        news_data = "No news articles found"
    await interaction.response.send_message(news_data[:2000])


# ------------------------ TASKS ------------------------
@tasks.loop(hours=12)
async def warn_data():
    """
    sends new data from warn act from texas every 12 hours
    """
    log_events("Sent warns message")
    warns = get_new_warn_data()
    for channel in bot_channels:
        await channel.send(warns)


@tasks.loop(hours=12)
async def news_notification():
    """
    Sends news notifications every 12 hours
    """
    log_events("sending news")
    news_data = news.get_news(size=5)
    for channel in news_channels:
        await channel.send(news_data)


# ------------------------ EVENTS ------------------------
@bot.event
async def on_message(message):
    """
    is called every time a message is sent in any channel the bot is a member of
    """
    if message.author.bot:
        print("Ignoring bot message")
        return
    print(f"{message.author.name} SAID: {message.content}")
    await bot.process_commands(message)


@bot.event
async def on_ready():
    """
    called when the bot is initialized
    """
    try:
        synced = await bot.tree.sync()
        print(f"Synced? {synced}")
    except Exception as e:
        log_events("exception occurred while syncing commands")
    events = []
    for guild in bot.guilds:
        events.append(f"Found guild {guild.name}")
        for channel in guild.channels:
            if channel.name.upper() == "BOT-ROOM":
                events.append(f"Found bot room in {guild.name}")
                bot_channels.append(channel)
            if channel.name.upper() == "NEWS":
                events.append(f"news room in {guild.name}")
                news_channels.append(channel)
    events.append(f'Logged on as {bot.user}!')
    log_events(events)
    task_functions = [
        warn_data,
        news_notification
    ]
    await wait_to_start(
        hr_start=9,
        delta_hours=12,
        funcs=task_functions
    )


async def wait_to_start(hr_start, delta_hours=12, funcs=[]):
    now = dt.now()
    start = dt(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=hr_start,
        minute=0,
        second=0
    )
    while now > start:
        start = start + tdelta(hours=delta_hours)

    seconds = start - now
    seconds = seconds.seconds
    print(f"waiting {seconds} seconds to start tasks at {start}")
    log_events(f"waiting {seconds} seconds to start tasks at {start}")
    await asyncio.sleep(seconds)
    for f in funcs:
        f.start()


if __name__ == '__main__':
    """
    Start the bot
    """
    bot.run(CREDS["DISCORD_TOKEN"])

