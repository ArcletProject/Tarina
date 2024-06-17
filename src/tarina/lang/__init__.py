from __future__ import annotations

import contextlib
import json
import locale
import os
import sys
from pathlib import Path
from typing import Dict, Final, TypedDict, Union, cast, final

from typing_extensions import Self

root_dir: Final[Path] = Path(__file__).parent.parent / "i18n"
WINDOWS = sys.platform.startswith("win") or (sys.platform == "cli" and os.name == "nt")


class _LangDict(TypedDict):
    default: str
    frozen: list[str]
    require: list[str]


def _get_win_locale_with_ctypes() -> str | None:
    import ctypes

    kernel32 = ctypes.windll.kernel32
    lcid: int = kernel32.GetUserDefaultUILanguage()
    return locale.windows_locale.get(lcid)


def _get_win_locale_from_registry() -> str | None:
    import winreg  # noqa

    with contextlib.suppress(Exception):
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\International") as key:
            if lcid := winreg.QueryValueEx(key, "Locale")[0]:
                return locale.windows_locale.get(int(lcid, 16))


if WINDOWS:
    try:
        import ctypes

        _get_win_locale = _get_win_locale_with_ctypes
    except ImportError:
        _get_win_locale = _get_win_locale_from_registry


def get_locale() -> str | None:
    if WINDOWS:
        return _get_win_locale()

    return locale.getlocale(locale.LC_MESSAGES)[0]  # type: ignore


def _get_config(root: Path) -> _LangDict:
    if not (root / ".config.json").exists():
        raise FileNotFoundError(f"Config file not found in {root}")
    with (root / ".config.json").open("r", encoding="utf-8") as f:
        return cast(_LangDict, json.load(f))



Types = Union[str, Dict[str, "Types"]]
Raw = Dict[str, Dict[str, Types]]


def convert_dictionary(data, prefix: str = ""):
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result.update(convert_dictionary(value, f"{prefix}{key}."))
        else:
            result[f"{prefix}{key}"] = value
    return result


def flatten(data: Raw) -> dict[str, dict[str, str]]:
    result = {}
    for scope, types in data.items():
        result[scope] = {}
        for type, value in types.items():
            if isinstance(value, dict):
                result[scope].update(convert_dictionary({type: value}))
            else:
                result[scope][type] = value
    return result


def merge(source: dict, target: dict) -> dict:
    for key, value in source.items():
        if isinstance(value, dict):
            target[key] = merge(value, target.get(key, {}))
        elif isinstance(value, list):
            target[key] = value + target.get(key, [])
        else:
            target[key] = value
    return target


def _expand(data: list[str]):
    result: dict[str, list[str]] = {}
    for i in data:
        if "." not in i:
            i += ".*"
        parts = i.split(".", 1)
        s = parts[0]
        if s not in result:
            result[s] = []
            if not parts[1].startswith("*"):
                result[s].append(parts[1])
        elif result[s] and not parts[1].startswith("*"):
            result[s].append(parts[1])
    return result


def _get_lang(file: Path) -> Raw:
    if not file.exists():
        raise FileNotFoundError(f"Lang file '{file}' not found")
    if file.suffix.startswith(".json"):
        with file.open("r", encoding="utf-8") as f:
            data: Raw = json.load(f)
        data.pop("$schema", None)
        return data
    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML is required to load yaml file")
    with file.open("r", encoding="utf-8") as f:
        data: Raw = yaml.safe_load(f)
    data.pop("$schema", None)
    return data



def _get_scopes(root: Path) -> dict[str, dict[str, dict[str, str]]]:
    result = {}
    for i in root.iterdir():
        if not i.is_file() or i.name.startswith(".") or i.suffix not in (".json", ".yaml", ".yml"):
            continue
        result[i.stem] = flatten(_get_lang(i))
    return result


