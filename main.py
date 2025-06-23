
import random
from pprint import pprint
from pathlib import Path
from src.custom.udf_manager import udf_manager, udf, FuncArg, FuncValue, FuncRet


import asyncio
from src.zen_rule import ZenRule

async def test_zenrule_custom_v2():
    zr = ZenRule()
    result = await zr.async_evaluate("custom_v2.json", {"input": 7, "myvar": 15})
    print("zen rule custom_v2 result:", result)


# async def test_zenrule_custom_v3():
#     zr = zenRule()
#     result = await zr.async_evaluate("custom_v3.json", {"input": 7, "myvar": 15})
#     print("zen rule custom_v3 result:", result)


if __name__ == "__main__":
    asyncio.run(test_zenrule_custom_v2())
    # asyncio.run(test_zenrule_custom_v3())