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


def enrich_exist_product():
    db = get_db()

    category_map = {c["_id"]: c.get("name", "") for c in db["categories"].find()}
    brand_map = {b["_id"]: b.get("name", "") for b in db["brands"].find()}

    ops = []
    for p in db["products"].find():
        semantic_text = build_semantic_text(p, category_map, brand_map)
        ops.append(
            UpdateOne(
                {"_id": p["_id"]},
                {"$set": {"semantic_text": semantic_text}},
            )
        )

    if ops:
        results = db["products"].bulk_write(ops)
        print(f"Updated {results.modified_count} products with semantic_text!")
    else:
        print("No products found in database.")


if __name__ == "__main__":
    enrich_exist_product()
    
