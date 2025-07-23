### 用下列命令来查看运行结果.
### pytest  tests/bench/test_zen_engine.py --benchmark-only
import random
import json
import string
from pprint import pprint
import pytest

import zen

con = """
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

def init_zen():
  engine = zen.ZenEngine()
  decision = engine.create_decision(con)
  return engine, decision


engine, decision = init_zen()


def zenengine_demo0(con):
  engine = zen.ZenEngine()
  decision = engine.create_decision(con)
  input = {
    "num": 10,
  }
  result = decision.evaluate(input, {"trace": True})


def zenengine_demo1(con, engine):
  decision = engine.create_decision(con)
  input = {
    "num": 10,
  }
  result = decision.evaluate(input, {"trace": True})


def zenengine_demo2(con, decision):
  input = {
    "num": 10,
  }
  result = decision.evaluate(input, {"trace": True})


def zenengine_demo3(con, decision):
  input = {
    "num": 10,
  }
  result = decision.evaluate(input)


def zenengine_demo4(con, decision):
  input = {
    "num": 10,
    "extra_num": random.randint(0, 100)
  }
  result = decision.evaluate(input)


def zenengine_demo5(con, decision):
  input = {
    "num": 10,
  }
  key = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
  value = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
  input[key] = value
  result = decision.evaluate(input)


@pytest.mark.benchmark(
    group="zen-engine-decision",
    disable_gc=True,
    # warmup=False
)
def test_0(benchmark):
  # benchmark something
  result = benchmark(zenengine_demo0, con)

  # Extra code, to verify that the run completed correctly.
  # Sometimes you may want to check the result, fast functions
  # are no good if they return incorrect results :-)
  assert True


@pytest.mark.benchmark(
    group="zen-engine-decision",
    disable_gc=True,
    # warmup=False
)
def test_1(benchmark):
  # benchmark something
  result = benchmark(zenengine_demo1, con, engine)

  # Extra code, to verify that the run completed correctly.
  # Sometimes you may want to check the result, fast functions
  # are no good if they return incorrect results :-)
  assert True


@pytest.mark.benchmark(
    group="zen-engine-decision",
    disable_gc=True,
    # warmup=False
)
def test_2(benchmark):
  # benchmark something
  result = benchmark(zenengine_demo2, con, decision)

  # Extra code, to verify that the run completed correctly.
  # Sometimes you may want to check the result, fast functions
  # are no good if they return incorrect results :-)
  assert True


@pytest.mark.benchmark(
    group="zen-engine-decision",
    disable_gc=True,
    # warmup=False
)
def test_3(benchmark):
  # benchmark something
  result = benchmark(zenengine_demo3, con, decision)

  # Extra code, to verify that the run completed correctly.
  # Sometimes you may want to check the result, fast functions
  # are no good if they return incorrect results :-)
  assert True


@pytest.mark.benchmark(
    group="zen-engine-decision",
    disable_gc=True,
    # warmup=False
)
def test_4(benchmark):
  # benchmark something
  result = benchmark(zenengine_demo4, con, decision)

  # Extra code, to verify that the run completed correctly.
  # Sometimes you may want to check the result, fast functions
  # are no good if they return incorrect results :-)
  assert True


@pytest.mark.benchmark(
    group="zen-engine-decision",
    disable_gc=True,
    # warmup=False
)
def test_5(benchmark):
  # benchmark something
  result = benchmark(zenengine_demo4, con, decision)

  # Extra code, to verify that the run completed correctly.
  # Sometimes you may want to check the result, fast functions
  # are no good if they return incorrect results :-)
  assert True


def custom_handler(request):
    from pprint import pprint
    pprint(dir(request))
    print("request.input:  ", request.input)
    print("request.node:   ", request.node)

    func1 = lambda x: x
    func2 = lambda x: x
    customnode2functions = {
      "138b3b11-ff46-450f-9704-3f3c712067b2": func1,
      "8284e0b9-d3ba-4617-8a6c-86682ee24425": func2,

    }
    node_id = ""
    customnode2functions[node_id]
    # if request.node["id"] == node_id:
    #   func = customnode2functions[node_id]
    #   func(request.input)
    return {
        "output": { "sum": 100 }
    }


if __name__ == "__main__":
    engine = zen.ZenEngine()
    decision = engine.create_decision(con)
    input = {
      "num": 10,
    }
    res = decision.evaluate(input, {"trace": False})
    pprint(res)