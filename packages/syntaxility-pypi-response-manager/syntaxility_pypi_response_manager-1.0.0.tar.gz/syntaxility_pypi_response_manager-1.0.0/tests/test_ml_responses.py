from fastapi import FastAPI, Query
from fastapi.testclient import TestClient
from syntaxility_pypi_response_manager import SyntaxilitYPyPiResponseManager, SyntaxilitYPagination

app = FastAPI()

# Sample ML dataset
ml_results = [
    {"input": [1, 2], "prediction": 0},
    {"input": [3, 4], "prediction": 1},
    {"input": [5, 6], "prediction": 1},
    {"input": [7, 8], "prediction": 0},
    {"input": [9, 10], "prediction": 1},
]

@app.post("/ml-ok")
def ml_ok(page: int = Query(1, ge=1), limit: int = Query(2, ge=1)):
    # Pagination params
    pagination_params = SyntaxilitYPagination.get_pagination_params({"page": page, "limit": limit})
    page, limit, skip = pagination_params["page"], pagination_params["limit"], pagination_params["skip"]

    # Slice dataset
    paginated_predictions = ml_results[skip: skip + limit]

    # Build metadata including pagination info
    metadata = {
        "metadata": {"model": "test_model", "version": "1.0"},
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

@app.post("/ml-fail")
def ml_fail():
    return SyntaxilitYPyPiResponseManager.ML_INFERENCE_FAILED(
        message="Model crashed",
        metadata={"error": "OOM"}
    )

client = TestClient(app)

# ========== TESTS ==========

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
