# 这里主要解析函数参数的字面量. 如果函数的参数是一些变量, 这个不会影响对于函数调用的解析.

import sys
import inspect
import logging
from pprint import pformat, pprint
from zen_rule import zen_custom_expr_parse
logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)


def test_string(*args, **kwargs):
    """
        '18271902319'
        '2025061611051974502'
        '二次号'
    """
    logger.info(f"{inspect.stack()[0][3]} args:{args}")
    logger.info(f"{inspect.stack()[0][3]} kwargs:{kwargs}")
    # 兼容字符串中包含 ARGS_SPLIT 的情况 msg_test('18271902319,15607101196,18727622961'   , '2025061611051974502', 'xxx',)
    ### sg_test('18271902319,15607101196,18727622961'   , '2025061611051974502'  , '二次号', [1,2,'3',4 ])
    ### todo: object 类型需要解析.
    ###  { firstName: 'John', lastName: 'Doe' }
    func_call_s = "msg_test('18271902319', '2025061611051974502', '二次号')"  # 增加对 ['a', 'b', 'c'] 数组类型的解析.  # 已经实现支持
    expr_ast = zen_custom_expr_parse(func_call_s)
    print("expr    :", func_call_s)
    print("expr_ast:", expr_ast)
    pprint(expr_ast)


def test_string_comma(*args, **kwargs):
    """
        '18271902319,15607101196,18727622961'
        '2025061611051974502'
        '二次号'
    """
    logger.info(f"{inspect.stack()[0][3]} args:{args}")
    logger.info(f"{inspect.stack()[0][3]} kwargs:{kwargs}")
    # 兼容字符串中包含 ARGS_SPLIT 的情况 msg_test('18271902319,15607101196,18727622961'   , '2025061611051974502', 'xxx',)
    ### sg_test('18271902319,15607101196,18727622961'   , '2025061611051974502'  , '二次号', [1,2,'3',4 ])
    ### todo: object 类型需要解析.
    ###  { firstName: 'John', lastName: 'Doe' }
    func_call_s = "msg_test('18271902319,15607101196,18727622961', '2025061611051974502', '二次号')"  # 增加对 ['a', 'b', 'c'] 数组类型的解析.  # 已经实现支持
    expr_ast = zen_custom_expr_parse(func_call_s)
    print("expr    :", func_call_s)
    print("expr_ast:", expr_ast)
    pprint(expr_ast)


def test_arrary(*args, **kwargs):
    """
        test_arrary
    """
    logger.info(f"{inspect.stack()[0][3]} args:{args}")
    logger.info(f"{inspect.stack()[0][3]} kwargs:{kwargs}")
    ### todo: array 中每一个元素的类型还需要解析.
    func_call_s = "array_call([1,2,3], ['a', 'b', 'c'])"  # 增加对 ['a', 'b', 'c'] 数组类型的解析.  # 已经实现支持
    expr_ast = zen_custom_expr_parse(func_call_s)
    print("array_call expr    :", func_call_s)
    print("array_call expr_ast:", expr_ast)
    pprint(expr_ast)


def test_object(*args, **kwargs):
    """
        test_object
        object 字面量
    """
    logger.info(f"{inspect.stack()[0][3]} args:{args}")
    logger.info(f"{inspect.stack()[0][3]} kwargs:{kwargs}")
    ### todo: object 类型需要解析. object 的字面量到底是 json 字符串还是 javascript 的字面表示量.
    #  {customer: { firstName: "John", lastName: "Doe" }}
    #  { firstName: "John", lastName: "Doe" }
    func_call_s = """object_call({customer: { "firstName": "John", lastName: "Doe" }}, ['a', 'b', 'c'])"""  # 增加对 ['a', 'b', 'c'] 数组类型的解析.  # 已经实现支持
    expr_ast = zen_custom_expr_parse(func_call_s)
    print("object_call expr    :", func_call_s)
    print("object_call expr_ast:", expr_ast)
    pprint(expr_ast)


if __name__ == "__main__":
    # test_string()
    # test_string_comma()
    # test_arrary()
    test_object()