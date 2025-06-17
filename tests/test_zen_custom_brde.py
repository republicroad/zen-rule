import asyncio
import logging
from pathlib import Path
from pprint import pprint, pformat
import json
import contextvars
import pytest
import zen
import aiohttp
import redis
logger = logging.getLogger(__name__)
context_http_client = contextvars.ContextVar('http_client', default=None)

rule_basedir = Path(__file__).parent / "test-data-brde"

class RuleAssert:
    def __init__(self, rule_content, **kwargs) -> None:
        # self.meta = meta
        self.user_name = kwargs.get("user_name")
        self.inputNode_name = kwargs.get("inputNode_name")
        con, _meta = self.open_graph_with_meta(rule_content)
        self.rule_content = con
        self.meta = _meta
        self.engine = zen.ZenEngine({"customHandler": self.custom_async_handler})
        self.decision = self.engine.create_decision(con)  # 耗时操作, 所以需要复用 decision 对象实例.
        # decision.__setattr__("meta", meta)   # AttributeError: 'builtins.ZenDecision' object has no attribute 'meta'

    def update_decision(self, rule_content):
        con, _meta = self.open_graph_with_meta(rule_content)
        self.rule_content = con
        self.meta = _meta
        self.decision = self.engine.create_decision(con)

    async def async_evaluate(self, input, context: dict={}):
        # input.update({"__meta__": self.meta})
        # result = await self.decision.async_evaluate(input)  # 也许这种字典本地改动性能会好一些.
        self.meta.update(context)
        result = await self.decision.async_evaluate({**input, **{"__meta__": self.meta}})
        return result

    async def custom_async_handler(self, request):
        """
            一旦有异步自定义函数，需要使用异步方法去求表达式的值

            为了便于拍错, 最后自定义函数最外层包裹一层异常捕获, 否则这些异常会再 rust 中捕获, 无法去控制出错信息的渲染.
            比如打印异常栈方便定位错误.
        """
        http_client_session  = context_http_client.get()
        logger.warning(f"http_client_session:{http_client_session}")
        async with http_client_session.get('http://httpbin.org/get') as resp:
                    assert resp.status == 200
                    res = await resp.json()
                    assert res["url"] == 'http://httpbin.org/get'
                    logger.warning(f"httpbin get:{res}")
        logger.info(f"request.input:\n{pformat(request.input)}")
        logger.info(f"request.node:\n{pformat(request.node)}")
        request_node = request.input.get("$nodes", {}).get("Request", {})
        # pprint(request_node)
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

    def open_graph_with_meta(self, rule_content):
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
        return json.dumps(rule_graph), meta


@pytest.mark.asyncio
async def test_custmer_node_cache_decision_contain_context_input():
    """
        request --> expression --> customer --> response
        customer 通过自定义函数可以获取上一个节点的输出和输入节点内容.
        通过此逻辑，可以在自定义函数中传递一些单例实例, 比如数据库的连接池, http的连接池, 业务参数, trace_id等.
    """
    # 方式二, 把meta信息写在 decision 对象中.
    # con, meta = open_graph_with_meta()
    # meta["redispool"] = "redispool"
    # meta["httpclient"] = "httpclient"
    # rule_basedir / "custom2.json"
    rule_path = rule_basedir / "custom2.json"
    with open(rule_path) as f:
        con = f.read()

    session = aiohttp.ClientSession()
    logger.warning(f"aiohttp session:{session}")
    context_http_client.set(session)
    # context_http_client.set(session) 必须要在 zen.ZenEngine({"customHandler": self.custom_async_handler}) 之前.
    # 否则 context_http_client 无法取到 session.
    rule_assert = RuleAssert(con)   # 缓存外层我们的规则包装对象.
    inputs = {"a": 10, "b": "cjn"}
    ### -------------------------------
    res = await rule_assert.async_evaluate(inputs, {"user": "brde@geetest.com"})
    assert res["result"]["prop1_raw"] == '{{ a + 10 }}'
    # 如果修改了规则图中的自定义节点的表达式, 需要重新修改这里的断言条件.
    assert res["result"]["prop1"]     == res["result"]["request.input"]['a'] + 10

    # 规则图中添加的元信息和自定义节点读取的元信息是否一致
    custome_request_node = res["result"]["request.node"]
    meta = rule_assert.meta
    assert meta["inputNode_name"] == custome_request_node["config"]["meta"]["inputNode_name"], "规则图中添加的元信息和自定义节点读取的元信息不一致"

    all_execd_nodes =  res["result"]["request.input"]["$nodes"]
    request_nodes_inuput = all_execd_nodes[meta["inputNode_name"]]
    del request_nodes_inuput["__meta__"]
    assert request_nodes_inuput == inputs, "输入和自定义节点中 request.input $nodes 中的输入不同"
 
    # 一般可以直接在测试函数的末尾 assert False 让测试失败, 然后使用 -l 选项输出测试失败时的局部变量的值. 方便排查问题.
    # result = res["result"]
    # assert False  # pytest tests/zen/test_zen_custom.py -k "test_custmer_node_cache_decision" -sv -l 


# @pytest.mark.asyncio
# async def test_aiohttp():
#     async with aiohttp.ClientSession() as session:
#         async with session.get('http://httpbin.org/get') as resp:
#             assert resp.status == 200
#             res = await resp.json()
#             assert res["url"] == 'http://httpbin.org/get'


# @pytest.mark.asyncio
# async def test_aiohttp2():
#     session = aiohttp.ClientSession()
#     async with session.get('http://httpbin.org/get') as resp:
#                 assert resp.status == 200
#                 res = await resp.json()
#                 assert res["url"] == 'http://httpbin.org/get'
