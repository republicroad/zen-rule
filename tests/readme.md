
# 测试


## pytest

在项目跟目录执行下列命令进行单元测试:  

```bash
$ pytest tests
```

在项目跟目录执行下列命令进行相关函数的压力测试以及结果对比:  

```bash
$ pytest tests --benchmark-only
```


### fixture

单元测试中最终要的概念，用于组织代码, 可以声明测试依赖，简化测试构建过程.


### asyncio

测试异步代码需要使用 `@pytest.mark.asyncio` 来进行标记
todo: 关于 loop_scope 需要补充说明

https://pytest-asyncio.readthedocs.io/en/v0.24.0/how-to-guides/index.html  
https://pytest-asyncio.readthedocs.io/en/v0.24.0/concepts.html  


### 调试技巧

一般可以直接在测试函数的末尾 assert False 让测试失败, 然后使用 -l 选项输出测试失败时的局部变量的值. 方便排查问题.

```bash
def test_xxxx():
    ...
    ...
    ...

    result = res["result"]
    assert False  # pytest tests/zen/test_zen_custom.py -k "test_custmer_node_cache_decision" -sv -l 
    # pytest -svlx

-s 捕获输出 
-l 断言错误时显示测试函数局部变量
-x 遇到单元测试错误时立即退出
-v 详细信息
--setup-show  展示测试前后的hook逻辑, 类似于 unittest 中的 tearup 和 teardown.
--log-cli-level=0  设置 live log 捕获级别，0 是 NOTSET, 所有的日志都会输出.

--pdb --pdbcls=IPython.terminal.debugger:TerminalPdb  单元测试失败时进入 ipdb shell. 可以进行单步调试.
```

所以，在单元测试的最佳实践中，尽量多用日志模块来记录信息. 这样可以是否设置 `--log-cli-level` 配置是否打印日志输出.
更重要的是, 日志信息可以被 caplog fixture 来进行断言. 可以方便的对日志进行管理.
只建议在临时调试的时候使用 print. 配合 `-s` 命令来查看输出.
如果滥用了 print, 那么在单元测试 `-s` 输出时就会有大量的信息干扰.

使用 `--setup-show ` 查看使用了哪些 **fixture**, 以及这些 **fixture** 怎么建立和销毁的.
使用 `-x` 让单元测试在失败后迅速终止，方便排查错误.
使用 `-l` 可以展示此单元测试函数内局部变量的值.

注意 live log 配置 `--log-cli-level` 与 `-s` 是没有关系的.
> Live Logs are now sent to sys.stdout and no longer require the -s command-line option to work.

测试用例变得复杂后, 使用 `--pdb --pdbcls=IPython.terminal.debugger:TerminalPdb` 在单元测试失败时进入 ipdb shell. 可以进行单步调试.


### coverage

> 依赖包:  
> coverage==7.6.12  
> pytest-cov==5.0.0  

```bash
  pytest --cov=. --cov-report=html tests/  在当前目录会生成一个 htmlcov 目录, 访问htmlcov/index.html 即可查看代码覆盖详细信息.
  pytest --cov=. tests/                    在命令行显示各个模块的代码覆盖率和总体覆盖率.
```

