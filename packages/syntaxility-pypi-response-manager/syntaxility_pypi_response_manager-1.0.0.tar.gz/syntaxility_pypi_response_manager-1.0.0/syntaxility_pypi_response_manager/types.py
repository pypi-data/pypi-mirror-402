from typing import Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    status: int
    code: str
    message: str
    data: Optional[T] = None
