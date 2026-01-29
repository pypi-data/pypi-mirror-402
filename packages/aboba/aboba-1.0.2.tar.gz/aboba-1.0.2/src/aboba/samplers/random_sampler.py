from typing import List

import pandas as pd

from aboba.base import BaseDataSampler
import numpy as np


class RandomSampler(BaseDataSampler):
    """
    Sample random groups from data.
    
    This sampler randomly selects specified numbers of observations from the data
    to form multiple groups. Each observation can only be selected once across
    all groups.
    
    Examples:
        ```python
        import pandas as pd
        import numpy as np
        from aboba.samplers.random_sampler import RandomSampler

        # Create sample data
        np.random.seed(42)
        data = pd.DataFrame({
            'value': np.random.normal(0, 1, 100)
        })

        # Sample 2 groups of 30 observations each
        sampler = RandomSampler(size=30, groups_n=2)
        samples = sampler.sample(data, {})
        print(f"Number of groups: {len(samples)}")
        print(f"Size of each group: {[len(sample) for sample in samples]}")
        # Check that no observation appears in both groups
        intersection = set(samples[0].index).intersection(set(samples[1].index))
        print(f"Number of shared observations: {len(intersection)}")
        ```
    """

    def __init__(self, size: int, groups_n: int = 2):
        """
        Initialize the RandomSampler.
        
        Args:
            size (int): Number of observations to sample for each group.
            groups_n (int): Number of groups to create. Default is 2.
        """
        self.size = size
        self.groups_n = groups_n

        assert groups_n >= 1
        assert size >= 1

    def sample(self, data: pd.DataFrame, _: dict) -> List[pd.DataFrame]:
        """
        Sample random groups from data.
        
        Args:
            data (pd.DataFrame): DataFrame to sample from.
            _: dict: Dictionary to store additional results (not used in this sampler).
            
        Returns:
            List[pd.DataFrame]: List of DataFrames, one for each group.
        """
        assert len(data.index) >= self.size

        left_index = set(list(data.index))
        result = []

        for _ in range(self.groups_n):
            group = list(
                np.random.choice(list(left_index), size=self.size, replace=False)
            )
            left_index = left_index.difference(group)
            result.append(group)

        return [data.loc[group] for group in result]
