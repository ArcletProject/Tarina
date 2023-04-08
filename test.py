def test_generic_isinstance():
    from typing import Union, List, TypeVar, Any, Literal, Dict
    from typing_extensions import Annotated
    from tarina import generic_isinstance

    S = TypeVar("S", bound=str)
    assert generic_isinstance("a", Any)
    assert generic_isinstance(1, int)
    assert generic_isinstance(1, Union[str, int])
    assert generic_isinstance(123, Literal[123])
    assert generic_isinstance([1], List[int])
    assert generic_isinstance(1, Annotated[int, lambda x: x > 0])
    assert generic_isinstance("a", S)
    assert generic_isinstance(1, (int, str))
    assert generic_isinstance('a', (int, str))
    assert not generic_isinstance(bool, (str, list))
    assert not generic_isinstance({123}, Dict[str, str])


def test_lru():
    """测试 LRU缓存"""
    from tarina import LRU
    cache: LRU[str, str] = LRU(3)
    cache["a"] = "a"
    cache["b"] = "b"
    cache["c"] = "c"
    assert cache.peek_first_item()[1] == "c"
    _ = cache.get("a", Ellipsis)
    print(f"\n{cache.items()}")
    assert cache.peek_first_item()[1] == "a"
    cache["d"] = "d"
    assert cache.get("b", Ellipsis) == Ellipsis
