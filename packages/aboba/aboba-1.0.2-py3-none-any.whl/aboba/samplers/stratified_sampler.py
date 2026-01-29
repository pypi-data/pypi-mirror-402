import pandas as pd
from typing import Optional, List

from aboba.base import BaseDataSampler
from .group_sampler import GroupSampler


class StratifiedGroupSampler(BaseDataSampler):
    """
    Sample groups with stratification.
    
    This sampler performs stratified sampling by dividing the data into strata
    based on specified columns, then sampling from each stratum to ensure
    proportional representation across groups.
    
    Examples:
        ```python
        import pandas as pd
        import numpy as np
        from aboba.samplers.stratified_sampler import StratifiedGroupSampler

        # Create sample data with strata
        np.random.seed(42)
        data = pd.DataFrame({
            'group': ['A'] * 200 + ['B'] * 200,
            'stratum': ['X'] * 100 + ['Y'] * 100 + ['X'] * 100 + ['Y'] * 100,
            'value': np.random.normal(0, 1, 400)
        })

        # Sample 50 observations from each group, maintaining strata proportions
        sampler = StratifiedGroupSampler(
            group_column='group',
            size=50,
            strata_columns=['stratum']
        )
        sampler.fit(data)  # Fit to calculate strata weights
        samples = sampler.sample(data, {})
        print(f"Number of groups: {len(samples)}")
        print(f"Size of each group: {[len(sample) for sample in samples]}")
        ```
    """

    def __init__(
        self,
        group_column: str,
        size: int,
        strata_columns: Optional[List[str]] = None,
        sample_time_weights: bool = False,
    ):
        """
        Initialize the StratifiedGroupSampler.
        
        Specified column is used to group dataframe, then size is used to sample
        from each group while maintaining stratification.
        
        Args:
            group_column (str): Name of the column to group by.
            size (int): Target size for each group before applying stratification.
            strata_columns (Optional[List[str]]): List of columns to stratify by.
            sample_time_weights (bool): Whether to refit strata weights during sampling.
                If False, weights are calculated during fit() and remain fixed.
        """
        self.size = size
        self.group_column = group_column

        self.strata_columns = strata_columns
        if strata_columns is not None and len(strata_columns) == 1:
            self.strata_columns = strata_columns[0]

        self.sample_time_weights = sample_time_weights
        self.strata_weights = None
        self.strata_sizes = None

    def fit(self, data: pd.DataFrame):
        """
        Fit the sampler on the data to calculate strata weights.
        
        Args:
            data (pd.DataFrame): DataFrame to fit on.
        """
        self._assert_strata_columns_in_data(data)
        self._set_strata_weights(data)

    def sample(self, data: pd.DataFrame, artefacts: dict) -> List[pd.DataFrame]:
        """
        Sample data using stratified sampling.
        
        Args:
            data (pd.DataFrame): DataFrame to sample from.
            artefacts (dict): Dictionary to store additional results.
            
        Returns:
            List[pd.DataFrame]: List of DataFrames, one for each group.
        """
        self._assert_strata_columns_in_data(data)

        if self.sample_time_weights:
            self._set_strata_weights(data)

        if self.strata_weights is None or self.strata_sizes is None:
            raise RuntimeError(
                "StratifedGroupSampler must be fitted before sampling without sample_time_weights=True"
            )

        strata_result = []
        for i, (_, strata_df) in enumerate(
            data.groupby(by=self.strata_columns, sort=True)
        ):
            if not self.strata_sizes[i]:
                # TODO warning
                continue
            group_sampler = GroupSampler(
                column=self.group_column, size=self.strata_sizes[i]
            )
            strata_result.append(group_sampler.sample(strata_df, artefacts))

        result = [pd.DataFrame() for _ in range(len(strata_result[0]))]
        for strata in strata_result:
            for i, grouped in enumerate(strata):
                result[i] = pd.concat([result[i], grouped])

        return result

    def _set_strata_weights(self, data: pd.DataFrame):
        strata_weights = data.groupby(by=self.strata_columns).count().iloc[:, 0].values

        self.strata_weights = strata_weights / strata_weights.sum()
        self.strata_sizes = (self.strata_weights * self.size + 0.5).astype(int)

    def _assert_strata_columns_in_data(self, data: pd.DataFrame):
        assert self.strata_columns is not None, "Strata columns must be specified"

        if isinstance(self.strata_columns, str):
            assert (
                self.strata_columns in data.columns
            ), f"Strata column '{self.strata_columns}' not in data"
        else:
            for column in self.strata_columns:
                assert column in data.columns, f"Strata column '{column}' not in data"

