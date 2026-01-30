"""Information 文档管理。"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from ..utils import normalize_url


class InformationItem:
    """单个 Information 条目。"""

    def __init__(
        self,
        type: str,  # noqa: A002
        description: str,
        path: str,
        file_path: Optional[str] = None,
        content: Optional[Any] = None,
    ):
        self.type = type
        self.description = description
        self.path = path if path.startswith("/") else f"/{path}"
        self.file_path = file_path
        self.content = content
        self.is_static = file_path is not None

    def get_content(self) -> Any:
        if self.is_static:
            file_path_obj = Path(self.file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"Information file not found: {self.file_path}")
            with open(file_path_obj, "r", encoding="utf-8") as file:
                return json.load(file)
        return self.content

    def to_dict(self, base_url: str) -> Dict[str, str]:
        return {
            "type": self.type,
            "description": self.description,
            "url": normalize_url(base_url, self.path),
        }


class InformationManager:
    """维护 Information 列表并注册对应路由。"""

    def __init__(self) -> None:
        self.items: List[InformationItem] = []

    def add_static(self, type: str, description: str, path: str, file_path: str) -> None:  # noqa: A002
        self.items.append(InformationItem(type, description, path, file_path=file_path))

    def add_dynamic(self, type: str, description: str, path: str, content: Any) -> None:  # noqa: A002
        self.items.append(InformationItem(type, description, path, content=content))

    def register_routes(self, app: FastAPI) -> None:
        for item in self.items:
            async def handler(info_item=item):
                try:
                    content = info_item.get_content()
                    return JSONResponse(content=content)
                except FileNotFoundError as exc:
                    return JSONResponse(status_code=404, content={"error": str(exc)})
                except json.JSONDecodeError as exc:
                    return JSONResponse(status_code=500, content={"error": f"Invalid JSON: {exc}"})
                except Exception as exc:  # noqa: BLE001
                    return JSONResponse(status_code=500, content={"error": f"Internal server error: {exc}"})

            app.add_api_route(item.path, handler, methods=["GET"], tags=["information"], summary=item.description)

    def get_information_list(self, base_url: str) -> List[Dict[str, str]]:
        return [item.to_dict(base_url) for item in self.items]
