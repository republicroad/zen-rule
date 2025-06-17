
# zen

## zen expression

## zen engine

## zen decsision

## zen graph

### custom node

#### custom node v1

```json
{
    "id": "138b3b11-ff46-450f-9704-3f3c712067b2",
    "type": "customNode",
    "position": {
        "x": 915,
        "y": 80
    },
    "name": "customNode_UDF",
    "content": {
    "kind": "UDF",
    "config": {
        "meta": {
            "user": "wanghao@geetest.com",
            "proj": "proj_id"
        },
        "inputs": [
        {
            "id": "f14cdcc1-5342-41a2-979a-556976b3c8a8",
            "key": "myrate1m",
            "type": "function",
            "funcmeta": {
                "name": "rate_1m",
                "arglength": 1,
                "arguments": {
                    "0": {
                        "arg_name": "mykey",
                        "arg_type": "string",
                        "defaults": "",
                        "comments": "统计字段或者表达式"
                    }
                },
                "arg_exprs": {
                    "0": "users.name"
                },
                "return_values":{"mykey": "", "rate": 0, "ttl": 0},
                "comments": [
                    "请输入频率计算参数"
                ]
            }
        },
        {
            "id": "f14cdcc1-5342-41a2-979a-556976b3c8a9",
            "key": "testrate1m",
            "type": "function",
            "funcmeta": {
                "name": "rate_1m",
                "arglength": 1,
                "arguments": {
                    "0": {
                        "arg_name": "mykey",
                        "arg_type": "string",
                        "defaults": "",
                        "comments": "统计字段或者表达式"
                    }
                },
                "arg_exprs": {
                    "0": "users.name"
                },
                "return_values":{"mykey": "", "rate": 0, "ttl": 0},
                "comments": [
                    "请输入频率计算参数"
                ]
            }
        },
        {
            "id": "0e4d45f1-0ad0-4edc-a474-44afa9430920",
            "key": "user_distinct_ip",
            "type": "function",
            "funcmeta": {
                "name": "group_distinct_1m",
                "arglength": 2,
                "arguments": {
                    "0": {
                        "arg_name": "group",
                        "arg_type": "string",
                        "defaults": "",
                        "comments": "分组字段表达式"
                    },
                    "1": {
                        "arg_name": "distinct",
                        "arg_type": "string",
                        "defaults": "",
                        "comments": "分组去重字段"
                    }
                },
                "arg_exprs": {
                    "0": "user",
                    "1": "ip"
                },
                "return_values":{
                    "group": "", 
                    "distinct": "",
                    "group_pv_rate": 0,
                    "group_uv_rate":  0,
                    "combine_key_pv_rate": 0,
                    "ttl": 0
                    },
                "comments": [
                    "最近一份中分组去重函数"
                ]
            }
        }
        ],
        "prop1": "{{ a + 10 }}"
    }
}
}

```

#### custom node v2

```c
foo(bar(2  , zoo(3,6),'a'), bas())
```


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
        "kind": "xxx",
        "version": "v2",  // version
        "config": {
            "prop1": "{{ a + 10 }}",
            "expressions": [
                {
                    "id": "a7b82f73-92ed-4abe-b4b9-e3caf6436b9b",
                    "key": "num",
                    "value": "rand(100)"  // 可以混合自定义函数和 zen 函数??? 在calludf中找不到就再zen expression 中去执行.
                },
                {
                    "id": "52d41e3d-067d-4930-89bd-832b038cd08f",
                    "key": "result",
                    "value": "foo(bar( 2,'a'), bas())"
                }
            ]
        }
    }
}
```