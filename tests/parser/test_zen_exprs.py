import zen

zen.evaluate_expression("{a:1}", {"a":3, "b":"fccdjny", "c": {'name': 'Alice', 'age': 30}})
zen.evaluate_expression("{'a':1}", {"a":3, "b":"fccdjny", "c": {'name': 'Alice', 'age': 30}})
zen.evaluate_expression('{"a":1}', {"a":3, "b":"fccdjny", "c": {'name': 'Alice', 'age': 30}})


## 注意, zen context 的键值对中的键是字符串，这个字符串可以用单引号，双引号，也可以不用引号(像一个变量一样)
zen.evaluate_expression('{ firstName: "John", lastName: last }',  {"firstName":"fff", "lastName": "lll", "last":"fccdjny"})
zen.evaluate_expression("{ 'firstName': 'John', lastName: last }",  {"firstName":"fff", "lastName": "lll", "last":"fccdjny"})
zen.evaluate_expression('{ "firstName": "John", lastName: last }',  {"firstName":"fff", "lastName": "lll", "last":"fccdjny"})
zen.evaluate_expression('values({ firstName: "John", lastName: last })',  {"firstName":"fff", "lastName": "lll", "last":"fccdjny"})
zen.evaluate_expression('keys({ firstName: "John", lastName: last })',  {"firstName":"fff", "lastName": "lll", "last":"fccdjny"})


## 测试 zen 表达式 变量数组 切片   支持
zen.evaluate_expression('a[1]', {"a": [1,2,3,4,5],"b":"fccdjny"})
zen.evaluate_expression('a[1:]', {"a": [1,2,3,4,5],"b":"fccdjny"})
zen.evaluate_expression('a[1:2]', {"a": [1,2,3,4,5],"b":"fccdjny"})

## 测试 zen 表达式 变量字符串 切片  支持
zen.evaluate_expression('b[1]', {"a": [1,2,3,4,5],"b":"fccdjny"})
zen.evaluate_expression('b[1:]', {"a": [1,2,3,4,5],"b":"fccdjny"})
zen.evaluate_expression('b[1:2]', {"a": [1,2,3,4,5],"b":"fccdjny"})

## 测试 zen 表达式 常量数组 切片    支持
zen.evaluate_expression('[1,2,3,4,5][1]', {"a": [1,2,3,4,5],"b":"fccdjny"})
zen.evaluate_expression('[1,2,3,4,5][1:]', {"a": [1,2,3,4,5],"b":"fccdjny"})
zen.evaluate_expression('[1,2,3,4,5][1:2]', {"a": [1,2,3,4,5],"b":"fccdjny"})

## 测试 zen 表达式 常量字符串 切片  不支持
zen.evaluate_expression('"fccdjny"[1]', {"a": [1,2,3,4,5],"b":"fccdjny"})
zen.evaluate_expression('"fccdjny"[1:]', {"a": [1,2,3,4,5],"b":"fccdjny"})
zen.evaluate_expression('"fccdjny"[1:2]', {"a": [1,2,3,4,5],"b":"fccdjny"})



zen.evaluate_expression('a[3: 3+3]', {"a": "fccdjny"})
zen.evaluate_expression('a[3: 3+1.3]', {"a": "fccdjny"})  


zen.evaluate_expression('`User ${user.name} is ${user.age} years old`', {"user":{"name":"John","age":30}})
zen.evaluate_expression("'User ${user.name} is ${user.age} years old'", {"user":{"name":"John","age":30}})



zen.evaluate_expression('user.contacts[i].phone.p[0]', {"i":1,"user":{"contacts":[{"phone":"123-456-7890"}, {"phone":{"p":["456-123-7890"]}}]}})
zen.evaluate_expression('user.contacts [i].phone.p[0]', {"i":1,"user":{"contacts":[{"phone":"123-456-7890"}, {"phone":{"p":["456-123-7890"]}}]}})



zen.evaluate_expression('a? 1 :2 + 3', {"a": True}) == 1
zen.evaluate_expression('(a? 1 : 2) + 3', {"a": True}) == 4



zen.evaluate_expression('a? b ?? "bbb" :2 + 3', {"a": True})