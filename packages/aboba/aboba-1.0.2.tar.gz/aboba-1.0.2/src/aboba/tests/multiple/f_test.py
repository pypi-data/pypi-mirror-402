from typing import List, Optional
import pandas as pd
import numpy as np
import scipy.stats as sps

from aboba.base import BaseTest, BaseDataProcessor, DataSampler, TestResult


class FIndependentTest(BaseTest):
    """
    Performs a custom F-test (ANOVA-style) for comparing multiple independent groups.

    Attributes:
        value_column (str): Name of the column containing the values to test.
    """

    def __init__(
        self,
        value_column="target",
    ):
        """
        Independent F-test for comparing variances between groups.
        
        This test compares the variances of two or more independent groups to determine
        if there are statistically significant differences between them.
        
        Args:
            value_column (str): Name of the column containing the values to test.
        
        Examples:
            ```python
            import pandas as pd
            import numpy as np
            from aboba.tests.multiple.f_test import FIndependentTest

            # Create sample data
            np.random.seed(42)
            group1 = pd.DataFrame({'target': np.random.normal(10, 1, 50)})
            group2 = pd.DataFrame({'target': np.random.normal(10, 2, 50)})
            group3 = pd.DataFrame({'target': np.random.normal(10, 1.5, 50)})

            # Perform the test
            test = FIndependentTest(value_column='target')
            result = test.test([group1, group2, group3], {})
            print(f"P-value: {result.pvalue:.4f}")
            ```
        """
        super().__init__()
        self.value_column = value_column

    def test(self, groups: List[pd.DataFrame], artefacts) -> TestResult:
        """
        Perform the independent F-test on the provided groups.
        
        Args:
            groups (List[pd.DataFrame]): List of DataFrames representing the groups to compare.
            artefacts (dict): Dictionary to store additional results.
            
        Returns:
            TestResult: Object containing the p-value.
        """
        ns = list(map(len, groups))
        N = sum(ns)
        k = len(groups)

        X_dot_j = [group[self.value_column].sum() / len(group) for group in groups]

        X_sum = sum(group[self.value_column].sum() for group in groups) / N

        V_in = sum(
            ((group[self.value_column] - X_dot) ** 2).sum()
            for group, X_dot in zip(groups, X_dot_j)
        )

        V_out = sum(n_j * ((X_dot - X_sum) ** 2) for n_j, X_dot in zip(ns, X_dot_j))

        F_X = (V_out / (k - 1)) / (V_in / (N - k))
        distr = sps.f(dfn=k - 1, dfd=N - k)
        pvalue = distr.sf(F_X)

        return TestResult(pvalue=pvalue)


class FRelatedTest(BaseTest):
    """
    Performs a custom F-test for comparing multiple related (paired) groups,
    akin to repeated-measures ANOVA.

    Attributes:
        value_column (str): Name of the column containing the values to test.
    """

    def __init__(
        self,
        value_column="target",
    ):
        """
        Related (paired) F-test for comparing variances between groups.
        
        This test compares the variances of two or more related groups (repeated measures)
        to determine if there are statistically significant differences between them.
        
        Args:
            value_column (str): Name of the column containing the values to test.
        
        Examples:
            ```python
            import pandas as pd
            import numpy as np
            from aboba.tests.multiple.f_test import FRelatedTest

            # Create sample paired data
            np.random.seed(42)
            subjects = 30
            treatments = 3
            data = []
            for i in range(subjects):
                base = np.random.normal(10, 2)
                for j in range(treatments):
                    data.append({
                        'subject': i,
                        'treatment': j,
                        'target': base + np.random.normal(0, 0.5) + j * 0.5
                    })
            df = pd.DataFrame(data)

            # Split into groups
            groups = [df[df['treatment'] == i][['target']] for i in range(treatments)]

            # Perform the test
            test = FRelatedTest(value_column='target')
            result = test.test(groups, {})
            print(f"P-value: {result.pvalue:.4f}")
            ```
        """
        super().__init__()
        self.value_column = value_column

    def test(self, groups: List[pd.DataFrame], artefacts) -> TestResult:
        """
        Executes an F-test for multiple related groups by computing an overall
        between-group and within-subject variability measure.

        Args:
            groups (List[pd.DataFrame]): A list of DataFrames, each representing a group/sample.
            artefacts (dict): A dictionary for storing or retrieving additional test information.

        Returns:
            TestResult: A `TestResult` object containing the p-value from the computed F-test.
        """

        ns = list(map(len, groups))
        n = ns[0]

        k = len(groups)

        assert all(n == ns[0] for n in ns), "Groups must have the same size"

        X_dot_j = [group[self.value_column].sum() / len(group) for group in groups]
        X_i_dot = sum(group[self.value_column].to_numpy() for group in groups) / k
        X_sum = sum(group[self.value_column].sum() for group in groups) / (k * n)

        V_beta = sum(((X_dot - X_sum) ** 2).sum() for X_dot in X_dot_j) * n

        V_in = sum(
            ((group[self.value_column] - X_j - X_i_dot + X_sum) ** 2).sum()
            for X_j, group in zip(X_dot_j, groups)
        )

        if np.isclose(V_in, 0):
            if np.isclose(V_beta, 0):
                F_X = 0
            else:
                F_X = 1e10
        else:
            F_X = (V_beta / (k - 1)) / (V_in / ((n - 1) * (k - 1)))
        distr = sps.f(dfn=k - 1, dfd=(n - 1) * (k - 1))
        pvalue = distr.sf(F_X)

        return TestResult(pvalue=pvalue)


class FOneWayIndependentTest(BaseTest):
    """
    Performs a one-way ANOVA test using SciPy's built-in `f_oneway` function
    for multiple independent groups.

    Attributes:
        value_column (str): Name of the column containing the values to test.
    """

    def __init__(
        self,
        value_column="target",
    ):
        super().__init__()
        self.value_column = value_column

    def test(self, groups: List[pd.DataFrame], artefacts) -> TestResult:
        """
        Executes a one-way ANOVA on the provided groups using `scipy.stats.f_oneway`.

        Args:
            groups (List[pd.DataFrame]): A list of DataFrames, each representing a group/sample.
            artefacts (dict): A dictionary for storing or retrieving additional test information.

        Returns:
            TestResult: A `TestResult` object containing the p-value from the ANOVA.
        """
        result = sps.f_oneway(*[group[self.value_column] for group in groups])
        return TestResult(pvalue=result.pvalue)
