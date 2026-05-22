import re
import time
import logging
import inspect
from itertools import groupby
from pprint import pformat
from typing import List, Dict, Any
from inspect import signature, Parameter, iscoroutinefunction
from pydantic import BaseModel, create_model, Field, TypeAdapter
from docstring_parser import parse

logger = logging.getLogger(__name__)

pyT_jsonT_maps = {
    None: 'null',
    bool: 'boolean',
    str: 'string',
    dict: 'object',
    list: 'array',
    int: 'integer',
    float: 'number'
}
json_py_type_maps = {v:k for k,v in pyT_jsonT_maps.items()}
pyT_jsonT_maps[tuple] = "array"

pyT_defaults_maps = {
    None: None,
    bool: False,  # bool()
    str: '',      # str()
    dict: {},     # dict()
    list: [],     # list()
    tuple: (),    # tuple()
    int: 0,       # int()
    float: 0.0    # float()
}


def jsonT2pyT(json_type: str):
    # 未知的 json 类型则转化为字符串
    return json_py_type_maps.get(json_type, str)


def pyT2jsonT(py_type: type):
    return pyT_jsonT_maps.get(py_type, 'string')


def jsonTV2pyTV(v: Any, json_type: Any, default: Any=None):
    """
    Docstring for jsonTV2pyTV. now ignore default value.
    todo: json_type 以后考虑支持复合类型
    
    :param v: Description
    :type v: Any
    :param json_type: Description
    :type json_type: Any
    :param default: Description
    :type default: Any
    """
    _T =  jsonT2pyT(json_type)
    if _T is None:
        value = v
    else:
        try:
            value = _T(v)
        except Exception as e:
            logger.debug("error:%s _T:%s v:%s", e, _T, v, exc_info=True)
            value = pyT_defaults_maps.get(_T, None)
    return value


def returns_description_parser(content:str):
    """
    函数注释的返回信息解析
    """
    content_lines = content.splitlines()
    try:
        if len(content_lines) > 0:
            title = content_lines[0]
            return_params = content_lines[1:]
            pattern = r"\*\*(\w+?)\*\*(?:\s*\((\w+?)\))?(?::\s*([^\n。]+))?"
            properties_list = []
            for item in return_params:
                match = re.search(pattern, item)
                name = match.group(1) or ''
                type_ = match.group(2) or ''
                desc = match.group(3) or ''
                if name:
                    item_propertie =  {name:{"title":name.capitalize(),"type":type_,"description":desc}}
                    properties_list.append(item_propertie)
            return {"properties":properties_list,"title":title}
        else:
            return {}
    except Exception as e:
        return {"msg":e.args}


def function_return_schema(f):
    """
    从函数得反射中获取到函数返回值得相关信息
    先从文档中获取
    再通过最后的反射来覆盖文档中的字段
    """
    return_schema = {
        "type":"null",
        "title":"",
        "properties":{},
    }
    # 从文档中获取到注释内容
    parsed_doc = parse(f.__doc__)
    parsed_doc_return = parsed_doc.returns
    if parsed_doc_return:
        res = returns_description_parser(parsed_doc.returns.description)
        return_schema.update({"title":res.get("title","")})
        return_properties_in_docs = res.get("properties",[])
        if return_properties_in_docs:
            return_schema_properties = return_schema.get("properties",{})
            for item in return_properties_in_docs:
                return_schema_properties.update(**item)
            return_schema["properties"] = return_schema_properties
    func_sig = inspect.signature(f)
    if func_sig.return_annotation == Parameter.empty:
        return_schema.update({'type': 'null'})
    elif  func_sig.return_annotation in {str}:
        return_schema.update({ "type": "string" })
    elif func_sig.return_annotation in {int}:
        return_schema.update({ "type": "integer" })
    elif func_sig.return_annotation in {float}:
        return_schema.update({ "type": "number" })
    elif func_sig.return_annotation in {bool}:
        return_schema.update({ "type": "boolean" })
    elif func_sig.return_annotation in {list, tuple}:
        return_schema.update({"type": "array"})
    elif func_sig.return_annotation in {dict}:
        return_schema.update({"type": "object"})
    elif issubclass(func_sig.return_annotation,BaseModel):
        return_schema.update(func_sig.return_annotation.model_json_schema())
    else:
        return_schema.update({'type': 'null'})
    return return_schema


