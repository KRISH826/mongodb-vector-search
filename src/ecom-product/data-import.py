import json
from pathlib import Path
from pymongo import ReplaceOne
from .db.db import get_db

DATA_DIR = Path(__file__).resolve().parent / "data"
FILES = ["categories", "brands", "products"]


def import_file(name: str) -> int:
    path = DATA_DIR / f"{name}.json"
    docs = json.loads(path.read_text(encoding="utf-8"))
    ops = [ReplaceOne({"_id": d["_id"]}, d, upsert=True) for d in docs]
    get_db()[name].bulk_write(ops)
    return len(docs)


def main():
    for name in FILES:
        count = import_file(name)
        print(f"{name}: {count} documents")


if __name__ == "__main__":
    main()