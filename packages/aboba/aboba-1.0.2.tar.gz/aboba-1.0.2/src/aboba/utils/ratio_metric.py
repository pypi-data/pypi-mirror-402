def ratio_metric(data, numerator_name, denominator_name):
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
  