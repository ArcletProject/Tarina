from __future__ import annotations
from typing import Final, final, Any
from typing_extensions import Self
from pathlib import Path
import json

root_dir: Final[Path] = Path(__file__).parent / "i18n"


def _get_config(root: Path) -> dict[str, Any]:
    if not (root / ".config.json").exists():
        return {}
    with (root / ".config.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def _get_scopes(root: Path) -> list[str]:
    return [
        i.stem for i in root.iterdir() if i.is_file() and not i.name.startswith(".")
    ]


def _get_lang(root: Path, _type: str) -> dict[str, dict[str, str]]:
    with (root / f"{_type}.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def merge(source: dict, target: dict, ignore: list[str] | None = None) -> dict:
    ignore = ignore or []
    for key, value in source.items():
        if key in target and key in ignore:
            continue
        if isinstance(value, dict):
            target[key] = merge(value, target.get(key, {}))
        elif isinstance(value, list):
            target[key] = value + target.get(key, [])
        else:
            target[key] = value
    return target


@final
class _LangConfig:
    def __init__(self):
        __config = _get_config(root_dir)
        self.__scope: str = __config["default"]
        self.__frozen: list[str] = __config["frozen"]
        self.__require: list[str] = __config["require"]
        self.__scopes = _get_scopes(root_dir)
        self.__langs = {t: _get_lang(root_dir, t) for t in self.__scopes}

    @property
    def scopes(self):
        return self.__scopes

    def scope(self, item: str) -> Self:
        if item not in self.__langs:
            raise ValueError(self.require("lang", "scope_error").format(target=item))
        self.__scope = item
        return self

    def save(self, root: Path | None = None):
        _root = root or root_dir
        config = _get_config(_root)
        config["default"] = self.__scope
        with (_root / ".config.json").open("w+", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def __getattr__(self, item: str):
        _lang = self.__langs[self.__scope]
        if item not in _lang:
            raise ValueError(
                _lang["lang"]["type_error"].format(target=item, scope=self.__scope)
            )

        class _getter:
            def __init__(_self, prefix: str):
                _self.prefix = prefix

        def __getattr__(_self, _item: str):
            _config = _lang[_self.prefix]
            if not _config.get(_item):
                raise AttributeError(
                    _lang["lang"]["name_error"].format(
                        target=_item, scope=self.__scope, type=_self.prefix
                    )
                )
            return _config[_item]

        return type(
            f"{self.__scope}_{item}_getter", (_getter,), {"__getattr__": __getattr__}
        )(item)

    def load_file(self, filepath: Path):
        _type = filepath.stem
        if _type in self.__scopes:
            self.__langs[_type] = merge(
                _get_lang(filepath.parent, _type), self.__langs[_type], self.__frozen
            )
        else:
            self.__scopes.append(_type)
            self.__langs[_type] = _get_lang(filepath.parent, _type)
        for key in self.__require:
            t, n = key.split(".", 1)
            if t not in self.__langs[_type]:
                raise KeyError(
                    self.require("lang", "miss_require_type", _type).format(
                        scope=_type, target=t
                    )
                )
            if n and n not in self.__langs[_type][t]:
                raise KeyError(
                    self.require("lang", "miss_require_name", _type).format(
                        scope=_type, type=t, target=n
                    )
                )

    def load(self, root: Path):
        config = _get_config(root)
        self.__scope = config.get("default", self.__scope)
        self.__frozen.extend(config.get("frozen", []))
        self.__require.extend(config.get("require", []))
        for i in root.iterdir():
            if i.is_file() and not i.name.startswith("."):
                continue
            self.load_file(i)

    def require(self, _type: str, _name: str, scope: str | None = None) -> str:
        scope = scope or self.__scope
        if scope not in self.__langs:
            raise ValueError(
                self.__langs[self.__scope]["lang"]["scope_error"].format(target=scope)
            )
        if _type in self.__langs[scope]:
            _types = self.__langs[scope][_type]
        elif _type in self.__langs[self.__scope]:
            _types = self.__langs[self.__scope][_type]
        else:
            raise ValueError(
                self.__langs[scope]["lang"]["type_error"].format(
                    target=_type, scope=scope
                )
            )
        if _name in _types:
            return _types[_name]
        elif _name in self.__langs[self.__scope][_type]:
            return self.__langs[self.__scope][_type][_name]
        else:
            raise ValueError(
                self.__langs[scope]["lang"]["name_error"].format(
                    target=_name, scope=scope, type=_type
                )
            )

    def set(self, _type: str, _name: str, content: str, scope: str | None = None):
        scope = scope or self.__scope
        if scope not in self.__langs:
            raise ValueError(
                self.__langs[self.__scope]["lang"]["scope_error"].format(target=scope)
            )
        if _type in self.__frozen:
            raise ValueError(
                self.__langs[scope]["lang"]["type_error"].format(
                    target=_type, scope=scope
                )
            )
        self.__langs[scope].setdefault(_type, {})[_name] = content

    def __repr__(self):
        return f"<LangConfig: {self.__scope}>"


lang: _LangConfig = _LangConfig()

__all__ = ["lang"]

if __name__ == "__main__":
    print(lang.scopes)
    print(lang.lang.name_error)
    print(lang.require("lang", "name_error"))
    print(lang.require("lang", "name_error", "en-US"))
    print(lang.scope("en-US"))
    print(lang.lang.name_error)
    print(lang.lang.type_error)
    print(lang.lang.scope_error)
