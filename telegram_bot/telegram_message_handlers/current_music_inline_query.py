import asyncio
from hashlib import md5

from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from async_spotify.authentification import SpotifyAuthorisationToken
from async_spotify.authentification.authorization_flows import AuthorizationCodeFlow

from telegram_bot.config import Config
from telegram_bot.models import (
    FriendModel,
    TemplateModel,
    TemplatesList,
    UserModel,
)
from telegram_bot.spotify_client import SpotifyClient


async def current_music_inline_query(inline_query: InlineQuery):
    user_telegram_id = inline_query.from_user.id
    user = await UserModel.query.where(UserModel.telegram_id == user_telegram_id).gino.first()

    if not user:
        return await send_inline_answer_not_authorized(inline_query)

    friends_records = await FriendModel.query.where(FriendModel.user_uuid == user.uuid).gino.all()

    if not user.spotify_access_token and not friends_records:
        return await send_inline_answer_not_authorized_and_no_friend(inline_query)

    friends = [await UserModel.get(friend_record.friend_uuid) for friend_record in friends_records]

    current_track_user_task = asyncio.create_task(get_current_track(user))
    current_track_friends_tasks = {asyncio.create_task(get_current_track(friend)): friend for friend in friends}

    inline_items = []
    pending_tasks = (current_track_user_task, *current_track_friends_tasks.keys())

    while pending_tasks:
        done_tasks, pending_tasks = await asyncio.wait(pending_tasks)

        for done_task in done_tasks:
            current_track_data = done_task.result()
            friend = current_track_friends_tasks.get(done_task)

            title_template_name = (
                TemplatesList.SPOTIFY_CURRENT_SONG_QUERY_RESULT_TITLE,
                TemplatesList.SPOTIFY_CURRENT_SONG_FRIEND_QUERY_RESULT_TITLE,
            )[friend is not None]

            if current_track_data:
                content_template_name = (
                    TemplatesList.SPOTIFY_CURRENT_SONG_QUERY_RESULT_CONTENT,
                    TemplatesList.SPOTIFY_CURRENT_SONG_FRIEND_QUERY_RESULT_CONTENT,
                )[friend is not None]
                (
                    current_track_name,
                    current_track_artists,
                    current_track_progress,
                    current_track_duration,
                    current_track_link,
                ) = parse_current_track_data(current_track_data)
            else:
                content_template_name = (
                    TemplatesList.SPOTIFY_NO_CURRENT_SONG_QUERY_CONTENT,
                    TemplatesList.SPOTIFY_NO_CURRENT_SONG_FRIEND_QUERY_CONTENT,
                )[friend is not None]
                current_track_name = current_track_artists = current_track_progress = current_track_duration = \
                    current_track_link = None

            title_template = await TemplateModel.find(title_template_name)
            title = title_template.render_template(dict(
                SPOTIFY_USER_NAME=user.spotify_user_name if friend is None else friend.spotify_user_name,
            ))

            content_template = await TemplateModel.find(content_template_name)
            content = content_template.render_template(dict(
                SPOTIFY_USER_NAME=user.spotify_user_name if friend is None else friend.spotify_user_name,
                TRACK_NAME=current_track_name,
                TRACK_ARTISTS=current_track_artists,
                TRACK_PROGRESS=current_track_progress,
                TRACK_DURATION=current_track_duration,
                TRACK_URL=current_track_link,
            ))

            thumbnail_url = user.spotify_user_pic if friend is None else friend.spotify_user_pic

            inline_item_content = InputTextMessageContent(content)
            result_id: str = md5(title.encode()).hexdigest()

            inline_item = InlineQueryResultArticle(
                id=result_id,
                title=title,
                input_message_content=inline_item_content,
                thumb_url=thumbnail_url,
            )

            if friend is None:
                inline_items.insert(0, inline_item)
            else:
                inline_items.append(inline_item)

    await inline_query.bot.answer_inline_query(inline_query.id, results=inline_items, cache_time=1)


