from aiogram.types import Message

from telegram_bot.models import (
    TemplateModel,
    TemplatesList,
    UserModel,
)
from telegram_bot.telegram_message_handlers import start_handler


async def unlink_spotify_handler(message: Message):
    """Command /unlink_spotify handler."""
    user_telegram_id = message.from_user.id
    user = await UserModel.query.where(UserModel.telegram_id == user_telegram_id).gino.first()

    if not user:
        return await start_handler(message)

    if not user.spotify_access_token:
        response_text = await TemplateModel.find_and_render_template(TemplatesList.UNLINK_SPOTIFY_NOT_LINKED_MESSAGE)
        return await message.answer(response_text)

    await user.update(
        spotify_access_token=None,
        spotify_refresh_token=None,
        spotify_authorized_at=None,
        spotify_expiration_token_at=None,
    ).apply()

    response_text = await TemplateModel.find_and_render_template(TemplatesList.UNLINK_SPOTIFY_SUCCESS_MESSAGE)
    await message.answer(response_text)
