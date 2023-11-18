import json
from ..functions.ai import OpenAIwrapper
from ..utils import log_events, theme_colors, read_file
from .trends_bll import get_trending_searches


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





