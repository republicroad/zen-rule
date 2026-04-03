
from typing import Any, Optional, TypedDict, Literal, Awaitable, Union
import logging
import json
import re
from pathlib import Path
from pprint import pprint, pformat
import asyncio
import inspect

import zen
from zen import ZenDecision, ZenDecisionContent
from .udf import UDFManager, udf_manager, udf, FuncArg, FuncRet
from .contrib import *
# from zen import EvaluateResponse  # cannot import
# zen_exprs_eval = lambda x, input: zen.evaluate_expression(x, input)
logger = logging.getLogger(__name__)


def zen_exprs_eval(expr, input):
    try:
        return zen.evaluate_expression(expr, input)
    except Exception as e:
        logger.error("Error occurred while evaluating zen expression: %s", e, exc_info=True)
        return None


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
    logger.debug("request: %s", request)
    logger.debug("request attrs: %s", dir(request))
    result = zen.evaluate_expression('rand(100)', request.input)
    logger.debug("return value: %s", result)
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
        logger.warning("graph json: %s", basedir / "custom" / key)
        return f.read()


class ZenRule:
    custom_handler_meta = "__meta__"
    udf_manager = udf_manager
    def __init__(self, options: Optional[dict] = None) -> None: 
        # {"customHandler": self.custom_handler_v3, "loader": self.loader}
        if options:
            ### loader 如果是异步函数, ZenEngine 的 get_decision 方法就会 hang 住. 这个需要在 rust 中去调整.
            loader = options.get("loader")
            if loader and inspect.iscoroutinefunction(loader):
                raise RuntimeError("loader is not allowed using async def, please use sync function definition")
            if not options.get("customHandler"):
                options["customHandler"] = self.custom_handler_v3
            self.options = options
        else: # custom_async_handler self.custom_handler_v3
            self.options = {"customHandler": self.custom_handler_v3}
        self.engine = zen.ZenEngine(self.options)

        self.decision_cache = {}  # key -> zen decision instance
        self.custom_context = {}  # 自定义节点中的需要传入的上线文参数, 比如 trace_id 或者规则的相关元信息.
        self.content_cache = {}

    def create_decision(self, content) -> ZenDecision:
        """
            如果不想 decision 被缓存, 那么请使用 create_decision 方法来获取 decision.
        """
        content_ = self.graph_addons(content)
        # logger.debug("after graph_addons: %s", content_)
        zen_decision_content = ZenDecisionContent(content_)
        return self.engine.create_decision(zen_decision_content)

    def create_decision_with_cache_key(self, key, content) -> ZenDecision:
        """
            创建规则和修改规则都是使用此方法.
        """
        if self.decision_cache.get(key):
            raise RuntimeError(f"rule key:{key} is existed, if confirm to overwrite this key,please use update_decision_with_cache_key")

        zendecision = self.create_decision(content)
        self.decision_cache[key] = zendecision
        self.content_cache[key] = content
        return zendecision

    def update_decision_with_cache_key(self, key, content) -> ZenDecision:
        """
            创建规则和修改规则都是使用此方法.
        """
        if self.decision_cache.get(key):
            zendecision = self.create_decision(content)
            self.decision_cache[key] = zendecision
            self.content_cache[key] = content
        else:
            raise RuntimeError(f"rule key:{key} is not existed, please use create_decision_with_cache_key")
        return zendecision

    def delete_decision_with_cache_key(self, key) -> None:
        """
            删除对应规则 decision 的缓存键.
        """
        if self.decision_cache.get(key):
            del self.decision_cache[key]
            del self.content_cache[key]
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
            self.content_cache[key] = decision_content
            return zendecision
        else:
            return zendecision

    def evaluate(self, key, ctx, options=None) -> EvaluateResponse:
        # return self.engine.evaluate(key, ctx, options)  # engine.evaluate 会隐式调用 loader 函数.
        decision = self.get_decision_cache(key)
        logger.debug("evaluate decision: %s", decision)
        return decision.evaluate(ctx, options)

    def async_evaluate(self, key, ctx, options=None) -> Awaitable[EvaluateResponse]:
        # return self.engine.async_evaluate(key, ctx, options)  # engine.async_evaluate 会隐式调用 loader 函数.
        decision = self.get_decision_cache(key)
        # decision = self.engine.get_decision(key)
        logger.debug("async_evaluate decision: %s", decision)
        return decision.async_evaluate(ctx, options)

    def graph_addons(self, graph_content):
        if isinstance(graph_content, dict):
            rule_graph = graph_content
        elif isinstance(graph_content, str):
            try:
                rule_graph = json.loads(graph_content)
            except Exception as e:
                raise ValueError(f"Invalid JSON string: {e}")
        else:
            raise TypeError(f"Expected str or dict, got {type(graph_content).__name__}")
        
        ## 在 loader 和 create_decision 中隐式调用.
        ### 1.讲 inputNode 的 name 写到所有的customNode(自定义节点)中, 这样方便在自定义节点取得入参. 有些参数希望全局可以访问.
        _input_node = [i.get("name") for i in rule_graph["nodes"] if i.get("type") == "inputNode"]
        input_node = [i for i in _input_node if i]  # 过滤掉 None 或 空字符串
        input_node_name = input_node[0] if input_node else ""
        rule_id = rule_graph.get("id", "")
        rule_meta = rule_graph.get("metadata", {})
        rule_meta["namespace"] = rule_id
        rule_meta["inputNode_name"] = input_node_name
        for node in rule_graph["nodes"]:
            if node.get("type") == "customNode":
                content = node.get("content", {})
                config  = content.get("config", {})
                ch_meta = config.get(self.custom_handler_meta, {}) or config.get("meta", {})
                ch_meta.update(rule_meta)
                node["content"]["config"][self.custom_handler_meta] = ch_meta
                # 自定节点默认设置为 passThrough = True，默认是透传行为
                if node["content"]["config"].get("passThrough") is None:
                    node["content"]["config"]["passThrough"] = True

                ### 将自定义节点中的表达式进行解析, 解析出其中表达式函数中的自定义函数(udf)的执行逻辑, 执行顺序.
                expr_asts = []
                custom_expressions = node["content"]["config"].get("expressions")
                if custom_expressions:
                    for func_item in custom_expressions:
                        item = {**func_item}
                        item["value"] = self.parse_oprator_expr_v3(func_item["value"])
                        expr_asts.append(item)
                    node["content"]["config"]["expr_asts"] = expr_asts

        logger.debug("rule_graph: %s", pformat(rule_graph))
        return json.dumps(rule_graph)

    @classmethod
    async def custom_handler_v3(cls, request):
        """
            v3 版本的自定义节点处理函数:
            为了简化决策引擎的使用, 决策引擎决定按照不同自定义节点算子的作用对自定义节点进行分类.
            v3 版本不支持 自定义算子 和 zen 表达式函数混合调用, 也不支持 自定义算子的嵌套调用.
            为了方便对自定义算子的参数中的复杂 zen 表达式进行解析，拟支持如下两种格式:

            foo;;myvar;;bar(zoo('fccdjny',6, 3.14),'a');; a+string(xxx)

            foo(myvar,bar(zoo('fccdjny',6, 3.14),'a'), a+string(xxx))

            这两种解析后得到的结果如下(json数组):
            ['foo', 'myvar', "bar(zoo('fccdjny',6, 3.14),'a')", ' a+string(xxx)']

            表示 foo 算子传入了 三个参数:
            1. zen 表达式变量 myvar
            2. zen 表达式函数 bar(zoo('fccdjny',6, 3.14),'a')
            3. zen 表达式 a+string(xxx)
        """
        # logger.debug(f"request.node: \n%s", pformat(request.node))
        # logger.debug(f"request.input:\n%s", pformat(request.input))
        # graph json 要放在 zen engine zen rule 中进行解析, 解析的自定义表达式函数再使用自定义函数表达式来执行.
        expr_asts = request.node["config"].get("expr_asts", [])
        inputField = request.node.get("config",{}).get("inputField")
        outputPath = request.node.get("config",{}).get("outputPath")
        passThrough = request.node.get("config",{}).get("passThrough")
        __meta__ = request.node["config"].get(cls.custom_handler_meta, {})
        logger.debug("custom node use custom_handler_v3")
        coro_funcs = []
        results = {}
        context = {
            "node_id": request.node["id"],  ## 隔离 graph 中的节点
            cls.custom_handler_meta: __meta__,
            "passThrough": passThrough,
            "inputField": inputField,
            "outputPath": outputPath,
        }

        for item in expr_asts:
            coro_funcs.append(cls.engine_v3(item, request.input, context))
        _results = await asyncio.gather(*coro_funcs)
        results = {k["key"]: v for k, v in zip(expr_asts, _results)}
        if passThrough:
            results.update({k: v for k, v in request.input.items() if k != "$nodes"})
        else:
            pass
        
        if outputPath:
            # get nested path like a.b.c for dict a["b"]["c"]
            results = zen.evaluate_expression(f"{outputPath}={'_'}", {"_": results})  # 先创建路径
        logger.debug("custom v3 result: %s", results)
        return {
            "output": results
        }

    @classmethod
    # async def engine_v3(cls, item, node_input, context):
    async def engine_v3(cls, exec_expr, node_input, context={}): 
        """
            item 代表自定义节点中的一个函数
            node_input 是此自定义节点的入参
            context 是额外传递的上下文(希望未来 zen-engine 直接支持此参数, 用于传入一些全局参数, 比如服务实例, trace_id等)

            exec_expr:
            ['foo', 'myvar', "bar(zoo('fccdjny',6, 3.14),'a')", ' a+string(xxx)']
        """
        try:
            expr_id = exec_expr["id"]
            expr_ast = exec_expr["value"]
            expr_key = exec_expr["key"]
            
            func_name, *op_arg_expressions  = expr_ast
            logger.debug("node_input: %s  context: %s", node_input, context)
            logger.debug("func: %s  literal args: %s", func_name, op_arg_expressions)
            inputfield = context.get("inputField")
            f = cls.udf_manager.udf_function_schema(func_name)  # 需要在这里设计一个函数执行异常时返回的值么.
            if f:
                ## 变量求值
                args = [zen_exprs_eval(f"{inputfield}.{i}" if inputfield else f"{i}", node_input) for i in op_arg_expressions]
                ## 绑定参数和形参, 并转化参数值的类型
                logger.debug("func: %s args evaluated: %s", func_name, args)
                oprator_kwargs = cls.udf_manager.func_bind_params(func_name, args)
                logger.debug("func: %s kwargs: %s", func_name, oprator_kwargs)
                kwargs = {
                    **oprator_kwargs,
                    **context,
                    "func_id": expr_id,
                    "expr_id": expr_id,
                    "_node_input_": node_input
                }
                result = await cls.udf_manager(func_name, *(), **kwargs)
            else:
                if func_name:
                    result = {"error": f"udf {func_name} not found"}
                else:
                    result = {"error": "empty udf name not allowed"}
            logger.debug("%s calling result->: %s", func_name, result)
            return result
        except Exception as e:
            logger.error(e, exc_info=True)
            # todo: 异常情况下自定义算子返回什么, 空字符串还是null.
            return None

    def get_decision_cache(self, key):
        return self.decision_cache.get(key, None)

    def get_content_cache(self, key):
        return self.content_cache.get(key, None)

    def parse_oprator_expr_v3(self, expr):
        """
            v3自定义节点中的算子 oprater 调用支持两种格式:
            1.  ;; 当作起始符号且作为oprater及参数的分隔符
                foo;;myvar ;;max([5,8,2,11, 7]);;rand(100)+120;;3+4;; 'singel;;quote' ;;"double;;quote" ;;`backquote;; ${bar}`

            2. 使用函数调用嵌套(todo:以后支持)
                foo(myvar,bar(zoo('fccdjny',6, 3.14),'a'), a+string(xxx))
        """
        # 不能简单使用字符串分割, 因为字符串中可能会有分隔符的模式出现, 比如:
        # foo ;; myvar ;; bar(zoo('fccd;;jny',6, 3.14),'a');; a+string(xxx)
        # foo;;myvar;;max([5, 8, 2, 11, 7]);;rand(100);; 'fccd;;jny' ;;3+4
        # expr.split(";;")
        # pattern = r""";;(?=(?:[^"'`]*["'`][^"'`]*["'`])*[^"'`]*$)"""
        pattern = re.compile(r""";;(?=(?:[^"'`]*["'`][^"'`]*["'`])*[^"'`]*$)""")
        # To split the string by these semicolon:
        _parts = re.split(pattern, expr)
        parts = [i.strip() for i in _parts]  # 去掉表达式前后的空格
        return parts

    @classmethod
    def udf_function_schema_tools(cls):
        return cls.udf_manager.udf_function_schema_tools()


__all__ = [
    ZenRule,
    udf,
    udf_manager,
    FuncArg,
    FuncRet,
]