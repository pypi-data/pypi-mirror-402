from typing import Union, Callable

import pandas as pd

from aboba.base import AbobaBase


class BaseDataSource(AbobaBase):
    """

    Defines source of data

    """

    def get(self) -> pd.DataFrame:
        """

        Returns data

        """
        raise NotImplemented

    def is_generated(self) -> bool:
        """

        Tells if data is generated.
        If it is not generated, then data processing can be cached

        """
        raise NotImplemented

    def __call__(self) -> pd.DataFrame:
        return self.get()


DataSource = Union[pd.DataFrame, BaseDataSource, Callable[[], pd.DataFrame]]
