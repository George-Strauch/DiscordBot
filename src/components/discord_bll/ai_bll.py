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
            "ticker_financials": self.finance.get_financial_statements
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


    def call_ava(self, prompt):
        """
        we do the continuous function calling here
        :param prompt:
        :return:
        """

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


    def create_agent(
            self,
    ):


        finance_fields = ['dates', 'Free Cash Flow', 'Repayment Of Debt', 'Issuance Of Debt', 'Issuance Of Capital Stock',
             'Capital Expenditure', 'Interest Paid Supplemental Data', 'Income Tax Paid Supplemental Data',
             'End Cash Position', 'Beginning Cash Position', 'Effect Of Exchange Rate Changes', 'Changes In Cash',
             'Financing Cash Flow', 'Cash Flow From Continuing Financing Activities', 'Net Other Financing Charges',
             'Proceeds From Stock Option Exercised', 'Net Common Stock Issuance', 'Common Stock Issuance',
             'Net Issuance Payments Of Debt', 'Net Long Term Debt Issuance', 'Long Term Debt Payments',
             'Long Term Debt Issuance', 'Investing Cash Flow', 'Cash Flow From Continuing Investing Activities',
             'Net Other Investing Changes', 'Net Investment Purchase And Sale', 'Sale Of Investment',
             'Purchase Of Investment', 'Net Business Purchase And Sale', 'Sale Of Business', 'Purchase Of Business',
             'Net Intangibles Purchase And Sale', 'Sale Of Intangibles', 'Purchase Of Intangibles',
             'Net PPE Purchase And Sale', 'Purchase Of PPE', 'Capital Expenditure Reported', 'Operating Cash Flow',
             'Cash Flow From Continuing Operating Activities', 'Change In Working Capital',
             'Change In Other Working Capital', 'Change In Other Current Liabilities', 'Change In Other Current Assets',
             'Change In Payables And Accrued Expense', 'Change In Prepaid Assets', 'Change In Inventory',
             'Change In Receivables', 'Changes In Account Receivables', 'Other Non Cash Items',
             'Stock Based Compensation', 'Asset Impairment Charge', 'Depreciation Amortization Depletion',
             'Depreciation And Amortization', 'Depreciation', 'Operating Gains Losses',
             'Net Foreign Currency Exchange Gain Loss', 'Gain Loss On Sale Of PPE',
             'Net Income From Continuing Operations', 'earnings_dates'] + ['dates', 'Ordinary Shares Number', 'Share Issued', 'Net Debt', 'Total Debt', 'Tangible Book Value', 'Invested Capital', 'Working Capital', 'Net Tangible Assets', 'Capital Lease Obligations', 'Common Stock Equity', 'Total Capitalization', 'Total Equity Gross Minority Interest', 'Minority Interest', 'Stockholders Equity', 'Gains Losses Not Affecting Retained Earnings', 'Other Equity Adjustments', 'Retained Earnings', 'Additional Paid In Capital', 'Capital Stock', 'Common Stock', 'Preferred Stock', 'Total Liabilities Net Minority Interest', 'Total Non Current Liabilities Net Minority Interest', 'Other Non Current Liabilities', 'Preferred Securities Outside Stock Equity', 'Non Current Accrued Expenses', 'Non Current Deferred Liabilities', 'Non Current Deferred Revenue', 'Non Current Deferred Taxes Liabilities', 'Long Term Debt And Capital Lease Obligation', 'Long Term Capital Lease Obligation', 'Long Term Debt', 'Long Term Provisions', 'Current Liabilities', 'Other Current Liabilities', 'Current Deferred Liabilities', 'Current Deferred Revenue', 'Current Debt And Capital Lease Obligation', 'Current Capital Lease Obligation', 'Current Debt', 'Other Current Borrowings', 'Current Provisions', 'Payables And Accrued Expenses', 'Current Accrued Expenses', 'Interest Payable', 'Payables', 'Total Tax Payable', 'Accounts Payable', 'Total Assets', 'Total Non Current Assets', 'Other Non Current Assets', 'Non Current Note Receivables', 'Goodwill And Other Intangible Assets', 'Other Intangible Assets', 'Goodwill', 'Net PPE', 'Accumulated Depreciation', 'Gross PPE', 'Leases', 'Construction In Progress', 'Other Properties', 'Machinery Furniture Equipment', 'Land And Improvements', 'Properties', 'Current Assets', 'Other Current Assets', 'Restricted Cash', 'Prepaid Assets', 'Inventory', 'Other Inventories', 'Finished Goods', 'Work In Process', 'Raw Materials', 'Receivables', 'Accounts Receivable', 'Cash Cash Equivalents And Short Term Investments', 'Other Short Term Investments', 'Cash And Cash Equivalents']
        finance_fields = ", ".join(finance_fields)

        tools = [
            self.function_definer(
                name="get_ticker_info",
                desc="function to provide GPT with a info about yearly financial reports of one or more publicly traded"
                     " companies including balance sheet, income statement, cashflow etc",
                params={
                    "tickers": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "Stock ticker symbol",
                        },
                        "description": "List of stock ticker symbols up to 5",
                    },
                    "fields": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": f"field that is required to be provided. most be one of: {finance_fields}"
                        },
                        "description": "List of stock ticker symbols up to 5",
                    }
                },
                required=["tickers"]
            ),


            self.function_definer(
                name="send_ticker_price",
                desc="function to send price and price graph for one or multiple stock tickers directly to the user in "
                     "Discord",
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

            self.function_definer(
                name="get_news",
                desc="returns truncated data from news articles used to respond to prompts about current events. "
                     "this should only be called to when GPT needs information about a current event to respond to a"
                     "prompt, if the user only wants the news articles, then 'send_news' should be used",
                params={
                    "topic": {
                        "type": "string",
                        "description": "Topic of what you want to see news articles about. If this parameter is not"
                                       " provided or is set to '', then the articles will be just general news",
                    },
                    "n": {
                        "type": "integer",
                        "description": "number of news articles that are wanted. This does not need to be provided"
                                       " and will be 3 be default. This number should be conservative to save tokens",
                    },
                    "category": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "Category of news articles to get. "
                                           "This should be left blank or not provided for 'all categories'"
                                           "Each element must be one of: 'business', 'crime', 'domestic', 'education',"
                                           "'entertainment', 'environment', 'food', 'other', 'politics', 'science', "
                                           "'sports', 'technology', 'top', 'tourism', 'world', 'health' ",
                        },
                        "description": "List of news categories **MAX 5**. 'top should usually be provided in this list",
                    },
                    # "country": {
                    #     "type": "array",
                    #     "items": {
                    #         "type": "string",
                    #         "description": "country code. should be one of 'us', 'gb', 'au', 'de', 'jp', 'fr', "
                    #                        " 'il' 'cn', 'it",
                    #     },
                    #     "description": "countries of origin for the news articles **MAX 5**."
                    #                    "By default, this should usually be 'us', only if news originating "
                    #                    "from somewhere else is specifically requested should that change. "
                    #                    "ex: 'what is going on in israel' should be topic='israel' and country=['us'] "
                    #                    "but 'show me news from japan' should be topic='' and country=['il']"
                    #                    "Language will always be english for any country provided, "
                    #                    "so that should not be a consideration",
                    # }
                },
                required=[]
            ),

            self.function_definer(
                name="send_news",
                desc="sends news articles directly to the user in discord",
                params={
                    "topic": {
                        "type": "string",
                        "description": "same as get_news",
                    },
                    "n": {
                        "type": "integer",
                        "description": "same as get_news",
                    },
                    "category": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "same as get_news",
                        },
                        "description": "same as get_news",
                    },
                    # "country": {
                    #     "type": "array",
                    #     "items": {
                    #         "type": "string",
                    #         "description": "ISO 3166 country code",
                    #     },
                    #     "description": "same as get_news",
                    # }
                },
                required=[]
            )
        ]
        agent = self.openai.create_agent(
            instructions="You are an intelligent bot for a discord server responsible answering questions"
                         " and for determining what functions need to be called to answer them."
                         " functions that start with 'send' are designed to send formatted information to the user,"
                         " while functions that start with 'get' are for you to retrieve data that you need."
                         " If answering a question requires a calculation, do not verbosely explain a walkthrough"
                         " of the steps unless asked. only provide the result of the calculation",
            name="AVA",
            tools=tools,
            model="gpt-4-1106-preview",
        )
        print(agent)





