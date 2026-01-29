from functools import wraps
from typing import Callable, Any
from .manager import SyntaxilitYPyPiResponseManager

def TryCatch(func: Callable):
    """
    Generic decorator to catch exceptions and return structured responses
    using SyntaxilitYPyPiResponseManager.
    Works for any function or route.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return SyntaxilitYPyPiResponseManager.HTTP_400_BAD_REQUEST(
                message=f"Value error: {str(e)}"
            )
        except KeyError as e:
            return SyntaxilitYPyPiResponseManager.HTTP_404_NOT_FOUND(
                message=f"Key error: {str(e)}"
            )
        except IndexError as e:
            return SyntaxilitYPyPiResponseManager.HTTP_404_NOT_FOUND(
                message=f"Index error: {str(e)}"
            )
        except TypeError as e:
            return SyntaxilitYPyPiResponseManager.HTTP_400_BAD_REQUEST(
                message=f"Type error: {str(e)}"
            )
        except Exception as e:
            return SyntaxilitYPyPiResponseManager.HTTP_500_INTERNAL_SERVER_ERROR(
                message=f"Internal server error: {str(e)}"
            )

    return wrapper
