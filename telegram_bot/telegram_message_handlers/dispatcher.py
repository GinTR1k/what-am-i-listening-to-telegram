from aiogram import (
    Bot,
    Dispatcher,
)


def register_dispatcher(telegram_bot: Bot) -> Dispatcher:
    from telegram_bot.telegram_message_handlers import (
        start_handler,
        current_music_inline_query,
        unlink_spotify_handler,
        add_friend_handler,
        all_messages_handler,
    )

    dispatcher = Dispatcher(telegram_bot)

    dispatcher.register_message_handler(start_handler, commands=['start'])
    dispatcher.register_message_handler(unlink_spotify_handler, commands=['unlink_spotify'])
    dispatcher.register_message_handler(add_friend_handler, commands=['add_friend'])
    dispatcher.register_message_handler(all_messages_handler)

    dispatcher.register_inline_handler(current_music_inline_query)

    return dispatcher
