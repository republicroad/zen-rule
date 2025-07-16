
# zen-rule

zen-rule 是 [zen-engine](https://pypi.org/project/zen-engine/) 加强版本:
  
1. 提供多个 decision 的缓存.  
2. 提供自定义节点中多个函数调用表达式的定义, 解析和调用规范.  

## example

推荐线上使用 decision 缓存模式, 这样规则只需要加载，解析一次后重复使用，提高系统性能.  
每次先判断zenRule实例中是否有规则的缓存，如果没有则去加载规则图; 如果有就直接通过规则键去调用规则对入参进行处理, 得到最后规则的输出.

```python
from pathlib import Path
from zen_rule import ZenRule, udf


async def test_zenrule():
    """
        推荐线上生产环境使用此模式进行规则执行, 可以缓存决策对象, 提高性能.
    """
    zr = ZenRule({})
    key = "xxxx_rule"
    basedir = Path(__file__).parent
    filename = basedir / "graph" / "custom_v2.json"

    if not zr.get_decision_cache(key):
        # 根据实际情况去加载规则图的内容.
        with open(filename, "r", encoding="utf8") as f:
            logger.warning(f"graph json: %s", filename)
            content =  f.read()
        zr.create_decision_with_cache_key(key, content)  # 将规则图缓存在键下, 这样可以只读取规则一次，解析一次，然后复用决策对象 decision
    result = await zr.async_evaluate(key, {"input": 7, "myvar": 15})
    print("zen rule custom_v2 result:", result)
```


如果提供 loader 函数, 就是如下调用示例.  
```python
from pathlib import Path
from zen_rule import ZenRule, udf


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
[custom_v2.json](graph/custom_v2.json)  

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

## develop

### 初始化包
初始化一个 python 库的包结构,

```bash
uv init --lib .
uv init --lib zen-rule
```

uv init 默认把程序放在 src 文件夹下(src文件夹下无 __init__.py 文件, 不是python模块). 

### 本地开发

程序开发时，需要对开发的包进行测试. 有两种方法:

1. 将 src 包加入 sys.path 中, 或者使用 PYTHONPATH=src python main.
2. 使用 `uv pip install -e .` 将开发包以编辑模式安装到系统依赖 site-packages 中.

pip install -e 在依赖库中安装了一个指向当前开发代码的链接文件 _zen_rule.pth 

```bash
(.venv) ryefccd@republic:~/workspace/zen-rule$ cat .venv/lib/python3.10/site-packages/zen_rule-0.1.0.dist-info/RECORD 
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

### 包构建

先把 dist 包中的文件删除, 然后 uv build 执行构建.

```bash
rm -r dist  
uv build
```

### 包发布

需要在 pypi 上创建一个账号, 在完成 `uv build` 之后, 使用 `uv publish` 进行包的上传.

```bash
uv publish
```


To set your API token for PyPI, you can create a $HOME/.pypirc similar to:

```ini
[pypi]
username = __token__
password = <PyPI token>
```

[Using a PyPI token](https://packaging.python.org/en/latest/specifications/pypirc/#using-a-pypi-token)  
[Building and publishing a package](https://docs.astral.sh/uv/guides/package/#publishing-your-package)  

## monorepo(multi develop packages dependencies)

[uv workspaces](https://docs.astral.sh/uv/concepts/projects/workspaces/#using-workspaces)



## uv 

uv 在 python 开发中可以用于选择python解释器, 创建虚拟环境, 创建python应用包,  创建 python 库.


### 管理 python 解释器(uv python)

#### `uv python list` 

可以显示当前python的解释器.
```bash
(.venv) $ uv python list
cpython-3.14.0b4-linux-x86_64-gnu                 <download available>
cpython-3.14.0b4+freethreaded-linux-x86_64-gnu    <download available>
cpython-3.14.0b2-linux-x86_64-gnu                 /home/ryefccd/.local/share/uv/python/cpython-3.14.0b2-linux-x86_64-gnu/bin/python3.14
cpython-3.13.5-linux-x86_64-gnu                   <download available>
cpython-3.13.5+freethreaded-linux-x86_64-gnu      <download available>
cpython-3.12.11-linux-x86_64-gnu                  <download available>
cpython-3.11.13-linux-x86_64-gnu                  <download available>
cpython-3.10.18-linux-x86_64-gnu                  <download available>
cpython-3.10.12-linux-x86_64-gnu                  /usr/bin/python3.10
cpython-3.10.12-linux-x86_64-gnu                  /usr/bin/python3 -> python3.10
cpython-3.9.23-linux-x86_64-gnu                   <download available>
cpython-3.8.20-linux-x86_64-gnu                   <download available>
pypy-3.11.13-linux-x86_64-gnu                     <download available>
pypy-3.10.16-linux-x86_64-gnu                     <download available>
pypy-3.9.19-linux-x86_64-gnu                      <download available>
pypy-3.8.16-linux-x86_64-gnu                      <download available>
graalpy-3.11.0-linux-x86_64-gnu                   <download available>
graalpy-3.10.0-linux-x86_64-gnu                   <download available>
graalpy-3.8.5-linux-x86_64-gnu                    <download available>
```

#### `uv python install`

安装 python 的版本(开代理加速安装)
```bash
uv python install 3.13  # 可以指定版本
uv python install  cpython-3.14.0b4-linux-x86_64-gnu   # 也可以指定全限定名版本.
```

`uv python install 3.12 --preview` 使用 `--preview` 选项可以将 python3.12 添加至 PATH 下.这样可以全局使用.


#### `uv python dir`
查看已经下载的 python 解释器.


```bash
ryefccd@republic:~$ ll `uv python dir`
总计 32
drwxrwxr-x 5 ryefccd ryefccd 4096  7月 15 11:48 ./
drwxrwxr-x 3 ryefccd ryefccd 4096  6月 27 15:35 ../
drwxrwxr-x 6 ryefccd ryefccd 4096  7月 15 11:48 cpython-3.12.11-linux-x86_64-gnu/
lrwxrwxrwx 1 ryefccd ryefccd   69  7月 15 11:48 cpython-3.12-linux-x86_64-gnu -> /home/ryefccd/.local/share/uv/python/cpython-3.12.11-linux-x86_64-gnu/
drwxrwxr-x 6 ryefccd ryefccd 4096  6月 27 15:35 cpython-3.14.0b2-linux-x86_64-gnu/
lrwxrwxrwx 1 ryefccd ryefccd   70  7月 15 11:48 cpython-3.14-linux-x86_64-gnu -> /home/ryefccd/.local/share/uv/python/cpython-3.14.0b2-linux-x86_64-gnu/
-rw-rw-r-- 1 ryefccd ryefccd    1  6月 27 15:35 .gitignore
-rwxrwxrwx 1 ryefccd ryefccd    0  6月 27 15:35 .lock*
drwxrwxr-x 7 ryefccd ryefccd 4096  7月 15 11:48 .temp/
```

#### uv python find

`uv python find` 查看当前的uv使用的python版本.
```bash
ryefccd@republic:~$ uv python find
/home/ryefccd/workspace/brde/.venv/bin/python3.1
```

`uv python find <verison>` 可以查看python版本解释器的位置. 
```bash
(.venv) $ uv python find 3.12
/home/ryefccd/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/bin/python3.12
(.venv) $ uv python find 3.13
error: No interpreter found for Python 3.13 in virtual environments, managed installations, or search path
(.venv) $ uv python find 3.14
/home/ryefccd/.local/share/uv/python/cpython-3.14-linux-x86_64-gnu/bin/python3.14
```


### 创建虚拟环境

`uv venv` 会再当前目录创造一个 .venv 的虚拟环境.

`uv venv --python 3.10 myvenv` 指定python的版本创建虚拟环境.

### 运行python命令

`uv run xxx.py`

`uv run python -c "import sys;print(sys.executable)"` 


### 创建python应用包

#### uv init without package

`uv init pyapp` 即可创建python应用包的结构. 应用由一个入口程序 main.py 和一个项目描述文件 pyproject.toml 构成.

```bash
uv init pyapp

(.venv) $ tree -a pyapp/
pyapp/
├── main.py
├── pyproject.toml
└── README.md
```

`uv add fastapi` 可以添加应用依赖.


#### uv init with package

`uv init pyapp2 --package` 即可创建python应用包的结构. 应用由一个入口程序包 src/pyapp2 一个项目描述文件 pyproject.toml 构成.

```bash
(.venv) $ tree -a pyapp2
pyapp2
├── pyproject.toml
├── README.md
└── src
    └── pyapp2
        └── __init__.py
```

### 创建 python 库

```bash
uv init --lib pylib

(.venv) $ tree -a pylib/
pylib/
├── pyproject.toml
├── README.md
└── src
    └── pylib
        ├── __init__.py
        └── py.typed
```

`uv add zen-engine` 可以添加库依赖.

如何对开发库进行测试:
程序开发时，需要对开发的包进行测试. 有两种方法:

1. 将 src 包加入 sys.path 中, 或者使用 PYTHONPATH=src python main.
2. 使用 `uv pip install -e .` 将开发包以编辑模式安装到系统依赖 site-packages 中.

pip install -e 在依赖库中安装了一个指向当前开发代码的链接文件 _pylib.pth 