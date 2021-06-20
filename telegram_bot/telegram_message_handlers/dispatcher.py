from aiogram import (
    Bot,
    Dispatcher,
)


def register_dispatcher(telegram_bot: Bot) -> Dispatcher:
    from telegram_bot.telegram_message_handlers import (
        start_handler,
        current_music_inline_query
    )

    dispatcher = Dispatcher(telegram_bot)

    dispatcher.register_message_handler(start_handler, commands=['start'])
    dispatcher.register_inline_handler(current_music_inline_query)

    return dispatcher
