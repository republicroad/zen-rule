
# 此版本用于研究 python 实现 zen expression 的解析, 进而实现python自定义函数和zen表达式的混合调用.
# 此模块处于研究状态.
# func_engine 此模块要改名为 udf_engine 或者是 func_engine.
# 此模块完成函数解析
## 完成 foo(bar(2  , zoo(3,6),'a'), bas())

# https://tree-sitter.github.io/tree-sitter/using-parsers/1-getting-started.html
# https://stackoverflow.com/questions/67656240/parsing-a-function-call-using-python-regex
# https://regex101.com/r/Umsdg0/1
import logging
import string
import uuid
from pprint import pprint
from dataclasses import dataclass, asdict, field
from pathlib import Path
import zen
from .udf_manager import udf_manager
logger = logging.getLogger(__name__)


FUNC_LEFT_BOUNDRY = "("
FUNC_RIGHT_BOUNDRY = ")"
ARGS_SPLIT = ","

# dataclass
# https://stackoverflow.com/a/75291788
# https://stackoverflow.com/a/76017464


# Types
# type('hello');;'string'
# type(123);;'number'
# type(true);;'bool'
# type(null);;'null'
# type([1, 2, 3]);;'array'
# type({customer: { firstName: "John", lastName: "Doe" }});;'object'
#
# In [143]: zen.evaluate_expression('type({customer: { firstName: "John", lastName: "Doe" }})', {})
# Out[143]: 'object'


@dataclass
class StringT:
    """
        zen expression string type
        type('hello');;'string'   
    """
    name: str
    token_type: str = "string"
    stop_word = {"'", '"'}


@dataclass
class NumberT:
    """
        zen expression number type
        type(123);;'number'
    """
    name: str
    token_type: str = "number"


@dataclass
class BoolT:
    """
        zen expression bool type
        type(true);;'bool'
    """
    name: str
    token_type: str = "bool"


@dataclass
class NullT:
    """
        zen expression null type
        type(null);;'null'
    """
    name: str
    token_type: str = "null"


@dataclass
class ArrayT:
    """
        zen expression array type
        type([1, 2, 3]);;'array'
    """
    name: str
    token_type: str = "array"
    Array_LEFT : str = "["
    Array_RIGHT: str = "]"

    @classmethod
    def predict(cls, c):
        return c in {cls.Array_LEFT, cls.Array_RIGHT}

    # @classmethod
    # def stack_token_lex(cls, stack):
    #     stop_chars = {"[", "]"}
    #     l = []
    #     c = ""
    #     while(stack and c not in stop_chars):
    #         c = stack.pop()
    #         l.append(c)
    #     l.reverse()
    #     token = "".join(l)
    #     logger.warning(f"token:{token}")
    #     return token

    @classmethod
    def parse_array_ast(cls, stack):
        # stop_chars = {cls.Array_LEFT}
        l = []
        token = ""
        logger.warning(f"before parse_array_ast stack:{stack}")
        while(stack):
            token = stack.pop()
            if isinstance(token, str) and token == cls.Array_LEFT:
                break
            else:
                l.append(token)
        l.reverse()
        logger.warning(f"after  parse_array_ast stack:{stack}, \n array:{l}")
        return l


@dataclass
class ObjectT:
    """
        zen expression object type
        type({customer: { firstName: "John", lastName: "Doe" }});;'object'
    """
    name: str
    token_type: str = "object"
    Object_LEFT : str = "{"
    Object_RIGHT: str = "}"

    @classmethod
    def predict(cls, c):
        return c in {cls.Object_LEFT, cls.Object_RIGHT}


@dataclass
class FuncT:
    """
        zen expression object type
        map(['a', 'b', 'c'], # + '!')
    """
    name: str
    token_type: str = "function"
    Func_LEFT : str = "("
    Func_RIGHT: str = ")"


    @classmethod
    def predict_func_call(cls, c):
        return c in {"(", ")"}

    @classmethod
    def predict_func_define(cls, c):
        pass
        # return c in {"{", "}"}


