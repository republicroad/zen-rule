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


def namespace_split(target,namespace=None) -> str:
    if namespace:
        return str(namespace)
    try:
        name_list = str(target).split(".")
        new_name_list = []
        for item in name_list:
            if "functions" == item:
                new_name_list = []
            else:
                new_name_list.append(item)
        return ".".join(new_name_list)
    except Exception as e:
        logger.error(e, exc_info=True)
        return ""


# Define classes for managing function arguments and return values
class FuncArg:
    def __init__(self, arg_name: str, arg_type: str, defaults: Any, comments: str):
        self.arg_name = arg_name
        self.arg_type = arg_type
        self.defaults = defaults
        self.comments = comments

    def to_dict(self):
        return {
            "arg_name": self.arg_name,
            "arg_type": self.arg_type,
            "defaults": self.defaults,
            "comments": self.comments,
        }

class FuncRet:
    def __init__(self, field_type: str, examples: Any, comments: str):
        self.field_type = field_type
        self.examples = examples
        self.comments = comments

    def to_dict(self):
        return {
            "field_type": self.field_type,
            "examples": self.examples,
            "comments": self.comments,
        }

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
        todo: function_schema 增加关于返回值schema的字段定义.
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
    # 之后再考虑是否支持 zen expression 的混用了.
    def __init__(self):
        self.functions = {}
        self.funcs = {}  # function schema dict
        self.param_annotation = {
            str: "string",
            dict: "object",  # json
            list: "array",
            tuple: "array",
            int: "number",
            float: "number",
        }
        self.default_type = "Any"

    def register_function(self, func, comments:str =None, args_info: FuncArg =None, return_info: FuncRet =None, namespace:str = None):
        sig = signature(func)
        arguments = []

        # Use provided args_info or derive from function signature
        if args_info:
            for info in args_info:
                arguments.append(info)
        else:
            # logger.debug(f"sig.parameters: {sig.parameters}")
            # logger.debug(f"sig.parameters items(): {pformat(sig.parameters.items())}")
            for name, param in sig.parameters.items():
                arg_type = self.param_annotation.get(param.annotation, self.default_type)
                defaults = '' if param.default == Parameter.empty else param.default
                comments = f'{name}:{arg_type}'
                arguments.append(FuncArg(name, arg_type, defaults, comments))

            # extra_arguments = [(arg.arg_name, arg.arg_type) for arg in arguments if arg.arg_name not in {"args", "kwargs"}]
            # if extra_arguments:
            #     raise Exception("udf function only allow to contains *args, **kwargs, please use @udf args_info to describe arg names")            
        # logger.debug(f"return_info:{return_info}")
        return_values = return_info.to_dict() if return_info else {}
        # logger.debug(f"return_values:{return_values}")
        self.functions[func.__name__] = {
            "func": func,
            "name": func.__name__,
            "arglength": len(arguments),
            "arguments": [arg.to_dict() for arg in arguments],
            "return_values": return_values,
            "returns": {},
            "comments": comments or func.__doc__,
            "namespace": namespace_split(func.__module__,namespace=namespace),
        }
        ### todo: 在 1.0 版本之前移除此兼容逻辑.
        ## 目前函数参数的定义都是 args 和 kwargs.
        ## 实际参数定义在udf装饰器中的args_info列表中的 FuncArg 实例上.
        ## 需要将这部分的参数定义也包含在 function json schema 的 parameters 参数中.
        func_schema = function_schema(func)
        func_schema['namespace'] = namespace_split(func.__module__, namespace=namespace)
        func_schema['kind'] = func_schema['namespace'].split('.')[-1]
        self.funcs[func.__name__] = func_schema

    def get_udf_info(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": data["name"],
                "arglength": data["arglength"],
                "arguments": data["arguments"],
                "return_values": data["return_values"],
                "comments": data["comments"],
                "namespace": data["namespace"],
                "kind": data["namespace"].split(".")[-1]
            }
            for data in self.functions.values()
        ]

    def udf_info(self, name) -> List[Dict[str, Any]]:
        return self.functions.get(name)

    def udf_function_schema(self, name: str) -> Dict[str, Any]:
        return self.funcs.get(name)

    def udf_function_schema_tools(self) -> Dict[str, Any]:
        d = []
        ## groupby list must sorted
        func_tools = [data for data in self.funcs.values()]
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
def udf(comments=None, args_info=None, return_info=None,namespace=None):
    def decorator(func):
        udf_manager.register_function(func, comments, args_info, return_info,namespace)
        return func
    return decorator
