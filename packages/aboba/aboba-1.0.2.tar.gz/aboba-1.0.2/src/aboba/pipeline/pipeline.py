import pandas as pd
from typing import List, Tuple, Union
from aboba.base.base_aboba import AbobaBase
from aboba.base.base_data_sampler import BaseDataSampler
from aboba.base.base_processors import BaseDataProcessor


class Pipeline(AbobaBase):
    """
    A sequence of data preprocessors with one optional sampler.
    Pipeline allows you to sequentially apply preprocessors to your data. If sampler is given then, when its turn comes, 
    the groups are sampled from the data and the following preprocessors will be applied to each group produced by the sampler.

    Examples:

    from aboba import tests
    from aboba import samplers
    from aboba import effect_modifiers
    from aboba import processing
    from aboba import pipelines

    import numpy as np
    import pandas as pd
    import scipy.stats as sps

    data_a = sps.norm.rvs(size=1000, loc=0, scale=100)
    data_b = sps.norm.rvs(size=1000, loc=0, scale=100)

    data_a_cov = data_a + sps.norm.rvs(size=1000, loc=0, scale=0.5)
    data_b_cov = data_b + sps.norm.rvs(size=1000, loc=0, scale=0.5)

    data_a_strat = sps.bernoulli.rvs(p=0.15, size=1000)
    data_b_strat = sps.bernoulli.rvs(p=0.15, size=1000)

    # dataset of two columns: value and group
    data = pd.DataFrame({
        'value': np.concatenate([
            data_a,
            data_b,
        ]),
        'covariate': np.concatenate([
            data_a_cov,
            data_b_cov,
        ]),
        'strat': np.concatenate([
            data_a_strat,
            data_b_strat,
        ]),
        'b_group': np.concatenate([
            np.repeat(0, 1000),
            np.repeat(1, 1000),
        ]),
    })

    cuped_preprocess = processing.CupedProcessor(
        value_column='value',
        covariate_column='covariate',
        result_column='value',
        group_column='b_group',
        group_test=1,
        group_control=0,
    )

    ensurecol_preprocess = processing.EnsureColsProcessor(cols=['value', 'covariate'])

    pipeline_cuped = pipelines.Pipeline([
        ('cuped', cuped_preprocess),
        ('sampler', sampler),
        ('ensurecols', ensurecol_preprocess)
    ])

    pipeline_cuped.fit(data) 
    result = pipeline_cuped.transform(data)
    """

    def __init__(self, steps: List[Tuple[str, Union[BaseDataSampler, BaseDataProcessor]]]):
        # TODO: use names to pretty print pipeline
        self.names = [] 
        self.transformers = []

        for i in range(len(steps)):
            step = steps[i]
            if isinstance(step, tuple):
                if len(step) > 1:
                    step_transformer = step[1]
                    step_name = step[0]
                else:
                    step_transformer = step[0]
                    step_name = type(step_transformer).__name__

                self.transformers.append(step_transformer)
                self.names.append(step_name)
            else:
                self.transformers.append(step)
                self.names.append(type(step).__name__)

            if not isinstance(self.transformers[-1], BaseDataSampler) and not isinstance(self.transformers[-1], BaseDataProcessor):
                raise TypeError("Object must be Sampler or Processor to be in pipeline")


    def fit(self, data: pd.DataFrame):
        for transformer in self.transformers:
            transformer.fit(data)
            if isinstance(transformer, BaseDataProcessor):
                if isinstance(data, pd.DataFrame):
                    data, artefacts = transformer.transform(data)
                elif isinstance(data, list):
                    processed = [transformer.transform(group) for group in data]
                    data = [group[0] for group in processed]
                    artefacts = [group[1] for group in processed] # TODO: remove artefacts if not needed
            elif isinstance(transformer, BaseDataSampler):
                if not isinstance(data, pd.DataFrame):
                    raise TypeError("Only one Sampler is allowed in pipeline")
                
                data = transformer.sample(data, None)
            else:
                raise TypeError("Object must be Sampler or Processor to be in pipeline")

        return self
    
    def transform(self, data: Union[pd.DataFrame, List[pd.DataFrame]]) -> Union[pd.DataFrame, List[pd.DataFrame]]:
        artefacts = {}
        for transformer in self.transformers:
            if isinstance(transformer, BaseDataProcessor):
                if isinstance(data, pd.DataFrame):
                    data, artefacts = transformer.transform(data) 
                elif isinstance(data, list):
                    processed = [transformer.transform(group) for group in data]
                    data = [group[0] for group in processed]
                    artefacts = [group[1] for group in processed]
                else:
                    raise TypeError("Data must be pd.DataFrame or List[pd.DataFrame] to be handled by Pipeline")

            elif isinstance(transformer, BaseDataSampler):
                if not isinstance(data, pd.DataFrame):
                    raise TypeError("Only one Sampler is allowed in pipeline")
                data = transformer.sample(data, artefacts) 

        return data 
