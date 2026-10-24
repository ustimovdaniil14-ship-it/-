import asyncio
import os

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

API_URL = "https://bot.catup.lol"
BOT_TOKEN = "1780243817:2gsgc9BoKqw1sntV-TEM-gYqfPVw9dj6fB9"

TEXT = """💫 <b>Пожертвования</b> 💫

Кто захотел, тот и задонатил ⭐

Отправляешь ты ему 👉 @Imabout 💙"""

session = AiohttpSession(api=TelegramAPIServer.from_base(API_URL))
bot = Bot(BOT_TOKEN, session=session)
dp = Dispatcher()


def donate_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"⭐ {n}", callback_data=f"don:{n}") for n in (1, 5, 10)],
            [InlineKeyboardButton(text=f"⭐ {n}", callback_data=f"don:{n}") for n in (50, 100)],
        ]
    )


@dp.message(CommandStart())
async def start(m: Message):
    await m.answer(TEXT, reply_markup=donate_kb(), parse_mode=ParseMode.HTML)


@dp.callback_query(F.data.startswith("don:"))
async def donate(c: CallbackQuery):
    amount = int(c.data.split(":")[1])
    await bot.send_invoice(
        chat_id=c.from_user.id,
        title="Пожертвование",
        description="Спасибо за поддержку 💙",
        payload=f"donate_{amount}",
        currency="XTR",
        prices=[LabeledPrice(label="Пожертвование", amount=amount)],
    )
    await c.answer()


@dp.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery):
    await q.answer(ok=True)


@dp.message(F.successful_payment)
async def paid(m: Message):
    await m.answer("Спасибо за донат! 💙")


async def health(request):
    return web.Response(text="ok")


async def start_web():
    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    await web.TCPSite(runner, "0.0.0.0", port).start()


async def main():
    await start_web()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
