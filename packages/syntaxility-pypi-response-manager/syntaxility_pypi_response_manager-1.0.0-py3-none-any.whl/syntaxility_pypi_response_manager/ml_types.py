from typing import Any, Dict, Optional
from pydantic import BaseModel

class MLInferenceResponse(BaseModel):
    status: int
    code: str
    message: str
    predictions: Optional[Any] = None
    probabilities: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None
