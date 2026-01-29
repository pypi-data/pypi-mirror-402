import operator
from typing import Any, Callable, Dict, Optional, Union
from numbers import Number
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
from scipy.stats._distn_infrastructure import rv_frozen
from aboba.base.base_effect_modifier import BaseEffectModifier


class TimeBasedEffectModifier(BaseEffectModifier):
    """
    Adds time-based effects to a column, accounting for when users entered the experiment.
    
    This modifier is designed for experiments where:
    - Users can be included in the treatment group at different times
    - The effect starts from a specific date (effect_start_date)
    - The effect optionally ends at a specific date (effect_end_date)
    - Only users in the treatment group who were included before or at the effect start date
      and have observations within the effect period receive the effect
    
    Args:
        effect: The effect to apply. Can be:
            - float: constant effect added to all qualifying observations
            - rv_frozen: random values sampled for each observation
            - np.random.RandomState/Generator: random values drawn for each observation
            - callable: applied row-wise to qualifying observations
        effect_start_date: Date when the effect begins (datetime or string)
        effect_end_date: Date when the effect ends (datetime or string, optional).
            If None, effect continues indefinitely after start date.
        value_column: Column name containing the values to modify
        date_column: Column name containing the observation dates
        group_column: Column name indicating group membership (0=control, 1=treatment)
        inclusion_date_column: Column name containing when each user was included in treatment
        method: Operator to apply the effect (default: operator.add)
    
    Examples:
        ```python
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta
        from aboba.effect_modifiers import TimeBasedEffectModifier
        
        # Create sample time-series data
        dates = pd.date_range('2024-01-01', '2024-12-31', freq='D')
        data = pd.DataFrame({
            'user_id': np.repeat(range(100), len(dates)),
            'date': np.tile(dates, 100),
            'payment': np.random.uniform(10, 100, len(dates) * 100),
            'is_in_b_group': 0,
            'inclusion_date': pd.NaT
        })
        
        # Some users included in treatment at different times
        treatment_users = np.random.choice(100, 30, replace=False)
        for user in treatment_users:
            inclusion_date = np.random.choice(dates[:200])  # Included in first 200 days
            mask = data['user_id'] == user
            data.loc[mask, 'is_in_b_group'] = 1
            data.loc[mask, 'inclusion_date'] = inclusion_date
        
        # Apply effect starting from a specific date
        modifier = TimeBasedEffectModifier(
            effect=5.0,  # +5 to payment
            effect_start_date='2024-07-01',
            value_column='payment',
            date_column='date',
            group_column='is_in_b_group',
            inclusion_date_column='inclusion_date'
        )
        
        # Split into groups and apply effect
        groups = [
            data[data['is_in_b_group'] == 0],
            data[data['is_in_b_group'] == 1]
        ]
        modified_groups = modifier.add_effect(groups)
        ```
    """
    
    def __init__(
        self,
        effect: Union[float, Callable, rv_frozen, np.random.RandomState, np.random.Generator],
        effect_start_date: Union[str, datetime],
        effect_end_date: Optional[Union[str, datetime]] = None,
        value_column: str = "value",
        date_column: str = "date",
        group_column: str = "is_in_b_group",
        inclusion_date_column: str = "inclusion_date",
        method: Callable[[Any, Any], Any] = operator.add
    ):
        """
        Initialize the time-based effect modifier.
        """
        self.effect = effect
        self.value_column = value_column
        self.date_column = date_column
        self.group_column = group_column
        self.inclusion_date_column = inclusion_date_column
        self.method = method
        
        # Convert effect_start_date to datetime if it's a string
        if isinstance(effect_start_date, str):
            self.effect_start_date = pd.to_datetime(effect_start_date)
        else:
            self.effect_start_date = effect_start_date
        
        # Convert effect_end_date to datetime if it's a string
        if effect_end_date is not None:
            if isinstance(effect_end_date, str):
                self.effect_end_date = pd.to_datetime(effect_end_date)
            else:
                self.effect_end_date = effect_end_date
        else:
            self.effect_end_date = None
    
    def add_effect(self, groups: list[pd.DataFrame]) -> list[pd.DataFrame]:
        """
        Apply time-based effect to the treatment group.
        
        The effect is applied only to observations that:
        1. Are in the treatment group (group_column == 1)
        2. Have observation date >= effect_start_date
        3. Have observation date <= effect_end_date (if effect_end_date is specified)
        4. Have inclusion_date <= effect_start_date (user was already in treatment when effect started)
        
        Args:
            groups: List of DataFrames representing different groups
        
        Returns:
            List of DataFrames with effect applied to qualifying observations
        """
        modified_groups = []
        
        for group in groups:
            # Create a copy to avoid modifying the original
            group_copy = group.copy()
            
            # Check if this is the treatment group
            assert self.group_column in group_copy.columns
            
            # Find observations that should receive the effect
            # 1. In treatment group
            is_treatment = group_copy[self.group_column] == 1
            
            # 2. Observation date is after effect start
            obs_date = pd.to_datetime(group_copy[self.date_column])
            after_effect_start = obs_date >= self.effect_start_date
            
            # 3. Observation date is before effect end (if specified)
            if self.effect_end_date is not None:
                before_effect_end = obs_date <= self.effect_end_date
            else:
                before_effect_end = True  # No end date means effect continues indefinitely
            
            # 4. User was included before effect started (or at the same time)
            if self.inclusion_date_column in group_copy.columns:
                inclusion_date = pd.to_datetime(group_copy[self.inclusion_date_column])
                included_before_effect = inclusion_date <= self.effect_start_date
            else:
                # If no inclusion date column, assume all treatment users were included from the start
                included_before_effect = is_treatment
            
            # Combine all conditions
            mask = is_treatment & after_effect_start & before_effect_end & included_before_effect
            
            # Apply effect to qualifying observations
            if mask.any():
                value = group_copy.loc[mask, self.value_column]
                effect_val = self._evaluate_effect(self.effect, value)
                group_copy.loc[mask, self.value_column] = self.method(value, effect_val)
            
            modified_groups.append(group_copy)
        
        return modified_groups
    
    def _evaluate_effect(
        self,
        effect: Union[float, rv_frozen, np.random.RandomState, np.random.Generator],
        value: pd.Series
    ) -> Union[float, np.ndarray]:
        """
        Evaluate the effect based on its type.
        
        Args:
            effect: The effect specification
            value: Series of values to apply effect to
        
        Returns:
            Either a scalar or array of effect values
        """
        if isinstance(effect, Number):
            return effect
        elif isinstance(effect, rv_frozen):
            return effect.rvs(size=value.size)
        elif isinstance(effect, np.random.RandomState):
            return effect.random(size=value.size)
        elif isinstance(effect, np.random.Generator):
            return effect.random(size=value.size)
        else:
            raise ValueError(f"Unknown effect type in _evaluate_effect: {type(effect)}")