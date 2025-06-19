
from pprint import pprint
from pathlib import Path
from src.udf_manager import udf_manager, udf, FuncArg, FuncValue


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
    return_info={"ipsegment": FuncValue(field_name="output_time", field_type="string", defaults="", comments="output_time")}
        
)
async def demofunc(*args, **kwargs):
    pass


@udf()
def foo():
    pass


pprint(udf_manager.get_udf_info())