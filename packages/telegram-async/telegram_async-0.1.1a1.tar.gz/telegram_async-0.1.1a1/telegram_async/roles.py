from enum import IntEnum
class Roles:
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"

    def __init__(self):
        self.user_roles = {}

    def set_role(self, user_id: int, role: str):
        self.user_roles[user_id] = role

    def get_role(self, user_id: int):
        return self.user_roles.get(user_id, self.USER)
