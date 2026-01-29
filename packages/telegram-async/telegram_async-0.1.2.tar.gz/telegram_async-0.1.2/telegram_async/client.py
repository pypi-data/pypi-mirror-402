import aiohttp

class TelegramClient:
    def __init__(self, token: str):
        self.base = f"https://api.telegram.org/bot{token}"

    async def send_message(self, chat_id: int, text: str):
        async with aiohttp.ClientSession() as s:
            await s.post(
                f"{self.base}/sendMessage",
                json={"chat_id": chat_id, "text": text}
            )

    async def answer_callback(self, callback_id: str, text: str = None):
        async with aiohttp.ClientSession() as s:
            await s.post(
                f"{self.base}/answerCallbackQuery",
                json={"callback_query_id": callback_id, "text": text or ""}
            )
