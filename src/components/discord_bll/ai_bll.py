import json
from ..functions.ai import OpenAIwrapper
from ..utils import log_events, theme_colors, read_file
from .trends_bll import get_trending_searches
from .finance_bll import FinanceBll


class AIBll:
    def __init__(self):
        cred_file = "/opt/bot/data/creds.json"
        self.openai = OpenAIwrapper(read_file(cred_file)["OPENAI_TOKEN"])
        self.log_file = "/opt/bot/data/ai.log"
        self.context = [
            self.context_definer(
                content="You are a intelligent assistant for a discord application. "
                        "Responses to direct requests should not be in any kind of template format"
            )
        ]
        self.finance = FinanceBll()
        self.function_map = {
            # "news": self.ada_news,
            # "get_news_notifications": self.ada_get_news_updates,
            # "set_news_notification": self.ada_set_news_update,
            # "text_response": self.text_response,
            # "generate_invite_link": self.ada_link_gen,
            # "ticker": self.ada_ticker,
            # # "trending": self.ada_get_trending,
            # "assign_roles": self.ada_assign_roles,
            # "invite": self.ada_link_gen,
            # "generate_image": self.ada_image_gen,
            # "news_summery": self.ada_news_summery,
            "ticker_financials": self.finance.get_yearly_financial_statements
        }


    @staticmethod
    def context_definer(content, role="system"):
        return {
            "role": role,
            "content": content
        }


    @staticmethod
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

    def price(self, run):
        # todo by model
        price_map = {
            "input_cost": 0.03/1000,
            "output_cost": 0.06/1000
        }
        return price_map["input_cost"]*run["input_tokens"] + price_map["output_cost"]*run["output_tokens"]

    def ask_gpt(
            self,
            prompt: str,
            additional_context: list = None,
            model: str = "gpt-4",
            **kwargs
    ) -> dict:
        """
        query Open ai
        :param prompt: question or request of model
        :param additional_context: list of context objects
        :param model: gpt model
        :return: dict {"content": "", "input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        """
        try:
            context = self.context + additional_context+[self.context_definer(prompt, "user")]
            response = self.openai.gpt_response(
                context=context,
                model=model,
                **kwargs
            )
            if "error" in response:
                # todo
                pass
            return response
        except Exception as ex:
            message = "An error occurred querying OpenAi"
            if len(ex.args) > 0:
                message = ex.args[0]
            return {"error": message}


    def gpt_functions(
            self,
    ) -> dict:
        """
        :return:
        """
        pass


    def image(
            self,
            prompt: str,
            **kwargs
    ) -> dict:
        """
        Generate an image with OpenAi
        :param prompt: question or request of model
        :return: dict {"content": "", "input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        """
        try:
            response = self.openai.image_generator(
                prompt=prompt,
                **kwargs
            )
            if "error" in response:
                # todo
                pass
            return response
        except Exception as ex:
            message = "An error occurred generating an image with OpenAi"
            if len(ex.args) > 0:
                message = ex.args[0]
            return {"error": message}

    def summerize_trending(
            self,
            # model: str = "gpt-4",
            model: str = "gpt-4-1106-preview",
            **kwargs
    ) -> dict:
        """
        summarizes google trends data
        :param model: gpt model
        :return: dict {"content": "", "input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        """
        try:

            trends = get_trending_searches()
            trends = "\n".join(trends)
            print(trends)
            formatting_instructions = (
                f"Summarize the trending google search terms and their events and ideas. "
                f"Each line represents a trending search term provided in multiple ways people may query it "
                f"seperated by a comma. "
                f"Each bullet point in the summary should be formatted as follows: "
                f"<very brief condensed text of a search term>: <explanation of event or idea>"
                f"each bullet point should belong under a super category such as sports, politics, music etc... "
                f"example: \n ```\n"
                f"**Sports**\n"
                # todo specify an exmaple output
                f" - 'MLB': ...\n"
                f"**Technology**\n"
                f" - 'twitter': ...\n```\n"
                f"Only use at max the 20 most important and noteworthy search terms, and do not "
                f"repeat bullet-points under different categories. Basic sports events should be considered lower "
                f"priority and not as important since they are very common."
                f"It is important not to speculate events happening if that is not clearly indicated, for example, "
                f"somthing relating to guns and a tragic shooting may be the result of renewed discussion of a past"
                f"tragedy rather than evidence of a recent one."
            )
            context = self.context + [
                self.context_definer(content=f"google trending searches are: \n{trends}"),
                self.context_definer(content=formatting_instructions, role="user"),
            ]
            print(json.dumps(context, indent=4))
            response = self.openai.gpt_response(
                context=context,
                model=model,
                temperature=0.2,
                frequency_penalty=.5,
                **kwargs
            )
            if "error" in response:
                # todo
                pass
            return response
        except Exception as ex:
            message = "An error occurred querying OpenAi"
            if len(ex.args) > 0:
                message = ex.args[0]
            return {"error": message}


    def call_eve(self, prompt):
        """
        we do the continuous function calling here
        :param prompt:
        :return:
        """
        # todo agent will eventually be created separately
        # agent = self.openai.create_agent(
        #     instructions="You are a bot responsible answering questions and for determining what "
        #                  "functions need to be called to answer them",
        #     name="EVE",
        #     tools=[
        #         self.function_definer(
        #             name="ticker_financials",
        #             desc="function to get information financial statement information about a stock",
        #             params={
        #                 "tickers": {
        #                     "type": "array",
        #                     "items": {
        #                         "type": "string",
        #                         "description": "Stock ticker symbol",
        #                     },
        #                     "description": "List of stock ticker symbols up to 5",
        #                 }
        #             },
        #             required=["tickers"]
        #         )
        #     ],
        #     model="gpt-4-1106-preview",
        # )
        # agent_id = agent.id
        agent_id = "asst_tW3PwDnWWF3Qq1yzkQEzgqYw"

        thread = self.openai.create_thread()
        message = self.openai.create_message(
            thread_id=thread.id,
            content=prompt
        )
        runner = self.openai.create_run(
            thread_id=thread.id,
            agent_id=agent_id,
            instructions="provide the user with the information they are requesting"
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
                    output = self.function_map[func_name](**args)
                    tool_outputs.append(
                        {
                            "tool_call_id": func_call_id,
                            "output": str(output)
                        }
                    )
                runner = self.openai.submit_tool_to_output(
                    run_id=runner.id,
                    thread_id=thread.id,
                    tool_outputs=tool_outputs
                )
            elif runner.status in ["expired", "cancelling", "cancelled", "failed", "expired", "completed"]:
                print(runner.status)
                messages = self.openai.retrieve_messages(thread_id=thread.id)
                print(messages)
                print(messages.data[0].content[0].text.value)
                break







    def assistant_sandbox(
            self,
            # prompt: str,
            # additional_context: list = None,
            # model: str = "gpt-4",
            # **kwargs
    ) -> dict:
        """
        query Open ai
        :param prompt: question or request of model
        :param additional_context: list of context objects
        :param model: gpt model
        :return: dict {"content": "", "input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        """
        try:
            self.openai.thread_starter_test()
        except Exception as ex:
            message = "An error occurred querying OpenAi"
            if len(ex.args) > 0:
                message = ex.args[0]
            return {"error": message}





