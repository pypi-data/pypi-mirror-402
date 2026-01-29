from typing import List, Optional
import pandas as pd
import scipy.stats as sps
from statsmodels.formula.api import ols, wls
import numpy as np

from aboba.base import BaseTest, TestResult


class CupedLinearRegressionTTest(BaseTest):
    """
    CUPED via linear regression.

    Attributes:      
    covariate_names : List[str], optional
            List of pre-experiment covariates to adjust for
    group_column : str, default "group"
            Name of column containing group assignment (A/B)
    value_column : str, default "target"
            Name of column containing metric values to test
    weight_column : Optional[str]
        Column with observation weights.
    alpha : float, default 0.05
        Significance level for confidence interval.
    center_on_control : bool, default True
        If True, covariates are centered by their mean in control group.
    artefacts : Any
            Additional testing artifacts (unused in current implementation)
    """

    def __init__(
        self,
        covariate_names: Optional[List[str]] = None,
        group_column: str = "group",
        value_column: str = "target",
        alpha: float = 0.05,
        center_on_control: bool = True,
        weight_column: Optional[str] = None,
        include_extra: bool = False 
    ) -> None:
        super().__init__()
        self.value_column = value_column
        self.group_column = group_column
        self.covariate_names = covariate_names or []
        self.alpha = alpha
        self.center_on_control = center_on_control
        self.weight_column = weight_column
        self.include_extra = include_extra

    def test(self, groups: List[pd.DataFrame], artefacts) -> TestResult:
        assert len(groups) == 2, "CupedLinearRegressionTTest expects exactly two groups"
        a_group, b_group = groups

        data = pd.concat([a_group, b_group], ignore_index=True)

        feature_names: List[str] = [self.group_column]
        for name in self.covariate_names:
            if self.center_on_control:
                if self.weight_column is None:
                    mean_control = a_group[name].mean()
                else:
                    assert self.weight_column in a_group.columns, (
                        f"Weight column '{self.weight_column}' not found in control group"
                    )
                    w = a_group[self.weight_column].to_numpy(float)
                    x = a_group[name].to_numpy(float)
                    mean_control = float(np.average(x, weights=w))
                cname = f"{name}_c"
                data[cname] = data[name] - mean_control
                feature_names.append(cname)
            else:
                feature_names.append(name)

        formula = f"{self.value_column} ~ " + " + ".join(feature_names)

        if self.weight_column is None:
            model = ols(formula, data=data).fit(cov_type="HC3")
        else:
            assert self.weight_column in data.columns, (
                f"Weight column '{self.weight_column}' not found in data"
            )
            model = wls(
                formula,
                data=data,
                weights=data[self.weight_column],
            ).fit(cov_type="HC3")

        ef = model.params[self.group_column]
        se = model.bse[self.group_column]
        pvalue = model.pvalues[self.group_column]

        q = sps.norm.ppf(1 - self.alpha / 2)
        left_bound, right_bound  = ef - q * se, ef + q * se  
        extra = None
        if self.include_extra:
            extra = {
                "params": model.params,
                "design_matrix": model.model.exog,
                "resid": model.resid
            }

        return TestResult(pvalue=pvalue, effect=ef, effect_interval=(left_bound, right_bound),extra=extra if self.include_extra else None)
