import pyparsing as pp
from pyparsing import QuotedString, Word, alphas, alphanums, nums, pyparsing_common
from pyparsing import infix_notation, OpAssoc, oneOf
from pyparsing import DelimitedList, Forward, Optional, ZeroOrMore, OneOrMore, FollowedBy
# Literal 符号出现在最后的解析中; Suppress 符号不出现在最后的解析中
from pyparsing import Literal, Suppress, Keyword
from pyparsing import Group, Dict, Combine
from pyparsing import originalTextFor, trace_parse_action, ParserElement
# 使用缓存加速递归模式的解析
ParserElement.enablePackrat()


@trace_parse_action
def parse_debug(tokens):
    """
        调试解析到的词法符号 token.
    """
    print("**debug**:", tokens)
    return tokens
    # return ''.join(sorted(set(''.join(tokens))))


def get_zen_object_array_parser(inner_func_originalText=False, debug=False, original_statment=True):
    """
        expressions to parse:
        1. {customer: { firstName: "John", lastName: "Doe" }}  已经完成.
        2. true and true                                       已经完成.
        3.  map([0..3], #);[0, 1, 2, 3]                        已经完成.
            map((0..3], #);[1, 2, 3]
            map([0..3), #);[0, 1, 2]
            map((0..3), #);[1, 2]
            user.contacts[0].phone;{"user":{"contacts":[{"phone":"123-456-7890"}]}};'123-456-7890'  已经完成.
        4. null ?? 'hello'                                        已经完成.
           null ?? null ?? 321
           user.name ?? 'Guest'
           (user.address.city) ?? 'Unknown'
        5. map([{id: 1, name: 'John'}, {id: 2, name: 'Jane'}], #.id)   已经完成. 变量 # 的处理
        6. 'Hello' + ' ' + 'World' + '!'                          已经完成.
        7. `User ${user.name} is ${user.age} years old`;{"user":{"name":"John","age":30}};'User John is 30 years old'  已经完成.
        8. boolean expr ? A : B                                   已经完成.
        9. a+string(xxxx)                                         已经完成.
        10. a.b.c.d                                               已经完成.
        11. a = 5                                                 已经完成.
        12. a=5;b=6                                               未完成解析
    """
    ast_group = originalTextFor if original_statment else Group
    # Define basic elements
    # https://github.com/pyparsing/pyparsing/wiki/Common-Pitfalls-When-Writing-Parsers#identifier--wordalphanums--_-should-be-delimitedlistwordalphas-alphanums--_--combinetrue
    _identifier = Word(alphas + '_#', alphanums + '_#').set_name("identifier")
    # identifier = Word(alphas + "_", alphanums + "_").set_name("identifier")
    identifier = DelimitedList(_identifier, ".", combine=True).set_name("qualified_identifier")

    # Define zen basic types
    double_quotes = QuotedString('"', escChar='\\', unquoteResults=False)
    single_quotes = QuotedString("'", escChar='\\', unquoteResults=False)
    backtick = QuotedString("`", escChar='\\', unquoteResults=False)
    string = (single_quotes | double_quotes | backtick).setName("string")
    number = pyparsing_common.number().setName("number")
    integer = pyparsing_common.integer
    boolean = (Literal("true") | Literal("false")).setName("boolean")
    null = Literal("null").setName("null")
    # Define zen array and object structures
    lbracket, rbracket, lbrace, rbrace, colon, comma = map(Suppress, "[]{}:,")

    zen_value = Forward().setName("zen_value")
    obejct_member = Group((string | identifier) + colon + zen_value).setName("obejct_member")
    zen_object = Dict((lbrace + Optional(DelimitedList(obejct_member)) + rbrace).setName("zen_object"))  # Dict
    zen_array = Group(lbracket + Optional(DelimitedList(zen_value)) + rbracket).setName("zen_array")

    # functions define
    lparen, rparen = Suppress('('), Suppress(')')  # 符号出现在最后的解析中 # lparen, rparen = Suppress('('), Suppress(')')  # 符号不出现在最后的解析中
    args = DelimitedList(ast_group(zen_value))
    function_call = Group(identifier('function_name') + lparen + Optional(args) + rparen)

    ### todo: 还需要解析这种表达式: a=5;b=6 
    assignmentExpr = originalTextFor(identifier.setResultsName("lhs") + Literal("=") + (zen_value).setResultsName("rhs"))

    _range_index_number = Combine(Word(nums) + Optional('.' + Word(nums)) + Optional('e' + Word(nums)))
    # number 这个python 内置的数字表示串会和 .. 冲突, 所以手动指定此处的数字字面量解析
    _range_start_index = (_range_index_number | function_call | identifier).setResultsName("range_start")
    _range_end_index   = (_range_index_number | function_call | identifier).setResultsName("range_end")
    range_expr = originalTextFor(
        Optional((number | function_call | identifier) + Optional(Literal("not")) + Literal("in")) +
        (Literal("[") | Literal("(")) +
        (_range_start_index)  +  
        Literal("..") +
        (_range_end_index) +
        (Literal("]") | Literal(")"))
    )

    atom = range_expr | number | string | boolean | null | function_call | identifier | range_expr
    # Define operator precedence
    _infix_expr = infix_notation(atom, [
        ('-', 1, OpAssoc.RIGHT),
        ('^', 2, OpAssoc.RIGHT),  # Exponentiation
        (oneOf('* / %'), 2, OpAssoc.LEFT),  # Multiplication, Division, Modulo
        (oneOf('+ -'), 2, OpAssoc.LEFT),  # Addition, Subtraction
        (oneOf('> >= < <= == !='), 2, OpAssoc.LEFT),  # Comparison operators
        ('not', 1, OpAssoc.RIGHT),  # Logical NOT
        ('and', 2, OpAssoc.LEFT),  # Logical AND
        ('or', 2, OpAssoc.LEFT),  # Logical OR
        ('??', 2, OpAssoc.LEFT),
        # Define the ternary operator using infix_notation
        # The (("?", ":"), 3, OpAssoc.RIGHT) specifies the ternary operator
        # with '?' and ':' as delimiters, 3 operands, and right-associativity.
        ((Literal("?") , Literal(":")), 3, OpAssoc.RIGHT),
    ])
    infix_expr = ast_group(_infix_expr)

    _slice_index_atom = infix_expr | integer
    _index_expr_ = originalTextFor(
        Suppress("[") + _slice_index_atom + Suppress("]")
    ).setResultsName("index")
    _slice_expr_ = originalTextFor(
        Suppress("[") + Optional(_slice_index_atom) + Literal(":") + Optional(_slice_index_atom) + Suppress("]")
    ).setResultsName("slice")
    ### ^ 代表或, 选择最长的模式去匹配解析
    index_slice_expr = _index_expr_ ^ _slice_expr_

    slice_or_index = originalTextFor(
            (infix_expr | zen_array | string) +  # ## 注意, + 优先级高于 |
            ZeroOrMore(index_slice_expr) + 
            ZeroOrMore(Literal(".") + identifier + ZeroOrMore(index_slice_expr)))
 
    # Define the recursive nature of zen_value
    ### 注意, 需要考虑表达式的顺序,  ^ 代表或, 选择最长的模式去匹配解析, | 表示优先匹配选择, 左边的先匹配.
    # https://github.com/pyparsing/pyparsing/wiki/FAQ---Frequently-Asked-Questions#what-is-the-difference-between-or-and-matchfirst
    zen_value <<= ((function_call ^ infix_expr ^ slice_or_index ^ assignmentExpr) | zen_array | zen_object)  
    # zen_value <<= infix_expr  # 只调试中缀表达式

    # Define the top-level zen parser
    zent_parser = zen_value.setName("zent_parser")
    if debug:
        zent_parser.setDebug()
        zent_parser.set_parse_action(parse_debug)
    return zent_parser

