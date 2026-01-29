from aegis_core.ast.features import AegisFeatureProviders
from aegis_core.ast.features.provider import SemanticsParams
from aegis_core.ast.features.provider import BaseFeatureProvider

from beet import Context

from .ast import AstMacroArgument


class MacroArgumentProvider(BaseFeatureProvider[AstMacroArgument]):
    @classmethod
    def semantics(cls, params: SemanticsParams[AstMacroArgument]):
        return [(params.node, "variable", "readonly")]

def setup_aegis(ctx: Context):
    providers = ctx.inject(AegisFeatureProviders)    
    providers.attach(AstMacroArgument, MacroArgumentProvider)