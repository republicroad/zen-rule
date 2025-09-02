import pyparsing as pp

import pyparsing as pp
from pyparsing import Word, nums, alphanums, Literal, Suppress, Group, delimitedList, Forward, Optional
from pyparsing import infixNotation, OpAssoc, oneOf
# for recursive infix notations, or those with many precedence levels, it is best to enable packrat parsing
pp.ParserElement.enablePackrat()


def test_infix_fn_call():
    LPAREN, RPAREN = map(pp.Suppress, "()")

    arith_expr= pp.Forward()

    var_name = pp.pyparsing_common.identifier()
    integer = pp.pyparsing_common.integer()
    fn_call = pp.Group(var_name + LPAREN - pp.Group(pp.Optional(pp.delimitedList(arith_expr))) + RPAREN)
    arith_operand =  integer |fn_call| var_name

    rel_comparison_operator = pp.oneOf("< > <= >=")
    eq_comparison_operator = pp.oneOf("== !=")
    plus_minus_operator = pp.oneOf("+ -")
    mult_div_operator = pp.oneOf("* / %")
    ### **注意 表达式解析顺序.**
    ### 看样子是 arith_operand 中的 fn_call 和 var_name 的顺序会影响诸如 a + string(xxx) 的解析.
    ### 毕竟, fn_call 的定义格式中包含 var_name, 如果先解析 var_name, 将会导致无法识别 fn_call 格式.
    infix_expr = pp.infixNotation(arith_operand,
                                    [
                                        # add other operators here - in descending order of precedence
                                        # http://www.tutorialspoint.com/cprogramming/c_operators_precedence.htm
                                        (mult_div_operator, 2, pp.opAssoc.LEFT,),
                                        (plus_minus_operator, 2, pp.opAssoc.LEFT,),
                                        (rel_comparison_operator, 2, pp.opAssoc.LEFT,),
                                        (eq_comparison_operator, 2, pp.opAssoc.LEFT,),
                                    ]
                    )
    arith_expr <<= infix_expr


    test_string = "foo(bar()+fccdjny, 3)"
    parsed_result = arith_expr.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")

    test_string = "a + string(xxx)"
    parsed_result = arith_expr.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")

    test_string = "foo(33 + (a+ string(xxx)), 3)"
    parsed_result = arith_expr.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")

    print(parsed_result.dump())
    tests = """\
        cos(60)
        sqrt(1 - sin(60) * sin(60))
        """
    arith_expr.runTests(tests)

    # divmod(a, 100)
    # iif(iif(condition1,value1,value2)>iif(condition2,value1,value2),value3,value4)



def test_infix_fn_call2():
    # Example base operands
    variable = pp.pyparsing_common.identifier
    integer = pp.pyparsing_common.integer

    # Example operator precedence list
    operator_precedence = [
        (Literal('-'), 1, OpAssoc.RIGHT), # Unary minus
        (oneOf('* /'), 2, OpAssoc.LEFT),
        (oneOf('+ -'), 2, OpAssoc.LEFT),
        (Literal('and'), 2, OpAssoc.LEFT),
        (Literal('or'), 2, OpAssoc.LEFT),
    ]

    # Combine base operand and operators to create the full expression grammar
    expression = Forward() # Use Forward for recursive definitions (e.g., nested expressions)

    # Example incorporating function calls
    LPAR, RPAR = map(Suppress, "()")
    func_name = Word(alphanums + '_')
    func_call = Group(func_name("name") + LPAR + Group(Optional(delimitedList(expression)))("args") + RPAR)

    # Update the base operand to include function calls
    expression <<= infixNotation(func_call | integer | variable, operator_precedence)

    # Example usage
    test_string = "f(x*y, g(z, y))"
    parsed_result = expression.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")
    # print(parsed_result.dump())

    test_string = "10 + var * 5 - 2"
    parsed_result = expression.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")
    # print(parsed_result.dump())

    test_string = "foo(bar, 3)"
    parsed_result = expression.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")
    # print(parsed_result.dump())

    test_string = "foo(zoo(bar), 3)"
    parsed_result = expression.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")
    # print(parsed_result.dump())

    test_string = "foo(bar()+fccdjny, 3)"
    parsed_result = expression.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")
    # print(parsed_result.dump())

    # Example usage
    test_string = "func1(x + y, func2(z)) * 5"
    parsed_result = expression.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")

    # Example usage
    test_string = "z * 5"
    parsed_result = expression.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")


if __name__ == "__main__":
    test_infix_fn_call()
    test_infix_fn_call2()