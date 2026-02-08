import json
import logging

from bot import config
from bot.services.openai_client import OpenAIWrapper
from bot.bll.ai import AIBll
from bot.bll.finance import FinanceBll
from bot.bll.news import NewsBll
from bot.bll.misc import MiscBll
from bot.utils import chunk_message

logger = logging.getLogger(__name__)


class AvaBll:
    def __init__(self):
        self.openai = OpenAIWrapper(config.OPENAI_API_KEY)
        self.ai_bll = AIBll()
        self.news_bll = NewsBll()
        self.misc_bll = MiscBll()
        self.finance_bll = FinanceBll()
        self.gpt_schema = config.load_schema("gpt.json")
        self.function_map = {
            "get_news": self.ava_get_news,
            "send_news": self.ava_send_news,
            "send_ticker_price": self.ava_send_ticker_price,
            "get_ticker_info": self.ava_get_financial_info,
        }
        self.display_functions = ["send_news", "send_ticker_price"]
        self.requires_channel_context = []

    def call_ava(self, prompt):
        prompt_context = self.ai_bll.context_definer(content=prompt, role="user")
        context = self.gpt_schema["context"] + [prompt_context]
        tools = self.gpt_schema["tools"]
        display_objects = []

        token_sum = 0
        gpt_tune_params = {
            "temperature": 0.4,
            "model": "gpt-4o-mini",
        }
        try:
            response = self.openai.gpt_response(context=context, tools=tools, **gpt_tune_params)
            if "total_tokens" in response:
                token_sum += response["total_tokens"]
            if "error" in response:
                return {"content": response["error"], "tokens": 0}
            if response["text"] != "":
                logger.debug("IN FIRST, RESPONSE TEXT: %s", response["text"])
                for cm in chunk_message(response["text"]):
                    display_objects.append({"content": cm})
            needs_second_call = False
            second_response_model = "gpt-4o"
            if response["tool_calls"]:
                logger.debug("TOOL CALLS: %s", json.dumps(response["tool_calls"], indent=4))
                new_context = []
                for tc in response["tool_calls"]:
                    func_name = tc["function"]
                    args = tc["arguments"]
                    if func_name in self.requires_channel_context:
                        args.update({})
                    response = self.function_map[func_name](**args)
                    if "error" in response:
                        new_context.append(
                            self.ai_bll.context_definer(
                                role="system",
                                content=f"A tool call made by a previous gpt query failed to perform an action or "
                                        f"retrieve information relevant to the prompt provided. "
                                        f"Function name: '{func_name}'."
                                        f"Ignore that portion of the user prompt and answer what is remaining with "
                                        f"provided information",
                            )
                        )
                    if "display" in response:
                        display_objects.append(response["display"])
                    if "context" in response:
                        new_context.append(response["context"])
                    if "preferred_model" in response:
                        second_response_model = response["preferred_model"]
                    needs_second_call = needs_second_call or response.get("requires_followup", False)
                if needs_second_call:
                    gpt_tune_params.update({"model": second_response_model, "max_tokens": 1500})
                    response = self.openai.gpt_response(context=new_context + [prompt_context], **gpt_tune_params)
                    if "error" in response:
                        return {"content": response["error"], "tokens": 0}
                    if "total_tokens" in response:
                        token_sum += response["total_tokens"]
                    if response["text"] != "":
                        for cm in chunk_message(response["text"]):
                            display_objects.append({"content": cm})
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
            return {"display_content": display_objects, "tokens": token_sum}
        except Exception:
            logger.exception("Error in call_ava")
            display_objects.append({"content": "An issue occurred calling Ava"})
            return {"display_content": display_objects, "tokens": 0}

    def ava_send_ticker_price(self, tickers, **kwargs):
        prices, display_data = self.finance_bll.send_ticker_price(
            tickers=tickers,
            return_price=True,
        )
        ticker_string = ", ".join([f"{t}" for t in tickers]) + ": " + ", ".join([f"${t:.2f}" for t in prices])
        return {
            "display": display_data,
            "context": self.ai_bll.context_definer(
                role="system",
                content=f"most recent stock price(s) for {ticker_string} ",
            ),
            "requires_followup": False,
        }

    def ava_get_financial_info(self, tickers, **kwargs):
        fin_info = self.finance_bll.get_financial_statements(tickers=tickers, **kwargs)
        return {
            "context": self.ai_bll.context_definer(
                role="system",
                content=f"This is financial info that may be relevant to answering the user prompt:\n{json.dumps(fin_info)}",
            ),
            "requires_followup": True,
        }

    def ava_send_news(self, text="", n=4, sources: list = None, **kwargs):
        response = self.news_bll.get_news(text=text, n=n, sources=sources)
        context_text = f"relating to {text}" if text else ""
        return {
            "display": response,
            "context": self.ai_bll.context_definer(
                role="system",
                content=f"news information {context_text} has already been sent to the user by another gpt"
                        f" query tool_call for this prompt and does not need to be addressed in this followup",
            ),
            "requires_followup": True,
        }

    def ava_get_news(self, text="", n=3, sources: list = None, **kwargs):
        n_words = 300
        news_articles = self.news_bll.get_news_raw(text=text, n=n, sources=sources)
        if "error" in news_articles:
            return {"context": self.ai_bll.context_definer(role="system", content=news_articles["error"])}
        else:
            news_articles = news_articles["news"]
            news_content = [{"text": x["text"]} for x in news_articles]
            processed_news_content = []
            for x in news_content:
                words = x["text"].split(" ")
                words = words[:n_words]
                words = " ".join(words)
                processed_news_content.append(words)
            processed_news_content = "\n\n".join(processed_news_content)
            processed_news_content = f"These are news articles that may be relevant to the prompt:\n\n{processed_news_content}"
        logger.debug("sending gpt: %s", processed_news_content)
        return {
            "context": self.ai_bll.context_definer(role="system", content=processed_news_content),
            "display": {"embed": self.news_bll.create_brief_article_embed(articles=news_articles, title="Articles used by gpt")},
            "requires_followup": True,
        }
