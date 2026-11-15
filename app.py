import streamlit as st

st.set_page_config(page_title="MongoDB Vector Search", page_icon="🔍")
st.title("🔍 MongoDB Vector Search")

st.subheader("System status")

if st.button("Test MongoDB connection"):
    try:
        # Import yahan hai taaki .env missing ho to error UI mein dikhe
        from mongodb_vector_search.db import ping

        ping()
        st.success("MongoDB connected ✅")
    except Exception as e:
        st.error(f"MongoDB connection failed: {e}")