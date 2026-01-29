"""
Statictical tests for multiple groups
"""


from .f_test import FIndependentTest, FRelatedTest, FOneWayIndependentTest
from .bartlet import BartletIndependentTest
from .hsd import HSDTukeyTest
from .kruskal import KruskalIndependentTest
from .dunn import PostHocDunnTest
