from .llm import get_llm
from ..vectorstore import search

def answer(question: str, k: int = 5):
    chunks = search(question, k)

    context = "\n\n".join(
        f"[{c['source_file']}, page {c['page']}]\n{c['text']}" for c in chunks
    )

    prompt = f"""Answer the question using ONLY the context below.
            If the answer is not in the context, say "I don't know".
            Context:
            {context}

    Question: {question}"""

    response = get_llm().invoke(prompt)
    return response.content, chunks