import pandas as pd
from tqdm.auto import tqdm
from typing import Tuple, Dict, Optional, Any, Callable, Union
import joblib

from aboba.base import AbobaBase


class BaseDataProcessor(AbobaBase):
    """

    Base processor class that is applied at full dataframe

    """

    def fit(self, data: pd.DataFrame):
        """
        This called once on **all** available data

        Args:
            data (pd.DataFrame): full data, with all groups
        """
        pass

    def transform(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, Optional[Dict]]:
        """
        Transforms data and returns transformed dataframe.
        Can generate artefacts that can be used later

        Args:
            data (pd.DataFrame): full dataframe to process

        Returns:
            Tuple[pd.DataFrame, Optional[Dict]]: tuple with processed row and artefacts dict
        """

        raise NotImplemented

    def fit_transform(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """

        Combination of fit and transform

        Args:
            data (pd.DataFrame): data to fit on and to transform

        Returns:
            Tuple[pd.DataFrame, Dict]: tuple with processed row and artefacts dict
        """
        self.fit(data)
        return self.transform(data)

    def __call__(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, Optional[Dict]]:
        return self.transform(data)


class BaseOneRowProcessor(BaseDataProcessor):
    """

    Base processor class that is applied for each row independently

    """

    def transform_one_row(
        self, row: pd.Series, index: Any, int_index: int
    ) -> Tuple[pd.Series, Optional[Dict]]:
        """
        Transforms data row by row. Can be parallelized.
        Can generate artefacts that can be used later

        Args:
            row (pd.Series): one row from data to process
            index (Any): dataframe index for row
            int_index (int): integer position of row in dataframe

        Returns:
            Tuple[pd.Series, Optional[Dict]]: tuple with processed row and artefacts dict
        """
        raise NotImplemented

    def transform(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, Optional[Dict]]:
        """
        Transforms data row by row. Can be parallelized.
        Can generate artefacts that can be used later

        Args:
            data (pd.DataFrame): full dataframe to process

        Returns:
            Tuple[pd.DataFrame, Optional[Dict]]: tuple with processed row and artefacts dict
        """
        artifacts: Optional[Dict] = None
        result = []

        # TODO: move to constructor
        n_jobs = -1

        itr = tqdm(enumerate(data.index), **self.tqdm_kwargs)
        itr.set_description(f"processing {type(self).__name__}")
        # processed = joblib.Parallel(return_as="generator", n_jobs=n_jobs)(
        processed = joblib.Parallel(n_jobs=n_jobs)(
            joblib.delayed(self.transform_one_row)(
                data.loc[index], index=index, int_index=int_index
            )
            for int_index, index in itr
        )
        for row, artifacts_new in processed:
            result.append(row)
            if artifacts_new is not None:
                if artifacts is None:
                    artifacts = artifacts_new
                else:
                    artifacts.update(artifacts_new)

        return pd.DataFrame(result, index=data.index), artifacts


DataProcessor = Union[
    BaseDataProcessor, Callable[[pd.DataFrame], Tuple[pd.DataFrame, Optional[Dict]]]
]
