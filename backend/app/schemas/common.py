from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel
from datetime import datetime, timezone

T = TypeVar("T")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    error: Optional[str] = None
    timestamp: str = ""

    def __init__(self, **data: Any):
        if "timestamp" not in data or not data["timestamp"]:
            data["timestamp"] = utc_now_iso()
        super().__init__(**data)
