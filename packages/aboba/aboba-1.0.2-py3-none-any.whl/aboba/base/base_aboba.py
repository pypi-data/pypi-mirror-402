import logging

from typing import Any
from copy import deepcopy
from aboba.utils import warn_once

logger = logging.getLogger(__name__)


class AbobaBase:
    """
    Base class that provides a generic `set` method 
    with warnings for private or undefined fields.
    """
    
    __warn_cache = set()

    def set(self, key: str, value: Any):
        assert isinstance(key, str) and len(key) > 0
        if key[0] == "_":
            warn_once(
                logger,
                f"Seems like you are trying to set private field {key = } on {type(self) = }. "
                "Do not do this. The code will explode",
                cache=self.__warn_cache,
            )
        if key not in dir(self):
            warn_once(
                logger,
                f"Setting {key = } on {type(self) = } possibly has "
                "no effect as this field is not defined",
                cache=self.__warn_cache,
            )
        obj = deepcopy(self)
        setattr(obj, key, value)
        return obj
