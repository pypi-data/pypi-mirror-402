from typing import List, Dict, Union, Callable

import pandas as pd

from aboba.base import AbobaBase


class BaseDataSampler(AbobaBase):
    def __call__(self, data: pd.DataFrame, artifacts: Dict) -> List[pd.DataFrame]:
        return self.sample(data, artifacts)

    def sample(self, data: pd.DataFrame, artifacts: Dict) -> List[pd.DataFrame]:
        """

        Sample ABn groups from dataframe

        Args:
            data (pd.DataFrame): dataframe with data
            artifacts (dict): artifacts retrieved after preprocessing step

        Returns:
            List[pd.DataFrame]: dataframes (possibly views) for each group
        """
        raise NotImplemented

    def fit(self, data: pd.DataFrame):
        """

        Full dataset *after* processing is passed to calculate statistics
        for correct sampling during the actual testing. If dataset is generated,
        nothing is passed on the .fit() stage of a Test

        """

        pass


DataSampler = Union[BaseDataSampler, Callable[[pd.DataFrame, Dict], List[pd.DataFrame]]]
