
import logging
import inspect
import asyncio
from pprint import pprint
from pathlib import Path
import sys
from zen_rule import ZenRule, udf

from utils import httpsession

logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)


@udf()
def foo(a:str, b:str, c:str, *args, **kwargs) -> str:
    """
    Docstring for UDF: foo

    :param a: 参数 a
    :type a: str
    :param b: 参数 b
    :type b: str
    :param c: 参数 c
    :type c: str
    :param args: Description
    :param kwargs: zen-rule 传入的节点入参和元信息, _node_input
    :returns: foo 函数返回
    :rtype: str 
    """
    logger.info("function: %s args: %s", sys._getframe(1).f_code.co_name, args)
    logger.info("function: %s kwargs: %s", sys._getframe(1).f_code.co_name, kwargs)
    return "foo value"


async def test_zenrule_foo():
    zr = ZenRule({})
    basedir = Path(__file__).parent
    filename = basedir / "graph" / "custom_fullnode.json"
    key = filename
    if not zr.get_decision_cache(key):
        with open(filename, "r", encoding="utf8") as f:
            logger.warning(f"graph json: %s", filename)
            content =  f.read()
        zr.create_decision_with_cache_key(key, content)
    for i in range(1):
        result = await zr.async_evaluate(key, {"input": 7, "myvar": 15})
        print("zen rule custom result:", result)
        assert result.get("result", {}).get("result") == "foo value", "custom 规则执行失败"
        print(f"------------------{i}------------------------")


async def test_zenrule():
    """
        推荐线上生产环境使用此模式进行规则执行, 可以缓存决策对象, 提高性能.
    """
    # httpsession.set(object())  # 先设置 contextvars 再创建包含 custom_handler 的zen engine 实例, 自定义函数可以 contextvars get.
    zr = ZenRule({})
    # httpsession.set(object())
    basedir = Path(__file__).parent
    filename = basedir / "graph" / "custom.json"  # custom2.json
    key = filename

    if not zr.get_decision_cache(key):
        # 根据实际情况去加载规则图的内容.
        with open(filename, "r", encoding="utf8") as f:
            logger.warning(f"graph json: %s", filename)
            content =  f.read()
        zr.create_decision_with_cache_key(key, content)  # 将规则图缓存在键下, 这样可以只读取规则一次，解析一次，然后复用决策对象 decision
    for i in range(1):
        result = await zr.async_evaluate(key, {"input": 7, "myvar": 15})
        print("zen rule custom result:", result)
        print(f"------------------{i}------------------------")


if __name__ == "__main__":
    # test_zenrule
    asyncio.run(test_zenrule())
    # asyncio.run(test_zenrule_foo())
