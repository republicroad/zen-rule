
from collections.abc import Awaitable
from typing import Any, Optional, TypedDict, Literal, TypeAlias, Union
import logging
import json
from pathlib import Path
from pprint import pprint, pformat
import asyncio
import inspect

import zen
from zen import ZenDecision
from .custom.udf_manager import udf_manager, udf, FuncArg, FuncRet
from .custom.func_engine_v2 import ast_exec, zen_custom_expr_parse
# from zen import EvaluateResponse  # cannot import
logger = logging.getLogger(__name__)

class EvaluateResponse(TypedDict):
    performance: str
    result: dict
    trace: dict


async def custom_async_handler(request):
    """
        示例自定义节点处理函数.
        todo: 是否需要包装一层异常捕获的逻辑.
    """
    # p1 = request.get_field("prop1")  # 没有prop1属性会报错.
    # await asyncio.sleep(0.1)
    logger.debug(f"request:{request}")
    logger.debug(f"request attrs:{dir(request)}")
    result = zen.evaluate_expression('rand(100)', request.input)
    logger.debug(f"return value:{result}")
    return {
        "output": {"sum": 112}
    }

def loader(key):
    """
        loader 如果 loader 是异步函数, 那么同步的 get_decision 会有问题.
        除非我们自己实现 zenRule 的 get_decision, 而不是去调用 zenEngine的 get_decision
        加载规则还是让客户自己选择实现, 然后调用 create_decision_with_cache_key 缓存下来即可.
        暂时loader选择使用同步函数.
        此方法需要被覆写.
    """
    basedir = Path(__file__).parent
    with open(basedir / "custom" / key, "r", encoding="utf8") as f:
        logger.warning(f"graph json: %s", basedir / "custom" / key)
        return f.read()


