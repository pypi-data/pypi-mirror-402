"""FastANP 请求上下文。"""

from typing import Optional

from fastapi import Request

from .session import Session


class Context:
    """对 JSON-RPC 接口暴露的上下文对象。"""

    def __init__(
        self,
        session: Session,
        did: str,
        request: Request,
        auth_result: Optional[dict] = None,
    ):
        self.session = session
        self.did = did
        self.request = request
        self.auth_result = auth_result or {}

    @property
    def headers(self) -> dict:
        return dict(self.request.headers)

    @property
    def client_host(self) -> Optional[str]:
        if self.request.client:
            return self.request.client.host
        return None
