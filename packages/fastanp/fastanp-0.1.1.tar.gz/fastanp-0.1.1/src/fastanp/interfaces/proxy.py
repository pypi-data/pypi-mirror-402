"""InterfaceProxy 表示单个接口的不同视图。"""

from typing import Any, Callable, Dict

from .utils import normalize_url


class InterfaceProxy:
    """提供 link/content/openrpc 三种访问方式。"""

    def __init__(
        self,
        func: Callable,
        openrpc_doc: Dict[str, Any],
        path: str,
        base_url: str,
        description: str,
    ):
        self.func = func
        self.path = path
        self.base_url = base_url
        self.description = description
        self._openrpc_doc = openrpc_doc

    @property
    def link_summary(self) -> Dict[str, Any]:
        return {
            "type": "StructuredInterface",
            "protocol": "openrpc",
            "description": self.description,
            "url": normalize_url(self.base_url, self.path),
        }

    @property
    def content(self) -> Dict[str, Any]:
        return {
            "type": "StructuredInterface",
            "protocol": "openrpc",
            "description": self.description,
            "content": self._openrpc_doc,
        }

    @property
    def openrpc_doc(self) -> Dict[str, Any]:
        return self._openrpc_doc
