from typing import List, Optional
import pandas as pd
import scipy.stats as sps
import numpy as np
from scipy.stats import chi2

from aboba.base import BaseTest, TestResult


class KruskalIndependentTest(BaseTest):
    """
    Performs a Kruskal-Wallis H-test for multiple independent samples, a non-parametric
    alternative to one-way ANOVA.

    Attributes:
        value_column (str): Name of the column containing the values to test.
    """

    def __init__(
        self,
        value_column="target",
    ):
        """
        Kruskal-Wallis H-test for comparing distributions between independent groups.
        
        This non-parametric test compares the distributions of two or more independent
        groups to determine if they come from the same distribution. It's an alternative
        to one-way ANOVA when the assumptions of normality are not met.
        
        Args:
            value_column (str): Name of the column containing the values to test.
        
        Examples:
            ```python
            import pandas as pd
            import numpy as np
            from aboba.tests.multiple.kruskal import KruskalIndependentTest

            # Create sample non-normal data
            np.random.seed(42)
            group1 = pd.DataFrame({'target': np.random.exponential(2, 50)})
            group2 = pd.DataFrame({'target': np.random.exponential(3, 50)})
            group3 = pd.DataFrame({'target': np.random.exponential(2.5, 50)})

            # Perform the test
            test = KruskalIndependentTest(value_column='target')
            result = test.test([group1, group2, group3], {})
            print(f"P-value: {result.pvalue:.4f}")
            ```
        """
        super().__init__()
        self.value_column = value_column

    @staticmethod
    def average_ranks(x: np.ndarray):
        """
        Average ranks with tie counts (for tie correction).
        """
        order = np.argsort(x, kind="mergesort")
        xs = x[order]
        N = xs.size

        ranks_sorted = np.empty(N, dtype=float)
        tie_counts = []

        i = 0
        while i < N:
            j = i + 1
            while j < N and xs[j] == xs[i]:
                j += 1

            midrank = 0.5 * ((i + 1) + j)
            ranks_sorted[i:j] = midrank

            cnt = j - i
            if cnt >= 2:
                tie_counts.append(cnt)

            i = j

        ranks = np.empty(N, dtype=float)
        ranks[order] = ranks_sorted
        return ranks, np.asarray(tie_counts, dtype=float)

    def test(self, groups: List[pd.DataFrame], artefacts=None) -> TestResult:
        """
        Executes the Kruskal-Wallis H-test on the provided groups.

        Args:
            groups (List[pd.DataFrame]): A list of DataFrames, each representing a group/sample.
            artefacts (dict): A dictionary for storing or retrieving additional test information.

        Returns:
            TestResult: A `TestResult` object containing the p-value from the Kruskal-Wallis test.
        """

        samples = [
            pd.to_numeric(g[self.value_column], errors="coerce")
              .dropna()
              .to_numpy()
            for g in groups
        ]

        k = len(samples)
        if k < 2:
            raise ValueError("Kruskal–Wallis test requires at least two groups.")

        ns = np.array([s.size for s in samples], dtype=int)
        if np.any(ns < 1):
            raise ValueError("All groups must contain at least one observation.")

        x = np.concatenate(samples)
        N = x.size

        ranks, tie_counts = self.average_ranks(x)

        if N > 1 and tie_counts.size > 0:
            gamma = 1.0 - np.sum(tie_counts**3 - tie_counts) / (N**3 - N)
        else:
            gamma = 1.0

        R_bar = (N + 1) / 2.0

        idx = 0
        sum_term = 0.0
        for n in ns:
            Rj = ranks[idx:idx + n].mean()
            sum_term += n * (Rj - R_bar) ** 2
            idx += n

        W = (12.0 / (N * (N + 1))) * sum_term
        W /= gamma

        pvalue = chi2.sf(W, df=k - 1)
        return TestResult(pvalue=float(pvalue))


class KruskalIndependentTest_sps(BaseTest):
    def __init__(
        self,
        value_column="target",
    ):
        super().__init__()
        self.value_column = value_column

    def test(self, groups: List[pd.DataFrame], artefacts) -> TestResult:
        result = sps.kruskal(*[group[self.value_column] for group in groups])
        return TestResult(pvalue=result.pvalue)

