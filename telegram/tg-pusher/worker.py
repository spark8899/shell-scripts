import asyncio
import random
from aiogram import Bot

class WorkerBot:
    """Telegram bot worker with rate limiting."""

    def __init__(self, bot: Bot, min_interval: int, jitter: int):
        self.bot = bot
        self.min_interval = min_interval
        self.jitter = jitter
        self.lock = asyncio.Lock()

    async def send(self, chat_id: int, text: str):
        """Send a message with rate limiting."""
        async with self.lock:
            await asyncio.sleep(
                self.min_interval + random.randint(0, self.jitter)
            )
            await self.bot.send_message(
                chat_id,
                text,
                parse_mode="Markdown"
            )
