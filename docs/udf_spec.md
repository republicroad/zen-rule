
# zen-rule

## 自定义函数spec

描述自定义函数的 json schema 规范:

1. 在 json schema 中使用 title 当作名称.一般来说, title 字段和name字段保持一致，title字段是json schema 的标准定义, name 是 openai 中的function calling 定义, 定义name字段是为了让自定义函数调用可以兼容openai, 这样我们的自定义函数可以注册为兼容 openai 大模型(基本上大模型都兼容openai接口)的工具函数.
   不管任何层级，建议我们都使用 title 字段，那么name字段用来兼容openai.  
2. 顶层tools字段中就是自定义算子的 schema 定义，算子中的 parameters 字段是标准的 json schema 定义.
3. parameters.properties 中包含函数的参数，键的顺序就是算子中入参的顺序.
4. parameters.required 表示哪些参数是必传的.
5. 旧的自定义函数定义会在函数定义中有 arglength 表示函数参数个数，现在需要遍历 parameters.properties 中的选项得到参数个数，并且其迭代顺序代表参数顺序。
6. 自定义函数的返回值的 json schema 中增加与 parameters 统一层级的 returns 字段表示返回值定义. returns.content 表示函数返回值的内容定义, returns.content.schema 则是具体的字段及其类型定义. 简化前端编辑表达式时做输入提示和补全.

```json
[  
    {
        "type": "namespace", /*顶层type namespace 表示自定义节点定义*/
        "title": "http", /* title 是 json schema 的规范*/
        "name": "http", /* 自定义节点的名字 */
        "description": "",
        "tools": [ /* tools 表示自定义节点中的自定义算子(函数)列表*/
            {
                "name": "http_call",
                "title": "http_call",
                "type": "function",
                "description": "http 请求调用\n第一个参数是 url, 第二个参数是请求方法(\"get\"/\"post\"),\n第三个参数是请求体(zen context/object)",
                "parameters": {
                    "properties": {
                        "url": {
                            "description": "目标 url",
                            "title": "Url",
                            "type": "string"
                        },
                        "method": {
                            "default": "get",
                            "description": "请求方法(\"get\" 或者 \"post\")",
                            "title": "Method",
                            "type": "string"
                        },
                        "payload": {
                            "additionalProperties": true,
                            "default": {},
                            "description": "请求的参数(zen context/object)",
                            "title": "Payload",
                            "type": "object"
                        }
                    },
                    "required": [
                        "url"
                    ],
                    "title": "http_call",
                    "type": "object"
                },
                "returns": {
                    "description": "http call use define function return value",
                    "content": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "integer",
                                    "description": "The user ID"
                                },
                                "username": {
                                    "type": "string",
                                    "description": "The user name"
                                }
                            }
                        }
                    }
                }，
                "namespace": "http",
                "kind": "http"
            },
            {
                "name": "http_call_with_headers",
                "title": "http_call_with_headers",
                "type": "function",
                "description": "http 请求调用\n第一个参数是 url, 第二个参数是请求方法(\"get\"/\"post\"),\n第三个参数是请求体(zen context/object),\n第四个参数是请求头headers(zen context/object).",
                "parameters": {
                    "properties": {
                        "url": {
                            "default": "",
                            "description": "目标 url",
                            "title": "Url",
                            "type": "string"
                        },
                        "method": {
                            "default": "",
                            "description": "请求方法(\"get\" 或者 \"post\")",
                            "title": "Method",
                            "type": "string"
                        },
                        "payload": {
                            "additionalProperties": true,
                            "default": {},
                            "description": "请求的参数(zen context/object)",
                            "title": "Payload",
                            "type": "object"
                        },
                        "headers": {
                            "additionalProperties": true,
                            "default": {},
                            "description": "请求头headers(zen context/object)",
                            "title": "Headers",
                            "type": "object"
                        }
                    },
                    "title": "http_call_with_headers",
                    "type": "object"
                },
                "namespace": "http",
                "kind": "http"
            }
        ]
    }
]
```