zent_parser = get_zen_object_array_parser(original_statment=True, debug=False)


### v3 格式调用
test_string = "foo(myvar,bar(zoo('fccdjny',6, 3.14),'a'), a+string(xxx))" 
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")


test_string = "rand(100) >= 0 and rand(100) <= 100" 
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")


test_string = "a=3" 
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

# test_string = "a=3;b=4"  # 暂不支持此解析
# parsed_result = zent_parser.parseString(test_string)
# print(f"{test_string} --> {parsed_result}")

# test_string = "map([0..3], #)"
# parsed_result = zent_parser.parseString(test_string)
# print(f"{test_string} --> {parsed_result}")

# test_string = "3 in (0..5]"
# parsed_result = zent_parser.parseString(test_string)
# print(f"{test_string} --> {parsed_result}")

# test_string = "3 in (2.2..5]"
# parsed_result = zent_parser.parseString(test_string)
# print(f"{test_string} --> {parsed_result}")

# test_string = "3 in (1e1..1e2]"
# parsed_result = zent_parser.parseString(test_string)
# print(f"{test_string} --> {parsed_result}")

# test_string = "3 not in (0..7]"
# parsed_result = zent_parser.parseString(test_string)
# print(f"{test_string} --> {parsed_result}")

# test_string = "3 in (aaa..3]"
# parsed_result = zent_parser.parseString(test_string)
# print(f"{test_string} --> {parsed_result}")

