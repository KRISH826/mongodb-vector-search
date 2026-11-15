from .llm import get_llm
from ..vectorstore import hybrid_search

def answer(
    question: str,
    k: int = 5,
    model:str = 'deepseek-v4-pro',
    temperature: float = 0.0,
    max_tokens: int = 2048,
):
    chunks = hybrid_search(question, k)

    context = "\n\n".join(
        f"[{c['source_file']}, page {c['page']}]\n{c['text']}" for c in chunks
    )

    prompt = f"""Answer the question using ONLY the context below.
            If the answer is not in the context, say "I don't know".
            Context:
            {context}

    Question: {question}"""

    response = get_llm(model, temperature, max_tokens).invoke(prompt)
    reply = response.text.strip()
    if not reply:
        finish_reason = response.response_metadata.get("finish_reason", "unknown")
        raise RuntimeError(
            "The model returned no visible answer "
            f"(finish reason: {finish_reason}). Increase the maximum answer length."
        )

    return reply, chunks
