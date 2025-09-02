from pathlib import Path
from pprint import pformat
import logging
import asyncio
import glob
import json
import os.path
import time
import unittest
import zen
logger = logging.getLogger(__name__)

basedir = Path(__file__).parent

async def loader(key):
    with open(basedir / "test-data/" / key, "r") as f:
        return f.read()


def sync_loader(key):
    with open(basedir / "test-data/" / key, "r") as f:
        return f.read()


def graph_loader(key):
    with open(basedir / "test-data/graphs/" / key, "r") as f:
        return f.read()


def custom_handler(request):
    p1 = request.get_field("prop1")
    return {
        "output": {"sum": p1}
    }


async def custom_async_handler(request):
    p1 = request.get_field("prop1")
    await asyncio.sleep(0.1)
    return {
        "output": {"sum": p1}
    }


class AsyncZenEngine(unittest.IsolatedAsyncioTestCase):
    def test_sync_loader_and_get_decision(self):
        engine = zen.ZenEngine({"loader": sync_loader})
        r1 = engine.get_decision("function.json")
        r2 = engine.get_decision("function.json")
        r3 = engine.get_decision("function.json")
        r4 = engine.get_decision("function.json")

    async def test_async_evaluate(self):
        engine = zen.ZenEngine({"loader": loader})
        r1 = engine.async_evaluate("function.json", {"input": 5})
        r2 = engine.async_evaluate("table.json", {"input": 2})
        r3 = engine.async_evaluate("table.json", {"input": 12})

        results = await asyncio.gather(r1, r2, r3)
        self.assertEqual(results[0]["result"]["output"], 10)
        self.assertEqual(results[1]["result"]["output"], 0)
        self.assertEqual(results[2]["result"]["output"], 10)

    async def test_async_evaluate_custom_handler(self):
        engine = zen.ZenEngine({"loader": loader, "customHandler": custom_async_handler})
        r1 = engine.async_evaluate("custom.json", {"a": 10})
        r2 = engine.async_evaluate("custom.json", {"a": 20})
        r3 = engine.async_evaluate("custom.json", {"a": 30})

        results = await asyncio.gather(r1, r2, r3)
        self.assertEqual(results[0]["result"]["sum"], 20)
        self.assertEqual(results[1]["result"]["sum"], 30)
        self.assertEqual(results[2]["result"]["sum"], 40)

    async def test_async_sleep_function(self):
        engine = zen.ZenEngine({"loader": loader, "customHandler": custom_async_handler})

        await engine.async_evaluate("sleep-function.json", {})
        self.assertTrue(True)

    async def test_async_http_function(self):
        engine = zen.ZenEngine({"loader": loader, "customHandler": custom_async_handler})

        await engine.async_evaluate("http-function.json", {})
        self.assertTrue(True)

    async def test_create_decisions_from_content(self):
        engine = zen.ZenEngine()
        with open(basedir / "test-data/function.json", "r") as f:
            functionContent = f.read()
        functionDecision = engine.create_decision(functionContent)

        r = await functionDecision.async_evaluate({"input": 15})
        self.assertEqual(r["result"]["output"], 30)

    async def test_evaluate_graphs(self):
        engine = zen.ZenEngine({"loader": graph_loader})
        json_files = glob.glob(str(basedir / "test-data/graphs/*.json"))
        # json_files = glob.glob(str(basedir / "test-data/*.json"))


        for json_file in json_files:
            logger.info("-----------------------")
            logger.info(json_file)
            with open(json_file, "r") as f:
                json_contents = json.loads(f.read())

            for test_case in json_contents["tests"]:
                logger.info("********start**********")
                logger.info("test_case:\n", pformat(test_case))
                key = os.path.basename(json_file)
                logger.info("before engine.async_evaluate")
                engine_response = await engine.async_evaluate(key, test_case["input"])
                logger.info("after engine.async_evaluate")
                logger.info("before engine.get_decision")
                decision = engine.get_decision(key)  # engine.get_decision 目前还不支持返回异步对象, 所以 graph_loader 只能用同步方法.
                logger.info("after engine.get_decision")
                decision_response = await decision.async_evaluate(test_case["input"])

                self.assertEqual(engine_response["result"], test_case["output"])
                self.assertEqual(decision_response["result"], test_case["output"])
                logger.info("********end**********")
            logger.info("-----------------------\n\n")


if __name__ == '__main__':
    unittest.main()
