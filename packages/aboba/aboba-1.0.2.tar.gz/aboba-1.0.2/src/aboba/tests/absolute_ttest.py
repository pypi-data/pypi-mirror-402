from typing import List
import pandas as pd
import scipy.stats as sps
import numpy as np

from aboba.base import BaseTest, TestResult
from aboba.utils.p_value import compute_pvalue 


class AbsoluteIndependentTTest(BaseTest):
    def __init__(
        self,
        value_column="target",
        equal_var=True,
        random_state=None,
        alternative="two-sided",
        alpha = 0.05
    ):
        """
        Independent t-test for absolute difference between two groups.
        
        This test compares the means of two independent groups to determine if there
        is a statistically significant difference between them in absolute terms.
        
        Args:
            value_column (str): Name of the column containing the values to test.
            equal_var (bool): If True, perform a standard independent 2 sample test
                that assumes equal population variances. If False, perform Welch's
                t-test, which does not assume equal population variances.
            random_state (int or None): Seed for the random number generator.
            alternative (str): Defines the alternative hypothesis. Options are:
                'two-sided' (default), 'less', or 'greater'.
        
        Examples:
            ```python
            import pandas as pd
            import numpy as np
            from aboba.tests.absolute_ttest import AbsoluteIndependentTTest

            # Create sample data
            np.random.seed(42)
            group_a = pd.DataFrame({'target': np.random.normal(10, 2, 100)})
            group_b = pd.DataFrame({'target': np.random.normal(12, 2, 100)})

            # Perform the test
            test = AbsoluteIndependentTTest(value_column='target')
            result = test.test([group_a, group_b], {})
            print(f"P-value: {result.pvalue:.4f}")
            print(f"Effect: {result.effect:.4f}")
            ```
        """

        super().__init__()
        self.value_column = value_column
        self.equal_var = equal_var
        self.random_state = random_state
        self.alternative = alternative
        self.alpha = alpha

    def test(self, groups: List[pd.DataFrame], artefacts) -> TestResult:
        assert len(groups) == 2, "Expected exactly two groups"

        a_group, b_group = groups
        a = np.asarray(a_group[self.value_column], dtype=float)
        b = np.asarray(b_group[self.value_column], dtype=float)
        n1 = a.size
        n2 = b.size
        mean1 = a.mean()
        mean2 = b.mean()
        var1 = a.var(ddof=1)
        var2 = b.var(ddof=1)

        if self.equal_var:
            df = n1 + n2 - 2   
            sp2 = ((n1 - 1) * var1 + (n2 - 1) * var2) / df
            se = np.sqrt(sp2 * (1.0 / n1 + 1.0 / n2))
        else:
            se1 = var1 / n1
            se2 = var2 / n2
            se = np.sqrt(se1 + se2)
            num = (se1 + se2) ** 2
            den = (se1 ** 2) / (n1 - 1) + (se2 ** 2) / (n2 - 1)
            df = num / den

        if se == 0.0:
            t_stat = 0.0
            pvalue = 1.0
        else:
            t_stat = (mean2 - mean1) / se
            pvalue = compute_pvalue(t_stat, df, self.alternative)

        effect = mean2 - mean1
        q = sps.t.ppf(1 - self.alpha / 2, df)
        left_bound, right_bound = (effect - q*se, effect + q*se)

        return TestResult(pvalue=pvalue, effect=effect, effect_interval = (left_bound, right_bound))


