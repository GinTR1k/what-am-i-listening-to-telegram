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

    async def update_spotify_tokens(self, spotify_auth_token: SpotifyAuthorisationToken):
        spotify_authorized_at = datetime.fromtimestamp(spotify_auth_token.activation_time)
        expiration_token_at = datetime.utcnow() + timedelta(seconds=spotify_auth_token.activation_time)

        await self.update(
            spotify_access_token=spotify_auth_token.access_token,
            spotify_refresh_token=spotify_auth_token.refresh_token,
            spotify_authorized_at=spotify_authorized_at,
            spotify_expiration_token_at=expiration_token_at,
        ).apply()
