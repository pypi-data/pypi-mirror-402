from aegis_core.ast.features import AegisFeatureProviders
from aegis_core.ast.features.provider import SemanticsParams, HoverParams
from aegis_core.ast.features.provider import BaseFeatureProvider
import lsprotocol.types as lsp

from beet import Context

from .ast import AstMacroArgument


class MacroArgumentProvider(BaseFeatureProvider[AstMacroArgument]):
    @classmethod
    def semantics(cls, params: SemanticsParams[AstMacroArgument]):
        return [(params.node, "variable", ["readonly"])]

    @classmethod
    def hover(cls, params: HoverParams[AstMacroArgument]) -> lsp.Hover:
        if params.node.parser == "string":
            value = f'"$({params.node.name})"'
        else:
            value = f"$({params.node.name})"

        return lsp.Hover(
            lsp.MarkupContent(
                kind=lsp.MarkupKind.Markdown, value=f"```python\n{value}\n```"
            )
        )


def setup_aegis(ctx: Context):
    providers = ctx.inject(AegisFeatureProviders)
    providers.attach(AstMacroArgument, MacroArgumentProvider)