@final
class _LangConfig:
    def __init__(self):
        __config = _get_config(root_dir)
        self.__locale: str = __config["default"]
        self.__frozen: dict[str, list[str]] = _expand(__config["frozen"])
        self.__require: dict[str, list[str]] = _expand(__config["require"])
        self.__langs: dict[str, dict[str, dict[str, str]]] = _get_scopes(root_dir)
        self.__locales = set(self.__langs.keys())
        self.select_local()

    @property
    def locales(self):
        return set(sorted(self.__locales))

    @property
    def current(self):
        return self.__locale

    def select_local(self):
        """
        依据系统语言尝试自动选择语言
        """
        if (lc := get_locale()) and lc.replace("_", "-") in self.__langs:
            self.__locale = lc.replace("_", "-")
        return self

    def select(self, locale: str) -> Self:
        locale = locale.replace("_", "-")
        if locale not in self.__langs:
            raise ValueError(self.require("lang", "error.locale").format(target=locale))
        self.__locale = locale
        return self

    def save(self, root: Path | None = None):
        _root = root or root_dir
        config = _get_config(_root)
        config["default"] = self.__locale
        with (_root / ".config.json").open("w+", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def load_data(self, locale: str, data: Raw):
        if locale in self.__langs:
            source = flatten(data)
            target = self.__langs[locale]
            for scope, ignores in self.__frozen.items():
                if scope not in target or scope not in source:
                    continue
                if not ignores:
                    source.pop(scope)
                else:
                    for i in ignores:
                        source[scope] = {k: v for k, v in source[scope].items() if not (k.startswith(i) and k in target[scope])}
            self.__langs[locale] = merge(source, target)
        else:
            self.__locales.add(locale)
            self.__langs[locale] = flatten(data)
        for scope, requries in self.__require.items():
            if scope not in self.__langs[locale]:
                raise KeyError(self.require("lang", "miss_require_scope", locale).format(locale=locale, target=scope))
            for t in requries:
                if any(k.startswith(t) for k in self.__langs[locale][scope]):
                    continue
                raise KeyError(self.require("lang", "miss_require_type", locale).format(locale=locale, scope=scope, target=t))

    def load_file(self, filepath: Path):
        return self.load_data(filepath.stem, _get_lang(filepath))

    def load_config(self, config: _LangDict):
        self.__locale = config.get("default", self.__locale)
        self.__frozen = merge(_expand(config.get("frozen", [])), self.__frozen)
        self.__require = merge(_expand(config.get("require", [])), self.__require)
        self.select_local()

    def load(self, root: Path) -> Self:
        self.load_config(_get_config(root))
        for i in root.iterdir():
            if not i.is_file() or i.name.startswith(".") or i.suffix not in (".json", ".yaml", ".yml"):
                continue
            self.load_file(i)
        return self

    def require(self, scope: str, type: str, locale: str | None = None) -> str:
        locale = locale or self.__locale
        if locale not in self.__langs:
            raise ValueError(self.__langs[self.__locale]["lang"]["error.locale"].format(target=locale))
        if scope in self.__langs[locale]:
            _types = self.__langs[locale][scope]
        elif scope in self.__langs[self.__locale]:
            _types = self.__langs[self.__locale][scope]
        elif scope in self.__langs[(default := _get_config(root_dir)["default"])]:
            _types = self.__langs[default][scope]
        else:
            raise ValueError(self.__langs[locale]["lang"]["error.scope"].format(target=scope, locale=locale))
        if type in _types:
            return _types[type]
        elif type in self.__langs[self.__locale][scope]:
            return self.__langs[self.__locale][scope][type]
        elif type in self.__langs[(default := _get_config(root_dir)["default"])][scope]:
            return self.__langs[default][scope][type]
        else:
            raise ValueError(self.__langs[locale]["lang"]["error.type"].format(target=type, locale=locale, scope=scope))

    def set(self, scope: str, type: str, content: str, locale: str | None = None):
        locale = locale or self.__locale
        if locale not in self.__langs:
            raise ValueError(self.__langs[self.__locale]["lang"]["error.locale"].format(target=locale))
        if scope in self.__frozen:
            raise ValueError(self.__langs[locale]["lang"]["error.scope"].format(target=scope, locale=locale))
        self.__langs[locale].setdefault(scope, {})[type] = content

    def __repr__(self):
        return f"<LangConfig: {self.__locale}>"


lang: _LangConfig = _LangConfig()

__all__ = ["lang"]
