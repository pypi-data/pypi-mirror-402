
class SessionStorage:
    def __init__(self):
        self.store = {}

    def get(self, user_id):
        return self.store.get(user_id, {})

    def set(self, user_id, data):
        self.store[user_id] = data
