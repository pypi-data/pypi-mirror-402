import asyncio
from typing import Callable

class Scheduler:
    def __init__(self):
        self.tasks = []

    def every(self, seconds: int, func: Callable):
        async def wrapper():
            while True:
                await func()
                await asyncio.sleep(seconds)
        self.tasks.append(wrapper)

    async def start(self):
        await asyncio.gather(*(task() for task in self.tasks))
