from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .db import get_collection
from .embeddings import embed_batch

def load_pdfs(folder: str):
    docs = []
    for pdf in Path(folder).glob("**/*.pdf"):
        try:
            pages = PyPDFLoader(str(pdf)).load()
            for p in pages:
                p.metadata["source_file"] = pdf.name

            docs.extend(pages)
            print(f"loaded {pdf.name}: {len(pages)} pages")
        except Exception as e:
            print(f"error in {pdf.name}: {e}")
    return docs

def split_docs(docs, chunk_size=1000, chunk_overlap = 200):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = chunk_size,
        chunk_overlap = chunk_overlap
    )

    return splitter.split_documents(docs)


def ingest (folder:str):
    docs = load_pdfs(folder)
    chunks = split_docs(docs)

    texts = [c.page_content for c in chunks]
    vectors = embed_batch(texts)

    records = [
        {
            "texts": c.page_content,
            "source_file": c.metadata["source_file"],
            "page": c.metadata.get("page", 0) + 1,
            "embedding": v,
        }
        for c , v in zip(chunks, vectors)
    ]

    collection = get_collection()
    collection.delete_many({})
    collection.insert_many(records)
    print(f"stored {len(records)} chunks")
