from __future__ import annotations

from async_spotify import SpotifyApiClient


class SpotifyClient(SpotifyApiClient):
    @classmethod
    def init(cls, *args, **kwargs) -> SpotifyClient:
        self = getattr(cls, '__original_instance', None)

        if not self:
            self = cls(*args, **kwargs)
            setattr(cls, '__original_instance', self)

        return self
