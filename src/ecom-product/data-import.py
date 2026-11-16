import json
import sys
from pathlib import Path
from pymongo import ReplaceOne

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db.db import get_db  # type: ignore[reportMissingImports]


DATA_DIR = Path("data")
FILES = ["categories", "brands", "products"]

def import_file(name:str) -> str:
    path = DATA_DIR
    docs = json.loads(path.read_text(encoding="utf-8"))
    ops = [ReplaceOne({"_id": d["_id"]}, d, upsert=True) for d in docs]
    get_db()[name].bulk_write(ops)
    return len(docs) # pyright: ignore[reportReturnType]



def main():
    for name in FILES:
        count = import_file(name)
        print(f"{name}: {count} documents")

if __name__ == "__main__":
    main()        