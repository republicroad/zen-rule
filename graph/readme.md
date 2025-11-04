
# 自定义函数规范

此文件件重包含自定义节点中的自定义函数(算子)规范.

> **注意**: zen-rule 从 0.17.0 版本开始不支持 custom_v1.json 格式.


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

### 格式二(WIP)

第二种就是保留技术更为熟悉的函数嵌套调用结构.
这种格式需要解析函数的嵌套调用, 还需要解析各种常量语法结构, 比如 数字， 布尔，字符串，数组，object对象, 
以及各种数组和字符串下标索引访问和切片访问语法格式, 还有中缀表达式(算术运算和逻辑运算), 非空判定, 三元表达式.

这部分需要使用上下无关文法定义解析或者peg语法解析.
目前使用 pyparsing 来解析, 将来考虑使用[lark](https://github.com/lark-parser/lark) 来做语法解析.

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


