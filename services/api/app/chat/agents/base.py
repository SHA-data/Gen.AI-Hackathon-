"""Agent base class."""
from typing import List, Optional
from pydantic import BaseModel

class AgentDefinition(BaseModel):
    key: str
    name: str
    description: str
    system_prompt: str
    allowed_tools: List[str]
