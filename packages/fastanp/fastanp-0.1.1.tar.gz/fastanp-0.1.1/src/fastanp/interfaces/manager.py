"""接口注册与路由管理。"""

import logging
from typing import Callable, Dict, Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from ..context import SessionManager
from .jsonrpc import build_jsonrpc_handler
from .openrpc import build_openrpc_document
from .proxy import InterfaceProxy
from .registered_function import RegisteredFunction
from .utils import get_function_name_from_callable

logger = logging.getLogger(__name__)


class InterfaceManager:
    """管理接口注册、OpenRPC 构建和 JSON-RPC 端点注入。"""

    def __init__(self, api_title: str = "API", api_version: str = "1.0.0", api_description: str = ""):
        self.api_title = api_title
        self.api_version = api_version
        self.api_description = api_description
        self.functions: Dict[Callable, RegisteredFunction] = {}
        self.registered_names: set[str] = set()
        self.session_manager = SessionManager()

    def register_function(
        self,
        func: Callable,
        path: str,
        description: Optional[str] = None,
        humanAuthorization: bool = False,
    ) -> RegisteredFunction:
        func_name = get_function_name_from_callable(func)
        if func_name in self.registered_names:
            raise ValueError(f"Function name '{func_name}' is already registered.")

        registered_func = RegisteredFunction(func, path, description, human_authorization=humanAuthorization)
        self.functions[func] = registered_func
        self.registered_names.add(func_name)

        logger.info("Registered function: %s at %s", func_name, path)
        return registered_func

    def create_interface_proxy(
        self,
        func: Callable,
        base_url: str,
        rpc_endpoint: str = "/rpc",
    ) -> InterfaceProxy:
        registered_func = self.functions.get(func)
        if not registered_func:
            raise ValueError(f"Function {func} is not registered")

        openrpc_doc = build_openrpc_document(
            registered_func,
            base_url=base_url,
            rpc_endpoint=rpc_endpoint,
            api_version=self.api_version,
        )

        return InterfaceProxy(
            func=func,
            openrpc_doc=openrpc_doc,
            path=registered_func.path,
            base_url=base_url,
            description=registered_func.description,
        )

    def register_jsonrpc_endpoint(self, app: FastAPI, rpc_path: str = "/rpc") -> None:
        handler = build_jsonrpc_handler(self.functions, self.session_manager)
        app.add_api_route(rpc_path, handler, methods=["POST"], tags=["rpc"])
        logger.info("Registered JSON-RPC endpoint at %s", rpc_path)
