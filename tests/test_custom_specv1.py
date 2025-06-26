
import random
import asyncio
from pprint import pprint
from pathlib import Path
from zen_rule import ZenRule


async def test_zenrule_custom_v1():
    zr = ZenRule()
    result = await zr.async_evaluate("custom_v1.json", {"ip": "1.2.3.4", "user": "1770711xxxx"})
    print("zen rule custom_v2 result:", result)


if __name__ == "__main__":
    asyncio.run(test_zenrule_custom_v1())
