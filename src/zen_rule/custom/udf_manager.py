import logging
import os
from pprint import pformat
from typing import List, Dict, Any
from inspect import signature, Parameter, iscoroutinefunction
from pathlib import Path
logger = logging.getLogger(__name__)


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


# UDF Manager class to manage the registered UDFs
class UDFManager:
    # 之后再考虑是否支持 zen expression 的混用了.
    def __init__(self):
        self.functions = {}
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

            extra_arguments = [(arg.arg_name, arg.arg_type) for arg in arguments if arg.arg_name not in {"args", "kwargs"}]
            if extra_arguments:
                raise Exception("udf function only allow to contains *args, **kwargs, please use @udf args_info to describe arg names")            
        # logger.debug(f"return_info:{return_info}")
        return_values = return_info.to_dict() if return_info else {}
        # logger.debug(f"return_values:{return_values}")
        self.functions[func.__name__] = {
            "func": func,
            "name": func.__name__,
            "arglength": len(arguments),
            "arguments": [arg.to_dict() for arg in arguments],
            "return_values": return_values,
            "comments": comments or func.__doc__,
            "namespace": namespace_split(func.__module__,namespace=namespace),
        }

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
        return self.functions[name] 

    async def __call__(self, udf_name: str, *args, **kwargs) -> Any:
        """
            v2 spec
            执行器要函数解析放到一起, 在function_call_parse中实现解析器和执行器,
            然后执行器调用真正的udf函数管理和执行器.
        """
        if udf_name in self.functions:
      
            func = self.functions[udf_name]["func"]
            if iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        else:
            raise ValueError(f"Function '{udf_name}' is not registered in UDFManager")

    async def call_udf(self, udf_name: str, *args, **kwargs) -> Any:

        if udf_name in self.functions:
      
            func = self.functions[udf_name]["func"]
            if iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
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

