import logging
from pprint import pformat
from typing import List, Dict, Any
from inspect import signature, Parameter, iscoroutinefunction
logger = logging.getLogger(__name__)

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

class FuncValue:
    def __init__(self, field_name: str, field_type: str, defaults: Any, comments: str):
        self.field_name = field_name
        self.field_type = field_type
        self.defaults = defaults
        self.comments = comments

    def to_dict(self):
        return {
            "field_name": self.field_name,
            "field_type": self.field_type,
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

    def register_function(self, func, comments=None, args_info=None, return_info=None):
        sig = signature(func)
        arguments = []

        # Use provided args_info or derive from function signature
        if args_info:
            for info in args_info:
                arguments.append(info)
        else:
            logger.debug(f"sig.parameters: {sig.parameters}")
            logger.debug(f"sig.parameters items(): {pformat(sig.parameters.items())}")
            for name, param in sig.parameters.items():
                # arg_type = "string" if param.annotation == str else "json" if param.annotation == dict else "Any"
                arg_type = self.param_annotation.get(param.annotation, self.default_type)
                defaults = '' if param.default == Parameter.empty else param.default
                # comments = f'{name} parameter'
                comments = f'{name}:{arg_type}'
                arguments.append(FuncArg(name, arg_type, defaults, comments))

        logger.debug(f"return_info:{return_info}")
        # # Use provided return_info or default to a simple return value
        # if return_info:
        #     return_values = {k: v for k, v in return_info.items()}
        # else:
        #     return_values = {
        #         "return_value": FuncValue("return", "string", "", "Function return value")
        #     }

        self.functions[func.__name__] = {
            "func": func,
            "name": func.__name__,
            "arglength": len(arguments),
            "arguments": [arg.to_dict() for arg in arguments],
            # 以后应该改成这个配置
            # "return_values": {k: v.to_dict() for k, v in return_values.items()},
            "return_values": {},  # {k: v.to_dict()['defaults'] for k, v in return_values.items()},
            "comments": comments or func.__doc__
        }

    def get_udf_info(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": data["name"],
                "arglength": data["arglength"],
                "arguments": data["arguments"],
                "return_values": data["return_values"],
                "comments": data["comments"]
            }
            for data in self.functions.values()
        ]

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
def udf(comments=None, args_info=None, return_info=None):
    def decorator(func):
        udf_manager.register_function(func, comments, args_info, return_info)
        return func
    return decorator

