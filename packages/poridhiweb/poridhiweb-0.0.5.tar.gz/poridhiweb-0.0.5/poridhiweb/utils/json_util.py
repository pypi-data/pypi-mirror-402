from collections.abc import Sequence
from enum import Enum
from typing import Any


class JSONUtils:
    @classmethod
    def to_dict(cls, content: dict | list | Any):
        if content is None:
            return None
        if isinstance(content, (str, int, float, bool)):
            return content
        if isinstance(content, Enum):
            return content.value
        if hasattr(content, "__dict__"):
            return cls.to_dict(content.__dict__)
        if hasattr(content, "_asdict"):
            return cls.to_dict(content._asdict())
        if isinstance(content, dict):
            return {
                key: cls.to_dict(value)
                for key, value in content.items()
            }
        if isinstance(content, (list, tuple, set, Sequence)):
            return [cls.to_dict(item) for item in content]

        return content
