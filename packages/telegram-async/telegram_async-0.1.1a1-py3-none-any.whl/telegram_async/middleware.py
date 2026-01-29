class MiddlewareManager:
    def __init__(self):
        self.middlewares = []

    def add(self, func):
        self.middlewares.append(func)

    async def run(self, ctx, handler):
        index = 0
        async def call(i):
            if i < len(self.middlewares):
                await self.middlewares[i](ctx, lambda: call(i+1))
            else:
                await handler(ctx)
        await call(index)
