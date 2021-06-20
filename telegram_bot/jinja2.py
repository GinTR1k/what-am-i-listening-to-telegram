from __future__ import annotations

from jinja2 import Environment


class Jinja2Environment(Environment):
    @classmethod
    def init(cls, *args, **kwargs) -> Jinja2Environment:
        self = getattr(cls, '__original_instance', None)

        if not self:
            self = cls(*args, **kwargs)
            setattr(cls, '__original_instance', self)

        return self
