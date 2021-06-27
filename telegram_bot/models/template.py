from __future__ import annotations

from datetime import datetime
from typing import (
    Optional,
)
from uuid import uuid4

from jinja2 import (
    BaseLoader,
    StrictUndefined,
)
from sqlalchemy import (
    and_,
    or_,
)

from telegram_bot.config import Config
from telegram_bot.jinja2 import Jinja2Environment
from telegram_bot.models import db


class TemplateModel(db.Model):
    __tablename__ = 'replies'
    uuid = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    language = db.Column(db.String(), nullable=False, index=True)
    name = db.Column(db.String(), nullable=False, index=True)
    value = db.Column(db.String(), nullable=False)

    @classmethod
    async def find(
        cls,
        template_name_or_id: str,
        language: str = Config.TELEGRAM_BOT_DEFAULT_LANGUAGE,
        raise_exception_on_not_found: bool = False,
    ) -> Optional[TemplateModel]:
        """Find a template by name or id."""
        template = await cls.query.where(
            and_(
                or_(
                    cls.name == template_name_or_id,
                    cls.uuid == template_name_or_id,
                ),
                cls.language.in_([language, Config.TELEGRAM_BOT_DEFAULT_LANGUAGE.upper()]),
            )
        ).order_by(
            db.case(
                (
                    (cls.language == language, '1'),
                )
            )
        ).gino.first()

        if template is None and raise_exception_on_not_found:
            raise ValueError(f'Cannot find a template with name={template_name_or_id}')

        return template

    def render_template(self, parameters: dict = None) -> str:
        """Render a template."""
        jinja2_environment = Jinja2Environment.init(
            loader=BaseLoader(),
            undefined=StrictUndefined,
        )

        jinja2_template = jinja2_environment.from_string(self.value)
        result = jinja2_template.render(parameters or {})
        return result

    @classmethod
    async def find_and_render_template(
        cls,
        template_name_or_id: str,
        parameters: dict = None,
        language: str = Config.TELEGRAM_BOT_DEFAULT_LANGUAGE,
        raise_exception_on_not_found: bool = True,
    ) -> str:
        """A shortcut for ``find()`` and ``render_template()``."""
        template = await cls.find(template_name_or_id, language, raise_exception_on_not_found)
        result = template.render_template(parameters)
        return result


class TemplatesList:
    WELCOME_MESSAGE = 'WELCOME_MESSAGE'
    WELCOME_ALL_OK_MESSAGE = 'WELCOME_ALL_OK_MESSAGE'
    WELCOME_SPOTIFY_AUTHORIZE_LINE_BUTTON = 'WELCOME_SPOTIFY_AUTHORIZE_LINE_BUTTON'

    SPOTIFY_AUTHORIZED_WEB_RESPONSE = 'SPOTIFY_AUTHORIZED_WEB_RESPONSE'
    SPOTIFY_AUTHORIZED_MESSAGE = 'SPOTIFY_AUTHORIZED_MESSAGE'
    SPOTIFY_CURRENT_SONG_QUERY_RESULT_TITLE = 'SPOTIFY_CURRENT_SONG_QUERY_RESULT_TITLE'
    SPOTIFY_CURRENT_SONG_QUERY_RESULT_CONTENT = 'SPOTIFY_CURRENT_SONG_QUERY_RESULT_CONTENT'
    SPOTIFY_CURRENT_SONG_FRIEND_QUERY_RESULT_TITLE = 'SPOTIFY_CURRENT_SONG_FRIEND_QUERY_RESULT_TITLE'
    SPOTIFY_CURRENT_SONG_FRIEND_QUERY_RESULT_CONTENT = 'SPOTIFY_CURRENT_SONG_FRIEND_QUERY_RESULT_CONTENT'
    SPOTIFY_NO_CURRENT_SONG_QUERY_TITLE = 'SPOTIFY_NO_CURRENT_SONG_QUERY_TITLE'
    SPOTIFY_NO_CURRENT_SONG_QUERY_CONTENT = 'SPOTIFY_NO_CURRENT_SONG_QUERY_CONTENT'
    SPOTIFY_NO_CURRENT_SONG_FRIEND_QUERY_TITLE = 'SPOTIFY_NO_CURRENT_SONG_FRIEND_QUERY_TITLE'
    SPOTIFY_NO_CURRENT_SONG_FRIEND_QUERY_CONTENT = 'SPOTIFY_NO_CURRENT_SONG_FRIEND_QUERY_CONTENT'
    SPOTIFY_NOT_AUTHORIZED_TITLE = 'SPOTIFY_NOT_AUTHORIZED_TITLE'
    SPOTIFY_NOT_AUTHORIZED_CONTENT = 'SPOTIFY_NOT_AUTHORIZED_CONTENT'
    SPOTIFY_NOT_AUTHORIZED_AND_NO_FRIENDS = 'SPOTIFY_NOT_AUTHORIZED_AND_NO_FRIENDS'

    UNLINK_SPOTIFY_SUCCESS_MESSAGE = 'UNLINK_SPOTIFY_SUCCESS_MESSAGE'
    UNLINK_SPOTIFY_NOT_LINKED_MESSAGE = 'UNLINK_SPOTIFY_NOT_LINKED_MESSAGE'

    ADD_FRIEND_ABOUT_MESSAGE = 'ADD_FRIEND_ABOUT_MESSAGE'
    ADD_FRIEND_SUCCESS_MESSAGE = 'ADD_FRIEND_SUCCESS_MESSAGE'
    ADD_FRIEND_NOT_FOUND_MESSAGE = 'ADD_FRIEND_NOT_FOUND_MESSAGE'

    ALL_MESSAGES_NOT_UNDERSTAND_MESSAGE = 'ALL_MESSAGES_NOT_UNDERSTAND_MESSAGE'
    ALL_MESSAGES_WAITING_FOR_A_FORWARD_MESSAGE_MESSAGE = 'ALL_MESSAGES_WAITING_FOR_A_FORWARD_MESSAGE_MESSAGE'
