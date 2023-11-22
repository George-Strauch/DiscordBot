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
        self.gpt_schema = read_file("../../gpt.json")


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


    def create_agent(
            self,
            **kwargs
    ):
        agent = self.openai.create_agent(
            **kwargs
        )
        return agent





