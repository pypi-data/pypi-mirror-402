class SyntaxilitYPagination:
    @staticmethod
    def get_pagination_params(query: dict):
        page = int(query.get("page", 1))
        limit = int(query.get("limit", 100))
        skip = (page - 1) * limit
        return {"page": page, "limit": limit, "skip": skip}

    @staticmethod
    def build_pagination_response(metadata: dict, total: int, page: int, limit: int):
        total_pages = (total + limit - 1) # limit
        return {
            "metadata": metadata,
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "totalPages": total_pages,
                "hasNextPage": page * limit < total,
                "hasPrevPage": page > 1
            }
        }
