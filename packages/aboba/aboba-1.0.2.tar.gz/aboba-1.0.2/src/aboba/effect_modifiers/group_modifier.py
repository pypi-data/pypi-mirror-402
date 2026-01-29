import operator
from typing import Any, Callable, Dict, Optional, Tuple, Union, List
from numbers import Number

import pandas as pd
import numpy as np
from scipy.stats._distn_infrastructure import rv_frozen
from aboba.base.base_effect_modifier import BaseEffectModifier


class GroupModifier(BaseEffectModifier):
    """
    Adds constant or random effect to a column, specified by group.

    If the effect is:
      - a float: it is added directly
      - an rv_frozen: random values are sampled once per row
      - an np.random.RandomState / np.random.Generator: random values are drawn once per row
      - a callable (not one of the above): row-wise .apply(effect, axis=1) is used
    """

    def __init__(
        self,
        effects: Dict[Any, Union[float, Callable, rv_frozen, np.random.RandomState, np.random.Generator]],
        value_column: str = "value",
        group_column: str = "group",
        method: Callable[[Any, Any], Any] = operator.add
    ):
        """
        Args:
            effects (Dict[any, ...]): dict of effects for each value in `group_column`.
                                      May be float, callable, rv_frozen, or a NumPy random generator.
            value_column (str): which column to modify
            group_column (str): which column to group by
            method (Callable[[Any, Any], Any]): operator to use, e.g., operator.add, operator.mul, ...
        """
        self.effects = effects
        self.value_column = value_column
        self.group_column = group_column
        self.method = method

    def add_effect(self, groups: List[pd.DataFrame]) -> List[pd.DataFrame]:
        for effect_group, effect in self.effects.items():
            for group in groups:
                mask = group[self.group_column] == effect_group

                if (
                    isinstance(effect, Number)
                    or isinstance(effect, rv_frozen)
                    or isinstance(effect, np.random.RandomState)
                    or isinstance(effect, np.random.Generator)
                ):
                    value = group.loc[mask, self.value_column]
                    effect_val = self._evaluate_effect(effect, value)
                    group.loc[mask, self.value_column] = self.method(value, effect_val)
                elif callable(effect):
                    group.loc[mask] = group.loc[mask].apply(effect, axis=1)
                else:
                    raise ValueError(f"Unknown effect type: {type(effect)}")
        return groups

    def _evaluate_effect(self, effect: Union[float, rv_frozen, np.random.RandomState, np.random.Generator],
                         value: pd.Series) -> Union[float, np.ndarray]:
        """
        Return either a float or an array of appropriate size, depending on effect type.
        """
        if isinstance(effect, Number):
            return effect
        elif isinstance(effect, rv_frozen):
            return effect.rvs(size=value.size)
        elif isinstance(effect, np.random.RandomState):
            # Older numpy version
            return effect.random(size=value.size)
        elif isinstance(effect, np.random.Generator):
            # Newer numpy version
            return effect.random(size=value.size)
        else:
            raise ValueError(f"Unknown effect type in _evaluate_effect: {type(effect)}")
