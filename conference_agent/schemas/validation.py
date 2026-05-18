from pydantic import BaseModel
from typing import Optional, Literal


class ValidationResult(BaseModel):
    conference_id: str
    passed: bool
    failed_condition: Optional[int] = None
    rejection_reason: Optional[str] = None
    date_bucket: Literal["now", "future", "reject"]
