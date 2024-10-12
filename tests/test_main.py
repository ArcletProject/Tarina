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
    assert generic_isinstance([1], list[int])
    assert generic_isinstance(1, Annotated[int, lambda x: x > 0])
    assert generic_isinstance("a", S)
    assert generic_isinstance(1, (int, str))
    assert generic_isinstance("a", (int, str))
    assert generic_isinstance((1, "a"), tuple[int, str])
    assert generic_isinstance((1, 2, 3), tuple[int, ...])
    assert not generic_isinstance(bool, (str, list))
    assert not generic_isinstance({123}, Dict[str, str])
    assert not generic_isinstance([1], List[str])
    assert not generic_isinstance({"a": 1}, dict[str, str])
    assert not generic_isinstance((1, 2), tuple[int, str])
    assert not generic_isinstance((1, "a"), tuple[int, str, str])


def test_generic_issubclass():
    from typing import Any, Dict, List, Literal, TypeVar, Union

    from typing_extensions import Annotated

    from tarina import generic_issubclass

    S = TypeVar("S", bound=str)
    assert generic_issubclass(str, Any)
    assert generic_issubclass(int, Union[str, int])
    assert generic_issubclass(List[int], List[int])
    assert generic_issubclass(int, Annotated[int, lambda x: x > 0])
    assert generic_issubclass(str, S)


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

    assert split_once("arclet-alconna", " ") == ("arclet-alconna", "")
    text1 = "rrr b bbbb"
    text2 = "'rrr b' bbbb"
    text3 = "\\'rrr b\\' bbbb"
    text4 = "\\'rrr \\b\\' bbbb"
    assert split_once(text1, " ") == ("rrr", "b bbbb")
    assert split_once(text2, " ") == ("rrr b", "bbbb")
    assert split_once(text3, " ") == ("'rrr b'", "bbbb")
    assert split_once(text4, " ") == ("'rrr \\b'", "bbbb")  # 不消除其他转义字符斜杠

    assert split_once("'rrr b\" b' bbbb", " ") == ('rrr b" b', "bbbb")
    assert split_once("rrr  bbbb", " ") == ("rrr", "bbbb")
    assert split_once("rrr 'bbb'", " ") == ("rrr", "'bbb'")

    assert split_once(
        r'\",\\"\\",\\"\\",\\"\\",\\"\\",\\"\\",\\"\\",\\"\\",\\"\\",\\"\\",\\"\\",\\"\\",\\"\\",\\"\\",\\"\\",\\"\\",\\"\\",\\",\\"',
        " ",
    ) == (
        r'\",\\"\\",\\"\\",\\"\\",\\"\\",\\"\\",\\"\\",\\"\\",\\"\\",\\"\\",\\"\\",\\"\\",\\"\\",\\"\\",\\"\\",\\"\\",\\"\\",\\",\\"',
        "",
    )

    assert (split_once("123456789", " ", True)) == ("123456789", "")
    assert (split_once("123 456 789", " ", True)) == ("123", "456 789")
    assert (split_once('"123 456" 789', " ", True)) == ("123 456", "789")
    assert (split_once('12"3 456" 789', " ", True)) == ('12"3', '456" 789')
    assert (split_once('12"3 456 789', " ", True)) == ('12"3', "456 789")
    assert (split_once('"123 456 789', " ", True)) == ('"123', "456 789")
    assert (split_once('123" 456 789', " ", True)) == ('123"', "456 789")
    assert (split_once('"""123 456"" 789', " ", True)) == ('"""123 456""', "789")
    assert (split_once('"123 "456 789', " ", True)) == ('"123', '"456 789')


def test_split():
    """测试分割函数, 能以引号扩起空格, 并允许保留引号"""
    from tarina import split

    text1 = "rrr b bbbb"
    text2 = "'rrr b' bbbb"
    text3 = "\\'rrr b\\' bbbb"
    assert split(text1, " ") == ["rrr", "b", "bbbb"]
    assert split(text2, " ") == ["rrr b", "bbbb"]
    assert split(text3, " ") == ["'rrr b'", "bbbb"]
    assert split("", " ") == []
    assert split("  ", " ") == []

    assert (split("123 456 789", " ", True)) == ["123", "456", "789"]
    assert (split('123 "456 789" abc', " ", True)) == ["123", "456 789", "abc"]
    assert (split('123 45"6 789 abc', " ", True)) == ["123", '45"6', "789", "abc"]
    assert (split('123 456" 789 abc', " ", True)) == ["123", '456"', "789", "abc"]
    assert (split('123 456 "789 abc def', " ", True)) == ["123", "456", '"789', "abc", "def"]
    assert (split('123 "456 "789', " ", True)) == ["123", '"456', '"789']
    assert (split('123 """456 7" 789', " ", True)) == ["123", "456 7", "789"]
    assert (split('123 """456 "789', " ", True)) == ["123", '"456', '"789']


def test_lang():
    """测试 i18n"""
    from pathlib import Path

    from tarina import lang

    assert lang.locales == {"zh-CN", "en-US"}
    lang.select("zh-CN")
    assert lang.current == "zh-CN"
    assert lang.require("lang", "error.type") == "'{target}' 在 '{locale}:{scope}' 不是合法的类型"
    assert lang.require("lang", "error.type", "en-US") == "'{target}' is not a valid type in '{locale}:{scope}'"
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
    lang.load_data("test", {"lang": {"error": {"type": "test"}}})
    lang.select("test")
    assert lang.require("lang", "error.type") == "test"
    assert lang.require("lang", "error.locale") == "'{target}' 不是合法的语种"
    lang.load_file(Path(__file__).parent / "en-UK.yml")
    assert lang.locales == {"zh-CN", "test", "en-US", "en-UK"}


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
    from datetime import datetime, timedelta

    from tarina import DateParser

    assert DateParser.parse("2021-01-01") == datetime(2021, 1, 1)
    assert DateParser.parse("2021-01-01 12:34:56") == datetime(2021, 1, 1, 12, 34, 56)
    assert DateParser.parse("1m").replace(microsecond=0) == datetime.now().replace(microsecond=0) + timedelta(minutes=1)
    assert DateParser.parse("h3").replace(microsecond=0) == datetime.now().replace(microsecond=0) + timedelta(hours=3)


def test_safe_eval():
    from tarina import safe_eval

    ctx = {"a": {"b": ["c"]}}

    assert safe_eval("a['b'][0]", ctx) == "c"

    class A:
        class B:
            c = 123

    assert safe_eval("A.B.c", {"A": A}) == 123
