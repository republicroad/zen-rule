import asyncio
import logging
from pathlib import Path
from pprint import pprint, pformat
import json
import contextvars
import pytest
import zen
logger = logging.getLogger(__name__)

# 设置 default 可以避免在调用 .get() 方法时报 LookupError 错误
# myvar = contextvars.ContextVar('myvar', default=None)
myvar = contextvars.ContextVar('myvar')


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


def loader(key):
    return graphs[key]


async def custom_async_handler(request):
    """
        一旦有异步自定义函数，需要使用异步方法去求表达式的值
    """
    # v = myvar.get()
    try:
        v = myvar.get()
        logger.warning(f"myvar.get():{v}")
    except LookupError as e:
        logger.error(e, exc_info=True)
        raise e
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
async def test_custmer_node_contextvars1():
    """
        测试自定义节点函数中的 contextvars 能否取得值.
        在实例化 ZenEngine 之前设置值.
    """
    o = object()
    myvar.set(o)
    engine = zen.ZenEngine({"loader": loader, "customHandler": custom_async_handler})
    logger.warning(f"myvar.set():{o}")
    res = await engine.async_evaluate("custom_node_demo.json", {"a": 10, "ip": "192.168.0.39"})
    assert res["result"]["prop1_raw"] == '{{ a + 10 }}'
    # 如果修改了规则图中的自定义节点的表达式, 需要重新修改这里的断言条件.
    assert res["result"]["prop1"]     == res["result"]["request.input"]['a'] + 10


@pytest.mark.asyncio
async def test_custmer_node_contextvars2():
    """
        测试自定义节点函数中的 contextvars 能否取得值.
        在实例化 ZenEngine 之后设置值.
        注意, 经过对 zen-engine 版本的二分查找定位, 发现 zen-engine==0.38.4 是这个用例失败的第一个版本.
        pytest test_zen_ch_contextvars.py  -sxlv --log-cli-level=0
    """
    engine = zen.ZenEngine({"loader": loader, "customHandler": custom_async_handler})
    o = object()
    myvar.set(o)
    logger.warning(f"myvar.set():{o}")
    res = await engine.async_evaluate("custom_node_demo.json", {"a": 10, "ip": "192.168.0.39"})
    assert res["result"]["prop1_raw"] == '{{ a + 10 }}'
    # 如果修改了规则图中的自定义节点的表达式, 需要重新修改这里的断言条件.
    assert res["result"]["prop1"]     == res["result"]["request.input"]['a'] + 1

