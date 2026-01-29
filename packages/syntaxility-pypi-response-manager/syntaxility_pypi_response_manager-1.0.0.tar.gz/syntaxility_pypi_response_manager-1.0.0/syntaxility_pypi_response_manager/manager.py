from typing import Optional, TypeVar, Any, Dict
from fastapi.responses import JSONResponse
from .types import APIResponse
from .ml_types import MLInferenceResponse

T = TypeVar("T")

class SyntaxilitYPyPiResponseManager:
    @staticmethod
    def http(status: int, code: str, message: str, data: Optional[T] = None):
        response = APIResponse[T](
            status=status,
            code=code,
            message=message,
            data=data
        )
        return JSONResponse(status_code=status, content=response.model_dump())

    @staticmethod
    def HTTP_200_OK(data: Optional[T] = None, message: str = "Request successful"):
        return SyntaxilitYPyPiResponseManager.http(200, "HTTP_200_OK", message, data)

    @staticmethod
    def HTTP_201_CREATED(data: Optional[T] = None, message: str = "Resource created"):
        return SyntaxilitYPyPiResponseManager.http(201, "HTTP_201_CREATED", message, data)

    @staticmethod
    def HTTP_204_NO_CONTENT(message: str = "No content"):
        return SyntaxilitYPyPiResponseManager.http(204, "HTTP_204_NO_CONTENT", message)

    @staticmethod
    def HTTP_400_BAD_REQUEST(message: str = "Bad request"):
        return SyntaxilitYPyPiResponseManager.http(400, "HTTP_400_BAD_REQUEST", message)

    @staticmethod
    def HTTP_401_UNAUTHORIZED(message: str = "Unauthorized"):
        return SyntaxilitYPyPiResponseManager.http(401, "HTTP_401_UNAUTHORIZED", message)

    @staticmethod
    def HTTP_403_FORBIDDEN(message: str = "Forbidden"):
        return SyntaxilitYPyPiResponseManager.http(403, "HTTP_403_FORBIDDEN", message)

    @staticmethod
    def HTTP_404_NOT_FOUND(message: str = "Not found"):
        return SyntaxilitYPyPiResponseManager.http(404, "HTTP_404_NOT_FOUND", message)

    @staticmethod
    def HTTP_409_CONFLICT(message: str = "Conflict"):
        return SyntaxilitYPyPiResponseManager.http(409, "HTTP_409_CONFLICT", message)

    @staticmethod
    def HTTP_422_UNPROCESSABLE_ENTITY(message: str = "Unprocessable entity"):
        return SyntaxilitYPyPiResponseManager.http(422, "HTTP_422_UNPROCESSABLE_ENTITY", message)

    @staticmethod
    def HTTP_429_TOO_MANY_REQUESTS(message: str = "Too many requests"):
        return SyntaxilitYPyPiResponseManager.http(429, "HTTP_429_TOO_MANY_REQUESTS", message)

    @staticmethod
    def HTTP_500_INTERNAL_SERVER_ERROR(message: str = "Internal server error"):
        return SyntaxilitYPyPiResponseManager.http(500, "HTTP_500_INTERNAL_SERVER_ERROR", message)

    @staticmethod
    def HTTP_503_SERVICE_UNAVAILABLE(message: str = "Service unavailable"):
        return SyntaxilitYPyPiResponseManager.http(503, "HTTP_503_SERVICE_UNAVAILABLE", message)

    @staticmethod
    def ML_INFERENCE_OK(
        predictions: Any,
        probabilities: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        message: str = "Inference completed"
    ):
        """
        Returns a properly structured ML response:
        {
            status, code, message, predictions, probabilities, metadata
        }
        """
        response_content = {
            "status": 200,
            "code": "ML_INFERENCE_OK",
            "message": message,
            "predictions": predictions,
            "probabilities": probabilities,
            "metadata": metadata
        }
        return JSONResponse(status_code=200, content=response_content)

    @staticmethod
    def ML_INFERENCE_FAILED(
        message: str = "Inference failed",
        metadata: Optional[Dict[str, Any]] = None
    ):
        response_content = {
            "status": 500,
            "code": "ML_INFERENCE_FAILED",
            "message": message,
            "predictions": None,
            "probabilities": None,
            "metadata": metadata
        }
        return JSONResponse(status_code=500, content=response_content)