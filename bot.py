import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv


load_dotenv()

bot_token = os.getenv("BOT_TOKEN")

dispatcher = Dispatcher()


@dispatcher.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        "Привет! 👋\n"
        "Я бот для учёта расходов.\n\n"
        "Скоро здесь можно будет добавлять и смотреть расходы."
    )


async def main() -> None:
    if not bot_token:
        raise RuntimeError(
            "Не найден BOT_TOKEN. Проверь файл .env."
        )

    bot = Bot(token=bot_token)

    print("Бот запущен. Для остановки нажми Ctrl+C.")

    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())