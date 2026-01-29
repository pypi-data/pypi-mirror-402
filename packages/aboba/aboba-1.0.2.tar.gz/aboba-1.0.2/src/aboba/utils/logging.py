from typing import Optional

_cache = set()


def warn_once(logger, message, cache: Optional[set] = None, *args, **kwargs):
    if cache is None:
        cache = _cache
    if message in cache:
        return
    cache.add(message)
    logger.warning(message, *args, **kwargs)
