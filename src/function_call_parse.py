
## 完成 foo(bar(2  , zoo(3,6),'a'), bas())

# https://tree-sitter.github.io/tree-sitter/using-parsers/1-getting-started.html
# https://stackoverflow.com/questions/67656240/parsing-a-function-call-using-python-regex
# https://regex101.com/r/Umsdg0/1
import string
from pprint import pprint
from dataclasses import dataclass, asdict


FUNC_LEFT_BOUNDRY = "("
FUNC_RIGHT_BOUNDRY = ")"
ARGS_SPLIT = ","


@dataclass
class FuncItem:
    """Function items"""
    name: str
    args: list
    namespace: list
    level: int


def stack_token_lex(stack):
    stop_chars = (FUNC_LEFT_BOUNDRY, FUNC_RIGHT_BOUNDRY, ARGS_SPLIT)
    l = []
    c = ""
    while(stack and c not in stop_chars):
        c = stack.pop()
        l.append(c)
    l.reverse()
    token = "".join(l)
    # logger.debug("token:", token)
    return token


def func_lex(s):
    tokens = []
    _mystack = []
    for c in s:
        if c in string.whitespace or c == '':
            continue
        if FUNC_LEFT_BOUNDRY == c:
            token = stack_token_lex(_mystack)
            # print(FUNC_LEFT_BOUNDRY, ":", token)
            if token:
                tokens.append(token)
            tokens.append(FUNC_LEFT_BOUNDRY)
        elif FUNC_RIGHT_BOUNDRY == c:
            # 完成右边括号匹配以后, 层级 -1.
            token = stack_token_lex(_mystack)
            if token:
                tokens.append(token)
            tokens.append(FUNC_RIGHT_BOUNDRY)
        elif ARGS_SPLIT == c: # 避免
            token = stack_token_lex(_mystack)
            if token:
                tokens.append(token)
            tokens.append(ARGS_SPLIT)
        else:
            _mystack.append(c)  
    return tokens


def parse_func_arguments(stack):
    stop_chars = (FUNC_LEFT_BOUNDRY,)
    l = []
    c = ""
    while(stack and c not in stop_chars):
        c = stack.pop()
        l.append(c)
    if stack:
        # pop function name
        l.append(stack.pop())
    l.reverse()
    # logger.debug("token:", token)
    return l


def func_ast_parser(tokens):
    res = []     # 保存解析之后的语法树
    _stack = []  # 对词法 token 进行入栈解析
    namespace = []  # 记录
    level = 0
    for token in  tokens:
        if token == FUNC_LEFT_BOUNDRY:
            # 左边界, 层级加一
            # 为了记忆这种无限层级调用关系, 所以需要一个对应的列表来记录层级, 这样也方便实现未来词法作用域.
            ns = _stack[-1]
            _stack.append(token)
            level = level + 1
            namespace.append(ns)
        elif token == FUNC_RIGHT_BOUNDRY:
            # 完成右边括号匹配以后, 完成一个无嵌套函数的调用解析. 
            # 层级 -1.
            # res = _stack and _stack.pop()
            _func_item = parse_func_arguments(_stack)
            func_name, _, *args = _func_item  # funcname ( arg1 arg2
            # item = [func_name, *args]  # 保存此列表会得到一个嵌套的列表(类似于s表达式)
            _ns = namespace.copy()
            func_item = FuncItem(name=func_name, args=args, namespace=_ns, level=level)
            res.append(asdict(func_item))
            _stack.append(asdict(func_item))  # 把嵌套函数作为上一层函数的参数放在参数位置上.
            # print("func_items _stack:", _stack)
            level = level - 1
            namespace and namespace.pop()
        elif token == ARGS_SPLIT:
            # 排除 ',' 号
            pass
        else:
            _stack.append(token)
    return res


### todo:
# 已经得到了 AST, 这个 AST 就是需要保存在zen-rule自定义节点中的一个输入中.
# 这样可以在保存规则时解析一次执行顺序，之后直接按解析的顺序去执行函数即可.
# 实现一个 AST 的执行引擎用来执行规则输入. 


if __name__ == "__main__":
    func_call_s = "foo(bar(2  , zoo(3,6),'a'), bas())"
    # func_call_s = "foo(bar( 2,'a'), bas())"
    mytokens = func_lex(func_call_s)
    res = func_ast_parser(mytokens)  # 得到了嵌套函数的求值顺序 AST.
    print("res:")
    pprint(res)
    import json
    rrr = json.dumps(res)
    print(rrr)