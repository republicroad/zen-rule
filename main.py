
import random
from pprint import pprint
from pathlib import Path
from src.udf_manager import udf_manager, udf, FuncArg, FuncValue, FuncRet


@udf()
def func1(x: list, y: dict, z,*, k=1):
    pass


@udf()
async def func2(a: str, b:int, c: Path, *args, **kwargs):
    pass


@udf()
async def func3(*args, **kwargs):
    pass


@udf(
    comments="obtain the desired time format",
    args_info=[
        FuncArg(arg_name="time_input", arg_type="string", defaults="", comments="input time"),
        FuncArg(arg_name="adjustment_str", arg_type="string", defaults="", comments="time delta example+1y-5M+30d+3h-20m"),
        FuncArg(arg_name="output_format", arg_type="string", defaults="", comments="output time format"),
    ],
    # return_info={"ipsegment": FuncValue(field_name="output_time", field_type="string", defaults="", comments="output_time")}
)
async def demofunc(*args, **kwargs):
    pass


@udf(
    comments="test udf foo",
    args_info=[
        FuncArg(arg_name="a", arg_type="string", defaults="", comments="var a"),
        FuncArg(arg_name="b", arg_type="string", defaults="", comments="var b"),
        FuncArg(arg_name="c", arg_type="string", defaults="", comments="var c"),
    ],
    return_info=FuncRet(field_type="string", examples="fccdjny", comments="返回值示例, 字段解释")     
)
def foo():
    pass


@udf(
    comments="rand(x,y) 返回[x, y]之间随机的整数",
    args_info=[
        FuncArg(arg_name="low", arg_type="number", defaults=0, comments="随机数区间下限值"),
        FuncArg(arg_name="high", arg_type="number", defaults=100, comments="随机数区间上限值"),
    ],
    return_info=FuncRet(field_type="number", examples=33, comments="返回[x, y]之间随机的整数")     
)
def rand(low: int, high: int):  # 故意和 zen expression rand函数名字一样, 演示函数的命令空间.
    return random.randint(low, high)


pprint(udf_manager.get_udf_info())


import asyncio
from src.zen_rule import zenRule

async def test_zenrule():
    zr = zenRule()
    result = await zr.async_evaluate("custom_v3.json", {"input": 7})
    print("zen rule result:", result)


if __name__ == "__main__":
    asyncio.run(test_zenrule())