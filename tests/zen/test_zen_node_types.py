
#  pytest tests/zen/test_zen.py -sl
#  -s 捕获标准输出
#  -l 显示出错的测试用例中的局部变量
#  -k 指定某一个测试用例执行
#  --setup-show  展示的单元测试 SETUP 和 TEARDOWN 的细节，展示测试依赖的加载和销毁顺序

import asyncio
import json
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


# zen engine node type
def test_zen_node_type():
    """
        zen_expression_switch_decisionTable
        这种调用模式可以复用 decision 对象. 所以线上服务推荐使用此种模式
E       RuntimeError: Failed to serialize decision content
E       
E       Caused by:
E           unknown variant `inputNodea`, expected one of `inputNode`, `outputNode`, `functionNode`, 
                            `decisionNode`, `decisionTableNode`, `expressionNode`, `switchNode`, `customNode` at line 12 column 5
    """
    engine = zen.ZenEngine()
    g = json.loads(graphjson)
    nodes = g["nodes"]
    for node in nodes:
        # 修改 inputNode 类型为一个新的类型, 这样执行引擎会报错.
        if node["type"] == "inputNode":
            node["type"] = "inputNode_xxx"
    
    con = json.dumps(g)

    with pytest.raises(RuntimeError) as exc:
        decision = engine.create_decision(con)

    assert "Invalid JSON" in str(exc.value)
    assert "unknown variant `inputNode_xxx`" in str(exc.value)
    node_types = ["inputNode", "outputNode", "functionNode", "decisionNode",
                  "decisionTableNode", "expressionNode", "switchNode", "customNode"]
    assert all([t in str(exc.value) for t in node_types]), f"node type must be {node_types}"


