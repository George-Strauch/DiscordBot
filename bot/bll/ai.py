import json
import logging

from bot import config
from bot.services.openai_client import OpenAIWrapper
from bot.utils import theme_colors

logger = logging.getLogger(__name__)


class AIBll:
    def __init__(self):
        self.openai = OpenAIWrapper(config.OPENAI_API_KEY)
        self.gpt_schema = config.load_schema("gpt.json")

    @staticmethod
    def context_definer(content, role="system"):
        return {"role": role, "content": content}

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
                    "required": required,
                },
            },
        }

    def price(self, run):
        price_map = {
            "input_cost": 0.03 / 1000,
            "output_cost": 0.06 / 1000,
        }
        return price_map["input_cost"] * run["input_tokens"] + price_map["output_cost"] * run["output_tokens"]

    def ask_gpt(self, prompt: str, additional_context: list = None, model: str = "gpt-4o", **kwargs) -> dict:
        try:
            context = additional_context + [self.context_definer(prompt, "user")]
            response = self.openai.gpt_response(context=context, model=model, **kwargs)
            if "error" in response:
                pass
            return response
        except Exception as ex:
            message = "An error occurred querying OpenAi"
            if len(ex.args) > 0:
                message = ex.args[0]
            return {"error": message}

    def image(self, prompt: str, **kwargs) -> dict:
        try:
            response = self.openai.image_generator(prompt=prompt, **kwargs)
            if "error" in response:
                pass
            return response
        except Exception as ex:
            message = "An error occurred generating an image with OpenAi"
            if len(ex.args) > 0:
                message = ex.args[0]
            return {"error": message}

    def create_agent(self, **kwargs):
        agent = self.openai.create_agent(**kwargs)
        return agent
