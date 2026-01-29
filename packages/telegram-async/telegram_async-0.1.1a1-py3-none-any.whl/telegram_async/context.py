from typing import Any

class Context:
    def __init__(self, client, update: dict, role: Any, session=None):
        self.client = client
        self.update = update
        self.message = update.get("message") or {}
        self.chat_id = self.message.get("chat", {}).get("id")
        self.user_id = self.message.get("from", {}).get("id")
        self.text = self.message.get("text", "")
        self.role = role
        self.session = session or {}

    async def reply(self, text: str):
        if self.chat_id:
            await self.client.send_message(self.chat_id, text)
