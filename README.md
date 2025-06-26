
# zen-rule

## develop

初始化一个 python 库的包结构,

> uv init --lib .
> uv init --lib zen-rule

uv init 默认把程序放在 src 文件夹下(src文件夹下无 __init__.py 文件, 不是python模块). 

程序开发时，需要对开发的包进行测试. 有两种方法:

1. 将 src 包加入 sys.path 中, 或者使用 PYTHONPATH=src python main.
2. 使用 `uv pip install -e .` 将开发包以编辑模式安装到系统依赖 site-packages 中.

pip install -e 在依赖库中安装了一个指向当前开发代码的链接文件 _zen_rule.pth 

```bash
/home/ryefccd/workspace/zen-rule/src(.venv) ryefccd@republic:~/workspace/zen-rule$ cat .venv/lib/python3.10/site-packages/zen_rule-0.1.0.dist-info/RECORD 
_zen_rule.pth,sha256=_hfX66NqcOptirPAFCr8WKBAxzevMvwcwIzxoCuR0Gc,36
zen_rule-0.1.0.dist-info/INSTALLER,sha256=5hhM4Q4mYTT9z6QB6PGpUAW81PGNFrYrdXMj4oM_6ak,2
zen_rule-0.1.0.dist-info/METADATA,sha256=KaQQLhC57VzmOx1iV40tKN6UPI9eQ6Mh2VM0dGUR_fA,777
zen_rule-0.1.0.dist-info/RECORD,,
zen_rule-0.1.0.dist-info/REQUESTED,sha256=47DEQpj8HBSa-_TImW-5JCeuQeRkm5NMpJWZG3hSuFU,0
zen_rule-0.1.0.dist-info/WHEEL,sha256=qtCwoSJWgHk21S1Kb4ihdzI2rlJ1ZKaIurTj_ngOhyQ,87
zen_rule-0.1.0.dist-info/direct_url.json,sha256=oUFJmKTIsuVYL6vu1pBc1kSxaxyaYoYahIAj2sIEEts,78
zen_rule-0.1.0.dist-info/uv_cache.json,sha256=f86k5FOHVCQBiOmxV_ANc62kP71iNC1Mc8Zz69AMbvM,89

(.venv) ryefccd@republic:~/workspace/zen-rule$ cat .venv/lib/python3.10/site-packages/_zen_rule.pth 
/home/ryefccd/workspace/zen-rule/src
```

## monorepo(multi develop packages dependencies)