def function_schema(f):
    """
        将 python 函数的签名(名字, 入参及其类型, 返回值及其类型) 转化为 json schema.
    """
    ### def bar(a: int, b:Annotated[str, "The city to get the weather for"]):
    ###     pass
    func_sig = inspect.signature(f)
    func_parameters = {}
    parsed_doc = parse(f.__doc__)
    param_docs = {param.arg_name:param for param in parsed_doc.params}
    for n, param in func_sig.parameters.items():
        if n == "args" or n == "kwargs":
            continue
        # Retrieve function argument Annotated tips
        _para_annotation_doc = getattr(param.annotation, "__metadata__", "")
        para_annotation_doc = _para_annotation_doc[0] if _para_annotation_doc else ""
        t = None if param.annotation in {Parameter.empty, Any} else param.annotation
        default_value = Ellipsis if param.default==Parameter.empty else param.default
        # comment from doc string or field annotation, field annotation first
        _param_func_doc = param_docs.get(n)
        param_func_doc = _param_func_doc.description if _param_func_doc else ""
        field = Field(default_value, description=para_annotation_doc or param_func_doc)
        func_parameters[n] = (t, field)

    parameter_model = create_model(f.__name__, **func_parameters)
    return_schema = function_return_schema(f)
    # function json schema
    func_docs = [parsed_doc.short_description, parsed_doc.long_description]
    func_description = "\n".join([i for i in func_docs if i])  # 取出非Node的 doc string
    schema = {
        'name': f.__name__,   # name是 openai function calling schema 的关键字
        'title': f.__name__,  # title 是 json schema 的关键字
        'type': 'function',
        'description': func_description,
        'parameters': parameter_model.model_json_schema(),
        'returns': return_schema
    }
    return schema


# UDF Manager class to manage the registered UDFs
class UDFManager:
    def __init__(self):
        self.functions = {}

    def register_function(self, func, namespace:str = None):
        func_schema = function_schema(func)
        func_schema['namespace'] = namespace or func.__module__.split(".")[-1]
        func_schema['kind'] = func_schema['namespace'].split('.')[-1]
        self.functions[func.__name__] = {
            "func": func,
            "name": func.__name__,
            "schema": func_schema
        }

    def udf_function_schema(self, name: str) -> Dict[str, Any]:
        return self.functions.get(name).get("schema")

    def udf_function_schema_tools(self) -> Dict[str, Any]:
        d = []
        ## groupby list must sorted
        func_tools = [data.get("schema") for data in self.functions.values()]
        group_key_func = lambda x: x.get("namespace", "default")
        for key, group in groupby(sorted(func_tools, key=group_key_func), key=group_key_func):
            # simulate openai function calling schema
            namespace_funcs = {
                "type": "namespace",
                "title": key,
                "name": key,
                "description": "",  # 以后从模块的顶层文档中提取或者增加显示定义.
                "tools": list(group)
            }
            d.append(namespace_funcs)
        return d

    def func_bind_params(self, name: str, args: list):
        """
            将参数值和参数名字组装为字典.
            f["parameters"]["properties"] 是如下结构
            {
                'b': {'default': '', 'description': 'var b', 'title': 'B', 'type': 'string'},
                'a': {'default': '', 'description': 'var a', 'title': 'A', 'type': 'string'},
                'c': {'default': '', 'description': 'var c', 'title': 'C', 'type': 'string'}
            }
        """
        f = self.udf_function_schema(name)
        param_with_values = {name: jsonTV2pyTV(v, schema.get("type"), schema.get("default"))
              for (name, schema), v in zip(f["parameters"]["properties"].items(), args)}
        return param_with_values

    async def __call__(self, udf_name: str, *args, **kwargs) -> Any:
        """
            v2 spec
            执行器要函数解析放到一起, 在function_call_parse中实现解析器和执行器,
            然后执行器调用真正的udf函数管理和执行器.
        """
        if udf_name in self.functions:
            t1 = time.time()
            func = self.functions[udf_name]["func"]
            if iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            logger.debug("%s cost: %s", udf_name, time.time() - t1)
            return result
        else:
            raise ValueError(f"Function '{udf_name}' is not registered in UDFManager")


# Instantiate UDF Manager
udf_manager = UDFManager()

# Decorator to register UDFs with optional custom metadata
def udf(namespace=None):
    def decorator(func):
        udf_manager.register_function(func, namespace)
        return func
    return decorator
