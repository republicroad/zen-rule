import logging
import inspect
import sys
from .udf import udf
logger = logging.getLogger(__name__)


@udf()
def inout(b: int, a: str|int, c, *args, **kwargs) -> str:
    """
    Docstring for inout
    自定义函数测试, 返回值返回入参, 用于调试.

    :param b: 参数 b
    :type b: int
    :param a: 参数 a
    :type a: str
    :type a: int
    :param c: 参数 c
    :param args: Description
    :param kwargs: kwargs 包含 zen-rule 传入的节点入参和元信息, _node_input
    :returns: inout 函数返回
    :rtype: str 
    """
    # todo: 考虑支持复合类型 union type. 比如参数 a: str|int
    logger.info("function: %s args: %s", sys._getframe(1).f_code.co_name, args)
    logger.info("function: %s kwargs: %s", sys._getframe(1).f_code.co_name, kwargs)
    return kwargs.get("_node_input_", {})


@udf()
def func_without_args(*args, **kwargs) -> str:
    """
    Docstring for func_without_args
    无参数函数, 用于自定义函数测试
    
    :param args: Description
    :param kwargs: kwargs 包含 zen-rule 传入的节点入参和元信息, 其中 _node_input 表示此节点的所有入参. 
    :returns: func_without_args 函数返回
    :rtype: str 
    """
    logger.info("function: %s args: %s", sys._getframe(1).f_code.co_name, args)
    logger.info("function: %s kwargs: %s", sys._getframe(1).f_code.co_name, kwargs)
    return kwargs.get("_node_input_", {})