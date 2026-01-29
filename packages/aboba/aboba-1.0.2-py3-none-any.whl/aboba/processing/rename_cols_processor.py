import pandas as pd

from typing import Dict

from aboba.base import BaseDataProcessor


class RenameColsProcessor(BaseDataProcessor):
    """
    Renames columns in a DataFrame according to a mapping dictionary.
    
    This processor takes a dictionary that maps old column names to new column
    names and applies the renaming to the DataFrame.
    
    Examples:
        ```python
        import pandas as pd
        from aboba.processing.rename_cols_processor import RenameColsProcessor

        # Create sample data
        data = pd.DataFrame({
            'old_name1': [1, 2, 3],
            'old_name2': ['a', 'b', 'c']
        })

        # Rename columns
        processor = RenameColsProcessor({
            'old_name1': 'new_name1',
            'old_name2': 'new_name2'
        })
        processed_data, _ = processor.transform(data)
        print(processed_data.columns.tolist())
        ```
    """

    def __init__(self, names_mapping: Dict[str, str]):
        super().__init__()
        self.names_mapping = names_mapping

    def transform(self, data: pd.DataFrame):
        data = data.rename(columns=self.names_mapping)
        return data, dict()
