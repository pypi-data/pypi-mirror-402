import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Union


def generate_time_based_data(
    n_users: int = 200,
    start_date: Union[str, datetime] = '2024-01-01',
    end_date: Union[str, datetime] = '2024-12-31',
    treatment_ratio: float = 0.3,
    payment_mean: float = 50,
    payment_std: float = 20,
    user_id_column: str = 'user_id',
    date_column: str = 'date',
    value_column: str = 'payment',
    group_column: str = 'is_in_b_group',
    inclusion_date_column: str = 'inclusion_date',
    max_inclusion_days: int = 200,
    random_state: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate synthetic time-based experimental data for testing TimeBasedDesigner.
    
    This function creates a dataset with:
    - Multiple users with daily observations
    - Some users assigned to treatment group at different times
    - Payment values drawn from a normal distribution
    - Realistic temporal structure for A/B testing
    
    Args:
        n_users: Number of unique users to generate
        start_date: Start date of the observation period
        end_date: End date of the observation period
        treatment_ratio: Proportion of users to assign to treatment group
        payment_mean: Mean payment value
        payment_std: Standard deviation of payment values
        user_id_column: Name for the user ID column
        date_column: Name for the date column
        value_column: Name for the value/payment column
        group_column: Name for the group indicator column
        inclusion_date_column: Name for the inclusion date column
        max_inclusion_days: Maximum number of days from start_date when users can be included
        random_state: Random seed for reproducibility
    
    Returns:
        DataFrame with columns:
        - user_id: User identifier
        - date: Observation date
        - payment: Payment value
        - is_in_b_group: 0 for control, 1 for treatment
        - inclusion_date: Date when user was included in treatment (NaT for control)
    
    Examples:
        ```python
        from aboba.design.time_based_data_generator import generate_time_based_data
        
        # Generate sample data
        data = generate_time_based_data(
            n_users=200,
            start_date='2024-01-01',
            end_date='2024-12-31',
            treatment_ratio=0.3,
            random_state=42
        )
        
        print(f"Total observations: {len(data)}")
        print(f"Unique users: {data['user_id'].nunique()}")
        print(f"Treatment users: {(data['is_in_b_group'] == 1).sum() / len(data):.2%}")
        ```
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    # Convert dates to datetime
    if isinstance(start_date, str):
        start_date = pd.to_datetime(start_date)
    if isinstance(end_date, str):
        end_date = pd.to_datetime(end_date)
    
    # Generate date range
    dates = pd.date_range(start_date, end_date, freq='D')
    n_days = len(dates)
    
    # Create base dataframe with all user-date combinations
    user_ids = np.arange(n_users)
    
    # Create data structure
    data_list = []
    
    # Determine which users are in treatment
    n_treatment = int(n_users * treatment_ratio)
    treatment_users = np.random.choice(user_ids, size=n_treatment, replace=False)
    
    for user_id in user_ids:
        is_treatment = user_id in treatment_users
        
        # Determine inclusion date for treatment users
        if is_treatment:
            # Random inclusion date within the first max_inclusion_days
            inclusion_day_offset = np.random.randint(0, min(max_inclusion_days, n_days))
            inclusion_date = start_date + timedelta(days=int(inclusion_day_offset))
        else:
            inclusion_date = pd.NaT
        
        # Generate daily observations for this user
        for date in dates:
            # Generate payment value with some user-specific variation
            user_baseline = np.random.normal(0, payment_std * 0.3)  # User-specific baseline
            daily_noise = np.random.normal(0, payment_std * 0.7)  # Daily variation
            payment = payment_mean + user_baseline + daily_noise
            
            # Ensure payment is positive
            payment = max(payment, 10)
            
            data_list.append({
                user_id_column: user_id,
                date_column: date,
                value_column: payment,
                group_column: 1 if is_treatment else 0,
                inclusion_date_column: inclusion_date
            })
    
    # Create DataFrame
    data = pd.DataFrame(data_list)
    
    return data


def generate_time_based_data_with_seasonality(
    n_users: int = 200,
    start_date: Union[str, datetime] = '2024-01-01',
    end_date: Union[str, datetime] = '2024-12-31',
    treatment_ratio: float = 0.3,
    payment_mean: float = 50,
    payment_std: float = 20,
    seasonality_amplitude: float = 10,
    seasonality_period_days: int = 7,
    user_id_column: str = 'user_id',
    date_column: str = 'date',
    value_column: str = 'payment',
    group_column: str = 'is_in_b_group',
    inclusion_date_column: str = 'inclusion_date',
    max_inclusion_days: int = 200,
    random_state: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate synthetic time-based data with seasonal patterns.
    
    Similar to generate_time_based_data but adds periodic seasonality to the payment values.
    This is useful for testing how the designer handles data with temporal patterns.
    
    Args:
        n_users: Number of unique users to generate
        start_date: Start date of the observation period
        end_date: End date of the observation period
        treatment_ratio: Proportion of users to assign to treatment group
        payment_mean: Mean payment value
        payment_std: Standard deviation of payment values
        seasonality_amplitude: Amplitude of seasonal variation
        seasonality_period_days: Period of seasonality in days (e.g., 7 for weekly)
        user_id_column: Name for the user ID column
        date_column: Name for the date column
        value_column: Name for the value/payment column
        group_column: Name for the group indicator column
        inclusion_date_column: Name for the inclusion date column
        max_inclusion_days: Maximum number of days from start_date when users can be included
        random_state: Random seed for reproducibility
    
    Returns:
        DataFrame with time-series data including seasonal patterns
    
    Examples:
        ```python
        from aboba.design.time_based_data_generator import generate_time_based_data_with_seasonality
        
        # Generate data with weekly seasonality
        data = generate_time_based_data_with_seasonality(
            n_users=200,
            seasonality_amplitude=15,
            seasonality_period_days=7,
            random_state=42
        )
        ```
    """
    # First generate base data
    data = generate_time_based_data(
        n_users=n_users,
        start_date=start_date,
        end_date=end_date,
        treatment_ratio=treatment_ratio,
        payment_mean=payment_mean,
        payment_std=payment_std,
        user_id_column=user_id_column,
        date_column=date_column,
        value_column=value_column,
        group_column=group_column,
        inclusion_date_column=inclusion_date_column,
        max_inclusion_days=max_inclusion_days,
        random_state=random_state
    )
    
    # Add seasonality
    start_date_dt = pd.to_datetime(start_date)
    data['_days_from_start'] = (data[date_column] - start_date_dt).dt.days
    
    # Add sinusoidal seasonality
    seasonal_component = seasonality_amplitude * np.sin(
        2 * np.pi * data['_days_from_start'] / seasonality_period_days
    )
    
    data[value_column] = data[value_column] + seasonal_component
    
    # Ensure payments remain positive
    data[value_column] = data[value_column].clip(lower=10)
    
    # Remove temporary column
    data = data.drop(columns=['_days_from_start'])
    
    return data