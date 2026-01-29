from dataclasses import dataclass

from beet.core.utils import required_field
from nbtlib import Base


class MacroRepresentation: ...


class StringWithMacro(str): ...


@dataclass
class MacroTag(Base):
    name: str = required_field()
    parser: str | None = required_field()

    def __post_init__(self):
        self.serializer = "macro"

    def __str__(self):
        return f"$({self.name})"
