from dataclasses import dataclass
from typing import Any, Callable, List

from beet.core.utils import required_field
from bolt import AstFormatString
from mecha import (
    AstCommand,
    AstLiteral,
    AstNbtPath,
    AstNbtPathKey,
    AstNode,
    CommandSpec,
    MutatingReducer,
    Visitor,
    rule,
)
from mecha.utils import number_to_string
from nbtlib import Serializer as NbtSerializer
from tokenstream import set_location

from .ast import (
    AstMacroArgument,
    AstMacroCoordinateArgument,
    AstMacroNbtArgument,
    AstMacroNbtCompoundKey,
    AstMacroNbtPathArgument,
    AstMacroNbtPathKeyArgument,
    AstMacroRange,
    AstMacroStringWrapper,
)
from .typing import (
    MacroRepresentation,
    MacroTag,
    QuotedStringWithMacro,
    StringWithMacro,
)


def serialize_macro(_self: NbtSerializer, tag: MacroTag):
    if tag.parser == "string":
        return f'"$({tag.name})"'

    return f"$({tag.name})"


@dataclass
class MacroConverter:
    """
    Used to convert interpolated strings with contain macros to the proper AstXWithMacro nodes
    """

    base_converter: Callable[[Any, AstNode], AstNode]
    node_type: type

    def __call__(self, obj: Any, node: AstNode) -> AstNode:
        if isinstance(obj, QuotedStringWithMacro):
            return self.node_type.from_value(obj)
        if isinstance(obj, StringWithMacro):
            return AstLiteral.from_value(obj)
        return self.base_converter(obj, node)


@dataclass
class CommandSerializer(Visitor):
    spec: CommandSpec = required_field()

    @rule(AstCommand)
    def command(self, node: AstCommand, result: list[str]):
        prototype = self.spec.prototypes[node.identifier]
        argument_index = 0

        sep = ""

        start_index = 0
        # Scan backwards until we find the start of the current line
        for i in range(len(result) - 1, -1, -1):
            if result[i] == "\n":
                start_index = i + 1
                break

        for token in prototype.signature:
            result.append(sep)
            sep = " "

            # If token is a string then we can move on, literals can't contain macros
            if isinstance(token, str):
                result.append(token)
            else:
                argument = node.arguments[argument_index]

                # Scan the argument for any MacroRepresentations
                for child in argument.walk():
                    if isinstance(child, MacroRepresentation):
                        result[start_index] = "$"
                        break

                yield argument
                argument_index += 1

        if result[start_index] == "$":
            return

        for i in range(start_index, len(result)):
            if result[i] == "$(" and result[i + 2] == ")":
                result[start_index] = "$"
                break

    def default(
        self, argument: AstMacroArgument | AstMacroNbtCompoundKey, result: list[str]
    ):
        string = argument.parser == "string"
        if string:
            result.append('"')

        result.append("$(")
        result.append(argument.name)
        result.append(")")

        if string:
            result.append('"')

    @rule(AstMacroArgument, AstMacroNbtPathArgument, AstMacroNbtArgument)
    def macro(self, argument: AstMacroArgument, result: list[str]):
        self.default(argument, result)

    @rule(AstMacroCoordinateArgument)
    def coordinate(self, argument: AstMacroCoordinateArgument, result: list[str]):
        if argument.type == "local":
            result.append("^")
        elif argument.type == "relative":
            result.append("~")

        self.default(argument, result)

    @rule(AstMacroNbtPathKeyArgument)
    def macro_path_key(self, argument: AstMacroNbtPathKeyArgument, result: list[str]):
        self.default(argument, result)

    @rule(AstNbtPath)
    def nbt_path(self, node: AstNbtPath, result: List[str]):
        sep = ""
        for component in node.components:
            if isinstance(
                component,
                (AstNbtPathKey, AstMacroNbtPathKeyArgument, AstMacroNbtPathArgument),
            ):
                result.append(sep)
            sep = "."
            yield component

    @rule(AstMacroNbtCompoundKey)
    def nbt_compound_key(self, node: AstMacroNbtCompoundKey, result: list[str]):
        self.default(node, result)

    @rule(AstMacroRange)
    def range(self, node: AstMacroRange, result: list[str]):
        if node.min == node.max and node.min is not None:
            if isinstance(node.min, AstMacroArgument):
                yield node.min
            else:
                result.append(number_to_string(node.min))
        else:
            if node.min is not None:
                if isinstance(node.min, AstMacroArgument):
                    yield node.min
                else:
                    result.append(number_to_string(node.min))

            result.append("..")

            if node.max is not None:
                if isinstance(node.max, AstMacroArgument):
                    yield node.max
                else:
                    result.append(number_to_string(node.max))


@dataclass
class MacroMutator(MutatingReducer):
    @rule(AstFormatString)
    def format_string(self, node: AstFormatString):
        if any(map(lambda v: isinstance(v, AstMacroArgument), node.values)):
            return set_location(
                AstMacroStringWrapper(child=node), node.location, node.end_location
            )

        return node
