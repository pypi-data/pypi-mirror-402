import copy
import random

from typing import List, Dict, Any

from saboteur.domain.mutation.strategies import MutationStrategy
from saboteur.domain.mutation.contexts import MutationContext
from saboteur.domain.mutation.configs import MutationConfig
from saboteur.utils.sampling import uniform_sample_from_dict


class Saboteur:
    """Facade for the saboteur mutation framework."""
    
    def __init__(self, config: MutationConfig):
        self.__config = config
    
    def _get_applicable_strategies(self, context: MutationContext) -> List[MutationStrategy]:
        return [s for s in self.__config.strategies if s.is_applicable(context)]
    
    def _mutate(self, context: MutationContext) -> List[object]:
        mutated = []
        for strategy in self._get_applicable_strategies(context):
            mutated_value = strategy.apply(context)
            mutated.append(mutated_value)
        return mutated
    
    def _wrap_into_contexts(self, data: Dict[str, Any]) -> List[MutationContext]:
        key_paths, value = uniform_sample_from_dict(data)
        return [
            MutationContext(
                key_paths=key_paths,
                original_value=value,
                original_type=type(value)
            )
        ] 
    
    def attack(self, data: Dict[str, Any]) -> Dict[str, Any]:
        _data = copy.deepcopy(data)
        contexts = self._wrap_into_contexts(_data)
        
        for context in contexts:
            candidates = self._get_applicable_strategies(context)
            if not candidates:
                continue
            if self.__config.apply_all_strategies:
                for strategy in candidates:
                    mutated = strategy.apply(context)
                    _data = mutated.mutate(_data)
            else:
                strategies_to_apply = random.sample(
                    population=candidates,
                    k=self.__config.num_strategies_to_apply,
                )
                for strategy in strategies_to_apply:
                    mutated = strategy.apply(context)
                    _data = mutated.mutate(_data)

        return _data