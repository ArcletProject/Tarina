from argparse import ArgumentParser
from tarina.lang.schema import write_lang_schema
from pathlib import Path

CONFIG_TEMPLATE = """
{
  "default": "zh-CN",
  "frozen": [],
  "require": []
}
"""

TEMPLATE_SCHEMA = """
{
  "title": "Template",
  "description": "Template for lang items to generate schema for lang files",
  "type": "object",
  "properties": {
    "scopes": {
      "title": "Scopes",
      "description": "All scopes of lang items",
      "type": "array",
      "uniqueItems": true,
      "items": {
        "title": "Scope",
        "description": "First level of all lang items",
        "type": "object",
        "properties": {
          "scope": {
            "type": "string",
            "description": "Scope name"
        },
          "types": {
            "type": "array",
            "description": "All types of lang items",
            "uniqueItems": true,
            "items": {
              "type": "string",
              "description": "Value of lang item"
            }
        }
        }
      }
    }
  }
}
"""

TEMPLATE_TEMPLATE = """
{
  "$schema": "./.template.schema.json",
  "scopes": []
}
"""

LANG_TEMPLATE = """
{
  "$schema": "./.lang.schema.json"
}
"""


def init(*_):
    root = Path.cwd()
    config_file = root / ".config.json"
    template_file = root / ".template.json"
    template_schema = root / ".template.schema.json"

    with config_file.open("w+") as f:
        f.write(CONFIG_TEMPLATE)

    with template_file.open("w+") as f:
        f.write(TEMPLATE_TEMPLATE)

    with template_schema.open("w+") as f:
        f.write(TEMPLATE_SCHEMA)

    print(
        f"""\
files created:
- {config_file}
- {template_file}

please edit the files to fit your needs
    """
    )

def schema(*_):
    root = Path.cwd()
    schema_file = root / ".lang.schema.json"
    created = not schema_file.exists()
    try:
        write_lang_schema(Path.cwd())
    except Exception as e:
        print(repr(e))
    else:
        print(f"schema for lang file {'created' if created else 'updated'}. Now you can create or update your lang files.")


def create(args):
    root = Path.cwd()
    lang_file = root / f"{args.name}.json"

    with lang_file.open("w+") as f:
        f.write(LANG_TEMPLATE)

    print(f"lang file created: {lang_file}")


def delete(args):
    root = Path.cwd()
    lang_file = root / f"{args.name}.json"

    if lang_file.exists():
        lang_file.unlink()
        print(f"lang file deleted: {lang_file}")
    else:
        print(f"lang file not found: {lang_file}")



def main():
    parser = ArgumentParser(description="tarina.lang CLI tool")

    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init", help="initialize a new lang configs")
    init_parser.set_defaults(func=init)

    schema_parser = subparsers.add_parser("schema", help="generate or update lang schema")
    schema_parser.set_defaults(func=schema)

    create_parser = subparsers.add_parser("create", help="create a new lang file")
    create_parser.add_argument("name", type=str, help="name of the lang file")
    create_parser.set_defaults(func=create)

    delete_parser = subparsers.add_parser("delete", help="delete a lang file")
    delete_parser.add_argument("name", type=str, help="name of the lang file")
    delete_parser.set_defaults(func=delete)

    args = parser.parse_args()

    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
