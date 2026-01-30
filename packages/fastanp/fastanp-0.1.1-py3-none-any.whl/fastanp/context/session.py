"""Session 数据结构。"""

import logging
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)


class Session:
    """基于 DID 的轻量 Session 封装。"""

    def __init__(self, session_id: str, did: str):
        self.id = session_id
        self.did = did
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.data: Dict[str, Any] = {}

    def touch(self) -> None:
        """更新访问时间。"""
        self.last_accessed = datetime.now()

    def set(self, key: str, value: Any) -> None:
        """写入会话数据。"""
        self.data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """读取会话数据。"""
        return self.data.get(key, default)

    def clear(self) -> None:
        """清空全部会话数据。"""
        self.data.clear()