class AbsoluteRelatedTTest(BaseTest):
    """
    Performs a paired (related) two-sample t-test on absolute data.

    Attributes:
        value_column (str): Name of the column containing the values to test.
        alternative (str): Defines the alternative hypothesis. The following options are
            available (default is 'two-sided'):
            - 'two-sided': the means of the distributions underlying the samples are unequal.
            - 'greater': the mean of the distribution underlying the first sample is greater.
            - 'less': the mean of the distribution underlying the first sample is smaller.
        alpha (float), default=0.05:  Significance level for confidence intervals
    """
    
    def __init__(
        self,
        value_column="target",
        alternative="two-sided",
        alpha = 0.05
    ):
        """
        Related (paired) t-test for absolute difference between two groups.
        
        This test compares the means of two related groups to determine if there
        is a statistically significant difference between them in absolute terms.
        It is typically used when the same subjects are measured twice (before/after).
        
        Args:
            value_column (str): Name of the column containing the values to test.
            alternative (str): Defines the alternative hypothesis. Options are:
                'two-sided' (default), 'less', or 'greater'.
        
        Examples:
            ```python
            import pandas as pd
            import numpy as np
            from aboba.tests.absolute_ttest import AbsoluteRelatedTTest

            # Create sample paired data
            np.random.seed(42)
            before = np.random.normal(10, 2, 50)
            after = before + np.random.normal(0.5, 1, 50)  # Adding effect
            group_a = pd.DataFrame({'target': before})
            group_b = pd.DataFrame({'target': after})

            # Perform the test
            test = AbsoluteRelatedTTest(value_column='target')
            result = test.test([group_a, group_b], {})
            print(f"P-value: {result.pvalue:.4f}")
            print(f"Effect: {result.effect:.4f}")
            ```
        """

        super().__init__()
        self.value_column = value_column
        self.alternative = alternative
        self.alpha = alpha

    def test(self, groups: List[pd.DataFrame], artefacts) -> TestResult:
        assert len(groups) == 2, "Expected exactly two groups"

        a_group, b_group = groups

        a = np.asarray(a_group[self.value_column], dtype=float)
        b = np.asarray(b_group[self.value_column], dtype=float)

        mask = np.isfinite(a) & np.isfinite(b)
        d = b[mask] - a[mask]
        n = d.size
        mean_diff = d.mean()
        std_diff = d.std(ddof=1)
        df = n - 1

        if std_diff == 0.0:
            se = 0.0
            if mean_diff == 0.0:
                t_stat = 0.0
                pvalue = 1.0
            else:
                t_stat = float("inf") if mean_diff > 0 else float("-inf")
                pvalue = compute_pvalue(t_stat, df, self.alternative)
        else:
            se = std_diff / np.sqrt(n)
            t_stat = mean_diff / se
            pvalue = compute_pvalue(t_stat, df, self.alternative)

        effect = mean_diff

        q = sps.t.ppf(1 - self.alpha / 2, df)
        left_bound, right_bound = effect - q * se, effect + q *se

        return TestResult(pvalue=pvalue, effect=effect, effect_type="absolute", effect_interval=(left_bound, right_bound))


class AbsoluteIndependentTTest_sps(BaseTest):
    def __init__(
        self,
        value_column="target",
        equal_var=True,
        random_state=None,
        alternative="two-sided",
        alpha = 0.05
    ):
        """
        Independent t-test for absolute difference between two groups.
        
        This test compares the means of two independent groups to determine if there
        is a statistically significant difference between them in absolute terms.
        
        Args:
            value_column (str): Name of the column containing the values to test.
            equal_var (bool): If True, perform a standard independent 2 sample test
                that assumes equal population variances. If False, perform Welch's
                t-test, which does not assume equal population variances.
            random_state (int or None): Seed for the random number generator.
            alternative (str): Defines the alternative hypothesis. Options are:
                'two-sided' (default), 'less', or 'greater'.
        
        Examples:
            ```python
            import pandas as pd
            import numpy as np
            from aboba.tests.absolute_ttest import AbsoluteIndependentTTest

            # Create sample data
            np.random.seed(42)
            group_a = pd.DataFrame({'target': np.random.normal(10, 2, 100)})
            group_b = pd.DataFrame({'target': np.random.normal(12, 2, 100)})

            # Perform the test
            test = AbsoluteIndependentTTest(value_column='target')
            result = test.test([group_a, group_b], {})
            print(f"P-value: {result.pvalue:.4f}")
            print(f"Effect: {result.effect:.4f}")
            ```
        """

        super().__init__()
        self.value_column = value_column
        self.equal_var = equal_var
        self.random_state = random_state
        self.alternative = alternative
        self.alpha = alpha

    def test(self, groups: List[pd.DataFrame], artefacts) -> TestResult:
        assert len(groups) == 2, "Expected exactly two groups"

        a_group, b_group = groups
        res = sps.ttest_ind(
            a_group[self.value_column],
            b_group[self.value_column],
            random_state=self.random_state,
            equal_var=self.equal_var,
            alternative=self.alternative,
        )
        pvalue = res.pvalue
        effect = b_group[self.value_column].mean() - a_group[self.value_column].mean()
        std = np.sqrt(a_group[self.value_column].var()/len(a_group) + b_group[self.value_column].var()/len(b_group))            
        q = sps.norm.ppf(1 - self.alpha/2)
        left_bound, right_bound  = (effect - q*std, effect + q*std)

        return TestResult(pvalue=pvalue, effect=effect, effect_interval = (left_bound, right_bound))


