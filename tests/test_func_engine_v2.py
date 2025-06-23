
import asyncio
import sys
from pprint import pprint, pformat
pprint(sys.path)
from custom.func_engine_v2 import zen_custom_expr_parse, ast_exec


if __name__ == "__main__":
    # "udf:foo(udf:bar(2  , rand(100),'a'), bas())"  "udf:foo(udf:bar(rand(100), udf:zoo(3,6),'a'), udf:bas())"
    # func_call_s = "udf:foo(myvar,udf:bar(rand(100), udf:zoo('fccdjny',6, 3.14),'a'), udf:bas())"
    func_call_s = "foo(myvar,bar(rand(100), zoo('fccdjny',6, 3.14),'a'), bas())"
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