
# uv

## best practice

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

初始化一个 `python 库`的包结构,

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

uv init 默认把程序放在 src 文件夹下(src文件夹下无 __init__.py 文件, 不是python模块). 


如何对开发库进行测试:  
以 zen-rule 项目为例, 使用如下命令构建开发环境，安装依赖库  

> uv pip install -e .

使用此命令将当前包以编辑模式(--editable, -e)安装在当前的虚拟环境中, 这样可以使用 `python main.py` 运行程序即可.(或者将 src 包加入 sys.path 中, 或者使用 PYTHONPATH=src python main.py)

```bash
(zen-rule) ryefccd@republic:~/workspace/zen-rule$ uv pip list
Package                  Version Editable project location
------------------------ ------- --------------------------------
...                      ...
zen-engine               0.49.1
zen-rule                 0.10.1  /home/ryefccd/workspace/zen-rule
```

此命令在依赖库中安装了一个指向当前开发代码的链接文件 _zen_rule.pth 

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


## uv commands

### 管理 python 解释器(uv python)

uv 在 python 开发中可以用于选择python解释器, 创建虚拟环境, 创建python应用包,  创建 python 库.

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


## monorepo(multi develop packages dependencies)

[uv workspaces](https://docs.astral.sh/uv/concepts/projects/workspaces/#using-workspaces)