# test_string = "abs(3) in (abs(-1)..3]"
# parsed_result = zent_parser.parseString(test_string)
# print(f"{test_string} --> {parsed_result}")

# test_string = "5 in [1e0..abs(-5)] and abc"
# parsed_result = zent_parser.parseString(test_string)
# print(f"{test_string} --> {parsed_result}")


# test_string = "score > 70 ? 'Pass' : 'Fail'"
# parsed_result = zent_parser.parseString(test_string)
# print(f"{test_string} --> {parsed_result}")


# test_string = "score > 90 ? 'A' : score > 80 ? 'B' : score > 70 ? 'C' : 'D'"
# parsed_result = zent_parser.parseString(test_string)
# print(f"{test_string} --> {parsed_result}")


# test_string = "null ?? 123 ?? 321"
# parsed_result = zent_parser.parseString(test_string)
# print(f"{test_string} --> {parsed_result}")

# test_string = "(user.address.city) ?? 'Unknown'"
# parsed_result = zent_parser.parseString(test_string)
# print(f"{test_string} --> {parsed_result}")


# test_string = "a ? b ?? 'bbb' :2 + 3"
# parsed_result = zent_parser.parseString(test_string)
# print(f"{test_string} --> {parsed_result}")


# test_string = "`User ${user.name} is ${user.age} years old`"
# parsed_result = zent_parser.parseString(test_string)
# print(f"{test_string} --> {parsed_result}")

# test_string = "a!=null"
# parsed_result = zent_parser.parseString(test_string)
# print(f"{test_string} --> {parsed_result}")

# test_string = "a==3"
# parsed_result = zent_parser.parseString(test_string)
# print(f"{test_string} --> {parsed_result}")

test_string = "user[0].contacts[a:].phone"  # todo: 目前这个还不支持.
# test_string = "user.contacts[1].phone[0].info[0]"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

test_string = "user[:].contacts[0].phone"  # todo: 目前这个还不支持.
# test_string = "user.contacts[1].phone[0].info[0]"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")


test_string = "user.contacts[0][0].phone"  # todo: 目前这个还不支持.
# test_string = "user.contacts[1].phone[0].info[0]"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

test_string = "user.contacts[0:][1].phone"  # todo: 目前这个还不支持.
# test_string = "user.contacts[1].phone[0].info[0]"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

test_string = "user.contacts[0][:1].phone"  # todo: 目前这个还不支持.
# test_string = "user.contacts[1].phone[0].info[0]"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

test_string = "user.contacts[1].phone.info"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")


