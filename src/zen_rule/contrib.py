import logging
import inspect
import sys
from .udf import udf, FuncArg
logger = logging.getLogger(__name__)


@udf(
    # todo: 等 UDFManager.get_udf_info 旧的逻辑完全被移除以后，再移除此处的参数.
    comments="default in out functions, Keep parameters unchanged output for debug",
    namespace="default",
    args_info=[
        FuncArg(arg_name="b", arg_type="string", defaults="", comments="var b"),
        FuncArg(arg_name="a", arg_type="string", defaults="", comments="var a"),
        FuncArg(arg_name="c", arg_type="string", defaults="", comments="var c"),
    ],  # todo: 以后考虑从入参定义中提取入参类型和名字, 从 Docstring 中提取参数和返回值的注释.
    return_info=None     
)
def inout(b: int, a: str|int, c, *args, **kwargs) -> str:
    """
    Docstring for inout
    自定义函数测试, 返回值返回入参, 用于调试.
    
    :param args: Description
    :param kwargs: Description
        kwargs 包含 zen-rule 传入的节点入参和元信息.
        其中 _node_input 表示此节点的所有入参.
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
    :param kwargs: Description
        kwargs 包含 zen-rule 传入的节点入参和元信息.
        其中 _node_input 表示此节点的所有入参.
    """
    logger.info("function: %s args: %s", sys._getframe(1).f_code.co_name, args)
    logger.info("function: %s kwargs: %s", sys._getframe(1).f_code.co_name, kwargs)
    return kwargs.get("_node_input_", {})