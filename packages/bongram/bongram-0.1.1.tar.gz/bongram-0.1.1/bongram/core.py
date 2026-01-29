import asyncio
from typing import Callable, Dict
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message


class BongramBot:
    def __init__(self, token: str):
        self.token = token
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.handlers: Dict[str, Callable] = {}
        
    def command(self, command_name: str):
        def decorator(func: Callable):
            self.handlers[command_name] = func
            self.dp.message.register(func, Command(command_name))
            return func
        return decorator
    
    def message(self, filter_type: str = "text"):
        def decorator(func: Callable):
            handler_key = f"message_{filter_type}"
            self.handlers[handler_key] = func
            if filter_type == "text":
                self.dp.message.register(func)
            elif filter_type == "photo":
                from aiogram.filters import F
                self.dp.message.register(func, F.photo)
            return func
        return decorator
    
    async def start(self):
        print("Бот запущен и готов к работе!")
        await self.dp.start_polling(self.bot)
    
    def run(self):
        asyncio.run(self.start())
