import pandas as pd
import numpy as np
from typing import Optional, List

from aboba.base import BaseDataSampler
from aboba.samplers.random_sampler import RandomSampler


class GroupSampler(BaseDataSampler):
    """
    Sample specified size from each group specified by column.
    
    This sampler groups data by a specified column and then samples a specified
    number of observations from each group. Groups are sorted by group name.
    
    Examples:
        ```python
        import pandas as pd
        import numpy as np
        from aboba.samplers.group_sampler import GroupSampler

        # Create sample data with groups
        np.random.seed(42)
        data = pd.DataFrame({
            'group': ['A'] * 100 + ['B'] * 100,
            'value': np.random.normal(0, 1, 200)
        })

        # Sample 50 observations from each group
        sampler = GroupSampler(column='group', size=50)
        samples = sampler.sample(data, {})
        print(f"Number of groups: {len(samples)}")
        print(f"Size of each group: {[len(sample) for sample in samples]}")
        ```
    """

    def __init__(self, column: str, size: Optional[int] = None, related: bool = False):
        """
        Initialize the GroupSampler.
        
        Specified column is used to group dataframe, then size is used to sample
        from each group.
        
        Args:
            column (str): Name of the column to group by.
            size (Optional[int]): Number of observations to sample from each group.
                If None, the whole group is returned.
            related (bool): If True, samples the same indexes from each group to
                generate related sets. All groups must be of the same size when
                related is True.
        """
        self.size = size
        self.column = column
        self.related = related
        self.random_sampler = (
            RandomSampler(size=size, groups_n=1) if size is not None else None
        )

    def sample(self, data: pd.DataFrame, artefacts: dict) -> List[pd.DataFrame]:
        """
        Sample data from each group.
        
        Args:
            data (pd.DataFrame): DataFrame to sample from.
            artefacts (dict): Dictionary to store additional results.
            
        Returns:
            List[pd.DataFrame]: List of DataFrames, one for each group.
        """
        assert self.column in data.columns, "Sampling column must be in data.columns"

        groupped = list(data.groupby(by=self.column, sort=True))

        if self.size is None:
            return [df for _, df in groupped]
        assert self.random_sampler is not None

        if self.related:
            size_all = len(groupped[0][1])
            assert all(
                size_all == len(df) for i, df in groupped
            ), "Groups must be of the same size when related is True"
            sampled_indexes = np.random.choice(np.arange(size_all), size=self.size)
            return [df.iloc[sampled_indexes] for _, df in groupped]

        return [self.random_sampler.sample(df, artefacts)[0] for _, df in groupped]
