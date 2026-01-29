from aiohttp import web

class WebhookServer:
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        self.app = web.Application()
        self.app.router.add_post("/webhook", self.handle)

    async def handle(self, request):
        update = await request.json()
        await self.dispatcher.dispatch(update)
        return web.Response(text="ok")

    def run(self, host="0.0.0.0", port=8080):
        web.run_app(self.app, host=host, port=port)
