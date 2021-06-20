from hashlib import md5

from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from async_spotify.authentification import SpotifyAuthorisationToken

from telegram_bot.models import (
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

    if not user.spotify_access_token:
        return await send_inline_answer_not_authorized(inline_query)

    spotify = SpotifyClient.init()
    await spotify.create_new_client()
    old_spotify_auth_token = SpotifyAuthorisationToken(
        access_token=user.spotify_access_token,
        refresh_token=user.spotify_refresh_token,
        activation_time=user.spotify_authorized_at.timestamp(),
    )
    if old_spotify_auth_token.is_expired():
        new_spotify_auth_token = await spotify.refresh_token(old_spotify_auth_token)
        await user.update_spotify_tokens(new_spotify_auth_token)
    else:
        new_spotify_auth_token = old_spotify_auth_token

    current_track = await spotify.player.get_current_track(new_spotify_auth_token)
    await spotify.close_client()

    if not current_track:
        return await send_inline_answer_no_song(inline_query)

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

    title = await TemplateModel.find_and_render_template(
        TemplatesList.SPOTIFY_CURRENT_SONG_QUERY_RESULT_TITLE,
        {
            'TRACK_NAME': current_track_name,
            'TRACK_ARTISTS': current_track_artists,
            'TRACK_PROGRESS': current_track_progress,
            'TRACK_DURATION': current_track_duration,
            'TRACK_URL': current_track_link,
        }
    )
    content = await TemplateModel.find_and_render_template(
        TemplatesList.SPOTIFY_CURRENT_SONG_QUERY_RESULT_CONTENT,
        {
            'TRACK_NAME': current_track_name,
            'TRACK_ARTISTS': current_track_artists,
            'TRACK_PROGRESS': current_track_progress,
            'TRACK_DURATION': current_track_duration,
            'TRACK_URL': current_track_link,
        }
    )
    input_content = InputTextMessageContent(content)

    result_id: str = md5(title.encode()).hexdigest()
    item = InlineQueryResultArticle(
        id=result_id,
        title=title,
        input_message_content=input_content,
        thumb_url=thumbnail_url,
        thumb_width=thumbnail_size,
        thumb_height=thumbnail_size,
    )

    await inline_query.bot.answer_inline_query(inline_query.id, results=[item], cache_time=1)


async def send_inline_answer_not_authorized(inline_query: InlineQuery):
    title = await TemplateModel.find_and_render_template(TemplatesList.SPOTIFY_NOT_AUTHORIZED_TITLE)
    content = await TemplateModel.find_and_render_template(
        TemplatesList.SPOTIFY_NOT_AUTHORIZED_CONTENT,
        {
            'BOT_TAG': (await inline_query.bot.me).mention,
        }
    )
    input_content = InputTextMessageContent(content)

    result_id: str = md5(title.encode()).hexdigest()
    item = InlineQueryResultArticle(
        id=result_id,
        title=title,
        input_message_content=input_content,
    )

    await inline_query.bot.answer_inline_query(inline_query.id, results=[item], cache_time=1)


async def send_inline_answer_no_song(inline_query: InlineQuery):
    title = await TemplateModel.find_and_render_template(TemplatesList.SPOTIFY_NO_CURRENT_SONG_QUERY_TITLE)
    content = await TemplateModel.find_and_render_template(TemplatesList.SPOTIFY_NO_CURRENT_SONG_QUERY_CONTENT)
    input_content = InputTextMessageContent(content)

    result_id: str = md5(title.encode()).hexdigest()
    item = InlineQueryResultArticle(
        id=result_id,
        title=title,
        input_message_content=input_content,
    )

    await inline_query.bot.answer_inline_query(inline_query.id, results=[item], cache_time=1)
