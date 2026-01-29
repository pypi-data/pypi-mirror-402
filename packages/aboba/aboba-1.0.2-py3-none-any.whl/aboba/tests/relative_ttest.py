from typing import List, Optional
import pandas as pd
import numpy as np
import scipy.stats as sps

from aboba.base import BaseTest, TestResult


class RelativeIndependentTTest(BaseTest):
    """
    Performs an independent t-test using a ratio-based measure for effect size relative
    to the control group.

    Attributes:
        value_column (str): Name of the column containing the values to test.
        alternative (str): Defines the alternative hypothesis. Must be one of
            {'two-sided', 'less', 'greater'}.
        alpha (float), default=0.05:  Significance level for confidence intervals
    """
    
    def __init__(
        self,
        value_column="target",
        alternative="two-sided",
        alpha = 0.05 
    ):
        """
        Independent t-test for relative difference between two groups.
        
        This test compares the means of two independent groups to determine if there
        is a statistically significant relative difference between them. The relative
        difference is calculated as (test_mean - control_mean) / control_mean.
        
        Args:
            value_column (str): Name of the column containing the values to test.
            alternative (str): Defines the alternative hypothesis. Options are:
                'two-sided' (default), 'less', or 'greater'.
        
        Examples:
            ```python
            import pandas as pd
            import numpy as np
            from aboba.tests.relative_ttest import RelativeIndependentTTest

            # Create sample data
            np.random.seed(42)
            control = pd.DataFrame({'target': np.random.normal(100, 10, 100)})
            test = pd.DataFrame({'target': np.random.normal(105, 10, 100)})  # 5% increase

            # Perform the test
            test_instance = RelativeIndependentTTest(value_column='target')
            result = test_instance.test([control, test], {})
            print(f"P-value: {result.pvalue:.4f}")
            print(f"Relative Effect: {result.effect:.4f}")
            ```
        """
        super().__init__()
        self.value_column = value_column
        self.alternative = alternative
        self.alpha = alpha
        assert alternative in {"two-sided", "less", "greater"}

    def test(self, groups: List[pd.DataFrame], artefacts) -> TestResult:
        """
        Perform the relative independent t-test on the provided groups.
        
        Args:
            groups (List[pd.DataFrame]): List of two DataFrames representing the groups to compare.
                The first group is treated as the control group, the second as the test group.
            artefacts (dict): Dictionary to store additional results.
            
        Returns:
            TestResult: Object containing the p-value and relative effect size.
        """
        control_group, test_group = groups

        Y, X = control_group[self.value_column], test_group[self.value_column]
        var_1, var_2 = np.var(X, ddof=1), np.var(Y, ddof=1)
        a_1, a_2 = np.mean(X), np.mean(Y)
        R = (a_1 - a_2) / a_2
        var_R = var_1 / (a_2**2) + (a_1**2) / (a_2**4) * var_2
        n = len(test_group)
        stat = np.sqrt(n) * R / np.sqrt(var_R)

        if self.alternative == "two-sided":
            pvalue = 2 * min(sps.norm.cdf(stat), sps.norm.sf(stat))
            pvalue = min(pvalue, 1)
        elif self.alternative == "less":
            pvalue = sps.norm.cdf(stat)
        elif self.alternative == "greater":
            pvalue = sps.norm.sf(stat)
        else:
            assert False

        q = sps.norm.ppf(1 - self.alpha/2)
        left_bound, right_bound  = (R - q*np.sqrt(var_R), R + q*np.sqrt(var_R))

        return TestResult(pvalue=pvalue, effect=R, effect_type="relative_control", effect_interval = (left_bound, right_bound))
