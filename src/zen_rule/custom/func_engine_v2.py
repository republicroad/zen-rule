
# func_engine 此模块要改名为 udf_engine 或者是 func_engine.
# 此模块完成函数解析
## 完成 foo(bar(2  , zoo(3,6),'a'), bas())

# https://tree-sitter.github.io/tree-sitter/using-parsers/1-getting-started.html
# https://stackoverflow.com/questions/67656240/parsing-a-function-call-using-python-regex
# https://regex101.com/r/Umsdg0/1
import asyncio
import logging
from pprint import pprint, pformat
from dataclasses import dataclass, asdict, field
from pathlib import Path
import zen
from .udf_manager import udf_manager
from .func_parser import zen_custom_expr_parse, FuncItem
logger = logging.getLogger(__name__)


args_expr_eval = lambda x, input: zen.evaluate_expression(x, input)


async def ast_exec(expr_ast, args_input, context={}):
    func_value_context = {}  # ast 求值时, 函数值暂存在此字典, 用于嵌套函数传参.
    # logger.debug(f"{pformat(expr_ast)}")
    for func in expr_ast:  # 执行一个嵌套函数表达式.
        ### 下列代码需要封装为一个执行引擎.
        logger.debug(f"current func_value_context: {func_value_context}")
        ### 目前只支持外部自定义函数调用. 不支持和 zen expression 的函数进行混合使用.
        func_name = func["name"]
        # todo: 将 udf 中定义的函数中的参数定义顺序和和当前的 args 来做字典映射. 这样可以将所有的位置参数转化为关键字参数.
        args = FuncItem.args_eval(func["args"], func_value_context, args_input, args_expr_eval)
        kwargs = {
            **context,
            "func_id": func["id"],
        }
        result = await udf_manager(func["name"], *args, **kwargs)
        logger.warning(f"{func_name}({args}) ->: {result}")
        func_value_context[func["id"]] = result

    return result


if __name__ == "__main__":
    ### 在项目根目录运行 python -m src.custom.func_engine_v2 即可测试此方法.
    # "udf:foo(udf:bar(2  , rand(100),'a'), bas())"  "udf:foo(udf:bar(rand(100), udf:zoo(3,6),'a'), udf:bas())"
    # func_call_s = "udf:foo(myvar,udf:bar(rand(100), udf:zoo('fccdjny',6, 3.14),'a'), udf:bas())"
    func_call_s = "foo(myvar,bar(zoo('fccdjny',6, 3.14),'a'), bas())"
    # func_call_s = "foo(bar( 2,'a'), bas())"

    expr_ast = zen_custom_expr_parse(func_call_s)
    print("--------------test case--------------------")
    print("expr    :", func_call_s)
    print("expr_ast:")
    pprint(expr_ast)
    import json
    rrr = json.dumps(expr_ast)
    print(rrr)

    res = asyncio.run(ast_exec(expr_ast, {"input": 7, "myvar": 15}))
    print("res:", res)