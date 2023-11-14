import traceback

import discord
from discord.ext import commands, tasks
from components.utils import read_file, log_events
from components.ai_cog import AI
from components.news_cog import News
from components.trends_cog import Trends
from components.finance_cog import Finance
from components.interactions_cog import Interactions
from components.admins_cog import AdminActions
from components.ada_cog import AdaNlp



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
        self.log_file = "/opt/bot/data/discord_runner.log"


    async def on_ready(self):
        """
        called when the bot is initialized
        """
        try:
            await self.load_cogs()
            # print("syncing")
            # x = await self.tree.sync()
            # print("back")
            # print(x)
        except Exception as e:
            print(traceback.format_exc())
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



    async def load_cogs(self):
        print("Loading Cogs")
        await self.add_cog(AI(self, api_key=self.creds["OPENAI_TOKEN"]))
        await self.add_cog(News(self, api_key=self.creds["NEWSDATAIO_TOKEN"], guilds=self.guilds))
        await self.add_cog(Trends(self))
        await self.add_cog(Finance(self))
        await self.add_cog(Interactions(self))
        await self.add_cog(AdaNlp(
            self,
            news_api_key=self.creds["NEWSDATAIO_TOKEN"],
            ai_api_key=self.creds["OPENAI_TOKEN"])
        )
        # await self.add_cog(NewsTask(self, api_key=self.creds["NEWSDATAIO_TOKEN"]))
        await self.add_cog(AdminActions(self))
        synced = await self.tree.sync()
        print(f"Synced {len(synced)} command(s).")
        print(synced)




if __name__ == '__main__':
    cred_file = "/opt/bot/data/creds.json"
    CREDS = read_file(cred_file)

    newbot = BasedClient(creds=CREDS)
    newbot.run(CREDS["DISCORD_TOKEN"])

