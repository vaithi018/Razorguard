from typing import Dict, Any
from pydantic import BaseModel


class RulesConfigResponse(BaseModel):
    thresholds: Dict[str, int]
    rules: Dict[str, Any]


class RulesConfigUpdate(BaseModel):
    thresholds: Dict[str, int]
    rules: Dict[str, Any]
