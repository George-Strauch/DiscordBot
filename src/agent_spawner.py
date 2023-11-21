from components.discord_bll.ai_bll import AIBll

bll = AIBll()


def make_ava():

    finance_fields = ['dates', 'Free Cash Flow', 'Repayment Of Debt', 'Issuance Of Debt', 'Issuance Of Capital Stock',
                      'Capital Expenditure', 'Interest Paid Supplemental Data', 'Income Tax Paid Supplemental Data',
                      'End Cash Position', 'Beginning Cash Position', 'Effect Of Exchange Rate Changes',
                      'Changes In Cash',
                      'Financing Cash Flow', 'Cash Flow From Continuing Financing Activities',
                      'Net Other Financing Charges',
                      'Proceeds From Stock Option Exercised', 'Net Common Stock Issuance', 'Common Stock Issuance',
                      'Net Issuance Payments Of Debt', 'Net Long Term Debt Issuance', 'Long Term Debt Payments',
                      'Long Term Debt Issuance', 'Investing Cash Flow',
                      'Cash Flow From Continuing Investing Activities',
                      'Net Other Investing Changes', 'Net Investment Purchase And Sale', 'Sale Of Investment',
                      'Purchase Of Investment', 'Net Business Purchase And Sale', 'Sale Of Business',
                      'Purchase Of Business',
                      'Net Intangibles Purchase And Sale', 'Sale Of Intangibles', 'Purchase Of Intangibles',
                      'Net PPE Purchase And Sale', 'Purchase Of PPE', 'Capital Expenditure Reported',
                      'Operating Cash Flow',
                      'Cash Flow From Continuing Operating Activities', 'Change In Working Capital',
                      'Change In Other Working Capital', 'Change In Other Current Liabilities',
                      'Change In Other Current Assets',
                      'Change In Payables And Accrued Expense', 'Change In Prepaid Assets', 'Change In Inventory',
                      'Change In Receivables', 'Changes In Account Receivables', 'Other Non Cash Items',
                      'Stock Based Compensation', 'Asset Impairment Charge', 'Depreciation Amortization Depletion',
                      'Depreciation And Amortization', 'Depreciation', 'Operating Gains Losses',
                      'Net Foreign Currency Exchange Gain Loss', 'Gain Loss On Sale Of PPE',
                      'Net Income From Continuing Operations', 'earnings_dates'] + [
                         'dates', 'Ordinary Shares Number', 'Share Issued', 'Net Debt', 'Total Debt',
                         'Tangible Book Value', 'Invested Capital', 'Working Capital', 'Net Tangible Assets',
                         'Capital Lease Obligations', 'Common Stock Equity', 'Total Capitalization',
                         'Total Equity Gross Minority Interest', 'Minority Interest', 'Stockholders Equity',
                         'Gains Losses Not Affecting Retained Earnings', 'Other Equity Adjustments',
                         'Retained Earnings', 'Additional Paid In Capital', 'Capital Stock', 'Common Stock',
                         'Preferred Stock', 'Total Liabilities Net Minority Interest',
                         'Total Non Current Liabilities Net Minority Interest', 'Other Non Current Liabilities',
                         'Preferred Securities Outside Stock Equity', 'Non Current Accrued Expenses',
                         'Non Current Deferred Liabilities', 'Non Current Deferred Revenue',
                         'Non Current Deferred Taxes Liabilities', 'Long Term Debt And Capital Lease Obligation',
                         'Long Term Capital Lease Obligation', 'Long Term Debt', 'Long Term Provisions',
                         'Current Liabilities', 'Other Current Liabilities', 'Current Deferred Liabilities',
                         'Current Deferred Revenue', 'Current Debt And Capital Lease Obligation',
                         'Current Capital Lease Obligation', 'Current Debt', 'Other Current Borrowings',
                         'Current Provisions', 'Payables And Accrued Expenses', 'Current Accrued Expenses',
                         'Interest Payable', 'Payables', 'Total Tax Payable', 'Accounts Payable', 'Total Assets',
                         'Total Non Current Assets', 'Other Non Current Assets', 'Non Current Note Receivables',
                         'Goodwill And Other Intangible Assets', 'Other Intangible Assets', 'Goodwill', 'Net PPE',
                         'Accumulated Depreciation', 'Gross PPE', 'Leases', 'Construction In Progress',
                         'Other Properties', 'Machinery Furniture Equipment', 'Land And Improvements', 'Properties',
                         'Current Assets', 'Other Current Assets', 'Restricted Cash', 'Prepaid Assets', 'Inventory',
                         'Other Inventories', 'Finished Goods', 'Work In Process', 'Raw Materials', 'Receivables',
                         'Accounts Receivable', 'Cash Cash Equivalents And Short Term Investments',
                         'Other Short Term Investments', 'Cash And Cash Equivalents'
                     ]
    finance_fields = [f'"{x}"' for x in finance_fields]
    finance_fields = ", ".join(finance_fields)



    tools = [
        bll.function_definer(
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
                        "description": f"field that is required to be provided."
                                       f" Must be one of the following options: {finance_fields}"
                    },
                    "description": "List of stock ticker symbols up to 5. "
                                   "All elements must be from this list provided",
                }
            },
            required=["tickers"]
        ),

        bll.function_definer(
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

        bll.function_definer(
            name="get_news",
            desc="returns truncated data from news articles used to respond to prompts about current events. "
                 "this should only be called to when GPT needs information about a current event to respond to a"
                 "prompt, if the user only wants the news articles, then 'send_news' should be used",
            params={
                "text": {
                    "type": "string",
                    "description": "Short query of what you want to see news articles about."
                                   " This Should only contain key words that would be present in the article.",
                },
                "n": {
                    "type": "integer",
                    "description": "number of news articles that are wanted. This does not need to be provided"
                                   " and will be 3 be default. This number should be conservative to save tokens",
                },
                "sources": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "description": "News source. Must be one of: 'AP', 'FOX', 'REUTERS', 'BBC', 'NPR', 'CNN', "
                                       " 'SKYNEWS'",
                    },
                    "description": "Source for news articles. Each element must be in the one of the options provided."
                                   " This parameter does not always need to be provided. "
                                   " If the text query is about something relating to politics, business, or international"
                                   " / world event, then this list should contain ['AP', 'REUTERS' and 'NPR']"
                                   " unless otherwise requested."
                }
            },
            required=[]
        ),

        bll.function_definer(
            name="send_news",
            desc="sends news articles directly to the user in discord",
            params={
                "text": {
                    "type": "string",
                    "description": "same as get_news",
                },
                "n": {
                    "type": "integer",
                    "description": "same as get_news but this should be 5 unless otherwise stated",
                },
                "sources": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "description": "same as get_news",
                    },
                    "description": "same as get_news",
                }
            },
            required=[]
        )
    ]

    agent = bll.create_agent(
        instructions="You are an intelligent bot for a discord server responsible answering questions"
                     " and for determining what functions need to be called to answer them."
                     " functions that start with 'send' are designed to send formatted information to the user,"
                     " while functions that start with 'get' are for you to retrieve data that you need."
                     " If answering a question requires a calculation, do not verbosely explain a walkthrough"
                     " of the steps unless asked. only provide the result of the calculation. Only use markdown "
                     "for code blocks, do not use formatting commands like /frac{}{} or /text",
        name="AVA",
        tools=tools,
        model="gpt-4-1106-preview",
    )
    return agent


if __name__ == '__main__':
    agent = make_ava()
    print(agent)
