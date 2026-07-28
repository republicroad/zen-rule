
# AGENTS.md — zen-rule AI 编码助手说明

## 项目概述

zen-rule 是 [zen-engine](https://pypi.org/project/zen-engine/) 的增强库，提供决策缓存和自定义节点/函数（UDF）规范。核心代码在 `src/zen_rule/`，使用 hatchling 构建，发布到 PyPI。

## 核心模块

| 模块 | 职责 |
|------|------|
| `src/zen_rule/engine.py` | ZenRule 主类：决策缓存、graph_addons 图增强、custom_handler_func、;;表达式解析 |
| `src/zen_rule/register.py` | UDFManager、@udf 装饰器、函数签名→JSON Schema 提取（inspect + docstring-parser + pydantic） |
| `src/zen_rule/contrib.py` | 内置 UDF（inout、func_without_args），随 engine 导入自动注册 |

## 常用命令

```bash
# 安装开发环境（编辑模式）
uv pip install -e .

# 运行演示
python main.py

# 运行全部测试
pytest tests

# 运行指定测试
pytest tests/zen/test_zen.py -sv

# 运行 benchmark
pytest tests --benchmark-only

# 代码覆盖率
pytest --cov=. --cov-report=html tests/

# 构建包
rm -r dist; uv build

# 发布到 PyPI
uv publish

# 版本管理
bump-my-version bump patch   # 0.30.0 → 0.30.1
bump-my-version bump minor   # 0.30.0 → 0.31.0
bump-my-version bump major   # 0.30.0 → 1.0.0
```

## 关键约定

### loader 必须同步

ZenRule 的 `options["loader"]` 函数必须是同步函数。异步 loader 会让 Rust 侧的 `ZenEngine.get_decision` 线程阻塞，导致 hang。

### UDF 注册

使用 `@udf(namespace="...")` 装饰器注册自定义函数。函数的签名（参数名、类型注解、默认值）和 docstring 会被自动提取为 JSON Schema，兼容 OpenAI function calling 格式。编写新 UDF 时请：

- 为参数添加类型注解
- 编写完整的 docstring（含 `:param`、`:type`、`:returns`、`:rtype`）
- 返回值类型注解同样会被提取

### 自定义节点规范

当前使用 v3 规范。自定义节点中的 UDF 调用表达式以 `;;` 作为分隔符（非函数参数分隔符）。解析逻辑在 `ZenRule.parse_oprator_expr`。

### 文档与注释

- 所有用户可见的文档和注释使用中文
- 日志输出使用 `logging` 模块，`__init__.py` 中不主动调用 `basicConfig`（库的惯例）
- 测试中尽量使用 `logger` 而非 `print`

## 测试

- 配置文件：`tests/pytest.ini`
- 异步测试标记：`@pytest.mark.asyncio`
- 基准测试：`tests/bench/`，默认 `--benchmark-skip`，用 `--benchmark-only` 启用
- fixture 定义：`tests/conftest.py`
- 测试数据：`tests/data/`、`tests/zen/test-data/`

常用调试命令：
```bash
pytest tests/zen/test_zen.py -k "test_name" -sv -l    # -l 显示失败时局部变量
pytest tests --pdb --pdbcls=IPython.terminal.debugger:TerminalPdb  # 失败时进入 ipdb
```

## 文档

- 架构文档：`docs/architecture.md`
- UDF 规范：`docs/udf_spec.md`
- JDM 规范：`docs/jdm.md`
- 测试指南：`tests/readme.md`
- 自定义节点演进：`archive/readme.md`

## TypeScript 子项目

`packages/zen-rule/` 是 TypeScript 重写实验（Bun + `@gorules/zen-engine`），功能与 Python 版等价。运行方式：

```bash
cd packages/zen-rule
bun install
bun run main.ts
```

详细实现计划见 `packages/zen-rule/PLAN.md`。改动 TypeScript 子项目时，请同步考虑是否需要更新 Python 版对应逻辑。

## Java 子项目

`java/` 是 Java 移植（Maven + `io.gorules:zen-engine` 0.4.7），功能与 Python 版等价。要求 **JDK 21+**。

```bash
# 编译并运行
$env:JAVA_HOME = "path/to/jdk-21"
mvn -f java/pom.xml compile exec:java
```

关键文件：
- `java/src/main/java/io/gorules/zen_rule/ZenRule.java` — 核心类
- `java/src/main/java/io/gorules/zen_rule/register/UdfManager.java` — UDF 注册与执行
- `java/src/main/java/io/gorules/zen_rule/register/UdfKwargs.java` — 模拟 Python `**kwargs`
- `java/src/main/java/io/gorules/zen_rule/contrib/` — 内置 UDF（inout, func_without_args）
- `java/src/main/java/io/gorules/zen_rule/Main.java` — 测试入口

架构详见 `docs/architecture.md` Java 移植子项目章节。