[uv workspaces](https://docs.astral.sh/uv/concepts/projects/workspaces/#using-workspaces)



## example

推荐线上使用 decision 缓存模式, 这样规则只需要加载，解析一次后重复使用，提高系统性能.

```python
from pathlib import Path
from zen_rule.custom.udf_manager import udf
from zen_rule import ZenRule


async def test_zenrule():
    """
        推荐线上生产环境使用此模式进行规则执行, 可以缓存决策对象, 提高性能.
    """
    zr = ZenRule({})
    key = "xxxx_rule"
    basedir = Path(__file__).parent
    filename = basedir / "graph" / "custom_v2.json"

    with open(filename, "r", encoding="utf8") as f:
        logger.warning(f"graph json: %s", filename)
        content =  f.read()

    zr.create_decision_with_cache_key(key, content)  # 将规则图缓存在键下, 这样可以只读取规则一次，解析一次，然后复用决策对象 decision
    result = await zr.async_evaluate(key, {"input": 7, "myvar": 15})
    print("zen rule custom_v2 result:", result)

    result = await zr.async_evaluate(key, {"input": 7, "myvar": 15})
    print("zen rule custom_v2 result2:", result)
```

```python
from pathlib import Path
from zen_rule.custom.udf_manager import udf
from zen_rule import ZenRule


def loader(key):
    basedir = Path(__file__).parent
    filename = basedir / "graph" / key
    with open(filename, "r", encoding="utf8") as f:
        logger.warning(f"graph json: %s", filename)
        return f.read()


async def test_zenrule_with_loader():
    zr = ZenRule({"loader": loader})

    result = await zr.async_evaluate("custom_v2.json", {"input": 7, "myvar": 15})
    print("zen rule custom_v2 result:", result)

    result = await zr.async_evaluate("custom_v2.json", {"input": 7, "myvar": 15})
    print("zen rule custom_v2 result2:", result)

    result = await zr.async_evaluate("custom_v2_parse.json", {"input": 7, "myvar": 15})
    print("zen rule custom_v2 result2:", result)

```


包含自定义函数示例的规则:

```json
{
  "contentType": "application/vnd.gorules.decision",
  "nodes": [
    {
      "id": "115975ef-2f43-4e22-b553-0da6f4cc7f68",
      "type": "inputNode",
      "position": {
        "x": 180,
        "y": 240
      },
      "name": "Request"
    },
    {
      "id": "138b3b11-ff46-450f-9704-3f3c712067b2",
      "type": "customNode",
      "position": {
        "x": 470,
        "y": 240
      },
      "name": "customNode1",
      "content": {
        "kind": "sum",
        "config": {
          "version": "v2",
          "meta": {
            "user": "wanghao@geetest.com",
            "proj": "proj_id"
          },
          "prop1": "{{ a + 10 }}",
          "passThrough": true,
          "inputField": null,
          "outputPath": null,
          "expressions": [
            {
              "id": "52d41e3d-067d-4930-89bd-832b038cd08f",
              "key": "result",
              "value": "foo(myvar,bar(zoo('fccdjny',6, 3.14),'a'), bas())"
            }
          ]
        }
      }
    },
    {
      "id": "db8797b1-bcc1-4fbf-a5d8-e7d43a181d5e",
      "type": "outputNode",
      "position": {
        "x": 780,
        "y": 240
      },
      "name": "Response"
    }
  ],
  "edges": [
    {
      "id": "05740fa7-3755-4756-b85e-bc1af2f6773b",
      "sourceId": "115975ef-2f43-4e22-b553-0da6f4cc7f68",
      "type": "edge",
      "targetId": "138b3b11-ff46-450f-9704-3f3c712067b2"
    },
    {
      "id": "5d89c1d6-e894-4e8a-bd13-22368c2a6bc7",
      "sourceId": "138b3b11-ff46-450f-9704-3f3c712067b2",
      "type": "edge",
      "targetId": "db8797b1-bcc1-4fbf-a5d8-e7d43a181d5e"
    }
  ]
}

```


## custom node spec v2

将函数调用解析为抽象语法树后解释执行:

> foo(myvar,bar(zoo('fccdjny',6, 3.14),'a'), bas())

解析后得到如下语法树, 解释执行即可:

```python
[
    {
        "name": "zoo",
        "args": [["'fccdjny'", "string"], [6, "int"], [3.14, "float"]],
        "ns": "",
        "id": "566a36f923b34cbd9c159272adc988ae",
    },
    {
        "name": "bar",
        "args": [
            [
                {
                    "name": "zoo",
                    "args": [
                        ["'fccdjny'", "string"],
                        [6, "int"],
                        [3.14, "float"],
                    ],
                    "ns": "",
                    "id": "566a36f923b34cbd9c159272adc988ae",
                },
                "func_value",
            ],
            ["'a'", "string"],
        ],
        "ns": "",
        "id": "5d0b81e086d748d4902a35fd85bad974",
    },
    {
        "name": "bas",
        "args": [],
        "ns": "",
        "id": "7f8448aad2594b479f6df2e2241707c7",
    },
    {
        "name": "foo",
        "args": [
            ["myvar", "var"],
            [
                {
                    "name": "bar",
                    "args": [
                        [
                            {
                                "name": "zoo",
                                "args": [
                                    ["'fccdjny'", "string"],
                                    [6, "int"],
                                    [3.14, "float"],
                                ],
                                "ns": "",
                                "id": "566a36f923b34cbd9c159272adc988ae",
                            },
                            "func_value",
                        ],
                        ["'a'", "string"],
                    ],
                    "ns": "",
                    "id": "5d0b81e086d748d4902a35fd85bad974",
                },
                "func_value",
            ],
            [
                {
                    "name": "bas",
                    "args": [],
                    "ns": "",
                    "id": "7f8448aad2594b479f6df2e2241707c7",
                },
                "func_value",
            ],
        ],
        "ns": "",
        "id": "0c509d4654ef443eb621d791d3ffcaa1",
    },
]

```

使用示例如下:

```python

async def ast_exec():
    v = [{"name": "zoo", "args": [["'fccdjny'", "string"], [6, "int"], [3.14, "float"]], "ns": "", "id": "566a36f923b34cbd9c159272adc988ae"}, {"name": "bar", "args": [[{"name": "zoo", "args": [["'fccdjny'", "string"], [6, "int"], [3.14, "float"]], "ns": "", "id": "566a36f923b34cbd9c159272adc988ae"}, "func_value"], ["'a'", "string"]], "ns": "", "id": "5d0b81e086d748d4902a35fd85bad974"}, {"name": "bas", "args": [], "ns": "", "id": "7f8448aad2594b479f6df2e2241707c7"}, {"name": "foo", "args": [["myvar", "var"], [{"name": "bar", "args": [[{"name": "zoo", "args": [["'fccdjny'", "string"], [6, "int"], [3.14, "float"]], "ns": "", "id": "566a36f923b34cbd9c159272adc988ae"}, "func_value"], ["'a'", "string"]], "ns": "", "id": "5d0b81e086d748d4902a35fd85bad974"}, "func_value"], [{"name": "bas", "args": [], "ns": "", "id": "7f8448aad2594b479f6df2e2241707c7"}, "func_value"]], "ns": "", "id": "0c509d4654ef443eb621d791d3ffcaa1"}]

    await ast_exec(v, {"input": 7, "myvar": 15}, {"node_id": "nodexxxxx", "meta": {}})
```