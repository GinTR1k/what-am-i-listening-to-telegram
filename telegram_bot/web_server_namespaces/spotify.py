from aiohttp import web

from telegram_bot.models import (
    TemplateModel,
    TemplatesList,
    UserModel,
)


def create_spotify_web_app(context: dict = None) -> web.Application:
    """Create a web application."""
    app = web.Application()
    app.update(context)

    app.router.add_view('', SpotifyView)
    return app


class SpotifyView(web.View):
    async def get(self):
        """GET request handler."""
        spotify_code = self.request.query.get('code')
        user_uuid = self.request.query.get('state')

        if not spotify_code or not user_uuid:
            raise web.HTTPNotFound()

        user = await UserModel.get(user_uuid)

        telegram_bot = self.request.app['telegram_bot']
        spotify = self.request.app['spotify']

        await spotify.create_new_client()
        spotify_auth_token = await spotify.get_auth_token_with_code(spotify_code)
        spotify_user = await spotify.user.me(spotify_auth_token)
        await spotify.close_client()

        await user.update_spotify_tokens(spotify_auth_token)

        web_response_text = await TemplateModel.find_and_render_template(
            TemplatesList.SPOTIFY_AUTHORIZED_WEB_RESPONSE,
            {
                'BOT_TAG': (await telegram_bot.me).mention.replace('@', ''),
            },
        )
        telegram_message_text = await TemplateModel.find_and_render_template(
            TemplatesList.SPOTIFY_AUTHORIZED_MESSAGE,
            {
                'SPOTIFY_USERNAME': spotify_user['display_name'],
            }
        )

        await telegram_bot.send_message(
            chat_id=user.telegram_id,
            text=telegram_message_text,
        )

        return web.Response(text=web_response_text, content_type='text/html')
