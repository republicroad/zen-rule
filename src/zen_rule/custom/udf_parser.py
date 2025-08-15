
import logging
import string
import uuid
from pprint import pprint
from dataclasses import dataclass, asdict, field
from pathlib import Path
import zen
logger = logging.getLogger(__name__)


def stack_token_lex(stack):
    l = []
    # logger.debug(f"lexer temp stack:{stack}")
    while(stack):
        c = stack.pop()
        l.append(c)
    l.reverse()
    token = "".join(l)
    # logger.debug(f"token: {token}")
    return token


def func_lexer(s):
    tokens = []
    _mystack = []
    stack_contains_label = lambda stack, label: "".join(stack).find(label) > -1 
    for c in s:
        if c in string.whitespace or c == '':
            continue
        if c in {","}:
            try:
                if stack_contains_label(_mystack, "("):
                    if stack_contains_label(_mystack, ")"):
                        pass
                else:
                    pass
                # _mystack.index("(")
                # _mystack.index("'")
                # _mystack.index('"')
                # 执行到此 说明逗号出现在了zen 函数中, 出现在了 字符串中.
                _mystack.append(c)  
            except Exception as e:
                print("_mystack contains non arg split comma:", _mystack)
                token = stack_token_lex(_mystack)
                if token:
                    tokens.append(token)  # funcname
                tokens.append(c)
                print("++_mystack:", _mystack)
                print("++tokens:", tokens)
        else:
            _mystack.append(c)  
        print("_mystack:", _mystack)
        print("tokens:", tokens)
    return tokens

def outer_func_lexer(expr):
    """
        考虑到函数的参数需要支持 zen 表达式的原因, 在参数解析时需要完全去解析 zen expression 的语法.
        如果未来更新 zen-engine 的版本时, 添加的新的表达式语法结构就需要跟进支持, 这一点恐怕成为一个隐患.
        因为我们希望能随时更新 zen-engine 的最新版本.
        group_distinct_1h(member_id + foo(totoal_fee, 34), ip)
        group_distinct_1h(member_id == foo(totoal_fee, 34), ip)
        group_distinct_1h(member_id ^= foo(totoal_fee, 34), ip)
        
        这样的话, 就不能实现任意嵌套函数的解析了. 否则就会出现函数参数中 zen 表达式, 解析zen表达式时需要判断 zen 中的表达式是zen中的原生函数
        还是在外部去实现的自定义函数. 遇到同名函数，就要确定哪个优先级高.
        如果是 zen 原生函数优先级高, 那么新的zen-engine的函数就可能会覆盖自定义函数实现, 如果函数同名不同义, 就会出逻辑问题.
        如果是 自定义函数优先级高, 那么同名函数在自定义节点和原来的表达式节点中的行为就会不一致, 也会影响使用者的认知.

        最佳解决方案就是像其他表达式引擎那样, zen expression 允许注册外部函数. 这样在 zen 表达式中的行为就是一致的.
        
    """
    i = expr.find("(")
    func_name = expr[:]
    expr[i:]  # 函数调用的左右小括号和参数.
    args = expr[i+1:-1]
    print("func_lexer args:", args)
    result = func_lexer(args)
    print("result:", result)


def zen_custom_expr_parse(expr):
    # expr func_call_s
    mytokens = outer_func_lexer(expr)
    logger.warning(f"func_lexer: {mytokens}")
    # expr_ast = func_ast_parser(mytokens)  # 得到了嵌套函数的求值顺序 AST.
    # return expr_ast


if __name__ == "__main__":
    ### 在项目根目录运行 python -m src.custom.func_engine_v3 即可测试此方法.

    # "udf:foo(udf:bar(2  , rand(100),'a'), bas())"  "udf:foo(udf:bar(rand(100), udf:zoo(3,6),'a'), udf:bas())"
    # func_call_s = "udf:foo(myvar,udf:bar(rand(100), udf:zoo('fccdjny',6, 3.14),'a'), udf:bas())"
    # func_call_s = "foo(bar( 2,'a'), bas())"
    # func_call_s = "rand(100)"
    # func_call_s = "map(['a', 'b', 'c'], # + '!')"  # 增加对 ['a', 'b', 'c'] 数组类型的解析.         # 已经实现支持
    func_call_s = "map(['a', lower('b'), 'c'], # + '!')"  # 增加对 ['a', 'b', 'c'] 数组类型的解析.  # 已经实现支持
    # func_call_s = '{customer: { firstName: "John", lastName: "Doe"}}'  # 增加对 json5 objects(结构)类型的解析. 这个表达式不是函数调用, 不会被解析.
    # func_call_s = "map([{id: 1, name: 'John'}, {id: 2, name: 'Jane'}], #.id)"  # 增加对数组和objects类型的解析.

    # # 这些语法和数组语法解析冲突, 需要在参数解析中来做分区.
    # func_call_s = "map([0..3], #)"   # 暂不支持
    # func_call_s = "map((0 .  .   3], #)"   # 暂不支持, 报错.

    ### ************************************************************************************************************
    ## 注意, zen-engine 又加入了很多新的语法, 从长远来说, 这些语法都得兼容, 否则就无法实现 python udf 和 zen 表达式函数的混合调用.
    ## 把用 python 实现 zen expression 的解析(得到 zen 表达式的抽象语法树ast)作为一个长期的目标去支持吧.
    ### ************************************************************************************************************

    func_call_s = 'group_distinct_1h(member_id + foo(totoal_fee, 34), ip)'
    expr_ast = zen_custom_expr_parse(func_call_s)
    print("expr    :", func_call_s)
    print("expr_ast:", expr_ast)
    # pprint(expr_ast)
    # import json
    # rrr = json.dumps(expr_ast)
    # print(rrr)