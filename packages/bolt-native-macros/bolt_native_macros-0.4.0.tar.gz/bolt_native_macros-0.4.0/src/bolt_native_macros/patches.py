from typing import Any

from nbtlib import Serializer as NbtSerializer

from .serialize import serialize_macro
from .typing import MacroTag


def apply_patches():
    NbtSerializer.serialize_macro = serialize_macro  # type: ignore

    try:
        import bolt_expressions.typing

        convert_tag = bolt_expressions.typing.convert_tag

        def convert_tag_with_macro(value: Any):
            match value:
                case MacroTag():
                    return value
                case _:
                    return convert_tag(value)

        bolt_expressions.typing.convert_tag = convert_tag_with_macro

    except ImportError:
        ...
