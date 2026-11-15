from mongodb_vector_search.db import get_collection

query = {"page": 2, "source_file": {"$regex": "JPMorgan"}}

for d in get_collection().find(query):
    print("-" * 60)
    print(d["texts"])