## 自定义算子规范

在决策引擎中, 自定义算子主要承担外部数据查询, 状态交互, 以及一些自定义功能拓展. 
考虑到界面中会对自定义算子进行分类, 这时候在某个自定义类别的节点中只能访问这个类别的函数,
这样有利于降低最后用户的使用难度. 

![alt text](custom_nodes.png)  

自定义节点中的算子 oprater 调用支持两种格式:

1. 字符串格式, 以 ;; 作为分隔符, 表示算子及其参数的分隔符, 比如:
> foo;;myvar ;;max([5, 8, 2, 11, 7]);;rand(100);; 'fccd;;jny' ;;3+4

2. json数组格式, 直接使用 json 数组表示算子及其参数, 比如:
> ["foo", "myvar", "max([5, 8, 2, 11, 7])", "rand(100)", "'fccd;;jny'", "3+4"]

表示 foo 算子传入了五个参数:
- zen 表达式变量 myvar
- zen 表达式函数 max([5, 8, 2, 11, 7])
- zen 表达式 rand(100)
- zen 表达式 'fccd;;jny'
- zen 表达式 3+4

格式1可以通过如下正则表达式来得到表达式2, 代码如下所示:

```python
def parse_oprator_expr(expr):
    # 不能简单使用字符串分割, 因为字符串中可能会有分隔符的模式出现, 比如:
    # foo;;myvar ;;max([5,8,2,11, 7]);;rand(100)+120;;3+4;; 'singel;;quote' ;;"double;;quote" ;;`backquote;; ${bar}`
    # expr.split(";;")
    pattern = r""";;(?=(?:[^"'`]*["'`][^"'`]*["'`])*[^"'`]*$)"""
    # To split the string by these semicolon:
    _parts = re.split(pattern, expr)
    parts = [i.strip() for i in _parts]  # 去掉表达式前后的空格
    return parts
```

### 解析后格式

```json

    "expressions": [
      {
        "id": "52d41e3d-067d-4930-89bd-832b038cd08f",
        "key": "result",
        "value": "foo;;myvar;;max([5, 8, 2, 11, 7]);;rand(100)"
      }
    ],
    "expr_asts": [
      {
        "id": "52d41e3d-067d-4930-89bd-832b038cd08f",
        "key": "result",
        "value": ["foo", "myvar", "max([5, 8, 2, 11, 7])", "rand(100)"]
      }
    ]

```


### 完全示例

```json
{
  "contentType": "application/vnd.gorules.decision",
  "nodes": [
    {
      "id": "115975ef-2f43-4e22-b553-0da6f4cc7f68",
      "type": "inputNode",
      "position": {
        "x": 180,
        "y": 240
      },
      "name": "Request"
    },
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
              "value": "foo;;myvar;;bar(zoo('fccdjny',6, 3.14),'a');; bas()",
            }
          ],
          "expr_asts": [
            {
              "id": "52d41e3d-067d-4930-89bd-832b038cd08f",
              "key": "result",
              "value": ["foo", "myvar", "bar(zoo('fccdjny',6, 3.14),'a')", "a+string(xxx)"]
            }
          ]
        }
      }
    },
    {
      "id": "db8797b1-bcc1-4fbf-a5d8-e7d43a181d5e",
      "type": "outputNode",
      "position": {
        "x": 780,
        "y": 240
      },
      "name": "Response"
    }
  ],
  "edges": [
    {
      "id": "05740fa7-3755-4756-b85e-bc1af2f6773b",
      "sourceId": "115975ef-2f43-4e22-b553-0da6f4cc7f68",
      "type": "edge",
      "targetId": "138b3b11-ff46-450f-9704-3f3c712067b2"
    },
    {
      "id": "5d89c1d6-e894-4e8a-bd13-22368c2a6bc7",
      "sourceId": "138b3b11-ff46-450f-9704-3f3c712067b2",
      "type": "edge",
      "targetId": "db8797b1-bcc1-4fbf-a5d8-e7d43a181d5e"
    }
  ]
}
```