from dataclasses import dataclass

from classic.composites import CachingNamespace, cached, no_cache


@dataclass
class SomeObj:
    prop: int


@dataclass
class OtherSomeObj:
    dep: SomeObj


caching_ns = CachingNamespace()
caching_ns.some_obj = lambda: SomeObj(1)
caching_ns.some_other_obj = lambda: OtherSomeObj(caching_ns.some_obj())
caching_ns.some_other_obj_not_cached = no_cache(
    lambda: OtherSomeObj(caching_ns.some_obj())
)

not_caching_ns = CachingNamespace(cache_by_default=False)
not_caching_ns.some_obj = lambda: SomeObj(1)
not_caching_ns.some_other_obj = lambda: OtherSomeObj(caching_ns.some_obj())
not_caching_ns.some_other_obj_cached = cached(
    lambda: OtherSomeObj(caching_ns.some_obj()),
)


def test_caching_namespace():
    some_obj = caching_ns.some_obj()
    assert some_obj == SomeObj(1)
    assert caching_ns.some_obj() is some_obj
    assert (
        caching_ns.some_other_obj_not_cached()
        is not caching_ns.some_other_obj_not_cached()
    )


def test_not_caching_namespace():
    some_obj = not_caching_ns.some_obj()
    assert some_obj == SomeObj(1)
    assert not_caching_ns.some_obj() is not some_obj
    assert (
        not_caching_ns.some_other_obj_cached()
        is not_caching_ns.some_other_obj_cached()
    )
