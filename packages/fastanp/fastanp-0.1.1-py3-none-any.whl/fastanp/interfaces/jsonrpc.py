"""统一 JSON-RPC 端点逻辑。"""

import inspect
import logging
from typing import Dict

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..context import Context, SessionManager

logger = logging.getLogger(__name__)


def build_jsonrpc_handler(functions: Dict[str, "RegisteredFunction"], session_manager: SessionManager):
    """创建 JSON-RPC 处理器。"""

    async def handle_jsonrpc(request: Request):
        func_map = {rf.name: rf for rf in functions.values()}

        try:
            body = await request.json()
        except Exception as exc:  # noqa: BLE001
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": "Parse error", "data": str(exc)},
                    "id": None,
                },
            )

        if not isinstance(body, dict):
            return JSONResponse(
                status_code=400,
                content={"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": None},
            )

        request_id = body.get("id")
        method_name = body.get("method")
        params = body.get("params", {})

        if method_name not in func_map:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": "Method not found",
                        "data": f"Method '{method_name}' does not exist",
                    },
                    "id": request_id,
                }
            )

        registered_func = func_map[method_name]
        func = registered_func.func

        try:
            final_params = {}
            sig = inspect.signature(func)

            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue
                annotation = param.annotation

                if annotation == Context or getattr(annotation, "__name__", "") == "Context":
                    continue
                if annotation == Request or getattr(annotation, "__name__", "") == "Request":
                    continue

                if param_name in params:
                    param_value = params[param_name]
                    if (
                        annotation != inspect.Parameter.empty
                        and inspect.isclass(annotation)
                        and issubclass(annotation, BaseModel)
                        and isinstance(param_value, dict)
                    ):
                        param_value = annotation(**param_value)

                    final_params[param_name] = param_value

            if registered_func.has_context_param:
                auth_result = getattr(request.state, "auth_result", None)
                did = getattr(request.state, "did", auth_result.get("did") if auth_result else "anonymous")

                session = session_manager.get_or_create(did=did, anonymous=(did == "anonymous"))
                context = Context(session=session, did=did, request=request, auth_result=auth_result)
                for param_name, param in sig.parameters.items():
                    annotation = param.annotation
                    if annotation == Context or getattr(annotation, "__name__", "") == "Context":
                        final_params[param_name] = context
                        break

            for param_name, param in sig.parameters.items():
                annotation = param.annotation
                if annotation == Request or getattr(annotation, "__name__", "") == "Request":
                    final_params[param_name] = request
                    break

            if inspect.iscoroutinefunction(func):
                result = await func(**final_params)
            else:
                result = func(**final_params)

            return JSONResponse(content={"jsonrpc": "2.0", "result": result, "id": request_id})

        except TypeError as exc:
            logger.warning("Invalid params for %s: %s", method_name, exc)
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32602, "message": "Invalid params", "data": str(exc)},
                    "id": request_id,
                }
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Error executing %s: %s", method_name, exc, exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": "Internal error", "data": str(exc)},
                    "id": request_id,
                }
            )

    return handle_jsonrpc
