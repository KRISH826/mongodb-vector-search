page = {
    "page_number": 187,
    "text": "Net income"
}

print(page["page_number"])

tables = ["T1", "T2"]
print(tables[0])
tables.append("T3")

# loops

tables = ["Income Statement", "Balance Sheet", "Cash Flow"]

for t in tables:
    print(t)

pages = [
    {"page_number": 1, "text": "Net income was 49.6 billion", "tables": ["Income Statement"]},
    {"page_number": 2, "text": "Risk factors overview", "tables": []},
    {"page_number": 3, "text": "Balance sheet and cash flow", "tables": ["Balance Sheet", "Cash Flow"]},
]

for p in pages:
    print(f"the dataset is: {p["page_number"]}")
    print(f"the text is: {p["text"]}")
    print(f"the tables is: {p["tables"]}")


def add(a, b):
    return a + b