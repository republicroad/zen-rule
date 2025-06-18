
from collections.abc import Awaitable
from typing import Any, Optional, TypedDict, Literal, TypeAlias, Union
import logging
import json
from pathlib import Path
import asyncio
import zen
from zen import EvaluateResponse, ZenDecision
logger = logging.getLogger(__name__)
print(zen.ZenEngine)

# class ZenEngine:
#     def __init__(self, options: Optional[dict] = None) -> None: ...

#     def evaluate(self, key: str, context: ZenContext,
#                  options: Optional[DecisionEvaluateOptions] = None) -> EvaluateResponse: ...

#     def async_evaluate(self, key: str, context: ZenContext, options: Optional[DecisionEvaluateOptions] = None) -> \
#             Awaitable[EvaluateResponse]: ...

#     def create_decision(self, content: ZenDecisionContentInput) -> ZenDecision: ...

#     def get_decision(self, key: str) -> ZenDecision: ...

class zenRule:
    def __init__(self, options: Optional[dict] = None) -> None: 
        # options 主要有 loader 和 custom_hander 两个回调函数.
        # self.options_cache = {}
        # self.options_dict = options_dict
        self.options = options
        # {"customHandler": self.custom_handler}
        self.engine = zen.ZenEngine(self.options)
        # decision 和 自定义节点中的 meta 信息是否需要包装在一个实例中???
        self.decision_cache = {}  # key -> zen decision instance
        self.meta = {}  # key -> rule meta dict 
        self.udf_manager = {}
        self.call_udf = lambda x: x

    def create_decision(self, content) -> ZenDecision:
        content_ = self._parse_graph_nodes(content)
        return self.engine.create_decision(content_)

    def get_decision(self, key) -> ZenDecision:
        zendecision = self.decision_cache.get(key, None)
        if not zendecision:
            zendecision = self.engine.get_decision(key)  # 会隐式调用 loader 函数.
            self.decision_cache[key] = zendecision
            return zendecision
        else:
            return zendecision

    def evaluate(self, key, ctx, options=None) -> EvaluateResponse:
        # return self.engine.evaluate(key, ctx, options)  # engine.evaluate 会隐式调用 loader 函数.
        decision = self.get_decision(key)
        return decision.evaluate(ctx, options)

    def async_evaluate(self, key, ctx, options=None) -> Awaitable[EvaluateResponse]:
        # return self.engine.async_evaluate(key, ctx, options)  # engine.async_evaluate 会隐式调用 loader 函数.
        decision = self.get_decision(key)
        return decision.async_evaluate(ctx, options)

    def _parse_graph_nodes(self, rule_graph):
        ## 在 loader 和 create_decision 中隐式调用.
        ### 1.讲 inputNode 的 name 写到所有的customNode(自定义节点)中, 这样方便在自定义节点取得入参. 有些参数希望全局可以访问.
        input_node_name = [i.get("name") for i in rule_graph['content']["nodes"] if i.get("type") == "inputNode"][0]
        for node in rule_graph['content']["nodes"]:
            if node.get("type") == "customNode":
                content = node.get("content", {})
                config  = content.get("config", {})
                meta = config.get("meta", {})
                meta["inputNode_name"] = input_node_name
                node["content"]["config"]["meta"] = meta
            else:
                meta = {}
        
        ### 2.将自定义节点中的表达式进行解析, 解析出其中表达式函数中的自定义函数(udf)的执行逻辑, 执行顺序.

        return json.dumps(rule_graph['content'])

    async def custom_handler_v1(self, request, **kwargs):
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
                "meta": request.node["config"].get("meta", {})
            }
            env.update(vars2value)
            bar.append((item["key"], funcname, env))
        results = await asyncio.gather(*[udf_manager.call_udf(_[1], *_[2], **_[2], **kwargs) for _ in bar])
        for key, result in zip([_[0] for _ in bar], results):
            res[key] = result
        res.update({k: v for k, v in request.input.items() if k != "$nodes"})
        return {
            "output": res
        }

    async def custom_handler_v2(self, request, **kwargs):
        """
            重新设计自定义函数调用逻辑, 最好实现兼容 custom_handler_v1 的逻辑.
        """
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
                "meta": request.node["config"].get("meta", {})
            }
            env.update(vars2value)
            bar.append((item["key"], funcname, env))
        results = await asyncio.gather(*[udf_manager.call_udf(_[1], *_[2], **_[2], **kwargs) for _ in bar])
        for key, result in zip([_[0] for _ in bar], results):
            res[key] = result
        res.update({k: v for k, v in request.input.items() if k != "$nodes"})
        return {
            "output": res
        }

    # async def rule_exec(self, data_dict, rule_id, trace, db, **kwargs):
    #     if rule_id in self.cache_set:
    #         rule_cache = self.cache_set[rule_id]
    #         decision = rule_cache['decision']
    #     else:
    #         rule_manager = await self.create_rule_manager(data_dict, rule_id, db, **kwargs)
    #         decision = rule_manager.decision
    #     logger.debug('rule exec info: rule_id:{}, rule_manager:{} ,decision:{}'.format(rule_id, self, decision))
    #     result = await decision.async_evaluate(data_dict['context'], {"trace": trace})
    #     return result

    # def update_rule_manager(self, rule_id):
    #     cache_dict = {
    #         'meta': self.meta,
    #         'engine': self.engine,
    #         'decision': self.decision
    #     }
    #     self.cache_set[rule_id] = cache_dict

    # def delete_rule_manager(self, rule_id):
    #     if rule_id in self.cache_set:
    #         del self.cache_set[rule_id]