@dataclass
class FuncItem:
    """Function items"""
    name: str
    args: list
    level: int  # 这些考虑作为调试信息, 是否有必要每次都展示函数嵌套层级.
    hierarchy: list
    # prefix: str = "udf:"


    def __post_init__(self):
        if self.name.find(":") > -1:
            self.ns, self.name = self.name.split(":")
        else:
            self.ns = ""  # self.name 保持不变
        self.hierarchy  = [i.replace("udf:", "") for i in self.hierarchy]
        self.args = self.args_parse(self.args)
        self.id = uuid.uuid4().hex

    def args_parse(self, args):
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
                elif arg.startswith("#"):  # 需要补充 zen 的基础类型.
                    final_args.append(arg)
                    arg_types.append("func_closure")
                else:
                    # 变量
                    # 是否加参数的类型描述.
                    final_args.append(arg)
                    arg_types.append("var")
            elif isinstance(arg, list):
                final_args.append(arg)
                arg_types.append("array")                
            else:
                final_args.append(arg)
                arg_types.append("func_value")
        l = [list(i) for i in zip(final_args, arg_types)]
        return l

    @classmethod
    def args_eval(cls, func_args, func_value_context, args_input, args_expr_eval):
        """
            args_parse 和 args_eval中所有的类型都要匹配, 这样才能实现所有参数类型都能解析执行.
        """
        args = []
        # for arg, t in func["args"]:
        for arg, t in func_args:
            # 这里的参数类型枚举需要在解析时定义和映射. 然后在导入其他地方使用.
            if t == "func_value":
                args.append(func_value_context.get(arg["id"]))
            elif t == "var":
                args.append(args_expr_eval(arg, args_input))
            elif t == "string":
                args.append(args_expr_eval(arg, args_input))
            else:  # ["int", "float"]
                args.append(arg)
        return args

    @classmethod
    def args_map(cls, args, function_meta):
        """
            将参数值和参数名字组装为字典.
            如果没有在自定义函数中设置对应的 arg_name, 那么默认的关键字参数的下标就是以下划线加数字(如_0, _1, _2 )等开头.
        """
        arguments = [i.get("arg_name") for i in function_meta["arguments"] if i.get("arg_name") not in {"args", "kwargs"}]
        if not arguments:
            arguments = [f"_{i}" for i in range(len(args))]
        keyword_args = {arg_name: v for arg_name, v in zip(arguments, args)}
        return keyword_args

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
    # stop chars 并没有传入.
    # stop_chars = {FUNC_LEFT_BOUNDRY, FUNC_RIGHT_BOUNDRY, ARGS_SPLIT, ArrayT.Array_LEFT, ArrayT.Array_RIGHT}
    # stop_chars = {}
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
        elif ArrayT.predict(c):
            # 这里的写法可以优化, append boudry char 是否可以放在 stack_token_lex 中完成.
            if c == ArrayT.Array_LEFT:
                token = stack_token_lex(_mystack)
                if token:
                    tokens.append(token)
                tokens.append(ArrayT.Array_LEFT)
            else: # ]
                token = stack_token_lex(_mystack)
                if token:
                    tokens.append(token)
                tokens.append(ArrayT.Array_RIGHT)
        elif ObjectT.predict(c):
            if c == ObjectT.Object_LEFT:
                token = stack_token_lex(_mystack)
                if token:
                    tokens.append(token)
                tokens.append(ObjectT.Object_LEFT)
            else: # ]
                token = stack_token_lex(_mystack)
                if token:
                    tokens.append(token)
                tokens.append(ObjectT.Object_RIGHT)
        else:
            _mystack.append(c)  
    return tokens


def parse_func_arguments(stack):
    stop_chars = (FUNC_LEFT_BOUNDRY,)
    l = []
    token = ""
    while(stack and token not in stop_chars):
        token = stack.pop()
        l.append(token)
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
        elif ArrayT.predict(token):
            if token == ArrayT.Array_LEFT:
                _stack.append(token)
            else:
                # ArrayT.Array_RIGHT
                # 出栈 匹配 ArrayT.Array_LEFT [ 即可.
                logger.warning(f'Array match:{_stack}')
                array_item = ArrayT.parse_array_ast(_stack)
                _stack.append(array_item)
        else:
            _stack.append(token)
    return res


def zen_custom_expr_parse(expr):
    # expr func_call_s
    mytokens = func_lexer(expr)
    logger.warning(f"func_lexer: {mytokens}")
    expr_ast = func_ast_parser(mytokens)  # 得到了嵌套函数的求值顺序 AST.
    return expr_ast


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

    expr_ast = zen_custom_expr_parse(func_call_s)
    print("expr    :", func_call_s)
    print("expr_ast:", expr_ast)
    pprint(expr_ast)
    import json
    rrr = json.dumps(expr_ast)
    print(rrr)