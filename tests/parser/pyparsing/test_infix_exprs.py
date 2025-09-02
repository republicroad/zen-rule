# Note: In pyparsing versions 3.0.x and later, operatorPrecedence has been renamed to infixNotation (and more 
# recently infix_notation following PEP 8 naming conventions). While operatorPrecedence might still work as 
# a compatibility synonym in some older 2.x versions, it is recommended to use infixNotation or infix_notation 
# for current and future code.

import pyparsing as pp
from pyparsing import oneOf, opAssoc, infixNotation, QuotedString

def test_infix_notation():
    # Define basic elements
    number = pp.pyparsing_common.number().setName("number")
    variable = pp.Word(pp.alphas, pp.alphanums + '_')
    double_quotes = QuotedString('"', escChar='\\', unquoteResults=False)
    single_quotes = QuotedString("'", escChar='\\', unquoteResults=False)
    string = (single_quotes | double_quotes).setName("string")
    # boolean = (pp.Literal("true") | pp.Literal("false")).setName("boolean")

    atom = number | variable | string 

    # Define operator precedence
    infix_expr = pp.infixNotation(atom, [
        ('-', 1, opAssoc.RIGHT),
        ('^', 2, pp.opAssoc.RIGHT),  # Exponentiation
        (pp.oneOf('* / %'), 2, pp.opAssoc.LEFT),  # Multiplication, Division, Modulo
        (pp.oneOf('+ -'), 2, pp.opAssoc.LEFT),  # Addition, Subtraction
        (pp.oneOf('> >= < <= == !='), 2, pp.opAssoc.LEFT),  # Comparison operators
        ('not', 1, pp.opAssoc.RIGHT),  # Logical NOT
        ('and', 2, pp.opAssoc.LEFT),  # Logical AND
        ('or', 2, pp.opAssoc.LEFT),  # Logical OR
    ])

    # Example usage
    # result = expression.parseString("2 + 3 * 4")
    # print(result) # Expected: ['2', '+', ['3', '*', '4']]

    # result = expression.parseString("True and False or not True")
    # print(result) # Expected: [['True', 'and', 'False'], 'or', ['not', 'True']]
    # # Example usage
    # result = infix_expr.parse_string("2 + 3 * 4")
    # print(result.as_list())  # Output: ['2', ['3', '*', '4'], '+'] (or similar structured output)

    test_string = "1"
    parsed_result = infix_expr.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")

    test_string = "true"
    parsed_result = infix_expr.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")

    test_string = "'true'"
    parsed_result = infix_expr.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")


    test_string = "1e+3"
    parsed_result = infix_expr.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")

    test_string = "1e1 ^ 2"
    parsed_result = infix_expr.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")

    test_string = "(1e2 + 2e2) * 1e1"
    parsed_result = infix_expr.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")

    test_string = "-2 + 3 * 4 ^ 2 + (3 + 0.1) * 2"
    parsed_result = infix_expr.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")

    test_string = "-5 * -5"
    parsed_result = infix_expr.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")

    test_string = "10 % 3 != 0"
    parsed_result = infix_expr.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")

    test_string = "5^2 + 3 * 4 - 6 / 2 > 20"
    parsed_result = infix_expr.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")

    test_string = "x or not true"
    parsed_result = infix_expr.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")

    test_string = "true"
    parsed_result = infix_expr.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")

    test_string = "true and false"
    parsed_result = infix_expr.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")

    test_string = "true and (not false or variable_name)"
    parsed_result = infix_expr.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")


    ## 字符串相加
    test_string = "'a' + 'b'"
    parsed_result = infix_expr.parseString(test_string)
    print(f"{test_string} --> {parsed_result}")


if __name__ == "__main__":
    test_infix_notation()