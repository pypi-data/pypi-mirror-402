from typing import List, Optional
import pandas as pd
import scikit_posthocs as sp

from aboba.base import BaseTest, BaseDataProcessor, DataSampler, TestResult


class PostHocDunnTest(BaseTest):
    """
    Performs a post-hoc Dunn test, typically used following a Kruskal-Wallis test,
    for multiple comparisons between groups.

    Attributes:
        value_column (str): Name of the column containing the values to test.
        p_adjust (str): Method used for p-value adjustment (e.g., 'bonferroni', 'holm', etc.).
    """

    def __init__(
        self,
        value_column="target",
        p_adjust="bonferroni",
    ):
        """
        Post-hoc Dunn's test for multiple comparisons.
        
        This test performs pairwise comparisons between groups after an omnibus test
        (like Kruskal-Wallis) indicates significant differences exist. It is a
        non-parametric alternative to Tukey's HSD test.
        
        Args:
            value_column (str): Name of the column containing the values to test.
            p_adjust (str): Method for adjusting p-values for multiple comparisons.
                Default is 'bonferroni'. Other options include 'holm', 'holm-sidak',
                'simes-hochberg', 'hommel', 'fdr_bh', 'fdr_by'.
        
        Examples:
            ```python
            import pandas as pd
            import numpy as np
            from aboba.tests.multiple.dunn import PostHocDunnTest

            # Create sample data with three groups
            np.random.seed(42)
            group1 = pd.DataFrame({'target': np.random.normal(10, 2, 50)})
            group2 = pd.DataFrame({'target': np.random.normal(12, 2, 50)})
            group3 = pd.DataFrame({'target': np.random.normal(11, 2, 50)})

            # Perform the test
            test = PostHocDunnTest(value_column='target', p_adjust='bonferroni')
            artefacts = {}
            result = test.test([group1, group2, group3], artefacts)
            print(f"Minimum p-value: {result.pvalue:.4f}")
            print("Pairwise comparison results:")
            print(artefacts['post_hoc_dunn_result'])
            ```
        """
        super().__init__()
        self.value_column = value_column
        self.p_adjust = p_adjust

    def test(self, groups: List[pd.DataFrame], artefacts) -> TestResult:
        """
        Perform Dunn's post-hoc test for multiple comparisons.
        
        Args:
            groups (List[pd.DataFrame]): List of DataFrames representing the groups to compare.
            artefacts (dict): Dictionary to store additional results, including the full
                pairwise comparison matrix under the key 'post_hoc_dunn_result'.
            
        Returns:
            TestResult: Object containing the minimum p-value from all pairwise comparisons.
        """
        result = sp.posthoc_dunn(
            [group[self.value_column] for group in groups], p_adjust=self.p_adjust
        )
        artefacts["post_hoc_dunn_result"] = result
        return TestResult(pvalue=result.min())
