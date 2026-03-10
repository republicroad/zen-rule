import zen
import pytest
import warnings
warnings.warn("This test is deprecated and will be removed in the future.", DeprecationWarning)
## 未来再合并到 zen 表达式的测试用例中
def test_zen_exprs():
    """
        @Deprecated: 此测试用例是想把 zen 表达式用 python 来解析.
        但是 zen 表达式没有明确的语法格式定义. 而且未来变动比较大.
        需要case by case去支持. 还不如直接在 zen-expression 的 rust 程序中去支持拓展.
    """
    assert zen.evaluate_expression("{a:1}", {"a":3, "b":"fccdjny", "c": {'name': 'Alice', 'age': 30}})
    assert zen.evaluate_expression("{'a':1}", {"a":3, "b":"fccdjny", "c": {'name': 'Alice', 'age': 30}})
    assert zen.evaluate_expression('{"a":1}', {"a":3, "b":"fccdjny", "c": {'name': 'Alice', 'age': 30}})

    ## 注意, zen context 的键值对中的键是字符串，这个字符串可以用单引号，双引号，也可以不用引号(像一个变量一样)
    assert zen.evaluate_expression('{ firstName: "John", lastName: last }',  {"firstName":"fff", "lastName": "lll", "last":"fccdjny"}) == {'lastName': 'fccdjny', 'firstName': 'John'}
    assert zen.evaluate_expression("{ 'firstName': 'John', lastName: last }",  {"firstName":"fff", "lastName": "lll", "last":"fccdjny"}) == {'lastName': 'fccdjny', 'firstName': 'John'}
    assert zen.evaluate_expression('{ "firstName": "John", lastName: last }',  {"firstName":"fff", "lastName": "lll", "last":"fccdjny"}) == {'lastName': 'fccdjny', 'firstName': 'John'}
    assert set(zen.evaluate_expression('values({ firstName: "John", lastName: last })',  {"firstName":"fff", "lastName": "lll", "last":"fccdjny"})) == set(['fccdjny', 'John'])
    assert set(zen.evaluate_expression('keys({ firstName: "John", lastName: last })',  {"firstName":"fff", "lastName": "lll", "last":"fccdjny"})) == set(['lastName', 'firstName'])
    ## 测试 zen 表达式 变量数组 下标访问   支持
    assert zen.evaluate_expression('a[1]', {"a": [1,2,3,4,5],"b":"fccdjny"}) == 2
    ## 测试 zen 表达式 变量数组 切片   支持
    assert zen.evaluate_expression('a[1:]', {"a": [1,2,3,4,5],"b":"fccdjny"}) == [2,3,4,5]
    assert zen.evaluate_expression('a[1:2]', {"a": [1,2,3,4,5],"b":"fccdjny"}) == [2,3]

    ## 测试 zen 表达式 变量字符串 下标访问  不支持  结果为None
    assert zen.evaluate_expression('b[1]', {"a": [1,2,3,4,5],"b":"fccdjny"}) is None

    ## 测试 zen 表达式 变量字符串 切片  支持
    assert zen.evaluate_expression('b[0:0]', {"a": [1,2,3,4,5],"b":"fccdjny"}) == "f"
    assert zen.evaluate_expression('b[1:]', {"a": [1,2,3,4,5],"b":"fccdjny"}) == "ccdjny"
    assert zen.evaluate_expression('b[1:2]', {"a": [1,2,3,4,5],"b":"fccdjny"}) == "cc"

    ## 测试 zen 表达式 常量数组 切片    支持
    assert zen.evaluate_expression('[1,2,3,4,5][1]', {"a": [1,2,3,4,5],"b":"fccdjny"}) == 2
    assert zen.evaluate_expression('[1,2,3,4,5][1:]', {"a": [1,2,3,4,5],"b":"fccdjny"}) == [2,3,4,5]
    assert zen.evaluate_expression('[1,2,3,4,5][1:2]', {"a": [1,2,3,4,5],"b":"fccdjny"}) == [2,3]

    ## 测试 zen 表达式 常量字符串 切片  不支持
    with pytest.raises(RuntimeError, match="parserError"):
        assert zen.evaluate_expression('"fccdjny"[1]', {"a": [1,2,3,4,5],"b":"fccdjny"}) == 'c' 
    with pytest.raises(RuntimeError, match="parserError"):
        assert zen.evaluate_expression('"fccdjny"[1:]', {"a": [1,2,3,4,5],"b":"fccdjny"}) == 'ccdjny' 
    with pytest.raises(RuntimeError, match="parserError"):
        assert zen.evaluate_expression('"fccdjny"[1:2]', {"a": [1,2,3,4,5],"b":"fccdjny"}) == 'cc'

    ## 测试 zen 表达式 变量字符串 切片 下标非整数  支持
    assert zen.evaluate_expression('a[3: 3+3]', {"a": "fccdjny"}) == "djny"
    assert zen.evaluate_expression('a[3: 3+1.3]', {"a": "fccdjny"}) == "dj"

    ## 测试 zen 表达式 字符串插值
    assert zen.evaluate_expression('`User ${user.name} is ${user.age} years old`', {"user":{"name":"John","age":30}}) == "User John is 30 years old"
    assert zen.evaluate_expression("'User ${user.name} is ${user.age} years old'", {"user":{"name":"John","age":30}}) == 'User ${user.name} is ${user.age} years old'

    ## 测试 zen 表达式 嵌套访问
    assert zen.evaluate_expression('user.contacts[i].phone.p[0]',
                                   {"i":1,
                                    "user":{"contacts":
                                            [
                                                {"phone":"123-456-7890"},
                                                {"phone":{"p":["456-123-7890"]}}
                                            ]
                                            }
                                    }) == '456-123-7890'
    assert zen.evaluate_expression('user.contacts [i].phone.p[0]', 
                                   {"i":1,
                                    "user":{"contacts":
                                            [
                                                {"phone":"123-456-7890"}, 
                                                {"phone":{"p":["456-123-7890"]}}
                                            ]
                                            }
                                    }) == '456-123-7890'

    ## 三元表达式和非空判断
    assert zen.evaluate_expression('a? 1 :2 + 3', {"a": True}) == 1
    assert zen.evaluate_expression('(a? 1 : 2) + 3', {"a": True}) == 4
    assert zen.evaluate_expression('a? b ?? "bbb" :2 + 3', {"a": True}) == "bbb"