[coverage config sample](https://coverage.readthedocs.io/en/7.6.12/config.html#sample-file)
[partial-branches](https://coverage.readthedocs.io/en/latest/branch.html)

### benchmark

默认在配置中pytest.ini禁用了 benchmark 测试

```ini
...

[pytest]
# 注意，ignore 文件夹要配置全路径
addopts = --ignore=tests/graph --ignore=tests/zen/test-data/graphs --ignore=tests/zen/test-data/js

...
```

使用 `--benchmark-only` 可以只跑 benchmark 用例.

> `pytest tests --benchmark-only`  
> `pytest tests --benchmark-only --benchmark-disable-gc` # 降低 gc 对测试的影响

对于相同功能的不同实现可以把他们的实现代码准备好，放在 benchmark 测试用例中, 可以直观体现技术选型的原因.


示例如下所示:
```bash
zen-ruleryefccd@republic:~/workspace/zen-rule$ pytest  tests --benchmark-only
=================================================================================== test session starts ====================================================================================
platform linux -- Python 3.10.12, pytest-8.4.1, pluggy-1.6.0
benchmark: 5.1.0 (defaults: timer=time.perf_counter disable_gc=False min_rounds=5 min_time=0.000005 max_time=1.0 calibration_precision=10 warmup=False warmup_iterations=100000)
rootdir: /home/ryefccd/workspace/zen-rule/tests
configfile: pytest.ini
plugins: benchmark-5.1.0, asyncio-1.1.0
asyncio: mode=strict, asyncio_default_fixture_loop_scope=session, asyncio_default_test_loop_scope=function
collected 47 items                                                                                                                                                                         

tests/bench/test_zen_engine.py ......                                                                                                                                                [ 12%]
tests/test_parser.py ssss                                                                                                                                                            [ 21%]
tests/test_pytest_demo.py s                                                                                                                                                          [ 23%]
tests/zen/custom_node/test_zen_cn_contextvars.py ss                                                                                                                                  [ 27%]
tests/zen/custom_node/test_zen_cn_input.py sss                                                                                                                                       [ 34%]
tests/zen/test_async.py sssssss                                                                                                                                                      [ 48%]
tests/zen/test_sync.py sssssssssss                                                                                                                                                   [ 72%]
tests/zen/test_zen.py sss                                                                                                                                                            [ 78%]
tests/zen/test_zen_expression.py sssssssss                                                                                                                                           [ 97%]
tests/zen/test_zen_node_types.py s                                                                                                                                                   [100%]


------------------------------------------------------------------------------- benchmark 'zen-engine-decision': 6 tests ------------------------------------------------------------------------------
Name (time in us)          Min                    Max                  Mean                StdDev              Median                 IQR            Outliers         OPS            Rounds  Iterations
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_5                167.7670 (1.0)       3,279.6570 (1.0)        531.9833 (1.0)        389.6361 (1.0)      390.7480 (1.0)      480.9100 (1.01)       147;33  1,879.7584 (1.0)        1190           1
test_4                170.3550 (1.02)     11,933.7080 (3.64)       886.3171 (1.67)     1,001.7255 (2.57)     483.7925 (1.24)     824.1735 (1.72)      371;250  1,128.2644 (0.60)       2676           1
test_3                180.1810 (1.07)      3,988.4590 (1.22)       575.3604 (1.08)       439.5681 (1.13)     406.8730 (1.04)     477.9995 (1.0)        190;72  1,738.0409 (0.92)       1521           1
test_2                210.7520 (1.26)      9,432.8170 (2.88)       898.7334 (1.69)     1,042.3410 (2.68)     455.7875 (1.17)     736.1245 (1.54)      413;315  1,112.6770 (0.59)       3012           1
test_1                256.4530 (1.53)      5,961.1790 (1.82)     1,002.9876 (1.89)     1,001.6547 (2.57)     561.2290 (1.44)     826.9592 (1.73)      317;246    997.0213 (0.53)       2209           1
test_0                259.4610 (1.55)      8,118.9630 (2.48)       762.2640 (1.43)       674.1789 (1.73)     529.9910 (1.36)     507.5360 (1.06)      205;163  1,311.8815 (0.70)       2269           1
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
============================================================================== 6 passed, 41 skipped in 11.88s ==============================================================================

```


https://pytest-benchmark.readthedocs.io/en/latest/usage.html


### live log

在 pytest.ini 配置文件中可以对 live log 的日志选项进行详细配置.
可以在命令行中 `--log-cli-level=0` 打开 live log 输出.

```bash
pytest tests --log-cli-level=0
```


```ini
[pytest]
# 注意，ignore 文件夹要配置全路径
addopts = --ignore=tests/zen/test-data/graphs --ignore=tests/zen/test-data/js --benchmark-skip
# norecursedirs = tests/exclude_pytest/
asyncio_default_fixture_loop_scope = session

# 关于 live log 细粒度配置选项
# live log 
log_cli = 1
log_cli_level = DEBUG
; log_cli_format = %(asctime)s [%(levelname)6s %(name)s ] %(message)s [(%(pathname)s:%(lineno)s)]  # 可以通过日志定位代码位置.
log_cli_format = %(asctime)s [%(levelname)6s %(name)s ] %(message)s
log_cli_date_format=%Y-%m-%d %H:%M:%S
```

https://docs.pytest.org/en/stable/how-to/logging.html#incompatible-changes-in-pytest-3-4


### caplog

https://docs.pytest.org/en/stable/how-to/logging.html#caplog-fixture


### ipdb

```bash
pytest tests --pdb --pdbcls=IPython.terminal.debugger:TerminalPdb
```

https://stackoverflow.com/a/43374657



## pytest 常见命令行选项

pytest tests/zen/test_zen.py -sl
pytest tests/zen/test_zen.py -k "test_xxx_function_name"
pytest tests/zen/test_zen.py --setup-show

> -s 捕获标准输出
> -l 显示出错的测试用例中的局部变量
> -k 指定某一个测试用例执行
> --setup-show  展示的单元测试 SETUP 和 TEARDOWN 的细节，展示测试依赖的加载和销毁顺序


## reference

[Python Developer Tooling Handbook](https://pydevtools.com/handbook/)

[Publishing Your First Python Package to PyPI](https://pydevtools.com/handbook/tutorial/publishing-your-first-python-package-to-pypi/)
[Setting up testing with pytest and uv](https://pydevtools.com/handbook/tutorial/setting-up-testing-with-pytest-and-uv/)  