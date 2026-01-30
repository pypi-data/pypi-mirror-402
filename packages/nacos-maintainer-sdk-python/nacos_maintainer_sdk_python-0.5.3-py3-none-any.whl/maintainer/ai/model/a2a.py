# -*- coding: utf-8 -*-
from typing import Optional, List

from a2a._base import A2ABaseModel
from a2a.types import AgentCapabilities, AgentSkill


class AgentVersionDetail(A2ABaseModel):
    version: Optional[str] = None
    create_at: Optional[str] = None
    update_at: Optional[str] = None
    is_latest: Optional[bool] = False


class AgentCardVersionInfo(A2ABaseModel):
    protocol_version: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    iconUrl: Optional[str] = None
    capabilities: Optional[AgentCapabilities]
    skills: Optional[List[AgentSkill]] = None
    latest_published_version: Optional[str] = None
    version_details: Optional[List[AgentVersionDetail]] = None
    registration_type: Optional[str] = None
