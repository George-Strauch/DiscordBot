import logging
import traceback

from pytrends.request import TrendReq

logger = logging.getLogger(__name__)

bad = [
    "NFL", "National Hockey League", "NBA", "ESPN",
    "Dancing with the Stars", "Ultimate Fighting Championship",
    "UFC", "Score", "Denver Nuggets", "MLB", "Kobe Bryant",
    "Ice hockey", "World Series", "National League Championship Series",
    "The Real Housewives of Beverly Hills", "Toronto Blue Jays",
    "Britney Spears", "The NBA Finals", "LPGA",
]
bad = [x.upper() for x in bad]


def get_trending_searches():
    try:
        pt = TrendReq()
        t = pt.realtime_trending_searches()
        t = list(t["title"])
        return t
    except Exception:
        logger.exception("Error querying trending data")
        return "There was an issue querying trending data"


def interest(q):
    try:
        pt = TrendReq()
        pt.build_payload(kw_list=[q])
        iot = pt.interest_over_time()
        vals = [x[q] for i, x in iot.iterrows()]
        last_day = iot.T.columns[0]
        return vals, last_day
    except Exception:
        logger.exception("Error querying interest data")
        return "There was an issue querying trending data"
