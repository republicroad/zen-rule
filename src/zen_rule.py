
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
# from zen import EvaluateResponse
logger = logging.getLogger(__name__)
print(zen.ZenEngine)
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
    # p1 = request.get_field("prop1")
    # await asyncio.sleep(0.1)
    print("request:", request)
    print("request attrs:", dir(request))
    result = zen.evaluate_expression('rand(100)', request.input)
    print("return value:", result)
    return {
        "output": {"sum": 112}
    }


class zenRule:
    def __init__(self, options: Optional[dict] = None) -> None: 
        # options 主要有 loader 和 custom_hander 两个回调函数.
        # self.options_cache = {}
        # self.options_dict = options_dict
        if options:
            self.options = options
        else: # custom_async_handler self.custom_handler_v2
            self.options = {"customHandler": self.custom_handler_v2, "loader": self.loader}
        # {"customHandler": self.custom_handler}
        self.engine = zen.ZenEngine(self.options)
        # decision 和 自定义节点中的 meta 信息是否需要包装在一个实例中???
        self.decision_cache = {}  # key -> zen decision instance
        self.meta = {}  # key -> rule meta dict 
        self.udf_manager = {}
        self.call_udf = lambda x: x

    def loader(self, key):
        """
            loader 如果 loader 是异步函数, 那么同步的 get_decision 会有问题.
            除非我们自己实现 zenRule 的 get_decision, 而不是去调用 zenEngine的 get_decision
            加载规则还是让客户自己选择实现, 然后调用 create_decision_with_cache_key 缓存下来即可.
            暂时loader选择使用同步函数.
            todo: 考虑是否需要异步.
        """
        basedir = Path(__file__).parent
        with open(basedir / "custom" / key, "r", encoding="utf8") as f:
            logger.warning(f"graph json: %s", basedir / "custom" / key)
            return f.read()

    def create_decision(self, content) -> ZenDecision:
        content_ = self._parse_graph_nodes(content)
        return self.engine.create_decision(content_)

    def create_decision_with_cache_key(self, key, content) -> ZenDecision:
        content_ = self._parse_graph_nodes(content)
        zendecision =  self.engine.create_decision(content_)
        self.decision_cache[key] = zendecision
        return zendecision

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
        logger.debug(f"decision: {decision}")
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
                "meta": request.node["config"].get("meta", {}),
                **vars2value,
            }
            # env.update(vars2value)
            bar.append((item["key"], funcname, env))
        results = await asyncio.gather(*[udf_manager.call_udf(_[1], *_[2], **_[2], **kwargs) for _ in bar])
        for key, result in zip([_[0] for _ in bar], results):
            res[key] = result
        res.update({k: v for k, v in request.input.items() if k != "$nodes"})
        return {
            "output": res
        }

    async def custom_handler_v2(self, request):
        """
            重新设计自定义函数调用逻辑, 最好实现兼容 custom_handler_v1 的逻辑.
        """
        # graph json 要放在 zen engine zen rule 中进行解析, 解析的自定义表达式函数再使用自定义函数表达式来执行.
        expr_asts = request.node["config"].get("expr_asts", [])
        if not expr_asts:  # 没有抽象语法树的解析, 那么使用 custom_handler_v1 版本.
            return await self.custom_handler_v1(request)

        coro_l = []
        out_res = {}
        context = {
            "node_id": request.node["id"],  ## 隔离 graph 中的节点
            "meta": request.node["config"].get("meta", {}),
        }
        for item in expr_asts:
            id  = item["id"]
            key = item["key"]
            # ast   = item["value"]  # ast for functions eval orders.
            # result = await ast_exec(item, request.input, context)
            # out_res[key] = result
            # todo: 这里改为用 asyncio.gather 来实现并发执行多个函数表达式.
            # 这样可以提高自定义节点的执行性能.
            coro_l.append(ast_exec(item, request.input, context))
        results = await asyncio.gather(*coro_l)
        out_res = {k["key"]: v for k, v in zip(expr_asts, results)}
        logger.warning(out_res)
        return {
            "output": out_res
        }


args_expr_eval = lambda x, input: zen.evaluate_expression(x, input)


async def ast_exec(expr_ast, args_input, context={}):
    id  = expr_ast["id"]
    key = expr_ast["key"]
    ast   = expr_ast["value"]  # ast for functions eval orders.
    env = {}  # ast 求值时, 函数值暂存在此字典, 用于嵌套函数传参.
    # logger.debug(f"{pformat(ast)}")
    for func in ast:  # 执行一个嵌套函数表达式.
        ### 下列代码需要封装为一个执行引擎.
        logger.debug(f"current env: {env}")
        if func["ns"] == "udf":
            # logger.warning(f"udf expression: {func}")
            func_name = func["name"]
            args = []
            # 变量类型需要使用 zen expression 求值.
            for arg, t in func["args"]:
                if t == "func_value":
                    args.append(env.get(arg["id"]))
                elif t == "var":
                    args.append(args_expr_eval(arg, args_input))
                elif t == "string":
                    args.append(args_expr_eval(arg, args_input))
                else:  # ["int", "float"]
                    args.append(arg)
           
            kwargs = {
                **context,
                "func_id": func["id"],
            }
            result = await udf_manager(func["name"], *args, **kwargs)
            logger.warning(f"{func_name}({args}) ->: {result}")
            env[func["id"]] = result
        elif func["ns"] == "":
            func_name = func["name"]
            args = func["args"]
            # 需要判断参数是嵌套函数的情况.
            args = [env.get(func["id"]) if t == "func_value" else str(arg) for arg, t in args]
            # 要判断 args 中是否还嵌套函数.
            func_call_args = ",".join(args)
            zen_expr = f"{func_name}({func_call_args})"
            result = zen.evaluate_expression(zen_expr, args_input)
            logger.warning(f"{zen_expr} ->: {result}")
            # 默认使用 zen 表达式.
            env[func["id"]] = result
        else:
            raise RuntimeError(f'自定义函数{func["name"]}表达式不支持')

    return result

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