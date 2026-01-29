from fastapi import FastAPI, Query
from fastapi.testclient import TestClient
from syntaxility_pypi_response_manager import (
    SyntaxilitYPyPiResponseManager,
    SyntaxilitYPagination,
    TryCatch
)

app = FastAPI(
    debug=False,
    title="SyntaxilitY PyPi Response Manager & Pagination",
    description="A unified response manager for FAST APIs, REST APIs, Machine Learning, Deep Learning, and AI inference outputs.",
    docs_url="/",
    redoc_url="/redoc",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "HTTP",
            "description": "HTTP responses",
        },
        {
            "name": "ML",
            "description": "Machine Learning responses",
        },
        {
            "name": "DECORATORS",
            "description": "HTTP responses",
        },
    ]
)

# ================================ HTTP RESPONSE ================================

# Sample data for pagination
items = [{"id": i, "value": f"Item {i}"} for i in range(1, 10)]

@app.get("/HTTP_200_OK", tags=["HTTP"])
def ok():
       
    # Build pagination response
    response = SyntaxilitYPagination.build_pagination_response(
        metadata=[],
        total=1,
        page=1,
        limit=1
    )
    
    return SyntaxilitYPyPiResponseManager.HTTP_200_OK(data=response, message="Data fetched successfully")

@app.get("/HTTP_201_CREATED", tags=["HTTP"])
def created():
    # Build pagination response
    response = SyntaxilitYPagination.build_pagination_response(
        metadata=[],
        total=1,
        page=1,
        limit=1
    )
    return SyntaxilitYPyPiResponseManager.HTTP_201_CREATED(data=response, message="Data created successfully")

@app.get("/HTTP_400_BAD_REQUEST", tags=["HTTP"])
def bad():
    return SyntaxilitYPyPiResponseManager.HTTP_400_BAD_REQUEST(message="Bad request")

@app.get("/HTTP_404_NOT_FOUND", tags=["HTTP"])
def not_found():
    return SyntaxilitYPyPiResponseManager.HTTP_404_NOT_FOUND(message="Not found")

@app.get("/HTTP_409_CONFLICT", tags=["HTTP"])
def conflict():
    return SyntaxilitYPyPiResponseManager.HTTP_409_CONFLICT(message="Conflict")

@app.get("/HTTP_422_UNPROCESSABLE_ENTITY", tags=["HTTP"])
def unprocessable():
    return SyntaxilitYPyPiResponseManager.HTTP_422_UNPROCESSABLE_ENTITY(message="Unprocessable entity")

@app.get("/HTTP_429_TOO_MANY_REQUESTS", tags=["HTTP"])
def tooManyRequests():
    return SyntaxilitYPyPiResponseManager.HTTP_429_TOO_MANY_REQUESTS(message="Too many requests")

@app.get("/HTTP_500_INTERNAL_SERVER_ERROR", tags=["HTTP"])
def internal():
    return SyntaxilitYPyPiResponseManager.HTTP_500_INTERNAL_SERVER_ERROR(message="Internal server error")

@app.get("/HTTP_503_SERVICE_UNAVAILABLE", tags=["HTTP"])
def serviceUnavailable():
    return SyntaxilitYPyPiResponseManager.HTTP_503_SERVICE_UNAVAILABLE(message="Service unavailable")

@app.get("/items", tags=["HTTP"])
def get_items(page: int = Query(1, ge=1), limit: int = Query(100, ge=1)):
    # Get pagination params
    pagination_params = SyntaxilitYPagination.get_pagination_params({"page": page, "limit": limit})
    page, limit, skip = pagination_params["page"], pagination_params["limit"], pagination_params["skip"]

    # Slice the items list
    paginated_items = items[skip: skip + limit]

    # Build pagination response
    response = SyntaxilitYPagination.build_pagination_response(
        paginated_items,
        total=len(items),
        page=page,
        limit=limit
    )

    return SyntaxilitYPyPiResponseManager.HTTP_200_OK(response)


client = TestClient(app)

def test_items_pagination():
    r = client.get("/items?page=2&limit=50")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == 200
    assert body["code"] == "HTTP_200_OK"
    assert body["data"]["pagination"]["page"] == 2
    assert body["data"]["pagination"]["limit"] == 50
    assert body["data"]["pagination"]["hasPrevPage"] is True
    assert body["data"]["pagination"]["hasNextPage"] is True
    assert len(body["data"]["data"]) == 50



# ================================ MACHINE LEARNING RESPONSE ================================

# Sample ML dataset
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

@app.post("/ml-fail", tags=["ML"])
def ml_fail():
    metadata = {
        "model": "test_model", 
        "version": "1.0",
        "pagination": SyntaxilitYPagination.build_pagination_response(
            metadata={},
            total=1,
            page=1,
            limit=1
        )["pagination"]
    }
    
    return SyntaxilitYPyPiResponseManager.ML_INFERENCE_FAILED(
        message="Model crashed",
        metadata=metadata
    )

client = TestClient(app)

def test_ml_inference_ok():
    r = client.post("/ml-ok?page=1&limit=2")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == 200
    assert body["code"] == "ML_INFERENCE_OK"
    assert body["message"] == "Paginated ML inference results"
    assert len(body["predictions"]) == 2
    assert body["metadata"]["metadata"]["model"] == "test_model"
    assert body["metadata"]["pagination"]["page"] == 1

def test_ml_inference_failed():
    r = client.post("/ml-fail")
    assert r.status_code == 500
    body = r.json()
    assert body["status"] == 500
    assert body["code"] == "ML_INFERENCE_FAILED"
    assert body["message"] == "Model crashed"
    assert body["metadata"]["error"] == "OOM"
    
    
# ================================ DECORATORS ================================
    
items = [{"id": i, "value": f"Item {i}"} for i in range(1, 10)]

@app.get("/safe-items", tags=["DECORATORS"])
@TryCatch
def safe_items(page: int = Query(1, ge=1), limit: int = Query(3, ge=1)):
    if page < 1:
        raise ValueError("Page must be >= 1")

    pagination_params = SyntaxilitYPagination.get_pagination_params({"page": page, "limit": limit})
    page, limit, skip = pagination_params["page"], pagination_params["limit"], pagination_params["skip"]

    paginated_items = items[skip: skip + limit]

    response = SyntaxilitYPagination.build_pagination_response(
        metadata=paginated_items,
        total=len(items),
        page=page,
        limit=limit
    )

    return SyntaxilitYPyPiResponseManager.HTTP_200_OK(response)