async def send_inline_answer_not_authorized(inline_query: InlineQuery):
    await _send_inline_answer(
        inline_query=inline_query,
        template_name=TemplatesList.SPOTIFY_NOT_AUTHORIZED_TITLE,
        template_parameters=dict(BOT_TAG=(await inline_query.bot.me).mention),
    )


async def send_inline_answer_no_song(inline_query: InlineQuery):
    await _send_inline_answer(
        inline_query=inline_query,
        template_name=TemplatesList.SPOTIFY_NO_CURRENT_SONG_QUERY_CONTENT,
    )


async def send_inline_answer_not_authorized_and_no_friend(inline_query: InlineQuery):
    await _send_inline_answer(
        inline_query=inline_query,
        template_name=TemplatesList.SPOTIFY_NOT_AUTHORIZED_AND_NO_FRIENDS,
        template_parameters=dict(BOT_TAG=(await inline_query.bot.me).mention),
    )


async def _send_inline_answer(inline_query: InlineQuery, template_name: str, template_parameters: dict = None):
    title = await TemplateModel.find_and_render_template(template_name)
    content = await TemplateModel.find_and_render_template(template_name, template_parameters)
    input_content = InputTextMessageContent(content)

    result_id: str = md5(title.encode()).hexdigest()
    item = InlineQueryResultArticle(
        id=result_id,
        title=title,
        input_message_content=input_content,
    )

    await inline_query.bot.answer_inline_query(inline_query.id, results=[item], cache_time=1)


def parse_current_track_data(current_track: dict) -> tuple:
    current_track_progress_in_secs = current_track['progress_ms'] // 1000
    current_track_progress_minutes = current_track_progress_in_secs // 60
    current_track_progress_seconds = current_track_progress_in_secs % 60
    current_track_progress = f'{current_track_progress_minutes:02d}:{current_track_progress_seconds:02d}'

    current_track_duration_in_secs = current_track['item']['duration_ms'] // 1000
    current_track_duration_minutes = current_track_duration_in_secs // 60
    current_track_duration_seconds = current_track_duration_in_secs % 60
    current_track_duration = f'{current_track_duration_minutes:02d}:{current_track_duration_seconds:02d}'

    current_track_name = current_track['item']['name']
    current_track_link = current_track['item']['external_urls']['spotify']
    current_track_artists = ', '.join([artist['name'] for artist in current_track['item']['artists']])

    thumbnail_url = None
    thumbnail_size = None
    for image in current_track['item']['album']['images']:
        if thumbnail_size is None or image['height'] > thumbnail_size:
            thumbnail_size = image['height']
            thumbnail_url = image['url']

    return (
        current_track_name,
        current_track_artists,
        current_track_progress,
        current_track_duration,
        current_track_link,
        # thumbnail_url,
        # thumbnail_size,
    )


async def get_current_track(user: UserModel):
    spotify = SpotifyClient(
        AuthorizationCodeFlow(
            application_id=Config.SPOTIFY_APPLICATION_ID,
            application_secret=Config.SPOTIFY_APPLICATION_SECRET,
            scopes=Config.SPOTIFY_SCOPES,
            redirect_url=Config.SPOTIFY_REDIRECT_URL,
        ),
    )

    await spotify.create_new_client()
    old_spotify_auth_token = SpotifyAuthorisationToken(
        access_token=user.spotify_access_token,
        refresh_token=user.spotify_refresh_token,
        activation_time=user.spotify_authorized_at.timestamp(),
    )
    if old_spotify_auth_token.is_expired():
        new_spotify_auth_token = await spotify.refresh_token(old_spotify_auth_token)
        spotify_user = await spotify.user.me(new_spotify_auth_token)
        await user.update_spotify_tokens(new_spotify_auth_token, spotify_user)
    else:
        new_spotify_auth_token = old_spotify_auth_token

    current_track = await spotify.player.get_current_track(new_spotify_auth_token)
    await spotify.close_client()

    return current_track
