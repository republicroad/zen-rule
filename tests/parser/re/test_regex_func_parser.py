### 注意正则表达式无法表达上下文无关文法. 所以正则表达式无法提取任意层次嵌套的函数调用.

import re

## 提取的格式不完整
# text = "my_function(arg1, arg2) another_call()"
text = 'group_distinct_1h(member_id+foo(totoal_fee, 34), ip)'
pattern = r"(\w+)\((.*?)\)"  # Captures function name and arguments
match = re.search(pattern, text)

if match:
    function_name = match.group(1)
    arguments = match.group(2)
    print(f"Function Name: {function_name}, Arguments: {arguments}")

## 无法识别函数调用之外的 infix notation(中缀表达式)
# text = "outer_func(arg1, inner_func(sub_arg))"
text = 'group_distinct_1h(member_id+foo(totoal_fee,bar(a)), ip)'
pattern = r"(\w+)\(([^()]*?(?:\(([^()]*)\))?[^()]*?)\)"

match = re.search(pattern, text)
if match:
    function_name = match.group(1)
    arguments_string = match.group(2)
    print(f"Function Name: {function_name}")
    print(f"Arguments String: {arguments_string}")