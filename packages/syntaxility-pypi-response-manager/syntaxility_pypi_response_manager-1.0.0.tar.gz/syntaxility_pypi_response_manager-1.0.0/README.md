## SyntaxilitY PyPi Response Manager & Decorators

A Unified response manager and decorators for FAST APIs, REST APIs, Machine Learning, Deep Learning, and AI inference outputs.

## Example for REST & FAST APIs:
```python
from syntaxility_pypi_response_manager import (
    SyntaxilitYPyPiResponseManager,
    SyntaxilitYPagination
)

@app.get("/HTTP_200_OK", tags=["HTTP"])
def ok():
    # try-catch block
    try:
        # Build pagination response
        response = SyntaxilitYPagination.build_pagination_response(
            metadata=[],
            total=1,
            page=1,
            limit=1
        )
        
        return SyntaxilitYPyPiResponseManager.HTTP_200_OK(data=response, message="Data fetched successfully")
    except Exception as e:
        return SyntaxilitYPyPiResponseManager.HTTP_500_INTERNAL_SERVER_ERROR(message=str(e))
```

```python
from syntaxility_pypi_response_manager import (
    SyntaxilitYPyPiResponseManager,
    SyntaxilitYPagination
)

@app.get("/HTTP_201_CREATED", tags=["HTTP"])
def created():
    # try-catch block
    try:
        # Build pagination response
        response = SyntaxilitYPagination.build_pagination_response(
            metadata=[],
            total=1,
            page=1,
            limit=1
        )
        return SyntaxilitYPyPiResponseManager.HTTP_201_CREATED(data=response, message="Data created successfully")
    except Exception as e:
        return SyntaxilitYPyPiResponseManager.HTTP_500_INTERNAL_SERVER_ERROR(message=str(e))
```

```python
from syntaxility_pypi_response_manager import (
    SyntaxilitYPyPiResponseManager,
    SyntaxilitYPagination,
    TryCatch
)

@app.get("/HTTP_201_CREATED", tags=["HTTP"])
# TryCatch is a decorator: will handle all the exceptions
# and return the appropriate response
@TryCatch
def created():
    # Build pagination response
    response = SyntaxilitYPagination.build_pagination_response(
        metadata=[],
        total=1,
        page=1,
        limit=1
    )
    return SyntaxilitYPyPiResponseManager.HTTP_201_CREATED(data=response, message="Data created successfully")
```

## Example for ML:
```python
ml_results = [
    {"input": [1, 2], "prediction": 0},
    {"input": [3, 4], "prediction": 1},
    {"input": [5, 6], "prediction": 1},
    {"input": [7, 8], "prediction": 0},
    {"input": [9, 10], "prediction": 1},
]

@app.post("/ml-ok", tags=["ML"])
def ml_ok(page: int = Query(1, ge=1), limit: int = Query(2, ge=1)):
    # Pagination params
    pagination_params = SyntaxilitYPagination.get_pagination_params({"page": page, "limit": limit})
    page, limit, skip = pagination_params["page"], pagination_params["limit"], pagination_params["skip"]

    # Slice dataset
    paginated_predictions = ml_results[skip: skip + limit]

    # Build metadata including pagination info
    metadata = {
        "model": "test_model", 
        "version": "1.0",
        "pagination": SyntaxilitYPagination.build_pagination_response(
            metadata={},
            total=len(ml_results),
            page=page,
            limit=limit
        )["pagination"]
    }

    return SyntaxilitYPyPiResponseManager.ML_INFERENCE_OK(
        predictions=paginated_predictions,
        probabilities=None,
        metadata=metadata,
        message="Paginated ML inference results"
    )
```

Licenses: MIT Free

Copyright (c) 2026 SyntaxilitY

Contact: [GitHub](https://github.com/SyntaxilitY/SyntaxilitY-PyPi-Response-Manager-Decorators.git/) | [LinkedIn](https://www.linkedin.com/in/tariq-mehmood-3ab013254/)

Developer: Tariq Mehmood

"""