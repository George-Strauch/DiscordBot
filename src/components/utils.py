import json
import os
import datetime
import asyncio
from datetime import datetime as dt
from datetime import timedelta as tdelta
import discord




theme_colors = [
    "#c9e6f2", "#F2D388", "#C98474", "#30475E",
    "#F1935C", "#BA6B57", "#E7B2A5", "#874C62",
]
# theme_colors = [int(x.replace("#", ""), base=16) for x in theme_colors]


blank_px = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z/C/HgAGgwJ/lK3Q6wAAAABJRU5ErkJggg=="


def read_file(fname, default={}):
    if not os.path.exists(fname):
        # raise Exception(f"Cannot find file[{fname}]")
        return default
    with open(fname, 'r') as fp:
        content = fp.read()
        return json.loads(content)


def write_json(fname, data=""):
    try:
        if not isinstance(data, str):
            data = json.dumps(data, indent=4)
        with open(fname, 'w') as fp:
            fp.writelines(data)
    except Exception as e:
        # todo
        raise e


def chunk_message(inpt: str) -> list:
    """
    Split a message into chunks if the input is over
    # todo, this is lazy, and works only most of the time, fix
    2000 characters taking into consideration markdown blocks
    :param inpt: input string
    :return: (list) chunks where each chunk is a string < 2000 chars
    """
    if len(inpt) < 2000:
        return [inpt]
    text = inpt.split("\n")
    message = ""
    parts = []
    for x in text:
        if len(message) + len(x) + 1 < 2000:
            message = message+"\n"+x
        else:
            parts.append(message)
            message = x

    return parts + [message[:2000]]



def log_events(events, log_file):
    """
    logs a string or list of string events to the log file
    """
    print(events)
    if log_file is None:
        return
    now = datetime.datetime.now()
    if len(events) == 0:
        return
    if not isinstance(events, list):
        events = [events]
    events = [f"[{now}] {x}\n" for x in events]
    if not os.path.exists(log_file):
        print("creating log file")
        with open(log_file, "w") as fp:
            fp.writelines(events)
    else:
        with open(log_file, "a") as fp:
            fp.writelines(events)


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
    # log_events(f"waiting {seconds} seconds to start tasks at {start}", LOG_FILE)
    await asyncio.sleep(seconds)
    for f in funcs:
        f.start()





    # todo finish
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






