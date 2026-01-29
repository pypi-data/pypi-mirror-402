from typing import Optional, List
from pydantic import (
    BaseModel,
    Field,
    model_validator,
)

from saboteur.domain.mutation.strategies import MutationStrategy


class MutationConfig(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    
    strategies: List[MutationStrategy] = Field(default_factory=list, description="List of mutation strategies to be used.")
    apply_all_strategies: bool = Field(default=True, description="Flag to determine if all applicable strategies should be applied.")
    num_strategies_to_apply: Optional[int] = Field(default=None, description="Number of strategies to apply randomly if not applying all.")
    
    @model_validator(mode="after")
    def validate_strategy_counts(self):
        if self.apply_all_strategies:
            assert self.num_strategies_to_apply is None, (
                "num_strategies_to_apply should be None when apply_all_strategies is True."
            )
        else:
            assert self.num_strategies_to_apply is not None or self.num_strategies_to_apply > 0, (
                "num_strategies_to_apply should be a positive integer or not None when apply_all_strategies is False."
            )
        return self