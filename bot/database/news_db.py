import logging
import os
import sqlite3
import traceback

logger = logging.getLogger(__name__)


class NewsNotificationDatabase:
    def __init__(self, file_name):
        self.file_name = file_name
        self.news_data_schema = (
            "guild_id INTEGER,"
            "notification_id INTEGER,"
            "q TEXT,"
            "size INTEGER,"
            "domain TEXT,"
            "category TEXT,"
            "country TEXT,"
            "no_news_update BOOLEAN,"
            "channel INTEGER,"
            "hours INTEGER,"
            "started TEXT"
        )

    def write_news_notification_to_db(self, guild_id, notification_id, data_dict: dict):
        new_row = (
            guild_id,
            notification_id,
            data_dict["news_params"].get("q", ""),
            data_dict["news_params"].get("size", 1),
            data_dict["news_params"].get("domain", ""),
            data_dict["news_params"].get("category", ""),
            data_dict["news_params"].get("country", ""),
            data_dict["news_params"].get("no_news_update", True),
            data_dict["news_params"]["channel"].id,
            data_dict["run_params"].get("hours", 9),
            data_dict["started"],
        )
        with sqlite3.connect(self.file_name) as con:
            c = con.cursor()
            table_exists = f'CREATE TABLE if NOT EXISTS "news_notifications" ({self.news_data_schema})'
            c.execute(table_exists)
            c.execute('INSERT INTO news_notifications VALUES (?,?,?,?,?,?,?,?,?,?,?)', new_row)
            con.commit()

    def delete_news_notification_from_db(self, guild_id, notification_id):
        with sqlite3.connect(self.file_name) as con:
            c = con.cursor()
            c.execute(
                'DELETE FROM news_notifications WHERE guild_id = ? AND notification_id = ?',
                (guild_id, notification_id)
            )
            con.commit()

    def read_news_notification_to_db(self, guild_id):
        try:
            if not os.path.exists(self.file_name):
                return {}
            guild_notifications = {}
            with sqlite3.connect(self.file_name) as con:
                c = con.cursor()
                for row in c.execute('SELECT * FROM news_notifications WHERE guild_id = ?', (guild_id,)):
                    guild_notifications[row[1]] = {
                        "news_params": {
                            "q": row[2],
                            "size": row[3],
                            "domain": row[4],
                            "category": row[5],
                            "country": row[6],
                            "no_news_update": bool(row[7]),
                            "channel": row[8],
                        },
                        "run_params": {
                            "hours": row[9],
                        },
                        "started": row[10],
                    }
            return guild_notifications
        except Exception:
            logger.exception("Error reading news notifications from db")
            return {}
