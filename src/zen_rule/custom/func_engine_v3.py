
# 此版本用于研究 python 实现 zen expression 的解析, 进而实现python自定义函数和zen表达式的混合调用.
# 此模块处于研究状态.
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
    """
        实现自定义函数的嵌套调用.
    """
    func_value_context = {}  # ast 求值时, 函数值暂存在此字典, 用于嵌套函数传参.
    # logger.debug(f"{pformat(ast)}")
    for func in expr_ast:  # 执行一个嵌套函数表达式.
        ### 下列代码需要封装为一个执行引擎.
        logger.debug(f"current func_value_context: {func_value_context}")
        if func["ns"] == "udf":
            # logger.warning(f"udf expression: {func}")
            func_name = func["name"]
            args = FuncItem.args_eval(func["args"], func_value_context, args_input, args_expr_eval)
            kwargs = {
                **context,
                "func_id": func["id"],
            }
            result = await udf_manager(func["name"], *args, **kwargs)
            logger.warning(f"{func_name}({args}) ->: {result}")
            func_value_context[func["id"]] = result
        elif func["ns"] == "":
            func_name = func["name"]
            args = func["args"]
            # 需要判断参数是嵌套函数的情况.
            args = [func_value_context.get(func["id"]) if t == "func_value" else str(arg) for arg, t in args]
            # 要判断 args 中是否还嵌套函数.
            func_call_args = ",".join(args)
            zen_expr = f"{func_name}({func_call_args})"
            result = zen.evaluate_expression(zen_expr, args_input)
            logger.warning(f"{zen_expr} ->: {result}")
            # 默认使用 zen 表达式.
            func_value_context[func["id"]] = result
        else:
            raise RuntimeError(f'自定义函数{func["name"]}表达式不支持')

    return result


if __name__ == "__main__":
    ### 在项目根目录运行 python -m src.custom.func_engine_v3 即可测试此方法.

    # "udf:foo(udf:bar(2  , rand(100),'a'), bas())"  "udf:foo(udf:bar(rand(100), udf:zoo(3,6),'a'), udf:bas())"
    func_call_s = "udf:foo(myvar,udf:bar(rand(100), udf:zoo('fccdjny',6, 3.14),'a'), udf:bas())"
    # func_call_s = "foo(bar( 2,'a'), bas())"
    # func_call_s = "rand(100)"
    # func_call_s = "map(['a', 'b', 'c'], # + '!')"  # 增加对 ['a', 'b', 'c'] 数组类型的解析.         # 已经实现支持
    # func_call_s = "map(['a', lower('b'), 'c'], # + '!')"  # 增加对 ['a', 'b', 'c'] 数组类型的解析.  # 已经实现支持
    # func_call_s = '{customer: { firstName: "John", lastName: "Doe"}}'  # 增加对 json5 objects(结构)类型的解析. 这个表达式不是函数调用, 不会被解析.
    # func_call_s = "map([{id: 1, name: 'John'}, {id: 2, name: 'Jane'}], #.id)"  # 增加对数组和objects类型的解析.

    # # 这些语法和数组语法解析冲突, 需要在参数解析中来做分区.
    # func_call_s = "map([0..3], #)"   # 暂不支持
    # func_call_s = "map((0 .  .   3], #)"   # 暂不支持, 报错.

    ### ************************************************************************************************************
    ## 注意, zen-engine 又加入了很多新的语法, 从长远来说, 这些语法都得兼容, 否则就无法实现 python udf 和 zen 表达式函数的混合调用.
    ## 把用 python 实现 zen expression 的解析(得到 zen 表达式的抽象语法树ast)作为一个长期的目标去支持吧.
    ### ************************************************************************************************************

    expr_ast = zen_custom_expr_parse(func_call_s)
    print("expr    :", func_call_s)
    print("expr_ast:", expr_ast)
    pprint(expr_ast)
    import json
    rrr = json.dumps(expr_ast)
    print(rrr)

    res = asyncio.run(ast_exec(expr_ast, {"input": 7, "myvar": 15}))
    print("res:", res)