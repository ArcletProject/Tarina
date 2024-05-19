import json
from pathlib import Path
from typing import cast, TypedDict


class _TemplateDict(TypedDict):
    scope: str
    types: list[str]


def get_template(root: Path):
    if not (root / ".template.json").exists():
        raise FileNotFoundError(f"Lang Template file not found in {root}")
    with (root / ".template.json").open("r", encoding="utf-8") as f:
        return cast(dict, json.load(f))


def schema_scope(scope: str, types: list[str]):
    return {
        "title": scope.capitalize(),
        "description": f"Scope '{scope}' of lang item",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            i: {
                "title": i,
                "description": f"value of lang item type '{i}'",
                "type": "string"
            } for i in types
        },
    }



def generate_lang_schema(root: Path):
    template = get_template(root)
    if "scopes" not in template:
        raise KeyError("Template file must have a 'scopes' key")
    scopes: list[_TemplateDict] = template["scopes"]
    return {
        "title": "Lang Schema",
        "description": f"Schema for lang file",
        "type": "object",
        "minProperties": 1 + len(scopes),
        "maxProperties": 1 + len(scopes),
        "properties": {
            s["scope"]: schema_scope(s["scope"], s["types"]) for s in scopes
        }
    }


def write_lang_schema(root: Path):
    schema = generate_lang_schema(root)
    with (root / f".lang.schema.json").open("w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
