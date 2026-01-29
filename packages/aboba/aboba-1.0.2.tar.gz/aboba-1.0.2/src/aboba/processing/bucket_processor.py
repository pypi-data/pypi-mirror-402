import pandas as pd
from typing import Optional, Any, Tuple, Dict

from aboba.base import BaseOneRowProcessor


class BucketProcessor(BaseOneRowProcessor):
    """
    Processor that assigns rows to buckets based on a hash of a source column.
    
    This processor creates a new column with bucket assignments by hashing the
    values in a source column and taking the modulo with the number of buckets.
    This ensures consistent bucket assignment for the same source values.
    
    Examples:
        ```python
        import pandas as pd
        from aboba.processing.bucket_processor import BucketProcessor

        # Create sample data
        data = pd.DataFrame({
            'user_id': ['user1', 'user2', 'user3', 'user4', 'user5']
        })

        # Assign users to 3 buckets
        processor = BucketProcessor(
            source_column='user_id',
            result_column='bucket',
            n_buckets=3
        )
        processed_data, _ = processor.transform(data)
        print(processed_data)
        ```
    """
    
    def __init__(self, source_column: str, result_column: str, n_buckets: int):
        """
        Initialize the BucketProcessor.
        
        Args:
            source_column (str): Name of the column to use for bucket assignment.
            result_column (str): Name of the column to store bucket assignments.
            n_buckets (int): Number of buckets to assign rows to.
        """
        super().__init__()
        self.source_column = source_column
        self.result_column = result_column
        self.n_buckets = n_buckets
        self.tqdm_kwargs = kwargs

    def transform_one_row(
        self, row: pd.Series, index: Any, int_index: int
    ) -> Tuple[pd.Series, Optional[Dict]]:
        """
        Transforms a single row by assigning a bucket index based on the hash of a specified column.

        Args:
            row (pd.Series): One row from the data to process.
            index (Any): DataFrame index for the row.
            int_index (int): Integer position of the row in the DataFrame.

        Returns:
            Tuple[pd.Series, Optional[Dict]]: 
                - The modified row with a bucket index in `result_column`.
                - An optional dictionary of artifacts (None in this case).
        """
        
        row = row.copy()
        row[self.result_column] = abs(hash(row[self.source_column])) % self.n_buckets
        return row, None
