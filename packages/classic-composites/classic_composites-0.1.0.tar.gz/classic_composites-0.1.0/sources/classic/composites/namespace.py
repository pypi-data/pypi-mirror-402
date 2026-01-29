from .wrappers import CacheWrapper, Factory, cached, no_cache


class CachingNamespace:
    """
    Пространство имен, умеющее кешировать результаты фабрик,
    указанных в атрибутах, при вызове.
    Сахар для описания композитов в ленивом стиле.
    """
    __cache_by_default__: bool
    __objects__: dict[str, CacheWrapper]
    __cache__: dict[Factory, object]

    def __init__(self, cache_by_default: bool = True) -> None:
        object.__setattr__(self, '__cache_by_default', cache_by_default)
        object.__setattr__(self, '__objects__', {})
        object.__setattr__(self, '__cache__', {})

    def __setattr__(self, key: str, value: object) -> None:
        if callable(value):
            if (not isinstance(value, no_cache) and
                object.__getattribute__(self, '__cache_by_default')):
                value = cached(value)

            if isinstance(value, cached):
                value.cache = object.__getattribute__(self, '__cache__')

        object.__getattribute__(self, '__objects__')[key] = value

    def __getattr__(self, key: str) -> object:
        return self.__objects__[key]
