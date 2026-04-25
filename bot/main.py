"""Точка входа бота."""
from __future__ import annotations

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from bot import progress
from bot.handlers import router


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    token = os.environ["BOT_TG_TOKEN"]

    await progress.init_db()

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=None),
    )
    dp = Dispatcher()
    dp.include_router(router)

    me = await bot.get_me()
    logging.info("Bot started: @%s (%s)", me.username, me.id)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
