from contextlib import suppress
from beet import Context
from bolt import Runtime
from mecha import AlternativeParser, Mecha, Parser

from .ast import (
    AstGreedyWithMacro,
    AstMacroExpression,
    AstMacroNbtArgument,
    AstMessageWithMacro,
    AstNbtValueWithMacro,
    AstStringWithMacro,
    AstWordWithMacro,
)
from .codegen import MacroCodegen, ast_to_macro, make_macro_string
from .parse import (
    MacroNbtParser,
    MacroNbtPathParser,
    MacroParser,
    MacroRangeParser,
    macro,
    parse_coordinate,
    parse_typed_macro,
)
from .patches import apply_patches
from .serialize import CommandSerializer, MacroConverter, MacroMutator


def get_parsers(parsers: dict[str, Parser]):
    parse_nbt: Parser = parsers["nbt"]

    def make_nbt_parser(parser: Parser):
        return AlternativeParser(
            [MacroParser(("nbt", "string"), AstMacroNbtArgument), parser]
        )

    new_parsers = {
        "typed_macro": parse_typed_macro,
        "bool": macro(parsers, "bool"),
        "numeric": macro(parsers, "numeric"),
        "coordinate": AlternativeParser([parsers["coordinate"], parse_coordinate]),
        "time": macro(parsers, "time"),
        "word": macro(parsers, "word", priority=True),
        "phrase": macro(parsers, "phrase", priority=True),
        "greedy": macro(parsers, "greedy", priority=True),
        "entity": macro(parsers, "entity", priority=True),
        "nbt": make_nbt_parser(parsers["nbt"]),
        "nbt_compound_entry": MacroNbtParser(parsers["nbt_compound_entry"]),
        "nbt_list_or_array_element": make_nbt_parser(
            parsers["nbt_list_or_array_element"]
        ),
        "nbt_compound": make_nbt_parser(parsers["nbt_compound"]),
        "nbt_path": AlternativeParser(
            [parsers["nbt_path"], MacroNbtPathParser(nbt_compound_parser=parse_nbt)]
        ),
        "range": AlternativeParser([parsers["range"], MacroRangeParser()]),
        "bolt:literal": macro(parsers, "bolt:literal", node_type=AstMacroExpression),
    }

    return new_parsers


conversions = {
    "interpolate_phrase": AstStringWithMacro,
    "interpolate_word": AstWordWithMacro,
    "interpolate_greedy": AstGreedyWithMacro,
    "interpolate_nbt": AstNbtValueWithMacro,
    "interpolate_message": AstMessageWithMacro,
}


def beet_default(ctx: Context):
    with suppress(ImportError):
        from .aegis import setup_aegis

        ctx.require(setup_aegis)

    apply_patches()

    mc = ctx.inject(Mecha)

    mc.spec.parsers.update(get_parsers(mc.spec.parsers))
    mc.serialize.extend(CommandSerializer(spec=mc.spec))
    mc.steps.insert(0, MacroMutator())

    runtime = ctx.inject(Runtime)

    runtime.modules.codegen.extend(MacroCodegen())
    runtime.helpers[ast_to_macro.__name__] = ast_to_macro
    runtime.helpers[make_macro_string.__name__] = make_macro_string

    for conversion, node_type in conversions.items():
        runtime.helpers[conversion] = MacroConverter(
            runtime.helpers[conversion], node_type
        )
