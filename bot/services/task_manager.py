class TaskManager:
    _self = None
    all_notifications = {}

    def __new__(cls):
        if cls._self is None:
            cls._self = super().__new__(cls)
        return cls._self

    def __init__(self):
        pass

    def get_notifications(self, key):
        return self.all_notifications.get(key, None)

    def set_notification(self, key, obj):
        self.all_notifications[key] = obj
        return self.all_notifications
