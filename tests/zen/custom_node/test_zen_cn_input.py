import asyncio
import logging
from pathlib import Path
from pprint import pprint, pformat
import json
import contextvars
import pytest
import zen
logger = logging.getLogger(__name__)


graph_json_customNode = """{
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
          "prop1": "{{ a + 10 }}"
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
}"""

graphs = {"custom_node_demo.json": graph_json_customNode}

## 也可以把 graphs 写到临时目录然后再用此loader方法加载.
# def loader(key):
#     rule_basedir = Path(__file__).parent / "test-data-brde"
#     file_path = rule_basedir / key
#     logger.warning(f"graph json path:{file_path}")
#     with open(file_path, "r") as f:
#         content =  f.read()
#         return content


def loader(key):
    return graphs[key]


def graph_addon(rule_content):
    # 此规则图只包含一个自定义节点.   请求 --> 自定义节点 --> 输出
    # 在自定义节点的 config meta 中添加输入节点的 name, 用于后续自定义函数通过 request.input 定位输入节点中
    # 传入的相关实例, 比如数据库的连接池, http的连接池, 业务参数, trace_id等
    rule_graph = json.loads(rule_content)
    name = [i.get("name") for i in rule_graph["nodes"] if i.get("type") == "inputNode"][0]
    for node in rule_graph["nodes"]:
        if node.get("type") == "customNode":
            content = node.get("content", {})
            config  = content.get("config", {})
            meta = config.get("meta", {})
            meta["inputNode_name"] = name
            # print("meta:", meta)
            node["content"]["config"]["meta"] = meta
        # print("node:", node)
    return json.dumps(rule_graph)


def loader_with_addons(key):
    """
        对规则图进行动态修改, 输入节点的名字写入自定义节点, 这样方便自定义节点在运行时动态获取输入节点的输入内容.
        因为默认情况下输入节点的名字是不确定的, 所以自定义节点的 handler 中无法确定输入节点的名字是什么. 这样就不能在自定义节点获取
        整个规则的输入.

        实现这个功能是方便在规则输入中传入一些全局参数. 这样方便去做日志或者 trace.
    """
    con =  graphs[key]
    addons_con = graph_addon(con)
    return addons_con


async def custom_async_handler(request):
    """
        一旦有异步自定义函数，需要使用异步方法去求表达式的值
    """
    logger.warning(f"request.input:{pformat(request.input)}")
    logger.warning(f"request.node: {pformat(request.node)}")
    request_node = request.input.get("$nodes", {}).get("Request", {})
    logger.warning(f"get request node input:{pformat(request_node)}")
    prop1 = request.get_field("prop1")
    prop1_raw = request.get_field_raw("prop1")

    await asyncio.sleep(0)
    return {
        "output": {
                    "prop1_raw": prop1_raw,
                    "prop1": prop1,
                    "request.input": request.input,
                    "request.node": request.node,
                }
    }


@pytest.mark.asyncio
async def test_custmer_node():
    """
        这种调用模式适合一次性的调用. 不能复用推理对象. 每次规则推理都需要去重复解析规则json文件.
    """
    engine = zen.ZenEngine({"loader": loader, "customHandler": custom_async_handler})
    res = await engine.async_evaluate("custom_node_demo.json", {"a": 10, "ip": "192.168.0.39"})
    assert res["result"]["prop1_raw"] == '{{ a + 10 }}'
    # 如果修改了规则图中的自定义节点的表达式, 需要重新修改这里的断言条件.
    assert res["result"]["prop1"]     == res["result"]["request.input"]['a'] + 10
    # 一般可以直接在测试函数的末尾 assert False 让测试失败, 然后使用 -l 选项输出测试失败时的局部变量的值. 方便排查问题.
    # result = res["result"]
    # assert False  # pytest tests/zen/test_zen_custom.py -k "test_custmer_node_cache_decision" -sv -l 


@pytest.mark.asyncio
async def test_custmer_node_with_object_input():
    """
        这种调用模式适合一次性的调用. 不能复用推理对象. 每次规则推理都需要去重复解析规则json文件.
    """
    class A:
        pass

    engine = zen.ZenEngine({"loader": loader, "customHandler": custom_async_handler})
    res = await engine.async_evaluate("custom_node_demo.json", {"a": 10, "ip": "192.168.0.39",
                                                      "__meta__":{"redispool": "redispool", "httpclient": "httpclient"}})
    assert res["result"]["prop1_raw"] == '{{ a + 10 }}'
    # 如果修改了规则图中的自定义节点的表达式, 需要重新修改这里的断言条件.
    assert res["result"]["prop1"]     == res["result"]["request.input"]['a'] + 10

    # await engine.async_evaluate("custom_node_demo.json", {"a": 10, "b": "cjn","__meta__":{"redispool": "redispool", "httpclient": A()}})
    ### input 只能传入能被序列化的对象, 比如普通的字符串和数字. python 类实例无法传递
    with pytest.raises(TypeError) as excinfo:
        await engine.async_evaluate("custom_node_demo.json", {"a": 10, "b": "cjn","__meta__":{"redispool": "redispool", "httpclient": A()}})
    assert "argument 'ctx': unsupported type" in str(excinfo.value)


@pytest.mark.asyncio
async def test_custmer_node_with_addons():
    """
        pytest '/home/ryefccd/workspace/zen-rule/tests/test_zen_ch_input.py' -xlsvv  # 可以将字段完全输出, 方便排除bug.
        使用 loader_with_addons 动态将元数据(比如输入节点名字)写入自定义节点元信息中.
        {'performance': '568.4µs',
        'result': {'prop1': 20,
                    'prop1_raw': '{{ a + 10 }}',
                    'request.input': {'$nodes': {'Request': {'a': 10,
                                                            'ip': '192.168.0.39'}},
                                      'a': 10,
                                      'ip': '192.168.0.39'},
                    'request.node': {'config': {'meta': {'inputNode_name': 'Request'},
                                                'prop1': '{{ a + 10 }}'},
                                    'id': '138b3b11-ff46-450f-9704-3f3c712067b2',
                                    'kind': 'sum',
                                    'name': 'customNode1'}}}
    """
    engine = zen.ZenEngine({"loader": loader_with_addons, "customHandler": custom_async_handler})
    res = await engine.async_evaluate("custom_node_demo.json", {"a": 10, "ip": "192.168.0.39"})
    assert res["result"]["prop1_raw"] == '{{ a + 10 }}'
    # 如果修改了规则图中的自定义节点的表达式, 需要重新修改这里的断言条件.
    assert res["result"]["prop1"]     == res["result"]["request.input"]['a'] + 10
