from environs import Env

env = Env()
env.read_env()


class Config:
    DEBUG = env('DEBUG', False)
    ENVIRONMENT = env('ENVIRONMENT', '')
    LOGGER_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    SENTRY_DSN = env('SENTRY_DSN', '')

    with env.prefixed('DATABASE_'):
        DATABASE_URI = env('URI', '') or 'postgres://{user}:{password}@{host}:{port}/{database}'.format(
            user=env('USER'),
            password=env('PASSWORD'),
            host=env('HOST'),
            port=env('PORT', 5432),
            database=env('NAME'),
        )

    with env.prefixed('TELEGRAM_BOT_'):
        TELEGRAM_BOT_TOKEN = env('TOKEN')
        TELEGRAM_BOT_DEFAULT_LANGUAGE = env('DEFAULT_LANGUAGE', 'ru')

    with env.prefixed('SPOTIFY_'):
        SPOTIFY_APPLICATION_ID = env('APPLICATION_ID')
        SPOTIFY_APPLICATION_SECRET = env('APPLICATION_SECRET')
        SPOTIFY_SCOPES = env.list('SCOPES', 'user-read-playback-state')
        SPOTIFY_REDIRECT_URL = env('REDIRECT_URL')

    with env.prefixed('WEB_'):
        WEB_HOST = env('HOST', '0.0.0.0')
        WEB_PORT = env('PORT', 12345)
        WEB_SPOTIFY_CALLBACK_ENDPOINT = env('SPOTIFY_CALLBACK_ENDPOINT', '/spotify_callback')
