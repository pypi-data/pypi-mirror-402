from dataclasses import dataclass, field
from typing import Any, Literal

from beet.core.utils import required_field
from mecha import (
    AstGreedy,
    AstMessage,
    AstNbtCompoundKey,
    AstNbtValue,
    AstNode,
    AstString,
    AstWord,
)

from .typing import MacroRepresentation, MacroTag

__all__ = [
    "AstMacroArgument",
    "AstMacroNbtArgument",
    "AstMacroCoordinateArgument",
    "AstMacroNbtPathKeyArgument",
    "AstMacroNbtPathArgument",
    "AstMacroRange",
    "AstMacroStringWrapper",
    "AstNbtValueWithMacro",
    "AstStringWithMacro",
    "AstGreedyWithMacro",
    "AstWordWithMacro",
    "AstMessageWithMacro",
]


@dataclass(frozen=True, slots=True)
class AstMacroArgument(AstNode, MacroRepresentation):
    name: str = required_field()
    parser: str | None = required_field()


@dataclass(frozen=True, slots=True)
class AstMacroNbtArgument(AstMacroArgument):
    def evaluate(self):
        return MacroTag(self.name, self.parser)


@dataclass(frozen=True, slots=True)
class AstMacroCoordinateArgument(AstMacroArgument):
    type: Literal["absolute", "local", "relative"] = required_field()


@dataclass(frozen=True, slots=True)
class AstMacroNbtPathKeyArgument(AstMacroArgument): ...


@dataclass(frozen=True, slots=True)
class AstMacroNbtPathArgument(AstMacroArgument): ...


@dataclass(frozen=True, slots=True)
class AstMacroExpression(AstMacroArgument): ...


@dataclass(frozen=True, slots=True)
class AstMacroRange(AstNode):
    min: int | float | AstMacroArgument | None = field(default=None)
    max: int | float | AstMacroArgument | None = field(default=None)


@dataclass(frozen=True, slots=True)
class AstMacroStringWrapper[N](AstNode):
    child: N = required_field()


@dataclass(frozen=True, slots=True)
class AstNbtValueWithMacro(AstNbtValue, MacroRepresentation):
    @classmethod
    def from_value(cls, value: Any) -> "AstNbtValueWithMacro":
        return cls(value=value)


@dataclass(frozen=True, slots=True)
class AstMacroNbtCompoundKey(AstNbtCompoundKey, MacroRepresentation):
    name: str = required_field()
    parser: str | None = required_field()


@dataclass(frozen=True, slots=True)
class AstStringWithMacro(AstString, MacroRepresentation):
    @classmethod
    def from_value(cls, value: Any) -> "AstStringWithMacro":
        return AstStringWithMacro(value=str(value))


@dataclass(frozen=True, slots=True)
class AstGreedyWithMacro(AstGreedy, MacroRepresentation):
    @classmethod
    def from_value(cls, value: Any) -> "AstGreedyWithMacro":
        return cls(value=AstGreedy.from_value(value).value)


@dataclass(frozen=True, slots=True)
class AstWordWithMacro(AstWord, MacroRepresentation):
    @classmethod
    def from_value(cls, value: Any) -> "AstWordWithMacro":
        return cls(value=AstWord.from_value(value).value)


@dataclass(frozen=True, slots=True)
class AstMessageWithMacro(AstMessage, MacroRepresentation):
    @classmethod
    def from_value(cls, value: Any) -> "AstMessageWithMacro":
        return cls(fragments=AstMessage.from_value(value).fragments)
