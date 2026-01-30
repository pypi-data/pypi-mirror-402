"""OpenRPC 文档构建。"""

from typing import Any, Dict

from ..models import OpenRPCDocument
from ..utils import normalize_url, pydantic_to_json_schema
from .registered_function import RegisteredFunction


def build_openrpc_document(
    registered_func: RegisteredFunction,
    base_url: str,
    rpc_endpoint: str,
    api_version: str,
) -> Dict[str, Any]:
    """根据注册函数构建 OpenRPC 文档。"""
    method = registered_func.to_openrpc_method()

    schemas = {}
    for model_name, model_class in registered_func.pydantic_models.items():
        if model_name in schemas:
            continue
        schema = pydantic_to_json_schema(model_class)
        if "properties" in schema:
            entry = {
                "type": "object",
                "properties": schema.get("properties", {}),
                "required": schema.get("required", []),
            }
            if "description" in schema:
                entry["description"] = schema["description"]
            schemas[model_name] = entry
        else:
            schemas[model_name] = schema

    document = {
        "openrpc": "1.3.2",
        "info": {
            "title": registered_func.name,
            "version": api_version,
            "description": registered_func.description,
            "x-anp-protocol-type": "ANP",
            "x-anp-protocol-version": "1.0.0",
        },
        "security": [{"didwba": []}],
        "servers": [
            {
                "name": "Production Server",
                "url": normalize_url(base_url, rpc_endpoint),
                "description": "Production server for API",
            }
        ],
        "methods": [method],
        "components": {
            "securitySchemes": {
                "didwba": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "DID-WBA",
                    "description": "DID-WBA authentication scheme",
                }
            }
        },
    }

    if schemas:
        document["components"]["schemas"] = schemas

    return document
