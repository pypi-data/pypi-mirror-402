"""接口相关辅助函数。"""

import inspect
from typing import Any, Callable, Dict, Type

from pydantic import BaseModel

from ..utils import (
    extract_pydantic_models_from_signature,
    get_function_name_from_callable,
    normalize_url,
    parse_docstring,
    pydantic_to_json_schema,
    python_type_to_json_schema,
)

__all__ = [
    "extract_pydantic_models_from_signature",
    "get_function_name_from_callable",
    "normalize_url",
    "parse_docstring",
    "pydantic_to_json_schema",
    "python_type_to_json_schema",
]


def convert_signature(func: Callable) -> Dict[str, Any]:
    """解析函数签名，提取参数、返回值与 Pydantic 模型。"""
    sig = inspect.signature(func)
    desc, param_docs = parse_docstring(func)

    params = []
    pydantic_models: Dict[str, Type[BaseModel]] = {}

    for name, param in sig.parameters.items():
        if name == "self":
            continue

        param_type = (
            param.annotation if param.annotation != inspect.Parameter.empty else str
        )
        schema = python_type_to_json_schema(param_type, name)
        if "$ref" in str(schema):
            if inspect.isclass(param_type) and issubclass(param_type, BaseModel):
                pydantic_models[param_type.__name__] = param_type

        params.append(
            {
                "name": name,
                "description": param_docs.get(name, f"Parameter: {name}"),
                "required": param.default == inspect.Parameter.empty,
                "schema": schema,
            }
        )

    return_type = (
        sig.return_annotation if sig.return_annotation != inspect.Signature.empty else dict
    )
    result_schema = python_type_to_json_schema(return_type, "result")

    pydantic_models.update(extract_pydantic_models_from_signature(func))

    return {
        "description": desc if desc else f"Method: {func.__name__}",
        "params": params,
        "result_schema": result_schema,
        "pydantic_models": pydantic_models,
    }
