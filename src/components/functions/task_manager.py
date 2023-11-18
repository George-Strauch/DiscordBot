


class TaskManager:
    _self = None
    news_notifications = {}

    def __new__(cls):
        if cls._self is None:
            cls._self = super().__new__(cls)
        return cls._self

    def __init__(self):
        pass

    def get_news_notifications(self):
        pass
