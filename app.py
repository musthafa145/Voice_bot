import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
import google.generativeai as genai
import os

# --- CONFIG ---
os.environ["GOOGLE_API_KEY"] = "AIzaSyCO9pLa6ctDJSQCuNJWfYG4cdj9ZdQINns"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# --- LOAD CSV ---
df = pd.read_csv("synthetic_myg_products.csv").fillna("")

df["combined"] = df.apply(
    lambda x: f"Product: {x['product_name']} | Category: {x['category']} | Brand: {x['brand']} | "
              f"Price: {x['price']} | Features: {x['features']} | Highlights: {x['highlights']} | "
              f"Stock: {x['stock_status']}", axis=1)

# --- INIT PERSISTENT CHROMA ---
client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_or_create_collection(
    name="products",
    embedding_function=embedding_functions.GoogleGenerativeAiEmbeddingFunction(
        api_key=os.environ["GOOGLE_API_KEY"],
        model_name="models/embedding-001"
    )
)

# --- EMBED & STORE ---
collection.add(
    ids=[str(i) for i in range(len(df))],
    documents=df["combined"].tolist(),
    metadatas=df.to_dict("records")
)

print(f"✅ Stored {len(df)} products persistently in Chroma collection.")
