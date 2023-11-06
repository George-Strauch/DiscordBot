import json
import os.path
import sqlite3
import traceback


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

    def write_news_notification_to_db(self, guild_id, notification_id, data_dict:dict):
        print(data_dict)
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
        print("new row", new_row)
        with sqlite3.connect(self.file_name) as con:
            c = con.cursor()
            table_exists = f'''CREATE TABLE if NOT EXISTS "news_notifications" ({self.news_data_schema })'''
            print(table_exists)
            c.execute(table_exists)

            insert = f'''INSERT INTO news_notifications VALUES {new_row}'''
            c.execute(insert)
            con.commit()


    def delete_news_notification_from_db(self, guild_id, notification_id):
        with sqlite3.connect(self.file_name) as con:
            c = con.cursor()
            c.execute(
                f'''
                DELETE FROM news_notifications WHERE
                "guild_id" is {guild_id} AND "notification_id" is {notification_id}
                '''
            )
            con.commit()


    def read_news_notification_to_db(self, guild_id):
        try:
            if not os.path.exists(self.file_name):
                return {}
            guild_notifications = {}
            with sqlite3.connect(self.file_name) as con:
                c = con.cursor()
                for row in c.execute(f'''SELECT * FROM news_notifications WHERE "guild_id" is {guild_id}'''):
                    guild_notifications[row[1]] = {
                        "news_params": {
                            "q": row[2],
                            "size": row[3],
                            "domain": row[4],
                            "category": row[5],
                            "country": row[6],
                            "no_news_update": bool(row[7]),
                            "channel": row[8]
                        },
                        "run_params": {
                            "hours": row[9]
                        },
                        "started": row[10]
                    }
            return guild_notifications
        except Exception as e:
            print(traceback.format_exc())
            print("error")
            return {}
            # todo log exception





if __name__ == '__main__':
    d = NewsNotificationDatabase("/home/george/PycharmProjects/discord_bot/src/data/news_notification.db")
    # a = '''{"1165720764486537266": {"1": {'task': "", 'news_params': {'q': 'cs2', 'size': 1, 'domain': '', 'category': '', 'channel': "", 'no_news_update': false}, 'run_params': {'hours': 12}, 'started': '2023-11-05: 15:17'}, "2": {'task': "", 'news_params': {'q': 'war', 'size': 1, 'domain': '', 'category': '', 'channel': "", 'no_news_update': false}, 'run_params': {'hours': 12}, 'started': '2023-11-05: 15:19'}}}'''.replace("'", '"')
    # print(a)
    # a = json.loads(a)
    # new_a = {}
    # for guild, guild_info in a.items():
    #     new_a[int(guild)] = {}
    #     for notif_id, notif in guild_info.items():
    #         print(int(guild))
    #         new_a[int(guild)][int(notif_id)] = notif
    #
    # d.write_news_notification_to_db(guild_id=1165720764486537266, notification_id=1, data_dict=new_a[1165720764486537266][1])
    # d.write_news_notification_to_db(guild_id=1165720764486537266, notification_id=2, data_dict=new_a[1165720764486537266][1])
    #
    #
    # x = d.read_news_notification_to_db(1165720764486537266)
    # print(x)

    # d.delete_news_notification_from_db(guild_id=1165720764486537266, notification_id=2)

    x = d.read_news_notification_to_db(1165720764486537266)
    print(x)



