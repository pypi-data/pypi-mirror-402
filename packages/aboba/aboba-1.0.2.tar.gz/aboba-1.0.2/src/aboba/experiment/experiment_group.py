from dataclasses import asdict, fields
from typing import Optional, Union, List

import joblib
import pandas as pd
from tqdm.auto import trange

from aboba.base import BaseTest, EffectModifier
from aboba.base.base_test import TestResult
from aboba.pipeline import Pipeline
from aboba.experiment.visualization import ExperimentData


class ExperimentGroup:
    """

    Manages experiment subset

    """

    def __init__(
        self,
        name: str,
        test: BaseTest,
        data: Union[pd.DataFrame, List[pd.DataFrame]],
        data_pipeline: Pipeline,
        synthetic_effect: Optional[EffectModifier] = None,
        n_iter: int = 1,
        joblib_kwargs: Optional[dict] = None,
    ):
        self._experiment_data = ExperimentData()
        self._name = name
        self._test = test
        self._data = data
        self._pipeline = data_pipeline
        self._synthetic_effect = synthetic_effect
        self._n_iter = n_iter
        self._joblib_kwargs = joblib_kwargs

        self._pipeline.fit(self._data)

        if self._joblib_kwargs is None:
            self._joblib_kwargs = dict()


    def run(self):
        """

        Run test multiple times in parallel and store results in currently activated experiment group

        Args:
            test (BaseTest): the test to run
            synthetic_effect (Optional[EffectModifier]): effect modifier to apply
            n_iter (int): number of iterations to run
            joblib_kwargs (dict): custom dict to pass to joblib.Parallel init

        """
        #itr = trange(self._n_iter, leave=False)
        #itr.set_description(self._name)
        results = joblib.Parallel(**self._joblib_kwargs)(
            joblib.delayed(self._run_one)() for _ in range(self._n_iter)
        )

        for result in results:
            self._experiment_data.record(result)
        
        return self


    def get_raw_data(self) -> ExperimentData:
        return self._experiment_data


    def get_data(self) -> pd.DataFrame:
        test_result_cols = [field.name for field in fields(TestResult)]
        columns = ['Test name'] + test_result_cols

        result = pd.DataFrame(columns=columns)

        result[columns[0]] = [f'{self._name}-{i}' for i in range(len(self._experiment_data.history))]
        for field_name in test_result_cols:
            result[field_name] = [asdict(item)[field_name] for item in self._experiment_data.history]

        return result


    def _run_one(self):
        groups = self._pipeline.transform(self._data)
        groups = self._add_effect(groups, self._synthetic_effect)

        result = self._test.test(groups, None)
        assert isinstance(result, TestResult), f"Test {self._test} must return TestResult instance"

        return result


    @staticmethod
    def _add_effect(
        groups: List[pd.DataFrame], synthetic_effect: Optional[EffectModifier]
    ) -> List[pd.DataFrame]:
        if synthetic_effect is None:
            return groups

        modified = synthetic_effect([group.copy() for group in groups])
        assert len(modified) == len(
            groups
        ), f"Effect modifier {synthetic_effect} must not change number of groups"
        return modified
