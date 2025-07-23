
#  pytest tests/zen/test_zen.py -sl
#  -s 捕获标准输出
#  -l 显示出错的测试用例中的局部变量
#  -k 指定某一个测试用例执行
#  --setup-show  展示的单元测试 SETUP 和 TEARDOWN 的细节，展示测试依赖的加载和销毁顺序

import asyncio
from pathlib import Path
from pprint import pprint
import pytest
import zen

graphjson = """
{
  "contentType": "application/vnd.gorules.decision",
  "nodes": [
    {
      "type": "inputNode",
      "content": {
        "schema": ""
      },
      "id": "d4c5fdef-96c0-4c5e-8e7b-e1e4f9797251",
      "name": "request",
      "position": {
        "x": 245,
        "y": 355
      }
    },
    {
      "type": "outputNode",
      "content": {
        "schema": ""
      },
      "id": "a2cb6433-140b-4d2c-89f2-0e4f3140dd1a",
      "name": "response",
      "position": {
        "x": 1120,
        "y": 365
      }
    },
    {
      "type": "expressionNode",
      "content": {
        "expressions": [
          {
            "id": "8bf2c094-3115-4608-9416-1c854c68cc89",
            "key": "result",
            "value": "num * 2"
          }
        ],
        "passThrough": false,
        "inputField": null,
        "outputPath": null,
        "executionMode": "single"
      },
      "id": "45bbd693-493b-415d-8ad6-0d57c9a40d3e",
      "name": "expression1",
      "position": {
        "x": 715,
        "y": 400
      }
    }
  ],
  "edges": [
    {
      "id": "84fa9a9a-e90a-4322-be6f-94d3efd84edf",
      "sourceId": "d4c5fdef-96c0-4c5e-8e7b-e1e4f9797251",
      "type": "edge",
      "targetId": "45bbd693-493b-415d-8ad6-0d57c9a40d3e"
    },
    {
      "id": "0cd7ec7d-05d9-4497-abc7-d51b2202ddb4",
      "sourceId": "45bbd693-493b-415d-8ad6-0d57c9a40d3e",
      "type": "edge",
      "targetId": "a2cb6433-140b-4d2c-89f2-0e4f3140dd1a"
    }
  ]
}
"""

graphs = {"expression_multi2.json": graphjson}

def loader(key):
    # 考虑是否把所有的规则都往文件系统上缓存一份.
    return graphs[key]

# 同步测试
def test_zen_with_loader():
    """
        engine.evaluate 会隐式地调用 loader 函数
    """
    engine = zen.ZenEngine({"loader": loader})
    input = {
        "num": 15,
        "ip": '127.0.0.1',
    }
    res_with_trace = engine.evaluate("expression_multi2.json", input, {"trace": True})  # 测试同步方法
    assert "result" in res_with_trace and "trace" in res_with_trace
    res = engine.evaluate("expression_multi2.json", input)  
    assert "result" in res

    # # todo: 修复这个错误
    # engine_without_loader = zen.ZenEngine({})
    # engine_without_loader.evaluate("expression_multi2.json", input, {"trace": True})  # 测试同步方法


# 同步测试
def test_zen_with_create_decision():
    """
        zen_expression_switch_decisionTable
        这种调用模式可以复用 decision 对象. 所以线上服务推荐使用此种模式
    """
    engine = zen.ZenEngine()
    con = loader("expression_multi2.json")
    decision = engine.create_decision(con)
    input = {
        "num": 15,
        "ip": '127.0.0.1',
        "phone": '1770711xxxx',
    }
    res_with_trace = decision.evaluate(input, {"trace": True})
    # pprint(res_with_trace)
    assert "result" in res_with_trace and "trace" in res_with_trace
    res = decision.evaluate(input)
    # pprint(res)
    assert "result" in res


@pytest.mark.asyncio
async def test_zen_with_loader_async_evaluate():
    """
        异步函数需要 pytest.mark.asyncio 装饰器. 
        以及需要导入 pytest-asyncio
        uv add --dev pytest-asyncio
    """
    engine = zen.ZenEngine({"loader": loader})
    input = {
        "num": 15,
        "ip": '127.0.0.1',
    }
    res_with_trace = await engine.async_evaluate("expression_multi2.json", input, {"trace": True})  # 测试同步方法
    assert "result" in res_with_trace and "trace" in res_with_trace
    res = await engine.async_evaluate("expression_multi2.json", input)  
    assert "result" in res