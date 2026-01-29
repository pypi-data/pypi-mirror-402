from typing import List, Tuple, Dict
from tqdm.auto import tqdm
import pandas as pd
import logging

from aboba.base import BaseDataProcessor, BaseOneRowProcessor, DataProcessor

logger = logging.getLogger(__name__)


class PreprocessorPipeline(BaseDataProcessor):
    """
    Processes data through a sequence of preprocessing steps.
    
    This pipeline applies a series of data processors in order, passing the
    output of each step as input to the next. It supports both fitting
    (for processors that need to learn from data) and transforming.
    
    Examples:
        ```python
        import pandas as pd
        from aboba.processing.preprocessor_pipeline import PreprocessorPipeline
        from aboba.processing.rename_cols_processor import RenameColsProcessor
        from aboba.processing.ensure_cols_processor import EnsureColsProcessor

        # Create sample data
        data = pd.DataFrame({
            'old_name': [1, 2, 3, 4, 5],
            'other_col': ['a', 'b', 'c', 'd', 'e']
        })

        # Create a pipeline with two steps
        pipeline = PreprocessorPipeline([
            RenameColsProcessor({'old_name': 'new_name'}),
            EnsureColsProcessor(['new_name', 'other_col'])
        ], verbose=True)

        # Fit and transform the data
        processed_data, artifacts = pipeline.fit_transform(data)
        print(processed_data.columns.tolist())
        ```
    """

    def __init__(self, steps: List[DataProcessor], verbose: bool = False, **kwargs):
        self.steps = steps
        self.verbose = verbose
        self.tqdm_kwargs = kwargs
    

    def fit(self, data: pd.DataFrame):
        """
        This called once on **all** available data, each processor step
        receives processed data from the previous step

        Args:
            data (pd.DataFrame): full data, with all groups
        """
        self._transform(data, fit=True)
        return self

    def transform(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """

        Transforms data in steps.
        Fit must be called before transforming

        Args:
            data (pd.DataFrame): data to fit on and to transform

        Returns:
            Tuple[pd.DataFrame, Dict]: tuple with processed row and artefacts dict
        """
        return self._transform(data, fit=False)

    def fit_transform(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """

        Combination of fit and transform

        Args:
            data (pd.DataFrame): data to fit on and to transform

        Returns:
            Tuple[pd.DataFrame, Dict]: tuple with processed row and artefacts dict
        """
        return self._transform(data, fit=True)

    def _transform(self, data: pd.DataFrame, fit=False) -> Tuple[pd.DataFrame, Dict]:
        artifacts = dict()

        itr = tqdm(self.steps, **self.tqdm_kwargs)
        
        for step in itr:
            if self.verbose:
                itr.set_description("processing pipeline")
            data, artifacts_new = self._process_step(step, data, fit=fit)
            self._merge_artifacts(artifacts, artifacts_new)
        return data, artifacts

    @staticmethod
    def _process_step(
        step: DataProcessor, data: pd.DataFrame, fit: bool
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Process a single step in the pipeline.
        
        Args:
            step (DataProcessor): The processor to apply.
            data (pd.DataFrame): Data to process.
            fit (bool): Whether to fit the processor before transforming.
            
        Returns:
            Tuple[pd.DataFrame, Dict]: Processed data and artifacts.
        """
        if isinstance(step, BaseDataProcessor):
            if fit:
                step.fit(data)
            data, artifacts_new = step.transform(data)
        elif hasattr(step, "__call__"):
            data, artifacts_new = step(data)
        else:
            assert False, "Data processor must be of DataProcessor type"
        return data, artifacts_new

    @staticmethod
    def _merge_artifacts(artifacts, artifacts_new):
        """
        Merge artifacts from a new step into the existing artifacts.
        
        Args:
            artifacts (Dict): Existing artifacts.
            artifacts_new (Dict): New artifacts to merge.
        """
        for key in artifacts_new:
            if key in artifacts:
                logger.warning(
                    f"Overwriting existing artifact {key} in processing step!"
                )
            artifacts[key] = artifacts_new[key]
