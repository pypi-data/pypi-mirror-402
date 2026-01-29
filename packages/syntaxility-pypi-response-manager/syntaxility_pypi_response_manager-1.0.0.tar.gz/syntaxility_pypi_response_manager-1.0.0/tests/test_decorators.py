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
            "name": "DECORATORS",
            "description": "HTTP responses",
        },
    ]
)

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
