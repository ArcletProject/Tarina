[`tarina.lang`](./src/tarina/lang) 提供了一个 tarina-lang 命令行工具

首先可以通过 `tarina-lang new` 创建文件夹 `i18n`

之后使用 `cd ./i18n` 和 `tarina-lang init`，会生成如下文件：
```diff
📦 project
├──📂 i18n
++     ├── __init__.py
++     ├── .config.json
++     ├── .template.json
++     └── .template.schema.json
├── xxx.py
└── ...
```

你需要将你语言文件中所有包含的项目声明在 `.template.json` 中，例如：

```json
{
  "$schema": ".template.schema.json",
  "scopes" : [
    {
      "scope": "example",
      "types": [
        "test",
        {
          "subtype": "test1",
          "types": [
            "test2"
          ]
        }
      ]
    }
  ]
}
```

然后通过 `tarina-lang schema` 和 `tarina-lang create XXX` 来创建新的语言文件。以下为使用命令创建 `en-US` 和 `zh-CN` 语言文件后的文件结构：
```diff
📦 project
├──📂 i18n
│      ├── __init__.py
│      ├── .config.json
│      ├── .template.json
│      ├── .template.schema.json
++     ├── en-US.json
++     └── zh-CN.json
├── xxx.py
└── ...
```

其中一个语言文件如下所示：

```json5
// en-US.json
{
  "$schema": "./.lang.schema.json",
  "example": {
    "test": "Test",
    "test1": {
      "test2": "Test2"
    }
  }
}
```

> [!NOTE]
> `tarina-lang` 支持创建和读取 YAML 格式的语言文件。当然首先你需要额外安装 `tarina[yaml]`
> 
> 然后通过 `tarina-lang create XXX --yaml` 创建 `.yml` 文件
>
> 一个 yaml 格式的语言文件如下所示：
> ```yaml
> # $schema: .lang.schema.json
> example:
>   test: Test
>   test1:
>     test2: Test2
> ```

之后，在 `xxx` 里面，你可以用如下方法来使用i18n条目：

```python
from .i18n import lang

...
text1 = lang.require("example", "test")  # Test
# 如果你的条目是模板字符串，你应该直接 text = text.format(...)
text2 = lang.require("example", "test1.test2")  # Test2
```

高级一点，你可以通过 `tarina-lang model` 来生成一个模型文件：

```diff
📦 project
├──📂 i18n
│      ├── __init__.py
│      ├── .config.json
│      ├── .template.json
│      ├── .template.schema.json
│      ├── en-US.json
++     ├── model.py
│      └── zh-CN.json
├── xxx.py
└── ...
```

其中 `model.py`:

```python
from tarina.lang.model import LangItem, LangModel


class ExampleTest1:
    test2: LangItem = LangItem("example", "test1.test2")


class Example:
    test: LangItem = LangItem("example", "test")
    test1: ExampleTest1


class Lang(LangModel):
    example = Example

```

之后便可以这样使用：

```python
from .i18n import Lang

...
text1 = Lang.example.test()  # Test
# 如果你的条目是模板字符串，你可以使用 text = Lang.example.test(...)
text2 = Lang.example.test1.test2()  # Test2
```