# 这个语义不存在, 但是可以解析. zen 表达式目前支持数组的切片, 不支持字符串切片.
test_string = "'user'[0].contacts[a:].phone" 
# test_string = "user.contacts[1].phone[0].info[0]"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

test_string = "[0,1,2,3,4,5][0].contacts[a:].phone" 
# test_string = "user.contacts[1].phone[0].info[0]"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

test_string = "map([0..5], #)[0].contacts[a:].phone" 
# test_string = "user.contacts[1].phone[0].info[0]"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")


## 字面量 数组切片
test_string = "[1,2,3,4,5]   [1:3]"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

# ## 字面量 字符串切片
# # test_string = "'fccdjny'[1:2]"  # 其实这个 zen expression 不支持字符串的字面量字符串切片
# # parsed_result = zent_parser.parseString(test_string)
# # print(f"{test_string} --> {parsed_result}")

## 变量下标访问(变量只支持数组和字符串), 数组支持下标访问, 字符串不支持下标访问，只能用 str[m:n] 来切片
test_string = "my_list   [1]"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

test_string = "a.b.my_list[1]"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

## 变量切片(变量只支持数组和字符串)
test_string = "another_list[1:5]"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

test_string = "some_list[2:]"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

test_string = "data[:7]"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

## 变量下标访问(下标支持函数)
test_string = "my_list[abs(-1)]"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

test_string = "my_list[abs(-1):abs(3)]"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

test_string = "map([{id: 1, name: 'John'}, {id: 2, name: 'Jane'}], #.id)"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

test_string = "a.b.c.d"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

test_string = "outer_func(234)"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

test_string = "outer_func(foo(bar), 234)"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

test_string = "outer_func(abc, 'arg1')"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

test_string = "another_func(x) * (y + 2)"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

test_string = "outer_func(abc, 'arg1', nested_func(foo(sub_arg), 'dddd'), 42, a.b)"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

test_string = "outer_func(a+b, 234)"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

test_string = "outer_func(a + string(xxx))"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

test_string = "a+b"
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

# # Example usage
# test_string = "outer_func(abc, 'arg1', nested_func(foo(sub_arg), 'dddd'), 42, a.b, [1,[2,3,5], b], {'firstName': 'John', 'lastName': Doe})"
# # test_string = "outer_func('arg1', nested_func(foo(sub_arg), 'dddd'), 42, a.b, [1, b], a+string(xxx)," \
# # "true and true,sum(values({a: 1, b: 2, c: 3})))"
# parsed_result = zent_parser.parseString(test_string)
# # print(parsed_result.dump())
# print(f"{test_string} --> {parsed_result}")
# # print(parsed_result[0][-1])

# test_string = "outer_func(a+string(xxx), 234)"
# parsed_result = zent_parser.parseString(test_string)
# print(f"{test_string} --> {parsed_result}")

# test_string = "[1,[2,3,5], b]"
# parsed_result = zent_parser.parseString(test_string)
# print(f"{test_string} --> {parsed_result}")



###----------------


# test_string = "{'firstName': 'John', 'lastName': Doe}"
# parsed_result = zent_parser.parseString(test_string)
# print(f"{test_string} --> {parsed_result}")

# test_string = "{firstName: 'John', lastName: Doe}"
# parsed_result = zent_parser.parseString(test_string)
# print(f"{test_string} --> {parsed_result}")


# test_string = "myFunction([1,2], arg1, 'a string', 123, foo(bar), abc)"
# # test_string = "myFunction(arg1, 'a string', 123, foo(bar))"
# test_string = "string[0:5]"
# parsed_result = zent_parser.parseString(test_string)
# print(f"{test_string} --> {parsed_result}")

# test_string = 'group_distinct_1h(member_id + foo(totoal_fee, "34,a,b"), ip)'
# parsed_result = zent_parser.parseString(test_string)
# print(f"{test_string} --> {parsed_result}")

test_string = 'group_distinct_1h(member_id + foo(totoal_fee, "34,a,b"), ip)'
parsed_result = zent_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")