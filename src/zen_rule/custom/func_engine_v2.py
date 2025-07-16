
# func_engine 此模块要改名为 udf_engine 或者是 func_engine.
# 此模块完成函数解析
## 完成 foo(bar(2  , zoo(3,6),'a'), bas())

# https://tree-sitter.github.io/tree-sitter/using-parsers/1-getting-started.html
# https://stackoverflow.com/questions/67656240/parsing-a-function-call-using-python-regex
# https://regex101.com/r/Umsdg0/1
import asyncio
import logging
from pprint import pprint, pformat
from pathlib import Path
import zen
from .udf_manager import udf_manager
from .func_parser import zen_custom_expr_parse, FuncItem
logger = logging.getLogger(__name__)


args_expr_eval = lambda x, input: zen.evaluate_expression(x, input)


async def ast_exec(expr_item, args_input, context={}): 
    func_value_context = {}  # ast 求值时, 函数值暂存在此字典, 用于嵌套函数传参.
    # logger.debug(f"{pformat(expr_ast)}")
    expr_id = expr_item["id"]
    expr_ast = expr_item["value"]
    for func in expr_ast:  # 执行一个嵌套函数表达式.
        logger.debug(f"current func_value_context: {func_value_context}")
        ### 目前只支持外部自定义函数调用. 不支持和 zen expression 的函数进行混合使用.
        func_name = func["name"]
        args = FuncItem.args_eval(func["args"], func_value_context, args_input, args_expr_eval)
        f = udf_manager.udf_info(func["name"])
        # 结合函数的装饰器中的参数描述, 将参数转化为关键字参数.
        _kwargs = FuncItem.args_map(args, f)
        logger.debug(f"ast_exec {func_name} args: {args}")
        logger.debug(f"ast_exec {func_name} kwargs: {_kwargs}")
        kwargs = {
            **_kwargs,
            **context,
            "func_id": expr_id,
            "expr_id": expr_id,
        }
        result = await udf_manager(func["name"], *args, **kwargs)
        logger.debug(f"{func_name} calling ->: {result}")
        func_value_context[expr_id] = result

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