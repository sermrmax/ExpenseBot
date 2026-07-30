import asyncio
import os

import aiosqlite
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_PATH = "expenses.db"

dp = Dispatcher()


async def init_db() -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.commit()


@dp.message(Command("start"))
async def start_handler(message: Message) -> None:
    await message.answer(
        "Привет! Я помогу учитывать расходы.\n\n"
        "Добавить расход:\n"
        "/add 350 еда\n\n"
        "Команды:\n"
        "/today — расходы за сегодня\n"
        "/month — расходы за месяц"
    )


@dp.message(Command("add"))
async def add_expense_handler(message: Message) -> None:
    if not message.text:
        return

    parts = message.text.split(maxsplit=2)

    if len(parts) < 3:
        await message.answer("Используй формат: /add 350 еда")
        return

    try:
        amount = float(parts[1].replace(",", "."))
    except ValueError:
        await message.answer("Сумма должна быть числом.")
        return

    if amount <= 0:
        await message.answer("Сумма должна быть больше нуля.")
        return

    category = parts[2].strip().lower()

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """
            INSERT INTO expenses (user_id, amount, category)
            VALUES (?, ?, ?)
            """,
            (message.from_user.id, amount, category),
        )
        await db.commit()

    await message.answer(
        f"Расход добавлен:\n"
        f"{amount:.2f} ₽ — {category}"
    )


@dp.message(Command("today"))
async def today_handler(message: Message) -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE user_id = ?
              AND DATE(created_at, 'localtime') = DATE('now', 'localtime')
            """,
            (message.from_user.id,),
        )
        row = await cursor.fetchone()

    total = row[0] if row else 0

    await message.answer(f"Сегодня потрачено: {total:.2f} ₽")


@dp.message(Command("month"))
async def month_handler(message: Message) -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """
            SELECT category, SUM(amount)
            FROM expenses
            WHERE user_id = ?
              AND STRFTIME('%Y-%m', created_at, 'localtime')
                  = STRFTIME('%Y-%m', 'now', 'localtime')
            GROUP BY category
            ORDER BY SUM(amount) DESC
            """,
            (message.from_user.id,),
        )
        rows = await cursor.fetchall()

    if not rows:
        await message.answer("В этом месяце расходов пока нет.")
        return

    total = sum(row[1] for row in rows)

    lines = ["Расходы за месяц:\n"]

    for category, amount in rows:
        lines.append(f"• {category}: {amount:.2f} ₽")

    lines.append(f"\nВсего: {total:.2f} ₽")

    await message.answer("\n".join(lines))


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("Переменная BOT_TOKEN не указана в .env")

    await init_db()

    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())