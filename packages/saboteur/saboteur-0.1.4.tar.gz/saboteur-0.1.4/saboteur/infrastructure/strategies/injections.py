from saboteur.domain.mutation.strategies import MutationStrategy
from saboteur.domain.mutation.contexts import MutationContext
from saboteur.utils.logging import logger


class NullInjectionStrategy(MutationStrategy):
    def is_applicable(self, context: MutationContext) -> bool:
        return context.original_value is not None

    def apply(self, context: MutationContext) -> MutationContext:
        logger.debug(
            f"NullInjectionStrategy replacing "
            f"{".".join(context.key_paths)}({context.original_value}) with None"
        )
        return MutationContext(
            key_paths=context.key_paths,
            original_value=None,
            original_type=type(None)
        )