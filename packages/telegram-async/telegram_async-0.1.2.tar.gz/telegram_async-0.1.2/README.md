# telegram-async

**Asynchronous Telegram bot framework** z middleware, throttlingiem, callbackami i pseudo-przyciskami.

Framework ułatwia tworzenie botów Telegram w Pythonie z wykorzystaniem `asyncio` i `aiohttp`. Wspiera:

- Komendy `/start`, `/help`, `/confirm`  
- Throttling wiadomości użytkownika  
- Middleware logger (Rich)  
- Callbacki i pseudo-przyciski (`/ok`)  
- Background task działający w pętli co X sekund  

## Instalacja

```bash
pip install telegram-async
