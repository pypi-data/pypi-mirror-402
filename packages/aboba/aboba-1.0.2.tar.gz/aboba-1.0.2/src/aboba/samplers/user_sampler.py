import pandas as pd
import numpy as np
from typing import Optional, List

from aboba.base import BaseDataSampler
from aboba.samplers.random_sampler import RandomSampler


class UserSampler(BaseDataSampler):
    """
     A sampler that creates experimental groups by randomly selecting unique users from each group  

     Attributes:
        group_column (str): Column name that defines the original grouping (e.g., 'group' for control/treatment)
        user_column (str): Column name containing unique user identifiers (default: 'user_id')
        size (Optional[int]): Number of unique users to sample in each group. If None, returns all users

    """

    def __init__(self, group_column: str = "group", user_column:str = "user_id", size: Optional[int] = None):
        self.group_column = group_column        
        self.user_column = user_column
        self.size = size 


    def sample(self, data: pd.DataFrame, artefacts: dict) -> List[pd.DataFrame]:
        assert self.group_column in data.columns # "Sampling column must be in data.columns"        
        grouped_data = list(data.groupby(by=self.group_column, sort=True))

        if self.size is None:
            return [df for _, df in grouped_data]
        
        res = [
            group_df[group_df[self.user_column].isin(
                np.random.choice(group_df[self.user_column].unique(), size=self.size, replace=False)
            )]
            for _, group_df in grouped_data
        ]

        return [
            group_df[group_df[self.user_column].isin(
                np.random.choice(group_df[self.user_column].unique(), size=self.size, replace=False)
            )]
            for _, group_df in grouped_data
        ]