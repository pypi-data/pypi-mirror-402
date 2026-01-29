from typing import Callable

Factory = Callable[[...], object]


NOT_FOUND = object()


class CacheWrapper:
    pass


class cached(CacheWrapper):
    """
    Помечает фабрику отметкой о кешировании результата.
    Используется только с Namespace.
    """

    cache: dict[Factory, object]

    def __init__(self, factory: Factory):
        self.factory = factory

    def __call__(self, *args, **kwargs):
        result = self.cache.get(self.factory, NOT_FOUND)
        if result is NOT_FOUND:
            result = self.cache[self.factory] = self.factory(*args, **kwargs)
        return result


class no_cache(CacheWrapper):
    """
    Помечает фабрику отметкой о запрете кеширования результата.
    Используется только с Namespace.
    """

    def __init__(self, factory: Factory):
        self.factory = factory

    def __call__(self, *args, **kwargs):
        return self.factory(*args, **kwargs)
