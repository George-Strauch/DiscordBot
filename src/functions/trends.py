from pytrends.request import TrendReq
import traceback

# todo wrap in a class
# todo ignore all of these https://en.wikipedia.org/wiki/List_of_professional_sports_teams_in_the_United_States_and_Canada
# todo, put this in a config file somewhere so it can be updated real time
bad = [
    "NFL",
    "National Hockey League",
    "NBA",
    "ESPN",
    "Dancing with the Stars",
    "Ultimate Fighting Championship",
    "UFC",
    "Score",
    "Denver Nuggets",
    "MLB",
    "Kobe Bryant",
    "Ice hockey",
    "World Series",
    "National League Championship Series",
    "The Real Housewives of Beverly Hills",
    "Toronto Blue Jays",
    "Britney Spears",
    "The NBA Finals",
    "LPGA",

]
bad = [x.upper() for x in bad]


def get_trending_searches():
    """
    gets current trending searches
    """
    try:
        pt = TrendReq()
        t = pt.realtime_trending_searches()
        titles = [x for x in t['title']]
        titles = [x[:60] for x in titles if not any([a.upper() in bad for a in x.split(", ")])]
        titles = "\n\n".join(titles)
        return titles if len(titles) > 0 else "All trending items were filtered as sports or irrelevant"
    except Exception as e:
        print(e.args)
        # todo catch specific exception
        print(traceback.format_exc(e))
        return "There was an issue querying trending data"


def interest(q):
    """
    WIP: I want to generate a line chart of interest over time for a search query
    # todo get dates correct
    :param q: search term
    :return: ?
    """
    try:
        pt = TrendReq()
        timeframe = "today 1-m"
        print(timeframe)
        pt.build_payload(kw_list=[q])
        iot = pt.interest_over_time()
        vals = [x[q] for i, x in iot.iterrows()]
        last_day = iot.T.columns[0]
        return vals, last_day
    except Exception as e:
        print(e.args)
        # todo catch specific exception
        print(traceback.format_exc(e))
        return "There was an issue querying trending data"