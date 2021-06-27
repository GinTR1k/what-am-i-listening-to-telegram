from datetime import datetime
from uuid import uuid4

from telegram_bot.models import db


class FriendModel(db.Model):
    __tablename__ = 'friends'
    uuid = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)

    user_uuid = db.Column(db.String(36), db.ForeignKey('users.uuid'), index=True, nullable=False)
    friend_uuid = db.Column(db.String(36), db.ForeignKey('users.uuid'), index=True, nullable=False)
