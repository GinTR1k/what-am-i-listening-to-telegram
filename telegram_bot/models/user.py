from datetime import (
    datetime,
    timedelta,
)
from uuid import uuid4

from async_spotify.authentification import SpotifyAuthorisationToken

from telegram_bot.models import db


class UserModel(db.Model):
    __tablename__ = 'users'
    uuid = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)

    telegram_id = db.Column(db.Integer(), index=True, unique=True, nullable=False)

    spotify_access_token = db.Column(db.String())
    spotify_refresh_token = db.Column(db.String())
    spotify_authorized_at = db.Column(db.DateTime())
    spotify_expiration_token_at = db.Column(db.DateTime())
    spotify_user_name = db.Column(db.String())
    spotify_user_pic = db.Column(db.String())

    async def update_spotify_tokens(self, spotify_auth_token: SpotifyAuthorisationToken, spotify_user: dict):
        spotify_authorized_at = datetime.fromtimestamp(spotify_auth_token.activation_time)
        expiration_token_at = None

        spotify_user_pic = None
        user_pic_size = None

        for image in spotify_user['images']:
            if user_pic_size is None or (image.get('height') is not None and image['height'] < user_pic_size):
                spotify_user_pic = image['url']
                user_pic_size = image['height']

        await self.update(
            spotify_access_token=spotify_auth_token.access_token,
            spotify_refresh_token=spotify_auth_token.refresh_token,
            spotify_authorized_at=spotify_authorized_at,
            spotify_expiration_token_at=expiration_token_at,
            spotify_user_name=spotify_user['display_name'],
            spotify_user_pic=spotify_user_pic,
        ).apply()
