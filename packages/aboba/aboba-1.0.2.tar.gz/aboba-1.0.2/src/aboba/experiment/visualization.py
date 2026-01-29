import matplotlib.pyplot as plt
import numpy as np

from typing import Dict, List

from aboba.experiment.experiment_data import ExperimentData
from aboba.utils import draw_interval, draw_pvalue_distribution, calculate_real_alpha


def _get_axes_limits_by_column(draw_cols, axes) -> List[List[float]]:
    """

    Groups entries by columns and returns common x-axis limits for each column

    """
    by_col_lims = [list(ax.get_xlim()) for ax in axes[:draw_cols]]
    for i, ax in enumerate(axes):
        lims = ax.get_xlim()
        for side in range(2):
            agg = min if side == 0 else max
            by_col_lims[i % draw_cols][side] = agg(
                by_col_lims[i % draw_cols][side], lims[side]
            )
    return by_col_lims


def default_visualization_method(
    groups: Dict[str, ExperimentData], alpha, experiment_name, **kwargs
):
    assert 0.0 < alpha < 1.0

    # gather non-empty experiments
    experiments = list(
        filter(lambda x: not x[1].is_empty(), groups.items())
    )

    # one column for pvalue distribution, one column for pvalue intervals
    draw_cols = 2
    n_rows = len(experiments)

    fig, axes = plt.subplots(
        nrows=n_rows, ncols=draw_cols, figsize=(8 * draw_cols, int(1.75 * n_rows))
    )
    axes = np.ravel(axes)

    for i in range(len(experiments)):
        experiment = experiments[i][0]
        data = groups[experiment]

        n_iter = len(data.history)
        n_errors = sum(int(i.pvalue < alpha) for i in data.history)
        real_alpha, left_alpha, right_alpha = calculate_real_alpha(
            n_iter=n_iter, n_errors=n_errors
        )

        ax_interval = axes[2 * i]
        ax_distribution = axes[2 * i + 1]

        draw_interval(
            real_alpha,
            left_alpha,
            right_alpha,
            axes=ax_interval,
            alpha=alpha,
            name=experiment,
        )

        draw_pvalue_distribution(
            pvals=[test_result.pvalue for test_result in data.history],
            axes=ax_distribution,
            name=experiment,
        )

    for ax, experiment in zip(axes, experiments):
        data = groups[experiment[0]]
        n_iter = len(data.history)
        n_errors = sum(int(i.pvalue < alpha) for i in data.history)
        real_alpha, left_alpha, right_alpha = calculate_real_alpha(
            n_iter=n_iter, n_errors=n_errors
        )

    by_col_lims = _get_axes_limits_by_column(draw_cols, axes)

    for i, ax in enumerate(axes):
        ax.set_xlim(by_col_lims[i % draw_cols])

    fig.suptitle(experiment_name, fontsize=16)
    fig.tight_layout()
    return fig, axes
