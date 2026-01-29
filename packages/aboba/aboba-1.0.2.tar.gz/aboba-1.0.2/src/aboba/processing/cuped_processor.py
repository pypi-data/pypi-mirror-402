import pandas as pd
import numpy as np

from typing import Optional, Any

from aboba.base import BaseDataProcessor


class CupedProcessor(BaseDataProcessor):
    """
    Performs CUPED (Controlled-experiment Using Pre-Experiment Data) transformation.
    
    CUPED is a variance reduction technique that uses pre-experiment data (covariates)
    to improve the sensitivity of A/B tests. It adjusts the target metric using
    information from a covariate that is correlated with the target metric.
    
    Examples:
        ```python
        import pandas as pd
        import numpy as np
        from aboba.processing.cuped_processor import CupedProcessor

        # Create sample data with pre-experiment data
        np.random.seed(42)
        n = 1000
        # Pre-experiment metric (covariate)
        pre_metric = np.random.normal(100, 10, n)
        # Post-experiment metric (target) - correlated with pre-metric
        post_metric = 2 * pre_metric + np.random.normal(0, 5, n)
        # Add treatment effect for second half
        post_metric[n//2:] += 5

        data = pd.DataFrame({
            'group': ['control'] * (n//2) + ['test'] * (n//2),
            'pre_metric': pre_metric,
            'post_metric': post_metric
        })

        # Apply CUPED transformation
        processor = CupedProcessor(
            value_column='post_metric',
            covariate_column='pre_metric',
            result_column='cuped_metric',
            group_column='group',
            group_test='test',
            group_control='control'
        )
        processed_data, _ = processor.transform(data)
        print(f"Original variance: {data['post_metric'].var():.2f}")
        print(f"CUPED variance: {processed_data['cuped_metric'].var():.2f}")
        ```
    """

    def __init__(
        self,
        value_column: str,
        covariate_column: str,
        result_column: str,
        group_column: Optional[str] = None,
        group_test: Any = None,
        group_control: Any = None,
    ):
        """
        Initialize the CUPED processor.
        
        Args:
            value_column (str): Name of the column with the target metric values.
            covariate_column (str): Name of the column with the covariate values.
            result_column (str): Name of the column to store the CUPED-transformed values.
            group_column (Optional[str]): Name of the column with group labels.
                If None, all data is used for CUPED transformation.
            group_test (Any): Value in group_column that identifies the test group.
            group_control (Any): Value in group_column that identifies the control group.
        """

        super().__init__()
        self.value_column = value_column
        self.covariate_column = covariate_column
        self.result_column = result_column

        if group_column is not None:
            assert group_test is not None
            assert group_control is not None

        self.group_column = group_column
        self.group_test = group_test
        self.group_control = group_control

    def transform(self, data: pd.DataFrame):
        """
        Apply CUPED transformation to the data.
        
        Args:
            data (pd.DataFrame): DataFrame to transform.
            
        Returns:
            Tuple[pd.DataFrame, Dict]: Transformed DataFrame and empty artifacts dict.
        """
        if self.group_column is not None:
            data_test = data[data[self.group_column] == self.group_test]
            data_control = data[data[self.group_column] == self.group_control]

            theta = (
                +np.cov(data_test[self.covariate_column], data_test[self.value_column])[
                    0, 1
                ]
                + np.cov(
                    data_control[self.covariate_column], data_control[self.value_column]
                )[0, 1]
            ) / (
                +data_test[self.covariate_column].var(ddof=0)
                + data_control[self.covariate_column].var(ddof=0)
            )

            data.loc[data[self.group_column] == self.group_test, self.result_column] = (
                data_test[self.value_column] - theta * data_test[self.covariate_column]
            )
            data.loc[
                data[self.group_column] == self.group_control, self.result_column
            ] = (
                data_control[self.value_column]
                - theta * data_control[self.covariate_column]
            )
        else:
            theta = (
                np.cov(data[self.covariate_column], data[self.value_column])[0, 1]
            ) / (data[self.covariate_column].var(ddof=0))
            data[self.result_column] = (
                data[self.value_column] - theta * data[self.covariate_column]
            )

        return data, dict()
