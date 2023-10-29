import datetime
import time
import discord
from discord.ext import tasks
from discord.ext import commands
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
    if not os.path.exists(f_name):
        raise Exception(f"please add a file with private tokens for discord and OpenAI [{f_name}]")
    with open(f_name, 'r') as fp:
        return json.load(fp)
CREDS = get_creds()

# ----------------------------------------------------------------------------------
bot_channels = []
news_channels = []
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
# ----------------------------------------------------------------------------------


# initialize libraries
ai = OpenAIwrapper(CREDS["OPENAI_TOKEN"])
news = News(CREDS["NEWSDATAIO_TOKEN"])


# log info
LOG_FILE = "data/discord_runner.log"


def log_events(events):
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


# ------------------------ COMMANDS ------------------------
@bot.command("gpt")
async def ask4(ctx, *, arg):
    log_events(f"[{ctx.author}] ASKED GPT: {arg}")
    reply = ai.generate_response_gpt4(arg)
    index = 0
    while index < len(reply):
        msg = reply[index: index + 2000]
        index = index+2000
        await ctx.send(msg)
        time.sleep(1)


@bot.command("imgen")
async def image_generator(ctx, *, arg):
    log_events(f"[{ctx.author}] WANTS TO GENERATE IMAGE: {arg}")
    reply = ai.image_generator(arg)
    log_events(f"Reply is {reply}")
    await ctx.send(reply)


@bot.command("trending")
async def trending(ctx):
    log_events(f"[{ctx.author}] QUERIED TRENDING")
    trends = get_trending_searches()
    await ctx.send(trends[:2000])


@bot.command("log")
async def get_log_data(ctx):
    # todo make a dm, not a server command
    with open(LOG_FILE, 'r') as fp:
        txt = fp.readlines()
        txt = "".join(txt)
    await ctx.send(txt[-2000:])
    time.sleep(1)
    with open("data/log.txt", 'r') as fp:
        txt = fp.readlines()
        txt = "".join(txt)
    await ctx.send(txt[-2000:])


@bot.command("warn")
async def get_warn_data(ctx):
    log_events("Sent warns message")
    warns = get_new_warn_data()
    await ctx.send(warns)


@bot.command("news")
async def get_news(ctx, *, args=None):
    if args:
        args = args.split(" ")
        print(args)
        if "=" not in args[0]:
            if args[0].lower() == "help":
                message = ("Syntax: !news [query] [arg1=value] [arg2=value]\n"
                           "All Arguments are optional\n"
                           "Arguments:\n"
                           "q: Search Query\n"
                           "size: [int] Number of articles to show (this may be truncated if total message is >2000 "
                           "characters)\n"
                           "domain: News publishers (see list in link)\n"
                           "category: Category (see list in link)\n"
                           "https://newsdata.io/documentation")
                await ctx.send(message)
                return
            args[0] = f"q={args[0]}"
        if not all(["=" in x for x in args]):
            await ctx.send(f"Invalid args, all args must be key=value. provided: {args}")
            return
        else:
            kwargs = {x.split('=')[0].lower(): x.split('=')[1].lower() for x in args}
            if "size" not in kwargs.keys():
                kwargs["size"] = 5
            else:
                kwargs["size"] = int(kwargs["size"])
    else:
        kwargs = {"size": 5}
    print(json.dumps(kwargs, indent=4))
    # return
    log_events("Sending News")
    news_data = news.get_news(**kwargs)
    print(f"len news data is: {len(news_data)}")
    if len(news_data) == 0:
        news_data = "No news articles found"
    await ctx.send(news_data[:2000])
# ------------------------ TASKS ------------------------


@tasks.loop(hours=12)
async def warn_data():
    log_events("Sent warns message")
    warns = get_new_warn_data()
    for channel in bot_channels:
        await channel.send(warns)

@tasks.loop(hours=12)
async def news_notification():
    log_events("sending news")
    news_data = news.get_news(size=5)
    for channel in news_channels:
        await channel.send(news_data)


# ------------------------ EVENTS ------------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        print("Ignoring bot message")
        return
    print(f"{message.author.name} SAID: {message.content}")
    await bot.process_commands(message)


@bot.event
async def on_ready():
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
    bot.run(CREDS["DISCORD_TOKEN"])

