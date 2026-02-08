import os
import json
import logging

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
WORLD_NEWS_API_KEY = os.environ["WORLD_NEWS_API_KEY"]
BOT_DATA_DIR = os.environ.get("BOT_DATA_DIR", "/opt/bot/data")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
COMMAND_PREFIX = os.environ.get("COMMAND_PREFIX", "!")

DB_PATH = os.path.join(BOT_DATA_DIR, "news_notification.db")


def load_json_config(filename, default=None):
    if default is None:
        default = {}
    path = os.path.join(BOT_DATA_DIR, filename)
    if not os.path.exists(path):
        return default
    with open(path, "r") as fp:
        return json.loads(fp.read())


def load_schema(name):
    schema_dir = os.path.join(os.path.dirname(__file__), "schemas")
    path = os.path.join(schema_dir, name)
    with open(path, "r") as fp:
        return json.loads(fp.read())


def setup_logging():
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
