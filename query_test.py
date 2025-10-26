import chromadb
from chromadb.utils import embedding_functions
import os, json

os.environ["GOOGLE_API_KEY"] = "AIzaSyCO9pLa6ctDJSQCuNJWfYG4cdj9ZdQINns"

# Load persistent Chroma DB
client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_or_create_collection(
    name="products",
    embedding_function=embedding_functions.GoogleGenerativeAiEmbeddingFunction(
        api_key=os.environ["GOOGLE_API_KEY"],
        model_name="models/embedding-001"
    )
)

query = input("Ask about a product: ")

results = collection.query(
    query_texts=[query],
    n_results=3
)

print("\n--- TOP MATCHES ---")
for i, meta in enumerate(results["metadatas"][0]):
    print(f"\nResult {i+1}")
    print("Product Name:", meta.get("product_name", "N/A"))
    print("Category:", meta.get("category", "N/A"))
    print("Brand:", meta.get("brand", "N/A"))
    print("Price:", meta.get("price", "N/A"))
    print("Highlights:", meta.get("highlights", "N/A"))
