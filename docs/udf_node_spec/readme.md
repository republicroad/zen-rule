
# 自定义函数规范

此文件件重包含自定义节点中的自定义函数(算子)规范，这些协议目前是归档状态。线上不使用这些自定义函数规范格式，仅仅用作记录曾经的演变记录。

```txt
(zen-rule)$ tree -L 2 docs/udf_node_spec/
docs/udf_node_spec/
├── custom_v0.json           zen-engine默认自定义节点示例
├── custom_v1.json           自定义节点v1版本规范(2024-07 到 2025-08在线上使用) 
├── custom_v2.json           自定义节点v2版本规范(未上线)
├── custom_v2_parse.json     自定义节点v2中的表达式(主要是嵌套函数调用)被解析后的示例(嵌套函数生成的语法树ast)
└── readme.md
```


## 第二版自定义节点(未上线)

> **注意**: 此版本作为实验版本存在，从未在线上使用. 在python中实现对 zen 表达式的完全兼容不如在zen expression项目中去支持扩展自定义函数调用.

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

> **注意**: zen-rule 从 0.17.0 版本开始不支持 custom_v1.json 格式.

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