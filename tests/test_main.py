def test_generic_isinstance():
    from typing import Any, Dict, List, Literal, TypeVar, Union

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
    assert generic_isinstance("a", (int, str))
    assert not generic_isinstance(bool, (str, list))
    assert not generic_isinstance({123}, Dict[str, str])


def test_lru():
    """测试 LRU缓存"""
    from tarina import LRU

    cache: LRU[str, str] = LRU(3)
    cache["a"] = "a"
    cache["b"] = "b"
    cache["c"] = "c"
    assert cache.peek_first_item()[1] == "c"  # type: ignore
    _ = cache.get("a", Ellipsis)
    print(f"\n{cache.items()}")
    assert cache.peek_first_item()[1] == "a"  # type: ignore
    cache["d"] = "d"
    assert cache.get("b", Ellipsis) == Ellipsis


def test_split_once():
    """测试单次分割函数, 能以引号扩起空格, 并允许保留引号"""
    from tarina import split_once

    assert split_once("arclet-alconna", (" ",)) == ("arclet-alconna", "")
    text1 = "rrr b bbbb"
    text2 = "'rrr b' bbbb"
    text3 = "\\'rrr b\\' bbbb"
    text4 = "\\'rrr \\b\\' bbbb"
    assert split_once(text1, (" ",)) == ("rrr", "b bbbb")
    assert split_once(text2, (" ",)) == ("rrr b", "bbbb")
    assert split_once(text3, (" ",)) == ("'rrr b'", "bbbb")
    assert split_once(text4, (" ",)) == ("'rrr \\b'", "bbbb")  # 不消除其他转义字符斜杠

    assert split_once("'rrr b\" b' bbbb", (" ",)) == ('rrr b" b', "bbbb")
    assert split_once("rrr  bbbb", (" ",)) == ("rrr", "bbbb")
    assert split_once("rrr 'bbb'", (" ",)) == ("rrr", "'bbb'")


def test_split():
    """测试分割函数, 能以引号扩起空格, 并允许保留引号"""
    from tarina import split

    text1 = "rrr b bbbb"
    text2 = "'rrr b' bbbb"
    text3 = "\\'rrr b\\' bbbb"
    assert split(text1, (" ",)) == ["rrr", "b", "bbbb"]
    assert split(text2, (" ",)) == ["rrr b", "bbbb"]
    assert split(text3, (" ",)) == ["'rrr b'", "bbbb"]
    assert split("", (" ",)) == []
    assert split("  ", (" ",)) == []

    try:
        split('rrr "bbb', (" ",))
    except SyntaxError as e:
        assert str(e) == "Unterminated string: 'rrr \"bbb'"


def test_lang():
    """测试 i18n"""
    from tarina import lang

    assert lang.locales == {"zh-CN", "en-US"}
    lang.select("zh-CN")
    assert lang.current == "zh-CN"
    assert lang.require("lang", "type_error") == "'{target}' 在 '{locale}:{scope}' 不是合法的类型"
    assert lang.require("lang", "type_error", "en-US") == "'{target}' is not a valid type in '{locale}:{scope}'"
    lang.select("en-US")
    assert lang.current == "en-US"
    try:
        lang.select("ru-RU")
    except ValueError as e:
        assert str(e) == "'ru-RU' is not a valid language locale"
    try:
        lang.load_data("test", {})
    except KeyError as e:
        assert str(e) == "\"lang file 'test' missed require scope 'lang'\""
    lang.load_data("test", {"lang": {"type_error": "test"}})
    lang.select("test")
    assert lang.require("lang", "type_error") == "test"
    assert lang.require("lang", "locale_error") == "'{target}' 不是合法的语种"


def test_init_spec():
    from dataclasses import dataclass

    from tarina import init_spec

    @dataclass
    class User:
        name: str
        age: int

    @init_spec(User)
    def add_user(user: User):
        return user

    assert add_user("test", age=1) == User("test", 1)


def test_date_parser():
    from datetime import datetime

    from tarina import DateParser

    assert DateParser.parse("2021-01-01") == datetime(2021, 1, 1)
    assert DateParser.parse("2021-01-01 12:34:56") == datetime(2021, 1, 1, 12, 34, 56)


def test_safe_eval():
    from tarina import safe_eval

    ctx = {"a": {"b": ["c"]}}

    assert safe_eval("a['b'][0]", ctx) == "c"

    class A:
        class B:
            c = 123

    assert safe_eval("A.B.c", {"A": A}) == 123
