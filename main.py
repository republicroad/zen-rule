
import logging
import inspect
import asyncio
from pprint import pprint
from pathlib import Path
from zen_rule import ZenRule, udf, FuncArg, FuncRet, ast_exec

from utils import httpsession, get_state

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@udf()
def zoo(*args, **kwargs):
    # get_state()
    # http_sess = httpsession.get()
    # logger.info(f"httpsession:{http_sess}")
    logger.info(f"{inspect.stack()[0][3]} args:{args}")
    logger.info(f"{inspect.stack()[0][3]} kwargs:{kwargs}")
    print("zoooooooooooooooooo")
    return "zoo value"


@udf()
def bar(*args, **kwargs):
    logger.info(f"{inspect.stack()[0][3]} args:{args}")
    logger.info(f"{inspect.stack()[0][3]} kwargs:{kwargs}")
    return "bar value"

@udf()
def bas(*args, **kwargs):
    logger.info(f"{inspect.stack()[0][3]} args:{args}")
    logger.info(f"{inspect.stack()[0][3]} kwargs:{kwargs}")
    return "bas value"

@udf(
    comments="test udf foo",
    args_info=[
        FuncArg(arg_name="a", arg_type="string", defaults="", comments="var a"),
        FuncArg(arg_name="b", arg_type="string", defaults="", comments="var b"),
        FuncArg(arg_name="c", arg_type="string", defaults="", comments="var c"),
    ],
    return_info=FuncRet(field_type="string", examples="fccdjny", comments="返回值示例, 字段解释")     
)
def foo(*args, **kwargs):
    logger.info(f"{inspect.stack()[0][3]} args:{args}")
    logger.info(f"{inspect.stack()[0][3]} kwargs:{kwargs}")
    return "foo value"


@udf(
    comments="group_distinct_1m_demo function",
    args_info=[
        FuncArg(arg_name="group", arg_type="string", defaults="", comments="var group"),
        FuncArg(arg_name="distinct", arg_type="string", defaults="", comments="var distinct"),
    ],
    return_info=FuncRet(field_type="object", examples={}, comments="返回值示例, 字段解释")     
)
def group_distinct_1m_demo(*args, **kwargs):
    logger.info(f"{inspect.stack()[0][3]} args:{args}")
    logger.info(f"{inspect.stack()[0][3]} kwargs:{kwargs}")
    return {
            "function": "group_distinct_1m_demo",
            "pv": 1,
            "uv": 2,
            "gpv": 3
        }

### 这个定义会报错
# @udf(
#     comments="group_distinct_1m_demo function",
#     args_info=[

#     ],
#     return_info=FuncRet(field_type="string", examples={}, comments="返回值示例, 字段解释")     
# )
# def group_distinct_1m_demo(ip, user, *args, **kwargs):
#     pass

async def test_zenrule():
    """
        推荐线上生产环境使用此模式进行规则执行, 可以缓存决策对象, 提高性能.
        规则图是 v2 版本, 执行引擎是 custom_handler_v2
    """
    # httpsession.set(object())  # 先设置 contextvars 再创建包含 custom_handler 的zen engine 实例, 自定义函数可以 contextvars get.
    zr = ZenRule({})
    # httpsession.set(object())
    key = "xxxx_rule"
    basedir = Path(__file__).parent
    filename = basedir / "graph" / "custom_v2.json"

    if not zr.get_decision_cache(key):
        # 根据实际情况去加载规则图的内容.
        with open(filename, "r", encoding="utf8") as f:
            logger.warning(f"graph json: %s", filename)
            content =  f.read()
        zr.create_decision_with_cache_key(key, content)  # 将规则图缓存在键下, 这样可以只读取规则一次，解析一次，然后复用决策对象 decision
    for i in range(1):
        result = await zr.async_evaluate(key, {"input": 7, "myvar": 15})
        print("zen rule custom_v2 result:", result)
        print(f"------------------{i}------------------------")

    # result = await zr.async_evaluate(key, {"input": 7, "myvar": 15})
    # print("zen rule custom_v2 result2:", result)


async def test_zenrulev1_with_enginev2():
    """
        规则图是 v1 版本, 执行引擎是 custom_handler_v2
    """
    zr = ZenRule({})
    key = "xxxx_rule"
    basedir = Path(__file__).parent
    filename = basedir / "graph" / "custom_v1.json"

    with open(filename, "r", encoding="utf8") as f:
        logger.warning(f"graph json: %s", filename)
        content =  f.read()

    zr.create_decision_with_cache_key(key, content)  # 将规则图缓存在键下, 这样可以只读取规则一次，解析一次，然后复用决策对象 decision
    result = await zr.async_evaluate(key, {"ip": "1.2.3.4", "user": "17707115956"})
    print("zen rule custom_v1 result:", result)


async def test_zenrulev1_with_enginev1():
    """
        规则图是 v1 版本, 执行引擎是 custom_handler_v1
    """
    zr = ZenRule({"customHandler": ZenRule.custom_handler_v1})
    key = "xxxx_rule"
    basedir = Path(__file__).parent
    filename = basedir / "graph" / "custom_v1.json"

    with open(filename, "r", encoding="utf8") as f:
        logger.warning(f"graph json: %s", filename)
        content =  f.read()

    zr.create_decision_with_cache_key(key, content)  # 将规则图缓存在键下, 这样可以只读取规则一次，解析一次，然后复用决策对象 decision
    result = await zr.async_evaluate(key, {"ip": "1.2.3.4", "user": "17707115956"})
    print("zen rule custom_v1 result:", result)




# 需要对 async loader 定义进行测试.
def loader(key):
    """
        loader 如果 loader 是异步函数, 那么同步的 get_decision 会有问题.
        除非我们自己实现 zenRule 的 get_decision, 而不是去调用 zenEngine的 get_decision
        加载规则还是让客户自己选择实现, 然后调用 create_decision_with_cache_key 缓存下来即可.
        暂时loader选择使用同步函数.
        此方法需要被覆写.
    """
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


if __name__ == "__main__":
    # test_zenrule
    # asyncio.run(test_zenrulev1_with_enginev1())
    # asyncio.run(test_zenrulev1_with_enginev2())
    asyncio.run(test_zenrule())
    # asyncio.run(test_zenrule_with_loader())
