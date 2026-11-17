from pymongo import UpdateOne
from .db.db import get_db
from typing_extensions import Dict, Any, List

def build_semantic_text(
    product: dict, category_map: dict[str, str], brand_map: dict[str, str]
) -> str:
    title = product.get("title") or product.get("name") or ""
    category = category_map.get(product.get("category_id", ""), "")
    brand = brand_map.get(product.get("brand_id", ""), "")
    price = product.get("price", "")
    description = product.get("description", "")
    tags = ", ".join(product.get("tags", []))

    specs = product.get("specs", {})
    specs_text = (
        ", ".join(f"{k}: {v}" for k, v in specs.items() if v)
        if isinstance(specs, dict)
        else ""
    )

    parts = [
        f"Product: {title}." if title else "",
        f"Brand: {brand}." if brand else "",
        f"Category: {category}." if category else "",
        f"Price: {price}." if price else "",
        f"Description: {description}." if description else "",
        f"Specifications: {specs_text}." if specs_text else "",
        f"Tags and Use Cases: {tags}." if tags else "",
    ]
    return " ".join(p for p in parts if p)


def enrich_exist_product(batch_size: int = 200):
    db = get_db()

    category_map = {
        c["_id"]: c.get("name", "") 
        for c in db["categories"].find({}, {"_id": 1, "name": 1})
    }
    brand_map = {
        b["_id"]: b.get("name", "") 
        for b in db["brands"].find({}, {"_id": 1, "name": 1})
    }


    # Projection: Sirf zaroori fields hi MongoDB se mangwayein
    projection = {
        "_id": 1,
        "title": 1,
        "name": 1,
        "category_id": 1,
        "brand_id": 1,
        "price": 1,
        "description": 1,
        "tags": 1,
        "specs": 1,
    }

    cursor = db["products"].find({}, projection).batch_size(batch_size)
    ops = []
    total_processed = 0
    total_modified = 0
    for p in cursor:
        semantic_text = build_semantic_text(p, category_map, brand_map)
        ops.append(
            UpdateOne(
                {"_id": p["_id"]},
                {"$set": {"semantic_text": semantic_text}},
            )
        )

    if len(ops) >= batch_size:
        result = db["products"].bulk_write(ops, ordered= False)
        total_processed += len(ops)
        total_modified += result.modified_count
        ops.clear()  # Memory free karne ke liye zaroori hai
        print(f"Processed: {total_processed} | Modified: {total_modified}")


    if ops:
        results = db["products"].bulk_write(ops, ordered=False)
        total_processed += len(ops)
        total_modified += results.modified_count
        ops.clear()
    else:
        print("No products found in database.")

    print(f"Completed! Total Processed: {total_processed}, Total Modified: {total_modified}")

if __name__ == "__main__":
    enrich_exist_product()
    
