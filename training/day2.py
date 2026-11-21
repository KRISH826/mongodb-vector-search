import json
from pydantic import BaseModel, Field

data = {"page_number": 1, "tables": ["Income Statement"]}

with open("page1.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent = 2)


with open("page1.json", "r", encoding="utf-8") as f:
    loaded = json.load(f)

print(loaded["tables"])    

# open(..., "w") likhne ke liye, "r" padhne ke liye.
# with file apne aap band kar deta hai, tumhe close() yaad nahi rakhna.
# json.dump Python dict ko file mein likhta hai, json.load wapas dict banata hai.

try:
    with open("missing.json", "r", encoding="utf-8") as k:
        data = json.load(k)

except FileNotFoundError:
    print("nahi mila")
except json.JSONDecodeError:
    print("json kharab hain")    


class Page(BaseModel):
    page_number: int
    text: str
    tables: list[str] = Field(default_factory=list)

p = Page(page_number= 1, text= 'hi i am krishnendu panja')
print(p.page_number)
print(p.tables)
print(p.model_dump())

