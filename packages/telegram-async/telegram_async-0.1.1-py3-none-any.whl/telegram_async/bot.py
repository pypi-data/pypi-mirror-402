import re
from .client import TelegramClient
from .dispatcher import Dispatcher
from .server import WebhookServer
from .roles import Role
from .logger import logger
from .decorators import command as command_deco, on_message, middleware, role_required

class Bot:
    @staticmethod
    def validate_token(token: str) -> bool:
        """Validate Telegram Bot API token format.
        
        Args:
            token: The Telegram Bot API token to validate
            
        Returns:
            bool: True if token is valid, False otherwise
        """
        if not token or not isinstance(token, str):
            return False
        # Telegram bot tokens are in format: 1234567890:ABCdefGHIjklmNOPqrstUVWXYZ
        pattern = r'^\d{9,11}:[A-Za-z0-9_-]{35}$'
        return bool(re.match(pattern, token))

    def __init__(self, token, role_provider=None, session_store=None):
        if not self.validate_token(token):
            raise ValueError("Invalid Telegram Bot API token format. "
                           "Token should be in format: 1234567890:ABCdefGHIjklmNOPqrstUVWXYZ")
        self.client = TelegramClient(token)
        self.role_provider = role_provider or (lambda _: Role.GUEST)
        self.dispatcher = Dispatcher(self.client, self.role_provider, session_store=session_store)

    def command(self, name: str):
        def wrapper(func):
            func = command_deco(name)(func)
            self.dispatcher.register(func)
            logger.info(f"Registered command {name}")
            return func
        return wrapper

    def on_message(self, **filters):
        def wrapper(func):
            func = on_message(**filters)(func)
            self.dispatcher.register(func)
            return func
        return wrapper

    def middleware(self):
        def wrapper(func):
            func = middleware()(func)
            self.dispatcher.register(func)
            return func
        return wrapper

    def require(self, role: Role):
        def wrapper(func):
            func = role_required(role)(func)
            return func
        return wrapper

    def run_webhook(self, host="0.0.0.0", port=8080):
        server = WebhookServer(self.dispatcher)
        server.run(host, port)

    async def run_polling(self):
        import asyncio
        from aiohttp import ClientSession
        offset = None
        while True:
            async with ClientSession() as session:
                params = {"timeout": 30}
                if offset:
                    params["offset"] = offset
                async with session.get(f"{self.client.base}/getUpdates", params=params) as r:
                    updates = await r.json()
                    for update in updates.get("result", []):
                        await self.dispatcher.dispatch(update)
                        offset = update["update_id"] + 1
            await asyncio.sleep(1)
