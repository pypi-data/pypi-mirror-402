from typing import Optional, List

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


def draw_interval(
    real_alpha: float,
    left_alpha: float,
    right_alpha: float,
    axes: plt.Axes,
    alpha: float = 0.05,
    name: Optional[str] = None,
):
    """

    Draw confidence interval

    Args:
        real_alpha (float): alpha estimation
        left_alpha (float): interval left border
        right_alpha (float): interval right border
        alpha (float): theoretical alpha
        axes (plt.Axes): axes to use
        name (str): name for this plot

    """

    with sns.axes_style("whitegrid"):
        axes.hlines(0, 0, 1, color="black", lw=2, alpha=0.6)
        axes.vlines(alpha, -2, 2, color="red", lw=5, linestyle="--", alpha=0.6)
        axes.fill_between(
            [left_alpha, right_alpha], [0.15] * 2, [-0.15] * 2, color="green", alpha=0.6
        )
        axes.scatter(real_alpha, 0, s=300, marker="*", color="red")
        axes.set_xlim((min(alpha, left_alpha) - 1e-3, max(alpha, right_alpha) + 1e-3))
        if name is not None:
            axes.set_title(
                f"{name} | rejections = {100 * real_alpha:.2f}%, "
                f"({100 * left_alpha:.2f}%, {100 * right_alpha:.2f}%)"
            )
        else:
            axes.set_title(
                f"Rejections  = {100 * real_alpha:.2f}%, "
                f"({100 * left_alpha:.2f}%, {100 * right_alpha:.2f}%)"
            )
        axes.set_ylim((-0.5, 0.5))
        axes.set_yticks([])


def draw_pvalue_distribution(
    pvals: List[float], axes: plt.Axes, name: Optional[str] = None
):
    """

    Draw pvalue distribution

    Args:
        pvals (List[float]): pvalues
        axes (plt.Axes): axes to use
        name (str): name for this plot
    """

    with sns.axes_style("whitegrid"):
        axes.hist(
            pvals,
            bins=np.linspace(0, 1, 21),
            alpha=0.7,
            weights=np.ones(len(pvals)) / len(pvals),
        )

        if name is not None:
            axes.set_title(f"{name} | pvalue distribution")
        else:
            axes.set_title("pvalue distribution")

    plt.title("Распределение p-value")
