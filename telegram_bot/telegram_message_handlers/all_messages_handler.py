from aiogram.types import (
    ContentType,
    Message,
)
from sqlalchemy import and_

from telegram_bot.models import (
    FriendModel,
    TemplateModel,
    TemplatesList,
    UserModel,
)
from telegram_bot.telegram_message_handlers import start_handler


async def all_messages_handler(message: Message):
    """Handler on all uncatched messages."""
    if message.from_user.id == message.bot.id or message.via_bot:
        return

    user_telegram_id = message.from_user.id
    user = await UserModel.query.where(UserModel.telegram_id == user_telegram_id).gino.first()

    if not user:
        return await start_handler(message)

    if message.content_type != ContentType.TEXT:
        response_text = await TemplateModel.find_and_render_template(TemplatesList.ALL_MESSAGES_NOT_UNDERSTAND_MESSAGE)
        return await message.answer(response_text)

    if message.forward_from is None:
        response_text = await TemplateModel.find_and_render_template(
            TemplatesList.ALL_MESSAGES_WAITING_FOR_A_FORWARD_MESSAGE_MESSAGE,
        )
        return await message.answer(response_text)

    friend_telegram_id = message.forward_from.id

    if friend_telegram_id == user_telegram_id:
        return

    friend = await UserModel.query.where(UserModel.telegram_id == friend_telegram_id).gino.first()

    if not friend or not friend.spotify_access_token:
        response_text = await TemplateModel.find_and_render_template(TemplatesList.ADD_FRIEND_NOT_FOUND_MESSAGE)
        return await message.answer(response_text)

    friendship = await FriendModel.query.where(
        and_(
            FriendModel.user_uuid == user.uuid,
            FriendModel.friend_uuid == friend.uuid,
        )
    ).gino.first()

    if not friendship:
        await FriendModel(
            user_uuid=user.uuid,
            friend_uuid=friend.uuid,
        ).create()

    response_text = await TemplateModel.find_and_render_template(TemplatesList.ADD_FRIEND_SUCCESS_MESSAGE)
    return await message.answer(response_text)
