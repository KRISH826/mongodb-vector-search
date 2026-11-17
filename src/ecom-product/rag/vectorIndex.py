from pymongo.errors import OperationFailure
from pymongo.operations import SearchIndexModel
from ..config.config import settings
from ..db.db import get_db

def create_vector_index():
    db = get_db()
    collection = db["products"]

    # Production Vector Search Index Definition (Vector + Pre-Filter fields)

    index_verification = {
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": int(settings.embedding_dim),  # 384 (strict int)
                "similarity": "cosine",
            },
            {"type": "filter", "path": "is_active"},
            {"type": "filter", "path": "budget_bucket"},
            {"type": "filter", "path": "gift_for"},
            {"type": "filter", "path": "occasions"},
            {"type": "filter", "path": "stock"},
            {"type": "filter", "path": "price.selling_price"},
        ]
    }

    search_index_model = SearchIndexModel(
        definition=index_verification,
        name=settings.vector_index_name,
        type="vectorsearch"
    )

    try:
        result = collection.create_search_index(model=search_index_model)
        print(f"Vector Search Index '{result}' creation initiated successfully!")
    except OperationFailure as e:
        print(f"MongoDB Index Error: {e.details}")


# main function

if __name__ == "__main__":
    create_vector_index()
