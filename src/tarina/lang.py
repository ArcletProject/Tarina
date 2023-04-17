from __future__ import annotations
from typing import Final, final, Any
from typing_extensions import Self
from pathlib import Path
import json

root_dir: Final[Path] = Path(__file__).parent / "i18n"


def _get_config(root: Path) -> dict[str, Any]:
    if not (root / ".config.json").exists():
        raise FileNotFoundError("Config file not found")
    with (root / ".config.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def _get_types(root: Path) -> list[str]:
    return [i.stem for i in root.iterdir() if i.is_file() and not i.name.startswith(".")]


def _get_lang(root: Path, _type: str) -> dict[str, dict[str, str]]:
    with (root / f"{_type}.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def merge(source: dict, target: dict, ignore: list[str] | None = None) -> dict:
    ignore = ignore or []
    for key, value in source.items():
        if isinstance(value, dict):
            target[key] = merge(value, target.get(key, {}))
        elif isinstance(value, list):
            target[key] = value + target.get(key, [])
        elif key in ignore:
            continue
        else:
            target[key] = value
    return target


@final
class _LangConfig:

    def __init__(self):
        __config = _get_config(root_dir)
        self.__scope: str = __config["default"]
        self.__immutable: list[str] = __config["immutable"]
        self.__types = _get_types(root_dir)
        self.__langs = {t: _get_lang(root_dir, t) for t in self.__types}

    @property
    def types(self):
        return self.__types

    def scope(self, item: str) -> Self:
        if item not in self.__langs:
            raise ValueError(
                self.__langs[self.__scope]["lang"]["scope_error"].format(target=item)
            )
        self.__scope = item
        return self

    def save(self):
        config = _get_config(root_dir)
        config["default"] = self.__scope
        with (root_dir / ".config.json").open("w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def __getattr__(self, item: str):
        _lang = self.__langs[self.__scope]
        if item not in _lang:
            raise ValueError(
                _lang["lang"]["type_error"].format(target=item)
            )

        class _getter:
            def __init__(self, prefix: str):
                self.prefix = prefix

        def __getattr__(_self, _item: str):
            _config = _lang[_self.prefix]
            if not _config.get(_item):
                raise AttributeError(_lang["lang"]["name_error"].format(target=_item))
            return _config[_item]

        return type(f"{self.__scope}_{item}_getter", (_getter,), {"__getattr__": __getattr__})(item)

    def load(self, root: Path):
        config = _get_config(root)
        self.__scope = config["default"]
        self.__immutable.extend(config.get("immutable", []))
        _types = _get_types(root)
        for t in _types:
            if t in self.__types:
                self.__langs[t] = merge(_get_lang(root, t), self.__langs[t], self.__immutable)
            else:
                self.__types.append(t)
                self.__langs[t] = _get_lang(root, t)

    def require(self, _type: str, _name: str, scope: str | None = None) -> str:
        scope = scope or self.__scope
        if scope not in self.__langs:
            raise ValueError(self.__langs[self.__scope]["lang"]["scope_error"].format(target=scope))
        if _type not in self.__langs[scope]:
            raise ValueError(self.__langs[scope]["lang"]["type_error"].format(target=_type))
        if not self.__langs[scope][_type].get(_name):
            raise ValueError(self.__langs[scope]["lang"]["name_error"].format(target=_name))
        return self.__langs[scope][_type][_name]

    def set(self, _type: str, _name: str, content: str, scope: str | None = None):
        scope = scope or self.__scope
        if scope not in self.__langs:
            raise ValueError(self.__langs[self.__scope]["lang"]["scope_error"].format(target=scope))
        if _type in self.__immutable:
            raise ValueError(self.__langs[scope]["lang"]["type_error"].format(target=_type))
        self.__langs[scope].setdefault(_type, {})[_name] = content

    def __repr__(self):
        return f"<LangConfig: {self.__scope}>"


lang: _LangConfig = _LangConfig()

__all__ = ["lang"]

if __name__ == '__main__':
    print(lang.types)
    print(lang.lang.name_error)
    print(lang.require("lang", "name_error"))
    print(lang.require("lang", "name_error", "en-US"))
    print(lang.scope("en-US"))
    print(lang.lang.name_error)
    print(lang.lang.type_error)
    print(lang.lang.scope_error)
