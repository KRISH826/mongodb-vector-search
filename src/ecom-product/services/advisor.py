from langchain_groq import ChatGroq
from ..config.config import settings
from typing import Any
from pydantic import SecretStr


def ai_advisor(user_query: str, products: list[dict[str, Any]]) -> str:
    if not products:
        return "Sorry Your Criteria Does Not Match With Us"

    if not settings.groq_api_key:
        top_names = ", ".join(p.get("name", "Product") for p in products[:3])
        return f"Top matching products for your search: {top_names}."

    try:
        llm = ChatGroq(
            api_key=SecretStr(settings.groq_api_key),
            model = settings.groq_api_model,
            temperature= 0.2,
            max_retries=2,
        )

        catalog_context = "\n".join(
            f"- {p.get('name')} | Price: ₹{p.get('price', {}).get('selling_price', 'N/A')} | "
            f"Details: {p.get('search_text', '')}"
            for p in products
        )

        prompt = (
            "You are a helpful Indian e-commerce shopping assistant. "
            "Recommend the best options from the VERIFIED CATALOG below based on the user's request.\n"
            "Rules:\n"
            "1. ONLY recommend products listed in the catalog below. Never invent products or prices.\n"
            "2. Mention exact prices in INR (₹) and explain briefly why each option fits their need.\n"
            "3. Match the user's language style (English or natural Hinglish) concisely.\n\n"
            f"User Request: {user_query}\n\n"
            f"VERIFIED CATALOG:\n{catalog_context}"
        )

        response = llm.invoke(prompt)
        return str(response.content)
    except Exception as e:
        print(f"[Warning] Advisor LLM fallback triggered: {e}")
        return f"Top recommendations: {top_names}."