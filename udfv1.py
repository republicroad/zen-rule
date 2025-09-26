
import logging
import inspect
import asyncio
from pprint import pprint
from pathlib import Path
from zen_rule import ZenRule, udf, FuncArg, FuncRet

from utils import httpsession, get_state

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@udf(
    comments="group_distinct_1m_demo function",
    args_info=[
        FuncArg(arg_name="group", arg_type="string", defaults="", comments="var group"),
        FuncArg(arg_name="distinct", arg_type="string", defaults="", comments="var distinct"),
    ],
    return_info=FuncRet(field_type="object", examples={}, comments="返回值示例, 字段解释")     
)
def group_distinct_1m_demo(*args, **kwargs):
    logger.info(f"{inspect.stack()[0][3]} args:{args}")
    logger.info(f"{inspect.stack()[0][3]} kwargs:{kwargs}")
    return {
            "function": "group_distinct_1m_demo",
            "pv": 1,
            "uv": 2,
            "gpv": 3
        }

async def test_zenrulev1_with_enginev3():
    zr = ZenRule({})
    basedir = Path(__file__).parent
    filename = basedir / "graph" / "custom_v1.json"
    key = filename

    with open(filename, "r", encoding="utf8") as f:
        logger.warning(f"graph json: %s", filename)
        content =  f.read()

    zr.create_decision_with_cache_key(key, content)  # 将规则图缓存在键下, 这样可以只读取规则一次，解析一次，然后复用决策对象 decision
    result = await zr.async_evaluate(key, {"ip": "1.2.3.4", "user": "17707115956"})
    print("zen rule custom_v1 result:", result)
    assert result.get("result", {}).get("a", {}).get("function") == "group_distinct_1m_demo", "custom_v1 规则执行失败"


if __name__ == "__main__":
    # test_zenrule_v3
    asyncio.run(test_zenrulev1_with_enginev3())
