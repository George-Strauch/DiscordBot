import json
import logging
import requests
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class News:
    source_map = {
        "AP": "https://apnews.com",
        "FOX": "https://www.foxnews.com",
        "REUTERS": "https://www.reuters.com",
        "BBC": "https://www.bbc.com",
        "NPR": "https://www.npr.org",
        "CNN": "https://www.cnn.com",
        "SKYNEWS": "https://news.sky.com",
    }

    def __init__(self, apikey=""):
        self.api_key = apikey
        self.base_url = "https://api.worldnewsapi.com/"

    def source_to_url(self, source):
        return self.source_map.get(source.upper(), "")

    def build_url(self, action, **kwargs):
        params = {"api-key": self.api_key}
        for k, v in kwargs.items():
            param = k.replace("_", "-")
            params[param] = v
        return f"{self.base_url}{action}?{urlencode(params)}"

    def verify_response(self, response: requests.Response):
        logger.debug("News API status: %d", response.status_code)
        if response.status_code // 100 != 2:
            logger.warning("News API error: %s", response.text)
            return False, {"error": "Non 200 status code from API"}
        try:
            data = response.json()
            news_articles = {"articles": data["news"]}
            return True, news_articles
        except Exception:
            return False, {"error": "Failed to read API response as json"}

    def search_news(self, sources: list = None, **kwargs):
        params = {
            "language": "en",
            "source-countries": "us",
            "sort": "publish-time",
            "sort-direction": "DESC",
            "text": "breaking news",
        }
        if sources:
            sources = [x.upper() for x in sources]
            sources = [self.source_to_url(x) for x in sources]
            sources = [x for x in sources if x != ""]
            params["news-sources"] = ",".join(sources)
        params.update(kwargs)
        url = self.build_url(action="search-news", **params)
        logger.debug("News API URL: %s", url)
        response = requests.get(url=url)
        success, data = self.verify_response(response=response)
        logger.debug("News API success: %s", success)
        return data
