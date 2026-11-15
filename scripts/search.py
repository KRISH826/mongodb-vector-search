import sys
from mongodb_vector_search.vectorstore import search


query = input("Enter your question: ")
results = search(query, k=3)

for r in results:
    print("Score:", round(r["score"], 2))
    print("File:", r["source_file"], "| Page:", r["page"])
    print("Text:", r["text"][:300])
    print("-" * 40)
