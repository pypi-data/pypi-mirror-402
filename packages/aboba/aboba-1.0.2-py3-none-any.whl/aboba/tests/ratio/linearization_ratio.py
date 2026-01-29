
from typing import List
import pandas as pd
import numpy as np
import scipy.stats as sps

from aboba.base import BaseTest, TestResult
from aboba.utils import ratio_metric
from aboba.tests.absolute_ttest import AbsoluteIndependentTTest


class LinearizationRatioTtest(BaseTest):

    """
    Implementation of t-test for ratio metric using linearization approach.
    Attributes:        
        groups : List[pd.DataFrame]
            Two samples of equal size (control and treatment groups)
        numerator_name : str
            Name of the column containing the numerator values
        denominator_name : str, optional
            Name of the column containing denominator values.
            If None, will create a denominator column of 1s (simple mean case)
        user_name : str
            Name of the column containing user identifiers
        eta : float
            Weighting parameter (0 ≤ η ≤ 1) for combining group statistics    
        alpha : float, default=0.05
            Significance level for confidence intervals      
    """
    
    def __init__(
        self,
        numerator_name : str = 'session_lengths',
        denominator_name: str =None, 
        user_name: str ='user_id', 
        eta = 0,
        alpha = 0.05
    ):
        super().__init__()
        self.numerator_name = numerator_name
        self.denominator_name = denominator_name
        self.user_name = user_name
        self.eta = eta
        self.alpha = alpha

    def linearization(self,
          a_group,
          b_group,
          result_name: str = "linearization_values"
            ):
        """
        Transforms the ratio metric problem into a linearized form suitable for t-test analysis.
        """

        if self.denominator_name is None:
            a_group = a_group.copy()
            b_group = b_group.copy()
            self.denominator_name = "ratio_denominator"        
        if self.denominator_name not in a_group.columns:
                a_group[self.denominator_name] = 1 
        if self.denominator_name not in b_group.columns:
                b_group[self.denominator_name] = 1
        kappa = (1 - self.eta) * ratio_metric(
             a_group, self.numerator_name, self.denominator_name
        ) + self.eta * ratio_metric( b_group, self.numerator_name, self.denominator_name)

        control_users =  a_group.groupby(self.user_name).sum()
        test_users =  b_group.groupby(self.user_name).sum()
        control_users[result_name] = (
            control_users[self.numerator_name] - kappa * control_users[self.denominator_name]
        )
        test_users[result_name] = (
            test_users[self.numerator_name] - kappa * test_users[self.denominator_name]
        )
        return control_users, test_users    

    def test(self, groups: List[pd.DataFrame], artefacts) -> TestResult:
        assert isinstance(groups[0], pd.DataFrame), "a_group must be DataFrame"
        assert isinstance(groups[1], pd.DataFrame), "b_group must be DataFrame"

        a_group, b_group = groups
        if self.denominator_name is None:
            self.denominator_name = 'ratio_denominator'
        if self.denominator_name not in a_group.columns:            
            a_group = a_group.copy()
            a_group[self.denominator_name] = 1 
        if self.denominator_name not in b_group.columns:
            b_group = b_group.copy()
            b_group[self.denominator_name] = 1 
        a_group,  b_group = self.linearization(
            a_group,
            b_group
            )

        name = "linearization_values"    
        col = name
        ttest = AbsoluteIndependentTTest(
            value_column=col,
            equal_var=False,      
            alternative="two-sided",
            alpha=self.alpha,
        )

        res = ttest.test([a_group, b_group], artefacts)
        coef = (
            (1 - self.eta) * float(a_group[self.denominator_name].mean())
            + self.eta * float(b_group[self.denominator_name].mean())
        )

        effect = res.effect / coef
        ci = None
        if res.effect_interval is not None:
            left, right = res.effect_interval
            ci = (left / coef, right / coef)

        return TestResult(
            pvalue=res.pvalue,
            effect=effect,
            effect_type="absolute",
            effect_interval=ci,
        )


class LinearizationRatioTtest_sps(BaseTest):
    def __init__(
        self,
        numerator_name : str = 'session_lengths',
        denominator_name: str =None, 
        user_name: str ='user_id', 
        eta = 0,
        alpha = 0.05
    ):
        super().__init__()
        self.numerator_name = numerator_name
        self.denominator_name = denominator_name
        self.user_name = user_name
        self.eta = eta
        self.alpha = alpha

    def linearization(self,
          a_group,
          b_group,
          result_name: str = "linearization_values"
            ):
        if self.denominator_name is None:
            a_group = a_group.copy()
            b_group = b_group.copy()
            self.denominator_name = "ratio_denominator"        
        if self.denominator_name not in a_group.columns:
                a_group[self.denominator_name] = 1 
        if self.denominator_name not in b_group.columns:
                b_group[self.denominator_name] = 1
        kappa = (1 - self.eta) * ratio_metric(
             a_group, self.numerator_name, self.denominator_name
        ) + self.eta * ratio_metric( b_group, self.numerator_name, self.denominator_name)

        control_users =  a_group.groupby(self.user_name).sum()
        test_users =  b_group.groupby(self.user_name).sum()
        control_users[result_name] = (
            control_users[self.numerator_name] - kappa * control_users[self.denominator_name]
        )
        test_users[result_name] = (
            test_users[self.numerator_name] - kappa * test_users[self.denominator_name]
        )
        return control_users, test_users    

    def test(self, groups: List[pd.DataFrame], artefacts) -> TestResult:
        assert isinstance(groups[0], pd.DataFrame), "a_group must be DataFrame"
        assert isinstance(groups[1], pd.DataFrame), "b_group must be DataFrame"
        a_group, b_group = groups
        if self.denominator_name is None:
            self.denominator_name = 'ratio_denominator'
        if self.denominator_name not in a_group.columns:
            a_group[self.denominator_name] = 1 
        if self.denominator_name not in b_group.columns:
            b_group[self.denominator_name] = 1 
        a_group,  b_group = self.linearization(
            a_group,
            b_group
            )
        name = "linearization_values"    

        res = sps.ttest_ind(a_group[name], b_group[name])
        stat = res.statistic
        pvalue = res.pvalue
        left_bound, right_bound = res.confidence_interval()
        coef = self.eta * a_group[self.denominator_name].mean() + (1 - self.eta) * b_group[self.denominator_name].mean()
        left_bound /= coef
        right_bound /= coef
        return TestResult(pvalue=pvalue, effect=stat, effect_type = "absolute", effect_interval = (left_bound, right_bound))
