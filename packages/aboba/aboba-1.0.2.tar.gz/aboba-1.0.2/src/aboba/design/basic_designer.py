import typing as tp
import pandas as pd
import numpy as np

from aboba.design.base_designer import BaseExperimentDesigner, ExperimentDesignMetrics, IntervalEstimate
from aboba.base.base_test import BaseTest
from aboba.base.base_effect_modifier import EffectModifier
from aboba.pipeline.pipeline import Pipeline
from aboba.experiment.aboba_experiment import AbobaExperiment


class BasicExperimentDesigner(BaseExperimentDesigner):
    """
    A simplified experiment designer that automatically handles experiment setup.
    
    This class extends BaseExperimentDesigner by providing a ready-to-use factory
    function that runs AA and AB tests to estimate Type I and Type II errors.
    Users only need to provide data, test, and pipeline - the designer handles
    the rest automatically.
    
    Args:
        data: DataFrame containing the experimental data. Should include all necessary
            columns for the test and pipeline.
        test: Statistical test to use for evaluating the experiment design.
        get_pipeline: Function that takes parameters and returns a data processing pipeline.
        synthetic_effect: Effect modifier to apply in AB tests for estimating Type II error.
            If None, no effect will be applied (useful for AA-only testing).
        n_iter: Number of iterations to run for each experiment configuration.
        alpha: Significance level for the test (default: 0.05).
        constraints: Dictionary mapping parameter names to their possible values.
        joblib_kwargs: Additional keyword arguments to pass to joblib for parallel processing.
    
    Examples:
        ```python
        import numpy as np
        import pandas as pd
        import scipy.stats as sps
        from aboba.design.basic_designer import BasicExperimentDesigner
        from aboba.tests import AbsoluteIndependentTTest
        from aboba.samplers import GroupSampler
        from aboba.pipeline import Pipeline
        from aboba.effect_modifiers import GroupModifier
        
        # Generate sample data
        n_samples = 1000
        data_a = sps.norm.rvs(size=n_samples, loc=0, scale=1)
        data_b = sps.norm.rvs(size=n_samples, loc=0, scale=1)
        
        data = pd.DataFrame({
            'value': np.concatenate([data_a, data_b]),
            'b_group': np.concatenate([
                np.repeat(0, n_samples),
                np.repeat(1, n_samples),
            ]),
        })
        
        # Define test and effect
        test = AbsoluteIndependentTTest(value_column='value')
        synthetic_effect = GroupModifier(
            effects={1: 0.3},
            value_column='value',
            group_column='b_group',
        )
        
        # Create designer with parameter constraints
        designer = BasicExperimentDesigner(
            data=data,
            test=test,
            get_pipeline=lambda params: Pipeline([
                ('GroupSampler', GroupSampler(size=params.get('group_size', 100), column='b_group')),
            ]),
            synthetic_effect=synthetic_effect,
            n_iter=1000,
            constraints={
                "group_size": [50, 100, 200, 500],
            }
        )
        
        # Find optimal parameters
        designer.optimize()
        best_params = designer.get_best_params()
        print(f"Best group size: {best_params.parameters['group_size']}")
        
        # Visualize results
        designer.visualize()
        ```
    """
    
    def __init__(
        self,
        data: pd.DataFrame,
        test: BaseTest,
        get_pipeline: tp.Callable[[tp.Dict[str, tp.Any]], Pipeline],
        synthetic_effect: EffectModifier | None = None,
        n_iter: int = 1000,
        alpha: float = 0.05,
        constraints: tp.Dict[str, tp.Iterable] | None = None,
        joblib_kwargs: tp.Dict[str, tp.Any] | None = None,
    ):
        """
        Initialize the basic experiment designer.
        
        The designer will automatically create an experiment factory that runs
        AA and AB tests to evaluate different parameter configurations.
        """
        self.data = data
        self.test = test
        self.get_pipeline = get_pipeline
        self.synthetic_effect = synthetic_effect
        self.n_iter = n_iter
        self.alpha = alpha
        self.joblib_kwargs = joblib_kwargs or {}
        
        # Create the experiment factory
        def experiment_factory(parameters: tp.Dict[str, tp.Any]) -> ExperimentDesignMetrics:
            """
            Factory function that evaluates experiment design for given parameters.
            
            This function runs AA and AB tests to estimate Type I and Type II errors.
            """
            # Get pipeline with current parameters
            pipeline = self.get_pipeline(parameters)
            
            # Create experiment
            experiment = AbobaExperiment()
            
            # Run AA test to estimate Type I error
            aa_group = experiment.group(
                "AA",
                test=self.test,
                data=self.data,
                data_pipeline=pipeline,
                n_iter=self.n_iter,
                joblib_kwargs=self.joblib_kwargs,
            ).run()
            
            type_I_error = (aa_group.get_data()["pvalue"] < self.alpha).mean()
            
            # Run AB test to estimate Type II error (if synthetic effect is provided)
            if self.synthetic_effect is not None:
                ab_group = experiment.group(
                    "AB",
                    test=self.test,
                    data=self.data,
                    data_pipeline=pipeline,
                    synthetic_effect=self.synthetic_effect,
                    n_iter=self.n_iter,
                    joblib_kwargs=self.joblib_kwargs,
                ).run()
                
                # Type II error is the probability of not rejecting H0 when H1 is true
                type_II_error = (ab_group.get_data()["pvalue"] >= self.alpha).mean()
            else:
                # If no synthetic effect, we can't estimate Type II error
                type_II_error = 0.0
            
            return ExperimentDesignMetrics(
                type_I_error=IntervalEstimate(parameter_estimate=type_I_error),
                type_II_error=IntervalEstimate(parameter_estimate=type_II_error),
            )
        
        # Initialize base class with factory and constraints
        if constraints is None:
            constraints = {}
        
        super().__init__(
            experiment_design_factory=experiment_factory,
            constraints=constraints,
        )
    