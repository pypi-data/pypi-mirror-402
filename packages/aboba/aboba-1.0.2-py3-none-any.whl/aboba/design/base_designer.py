import typing as tp

from enum import Enum
from functools import total_ordering
from itertools import product
from numbers import Number

import matplotlib.pyplot as plt
import numpy as np
from pydantic import BaseModel, field_validator


class IntervalEstimate(BaseModel):
    parameter_estimate: float
    left_bound: float | None = None
    right_bound: float | None = None
    probability: float | None = None


@total_ordering
class ExperimentDesignMetrics(BaseModel):
    type_I_error: IntervalEstimate
    type_II_error: IntervalEstimate

    def __lt__(self, other: 'ExperimentDesignMetrics') -> bool:
        # TODO: use left / right bounds to compare metrics more precisely
        if self.type_I_error.parameter_estimate != other.type_I_error.parameter_estimate:
            return self.type_I_error.parameter_estimate > other.type_I_error.parameter_estimate

        return self.type_II_error.parameter_estimate > other.type_II_error.parameter_estimate

    # TODO: Maybe distance between metrics should exist?
    # The behavior can always be overridden by inheriting from this class.
    # If a metric function is needed for some optimization method, it can be easily added.


class BaseExperimentDesigner:
    """
    Base class for finding optimal experiment parameters.
    
    This class searches for the best hyperparameters from a given set of constraints
    by maximizing ExperimentDesignMetrics (minimizing both Type I and Type II errors).
    
    The designer evaluates different parameter combinations and identifies the configuration
    that provides the best statistical properties for your experiment.
    """

    class OptimizerMethod(Enum):
        BRUTE_FORCE = 'brute_force'

    class OptimizerResult(BaseModel):
        parameters: tp.Dict[str, tp.Any]
        experiment_design_metrics: ExperimentDesignMetrics

        # Because pydantic doesn't support abstract types like Number
        # @field_validator('parameters')
        # def check_numbers(cls, v):
        #     for key, value in v.items():
        #         if not isinstance(value, Number) and not isinstance(value, str):
        #             raise ValueError(f"Value {value} for key {key} is not a number or a string")
        #     return v

    def __init__(
        self,
        experiment_design_factory: tp.Callable[[tp.Dict[str, Number]], ExperimentDesignMetrics],
        constraints: tp.Dict[str, tp.Iterable[Number]],
    ) -> None:
        """
        Initialize the experiment designer.
        
        Args:
            experiment_design_factory: A callable that takes a dictionary of parameters
                and returns ExperimentDesignMetrics. This function evaluates the quality
                of an experiment configuration by running simulations and computing
                Type I and Type II error rates.
            constraints: Dictionary mapping parameter names to their possible values.
                Keys are parameter names, values are iterables of numeric values to test.
        
        Examples:
            ```python
            import numpy as np
            from aboba.design.designer import BaseExperimentDesigner, ExperimentDesignMetrics, IntervalEstimate
            import aboba
            
            # Define a factory function that evaluates experiment configurations
            class ExperimentSetup:
                def __call__(self, parameters):
                    n_samples = parameters["n_samples"]
                    
                    # Generate synthetic data
                    data = self.generate_data(n_samples)
                    pipeline = self.generate_pipeline(n_samples)
                    test = aboba.tests.AbsoluteIndependentTTest(value_column='value')
                    
                    # Run AA test to estimate Type I error
                    experiment = aboba.experiment.AbobaExperiment()
                    aa_group = experiment.group(
                        "AA",
                        test=test,
                        data=data,
                        data_pipeline=pipeline,
                        n_iter=1000,
                    ).run()
                    
                    type_I_error = (aa_group.get_data()["pvalue"] < 0.05).mean()
                    
                    # Run AB test to estimate Type II error (power)
                    ab_group = experiment.group(
                        "AB",
                        test=test,
                        data=data,
                        data_pipeline=pipeline,
                        synthetic_effect=aboba.effect_modifiers.GroupModifier(
                            effects={1: 0.3},
                            value_column='value',
                            group_column='b_group',
                        ),
                        n_iter=1000,
                    ).run()
                    
                    type_II_error = (ab_group.get_data()["pvalue"] >= 0.05).mean()
                    
                    return ExperimentDesignMetrics(
                        type_I_error=IntervalEstimate(parameter_estimate=type_I_error),
                        type_II_error=IntervalEstimate(parameter_estimate=type_II_error),
                    )

                def generate_data(self, n_samples: int) -> pd.DataFrame:
                    data_a = sps.norm.rvs(size=n_samples, loc=0, scale=1)
                    data_b = sps.norm.rvs(size=n_samples, loc=0, scale=1)
                    
                    # dataset of two columns: value and group
                    data = pd.DataFrame({
                        'value': np.concatenate([
                            data_a,
                            data_b,
                        ]),
                        'b_group': np.concatenate([
                            np.repeat(0, n_samples),
                            np.repeat(1, n_samples),
                        ]),
                    })
                    
                    return data
                
                def generate_test(self) -> aboba.base.base_test.BaseTest:
                    return aboba.tests.AbsoluteIndependentTTest(
                        value_column='value',
                    )
                
                def generate_pipeline(self, n_samples: int) -> aboba.pipeline.Pipeline:
                    group_size = max(n_samples // 10, 2)
                    return aboba.pipeline.Pipeline([
                        ('GroupSampler', aboba.samplers.GroupSampler(size=group_size, column='b_group')),
                    ])
            
            # Create designer with parameter constraints
            designer = BaseExperimentDesigner(
                experiment_design_factory=ExperimentSetup(),
                constraints={
                    "n_samples": np.array(np.logspace(1, 5, 20), dtype=np.int32)
                }
            )
            
            # Find optimal parameters
            designer.optimize(method=BaseExperimentDesigner.OptimizerMethod.BRUTE_FORCE)
            best_params = designer.get_best_params()
            print(f"Best sample size: {best_params.parameters['n_samples']}")
            ```
        """

        self.experiment_factory = experiment_design_factory
        self.parameter_space: tp.Dict[str, tp.Iterable[Number]] = constraints
        self.optimizer_results: tp.List[BaseExperimentDesigner.OptimizerResult] = []

    def optimize(
        self,
        *,
        method: OptimizerMethod = OptimizerMethod.BRUTE_FORCE,
        method_kwargs: tp.Dict[str, tp.Any] | None = None,
    ):
        """
        Find the best experiment parameters by maximizing ExperimentDesignMetrics.
        
        This method searches through the parameter space defined by constraints
        and evaluates each configuration using the experiment_design_factory.
        
        Args:
            method: Optimization method to use. Currently only BRUTE_FORCE is supported.
            method_kwargs: Additional parameters for the optimization method (method-specific).
        """

        assert method == BaseExperimentDesigner.OptimizerMethod.BRUTE_FORCE, f"Only brute force optimization is supported, recieved {method}"

        best_metric = None

        parameter_names = list(self.parameter_space.keys())
        for parameter_point in product(*self.parameter_space.values()):
            exp_setup = {name: parameter for name, parameter in zip(parameter_names, parameter_point)}

            metric = self.experiment_factory(exp_setup)

            self.optimizer_results.append(BaseExperimentDesigner.OptimizerResult(
                parameters=exp_setup,
                experiment_design_metrics=metric,
            ))

            if best_metric is None or metric > best_metric:
                best_metric = metric

    def get_results(self) -> tp.List[OptimizerResult]:
        """
        Get all optimization results.
        
        Returns:
            List of OptimizerResult objects containing parameter configurations
            and their corresponding ExperimentDesignMetrics, ordered by evaluation order
            (not sorted by quality).
        """
        return self.optimizer_results

    def get_best_params(self) -> OptimizerResult | None:
        if not self.optimizer_results:
            return None

        return max(self.optimizer_results, key=lambda x: x.experiment_design_metrics)

    def visualize(
        self,
        parameters: tp.List[str] | None = None,
        figsize: tp.Tuple[int, int] | None = None,
        alpha=0.05,
        fixed_parameters: tp.Dict[str, tp.Union[Number, tp.List[Number]]] | None = None,
    ) -> tp.Tuple[plt.Figure, np.ndarray]:
        """
        Visualize experiment design metrics across different parameter values.
        
        Creates plots showing Type I and Type II errors for each parameter in the optimization space.
        
        Args:
            parameters: List of parameter names to visualize. If None, visualizes all parameters
                except those in fixed_parameters.
            figsize: Figure size as (width, height). If None, automatically calculated based on
                number of parameters.
            alpha: Significance level to display as reference line on Type I error plots.
            fixed_parameters: Dictionary mapping parameter names to fixed values. Results will be
                filtered to only include runs where these parameters match the specified values.
                Values can be either a single number or a list of numbers. Fixed parameters will
                not be plotted but will filter all other plots.
                Example: {'n_samples': 1000} or {'method': ['A', 'B']}
        
        Returns:
            Tuple of (figure, axes) where axes is a 2D numpy array of matplotlib axes objects.
        
        Raises:
            ValueError: If no optimization results are available, if parameter names are invalid,
                or if no results match the fixed parameters.
        
        Examples:
            ```python
            # Visualize all parameters
            fig, axes = designer.visualize()
            
            # Visualize specific parameters
            fig, axes = designer.visualize(parameters=['n_samples', 'effect_size'])
            
            # Fix some parameters and visualize others
            fig, axes = designer.visualize(
                parameters=['n_samples'],
                fixed_parameters={'method': 'A', 'alpha': 0.05}
            )
            
            # Fix parameter to multiple values (show results for any of these values)
            fig, axes = designer.visualize(
                fixed_parameters={'method': ['A', 'B']}
            )
            ```
        """
        if not self.optimizer_results:
            raise ValueError("No optimization results available. Run optimize() first.")
        
        # Filter results based on fixed_parameters
        filtered_results = self.optimizer_results
        if fixed_parameters:
            # Validate fixed parameter names
            for param in fixed_parameters:
                if param not in self.parameter_space:
                    raise ValueError(
                        f"Fixed parameter '{param}' not found in parameter space. "
                        f"Available parameters: {list(self.parameter_space.keys())}"
                    )
            
            # Filter results
            filtered_results = []
            for result in self.optimizer_results:
                include_result = True
                for param_name, fixed_value in fixed_parameters.items():
                    result_value = result.parameters[param_name]
                    # Handle both single values and lists of values
                    if isinstance(fixed_value, list):
                        if result_value not in fixed_value:
                            include_result = False
                            break
                    else:
                        if result_value != fixed_value:
                            include_result = False
                            break
                
                if include_result:
                    filtered_results.append(result)
            
            if not filtered_results:
                raise ValueError(
                    f"No results match the fixed parameters: {fixed_parameters}. "
                    f"Please check your fixed parameter values."
                )
        
        # Determine which parameters to visualize
        if parameters is None:
            parameters = list(self.parameter_space.keys())
            # Remove fixed parameters from visualization
            if fixed_parameters:
                parameters = [p for p in parameters if p not in fixed_parameters]
        else:
            # Validate parameter names
            for param in parameters:
                if param not in self.parameter_space:
                    raise ValueError(
                        f"Parameter '{param}' not found in parameter space. "
                        f"Available parameters: {list(self.parameter_space.keys())}"
                    )
            # Ensure fixed parameters are not in the visualization list
            if fixed_parameters:
                parameters = [p for p in parameters if p not in fixed_parameters]
        
        n_params = len(parameters)
        if n_params == 0:
            raise ValueError("No parameters to visualize")
        
        # Calculate figure size if not provided
        if figsize is None:
            figsize = (14, 4 * n_params)
        
        # Create subplots: 2 columns (Type I and Type II errors), n_params rows
        fig, axes = plt.subplots(
            nrows=n_params,
            ncols=2,
            figsize=figsize,
            squeeze=False
        )
        
        # Plot each parameter
        for i, param_name in enumerate(parameters):
            # Extract data for this parameter
            param_values = []
            type_I_errors = []
            type_II_errors = []
            
            for result in filtered_results:
                param_values.append(result.parameters[param_name])
                type_I_errors.append(result.experiment_design_metrics.type_I_error.parameter_estimate)
                type_II_errors.append(result.experiment_design_metrics.type_II_error.parameter_estimate)
            
            # Convert to numpy arrays
            param_values = np.array(param_values)
            type_I_errors = np.array(type_I_errors)
            type_II_errors = np.array(type_II_errors)
            
            # Check if parameter is categorical (has duplicate values)
            unique_values = np.unique(param_values)
            is_categorical = len(unique_values) < len(param_values)
            
            if is_categorical:
                # For categorical parameters, collect all values for each category
                type_I_data = []
                type_II_data = []
                x_labels = []
                
                for val in unique_values:
                    mask = param_values == val
                    type_I_data.append(type_I_errors[mask])
                    type_II_data.append(type_II_errors[mask])
                    x_labels.append(str(val))
                
                # Plot Type I error as box plot
                ax_type_I = axes[i, 0]
                bp1 = ax_type_I.boxplot(type_I_data, labels=x_labels, patch_artist=True)
                # Style the box plot
                for patch in bp1['boxes']:
                    patch.set_facecolor('steelblue')
                    patch.set_alpha(0.7)
                ax_type_I.axhline(y=alpha, color='r', linestyle='--', alpha=0.7, label=f'α = {alpha}')
                ax_type_I.set_xlabel(param_name, fontsize=12)
                ax_type_I.set_ylabel('Type I Error', fontsize=12)
                ax_type_I.set_title(f'Type I Error vs {param_name}', fontsize=13)
                ax_type_I.grid(True, alpha=0.3, axis='y')
                ax_type_I.legend()
                # Rotate x-axis labels if needed
                if len(x_labels) > 5:
                    ax_type_I.tick_params(axis='x', rotation=45)
                
                # Plot Type II error as box plot
                ax_type_II = axes[i, 1]
                bp2 = ax_type_II.boxplot(type_II_data, labels=x_labels, patch_artist=True)
                # Style the box plot
                for patch in bp2['boxes']:
                    patch.set_facecolor('orange')
                    patch.set_alpha(0.7)
                ax_type_II.set_xlabel(param_name, fontsize=12)
                ax_type_II.set_ylabel('Type II Error', fontsize=12)
                ax_type_II.set_title(f'Type II Error vs {param_name}', fontsize=13)
                ax_type_II.grid(True, alpha=0.3, axis='y')
                # Rotate x-axis labels if needed
                if len(x_labels) > 5:
                    ax_type_II.tick_params(axis='x', rotation=45)
            else:
                # For continuous parameters, sort and use line plots
                sorted_indices = np.argsort(param_values)
                param_values = param_values[sorted_indices]
                type_I_errors = type_I_errors[sorted_indices]
                type_II_errors = type_II_errors[sorted_indices]
                
                # Plot Type I error as line plot
                ax_type_I = axes[i, 0]
                ax_type_I.plot(param_values, type_I_errors, marker='o', linestyle='-', linewidth=2)
                ax_type_I.axhline(y=alpha, color='r', linestyle='--', alpha=0.7, label=f'α = {alpha}')
                ax_type_I.set_xlabel(param_name, fontsize=12)
                ax_type_I.set_ylabel('Type I Error', fontsize=12)
                ax_type_I.set_title(f'Type I Error vs {param_name}', fontsize=13)
                ax_type_I.grid(True, alpha=0.3)
                ax_type_I.legend()
                
                # Plot Type II error as line plot
                ax_type_II = axes[i, 1]
                ax_type_II.plot(param_values, type_II_errors, marker='o', linestyle='-',
                               linewidth=2, color='orange')
                ax_type_II.set_xlabel(param_name, fontsize=12)
                ax_type_II.set_ylabel('Type II Error', fontsize=12)
                ax_type_II.set_title(f'Type II Error vs {param_name}', fontsize=13)
                ax_type_II.grid(True, alpha=0.3)
        
        fig.suptitle('Experiment Design Metrics by Parameter', fontsize=16, y=1.0)
        fig.tight_layout()
        
        return fig, axes
