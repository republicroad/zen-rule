
#  pytest tests/zen/test_zen.py -sl
#  -s 捕获标准输出
#  -l 显示出错的测试用例中的局部变量
#  -k 指定某一个测试用例执行
#  --setup-show  展示的单元测试 SETUP 和 TEARDOWN 的细节，展示测试依赖的加载和销毁顺序

import asyncio
import csv
import json
import logging
import inspect
from dataclasses import dataclass
from pathlib import Path
from pprint import pprint
import uuid
import pytest
import zen
from zen_rule import ZenRule, udf, FuncArg, FuncRet
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

graphjson = """
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
"""
file_path = Path(__file__).parent / 'data/standard.csv'


@dataclass
class ExprEval:
    ## 使用 zen.evaluate_expression 求值 
    expr: str
    input: dict
    output: str

zen_expression_demos = []
with open(file_path) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=';')
    line_count = 0
    header = next(csv_reader)
    logger.debug(f"headers:{header}")
    for row in csv_reader:
        if len(row) == 3:
            logger.debug(row)
            _args = row[1].strip()
            args = zen.evaluate_expression(_args) if _args else {}
            item = ExprEval(expr=row[0], input=args, output=row[2])
            zen_expression_demos.append(item)
    logger.debug(f'zen expressions: {len(zen_expression_demos)} rules.')


# 默认情况下使用位置参数传参.
# 如果有关键字参数, 那么同时也会使用关键字传参.
@udf(
    comments="test udf foo",
    args_info=[
        FuncArg(arg_name="a", arg_type="string", defaults="", comments="var a"),
        FuncArg(arg_name="b", arg_type="string", defaults="", comments="var b"),
        FuncArg(arg_name="c", arg_type="string", defaults="", comments="var c"),
    ],
    return_info=FuncRet(field_type="string", examples="fccdjny", comments="返回值示例, 字段解释")     
)
def foo(*args, **kwargs):
    """
        此测试传入一个参数, 将此参数当做返回值, 便于去做 assert.
    """
    logger.debug(f"{inspect.stack()[0][3]} args:{args}")
    logger.debug(f"{inspect.stack()[0][3]} kwargs:{kwargs}")
    
    return args[0]


def loader(key):
    _graph =  graphjson
    return _graph


def udf_args_helper(graph, rule, expr_key):
    """
        把规则写在表达式的 value 中.
    """
    graph = json.loads(graph)
    func_call_expr = f"{foo.__name__};;{rule.expr}"
    for node in graph["nodes"]:
        if node["type"] == "customNode":
          udf_expr = {
            "id": str(uuid.uuid4()),
            "key": expr_key,
            "value": func_call_expr
          }
          node["content"]["config"]["expressions"] = [udf_expr]
    logger.debug(f"{rule.expr} graph:{graph}")
    res =  json.dumps(graph)
    return res


async def test_zenrule():
    """
        把这个改造为pytest单元测试的的最佳实践.
    """
    zr = ZenRule({})
    key = "udf.json"
    for i, rule in enumerate(zen_expression_demos):
      logger.info(f"round: {i}")
      expr_key = str(i)
      content = udf_args_helper(graphjson, rule, expr_key)
      zr.create_decision_with_cache_key(key, content)  # 将规则图缓存在键下, 这样可以只读取规则一次，解析一次，然后复用决策对象 decision
      result = await zr.async_evaluate(key, rule.input)
      output = result.get("result").get(expr_key)
      logger.info(f'expr: "{rule.expr}" input: {rule.input} expect: {rule.output} --> result: {output}')
      assert output == zen.evaluate_expression(rule.output)
      zr.delete_decision_with_cache_key(key)


if __name__ == "__main__":
    asyncio.run(test_zenrule())