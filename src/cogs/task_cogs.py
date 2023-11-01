# Todo
# # ------------------------ TASKS ------------------------
# @tasks.loop(hours=12)
# async def warn_data():
#     """
#     sends new data from warn act from texas every 12 hours
#     """
#     log_events("Sent warns message", LOG_FILE)
#     warns = get_new_warn_data()
#     for channel in bot_channels:
#         await channel.send(warns)
#
#
# @tasks.loop(hours=12)
# async def news_notification():
#     """
#     Sends news notifications every 12 hours
#     """
#     log_events("sending news", LOG_FILE)
#     news_data = news.get_news(size=5)
#     for channel in news_channels:
#         await channel.send(news_data)
#
#