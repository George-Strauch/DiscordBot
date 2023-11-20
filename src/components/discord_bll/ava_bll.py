import asyncio
import datetime
import pandas as pd
import json
import traceback
from ..utils import log_events
from ..functions.ai import OpenAIwrapper
from ..discord_bll.finance_bll import FinanceBll
from ..discord_bll.news_bll import NewsBll
from ..discord_bll.misc_bll import MiscBll
from ..discord_bll.trends_bll import get_trending_searches
from ..utils import chunk_message, read_file


class AvaBll:
    """
    wraps most other functions from bll files such that they can be called
    """
    def __init__(self):
        self.log_file = "/opt/bot/data/ava.log"
        cred_file = "/opt/bot/data/creds.json"
        self.openai = OpenAIwrapper(read_file(cred_file)["OPENAI_TOKEN"])
        self.news_bll = NewsBll()
        self.misc_bll = MiscBll()
        self.finance_bll = FinanceBll()
        self.ava_agent = "asst_dTTu2Wvl8eouRdagRf6Lluun"
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

    def call_ava(self, prompt):
        """
        we do the continuous function calling here
        :param prompt:
        :return:
        """
        display_objects = []
        try:
            thread = self.openai.create_thread()
            message = self.openai.create_message(
                thread_id=thread.id,
                content=prompt
            )
            runner = self.openai.create_run(
                thread_id=thread.id,
                agent_id=self.ava_agent,
                instructions=f"provide the user with the information they are requesting,"
                             f" the current date is {pd.to_datetime(str(datetime.datetime.now())).strftime('%Y-%m-%d')}"
            )
            while True:
                runner = self.openai.wait_for_run(
                    run_id=runner.id,
                    thread_id=thread.id,
                    dt=2
                )
                if runner.status == "requires_action":
                    tool = runner.required_action
                    funcs_to_call = tool.submit_tool_outputs.tool_calls
                    tool_outputs = []
                    for f in funcs_to_call:
                        print(f)
                        func_call_id = f.id
                        func_name = f.function.name
                        args = json.loads(f.function.arguments)
                        print(f"Function: {func_name}\nParameters:\n{json.dumps(args)}")
                        # todo
                        # if func_name in self.needs_channel_context:
                        #     args.update({})
                        output = self.function_map[func_name](**args)
                        if func_name in self.display_functions:
                            display_objects.append(output)
                        else:
                            tool_outputs.append(
                                {
                                    "tool_call_id": func_call_id,
                                    "output": str(output)
                                }
                            )
                    if len(tool_outputs) > 0:
                        runner = self.openai.submit_tool_to_output(
                            run_id=runner.id,
                            thread_id=thread.id,
                            tool_outputs=tool_outputs
                        )
                        tool_outputs = []
                    else:
                        print(f"returning: \n{display_objects}")
                        return display_objects

                elif runner.status in ["expired", "cancelling", "cancelled", "failed", "expired", "completed"]:
                    if runner.status == "completed":
                        print(f"runner status: {runner.status}")
                        # if display is empty
                        messages = self.openai.retrieve_messages(thread_id=thread.id)
                        response = messages.data[0].content[0].text.value
                        print(f"response: {response}")
                        if len(response) > 1996:
                            response = response[:1996]
                        if '`' not in response:
                            response = f"```{response}```"
                        display_objects.append(
                            {
                                "content": response
                            }
                        )
                    else:
                        display_objects.append(
                            {
                                "content": f"Ava encountered an issues :[ agent runner status: {runner.status})"
                            }
                        )
                    break
            print(f"returning: {display_objects}")
            return display_objects
        except Exception as ex:
            # todo remove args from response
            print("error")
            print(ex.args)
            display_objects.append(
                {
                    "content": f"Exception occurred in Ava execution: {ex.args}"
                }
            )
            return display_objects

    def ava_send_ticker_price(self, tickers, **kwargs):
        return self.finance_bll.send_ticker_price(
            tickers=tickers,
            **kwargs
        )

    def ava_get_financial_info(self, tickers, **kwargs):
        return self.finance_bll.get_financial_statements(
            tickers=tickers,
            **kwargs
        )

    def ava_send_image(self, prompt, **kwargs):
        return self.openai.image_generator(prompt, **kwargs)


    def ava_send_news(
            self,
            topic="",
            n=4,
            source: str = "",
            category: str = "",
            country: str = "us",
            **kwargs
    ):
        response = self.news_bll.get_news(
            topic=topic,
            n=n,
            source=source,
            category=category,
            country=country
        )
        return response

    def ava_get_news(
            self,
            topic="",
            n=3,
            source: str = "",
            category: str = "",
            country: str = "us",
            **kwargs
    ):
        news_articles = self.news_bll.get_full_raw_news(
            topic=topic,
            n=n,
            source=source,
            category=category,
            country=country
        )
        if len(news_articles) == 0:
            return {
                "error": "No news articles were retrieved"
            }
        news_content = [
            {
                # "title": x["title"],
                "content": x["content"].replace(r"\u2014", "-").replace(r"\u2019", "'")
                if x["content"] is not None else x["description"].replace(r"\u2014", "-").replace(r"\u2019", "'")
            }
            for x in news_articles
        ]

        refined_news_content = []
        for x in news_content:
            # todo make sure that is enough characters, perhapse break by space
            # words = x["content"].split(" ")
            refined_news_content.append(x["content"][:2000])
        print(json.dumps(refined_news_content, indent=4))
        refined_news_content = "\n\n".join(refined_news_content)
        print(f"sending gpt:\n{refined_news_content}")
        return refined_news_content


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
