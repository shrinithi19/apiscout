import chromadb
from chromadb.utils import embedding_functions

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def store_in_chromadb(pages_content: dict, collection_name: str = "apiscout") -> chromadb.Collection:
    client = chromadb.Client()

    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    try:
        client.delete_collection(collection_name)
    except:
        pass

    collection = client.create_collection(
        name=collection_name,
        embedding_function=embedding_fn
    )

    doc_id = 0
    for url, text in pages_content.items():
        chunks = chunk_text(text)
        for chunk in chunks:
            collection.add(
                documents=[chunk],
                metadatas=[{"source": url}],
                ids=[f"doc_{doc_id}"]
            )
            doc_id += 1

    print(f"Stored {doc_id} chunks in ChromaDB")
    return collection


def query_collection(collection: chromadb.Collection, query: str, n_results: int = 5) -> list[str]:
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return results["documents"][0]