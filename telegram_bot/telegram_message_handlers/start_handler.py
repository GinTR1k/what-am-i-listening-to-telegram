import asyncpg
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from telegram_bot.models import (
    TemplateModel,
    TemplatesList,
    UserModel,
)
from telegram_bot.spotify_client import SpotifyClient


async def start_handler(message: Message):
    """Command /start handler."""
    user_telegram_id = message.from_user.id

    try:
        user = await UserModel(telegram_id=user_telegram_id).create()
        new_registration = True
    except asyncpg.UniqueViolationError:
        user = await UserModel.query.where(UserModel.telegram_id == user_telegram_id).gino.first()
        new_registration = False

    if new_registration:
        return await send_welcome_message_to_new_user(user, message)
    elif user.spotify_access_token is None:
        return await send_welcome_message_to_new_user(user, message)
    return await send_welcome_all_ok_message(message)


async def send_welcome_message_to_new_user(user: UserModel, message: Message):
    response_text = await TemplateModel.find_and_render_template(TemplatesList.WELCOME_MESSAGE)
    button_text = await TemplateModel.find_and_render_template(TemplatesList.WELCOME_SPOTIFY_AUTHORIZE_LINE_BUTTON)

    spotify_api = SpotifyClient.init()
    spotify_authorization_url = spotify_api.build_authorization_url(state=user.uuid)

    inline_keyboard = InlineKeyboardMarkup(resize_keyboard=True)
    inline_keyboard.add(InlineKeyboardButton(button_text, url=spotify_authorization_url))

    await message.answer(
        response_text,
        reply_markup=inline_keyboard,
    )


async def send_welcome_all_ok_message(message: Message):
    response_text = await TemplateModel.find_and_render_template(TemplatesList.WELCOME_ALL_OK_MESSAGE)
    await message.answer(response_text)
