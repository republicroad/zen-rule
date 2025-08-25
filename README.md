
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
    basedir = Path(__file__).parent
    filename = basedir / "graph" / "custom_v3.json"
    key = filename

    if not zr.get_decision_cache(key):
        # 根据实际情况去加载规则图的内容.
        with open(filename, "r", encoding="utf8") as f:
            logger.warning(f"graph json: %s", filename)
            content =  f.read()
        zr.create_decision_with_cache_key(key, content)  # 将规则图缓存在键下, 这样可以只读取规则一次，解析一次，然后复用决策对象 decision
    result = await zr.async_evaluate(key, {"input": 7, "myvar": 15})
    print("zen rule custom_v3 result:", result)
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

    result = await zr.async_evaluate("custom_v3.json", {"input": 7, "myvar": 15})
    print("zen rule custom_v3 result:", result)

    result = await zr.async_evaluate("custom_v3.json", {"input": 7, "myvar": 15})
    print("zen rule custom_v3 result2:", result)
```

示例程序请参考 main.py, 运行 python main.py 即可运行测试示例.  

包含自定义函数示例的规则:  
[custom_v3.json](graph/custom_v3.json)  



## 自定义算子规范v3

在决策引擎中, 自定义算子主要承担外部数据查询, 状态交互, 以及一些自定义功能拓展. 
考虑到界面中会对自定义算子进行分类, 这时候在某个自定义类别的节点中只能访问这个类别的函数,
这样有利于降低最后用户的使用难度. 


![alt text](docs/custom_nodes.png)  


### 格式一

如果支持不同自定义算子的嵌套, 那么这些节点分类就形同虚设.
考虑到自定义算子再未来的功能以及演化, 暂时决定自定义算子不支持嵌套调用和解析.
参考 zen-engine 的表达式测试用例. 为了简化参数的解析, 决定选用 `;;` 作为函数的分隔符号.

> foo;;myvar ;;max([5, 8, 2, 11, 7]);;rand(100);; 'fccd;;jny' ;;3+4

表示 foo 算子传入了五个参数:
1. zen 表达式变量 myvar
2. zen 表达式函数 max([5, 8, 2, 11, 7])
3. zen 表达式 rand(100)
4. zen 表达式 'fccd;;jny'
5. zen 表达式 3+4


解析后得到如下结构, 解释执行即可:

> ["foo", "myvar", "max([5, 8, 2, 11, 7])", "rand(100)", "3+4"]

解析逻辑如下:

```python
def parse_oprator_expr_v3(expr):
    # 不能简单使用字符串分割, 因为字符串中可能会有分隔符的模式出现, 比如:
    # foo ;; myvar ;; bar(zoo('fccd;;jny',6, 3.14),'a');; a+string(xxx)
    # foo;;myvar;;max([5, 8, 2, 11, 7]);;rand(100);; 'fccd;;jny' ;;3+4
    # expr.split(";;")
    pattern = r""";;(?=(?:[^"']*["'][^"']*["'])*[^"']*$)"""
    # To split the string by these semicolon:
    _parts = re.split(pattern, expr)
    parts = [i.strip() for i in _parts]  # 去掉表达式前后的空格
    return parts
```

### 格式二

第二种就是保留技术更为熟悉的函数嵌套调用结构.
这种格式需要解析函数的嵌套调用, 还需要解析各种常量语法结构, 比如 数字， 布尔，字符串，数组，object对象, 
以及各种数组和字符串下标索引访问和切片访问语法格式, 还有中缀表达式(算术运算和逻辑运算), 非空判定, 三元表达式.

这部分需要使用上下无关文法定义解析或者peg语法解析.

> foo(myvar,max([5, 8, 2, 11, 7]),rand(100), 'fccd;;jny', 3+4)


解析后格式如下:

> [["foo", "myvar", "max([5, 8, 2, 11, 7])", "rand(100)", "'fccd;;jny'", "3+4"]]

此实现需要不断的去补充关于 zen 表达式语法结构的解析.  
详细参考 tests/test_zen_expr_parser.py 中的实现. 
```bash
$ python '/home/ryefccd/workspace/zen-rule/tests/test_zen_expr_parser.py'
foo(myvar,max([5, 8, 2, 11, 7]),rand(100), 'fccd;;jny', 3+4) --> [['foo', 'myvar', 'max([5, 8, 2, 11, 7])', 'rand(100)', "'fccd;;jny'", '3+4']]
...
```

目前使用 pyparsing 来解析, 将来考虑使用[lark](https://github.com/lark-parser/lark) 来做语法解析.

### 解析后格式

```json
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
        "expressions": [/*expressions 是约定的前端格式*/
        {
            "id": "52d41e3d-067d-4930-89bd-832b038cd08f",
            "key": "result",
            "value": "foo;;myvar ;;max([5, 8, 2, 11, 7]);;rand(100);; 'fccd;;jny' ;;3+4"
        }
        ],
        "expr_asts": [/*expr_asts 是后端解析动态产生的*/
        {
            "id": "52d41e3d-067d-4930-89bd-832b038cd08f",
            "key": "result",
            "value": ["foo", "myvar", "max([5, 8, 2, 11, 7])", "rand(100)", "\\'fccd;;jny\\'", "3+4"]
        }
        ]
    }
    }
}
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

### uv python包依赖设置

在当前项目中或者 ~/.config/uv/uv.toml 或者 /etc/uv/uv.toml 填写下面的内容：

uv.toml
```toml
[[index]]
url = "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/"
default = true

[[index]]
url = "https://pypi.org/simple/"
default = false

```

或者在当前的 pyproject.toml 加入

```toml
[[tool.uv.index]]
url = "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/"
default = true

[[tool.uv.index]]
url = "https://pypi.org/simple/"
default = false
```

[Configuration files](https://docs.astral.sh/uv/concepts/configuration-files/)  
[tsinghua pypi](https://mirrors.tuna.tsinghua.edu.cn/help/pypi/)  
[How to set index url for uv like pip configurations](https://stackoverflow.com/questions/79603558/how-to-set-index-url-for-uv-like-pip-configurations)  
[flat-indexes](https://docs.astral.sh/uv/concepts/indexes/#flat-indexes)  

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


### 依赖管理

增加 pytest 作为开发依赖  
```bash
$ uv add --dev pytest
```

增加不同开发组依赖  
```bash
$ uv add --group lint ruff
```

[Managing dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/#managing-dependencies)  
[Development dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/#development-dependencies)  


导出 requirements.txt 格式的依赖
```bash
$ uv pip compile pyproject.toml > requirements.txt
```


## logging

[Configuring Logging for a Library](https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library)  
[What are the uses of Null handler in python logging?](https://stackoverflow.com/a/76887486)  


## reference

[Setting up testing with pytest and uv](https://pydevtools.com/handbook/tutorial/setting-up-testing-with-pytest-and-uv/)  

pypi src:

- https://pypi.org/simple/