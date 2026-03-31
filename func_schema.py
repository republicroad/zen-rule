
import logging
from typing import Annotated, Optional
import inspect
import asyncio
from pprint import pprint
from pathlib import Path
from zen_rule import ZenRule, udf, FuncArg, FuncRet

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


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


@udf()
def bar(c: int, b:Annotated[str, "Annotated tips for arg b"],
        a: int, z: int = "fccdjny", *args, **kwargs)-> int:
    """
    Docstring for bar short description only one line
    Docstring for bar long description multiple line, end by first :param line
    1
    2

    3
    
    :param a: arg a
    :type a: int
    :param b: arg b
    :param c: arg c
    :type c: int
    :param args: param args
    :param d: Description
    :type d: int
    :param kwargs: param kwargs
    """
    pass


if __name__ == "__main__":
    from pprint import pprint
    from zen_rule import ZenRule
    # from zen_rule import udf_manager
    # pprint(udf_manager.udf_function_schema_tools(), sort_dicts=False)
    # print("-------------------")
    # pprint(udf_manager.get_udf_info(), sort_dicts=False)
    pprint(ZenRule.udf_function_schema_tools(), sort_dicts=False)
