import pyparsing as pp
from pyparsing import Literal, Word, delimited_list, Group, Forward, nums, QuotedString, Optional, alphanums, alphas, identchars, Suppress

# Define basic elements
# integer = Word(nums).set_parse_action(lambda t: int(t[0]))
integer = pp.pyparsing_common.number 
string = QuotedString('"') | QuotedString("'")
identifier = Word(alphas + '_' , alphanums + '_')

strslice = Forward()
_strslice = Group(
    identifier + Literal("[") + Optional(strslice) + Literal(":") + Optional(strslice) + Literal("]")
)
strslice <<= _strslice | integer | identifier

# # Example usage
# list_string = '[1, "hello", [2, "world"], 3]'
# parsed_list = py_list.parseString(list_string)
# print(parsed_list.asList())

# Example usage
test_string = "strings[1:2]"
parsed_result = strslice.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

test_string = "strings[a:b]"
parsed_result = strslice.parseString(test_string)
print(f"{test_string} --> {parsed_result}")

test_string = "strings[a:2]"
parsed_result = strslice.parseString(test_string)
print(f"{test_string} --> {parsed_result}")


test_string = "strings[a:abc[2:2]]"
parsed_result = strslice.parseString(test_string)
print(f"{test_string} --> {parsed_result}")