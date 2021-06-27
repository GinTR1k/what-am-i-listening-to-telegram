from gino import Gino

db = Gino()

from .template import TemplateModel, TemplatesList
from .user import UserModel
from .friend import FriendModel

__all__ = (
    'db',
    'TemplateModel',
    'TemplatesList',
    'UserModel',
    'FriendModel',
)
