from dataclasses import dataclass
from typing import Generator, List, Optional

from bolt import Accumulator, visit_generic, visit_single
from mecha import AstNode, Visitor, rule

from .ast import AstMacroArgument, AstMacroExpression, AstMacroStringWrapper
from .typing import MacroTag, QuotedStringWithMacro


def ast_to_macro(macro: AstMacroArgument):
    return MacroTag(macro.name, macro.parser)


def make_macro_string():
    """
    Returns the type `StringWithMacro`, this is to add the type to the scope w/o making it globally accessible.

    Kind of hacky but works well
    """
    return QuotedStringWithMacro


@dataclass
class MacroCodegen(Visitor):
    @rule(AstMacroExpression)
    def macro(
        self, node: AstMacroExpression, acc: Accumulator
    ) -> Generator[AstNode, Optional[List[str]], Optional[List[str]]]:
        # This allows for macros to be used as literals
        result = yield from visit_generic(node, acc)

        if result is None:
            result = acc.make_ref(node)

        result = acc.helper(ast_to_macro.__name__, result)

        return [result]

    @rule(AstMacroStringWrapper)
    def wrapper(
        self, node: AstMacroStringWrapper, acc: Accumulator
    ) -> Generator[AstNode, Optional[List[str]], Optional[List[str]]]:
        # Codegen the underlying child and get its result
        child = yield from visit_single(node.child, required=True)

        # Create a variable and assign it to a new instance of StringWithMacro
        result = acc.make_variable()
        # make_macro_string returns the **type** StringWithMacro, you must manually create the instance afterwards
        acc.statement(f"{result} = {acc.helper(make_macro_string.__name__)}({child})")

        return [result]
