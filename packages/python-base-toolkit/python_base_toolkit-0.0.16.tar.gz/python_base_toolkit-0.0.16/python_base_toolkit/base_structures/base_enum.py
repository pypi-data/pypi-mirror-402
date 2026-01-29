import json
from enum import Enum, StrEnum
from typing import Any, TypeVar

E = TypeVar("E", bound=Enum)


class EnumMixin:
    def __str__(self: E) -> str:
        return str(self.value)

    def __repr__(self: E) -> str:
        return str(self.value)
        # return f"<{self.__class__.__name__}.{self.name}: {self.value}>"

    @classmethod
    def to_list(cls: type[E]) -> list[Any]:
        return [c.value for c in cls]

    @classmethod
    def to_dict(cls: type[E]) -> dict:
        return {member.name: member.value for member in cls}

    @classmethod
    def names(cls: type[E]) -> list[str]:
        return [c.name for c in cls]

    @classmethod
    def values(cls: type[E]) -> list[Any]:
        return [c.value for c in cls]

    @classmethod
    def from_value(cls: type[E], value: Any) -> list[E]:
        return [member for member in cls if value in member.value]

    @classmethod
    def has_name(cls: type[E], name: str) -> bool:
        return any(member.name == name for member in cls)

    @classmethod
    def has_value(cls: type[E], value: Any) -> bool:
        return any(member.value == value for member in cls)

    @classmethod
    def to_json(cls) -> str:
        return json.dumps(cls.to_dict())


class BaseEnum(EnumMixin, Enum):
    pass


class BaseStrEnum(EnumMixin, StrEnum):
    pass
