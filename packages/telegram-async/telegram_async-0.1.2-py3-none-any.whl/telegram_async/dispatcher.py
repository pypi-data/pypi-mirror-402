from .context import Context
from .roles import Roles

class Dispatcher:
    def __init__(self, client, role_provider, session_store=None):
        self.client = client
        self.role_provider = role_provider
        self.session_store = session_store or {}
        self.command_handlers = {}
        self.message_handlers = []
        self.middlewares = []

    def register(self, func):
        if hasattr(func, "__command__"):
            role = getattr(func, "__required_role__", Role.GUEST)
            self.command_handlers[func.__command__] = (func, role)

        if hasattr(func, "__on_message__"):
            self.message_handlers.append(func)

        if hasattr(func, "__middleware__"):
            self.middlewares.append(func)

    async def _run_middlewares(self, ctx, handler):
        async def call(index):
            if index < len(self.middlewares):
                await self.middlewares[index](ctx, lambda: call(index + 1))
            else:
                await handler(ctx)
        await call(0)

    async def dispatch(self, update: dict):
        msg = update.get("message")
        if not msg:
            return

        user_id = msg.get("from", {}).get("id")
        role = self.role_provider(user_id)
        session = self.session_store.get(user_id, {})

        ctx = Context(self.client, update, role, session)

        text = msg.get("text", "")

        if text.startswith("/"):
            command = text.split()[0]
            if command in self.command_handlers:
                handler, min_role = self.command_handlers[command]
                if role >= min_role:
                    await self._run_middlewares(ctx, handler)
                return

        for handler in self.message_handlers:
            filt = getattr(handler, "__filter__", {})
            if filt.get("text_contains") and filt["text_contains"] not in text:
                continue
            if filt.get("from_user") and filt["from_user"] != user_id:
                continue
            if filt.get("chat_id") and filt["chat_id"] != ctx.chat_id:
                continue
            await self._run_middlewares(ctx, handler)
