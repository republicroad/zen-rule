
import logging
import random
import asyncio
from pprint import pprint
from pathlib import Path

from zen_rule import ZenRule, ast_exec

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_ast_exec():
    v = [{"name": "zoo", "args": [["'fccdjny'", "string"], [6, "int"], [3.14, "float"]], "ns": "", "id": "566a36f923b34cbd9c159272adc988ae"}, {"name": "bar", "args": [[{"name": "zoo", "args": [["'fccdjny'", "string"], [6, "int"], [3.14, "float"]], "ns": "", "id": "566a36f923b34cbd9c159272adc988ae"}, "func_value"], ["'a'", "string"]], "ns": "", "id": "5d0b81e086d748d4902a35fd85bad974"}, {"name": "bas", "args": [], "ns": "", "id": "7f8448aad2594b479f6df2e2241707c7"}, {"name": "foo", "args": [["myvar", "var"], [{"name": "bar", "args": [[{"name": "zoo", "args": [["'fccdjny'", "string"], [6, "int"], [3.14, "float"]], "ns": "", "id": "566a36f923b34cbd9c159272adc988ae"}, "func_value"], ["'a'", "string"]], "ns": "", "id": "5d0b81e086d748d4902a35fd85bad974"}, "func_value"], [{"name": "bas", "args": [], "ns": "", "id": "7f8448aad2594b479f6df2e2241707c7"}, "func_value"]], "ns": "", "id": "0c509d4654ef443eb621d791d3ffcaa1"}]

    await ast_exec(v, {"input": 7, "myvar": 15}, {"node_id": "nodexxxxx", "meta": {}})


async def test_zenrule_loader():
    def loader(key):
        print("key:", key)
        basedir = Path(__file__).parent
        filename = basedir / "graph" / key
        with open(filename, "r", encoding="utf8") as f:
            logger.warning(f"graph json: %s", filename)
            return f.read()

    # 测试同步和异步的 loader
    zr = ZenRule({"loader": loader})
    print(zr.engine.get_decision("custom_v2.json"))
    print(zr.engine.get_decision("custom_v2.json"))
    print(zr.engine.get_decision("custom_v2.json"))
    print(zr.engine.get_decision("custom_v2.json"))


async def test_zenengine_loader():
    import inspect
    from zen import ZenEngine
    def loader(key):
        print("key:", key)
        basedir = Path(__file__).parent
        filename = basedir / "graph" / key
        with open(filename, "r", encoding="utf8") as f:
            logger.warning(f"graph json: %s", filename)
            return f.read()

    # 测试同步和异步的 loader
    ze = ZenEngine({"loader": loader})
    print(inspect.iscoroutinefunction(ze.get_decision))
    # ze.get_decision("custom_v2.json") 如果 loader 是异步函数, 此函数调用会 hang 住. 
    # 这就是为什么不建议异步 loader 函数和 get_decision
    # print(inspect.iscoroutinefunction(ze.get_decision("custom_v2.json")))
    print(ze.get_decision("custom_v2.json"))
    print(ze.get_decision("custom_v2.json"))
    print(ze.get_decision("custom_v2.json"))
    print(ze.get_decision("custom_v2.json"))

    # result = await zr.async_evaluate("custom_v2_parse.json", {"input": 7, "myvar": 15})
    # print("zen rule custom_v2 result2:", result)


if __name__ == "__main__":
    asyncio.run(test_zenengine_loader())

    # import time
    # t1 = time.time()
    # asyncio.run(test_ast_exec())
    # t2 = time.time()
    # print("delta time:", t2 - t1)