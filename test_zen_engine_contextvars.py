from typing import Any, Optional, TypedDict, Literal, Awaitable, Union
import logging
import json
from pathlib import Path
from pprint import pprint, pformat
import asyncio
import inspect
import contextvars

import zen
from zen import ZenDecision
from utils import httpsession
# from zen import EvaluateResponse  # cannot import
zen_exprs_eval = lambda x, input: zen.evaluate_expression(x, input)
logger = logging.getLogger(__name__)
logging.basicConfig(level="NOTSET")


class EvaluateResponse(TypedDict):
    performance: str
    result: dict
    trace: dict


# async def custom_async_handler(request):
#     print("custom_async_handler custom_async_handler custom_async_handler")
#     p1 = request.get_field("prop1")
#     await asyncio.sleep(0.1)
#     return {
#         "output": {"sum": p1}
#     }


async def custom_async_handler(request):
    """
        示例自定义节点处理函数.
        todo: 是否需要包装一层异常捕获的逻辑.
    """
    try:
        # p1 = request.get_field("prop1")  # 没有prop1属性会报错.
        # await asyncio.sleep(0.1)
        ctx = contextvars.copy_context()
        print("custom_async_handler contextvars:")
        pprint(dict(ctx.items()))
        print("custom_async_handler -> httpsession.get():", httpsession.get())
        print("custom_async_handler -> httpsession.set('custom_async_handler'):")
        httpsession.set("custom_async_handler")
        print("custom_async_handler -> httpsession.get():", httpsession.get())
        logger.debug(f"request:{request}")
        logger.debug(f"request attrs:{dir(request)}")
        result = zen.evaluate_expression('rand(100)', request.input)
        logger.debug(f"return value:{result}")
        await asyncio.sleep(0)
        return {
            "output": {"sum": 112}
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e


def read_json_graph(filename):
    with open(filename, "r", encoding="utf8") as f:
        logger.warning(f"graph json: %s", filename)
        content =  f.read()
    return content



async def init_zen_engine():
    # httpsession.set("fccdjny")  # 先设置 contextvars 再创建包含 custom_handler 的zen engine 实例, 自定义函数可以 contextvars get.
    # print("init_zen_engine -> httpsession.get():", httpsession.get())
    ## options 中 customHandler 为 async_function, 必须放在异步函数中.
    ## 否则会报错 sys:1: RuntimeWarning: coroutine 'custom_async_handler' was never awaited
    ## custom_async_handler 中的 contextvars 必须在 zen.ZenEngine 初始化之前设置.
    ## 否则 custom_async_handler 中无法获取相关的contextvars.
    options = {"customHandler": custom_async_handler}
    engine = zen.ZenEngine(options) 
    basedir = Path(__file__).parent
    filename = basedir / "graph" / "custom_v0.json"
    content = read_json_graph(filename=filename)
    httpsession.set("fccdjny2")  # zen.ZenEngine 初始后设置 contextvars, custom_async_handler 中无法获取.
    zendecision = engine.create_decision(content)
    result = await zendecision.async_evaluate({"input": 7, "myvar": 15})
    print("init_zen_engine -> httpsession.get():", httpsession.get())
    return result


result = asyncio.run(init_zen_engine())
print("result:", result)


# if __name__ == "__main__":
#     pass