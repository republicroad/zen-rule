
from collections.abc import Awaitable
from typing import Any, Optional, TypedDict, Literal, TypeAlias, Union
import logging
import json
from pathlib import Path
from pprint import pprint, pformat
import asyncio
import zen
from zen import ZenDecision
from .custom.udf_manager import udf_manager
from .custom.func_engine_v2 import ast_exec, zen_custom_expr_parse
# from zen import EvaluateResponse
logger = logging.getLogger(__name__)

EvaluateResponse = {}

# class ZenEngine:
#     def __init__(self, options: Optional[dict] = None) -> None: ...

#     def evaluate(self, key: str, context: ZenContext,
#                  options: Optional[DecisionEvaluateOptions] = None) -> EvaluateResponse: ...

#     def async_evaluate(self, key: str, context: ZenContext, options: Optional[DecisionEvaluateOptions] = None) -> \
#             Awaitable[EvaluateResponse]: ...

#     def create_decision(self, content: ZenDecisionContentInput) -> ZenDecision: ...

#     def get_decision(self, key: str) -> ZenDecision: ...


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


class ZenRule:
    def __init__(self, options: Optional[dict] = None) -> None: 
        # options 主要有 loader 和 custom_hander 两个回调函数.
        # self.options_cache = {}
        # self.options_dict = options_dict
        if options:
            ### todo assert loader function 是同步函数.
            ###      或者, 是否需要loader 函数.
            self.options = options
        else: # custom_async_handler self.custom_handler_v2
            self.options = {"customHandler": self.custom_handler_v2, "loader": self.loader}
        # {"customHandler": self.custom_handler}
        self.engine = zen.ZenEngine(self.options)
        # decision 和 自定义节点中的 meta 信息是否需要包装在一个实例中???
        self.decision_cache = {}  # key -> zen decision instance
        self.meta = {}  # key -> rule meta dict 

    def loader(self, key):
        """
            loader 如果 loader 是异步函数, 那么同步的 get_decision 会有问题.
            除非我们自己实现 zenRule 的 get_decision, 而不是去调用 zenEngine的 get_decision
            加载规则还是让客户自己选择实现, 然后调用 create_decision_with_cache_key 缓存下来即可.
            暂时loader选择使用同步函数.
            此方法需要被覆写.
            todo: 考虑是否需要异步.
        """
        basedir = Path(__file__).parent
        with open(basedir / "custom" / key, "r", encoding="utf8") as f:
            logger.warning(f"graph json: %s", basedir / "custom" / key)
            return f.read()

    def create_decision(self, content) -> ZenDecision:
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
            # self.engine.get_decision
            decision_content = self.loader(key)
            zendecision = self.create_decision(decision_content)
            # zendecision = self.engine.get_decision(key)  # 会隐式调用 loader 函数.
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
        # decision = self.engine.get_decision(key)
        logger.debug(f"decision: {decision}")
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

                ### 2.将自定义节点中的表达式进行解析, 解析出其中表达式函数中的自定义函数(udf)的执行逻辑, 执行顺序.
                expr_asts = []
                custom_expressions = node["content"]["config"].get("expressions")
                if custom_expressions:
                    for i in custom_expressions:
                        item = {**i}
                        item["value"] = zen_custom_expr_parse(i["value"])
                        expr_asts.append(item)
                    node["content"]["config"]["expr_asts"] = expr_asts

                ### 3.将自定义节点格式v1转换为 v2 格式. todo.
            else:
                meta = {}
        # logger.debug(f"rule_graph:{pformat(rule_graph)}")
        return json.dumps(rule_graph)

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
                "meta": request.node["config"].get("meta", {}),
                **vars2value,
            }
            # env.update(vars2value)
            bar.append((item["key"], funcname, env))
        results = await asyncio.gather(*[udf_manager.call_udf(_[1], *_[2], **_[2], **kwargs) for _ in bar])
        for key, result in zip([_[0] for _ in bar], results):
            res[key] = result
        res.update({k: v for k, v in request.input.items() if k != "$nodes"})
        logger.warning(f"custom v1 result:{res}")
        return {
            "output": res
        }

    async def custom_handler_v2(self, request):
        """
            v2 支持字面量的自定义函数的表达式, 和普通函数类似, 也支持函数表达式的嵌套调用.
            参考 src/custom/custom_v2.json 中的示例.
            兼容 custom_handler_v1 元数据定义和执行逻辑.
        """
        # logger.debug(f"request.node:{request.node}")
        # graph json 要放在 zen engine zen rule 中进行解析, 解析的自定义表达式函数再使用自定义函数表达式来执行.
        expr_asts = request.node["config"].get("expr_asts", [])
        if not expr_asts:  # 没有抽象语法树的解析, 那么使用 custom_handler_v1 版本.
            return await self.custom_handler_v1(request)

        coro_funcs = []
        results = {}
        context = {
            "node_id": request.node["id"],  ## 隔离 graph 中的节点
            "meta": request.node["config"].get("meta", {}),
        }
        for item in expr_asts:
            # result = await ast_exec(item, request.input, context)
            # out_res[key] = result
            coro_funcs.append(ast_exec(item["value"], request.input, context))
        _results = await asyncio.gather(*coro_funcs)
        results = {k["key"]: v for k, v in zip(expr_asts, _results)}
        logger.debug(results)

        return {
            "output": results
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
