import asyncio
import os

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
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

TEXT = """🟡 <b>Пожертвования</b> 🟡

Кто захотел, тот и задонатил ⭐

Отправляешь ты ему 👉 @Imabout 💛"""

session = AiohttpSession(api=TelegramAPIServer.from_base(API_URL))
bot = Bot(BOT_TOKEN, session=session)
dp = Dispatcher(storage=MemoryStorage())


class Donate(StatesGroup):
    waiting_amount = State()


def donate_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⭐ 50", callback_data="don:50"),
                InlineKeyboardButton(text="⭐ 100", callback_data="don:100"),
                InlineKeyboardButton(text="⭐ 500", callback_data="don:500"),
            ],
            [InlineKeyboardButton(text="✏️ Своё число", callback_data="don:custom")],
        ]
    )


async def send_donate_invoice(chat_id: int, amount: int):
    await bot.send_invoice(
        chat_id=chat_id,
        title=f"⭐ Пожертвование {amount}",
        description="Спасибо за поддержку 💛",
        payload=f"donate_{amount}",
        currency="XTR",
        prices=[LabeledPrice(label="Пожертвование", amount=amount)],
    )


@dp.message(CommandStart())
async def start(m: Message, state: FSMContext):
    await state.clear()
    await m.answer(TEXT, reply_markup=donate_kb(), parse_mode=ParseMode.HTML)


@dp.callback_query(F.data == "don:custom")
async def custom(c: CallbackQuery, state: FSMContext):
    await state.set_state(Donate.waiting_amount)
    await c.message.answer(
        "✏️ Напиши любое число звёзд, например <b>250</b> 💛",
        parse_mode=ParseMode.HTML,
    )
    await c.answer()


@dp.callback_query(F.data.startswith("don:"))
async def preset(c: CallbackQuery, state: FSMContext):
    await state.clear()
    amount = int(c.data.split(":")[1])
    await send_donate_invoice(c.from_user.id, amount)
    await c.answer()


@dp.message(Donate.waiting_amount, F.text)
async def got_amount(m: Message, state: FSMContext):
    text = m.text.strip()
    if not text.isdigit() or int(text) < 1 or len(text) > 12:
        await m.answer("🟡 Напиши целое число больше нуля, например 250")
        return
    await state.clear()
    try:
        await send_donate_invoice(m.from_user.id, int(text))
    except Exception:
        await m.answer("🟡 Не получилось выставить счёт на такую сумму, попробуй другое число")


@dp.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery):
    await q.answer(ok=True)


@dp.message(F.successful_payment)
async def paid(m: Message):
    await m.answer("Спасибо за донат! 💛")


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
