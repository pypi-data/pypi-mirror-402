from typing import List, Union, Callable

import pandas as pd

from aboba.base import AbobaBase


class BaseEffectModifier(AbobaBase):
    """

    Base class for effect modification.

    """

    def add_effect(self, groups: List[pd.DataFrame]) -> List[pd.DataFrame]:
        """

        Receives all groups and must return the same number of groups

        """
        raise NotImplemented

    def __call__(self, groups: List[pd.DataFrame]) -> List[pd.DataFrame]:
        return self.add_effect(groups)


EffectModifier = Union[
    BaseEffectModifier, Callable[[List[pd.DataFrame]], List[pd.DataFrame]]
]
