
from typing import Any, Optional, TypedDict, Literal, Awaitable, Union
import logging
import json
from pathlib import Path
from pprint import pprint, pformat
import asyncio
import inspect

import zen
from zen import ZenDecision
from .custom.udf_manager import udf_manager, udf, FuncArg, FuncRet
from .custom import op_args_combination, parse_oprator_expr_v3
# from zen import EvaluateResponse  # cannot import
zen_exprs_eval = lambda x, input: zen.evaluate_expression(x, input)
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
        # logger.debug(f"after graph_addons: {content_}")
        return self.engine.create_decision(content_)

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
        logger.debug(f"evaluate decision: {decision}")
        return decision.evaluate(ctx, options)

    def async_evaluate(self, key, ctx, options=None) -> Awaitable[EvaluateResponse]:
        # return self.engine.async_evaluate(key, ctx, options)  # engine.async_evaluate 会隐式调用 loader 函数.
        decision = self.get_decision_cache(key)
        # decision = self.engine.get_decision(key)
        logger.debug(f"async_evaluate decision: {decision}")
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
        input_node_name = [i.get("name") for i in rule_graph["nodes"] if i.get("type") == "inputNode"][0]
        for node in rule_graph["nodes"]:
            if node.get("type") == "customNode":
                content = node.get("content", {})
                config  = content.get("config", {})
                meta = config.get("meta", {})
                meta["inputNode_name"] = input_node_name
                node["content"]["config"]["meta"] = meta
                # 自定节点默认设置为 passThrough = True，默认是透传行为
                if node["content"]["config"].get("passThrough") is None:
                    node["content"]["config"]["passThrough"] = True
                node["content"]["config"]["version"] = "v3"
                ## 兼容旧版编辑器自定义节点执行逻辑, 将 v1 版本的自定义节点转化为 v3 版本.
                self.mix_custom_node_v1_and_v3(node)
                ### 将自定义节点中的表达式进行解析, 解析出其中表达式函数中的自定义函数(udf)的执行逻辑, 执行顺序.
                expr_asts = []
                custom_expressions = node["content"]["config"].get("expressions")
                if custom_expressions:
                    for func_item in custom_expressions:
                        item = {**func_item}
                        item["value"] = parse_oprator_expr_v3(func_item["value"])
                        expr_asts.append(item)
                    node["content"]["config"]["expr_asts"] = expr_asts

        logger.debug(f"rule_graph:{pformat(rule_graph)}")
        return json.dumps(rule_graph)

    def mix_custom_node_v1_and_v3(self, node):
        """
            运行时: 将 v1 版本的自定义节点转化为 v3 版本, v1 中新的节点添加到 v3 函数中, v1 和v3相同的节点则覆盖 v3 的节点.
        """
        v3_funcs = node["content"]["config"].get("expressions", [])
        v3_func_ids = {i["id"] for i in v3_funcs}
        v1_funcs = node["content"]["config"].get("inputs", [])
        v1_func_ids = {i["id"] for i in v1_funcs}

        if not v3_funcs:
            node["content"]["config"]["expressions"] = []
        if not v1_funcs:
            node["content"]["config"]["inputs"] = []

        for func_item in node["content"]["config"]["inputs"]:  # 遍历 v1 的输入函数 v3_func_ids
            func_name = func_item["funcmeta"]["name"]
            v1_arg_exprs = func_item["arg_exprs"]
            args = [[i["arg_name"], v1_arg_exprs[i["arg_name"]]] for i in func_item["funcmeta"]["arguments"]]
            args_ = ";;".join([j for _, j in args])
            func_call = f"{func_name};;{args_}"
            d = {
                "id": func_item["id"],
                "key": func_item["key"],
                "value": func_call
            }
            ## 如果当前 v1_func 的 id 不在 v3_func_ids 中, 那么就添加到 v3 的func表达式中
            if func_item["id"] not in v3_func_ids:
                node["content"]["config"]["expressions"].append(d)
            else:
                # 如果在 v3_func_ids 中, 那么更新此 v3_func
                for item in node["content"]["config"]["expressions"]:
                    if item["id"] == func_item["id"]:
                        item.update(d)

    def custom_node_v1_to_v3(self, node):
        """
            保存规则: 将 v1 版本的自定义节点转化为 v3 版本
        """
        if not node["content"]["config"].get("inputs", []):
            node["content"]["config"]["inputs"] = []
        node["content"]["config"]["expressions"] = []   ## 先清空 v3 的表达式, 然后再添加 v1 的表达式.
        for func_item in node["content"]["config"]["inputs"]:  # 遍历 v1 的输入函数 v3_func_ids
            if func_item.get("funcmeta") is None:
                continue
            func_name = func_item["funcmeta"]["name"]
            v1_arg_exprs = func_item["arg_exprs"]
            args = []
            for i in func_item["funcmeta"]["arguments"]:
                if not isinstance(v1_arg_exprs, dict):
                    continue
                # 如果 v1_arg_exprs 没有 i["arg_name"] 这个key, 会报错.
                # 需要考虑下这种情况么?
                # 这种情况则从funcmeta 中的arguments 中取默认值
                if v1_arg_exprs.get(i["arg_name"]) is None:
                    args.append([i["arg_name"], i["defaults"]])
                else:
                    args.append([i["arg_name"], v1_arg_exprs[i["arg_name"]]])
            # args = [[i["arg_name"], v1_arg_exprs[i["arg_name"]]] for i in func_item["funcmeta"]["arguments"]]
            args_ = ";;".join([str(j) for _, j in args])
            func_call = f"{func_name};;{args_}"
            d = {
                "id": func_item["id"],
                "key": func_item["key"],
                "value": func_call
            }
            ## 将 v1 的func覆写到 v3 的函数中.
            node["content"]["config"]["expressions"].append(d)
            # ## 如果当前 v1_func 的 id 不在 v3_func_ids 中, 那么就添加到 v3 的func表达式中
            # if func_item["id"] not in v3_func_ids:
            #     node["content"]["config"]["expressions"].append(d)
            # else:
            #     # 如果在 v3_func_ids 中, 那么更新此 v3_func
            #     for item in node["content"]["config"]["expressions"]:
            #         if item["id"] == func_item["id"]:
            #             item.update(d)

    def custom_node_v3_to_v1(self, node):
        """
            保存规则: 将 v3 版本的自定义节点转化为 v1 版本
            主要用于将新版编辑器的自定义节点函数转化为旧版编辑器可识别的格式.
            旧版本编辑器移除后, 需要线下把所有v1格式转化为 v3 格式，并移除此代码(顺便可以去掉v1格式, 即删除content config inputs 字段).
        """
        if not node["content"]["config"].get("expressions", []):
            node["content"]["config"]["expressions"] = []
        node["content"]["config"]["inputs"] = []  ## 先清空 v1 的输入函数, 然后再添加 v3 的表达式.
        for func_item in node["content"]["config"]["expressions"]:
            expr_ast = parse_oprator_expr_v3(func_item["value"])
            operator, *op_arg_expressions  = expr_ast
            func_name = operator
            f = udf_manager.udf_info(func_name)  # 需要在这里设计一个函数执行异常时返回的值么.
            # args = [zen_exprs_eval(i, node_input) for i in op_arg_expressions]
            oprator_kwargs = op_args_combination(op_arg_expressions, f)
            d = {
                "id": func_item["id"],
                "key": func_item["key"],
                "type": "function",
                "arg_exprs": oprator_kwargs,
                "funcmeta": {
                    "name": f["name"],
                    "arglength": f["arglength"],
                    "arguments": f["arguments"],
                    "return_values": f["return_values"],
                    "comments": f["comments"]
                }
            }
            ## 将 v3 的func覆写到 v1 的函数中.
            node["content"]["config"]["inputs"].append(d)
            # if func_item["id"] not in v1_func_ids:
            #     node["content"]["config"]["inputs"].append(d)
            # else:
            #    for item in node["content"]["config"]["inputs"]:
            #         if item["id"] == func_item["id"]:
            #             item.update(d)


    def graph_addons_v1_to_v3(self, graph_content):
        """
            将规则图中的自定义节点由v1格式转化为v3格式. 用于兼容旧编辑器.
            彻底移除旧版本编辑器后可移除此逻辑.
            graph_content: json string/dict
            return graph json string
        """
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
        input_node_name = [i.get("name") for i in rule_graph["nodes"] if i.get("type") == "inputNode"][0]
        for node in rule_graph["nodes"]:
            if node.get("type") == "customNode":
                content = node.get("content", {})
                config  = content.get("config", {})
                meta = config.get("meta", {})
                meta["inputNode_name"] = input_node_name
                node["content"]["config"]["meta"] = meta
                if node["content"]["config"].get("passThrough") is None:
                    node["content"]["config"]["passThrough"] = True

                node["content"]["config"]["version"] = "v3"
                ## 兼容旧版编辑器自定义节点执行逻辑, 将 v3 版本的自定义节点转化为 v1 版本. 这样可以在旧编辑器查看新版的自定义规则.
                self.custom_node_v1_to_v3(node)
                ### 将自定义节点中的表达式进行解析, 解析出其中表达式函数中的自定义函数(udf)的执行逻辑, 执行顺序.
                expr_asts = []
                custom_expressions = node["content"]["config"].get("expressions")
                if custom_expressions:
                    for func_item in custom_expressions:
                        item = {**func_item}
                        item["value"] = parse_oprator_expr_v3(func_item["value"])
                        expr_asts.append(item)
                    node["content"]["config"]["expr_asts"] = expr_asts

        logger.debug(f"rule_graph:{pformat(rule_graph)}")
        return json.dumps(rule_graph)


    def graph_addons_v3_to_v1(self, graph_content):
        """
            将规则图中的自定义节点由v3格式转化为v1格式. 用于兼容旧编辑器.
            彻底移除旧版本编辑器后可移除此逻辑.
            graph_content: json string/dict
            return graph json string
        """
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
        input_node_name = [i.get("name") for i in rule_graph["nodes"] if i.get("type") == "inputNode"][0]
        for node in rule_graph["nodes"]:
            if node.get("type") == "customNode":
                content = node.get("content", {})
                config  = content.get("config", {})
                meta = config.get("meta", {})
                meta["inputNode_name"] = input_node_name
                node["content"]["config"]["meta"] = meta
                if node["content"]["config"].get("passThrough") is None:
                    node["content"]["config"]["passThrough"] = True

                node["content"]["config"]["version"] = "v3"
                ## 兼容旧版编辑器自定义节点执行逻辑, 将 v3 版本的自定义节点转化为 v1 版本. 这样可以在旧编辑器查看新版的自定义规则.
                self.custom_node_v3_to_v1(node)
                ### 将自定义节点中的表达式进行解析, 解析出其中表达式函数中的自定义函数(udf)的执行逻辑, 执行顺序.
                expr_asts = []
                custom_expressions = node["content"]["config"].get("expressions")
                if custom_expressions:
                    for func_item in custom_expressions:
                        item = {**func_item}
                        item["value"] = parse_oprator_expr_v3(func_item["value"])
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
    async def custom_handler_v3(cls, request):
        """
            v2 支持字面量的自定义函数的表达式, 和普通函数类似, 也支持函数表达式的嵌套调用.
            参考 src/custom/custom_v2.json 中的示例.
            兼容 custom_handler_v1 元数据定义和执行逻辑.

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
            注意, 需要对 v1 版本和 v2 版本进行兼容.
            因为 v2 版本并未正式上线, 主要是对 v1 版本进行兼容.
        """
        # logger.debug(f"request.node:{request.node}")
        # graph json 要放在 zen engine zen rule 中进行解析, 解析的自定义表达式函数再使用自定义函数表达式来执行.
        expr_asts = request.node["config"].get("expr_asts", [])
        inputField = request.node.get("config",{}).get("inputField")
        outputPath = request.node.get("config",{}).get("outputPath")
        passThrough = request.node.get("config",{}).get("passThrough")
        logger.debug("custom node use custom_handler_v3")
        coro_funcs = []
        results = {}
        context = {
            "node_id": request.node["id"],  ## 隔离 graph 中的节点
            "meta": request.node["config"].get("meta", {}),
            "passThrough": passThrough,
            "inputField": inputField,
            "outputPath": outputPath,
        }

        node_input_args = {k: v for k, v in request.input.items() if k != "$nodes"}
        for item in expr_asts:
            coro_funcs.append(cls.engine_v3(item, node_input_args, context))
        _results = await asyncio.gather(*coro_funcs)
        results = {k["key"]: v for k, v in zip(expr_asts, _results)}
        if passThrough:
            results.update(node_input_args)
        else:
            pass
        
        if outputPath:
            # get nested path like a.b.c for dict a["b"]["c"]
            results = zen.evaluate_expression(f"{outputPath}={'_'}", {"_": results})  # 先创建路径
        logger.warning(f"custom v3 result:{results}")
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
            
            operator, *op_arg_expressions  = expr_ast
            logger.debug(f"node_input:{node_input}  context:{context}")
            logger.debug(f"operator:{operator}  args:{op_arg_expressions}")
            inputfield = context.get("inputField")
            func_name = operator
            f = udf_manager.udf_info(func_name)  # 需要在这里设计一个函数执行异常时返回的值么.
            args = [zen_exprs_eval(f"{inputfield}.{i}" if inputfield else f"{i}", node_input) for i in op_arg_expressions]
            oprator_kwargs = op_args_combination(args, f)
            logger.debug(f"ast_exec {func_name} args: {args}")
            logger.debug(f"ast_exec {func_name} kwargs: {oprator_kwargs}")
            kwargs = {
                **oprator_kwargs,
                **context,
                "func_id": expr_id,
                "expr_id": expr_id,
            }
            result = await udf_manager(func_name, *args, **kwargs)
            logger.debug(f"{func_name} calling ->: {result}")
            return result
        except Exception as e:
            logger.error(e, exc_info=True)
            # todo: 异常情况下自定义算子返回什么, 空字符串还是null.
            return None

    def get_decision_cache(self, key):
        return self.decision_cache.get(key, None)

    def get_content_cache(self, key):
        return self.content_cache.get(key, None)
 

__all__ = [
    ZenRule,
    udf,
    udf_manager,
    FuncArg,
    FuncRet,
]