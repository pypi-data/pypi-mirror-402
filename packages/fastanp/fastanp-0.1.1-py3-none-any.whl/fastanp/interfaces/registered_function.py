"""存储注册函数的元数据。"""

import inspect
from typing import Any, Dict, Type

from fastapi import Request
from pydantic import BaseModel

from ..context import Context
from .utils import (
    convert_signature,
    get_function_name_from_callable,
    parse_docstring,
    python_type_to_json_schema,
)


class RegisteredFunction:
    """描述一个 JSON-RPC 接口。"""

    def __init__(
        self,
        func,
        path: str,
        description: str | None = None,
        human_authorization: bool = False,
    ):
        self.func = func
        self.name = get_function_name_from_callable(func)
        self.path = path
        self.description = description
        self.humanAuthorization = human_authorization
        self.pydantic_models: Dict[str, Type[BaseModel]] = {}
        self.has_context_param = False
        self.has_request_param = False

        self._parse_signature()

    def _parse_signature(self) -> None:
        sig = inspect.signature(self.func)
        desc, param_docs = parse_docstring(self.func)

        params = []
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            annotation = param.annotation
            if annotation == Context or getattr(annotation, "__name__", "") == "Context":
                self.has_context_param = True
                continue
            if annotation == Request or getattr(annotation, "__name__", "") == "Request":
                self.has_request_param = True
                continue

            param_type = annotation if annotation != inspect.Parameter.empty else str
            schema = python_type_to_json_schema(param_type, param_name)

            if (
                schema
                and isinstance(schema, dict)
                and "$ref" in schema
                and inspect.isclass(param_type)
                and issubclass(param_type, BaseModel)
            ):
                self.pydantic_models[param_type.__name__] = param_type

            params.append(
                {
                    "name": param_name,
                    "description": param_docs.get(param_name, f"Parameter: {param_name}"),
                    "required": param.default == inspect.Parameter.empty,
                    "schema": schema,
                }
            )

        self.params = params
        self.description = self.description or desc or f"Method: {self.name}"
        return_type = (
            sig.return_annotation if sig.return_annotation != inspect.Signature.empty else dict
        )
        self.result_schema = python_type_to_json_schema(return_type, "result")

        self.pydantic_models.update(convert_signature(self.func)["pydantic_models"])

    def to_openrpc_method(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "summary": self.description[:100]
            if len(self.description) > 100
            else self.description,
            "description": self.description,
            "params": self.params,
            "result": {
                "name": f"{self.name}Result",
                "description": f"Result of {self.name}",
                "schema": self.result_schema,
            },
        }
