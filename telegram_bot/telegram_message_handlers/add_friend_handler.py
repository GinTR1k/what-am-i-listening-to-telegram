from aiogram.types import Message

from telegram_bot.models import (
    TemplateModel,
    TemplatesList,
    UserModel,
)
from telegram_bot.telegram_message_handlers import start_handler


async def add_friend_handler(message: Message):
    """Command /add_friend handler."""
    user_telegram_id = message.from_user.id
    user = await UserModel.query.where(UserModel.telegram_id == user_telegram_id).gino.first()

    if not user:
        return await start_handler(message)

    response_text = await TemplateModel.find_and_render_template(TemplatesList.ADD_FRIEND_ABOUT_MESSAGE)
    await message.answer(response_text)
