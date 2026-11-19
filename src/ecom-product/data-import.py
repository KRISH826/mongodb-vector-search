import json
from pathlib import Path
from pymongo import ReplaceOne
from typing import Any
from .db.db import get_db

DATA_DIR = Path(__file__).resolve().parent / "data"
FILES = ["categories", "brands", "products"]




# def import_file(name: str) -> int:
#     path = DATA_DIR / f"{name}.json"
#     docs = json.loads(path.read_text(encoding="utf-8"))
#     ops = [ReplaceOne({"_id": d["_id"]}, d, upsert=True) for d in docs]
#     get_db()[name].bulk_write(ops)
#     return len(docs)


# def main():
#     for name in FILES:
#         count = import_file(name)
#         print(f"{name}: {count} documents")


# if __name__ == "__main__":
#     main()


def normalize_product(doc: dict[str, Any]) -> dict[str,Any]:
    """80k dataset ke fields ko clean & lowercase-safe banata hai fast pre-filtering ke liye."""

    if isinstance(doc.get("gift_for"), list):
        doc["gift_for"] = [str(x).strip().lower() for x in doc["gift_for"] if x]

    if isinstance(doc.get("occasions"), list):
        doc["occasions"] = [str(x).strip().lower() for x in doc["occasions"] if x]

    intent = doc.get("intent")
    if isinstance(intent, dict):
        if intent.get("gender"):
            intent["gender"] = str(intent["gender"]).strip().lower()
        if intent.get("style"):
            intent["style"] = str(intent["style"]).strip().lower()
        if intent.get("season"):
            intent["season"] = str(intent["season"]).strip().lower()
        if intent.get("age_group"):
            intent["age_group"] = str(intent["age_group"]).strip().lower()
        if isinstance(intent.get("vibe_keywords"), list):
            intent["vibe_keywords"] = [
                str(k).strip().lower() for k in intent["vibe_keywords"] if k
            ]

    return doc        



def reset_import_data(file_path: str, batch_size= 2000) -> None:
    db = get_db()
    collection = db["products"]

    collection.drop()
    print("existing data collection drop successfully")

    path = Path(file_path)
    if not path.exists:
        raise FileNotFoundError(f"Dataset not found at: {path.resolve()}")

    with path.open("r", encoding="utf-8") as f:
        products: list[dict[str, Any]] = json.load(f)

    total = len(products)
    print(f"Total records loaded: {total}. Starting batched import...")

    inserted_data = 0

    for start in range(0, total, batch_size):
        batch = [normalize_product(doc) for doc in products[start: start + batch_size]]
        result = collection.insert_many(batch, ordered= False)
        inserted_data += len(result.inserted_ids)
        print(f"Inserted {inserted_data}/{total} products...")


    collection.create_index("sku", unique=True)
    collection.create_index("is_active")

    print("Import complete! Standard indexes created.")



if __name__ == "__main__":
    reset_import_data("src/ecom-product/data/products_80000.json", batch_size=2000)




