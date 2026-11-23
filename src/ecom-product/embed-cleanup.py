from itertools import batched
from .db.db import get_db


def delete_unembedded_products(batch_size: int = 2000) -> None:
    db = get_db()
    collection = db["products"]

    unembedded_query = {
        "$or": [
            {"embedding": {"$exists": False}},
            {"embedding": None},
            {"embedding": {"$size": 0}},
        ]
    }

    total_to_delete = collection.count_documents(unembedded_query)
    if total_to_delete == 0:
        print("Database already clean! 0 un-embedded products found.")
        return

    print(f"Found {total_to_delete:,} un-embedded products. Deleting in batches of {batch_size}...")

    deleted_total = 0
    while True:
        # Har iteration mein fresh batch uthao taaki cursor shift na ho
        docs = list(collection.find(unembedded_query, {"_id": 1}).limit(batch_size))
        if not docs:
            break

        ids = [d["_id"] for d in docs]
        res = collection.delete_many({"_id": {"$in": ids}})
        deleted_total += res.deleted_count
        print(f"Deleted {deleted_total:,} / {total_to_delete:,}...")

    remaining_valid = collection.count_documents({"embedding": {"$exists": True}})
    print(f"Cleanup complete! Final embedded product count: {remaining_valid:,}")


if __name__ == "__main__":
    delete_unembedded_products(batch_size=2000)