class AbsoluteRelatedTTest_sps(BaseTest):
    """
    Performs a paired (related) two-sample t-test on absolute data.

    Attributes:
        value_column (str): Name of the column containing the values to test.
        alternative (str): Defines the alternative hypothesis. The following options are
            available (default is 'two-sided'):
            - 'two-sided': the means of the distributions underlying the samples are unequal.
            - 'greater': the mean of the distribution underlying the first sample is greater.
            - 'less': the mean of the distribution underlying the first sample is smaller.
        alpha (float), default=0.05:  Significance level for confidence intervals
    """
    
    def __init__(
        self,
        value_column="target",
        alternative="two-sided",
        alpha = 0.05
    ):
        """
        Related (paired) t-test for absolute difference between two groups.
        
        This test compares the means of two related groups to determine if there
        is a statistically significant difference between them in absolute terms.
        It is typically used when the same subjects are measured twice (before/after).
        
        Args:
            value_column (str): Name of the column containing the values to test.
            alternative (str): Defines the alternative hypothesis. Options are:
                'two-sided' (default), 'less', or 'greater'.
        
        Examples:
            ```python
            import pandas as pd
            import numpy as np
            from aboba.tests.absolute_ttest import AbsoluteRelatedTTest

            # Create sample paired data
            np.random.seed(42)
            before = np.random.normal(10, 2, 50)
            after = before + np.random.normal(0.5, 1, 50)  # Adding effect
            group_a = pd.DataFrame({'target': before})
            group_b = pd.DataFrame({'target': after})

            # Perform the test
            test = AbsoluteRelatedTTest(value_column='target')
            result = test.test([group_a, group_b], {})
            print(f"P-value: {result.pvalue:.4f}")
            print(f"Effect: {result.effect:.4f}")
            ```
        """
        super().__init__()
        self.value_column = value_column
        self.alternative = alternative
        self.alpha = alpha

    def test(self, groups: List[pd.DataFrame], artefacts) -> TestResult:
        assert len(groups) == 2, "Expected exactly two groups"

        a_group, b_group = groups
        res = sps.ttest_rel(
            a_group[self.value_column],
            b_group[self.value_column],
            alternative=self.alternative,
        )
        pvalue = res.pvalue
        # left_bound, right_bound  = res.confidence_interval(confidence_level=0.95)
        effect = b_group[self.value_column].mean() - a_group[self.value_column].mean()
        std = np.sqrt(a_group[self.value_column].var()/len(a_group) + b_group[self.value_column].var()/len(b_group)) 
        q = sps.norm.ppf(1 - self.alpha/2)
        left_bound, right_bound  = (effect - q*std, effect + q*std)

        return TestResult(pvalue=pvalue, effect=effect, effect_type="absolute", effect_interval = (left_bound, right_bound))
