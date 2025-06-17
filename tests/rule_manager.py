import logging
from pathlib import Path
from pprint import pprint, pformat
import zen
import asyncio
import json
import zen

from tools import contexts
from udfs.udf_manager import udf_manager
from cachetools import LRUCache
from cachetools import cached
from config import CACHE_SIZE
from db.models.rule_meta import BrdeRule
from db.postgresql.database import SessionLocal
from db.postgresql.crud import read_one
from db.models.rule_meta import BrdeUser, BrdeProj, BrdeRule, BrdeList, ListData

lru_cache = LRUCache(maxsize=CACHE_SIZE)
cache_dict = {}

logger = logging.getLogger(__name__)


class RuleManager:

    async def create_rule_manager(self, data_dict,  rule_id=None, db=None, **kwargs):
        await self._init(data_dict, rule_id, db, **kwargs)
        return self 

    def __init__(self):
        self.meta = {}
        self.cache_set = {}
        self.engine = None
        self.decision = None
    
    async def _init(self, data_dict, rule_id, db, **kwargs):
        engine = self.create_engine()
        self.engine = engine
        decision, _meta = await self._init_decsion(data_dict, rule_id, db, **kwargs)
        self.decision = decision
        self.meta = _meta
        if rule_id:
            await self._init_cache(rule_id)
        return

    async def custom_handler(self, request, **kwargs):
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

    def create_engine(self):
        engine = zen.ZenEngine({"customHandler": self.custom_handler})
        return engine

    def add_graph_meta(self, rule_graph):
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
        return json.dumps(rule_graph['content']), meta
    
    async def get_graph_data_from_db(self, rule_id, db, **kwargs):
        rule_data = await read_one(db, BrdeRule, {"id": rule_id})
        rule_dict = rule_data.as_dict(all_columns=True)
        jdm_graph = json.loads(rule_dict['rule_graph'])
        jdm_str, _meta = self.add_graph_meta(jdm_graph)
        return jdm_str, _meta 
    
    def get_graph_data_from_content(self, data_dict):
        jdm_str = json.dumps(data_dict['content'])
        return jdm_str
    
    async def _init_decsion(self, data_dict, rule_id, db, **kwargs):
        _meta = {}
        if rule_id:
            jdm_str, _meta = await self.get_graph_data_from_db(rule_id, db, **kwargs)
        else:
            jdm_str = self.get_graph_data_from_content(data_dict)
        decision = self.engine.create_decision(jdm_str) 
        return decision, _meta

    async def _init_cache(self, rule_id):
        cache_dict = {
            'meta': self.meta,
            'engine': self.engine,
            'decision': self.decision
        }

        self.cache_set[rule_id] = cache_dict
        return
        
    async def rule_exec(self, data_dict, rule_id, trace, db, **kwargs):
        if rule_id in self.cache_set:
            rule_cache = self.cache_set[rule_id]
            decision = rule_cache['decision']
        else:
            rule_manager = await self.create_rule_manager(data_dict, rule_id, db, **kwargs)
            decision = rule_manager.decision
        logger.debug('rule exec info: rule_id:{}, rule_manager:{} ,decision:{}'.format(rule_id, self, decision))
        result = await decision.async_evaluate(data_dict['context'], {"trace": trace})
        return result

    def update_rule_manager(self, rule_id):
        cache_dict = {
            'meta': self.meta,
            'engine': self.engine,
            'decision': self.decision
        }
        self.cache_set[rule_id] = cache_dict

    def delete_rule_manager(self, rule_id):
        if rule_id in self.cache_set:
            del self.cache_set[rule_id]

class zenRule:
    def __init__(self, options_dict=None):
        self.options_cache = {}
        self.options_dict = options_dict
        self.engine = zen.ZenEngine(self.options_dict)

    def create_decision(self, content):
        return self.engine.create_decision(content)

    def get_decision(self, key):
        zendecision = self.options_cache.get(key, None)
        if not zendecision:
            zendecision = self.engine.get_decision(key)
            self.options_cache[key] = zendecision
            return zendecision
        else:
            return zendecision

    def evaluate(self, key, ctx, options_dict=None):
        return self.engine.evaluate(key, ctx, options_dict)

    def async_evaluate(self, key, ctx, options_dict=None):
        return self.engine.async_evaluate(key, ctx, options_dict)

rule_manager = RuleManager()