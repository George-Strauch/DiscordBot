import asyncio
import datetime
import pandas as pd
import json
import traceback
from ..utils import log_events
from ..functions.ai import OpenAIwrapper
from .ai_bll import AIBll
from ..discord_bll.finance_bll import FinanceBll
from ..discord_bll.news_bll import NewsBll
from ..discord_bll.misc_bll import MiscBll
from ..utils import chunk_message, read_file


class AvaBll:
    """
    wraps most other functions from bll files such that they can be called
    """
    def __init__(self):
        self.log_file = "/opt/bot/data/ava.log"
        cred_file = "/opt/bot/data/creds.json"
        self.openai = OpenAIwrapper(read_file(cred_file)["OPENAI_TOKEN"])
        self.ai_bll = AIBll()
        self.news_bll = NewsBll()
        self.misc_bll = MiscBll()
        self.finance_bll = FinanceBll()
        self.gpt_schema = read_file("gpt.json")
        print(self.gpt_schema)
        self.function_map = {
            "get_news": self.ava_get_news,
            "send_news": self.ava_send_news,
            "send_ticker_price": self.ava_send_ticker_price,
            "get_ticker_info": self.ava_get_financial_info,
            # "send_invite": self.ava,
            # "get_news_notifications": self.ada_get_news_updates,
            # "set_news_notification": self.ada_set_news_update,
            # "ticker_price": self.ada_ticker,
            # "trending": self.ada_get_trending,
            # "assign_roles": self.ada_assign_roles,
            # "invite": self.ada_link_gen,
            # "generate_image": self.ada_image_gen,
            # "news_summery": self.ada_news_summery,
            # "trending": self.ada_google_trends_summery
        }
        self.display_functions = ["send_news", "send_ticker_price"]
        self.requires_channel_context = []

    def call_ava(
            self,
            prompt
    ):
        """
        we do the continuous function calling here
        :param prompt:
        :return:
        """
        prompt_context = self.ai_bll.context_definer(content=prompt)
        context = self.gpt_schema["context"] + [prompt_context]
        tools = self.gpt_schema["tools"]
        display_objects = []

        token_sum = 0
        gpt_tune_params = {
            # "frequency_penalty": 1.5,
            # "presence_penalty": 1.5,
            "temperature": 0.4,
            # "model": "gpt-4-1106-preview",
            # "model": "gpt-4",
            "model": "gpt-3.5-turbo-1106"

        }
        try:
            response = self.openai.gpt_response(
                context=context,
                tools=tools,
                **gpt_tune_params
            )
            if "total_tokens" in response:
                token_sum += response["total_tokens"]*0.3
            if "error" in response:
                return {
                    "content": response["error"],
                    "tokens": 0
                }
            if response["text"] != "":
                print(f"IN FIRST, RESPONSE TEXT: {response['text']}")
                for cm in chunk_message(response["text"]):
                    display_objects.append(
                        {
                            "content": cm
                        }
                    )
            needs_second_call = False
            if response["tool_calls"]:
                new_context = []
                for tc in response["tool_calls"]:
                    func_name = tc["function"]
                    args = tc["arguments"]
                    if func_name in self.requires_channel_context:
                        # todo
                        args.update({})
                    response = self.function_map[func_name](**args)
                    if "display" in response:
                        display_objects.append(response["display"])
                    if "context" in response:
                        # then this is a function that returns a context object ment for gpt
                        needs_second_call = True
                        new_context.append(response["context"])
                if needs_second_call:
                    gpt_tune_params.update(
                        {
                            # "model": "gpt-3.5-turbo-1106"
                            "model": "gpt-4-1106-preview",
                            "max_tokens": 1500
                            # "model": "gpt-4",
                        }
                    )
                    response = self.openai.gpt_response(
                        context=new_context + [prompt_context],
                        **gpt_tune_params
                    )
                    if "error" in response:
                        return {
                            "content": response["error"],
                            "tokens": 0
                        }
                    if "total_tokens" in response:
                        token_sum += response["total_tokens"]
                    if response["text"] != "":
                        print(f"IN SECOND, RESPONSE TEXT: {response['text']}")
                        for cm in chunk_message(response["text"]):
                            display_objects.append(
                                {
                                    "content": cm
                                }
                            )
                    else:
                        display_objects.append({"content": "Issue retrieving response to followup gpt call"})
            with_embeds = []
            without_embeds = []
            for x in display_objects:
                if "embed" in x or "embeds" in x:
                    with_embeds.append(x)
                else:
                    without_embeds.append(x)
            display_objects = without_embeds + with_embeds
            final_response = {
                "display_content": display_objects,
                "tokens": token_sum
            }
            print("----------------")
            print(final_response)
            print("----------------")
            return final_response
        except Exception as ex:
            # todo remove args from response
            import traceback
            print(traceback.format_exc())
            print("error")
            print(ex.args)
            display_objects.append(
                {
                    "content": f"An issue occurred calling Ava: {ex.args}"
                }
            )
            final_response = {
                "display_content": display_objects,
                "tokens": 0
            }
            print("----------------")
            print(final_response)
            print("----------------")
            return final_response


    def ava_send_ticker_price(self, tickers, **kwargs):
        return {
            "display": self.finance_bll.send_ticker_price(
                tickers=tickers,
                **kwargs
            )
        }


    def ava_get_financial_info(self, tickers, **kwargs):
        fin_info = self.finance_bll.get_financial_statements(
            tickers=tickers,
            **kwargs
        )
        # todo: make cheaper by manually defining list of acceptable params here
        return {
            "context": self.ai_bll.context_definer(
                role="system",
                content=f"This is financial info that may be relevant to answering the user prompt:\n{json.dumps(fin_info)}"
            )
        }


    def ava_send_image(self, prompt, **kwargs):
        return self.openai.image_generator(prompt, **kwargs)


    def ava_send_news(
            self,
            text="",
            n=4,
            sources: list = None,
            **kwargs
    ):
        response = self.news_bll.get_news(
            text=text,
            n=n,
            sources=sources
        )
        return {
            "display": response
        }

    def ava_get_news(
            self,
            text="",
            n=3,
            sources: list = None,
            **kwargs
    ):
        n_words = 300
        news_articles = self.news_bll.get_news_raw(
            text=text,
            n=n,
            sources=sources
        )
        processed_news_content = ""
        if "error" in news_articles:
            return {
                "context": self.ai_bll.context_definer(role="system", content=news_articles["error"]),
            }
        else:
            news_articles = news_articles["news"]
            news_content = [
                {
                    # "title": x["title"],
                    "text": x["text"]
                }
                for x in news_articles
            ]
            processed_news_content = []
            for x in news_content:
                # refined_news_content.append(x["text"][:2000])
                words = x["text"].split(" ")
                words = words[:n_words]
                words = " ".join(words)
                print(f"WORDS: {words}")
                processed_news_content.append(words)

            processed_news_content = "\n\n".join(processed_news_content)
            processed_news_content = f"These are news articles that may be relevant to the prompt:\n\n{processed_news_content}"
        print(f"sending gpt:\n{processed_news_content}")
        return {
            "context": self.ai_bll.context_definer(role="system", content=processed_news_content),
            "display": {"embed": self.news_bll.create_brief_article_embed(articles=news_articles, title="Articles used by gpt")}
        }


    async def ada_set_news_update(self, **kwargs):
        pass

    async def ada_get_news_updates(self, **kwargs):
        pass

    async def ada_get_trending(self, **kwargs):
        pass

    async def ada_google_trends_summery(self, ctx, **kwargs):
        pass


    # async def ada_link_gen(self, **kwargs):
    #     return {
    #         "content": await self.misc_bll.generate_invite_link(channel)
    #     }


    async def ada_assign_roles(self):
        pass
