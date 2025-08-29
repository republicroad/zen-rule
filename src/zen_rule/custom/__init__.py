import re


def op_args_combination(args, function_meta):
    """
        将参数值和参数名字组装为字典.
        如果没有在自定义函数中设置对应的 arg_name, 那么默认的关键字参数的下标就是以下划线加数字(如_0, _1, _2 )等开头.
    """
    arguments = [i.get("arg_name") for i in function_meta["arguments"] if i.get("arg_name") not in {"args", "kwargs"}]
    if not arguments:
        arguments = [f"_{i}" for i in range(len(args))]
    keyword_args = {arg_name: v for arg_name, v in zip(arguments, args)}
    return keyword_args


def parse_oprator_expr_v3(expr):
    """
        v3自定义节点中的算子 oprater 调用支持两种格式:
        1.  ;; 当作起始符号且作为oprater及参数的分隔符
            foo;;myvar ;;max([5,8,2,11, 7]);;rand(100)+120;;3+4;; 'singel;;quote' ;;"double;;quote" ;;`backquote;; ${bar}`

        2. 使用函数调用嵌套(todo:以后支持)
            foo(myvar,bar(zoo('fccdjny',6, 3.14),'a'), a+string(xxx))
    """
    # 不能简单使用字符串分割, 因为字符串中可能会有分隔符的模式出现, 比如:
    # foo ;; myvar ;; bar(zoo('fccd;;jny',6, 3.14),'a');; a+string(xxx)
    # foo;;myvar;;max([5, 8, 2, 11, 7]);;rand(100);; 'fccd;;jny' ;;3+4
    # expr.split(";;")
    ## todo: 是否将此模式编译
    pattern = r""";;(?=(?:[^"'`]*["'`][^"'`]*["'`])*[^"'`]*$)"""
    # To split the string by these semicolon:
    _parts = re.split(pattern, expr)
    parts = [i.strip() for i in _parts]  # 去掉表达式前后的空格
    return parts