from pyparsing import Word, alphas, alphanums, Literal, Optional, delimitedList, Forward, Group
from pyparsing import QuotedString

# # Define a QuotedString instance for single quotes
# single_quoted_string = QuotedString(quoteChar="'")
# # Example usage
# text_to_parse = "This is a 'single quoted string' within some text."
# parsed_result = single_quoted_string.parseString(text_to_parse)

single_quote = "''"
double_quote = '""'
zen_key_chars = single_quote + double_quote +"+<>= ;!" 
print("zen_key_chars:", zen_key_chars)
# Define the function name as a word starting with alpha or '_'
#function_name = Word(init_chars, body_chars)
function_name = Word(alphas + "_", alphanums + "_"+ zen_key_chars)

# Define the expression for arguments within the function call.
# This can be a recursive definition to handle nested function calls or complex expressions.
# For simplicity, this example allows for basic words or nested function calls.
argument_expression = Forward()
argument_expression <<= (
    function_name + Literal("(") + Optional(delimitedList(argument_expression | Word(alphanums + "_"))) + Literal(")")
) | Word(alphanums + "_")

# Define the complete function call structure
function_call = Group(function_name + Literal("(") + Optional(delimitedList(argument_expression)) + Literal(")"))

# Example usage:
test_string_1 = "myFunction(arg1, arg2)"
test_string_2 = "anotherFunc(nested(param1), param2)"  # true and not x;  # foo(totoal_fee, 34)
func3 = 'group_distinct_1h(member_id+foo(totoal_fee, 34), ip)'

print(f"Parsing '{test_string_1}': {function_call.parseString(test_string_1)}")
print(f"Parsing '{test_string_2}': {function_call.parseString(test_string_2)}")
print(f"Parsing '{func3}': {function_call.parseString(func3)}")
