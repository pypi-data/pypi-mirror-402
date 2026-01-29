from dataclasses import dataclass
from typing import Any, List, cast

from bolt import AstInterpolation
from mecha import (
    NUMBER_PATTERN,
    AlternativeParser,
    AstChildren,
    AstMacroLineVariable,
    AstNbtPath,
    AstNbtPathKey,
    NbtPathParser,
    Parser,
    delegate,
)
from mecha.utils import string_to_number
from tokenstream import InvalidSyntax, TokenStream, set_location

from .ast import (
    AstMacroArgument,
    AstMacroCoordinateArgument,
    AstMacroNbtPathArgument,
    AstMacroNbtPathKeyArgument,
    AstMacroRange,
)


@dataclass
class MacroParser:
    """
    Used to parse typed_macro's and create the proper AstNode's
    """

    parser: str | tuple[str, ...]
    node_type: type[AstMacroArgument]

    def __call__(self, stream: TokenStream):
        macro: AstMacroArgument = delegate("typed_macro", stream)

        if macro.parser:
            # Implements type checking where it makes sense, this helps to prevent unintended macro injections
            if isinstance(self.parser, str) and macro.parser != self.parser:
                raise ValueError(
                    f"Invalid macro type, received {macro.parser} expected {self.parser}"
                )
            elif macro.parser not in self.parser:
                raise ValueError(
                    f"Invalid macro type, received {macro.parser} expected one of {', '.join(self.parser)}"
                )

        parser = macro.parser

        # If there was no parser just use one of the intended ones for this MacroParser
        if isinstance(self.parser, tuple) and parser is None:
            parser = self.parser[0]
        elif isinstance(self.parser, str):
            parser = self.parser

        # Creates the proper instance of node_type
        if not isinstance(macro, self.node_type):
            return self.node_type(name=macro.name, parser=parser)

        return macro


@dataclass
class MacroNbtPathParser(NbtPathParser):
    """Parser for nbt paths."""

    def __call__(self, stream: TokenStream) -> AstNbtPath:
        components: List[Any] = []

        with stream.syntax(
            dot=r"\.",
            curly=r"\{|\}",
            bracket=r"\[|\]",
            quoted_string=r'"(?:\\.|[^\\\n])*?"' "|" r"'(?:\\.|[^\\\n])*?'",
            string=r"(?:[0-9a-z_\-]+:)?[a-zA-Z0-9_+-]+",
        ):
            components.extend(self.parse_modifiers(stream))

            while not components or stream.get("dot"):
                with stream.checkpoint() as commit:
                    macro: AstMacroArgument = delegate("typed_macro", stream)

                    if not macro.parser or macro.parser == "string":
                        components.append(
                            set_location(
                                AstMacroNbtPathKeyArgument(
                                    name=macro.name, parser="string"
                                ),
                                macro,
                            )
                        )
                    elif macro.parser == "nbt":
                        components.append(
                            set_location(
                                AstMacroNbtPathArgument(name=macro.name, parser="nbt"),
                                macro,
                            )
                        )

                    commit()

                if commit.rollback:
                    quoted_string, string = stream.expect("quoted_string", "string")

                    if quoted_string:
                        component_node = AstNbtPathKey(
                            value=self.quote_helper.unquote_string(quoted_string),
                        )
                        components.append(set_location(component_node, quoted_string))
                    elif string:
                        component_node = AstNbtPathKey(value=string.value)
                        components.append(set_location(component_node, string))

                components.extend(self.parse_modifiers(stream))

        if not components:
            raise stream.emit_error(InvalidSyntax("Empty nbt path not allowed."))

        node = AstNbtPath(components=AstChildren(components))
        return set_location(node, components[0], components[-1])


class MacroRangeParser:
    def get_bound(self, stream: TokenStream) -> int | float | AstMacroArgument | None:
        if number := stream.get("number"):
            return string_to_number(number.value)

        with stream.checkpoint() as commit:
            macro: AstMacroArgument = delegate("typed_macro", stream)

            if macro.parser and macro.parser != "numeric":
                raise ValueError(
                    f"Invalid macro type, received {macro.parser} expected numeric"
                )

            commit()

        if not commit.rollback:
            return macro

        return None

    def __call__(self, stream: TokenStream):
        with stream.syntax(range=r"\.\.", number=NUMBER_PATTERN):
            lower_bound = self.get_bound(stream)
            range = stream.get("range")
            upper_bound = self.get_bound(stream)

        return set_location(
            AstMacroRange(min=lower_bound, max=upper_bound),
            lower_bound or range or upper_bound,
            upper_bound or range or lower_bound,
        )


def macro(
    parsers: dict[str, Parser],
    type: str | tuple[str],
    priority=False,
    node_type: type[AstMacroArgument] = AstMacroArgument,
):
    """
    Creates the proper AlternativeParser

    :param parsers: The current set of parsers from mecha
    :type parsers: dict[str, Parser]
    :param type: The parser to create an alternative for
    :type type: str | tuple[str]
    :param priority: Should a macro be checked for before the original parser is used
    :param node_type: The kind of node to be created by the parser
    :type node_type: type[AstMacroArgument]
    """
    parser_type = type
    if isinstance(type, tuple):
        parser_type = type[0]

    if not priority:
        return AlternativeParser(
            [parsers[cast(str, parser_type)], MacroParser(type, node_type)]
        )
    return AlternativeParser(
        [MacroParser(type, node_type), parsers[cast(str, parser_type)]]
    )


def parse_typed_macro(stream: TokenStream):
    """
    Parses macros with a parser type
    Ex: $(foo: numeric)

    :param stream: The instance of TokenStream
    :type stream: TokenStream
    """
    with stream.syntax(
        open_variable=r"\$\(", close_variable=r"\)", parser=r"\w+", colon=r":\s*"
    ):
        open_variable = stream.expect("open_variable")
        node: AstMacroLineVariable | AstInterpolation = delegate(
            "macro_line_variable", stream
        )

        parser = None
        if isinstance(node, AstMacroLineVariable):
            name = node.value

            if stream.get("colon"):
                parser = stream.expect("parser").value

        closed_variable = stream.expect("close_variable")
    return set_location(
        AstMacroArgument(name=name, parser=parser), open_variable, closed_variable
    )


def parse_coordinate(stream: TokenStream):
    """
    Parses coordinates with support for macros

    :param stream: The TokenStream instance
    :type stream: TokenStream
    """
    with stream.syntax(modifier="[~^]"):
        modifier_token = stream.get("modifier")

        modifier = "absolute"

        if modifier_token and modifier_token.value == "~":
            modifier = "relative"
        elif modifier_token and modifier_token.value == "^":
            modifier = "local"

        macro: AstMacroArgument = delegate("typed_macro", stream)

        if macro.parser and macro.parser != "numeric":
            raise ValueError(
                f"Invalid macro type, received {macro.parser} expected numeric"
            )

        return set_location(
            AstMacroCoordinateArgument(
                name=macro.name, type=modifier, parser="numeric"
            ),
            modifier_token or macro.location,
            macro.end_location,
        )
