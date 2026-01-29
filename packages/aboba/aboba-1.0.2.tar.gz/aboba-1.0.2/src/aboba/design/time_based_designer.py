import typing as tp
import pandas as pd
import numpy as np
from datetime import datetime

from aboba.design.base_designer import BaseExperimentDesigner, ExperimentDesignMetrics, IntervalEstimate
from aboba.base.base_test import BaseTest
from aboba.base.base_effect_modifier import EffectModifier
from aboba.pipeline.pipeline import Pipeline
from aboba.experiment.aboba_experiment import AbobaExperiment


class TimeBasedDesigner(BaseExperimentDesigner):
    """
    A designer for time-based experiments where users can be included at different times.
    
    This class extends BaseExperimentDesigner to handle experiments with temporal data where:
    - Users have multiple observations over time
    - Users can be included in the treatment group at different moments
    - The effect starts from a specific date and only affects qualifying observations
    - You want to optimize parameters like effect start date, effect size, experiment duration, etc.
    
    The designer automatically handles:
    - Creating time-based effect modifiers with different parameters
    - Running AA and AB tests to estimate Type I and Type II errors
    - Accounting for the temporal nature of user inclusion
    
    Args:
        data: DataFrame containing time-series experimental data with columns:
            - user_id or similar identifier
            - date column with observation dates
            - value column with the metric to test
            - group column indicating treatment assignment
            - inclusion_date column indicating when users entered treatment
        test: Statistical test to use for evaluating the experiment design
        get_pipeline: Function that takes parameters and returns a data processing pipeline
        get_effect: Function that takes parameters and returns an EffectModifier, or None for AA tests
        date_column: Name of the column containing observation dates
        experiment_duration: Either a parameter name (str) to extract from parameters, or a fixed timedelta value.
            If a string, the value will be extracted from parameters dict and should be a timedelta.
            If a timedelta, it's used as a fixed value. This parameter is required.
        effect_start_date: Either a parameter name (str) to extract from parameters, or a fixed date value.
            If a string, the value will be extracted from parameters dict.
            If a date/datetime, it's used as fixed. This parameter is required.
        n_iter: Number of iterations to run for each experiment configuration
        alpha: Significance level for the test (default: 0.05)
        constraints: Dictionary mapping parameter names to their possible values.
            Common parameters:
            - 'effect_start_date': List of dates when effect should start
            - 'effect_multiplier': List of multipliers for the base effect
            - 'experiment_duration': List of timedeltas for experiment durations
        joblib_kwargs: Additional keyword arguments for parallel processing
    
    Examples:
        ```python
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta
        from aboba.design.time_based_designer import TimeBasedDesigner
        from aboba.tests import AbsoluteIndependentTTest
        from aboba.samplers import UserSampler
        from aboba.pipeline import Pipeline
        
        # Generate sample time-series data (see data generator for full example)
        data = generate_time_based_data(
            n_users=200,
            start_date='2024-01-01',
            end_date='2024-12-31'
        )
        
        # Define test and pipeline
        test = AbsoluteIndependentTTest(value_column='payment')
        get_pipeline = lambda params: Pipeline([
            ('UserSampler', UserSampler(
                group_column='is_in_b_group',
                user_column='user_id',
                size=params.get('user_sample_size', 50)
            ))
        ])
        
        get_effect = lambda params: TimeBasedEffectModifier(
            effect=5.0 * params.get('effect_multiplier', 1.0),
            effect_start_date=pd.to_datetime(params['effect_start_date']),
            value_column='payment',
            date_column='date',
            group_column='is_in_b_group',
            inclusion_date_column='inclusion_date'
        ) if params.get('effect_start_date') else None
        
        # Create designer with parameter constraints
        designer = TimeBasedDesigner(
            data=data,
            test=test,
            get_pipeline=get_pipeline,
            get_effect=get_effect,
            date_column='date',
            experiment_duration='experiment_duration',  # parameter name
            effect_start_date='effect_start_date',  # parameter name
            n_iter=1000,
            constraints={
                'effect_start_date': [
                    '2024-03-01',
                    '2024-04-01',
                    '2024-05-01'
                ],
                'effect_multiplier': [0.8, 1.0, 1.2, 1.5],
                'experiment_duration': [
                    pd.Timedelta(weeks=4),
                    pd.Timedelta(weeks=6),
                    pd.Timedelta(weeks=8)
                ]
            }
        )
        
        # Find optimal parameters
        designer.optimize()
        best_params = designer.get_best_params()
        print(f"Best effect start date: {best_params.parameters['effect_start_date']}")
        print(f"Best effect multiplier: {best_params.parameters['effect_multiplier']}")
        print(f"Best experiment duration: {best_params.parameters['experiment_duration']}")
        
        # Visualize results
        designer.visualize()
        ```
    """
    
    def __init__(
        self,
        data: pd.DataFrame,
        test: BaseTest,
        get_pipeline: tp.Callable[[tp.Dict[str, tp.Any]], Pipeline],
        get_effect: tp.Callable[[tp.Dict[str, tp.Any]], EffectModifier | None],
        experiment_duration: str | pd.Timedelta,
        effect_start_date: str | datetime | pd.Timestamp,
        date_column: str = "date",
        n_iter: int = 1000,
        alpha: float = 0.05,
        constraints: tp.Dict[str, tp.Iterable] | None = None,
        joblib_kwargs: tp.Dict[str, tp.Any] | None = None,
    ):
        """
        Initialize the time-based experiment designer.
        """
        self.data = data
        self.test = test
        self.get_pipeline = get_pipeline
        self.get_effect = get_effect
        self.date_column = date_column
        self.experiment_duration = experiment_duration
        self.effect_start_date = effect_start_date
        self.n_iter = n_iter
        self.alpha = alpha
        self.joblib_kwargs = joblib_kwargs or {}
        
        # Ensure date column is datetime
        self.data[self.date_column] = pd.to_datetime(self.data[self.date_column])
        
        # Create the experiment factory
        def experiment_factory(parameters: tp.Dict[str, tp.Any]) -> ExperimentDesignMetrics:
            """
            Factory function that evaluates experiment design for given parameters.
            
            This function:
            1. Filters data based on experiment duration
            2. Gets the effect modifier from user-provided function
            3. Runs AA and AB tests to estimate Type I and Type II errors
            """
            # Resolve experiment_duration: extract from parameters if string, use directly if timedelta
            if isinstance(self.experiment_duration, str):
                experiment_duration = parameters.get(self.experiment_duration)
                assert experiment_duration is not None, f"Parameter '{self.experiment_duration}' must be provided in parameters"
                assert isinstance(experiment_duration, pd.Timedelta), f"Parameter '{self.experiment_duration}' must be a pd.Timedelta"
            else:
                experiment_duration = self.experiment_duration
            
            # Resolve effect_start_date: extract from parameters if string, use directly if date
            if isinstance(self.effect_start_date, str):
                effect_start_date = parameters.get(self.effect_start_date)
                assert effect_start_date is not None, f"Parameter '{self.effect_start_date}' must be provided in parameters"
            else:
                effect_start_date = self.effect_start_date
            
            # Convert to datetime if needed
            if isinstance(effect_start_date, str):
                effect_start_date = pd.to_datetime(effect_start_date)
            
            # Filter data based on experiment duration
            experiment_end_date = effect_start_date + experiment_duration
            experiment_data = self.data[
                (self.data[self.date_column] >= effect_start_date) &
                (self.data[self.date_column] <= experiment_end_date)
            ].copy()
            
            # Get effect modifier from user function
            synthetic_effect = self.get_effect(parameters)
            
            # Get pipeline with current parameters
            pipeline = self.get_pipeline(parameters)
            
            # Create experiment
            experiment = AbobaExperiment()
            
            # Run AA test to estimate Type I error
            aa_group = experiment.group(
                "AA",
                test=self.test,
                data=experiment_data,
                data_pipeline=pipeline,
                n_iter=self.n_iter,
                joblib_kwargs=self.joblib_kwargs,
            ).run()
            
            type_I_error = (aa_group.get_data()["pvalue"] < self.alpha).mean()
            
            # Run AB test to estimate Type II error (if synthetic effect is provided)
            if synthetic_effect is not None:
                ab_group = experiment.group(
                    "AB",
                    test=self.test,
                    data=experiment_data,
                    data_pipeline=pipeline,
                    synthetic_effect=synthetic_effect,
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
    