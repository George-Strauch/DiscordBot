import discord
from discord.ext import commands
from cogs.utils import read_file, log_events
from cogs.ai_cog import AI
from cogs.news_cog import News
from cogs.trends_cog import Trends
from cogs.finance_cog import Finance


class BasedClient(commands.Bot):
    def __init__(self, **kwargs):
        if "command_prefix" not in kwargs:
            kwargs.update(
                {"command_prefix": "!"}
            )
        if "intents" not in kwargs:
            intents = discord.Intents.default()
            intents.message_content = True
            kwargs.update(
                {"intents": intents}
            )
        super().__init__(**kwargs)

        # channels for the bot and news
        self.bot_channel_ids = read_file("bot_channels.json", default=[])
        self.news_channels_ids = read_file("news_channels.json", default=[])
        self.bot_channel = []
        self.news_channels = []
        self.creds = kwargs["creds"]
        self.log_file = "data/discord_runner.log"

    async def on_ready(self):
        """
        called when the bot is initialized
        """
        try:
            await self.load_cogs()
        except Exception as e:
            log_events("exception occurred while syncing commands", self.log_file)
        events = [f'Logged on as {self.user}!']
        log_events(events, self.log_file )


    async def on_message(self, message):
        """
        is called every time a message is sent in any channel the bot is a member of
        """
        if message.author.bot:
            print("Ignoring bot message")
            return
        print(f"{message.author.name} SAID: {message.content}")
        await super().on_message(message)  # todo?
        # await self.process_commands(message)

    async def load_guild_info(self):
        for guild in self.guilds:
            print(f"Found guild {guild.name}")
            # for channel in guild.channels:
            #     if channel.name.upper() == "BOT-ROOM":
            #         events.append(f"Found bot room in {guild.name}")
            #         bot_channels.append(channel)
            #     if channel.name.upper() == "NEWS":
            #         events.append(f"news room in {guild.name}")
            #         news_channels.append(channel)

    async def load_tasks(self):
        # task_functions = [
        #     warn_data,
        #     news_notification
        # ]
        # await wait_to_start(
        #     hr_start=9,
        #     delta_hours=12,
        #     funcs=task_functions
        # )
        pass

    async def load_cogs(self):
        print("Loading Cogs")
        await self.add_cog(AI(self, api_key=self.creds["OPENAI_TOKEN"]))
        await self.add_cog(News(self, api_key=self.creds["NEWSDATAIO_TOKEN"]))
        await self.add_cog(Trends(self))
        await self.add_cog(Finance(self))
        synced = await self.tree.sync()
        print(f"Synced {len(synced)} command(s).")
        print(synced)



if __name__ == '__main__':
    cred_file = "/home/george/Documents/dev-creds.json"
    CREDS = read_file(cred_file)
    # CREDS = read_file("data/creds.json")
    newbot = BasedClient(creds=CREDS)
    newbot.run(CREDS["DISCORD_TOKEN"])

