import pyparsing as pp

def get_json_parser():
    # Define JSON basic types
    string = pp.QuotedString('"', escChar='\\').setName("string")
    number = pp.pyparsing_common.number().setName("number")
    boolean = (pp.Literal("true") | pp.Literal("false")).setName("boolean")
    null = pp.Literal("null").setName("null")

    # Define JSON array and object structures
    lbracket, rbracket, lbrace, rbrace, colon, comma = map(pp.Suppress, "[]{}:,")

    json_value = pp.Forward().setName("json_value")
    json_member = pp.Group(string + colon + json_value).setName("json_member")
    json_object = pp.Group(pp.Dict(lbrace + pp.Optional(pp.delimitedList(json_member)) + rbrace).setName("json_object"))
    json_array = pp.Group(lbracket + pp.Optional(pp.delimitedList(json_value)) + rbracket).setName("json_array")

    # Define the recursive nature of json_value
    json_value <<= (string | number | boolean | null | json_array | json_object)

    # Define the top-level JSON parser
    json_parser = json_value.setName("json_parser")
    return json_parser


json_parser = get_json_parser()

test_string = '{"name": "Alice", "age": 30, "isStudent": false, "courses": ["Math", "Science"], "address": null}'
parsed_result = json_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")


test_string = '[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]'
parsed_result = json_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")


test_string = "{'name': 'Alice', 'age': 30}"
parsed_result = json_parser.parseString(test_string)
print(f"{test_string} --> {parsed_result}")