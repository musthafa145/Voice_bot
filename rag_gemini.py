import os
from dotenv import load_dotenv
from google import genai
import chromadb
from chromadb.utils import embedding_functions

# --- Load API key from .env ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Initialize Gemini client ---
client = genai.Client(api_key=GEMINI_API_KEY)

# --- Load Chroma DB ---
chroma_client = chromadb.PersistentClient(path="chroma_db")
collection = chroma_client.get_or_create_collection(
    name="products",
    embedding_function=embedding_functions.GoogleGenerativeAiEmbeddingFunction(
        api_key=GEMINI_API_KEY,
        model_name="models/embedding-001"
    )
)

# --- User query ---
user_query = input("User: ")

# --- Retrieve top 3 products ---
results = collection.query(query_texts=[user_query], n_results=3)
top_products = results["metadatas"][0]

# --- Prepare prompt with product info ---
context_text = ""
for i, p in enumerate(top_products, 1):
    context_text += f"{i}. {p['product_name']} | Category: {p['category']} | Brand: {p['brand']} | " \
                    f"Price: {p['price']} | Features: {p['features']} | Highlights: {p['highlights']} | " \
                    f"Stock: {p['stock_status']}\n"

prompt = f"""
You are a helpful shopping assistant. Here are some products:

{context_text}

Answer the user's query in a friendly way, recommending products if suitable.

User query: "{user_query}"
"""

# --- Call Gemini ---
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt
)

# --- Print response ---
print("\nGemini Assistant:")
print(response.text)
