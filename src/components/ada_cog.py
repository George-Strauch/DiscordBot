import traceback
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, View
from .functions.ai import OpenAIwrapper
from .discord_bll.finance_bll import FinanceBll
from .discord_bll.news_bll import NewsBll
from .discord_bll.misc_bll import MiscBll


def function_definer(name, desc, params, required):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": desc,
            "parameters": {
                "type": "object",
                "properties": params,
                "required": required
            },
        },
    }


tools = [
    function_definer(
        name="ticker",
        desc="function to display information on upto 5 stock ticker symbols",
        params={
            "tickers": {
                "type": "array",
                "items": {
                    "type": "string",
                    "description": "Stock ticker symbol. Tickers for indexes should be prefixed with '^'"
                                   " for example, the dow jones would be: ^DJI, and the S&P 500 would be: ^SPX",
                },
                "description": "List of stock ticker symbols up to 5. Index symbols should be prefixed with '^'"
                               " for example, the dow jones: would be ^DJI or the S&P 500 would be ^SPX",
            }
        },
        required=["tickers"]
    ),

    function_definer(
        name="news",
        desc="Provides news articles",
        params={
            "topic": {
                "type": "string",
                "description": "Topic of what you want to see news articles about. If this parameter is not provided, "
                               "then the articles will be just general news",
            },
            "n": {
                "type": "integer",
                "description": "number of news articles that are wanted. this does not need to be provided and will be "
                               "5 be default",
            }
        },
        required=[]
    ),

    function_definer(
        name="invite",
        desc="Generates an invitation link to the server",
        params={},
        required=[]
    ),

]


class AdaNlp(commands.Cog):
    def __init__(self, bot: commands.Bot, ai_api_key: str="",  news_api_key: str=""):
        print("loading ada cog")
        self.bot = bot
        self.log_file = "/opt/bot/data/ada.log"
        self.open_ai = OpenAIwrapper(ai_api_key)
        self.news = NewsBll(news_api_key)
        self.misc = MiscBll()
        self.finance = FinanceBll()
        self.function_map = {
            "news": self.ada_news,
            "get_news_notifications": self.ada_get_news_updates,
            "set_news_notification": self.ada_set_news_update,
            "text_response": self.text_response,
            "generate_invite_link": self.ada_link_gen,
            "ticker": self.ada_ticker,
            "trending": self.ada_get_trending,
            "assign_roles": self.ada_assign_roles,
            "invite": self.ada_link_gen,

        }
        self.placeholder_delete = ["news", "text_response", "ticker"]


    @commands.hybrid_command(
        name="ada",
        description="Provide a natural language input for the bot to do things, powered by GPT"
    )
    @app_commands.describe(prompt="Prompt for what action you want the bot to do")
    async def ada(
            self,
            ctx: commands.Context,
            *,
            prompt: str,
    ):
        print(f"prompt is {prompt}")
        print(f"interaction is {type(ctx)}")
        await ctx.defer()
        try:
            valid, output = await self.open_ai.function_caller(
                _input=prompt,
                tools=tools,
            )
            if not valid:
                if "`" in output:
                    output = {
                        "name": "text_response",
                        "arguments": {
                            "text": f"{output}"
                        }
                    }
                else:
                    output = {
                        "name": "text_response",
                        "arguments": {
                            "text": f"```{output}```"
                        }
                    }
            await self.call_function(
                call=output,
                ctx=ctx,
            )
        except Exception as e:
            print(e.args)
            print(traceback.format_exc())
            message = "somthing went wrong with ada :["
            await ctx.reply(content=message)


    async def call_function(self, call, ctx):
        name = call["name"].split(".")[0]
        params = call["arguments"]
        params["ctx"] = ctx
        func = self.function_map[name]
        print(f"name: {name}")
        print(f"params: {params}")
        print(f"func: {func}")
        await func(**params)


    async def text_response(self, text, ctx):
        await ctx.reply(text)


    async def ada_ticker(self, ctx, **kwargs):
        # tickers = kwargs["tickers"].split(" ")
        data = self.finance.get_ticker_info(
            tickers=kwargs["tickers"],
            # period=kwargs.get("period", )
        )
        await ctx.reply(**data)

    async def ada_image_gen(self):
        pass

    async def ada_news(self):
        pass

    async def ada_set_news_update(self):
        pass

    async def ada_get_news_updates(self):
        pass

    async def ada_get_trending(self):
        pass

    async def ada_link_gen(self, ctx):
        try:
            response = await self.misc.generate_invite_link(ctx.channel)
            await ctx.reply(
                **response
            )
        except Exception as ex:
            # todo log
            print(ex.args)

    async def ada_assign_roles(self):
        pass






