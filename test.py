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


def test_split_once():
    """测试单次分割函数, 能以引号扩起空格, 并允许保留引号"""
    from tarina import split_once
    assert split_once("arclet-alconna", (' ',)) == ('arclet-alconna', '')
    text1 = "rrr b bbbb"
    text2 = "\'rrr b\' bbbb"
    text3 = "\\\'rrr b\\\' bbbb"
    text4 = "\\\'rrr \\b\\\' bbbb"
    assert split_once(text1, (' ',)) == ('rrr', 'b bbbb')
    assert split_once(text2, (' ',)) == ("rrr b", 'bbbb')
    assert split_once(text3, (' ',)) == ("'rrr b'", 'bbbb')
    assert split_once(text4, (' ',)) == ("'rrr \\b'", 'bbbb')  # 不消除其他转义字符斜杠

    assert split_once("'rrr b\" b' bbbb", (' ',)) == ("rrr b\" b", 'bbbb')
    assert split_once("rrr  bbbb", (' ',)) == ("rrr", 'bbbb')


def test_split():
    """测试分割函数, 能以引号扩起空格, 并允许保留引号"""
    from tarina import split

    text1 = "rrr b bbbb"
    text2 = "\'rrr b\' bbbb"
    text3 = "\\\'rrr b\\\' bbbb"
    assert split(text1, (' ',)) == ["rrr", "b", "bbbb"]
    assert split(text2, (' ',)) == ["rrr b", "bbbb"]
    assert split(text3, (' ',)) == ["'rrr b'", "bbbb"]
    assert split("", (' ',)) == []
    assert split("  ", (' ',)) == []
