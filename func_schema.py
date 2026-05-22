
import logging
import sys
from typing import Annotated, Optional
import inspect
import asyncio
from pprint import pprint
from pathlib import Path
from zen_rule import ZenRule, udf

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@udf()
def foo(*args, **kwargs) -> str:
    """
    Docstring for UDF: foo

    :param args: Description
    :param kwargs: zen-rule 传入的节点入参和元信息, _node_input
    :returns: foo 函数返回
    :rtype: str 
    """
    logger.info("function: %s args: %s", sys._getframe(1).f_code.co_name, args)
    logger.info("function: %s kwargs: %s", sys._getframe(1).f_code.co_name, kwargs)
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

    :param c: arg c
    :type c: int
    :param b: arg b
    :type b: str
    :param a: arg a
    :type a: int
    :param z: arg z
    :type z: int
    :param args: param args
    :param kwargs: param kwargs
    :returns: bar 函数返回
    :rtype: str 
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