class ZenRule:
    def __init__(self, options: Optional[dict] = None) -> None: 
        # {"customHandler": self.custom_handler_v2, "loader": self.loader}
        if options:
            ### loader 如果是异步函数, ZenEngine 的 get_decision 方法就会 hang 住. 这个需要在 rust 中去调整.
            loader = options.get("loader")
            if loader and inspect.iscoroutinefunction(loader):
                raise RuntimeError("loader is not allowed using async def, please use sync function definition")
            if not options.get("customHandler"):
                options["customHandler"] = self.custom_handler_v2
            self.options = options
        else: # custom_async_handler self.custom_handler_v2
            self.options = {"customHandler": self.custom_handler_v2}
        self.engine = zen.ZenEngine(self.options)

        self.decision_cache = {}  # key -> zen decision instance
        self.custom_context = {}  # 自定义节点中的需要传入的上线文参数, 比如 trace_id 或者规则的相关元信息.

    def create_decision(self, content) -> ZenDecision:
        """
            如果不想 decision 被缓存, 那么请使用 create_decision 方法来获取 decision.
        """
        content_ = self._parse_graph_nodes(content)
        # logger.debug(f"after _parse_graph_nodes: {content_}")
        return self.engine.create_decision(content_)

    def create_decision_with_cache_key(self, key, content) -> ZenDecision:
        """
            创建规则和修改规则都是使用此方法.
        """
        if self.decision_cache.get(key):
            raise RuntimeError(f"rule key:{key} is existed, if confirm to overwrite this key,please use update_decision_with_cache_key")

        zendecision = self.create_decision(content)
        self.decision_cache[key] = zendecision
        return zendecision

    def update_decision_with_cache_key(self, key, content) -> ZenDecision:
        """
            创建规则和修改规则都是使用此方法.
        """
        if self.decision_cache.get(key):
            zendecision = self.create_decision(content)
            self.decision_cache[key] = zendecision
        else:
            raise RuntimeError(f"rule key:{key} is not existed, please use create_decision_with_cache_key")
        return zendecision

    def delete_decision_with_cache_key(self, key) -> None:
        """
            删除对应规则 decision 的缓存键.
        """
        if self.decision_cache.get(key):
            del self.decision_cache[key]
        else:
            raise RuntimeError(f"delete failed! rule key:{key} is not existed")

    def get_decision(self, key) -> ZenDecision:
        zendecision = self.decision_cache.get(key, None)
        if not zendecision:
            loader = self.options.get("loader")
            if not loader:
                raise RuntimeError(f"decision {key} not found, please create_decision_with_cache_key")
            decision_content = loader(key)
            zendecision = self.create_decision(decision_content)
            # zendecision = self.engine.get_decision(key)  # 会隐式调用 loader 函数.
            self.decision_cache[key] = zendecision
            return zendecision
        else:
            return zendecision

    def evaluate(self, key, ctx, options=None) -> EvaluateResponse:
        # return self.engine.evaluate(key, ctx, options)  # engine.evaluate 会隐式调用 loader 函数.
        decision = self.get_decision_cache(key)
        logger.debug(f"evaluate decision: {decision}")
        return decision.evaluate(ctx, options)

    def async_evaluate(self, key, ctx, options=None) -> Awaitable[EvaluateResponse]:
        # return self.engine.async_evaluate(key, ctx, options)  # engine.async_evaluate 会隐式调用 loader 函数.
        decision = self.get_decision_cache(key)
        # decision = self.engine.get_decision(key)
        logger.debug(f"async_evaluate decision: {decision}")
        return decision.async_evaluate(ctx, options)

    def _parse_graph_nodes(self, graph_content):
        rule_graph = json.loads(graph_content)
        ## 在 loader 和 create_decision 中隐式调用.
        ### 1.讲 inputNode 的 name 写到所有的customNode(自定义节点)中, 这样方便在自定义节点取得入参. 有些参数希望全局可以访问.
        input_node_name = [i.get("name") for i in rule_graph["nodes"] if i.get("type") == "inputNode"][0]
        for node in rule_graph["nodes"]:
            if node.get("type") == "customNode":
                content = node.get("content", {})
                config  = content.get("config", {})
                meta = config.get("meta", {})
                meta["inputNode_name"] = input_node_name
                node["content"]["config"]["meta"] = meta

                # config 中从 v2 spec 开始就必须有 version 字段.
                # config 中如果没有 version, 那么就是 v1 版本.
                custom_node_version = node["content"]["config"].get("version", "v1")
                if custom_node_version  == "v1":
                    ### 将自定义节点格式v1转换为 v2 格式.
                    v1_inputs = node["content"]["config"].get("inputs", [])
                    if v1_inputs:
                        expressions = []
                        for func_item in v1_inputs:
                            id = func_item["id"]
                            key = func_item["key"]
                            func_name = func_item["funcmeta"]["name"]
                            v1_arg_exprs = func_item["arg_exprs"]
                            args = [[i["arg_name"], v1_arg_exprs[i["arg_name"]]] for i in func_item["funcmeta"]["arguments"]]
                            args_ = ",".join([j for _, j in args])
                            func_call = f"{func_name}({args_})"
                            d = {
                                "id": id,
                                "key": key,
                                "value": func_call
                            }
                            expressions.append(d)

                        # 将 v1 格式转化为 v2 的格式. 然后统一使用解析, 将函数调用表达式得到的抽象语法树保存下来.
                        node["content"]["config"]["expressions"] = expressions
                        node["content"]["config"]["version"] = "v2"
                        # 是否删除 inputs 字段?

                ### 将自定义节点中的表达式进行解析, 解析出其中表达式函数中的自定义函数(udf)的执行逻辑, 执行顺序.
                expr_asts = []
                custom_expressions = node["content"]["config"].get("expressions")
                if custom_expressions:
                    for func_item in custom_expressions:
                        item = {**func_item}
                        item["value"] = zen_custom_expr_parse(func_item["value"])
                        expr_asts.append(item)
                    node["content"]["config"]["expr_asts"] = expr_asts

        logger.debug(f"rule_graph:{pformat(rule_graph)}")
        return json.dumps(rule_graph)

    @classmethod
    async def custom_handler_v1(cls, request):
        logger.debug("custom node use custom_handler_v1")
        funcs = request.node["config"].get("inputs", [])
        trans_func = lambda x: zen.evaluate_expression(x, request.input)
        res = {}
        bar = []
        for item in funcs:
            funcmeta = item["funcmeta"]
            funcname = funcmeta["name"]
            func_variables = {k: v for k, v in item["arg_exprs"].items()}
            vars2value = {k: trans_func(v) for k, v in func_variables.items()}
            env = {
                "node_id": request.node["id"],  ## 隔离 graph 中的节点
                "func_id": item["id"],  ## 隔离每一个计算逻辑.
                "meta": request.node["config"].get("meta", {}),
                **vars2value,
            }
            # env.update(vars2value)
            bar.append((item["key"], funcname, env))
        results = await asyncio.gather(*[udf_manager.call_udf(_[1], *_[2], **_[2]) for _ in bar])
        for key, result in zip([_[0] for _ in bar], results):
            res[key] = result
        res.update({k: v for k, v in request.input.items() if k != "$nodes"})
        logger.warning(f"custom v1 result:{res}")
        return {
            "output": res
        }

    @classmethod
    async def custom_handler_v2(cls, request):
        """
            v2 支持字面量的自定义函数的表达式, 和普通函数类似, 也支持函数表达式的嵌套调用.
            参考 src/custom/custom_v2.json 中的示例.
            兼容 custom_handler_v1 元数据定义和执行逻辑.
        """
        # logger.debug(f"request.node:{request.node}")
        # graph json 要放在 zen engine zen rule 中进行解析, 解析的自定义表达式函数再使用自定义函数表达式来执行.
        expr_asts = request.node["config"].get("expr_asts", [])
        # if not expr_asts and request.node["config"].get("inputs"):  # 没有抽象语法树的解析, 那么使用 custom_handler_v1 版本.
        #     logger.debug("custom node use custom_handler_v1")
        #     return await cls.custom_handler_v1(request)
        logger.debug("custom node use custom_handler_v2")
        coro_funcs = []
        results = {}
        context = {
            "node_id": request.node["id"],  ## 隔离 graph 中的节点
            "meta": request.node["config"].get("meta", {}),
        }
        for item in expr_asts:
            # result = await ast_exec(item, request.input, context)
            # out_res[key] = result
            # coro_funcs.append(ast_exec(item["value"], request.input, context))
            coro_funcs.append(ast_exec(item, request.input, context))
        _results = await asyncio.gather(*coro_funcs)
        results = {k["key"]: v for k, v in zip(expr_asts, _results)}
        results.update({k: v for k, v in request.input.items() if k != "$nodes"})
        logger.debug(results)

        return {
            "output": results
        }

    def get_decision_cache(self, key):
        return self.decision_cache.get(key, None)

__all__ = [
    ZenRule,
    udf,
    udf_manager,
    FuncArg,
    FuncRet,
]