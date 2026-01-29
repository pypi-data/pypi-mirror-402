import time
from collections import defaultdict
from asyncio import Lock

class Throttle:
    def __init__(self):
        # user_id -> [timestamp1, timestamp2, ...]
        self.calls = defaultdict(list)
        self.lock = Lock()

    async def check(self, user_id: int, rate: int = 5, per: int = 10) -> bool:
        """Zwraca True jeśli użytkownik może wykonać akcję"""
        now = time.time()
        async with self.lock:
            timestamps = self.calls[user_id]
            # usuwamy stare
            self.calls[user_id] = [t for t in timestamps if now - t < per]
            if len(self.calls[user_id]) >= rate:
                return False
            self.calls[user_id].append(now)
            return True
