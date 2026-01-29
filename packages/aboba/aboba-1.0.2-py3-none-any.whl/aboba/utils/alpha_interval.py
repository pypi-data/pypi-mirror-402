from statsmodels.stats.proportion import proportion_confint


def calculate_real_alpha(n_errors: int, n_iter: int, method: str = "wilson"):
    """

    Estimate real alpha level and its interval

    Args:
        n_errors (int): number of errors in an experiment
        n_iter (int): number of experiments
        method (str): `proportion_confint` method

    Returns:
        Tuple[float, float, float]: real_alpha, left_alpha, right_alpha
    """

    real_alpha = n_errors / n_iter
    left_alpha, right_alpha = proportion_confint(n_errors, n_iter, method=method)

    return real_alpha, left_alpha, right_alpha
