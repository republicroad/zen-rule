
# func_engine 此模块要改名为 udf_engine 或者是 func_engine.
# 此模块完成函数解析
## 完成 foo(bar(2  , zoo(3,6),'a'), bas())

# https://tree-sitter.github.io/tree-sitter/using-parsers/1-getting-started.html
# https://stackoverflow.com/questions/67656240/parsing-a-function-call-using-python-regex
# https://regex101.com/r/Umsdg0/1
import string
import uuid
from pprint import pprint
from dataclasses import dataclass, asdict, field
from pathlib import Path


FUNC_LEFT_BOUNDRY = "("
FUNC_RIGHT_BOUNDRY = ")"
ARGS_SPLIT = ","


# https://stackoverflow.com/a/75291788
# https://stackoverflow.com/a/76017464

@dataclass
class ArgItem:
    """Function Argument items"""
    name: str
    arg_type: str


@dataclass
class FuncItem:
    """Function items"""
    name: str
    args: list
    level: int  # 这些考虑作为调试信息, 是否有必要每次都展示函数嵌套层级.
    hierarchy: list

    def __post_init__(self):
        if self.name.find(":") > -1:
            self.ns, self.name = self.name.split(":")
        else:
            self.ns = ""  # self.name 保持不变
        self.hierarchy  = [i.replace("udf:", "") for i in self.hierarchy]
        self.args = self.args_type_parse(self.args)
        self.id = uuid.uuid4().hex

    def args_type_parse(self, args):
        # 对 c 进行字符串, 数字常量(int, float) 和变量的区分.
        final_args = []
        arg_types = []
        for arg in args:
            if isinstance(arg, str):
                if (arg.startswith("'") and arg.endswith("'")) or (arg.startswith('"') and arg.endswith('"')):
                    # 常量字符串
                    final_args.append(arg)
                    arg_types.append("string")
                elif arg.isdigit():
                    # 常量整型数
                    arg = int(arg)
                    final_args.append(arg)
                    arg_types.append("int")
                elif arg.find(".") > 0 and arg.replace(".", "").isdecimal():
                    # 常量浮点数
                    arg = float(arg)
                    final_args.append(arg)
                    arg_types.append("float")
                else:
                    # 变量
                    # 是否加参数的类型描述.
                    final_args.append(arg)
                    arg_types.append("var")
            else:
                final_args.append(arg)
                arg_types.append("func_value")
        l = [list(i) for i in zip(final_args, arg_types)]
        return l

    @property
    def path(self):
        return ".".join(self.hierarchy)

    def to_dict(self):
        d = {
                **asdict(self),
                **{
                    "path": self.path,
                    "ns": self.ns,
                    "id": self.id,
                    # "arg_types": self.arg_types,
                }
            }
        del d["hierarchy"]
        del d["level"]
        del d["path"]
        return d


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


def func_lexer(s):
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
    hierarchy = []  # 记录
    level = 0
    for token in  tokens:
        if token == FUNC_LEFT_BOUNDRY:
            # 左边界, 层级加一
            # 为了记忆这种无限层级调用关系, 所以需要一个对应的列表来记录层级, 这样也方便实现未来词法作用域.
            ns = _stack[-1]
            _stack.append(token)
            level = level + 1
            hierarchy.append(ns)
        elif token == FUNC_RIGHT_BOUNDRY:
            # 完成右边括号匹配以后, 完成一个无嵌套函数的调用解析. 
            # 层级 -1.
            # res = _stack and _stack.pop()
            _func_item = parse_func_arguments(_stack)
            func_name, _, *args = _func_item  # funcname ( arg1 arg2
            # item = [func_name, *args]  # 保存此列表会得到一个嵌套的列表(类似于s表达式)
            func_item = FuncItem(name=func_name, args=args, hierarchy=hierarchy.copy(), level=level)
            res.append(func_item.to_dict())
            _stack.append(func_item.to_dict())  # 把嵌套函数作为上一层函数的参数放在参数位置上.
            # print("func_items _stack:", _stack)
            level = level - 1
            hierarchy and hierarchy.pop()
        elif token == ARGS_SPLIT:
            # 排除 ',' 号
            pass
        else:
            _stack.append(token)
    return res


def ast_exec(ast):
    # 将函数执行顺序打印出来.
    for func in ast:
        pass

### todo:
# 已经得到了 AST, 这个 AST 就是需要保存在zen-rule自定义节点中的一个输入中.
# 这样可以在保存规则时解析一次执行顺序，之后直接按解析的顺序去执行函数即可.
# 实现一个 AST 的执行引擎用来执行规则输入. 

def zen_custom_expr_parse(expr):
    # expr func_call_s
    mytokens = func_lexer(expr)
    expr_ast = func_ast_parser(mytokens)  # 得到了嵌套函数的求值顺序 AST.
    return expr_ast


if __name__ == "__main__":
    # "udf:foo(udf:bar(2  , rand(100),'a'), bas())"  "udf:foo(udf:bar(rand(100), udf:zoo(3,6),'a'), udf:bas())"
    func_call_s = "udf:foo(myvar,udf:bar(rand(100), udf:zoo('fccdjny',6, 3.14),'a'), udf:bas())"
    # func_call_s = "foo(bar( 2,'a'), bas())"
    # func_call_s = "rand(100)"
    func_call_s = "map([0..3], #)"
    func_call_s = "map(['a', 'b', 'c'], # + '!')"  # 增加对 ['a', 'b', 'c'] 数组类型的解析.
    # func_call_s = '{customer: { firstName: "John", lastName: "Doe"}}'  # 增加对 json5 objects(结构)类型的解析. 这个表达式不是函数调用, 不会被解析.
    # func_call_s = "map([{id: 1, name: 'John'}, {id: 2, name: 'Jane'}], #.id)"  # 增加对数组和objects类型的解析.
    expr_ast = zen_custom_expr_parse(func_call_s)
    print("expr    :", func_call_s)
    print("expr_ast:", expr_ast)
    pprint(expr_ast)
    import json
    rrr = json.dumps(expr_ast)
    print(rrr)