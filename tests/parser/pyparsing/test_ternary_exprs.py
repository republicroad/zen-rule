# Ternary operator definition
# The '?' and ':' are defined as separate tokens, but they work together
# as part of a single ternary operation.
# The 3 indicates three operands.
# The OpAssoc.RIGHT is typical for ternary operators in many languages.

import pyparsing as pp

# Define basic elements
identifier = pp.pyparsing_common.identifier
integer = pp.pyparsing_common.integer
true_literal = pp.Literal("T")
false_literal = pp.Literal("F")
operand = integer | true_literal | false_literal | identifier

# Define the ternary operator using infixNotation
# The (("?", ":"), 3, pp.opAssoc.RIGHT) specifies the ternary operator
# with '?' and ':' as delimiters, 3 operands, and right-associativity.
ternary_expr = pp.infixNotation(
    operand,
    [   
        # Other operators can be defined here with their respective precedence
        # For example, binary arithmetic operators:
        # (pp.oneOf('* /'), 2, pp.OpAssoc.LEFT),
        # (pp.oneOf('+ -'), 2, pp.OpAssoc.LEFT),

        ((pp.Literal("?"), pp.Literal(":")), 3, pp.opAssoc.RIGHT),
    ]
)

# Example usage
test_string = "T ? 1 : F ? 2 : 3"
parsed_result = ternary_expr.parseString(test_string, parseAll=True)
# print(parsed_result.asList())
print(f"{test_string} --> {parsed_result}")


test_string = "T ? a : F ? 2 : 3"
parsed_result = ternary_expr.parseString(test_string, parseAll=True)
# print(parsed_result.asList())
print(f"{test_string} --> {parsed_result}")

test_string = "1 ? (2 ? 3 : 4) : 5"
parsed_result = ternary_expr.parseString(test_string)
print(f"{test_string} --> {parsed_result}")