import streamlit as st

from mongodb_vector_search.rag import answer
from mongodb_vector_search.config import settings


st.set_page_config(page_title="Ask your PDFs", page_icon="🔍", layout="wide")

with st.sidebar:
    st.title("⚙️ Settings")
    st.caption("Adjust how the assistant writes its answer.")

    model = st.selectbox(
        "Model",
        options=settings.available_models,
        index=settings.available_models.index(settings.default_model),
    )

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.5,
        value=0.0,
        step=0.1,
        help="Lower values are more focused and factual; higher values are more varied.",
    )
    max_tokens = st.slider(
        "Maximum answer length",
        min_value=512,
        max_value=10_000,
        value=2_048,
        step=256,
        help="Includes the model's reasoning and visible reply. Use 2,048 or more for analytical questions.",
    )
    retrieval_count = st.slider(
        "PDF sections to search",
        min_value=1,
        max_value=10,
        value=5,
        help="More sections provide more context, but may make answers slower.",
    )

    st.divider()
    st.caption(f"Model: `{model}`")
    st.caption("Answers are based only on retrieved PDF content.")

st.title("Banking Documents")
st.caption("Ask a question about the documents you have indexed in MongoDB.")

with st.form("question_form"):
    question = st.text_area(
        "Question",
        placeholder="For example: Compare Citigroup's 2025 and 2026 profitability trends.",
        height=100,
    )
    submitted = st.form_submit_button(
        "Ask question", type="primary", use_container_width=True
    )

if submitted and question.strip():
    try:
        with st.spinner("Thinking..."):
            reply, chunks = answer(
                question.strip(),
                k=retrieval_count,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        st.subheader("Answer")
        st.write(reply)

        st.subheader("Sources")
        for chunk in chunks:
            title = (
                f"{chunk['source_file']} - page {chunk['page']} "
                f"(score {chunk['score']:.2f})"
            )
            with st.expander(title):
                st.write(chunk["text"])
    except Exception as error:
        st.error(f"Unable to generate an answer: {error}")
elif submitted:
    st.warning("Enter a question before submitting.")
