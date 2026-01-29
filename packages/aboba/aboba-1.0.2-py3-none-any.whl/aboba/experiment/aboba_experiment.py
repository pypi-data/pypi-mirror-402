from matplotlib.pyplot import Figure
from typing import Any, Callable, Dict, Optional, Tuple, Union, List

import pandas as pd

from aboba.experiment.visualization import default_visualization_method, ExperimentData
from aboba.experiment.experiment_group import ExperimentGroup
from aboba.pipeline import Pipeline
from aboba.base.base_test import BaseTest
from aboba.base import EffectModifier


class AbobaExperiment:
    """

    Context for conducting and displaying AB tests results.

    Results are displayed on a figure with confidence levels.
    By specifying number of columns, you can generate nice comparisons

    Examples:
        ```python
        # First create tests
        value_column = 'value'
        size = 100

        sampler = samplers.GroupSampler(
            column='b_group',
            size=size,
        )
        cuped_preprocess = processing.CupedProcessor(...)
        test_cuped = tests.AbsoluteIndependentTTest(
            preprocess=cuped_preprocess,
            data_sampler=sampler,
            value_column=value_column,
        )
        test_regular = tests.AbsoluteIndependentTTest(
            preprocess=None,
            data_sampler=sampler,
            value_column=value_column,
        )

        # Next create an experiment with relevant name.
        # You can also generate several columns
        experiment = AbobaExperiment(experiment_name="CUPED vs regular", draw_cols=2)

        regular_aa_group = experiment.group("AA, regular")
        regular_aa_group.run(test_regular, n_iter=n_iter)

        regular_ab_group = experiment.group("AB, regular")
        regular_ab_group.run(test_regular, synthetic_effect=effect, n_iter=n_iter)

        cuped_aa_group = experiment.group("AA, cuped")
        cuped_aa_group.run(test_cuped, n_iter=n_iter)

        cuped_ab_group = experiment.group("AB, cuped")
        cuped_ab_group.run(test_cuped, synthetic_effect=effect, n_iter=n_iter)

        # Get results from each group
        ab_results = cuped_ab_group.get_data()
        ```
    """

    def __init__(
        self,
        alpha=0.05,
        experiment_name: Optional[str] = "AB experiment",
        visualization_method: Optional[
            Callable[[Dict[str, ExperimentData], Dict[str, Any]], tuple[Figure, Any]]
        ] = default_visualization_method,
        **visualization_kwargs,
    ):
        """

        Create a new experiment.
        Refer to the class description for more information

        Args:
            experiment_name (str): name of experiment to display
        """

        assert 0.0 < alpha < 1.0

        self.alpha = alpha
        self.experiment_name = experiment_name
        self.visualization_method = visualization_method

        visualization_kwargs["alpha"] = visualization_kwargs.get("alpha", alpha)
        visualization_kwargs["experiment_name"] = visualization_kwargs.get(
            "experiment_name", experiment_name
        )
        self.visualization_kwargs = visualization_kwargs

        self._groups: Dict[str, ExperimentGroup] = {}

    def group(
        self,
        name: str,
        test: BaseTest,
        data: Union[pd.DataFrame, List[pd.DataFrame]],
        data_pipeline: Pipeline,
        synthetic_effect: Optional[EffectModifier] = None,
        n_iter: int = 1,
        joblib_kwargs: Optional[dict] = None,
    ) -> ExperimentGroup:
        """

        Creates new context for experiment with specified name.

        Args:
            name (str): name to use for this experiment subset. This will be used as id

        """
        # TODO: raise one-time warning, if needed
        # assert name not in self._groups, (
        #     f"Trying to create group with {name = } but "
        #     f"it is already defined ({self._groups.keys()})"
        # )

        group = ExperimentGroup(
            name,
            test,
            data,
            data_pipeline,
            synthetic_effect,
            n_iter,
            joblib_kwargs,
        )
        self._groups[name] = group

        return group

    def draw(self) -> Tuple[Optional[Figure], Any]:
        if self.visualization_method is None:
            return None, None
        else:
            values = {key: value.get_raw_data() for key, value in self._groups.items()}
            return self.visualization_method(values, **self.visualization_kwargs)
