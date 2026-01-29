from typing import List, Optional
import pandas as pd
import scipy.stats as sps
from scipy.stats import chi2
import numpy as np

from aboba.base import BaseTest, TestResult


class BartletIndependentTest(BaseTest):
    """
    Performs Bartlett's test to check if groups have equal variance.

    Attributes:
        value_column (str): Name of the column containing the values to test.
    """
    def __init__(
        self,
        value_column="target",
    ):
        """
        Bartlett's test for equal variances across multiple groups.
        
        This test checks the null hypothesis that all input samples are from populations
        with equal variances. It is commonly used before performing ANOVA to verify
        the assumption of homoscedasticity.
        
        Args:
            value_column (str): Name of the column containing the values to test.
        
        Examples:
            ```python
            import pandas as pd
            import numpy as np
            from aboba.tests.multiple.bartlet import BartletIndependentTest

            # Create sample data with equal variances
            np.random.seed(42)
            group1 = pd.DataFrame({'target': np.random.normal(10, 2, 50)})
            group2 = pd.DataFrame({'target': np.random.normal(12, 2, 50)})
            group3 = pd.DataFrame({'target': np.random.normal(11, 2, 50)})

            # Perform the test
            test = BartletIndependentTest(value_column='target')
            result = test.test([group1, group2, group3], {})
            print(f"P-value: {result.pvalue:.4f}")

            # Create data with unequal variances
            group1_unequal = pd.DataFrame({'target': np.random.normal(10, 1, 50)})
            group2_unequal = pd.DataFrame({'target': np.random.normal(12, 3, 50)})
            group3_unequal = pd.DataFrame({'target': np.random.normal(11, 2, 50)})

            result_unequal = test.test([group1_unequal, group2_unequal, group3_unequal], {})
            print(f"P-value (unequal variances): {result_unequal.pvalue:.4f}")
            ```
        """
        super().__init__()
        self.value_column = value_column

    def test(self, groups: List[pd.DataFrame], artefacts) -> TestResult:
        """
        Perform Bartlett's test for equal variances.
        
        Args:
            groups (List[pd.DataFrame]): List of DataFrames representing the groups to compare.
            artefacts (dict): Dictionary to store additional results.
            
        Returns:
            TestResult: Object containing the p-value.
        """
        
        xs = [g[self.value_column].to_numpy() for g in groups]

        k = len(xs)
        ns = np.array([len(x) for x in xs], dtype=float)
        vars_ = np.array([x.var(ddof=1) for x in xs], dtype=float)

        n_total = ns.sum()

        pooled_var = np.sum((ns - 1) * vars_) / (n_total - k)

        numerator = (
            (n_total - k) * np.log(pooled_var)
            - np.sum((ns - 1) * np.log(vars_))
        )

        correction = 1.0 + (1.0 / (3 * (k - 1))) * (
            np.sum(1.0 / (ns - 1)) - 1.0 / (n_total - k)
        )

        chi2_stat = numerator / correction
        df = k - 1

        pvalue = chi2.sf(chi2_stat, df)

        return TestResult(
            pvalue=pvalue          
        )


class BartletIndependentTest_sps(BaseTest):
    def __init__(
        self,
        value_column="target",
    ):
        super().__init__()
        self.value_column = value_column

    def test(self, groups: List[pd.DataFrame], artefacts) -> TestResult:
        result = sps.bartlett(*[group[self.value_column] for group in groups])
        return TestResult(pvalue=result.pvalue)
