from typing import List, Optional
import numpy as np
import pandas as pd
import scipy.stats as sps

from aboba.base import BaseTest, BaseDataProcessor, DataSampler, TestResult
from aboba.samplers import StratifiedGroupSampler, GroupSampler


class StratifiedTTest(BaseTest):
    def __init__(
        self,
        group_column: str,
        group_size: int,
        method: str,
        strata_columns: List[str],
        col_name: str = "target",
        alpha: float = 0.05 
    ):
        """
        Performs a stratified t-test on the data.
        
        This test performs a t-test while accounting for stratification in the data.
        The test decides what sampler to use based on the method passed.
        
        Args:
            group_column (str): Name of the column containing group identifiers.
            group_size (int): Size of groups to sample.
            method (str): Sampling method. One of 'random', 'stratified', 'post_stratified'.
            strata_columns (List[str]): List of columns to stratify by.
            col_name (str): Name of the column to test.
        
        Examples:
            ```python
            import pandas as pd
            import numpy as np
            from aboba.tests.stratified_ttest import StratifiedTTest

            # Create sample stratified data
            np.random.seed(42)
            data = pd.DataFrame({
                'group': np.repeat(['A', 'B'], 100),
                'strata': np.tile(['X', 'Y'], 100),
                'target': np.concatenate([
                    np.random.normal(10, 2, 100),
                    np.random.normal(12, 2, 100)
                ])
            })

            # Create test instance
            test = StratifiedTTest(
                group_column='group',
                group_size=50,
                method='stratified',
                strata_columns=['strata'],
                col_name='target'
            )

            # Fit and test
            test.fit(data)
            groups = [data[data['group'] == 'A'], data[data['group'] == 'B']]
            result = test.test(groups, {})
            print(f"P-value: {result.pvalue:.4f}")
            print(f"Effect: {result.effect:.4f}")
            ```
        """

        raise NotImplementedError("")

        assert method in [
            "random",
            "stratified",
            "post_stratified",
        ], f"Invalid {method = }. Must be one of 'random', 'stratified', 'post_stratified'"
        assert len(strata_columns) > 0, "Must have at least one strata column"

        if method in ["random", "post_stratified"]:
            data_sampler = GroupSampler(column=group_column, size=group_size)
        elif method == "stratified":
            data_sampler = StratifiedGroupSampler(
                group_column=group_column,
                strata_columns=strata_columns,
                size=group_size,
            )
        else:
            raise RuntimeError(f"Unsupported {method = }")

        super().__init__(preprocess, data_sampler)
        self.col_name = col_name
        self.method = method
        self.strata_columns = strata_columns
        self.strata_weights = None
        self.alpha = alpha

    def fit(self, data: pd.DataFrame):
        """
        Fit the test on the provided data.
        
        Args:
            data (pd.DataFrame): DataFrame containing the data to fit on.
            
        Returns:
            self: Returns the instance for method chaining.
        """
        super().fit(data)
        self.strata_weights = self._calculate_strata_weights(self._cache.data)
        return self

    def test(self, groups: List[pd.DataFrame], artefacts) -> TestResult:
        """
        Perform the stratified t-test on the provided groups.
        
        Args:
            groups (List[pd.DataFrame]): List of two DataFrames representing the groups to compare.
            artefacts (dict): Dictionary to store additional results.
            
        Returns:
            TestResult: Object containing the p-value and effect size.
        """
        assert len(groups) == 2

        if self.method == "random":
            mean_function = self._simple_mean
            var_function = self._simple_var
        elif self.method == "stratified":
            mean_function = self._weighted_mean
            var_function = self._weighted_var
        elif self.method == "post_stratified":
            mean_function = self._weighted_mean
            var_function = self._weighted_post_var
        else:
            raise RuntimeError(f"method not supported {self.method = }")

        assert len(groups) == 2

        x_mean = mean_function(groups[0])
        y_mean = mean_function(groups[1])
        x_var = var_function(groups[0])
        y_var = var_function(groups[1])

        effect = x_mean - y_mean
        std = np.sqrt(x_var + y_var)
        t_stat = effect / std
        pvalue = 2 * sps.norm.sf(np.abs(t_stat))
        q = sps.norm.ppf(1 - self.alpha/2)
        left_bound, right_bound = (effect - q*std, effect + q*std)

        return TestResult(pvalue, effect,  effect_interval = (left_bound, right_bound))

    def _calculate_strata_weights(self, data):
        strata_weights = data.groupby(by=self.strata_columns)[self.col_name].count()
        strata_weights = strata_weights / strata_weights.sum()
        return strata_weights

    def _weighted_mean(self, data):
        strata_means = data.groupby(by=self.strata_columns)[self.col_name].mean()
        return (strata_means * self.strata_weights).sum()

    def _weighted_var(self, data):
        strata_vars = data.groupby(by=self.strata_columns)[self.col_name].var()
        return (strata_vars * self.strata_weights).sum() / len(data)

    def _weighted_post_var(self, data):
        strata_vars = data.groupby(by=self.strata_columns)[self.col_name].var()
        weighted_var = (strata_vars * self.strata_weights).sum() / len(data)
        post_addition = (strata_vars * (1 - self.strata_weights)).sum() / (
            len(data) ** 2
        )
        return weighted_var + post_addition

    def _simple_mean(self, data):
        return data[self.col_name].mean()

    def _simple_var(self, data):
        return data[self.col_name].var() / len(data)
