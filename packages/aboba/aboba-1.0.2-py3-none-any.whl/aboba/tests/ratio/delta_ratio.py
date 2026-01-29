from typing import List
import pandas as pd
import numpy as np
import scipy.stats as sps

from aboba.base import BaseTest, TestResult

class DeltaRatioTtest(BaseTest):
    """
        Implementation of t-test for ratio metrics using asymptotic variance 
        estimated via the delta method.

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
        alpha : float, default=0.05
            Significance level for confidence intervals
    """   
 
    def __init__(
        self,
        numerator_name : str = 'session_lengths',
        denominator_name: str =None, 
        user_name: str ='user_id', 
        alpha = 0.05
    ):
        super().__init__()
        self.numerator_name = numerator_name
        self.denominator_name = denominator_name
        self.user_name = user_name
        self.alpha = alpha

    def ratio_metric(self, data, numerator_name, denominator_name):
        """
        Computes a ratio metric from the given data.  

        Attributes:
        data : pd.DataFrame
              Input data containing the metric values
        numerator_name : str
              Name of the column containing numerator values
        denominator_name : str or None
              Name of the column containing denominator values.
             If None, computes simple mean of numerator.
                    
        """
        if denominator_name is None:
            return data[numerator_name].mean()
        else:
            return data[numerator_name].sum() / data[denominator_name].sum()
            
    def ratio_var(self, data, numerator_name, denominator_name, user_name):
        """
        Estimates the asymptotic variance of a ratio metric using the delta method.
        
       Attributes:
        data : pd.DataFrame
            Input data containing the metric values
        numerator_name : str
            Name of the column containing the numerator values for the ratio metric
        denominator_name : str
            Name of the column containing the denominator values for the ratio metric
        user_name : str
            Name of the column containing user identifiers
            
        Returns:
        float
            The estimated asymptotic variance of the ratio metric

        """
        user_sums = data.groupby(user_name).sum()        
        mean1, mean2 = user_sums.mean().loc[[numerator_name, denominator_name]]
        var1, var2 = user_sums.var().loc[[numerator_name, denominator_name]] / len(user_sums)
        cov = user_sums.cov().loc[numerator_name, denominator_name] / len(user_sums)
        
        return  (
          var1 / mean2**2
          + var2 * mean1**2 / mean2**4
          - 2 * cov * mean1 / mean2**3
        )


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
        a_mean = self.ratio_metric(a_group, self.numerator_name, self.denominator_name)
        b_mean = self.ratio_metric(b_group, self.numerator_name, self.denominator_name)
        a_var = self.ratio_var(a_group, self.numerator_name, self.denominator_name, user_name=self.user_name)
        b_var = self.ratio_var(b_group, self.numerator_name, self.denominator_name, user_name=self.user_name)
        stat = b_mean - a_mean
        var = a_var + b_var
        std = np.sqrt(var)    
        z_stat = stat / std
        pvalue = 2*sps.norm.sf(np.abs(z_stat))        
        q = sps.norm.ppf(1 - self.alpha/2)
        left_bound = stat - q*std
        right_bound = stat + q*std
        return TestResult(pvalue=pvalue, effect=stat, effect_type = "absolute", effect_interval = (left_bound, right_bound))