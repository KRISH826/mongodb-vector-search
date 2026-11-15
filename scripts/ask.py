from mongodb_vector_search.rag import answer

question = "What was JPMorgan's net income?"
reply, chunks = answer(question)
print("ANSWER:")
print(reply)

print("\nSOURCES:")
for c in chunks:
    score = round(c["score"], 2)
    print("-", c["source_file"], "| Page:", c["page"], "| Score:", score)

