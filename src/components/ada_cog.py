import asyncio
import json
import traceback
import discord
from discord.ext import commands
from discord import app_commands
from .utils import log_events
from .functions.ai import OpenAIwrapper
from .discord_bll.finance_bll import FinanceBll
from .discord_bll.news_bll import NewsBll
from .discord_bll.misc_bll import MiscBll
from .discord_bll.trends_bll import get_trending_searches
from .utils import chunk_message


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

    function_definer(
        name="generate_image",
        desc="Generates an image given a simple prompt",
        params={
            "prompt": {
                "type": "string",
                "description": "a description of the image to be generated",
            }
        },
        required=["prompt"]
    ),

    function_definer(
        name="news_summery",
        desc="a summery of the current news. this method will get a list of news articles, about a certain topic " 
             "if the parameter 'topic' is provided, then ask a LLM to summarize the news articles once it has that "
             "list. This should only be called instead of the 'news' function if confident the user wants a summery "
             "instead of the news articles themselves, if unsure, then the default behavior should be to just "
             "get 'news'",
        params={
            "topic": {
                "type": "string",
                "description": "topic of the news coverage if any",
            }
        },
        required=["prompt"]
    ),

    function_definer(
        name="trending",
        desc="Summarizes current google trending searches. this method will first get a list of trending search terms, "
             "then use an LLM to summarize them",
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
        self.news_bll = NewsBll(news_api_key)
        self.misc_bll = MiscBll()
        self.finance_bll = FinanceBll()
        self.function_map = {
            "news": self.ada_news,
            "get_news_notifications": self.ada_get_news_updates,
            "set_news_notification": self.ada_set_news_update,
            "text_response": self.text_response,
            "generate_invite_link": self.ada_link_gen,
            "ticker": self.ada_ticker,
            # "trending": self.ada_get_trending,
            "assign_roles": self.ada_assign_roles,
            "invite": self.ada_link_gen,
            "generate_image": self.ada_image_gen,
            "news_summery": self.ada_news_summery,
            "trending": self.ada_google_trends_summery
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
                original_prompt=prompt
            )
        except Exception as e:
            print(e.args)
            print(traceback.format_exc())
            message = "somthing went wrong with ada :["
            await ctx.reply(content=message)


    async def call_function(self, call, ctx, original_prompt):
        name = call["name"].split(".")[0]
        params = call["arguments"]
        params["ctx"] = ctx
        params["original_prompt"] = original_prompt
        func = self.function_map[name]
        print(f"name: {name}")
        print(f"params: {params}")
        print(f"func: {func}")
        await func(**params)


    async def text_response(self, text, ctx):
        await ctx.reply(text)


    async def ada_ticker(self, ctx, **kwargs):
        # tickers = kwargs["tickers"].split(" ")
        data = self.finance_bll.send_ticker_price(
            tickers=kwargs["tickers"],
            # period=kwargs.get("period", )
        )
        await ctx.reply(**data)


    async def ada_image_gen(self, ctx, prompt, **kwargs):
        try:
            reply = self.open_ai.image_generator(prompt)
            await ctx.reply(content=reply)
        except Exception as ex:
            await ctx.reply(content="OpenAI rejected the prompt")


    async def ada_news(
            self,
            ctx,
            topic="",
            n=5,
            source="",
            category="",
            country="us,au,gb",
            **kwargs
    ):
        try:
            response = self.news_bll.get_news(
                topic=topic,
                n=n,
                source=source,
                category=category,
                country=country
            )
            await ctx.reply(**response)
        except Exception as e:
            await ctx.reply(content="Something went wrong getting news :[")
            log_events(str(e.args), self.log_file)


    async def ada_news_summery(self, ctx, topic="", original_prompt="", **kwargs):
        news_articles = self.news_bll.get_full_raw_news(
            topic=topic,
        )
        if len(news_articles) == 0:
            await ctx.reply(f"Ada cannot find any news articles about {topic} :[")
            return
        news_content = [
            {
                # "title": x["title"],
                # "content": x["content"].replace(r"\u2014", "-").replace(r"\u2019", "'")[:500]+"..."
                "content": x["content"].replace(r"\u2014", "-").replace(r"\u2019", "'")
                if x["content"] is not None else x["description"].replace(r"\u2014", "-").replace(r"\u2019", "'")
            }
            for x in news_articles
        ]

        news_str = ""
        for x in news_content:
            # news_str = news_str + f"\n\n{x['title']}\n{x['content']}"
            news_str = news_str + f"\n\n{x['content']}"


        message = (f"use the following news articles to answer this prompt as briefly as possible"
                   f" and leave out data that does not seem important since these articles may be poorly filtered: "
                   f"'{original_prompt}'\n{news_str}")
        print(message)
        gpt_reply = await self.open_ai.general_gpt_query(
            _input=message,
            # model="gpt-3.5-turbo-1106"
        )
        gpt_reply = chunk_message(gpt_reply)
        for x in gpt_reply:
            await ctx.reply(x)
            await asyncio.sleep(1)
        await ctx.reply(
            embed=self.news_bll.create_brief_article_embed(
                articles=news_articles,
                title="Summery was generated using data from news sources"
            )
        )


    async def ada_set_news_update(self, **kwargs):
        pass

    async def ada_get_news_updates(self, **kwargs):
        pass

    async def ada_get_trending(self, **kwargs):
        pass

    async def ada_google_trends_summery(self, ctx, **kwargs):
        trends = get_trending_searches()
        trends = "\n".join(trends)

        message = (f"Summarize this list of trending search terms in a way that clearly explains what "
                   f"event or idea each of these is referring to. "
                   f"Each line is a set of related search terms about the same general event or idea seperated "
                   f"by a comma. "
                   f"Each bullet point in the summary should be formatted as follows: "
                   f"<very brief condensed text of a search term>: <explanation of event or idea>"
                   f"each bullet point should belong under a super category such as sports, politics, music etc... "
                   f"example: \n ```\n"
                   f"**Sports**\n"
                   f" - 'MLB': ...\n"
                   f"**Technology**\n"
                   f" - 'twitter': ...\n```\n"
                   f"Only use at max the 25 most important and noteworthy search terms, and do not "
                   f"repeat bullet-points under different categories. Basic sporting events are lower priority "
                   # f"the summary should have them in order of importance."
                   f"\n\n{trends}")
        print(message)
        gpt_reply = await self.open_ai.general_gpt_query(
            _input=message,
            # model="gpt-3.5-turbo-1106"
        )
        gpt_reply = chunk_message(gpt_reply)
        for x in gpt_reply:
            await ctx.reply(x)
            await asyncio.sleep(1)


    async def ada_link_gen(self, ctx, **kwargs):
        try:
            response = await self.misc_bll.generate_invite_link(ctx.channel)
            await ctx.reply(
                **response
            )
        except Exception as ex:
            # todo log
            print(ex.args)

    async def ada_assign_roles(self):
        pass






