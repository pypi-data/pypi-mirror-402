import pandas as pd
import typing as tp

from aboba.base import BaseDataProcessor


class EnsureColsProcessor(BaseDataProcessor):
    """
    Verifies that specified columns are present in dataframe.
    
    This processor checks that all required columns are present in the DataFrame
    and raises an assertion error if any are missing. It's useful for validating
    data before processing.
    
    Examples:
        ```python
        import pandas as pd
        from aboba.processing.ensure_cols_processor import EnsureColsProcessor

        # Create sample data
        data = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c']
        })

        # Verify required columns are present
        processor = EnsureColsProcessor(['col1', 'col2'])
        processed_data, _ = processor.transform(data)  # No error
        print("Columns verified successfully")

        # This would raise an AssertionError:
        # processor = EnsureColsProcessor(['col1', 'missing_col'])
        # processor.transform(data)
        ```
    """

    def __init__(self, cols: tp.List[str]) -> None:
        super().__init__()
        self.cols = cols

    def transform(self, data: pd.DataFrame):
        """
        Verify that all required columns are present in the data.
        
        Args:
            data (pd.DataFrame): DataFrame to verify.
            
        Returns:
            Tuple[pd.DataFrame, Dict]: Original DataFrame and empty artifacts dict.
            
        Raises:
            AssertionError: If any required column is missing from the DataFrame.
        """
        for col in self.cols:
            assert (
                col in data.columns
            ), f"Expected column '{col}' in dataframe, got only {data.columns}"
        return data, dict()
