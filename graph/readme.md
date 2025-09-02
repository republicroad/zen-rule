
# 自定义函数规范

此文件件重包含自定义节点中的自定义函数(算子)规范.


## 第三版自定义节点(当前默认规范)

`custom_v3.json` 表示第三版自定义节点规范. 


### 格式一

如果支持不同自定义算子的嵌套, 那么这些节点分类就形同虚设.
考虑到自定义算子再未来的功能以及演化, 暂时决定自定义算子不支持嵌套调用和解析.
参考 zen-engine 的表达式测试用例. 为了简化参数的解析, 决定选用 `;;` 作为函数的分隔符号.

> foo;;myvar ;;max([5, 8, 2, 11, 7]);;rand(100);; 'fccd;;jny' ;;3+4

表示 foo 算子传入了五个参数:
1. zen 表达式变量 myvar
2. zen 表达式函数 max([5, 8, 2, 11, 7])
3. zen 表达式 rand(100)
4. zen 表达式 'fccd;;jny'
5. zen 表达式 3+4


解析后得到如下结构, 解释执行即可:

> ["foo", "myvar", "max([5, 8, 2, 11, 7])", "rand(100)", "fccd;;jny", "3+4"]

解析逻辑如下:

```python
def parse_oprator_expr_v3(expr):
    # 不能简单使用字符串分割, 因为字符串中可能会有分隔符的模式出现, 比如:
    # foo ;; myvar ;; bar(zoo('fccd;;jny',6, 3.14),'a');; a+string(xxx)
    # foo;;myvar;;max([5, 8, 2, 11, 7]);;rand(100);; 'fccd;;jny' ;;3+4
    # expr.split(";;")
    pattern = r""";;(?=(?:[^"'`]*["'`][^"'`]*["'`])*[^"'`]*$)"""
    # To split the string by these semicolon:
    _parts = re.split(pattern, expr)
    parts = [i.strip() for i in _parts]  # 去掉表达式前后的空格
    return parts
```

### 格式二(正在支持中)

第二种就是保留技术更为熟悉的函数嵌套调用结构.
这种格式需要解析函数的嵌套调用, 还需要解析各种常量语法结构, 比如 数字， 布尔，字符串，数组，object对象, 
以及各种数组和字符串下标索引访问和切片访问语法格式, 还有中缀表达式(算术运算和逻辑运算), 非空判定, 三元表达式.

这部分需要使用上下无关文法定义解析或者peg语法解析.

> foo(myvar,max([5, 8, 2, 11, 7]),rand(100), 'fccd;;jny', 3+4)


解析后格式如下:

> [["foo", "myvar", "max([5, 8, 2, 11, 7])", "rand(100)", "'fccd;;jny'", "3+4"]]

此实现需要不断的去补充关于 zen 表达式语法结构的解析.  
详细参考 tests/test_zen_expr_parser.py 中的实现. 
```bash
$ python '/home/ryefccd/workspace/zen-rule/tests/test_zen_expr_parser.py'
foo(myvar,max([5, 8, 2, 11, 7]),rand(100), 'fccd;;jny', 3+4) --> [['foo', 'myvar', 'max([5, 8, 2, 11, 7])', 'rand(100)', "'fccd;;jny'", '3+4']]
...
```

解析后格式如下:  

```json
{
    "id": "138b3b11-ff46-450f-9704-3f3c712067b2",
    "type": "customNode",
    "position": {
    "x": 470,
    "y": 240
    },
    "name": "customNode1",
    "content": {
    "kind": "sum",
    "config": {
        "version": "v3",
        "meta": {
        "user": "wanghao@geetest.com",
        "proj": "proj_id"
        },
        "prop1": "{{ a + 10 }}",
        "passThrough": true,
        "inputField": null,
        "outputPath": null,
        "expressions": [
        {
            "id": "52d41e3d-067d-4930-89bd-832b038cd08f",
            "key": "result",
            "value": "foo;;myvar ;;max([5, 8, 2, 11, 7]);;rand(100);; 'fccd;;jny' ;;3+4"
        }
        ],
        "expr_asts": [
        {
            "id": "52d41e3d-067d-4930-89bd-832b038cd08f",
            "key": "result",
            "value": ["foo", "myvar", "max([5, 8, 2, 11, 7])", "rand(100)", "\\'fccd;;jny\\'", "3+4"]
        }
        ]
    }
    }
}
```


## 第二版自定义节点

`custom_v2.json` 表示第二版自定义节点规范. 此版本打算实现python自定义函数和zen表达式中的函数的混合嵌套调用. 
考虑到产品上会将自定义节点的自定义函数分为多个节点实现. 那么嵌套函数调用的就没有实际意义了.

`custom_v2_parse.json` 中包含界面编写的自定义函数表达式, 同时也有后端解析这部分表达式的属性.

```json
{
    "id": "138b3b11-ff46-450f-9704-3f3c712067b2",
    "type": "customNode",
    "position": {
    "x": 470,
    "y": 240
    },
    "name": "customNode1",
    "content": {  
        "kind": "sum",
        "config": {
            "version": "v2",
            "meta": {
                "user": "wanghao@geetest.com",
                "proj": "proj_id"
            },
            "prop1": "{{ a + 10 }}",
            "passThrough": true,
            "inputField": null,
            "outputPath": null,
            "expressions": [
                {
                    "id": "52d41e3d-067d-4930-89bd-832b038cd08f",
                    "key": "result",
                    "value": "foo(myvar,bar(zoo('fccdjny',6, 3.14),'a'), bas())"
                }
            ],
            "expr_asts": [
                {
                    "id": "52d41e3d-067d-4930-89bd-832b038cd08f",
                    "key": "result",
                    "value": [{"name": "zoo", "args": [["'fccdjny'", "string"], [6, "int"], [3.14, "float"]], "ns": "", "id": "566a36f923b34cbd9c159272adc988ae"}, {"name": "bar", "args": [[{"name": "zoo", "args": [["'fccdjny'", "string"], [6, "int"], [3.14, "float"]], "ns": "", "id": "566a36f923b34cbd9c159272adc988ae"}, "func_value"], ["'a'", "string"]], "ns": "", "id": "5d0b81e086d748d4902a35fd85bad974"}, {"name": "bas", "args": [], "ns": "", "id": "7f8448aad2594b479f6df2e2241707c7"}, {"name": "foo", "args": [["myvar", "var"], [{"name": "bar", "args": [[{"name": "zoo", "args": [["'fccdjny'", "string"], [6, "int"], [3.14, "float"]], "ns": "", "id": "566a36f923b34cbd9c159272adc988ae"}, "func_value"], ["'a'", "string"]], "ns": "", "id": "5d0b81e086d748d4902a35fd85bad974"}, "func_value"], [{"name": "bas", "args": [], "ns": "", "id": "7f8448aad2594b479f6df2e2241707c7"}, "func_value"]], "ns": "", "id": "0c509d4654ef443eb621d791d3ffcaa1"}]
                }
            ]
        }
    }
}
```

## 第一版自定义节点

`custom_v1.json` 表示第一版自定义节点规范. 这个版本的自定义函数的解析规范在前端实现.

```json
{
    "id": "dbb053ea-03e9-4a84-95e4-2cb8936dd817",
    "key": "res_get",
    "type": "function",
    "arg_exprs": {
    "url": "'http://httpbin.org/get'",
    "method": "'get'",
    "payload": "a"
    },
    "funcmeta": {
    "name": "http_call",
    "arglength": 3,
    "arguments": [
        {
        "arg_name": "url",
        "arg_type": "string",
        "defaults": "",
        "comments": "http request url"
        },
        {
        "arg_name": "method",
        "arg_type": "string",
        "defaults": "",
        "comments": "get/post"
        },
        {
        "arg_name": "payload",
        "arg_type": "dict",
        "defaults": "",
        "comments": "json payload"
        }
    ],
    "return_values": {
        "return_value": ""
    },
    "comments": "send a http request"
    }
}
```

## 默认自定义节点

`custom_v0.json` 表示默认的自定义节点示例.