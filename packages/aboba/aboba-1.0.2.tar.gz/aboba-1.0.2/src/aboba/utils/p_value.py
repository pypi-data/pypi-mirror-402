import scipy.stats as sps


def compute_pvalue(t_stat: float, df: float, alternative: str) -> float:
    """
    Compute p-value for a t-statistic with given degrees of freedom
    for different alternatives.
    """

    if alternative == "two-sided":
        return 2.0 * sps.t.sf(abs(t_stat), df)
    elif alternative == "greater":
        return float(sps.t.sf(t_stat, df))
    elif alternative == "less":
        return float(sps.t.cdf(t_stat, df))
    else:
        raise ValueError(f"Unknown alternative: {alternative!r}")
