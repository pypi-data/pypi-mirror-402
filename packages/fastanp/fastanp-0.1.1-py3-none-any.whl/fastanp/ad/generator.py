"""Agent Description 公共头生成器。"""

from datetime import UTC, datetime
from typing import Any, Dict, Optional

from ..models import Owner
from ..utils import normalize_agent_domain


class ADGenerator:
    """生成符合 ANP 规范的 Agent Description 公共字段。"""

    def __init__(
        self,
        name: str,
        description: str,
        did: str,
        agent_domain: str,
        owner: Optional[Dict[str, str]] = None,
        protocol_version: str = "1.0.0",
    ):
        self.name = name
        self.description = description
        self.did = did
        self.agent_domain, _ = normalize_agent_domain(agent_domain)
        self.owner = Owner(**owner) if owner else None
        self.protocol_version = protocol_version

    def generate_common_header(
        self,
        agent_description_path: str = "/ad.json",
        ad_url: Optional[str] = None,
        require_auth: bool = True,
    ) -> Dict[str, Any]:
        if ad_url is None:
            ad_url = f"{self.agent_domain}{agent_description_path}"

        ad_data = {
            "protocolType": "ANP",
            "protocolVersion": self.protocol_version,
            "type": "AgentDescription",
            "url": ad_url,
            "name": self.name,
            "did": self.did,
            "description": self.description,
            "created": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        if self.owner:
            ad_data["owner"] = self.owner.model_dump(exclude_none=True)

        ad_data["securityDefinitions"] = {
            "didwba_sc": {"scheme": "didwba", "in": "header", "name": "Authorization"}
        }
        ad_data["security"] = "didwba_sc"
        return ad_data
