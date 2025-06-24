
import logging
import random
from pprint import pprint
from pathlib import Path
from src.custom.udf_manager import udf_manager, udf, FuncArg, FuncValue, FuncRet

logging.basicConfig(level=logging.DEBUG)


import asyncio
from src.zen_rule import ZenRule, ast_exec

async def test_zenrule_custom_v2():
    zr = ZenRule()
    print(zr.engine.get_decision("custom_v2.json"))
    print(zr.engine.get_decision("custom_v2.json"))
    print(zr.engine.get_decision("custom_v2.json"))
    print(zr.engine.get_decision("custom_v2.json"))
    print("-----------------------------------------------")

    result = await zr.async_evaluate("custom_v2.json", {"input": 7, "myvar": 15})
    print("zen rule custom_v2 result:", result)
    import time
    time.sleep(1)
    result = await zr.async_evaluate("custom_v2.json", {"input": 7, "myvar": 15})
    print("zen rule custom_v2 result2:", result)

    result = await zr.async_evaluate("custom_v2_parse.json", {"input": 7, "myvar": 15})
    print("zen rule custom_v2 result2:", result)


    # result = await zr.async_evaluate("custom_v2_parse.json", {"input": 7, "myvar": 15})
    # print("zen rule custom_v2 result2:", result)

# async def test_zenrule_custom_v3():
#     zr = zenRule()
#     result = await zr.async_evaluate("custom_v3.json", {"input": 7, "myvar": 15})
#     print("zen rule custom_v3 result:", result)

async def test_ast_exec():
    v = [{"name": "zoo", "args": [["'fccdjny'", "string"], [6, "int"], [3.14, "float"]], "ns": "", "id": "566a36f923b34cbd9c159272adc988ae"}, {"name": "bar", "args": [[{"name": "zoo", "args": [["'fccdjny'", "string"], [6, "int"], [3.14, "float"]], "ns": "", "id": "566a36f923b34cbd9c159272adc988ae"}, "func_value"], ["'a'", "string"]], "ns": "", "id": "5d0b81e086d748d4902a35fd85bad974"}, {"name": "bas", "args": [], "ns": "", "id": "7f8448aad2594b479f6df2e2241707c7"}, {"name": "foo", "args": [["myvar", "var"], [{"name": "bar", "args": [[{"name": "zoo", "args": [["'fccdjny'", "string"], [6, "int"], [3.14, "float"]], "ns": "", "id": "566a36f923b34cbd9c159272adc988ae"}, "func_value"], ["'a'", "string"]], "ns": "", "id": "5d0b81e086d748d4902a35fd85bad974"}, "func_value"], [{"name": "bas", "args": [], "ns": "", "id": "7f8448aad2594b479f6df2e2241707c7"}, "func_value"]], "ns": "", "id": "0c509d4654ef443eb621d791d3ffcaa1"}]

    await ast_exec(v, {"input": 7, "myvar": 15}, {"node_id": "nodexxxxx", "meta": {}})


if __name__ == "__main__":
    asyncio.run(test_zenrule_custom_v2())
    # asyncio.run(test_zenrule_custom_v3())

    # import time
    # t1 = time.time()
    # asyncio.run(test_ast_exec())
    # t2 = time.time()
    # print("delta time:", t2 - t1)