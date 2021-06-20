import logging

import sentry_sdk
from aiogram import Bot
from aiohttp import web
from aiohttp.web_middlewares import normalize_path_middleware
from aiohttp.web_runner import (
    AppRunner,
    TCPSite,
)
from async_spotify.authentification.authorization_flows import AuthorizationCodeFlow

from telegram_bot.__version__ import VERSION
from telegram_bot.config import Config
from telegram_bot.models import db
from telegram_bot.spotify_client import SpotifyClient
from telegram_bot.telegram_message_handlers import register_dispatcher
from web_server_namespaces.spotify import create_spotify_web_app


class App:
    def __init__(self):
        self.logger = logging.getLogger('Telegram bot')
        logging.basicConfig(format=Config.LOGGER_FORMAT, level=logging.INFO)
        self.logger.setLevel(logging.DEBUG if Config.DEBUG else logging.INFO)

        sentry_sdk.init(
            dsn=Config.SENTRY_DSN,
            release=VERSION,
            environment=Config.ENVIRONMENT,
        )

        self.database = db
        self.telegram_bot = Bot(token=Config.TELEGRAM_BOT_TOKEN, parse_mode='html')
        self.telegram_dispatcher = register_dispatcher(self.telegram_bot)
        self.spotify = SpotifyClient.init(
            AuthorizationCodeFlow(
                application_id=Config.SPOTIFY_APPLICATION_ID,
                application_secret=Config.SPOTIFY_APPLICATION_SECRET,
                scopes=Config.SPOTIFY_SCOPES,
                redirect_url=Config.SPOTIFY_REDIRECT_URL,
            ),
        )
        self.web_server = web.Application(
            middlewares=[normalize_path_middleware(append_slash=False, remove_slash=True)],
        )
        self.web_server_runner = AppRunner(self.web_server, access_log=None)

        self._is_working = False

    async def start(self):
        """Start an app."""
        self.logger.debug('Starting app...')

        try:
            await self._on_start()
            self._is_working = True
            self.logger.info('App started!')
        except Exception:
            await self.shutdown()
            raise

        try:
            await self._run()
        except Exception:
            await self.shutdown()
            raise

    async def _on_start(self):
        """Подготовка перед запуском приложения."""
        await self.setup_database()
        await self.setup_web_server()

    async def _run(self):
        """Main method."""
        site = TCPSite(self.web_server_runner, Config.WEB_HOST, Config.WEB_PORT)
        await site.start()

        await self.telegram_dispatcher.start_polling()

    async def setup_database(self):
        await self.database.set_bind(Config.DATABASE_URI)

    async def setup_web_server(self):
        self.web_server.add_subapp(Config.WEB_SPOTIFY_CALLBACK_ENDPOINT, create_spotify_web_app(context={
            'telegram_bot': self.telegram_bot,
            'spotify': self.spotify,
        }))
        await self.web_server_runner.setup()

    async def shutdown(self):
        if not self._is_working:
            return

        self.logger.debug('App is shutting down...')

        try:
            if self.telegram_dispatcher:
                await self.telegram_dispatcher.stop_polling()

            await self.web_server_runner.shutdown()
            await self.web_server_runner.cleanup()

            await db.pop_bind().close()

            self._is_working = False
        except Exception:
            self.logger.exception('While app is shutting down, raised an exception')
            raise

        self.logger.info('App stopped!')
