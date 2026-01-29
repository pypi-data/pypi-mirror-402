from typing import List, Optional
import pandas as pd
import numpy as np
import scipy.stats as sps
from scipy.stats import studentized_range, chi2

from aboba.base import BaseTest, TestResult


class HSDTukeyTest(BaseTest):
    """
    Performs Tukey's HSD (honestly significant difference) test for multiple
    comparison of group means.

    Attributes:
        value_column (str): Name of the column containing the values to test.
    """
    def __init__(
        self,
        value_column="target",
    ):
        """
        Tukey's Honestly Significant Difference (HSD) test for multiple comparisons.
        
        This post-hoc test is used to find means that are significantly different
        from each other after an ANOVA test indicates significant differences exist.
        It controls the family-wise error rate.
        
        Args:
            value_column (str): Name of the column containing the values to test.
        
        Examples:
            ```python
            import pandas as pd
            import numpy as np
            from aboba.tests.multiple.hsd import HSDTukeyTest

            # Create sample data with three groups
            np.random.seed(42)
            group1 = pd.DataFrame({'target': np.random.normal(10, 2, 50)})
            group2 = pd.DataFrame({'target': np.random.normal(12, 2, 50)})
            group3 = pd.DataFrame({'target': np.random.normal(11, 2, 50)})

            # Perform the test
            test = HSDTukeyTest(value_column='target')
            result = test.test([group1, group2, group3], {})
            print(f"Minimum p-value: {result.pvalue:.4f}")
            ```
        """
        super().__init__()
        self.value_column = value_column

        raise NotImplementedError("")

    def test(self, groups: List[pd.DataFrame], artefacts) -> TestResult:
        """
        Perform Tukey's HSD test for multiple comparisons.
        
        Args:
            groups (List[pd.DataFrame]): List of DataFrames representing the groups to compare.
            artefacts (dict): Dictionary to store additional results.
            
        Returns:
            TestResult: Object containing the minimum p-value from all pairwise comparisons.
        """

        k = len(groups)
        if k < 2:
            raise ValueError("Tukey HSD requires at least two groups.")

        samples = [
            pd.to_numeric(g[self.value_column], errors="coerce")
              .dropna()
              .to_numpy()
            for g in groups
                  ]

        ns = np.array([x.size for x in samples])
        means = np.array([x.mean() for x in samples])

        N = ns.sum()
        df = N - k

        sse = sum(((x - m) ** 2).sum() for x, m in zip(samples, means))
        mse = sse / df

        min_p = 1.0
        for i in range(k):
            for j in range(i + 1, k):
                se = np.sqrt((mse / 2.0) * (1.0 / ns[i] + 1.0 / ns[j]))
                if se == 0:
                    continue
                q = abs(means[i] - means[j]) / se
                p = studentized_range.sf(q, k, df)
                if p < min_p:
                    min_p = p

        return TestResult(pvalue=float(min_p))


class HSDTukeyTest_sps(BaseTest):
    def __init__(
        self,
        value_column="target",
    ):
        super().__init__()
        self.value_column = value_column

        raise NotImplementedError("")

    def test(self, groups: List[pd.DataFrame], artefacts) -> TestResult:
        result = sps.tukey_hsd(*[group[self.value_column] for group in groups])
        return TestResult(pvalue=min(result.pvalue))
