from typing import List, Literal, Optional, Tuple
import dataclasses
import pandas as pd

from aboba.base.base_effect_modifier import EffectModifier
from aboba.base.base_data_sampler import DataSampler
from aboba.base.base_processors import BaseDataProcessor
from aboba.base.base_data_source import DataSource, BaseDataSource
from aboba.base.base_aboba import AbobaBase


@dataclasses.dataclass
class TestResult:
    """
    Represents the result of a statistical test, including p-value, effect, effect type,
    and optional effect interval.
    """

    pvalue: float
    effect: Optional[float] = None
    effect_type: Literal["absolute", "relative_test", "relative_control"] = "absolute"
    effect_interval: Optional[Tuple[float, float]] = None    
    extra: dict = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class _BaseTestCache:
    """
    Internal cache holding the data and artifacts used for a test.
    """

    data: pd.DataFrame
    artefacts: dict


class BaseTest(AbobaBase):
    """
    Base class for AB-tests, providing a structure for fitting and testing data.
    """
    
    def __init__(self,):
        super().__init__()

    def fit(self, data: DataSource):
        pass

    def test(self, groups: List[pd.DataFrame], artefacts) -> TestResult:
        raise NotImplemented("test method should be defined by derived AB-tests")
