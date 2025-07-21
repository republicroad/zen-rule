
import sys
import inspect
import logging
from pprint import pformat, pprint
from zen_rule import zen_custom_expr_parse
logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)


def msg_test(*args, **kwargs):
    """
        '18271902319,15607101196,18727622961'
        '2025061611051974502'
        '二次号'
    """
    logger.info(f"{inspect.stack()[0][3]} args:{args}")
    logger.info(f"{inspect.stack()[0][3]} kwargs:{kwargs}")
    print("msg_test")
    return "msg_test"


if __name__ == "__main__":
    # 兼容字符串中包含 ARGS_SPLIT 的情况 msg_test('18271902319,15607101196,18727622961'   , '2025061611051974502', 'xxx',)
    ### sg_test('18271902319,15607101196,18727622961'   , '2025061611051974502'  , '二次号', [1,2,'3',4 ])
    ### todo: array 的类型还需要解析.
    ### todo: object 类型需要解析.
    ###  { firstName: 'John', lastName: 'Doe' }
    func_call_s = "msg_test('18271902319,15607101196,18727622961', '2025061611051974502', '二次号')"  # 增加对 ['a', 'b', 'c'] 数组类型的解析.  # 已经实现支持
    expr_ast = zen_custom_expr_parse(func_call_s)
    print("expr    :", func_call_s)
    print("expr_ast:", expr_ast)
    pprint(expr_ast)
    # import json
    # rrr = json.dumps(expr_ast)
    # print(rrr)
