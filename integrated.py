from gtts import gTTS
from playsound import playsound
import os
from google import genai
import chromadb
from chromadb.utils import embedding_functions

# ---------------- TTS ----------------
def speak_malayalam(text):
    tts = gTTS(text=text, lang='ml')
    filename = "response.mp3"
    tts.save(filename)
    playsound(filename)
    os.remove(filename)

# ---------------- Gemini + RAG ----------------
def gemini_response(user_text):
    # Load your Chroma collection
    chroma_client = chromadb.PersistentClient(path="chroma_db")
    collection = chroma_client.get_or_create_collection(
        name="products",
        embedding_function=embedding_functions.GoogleGenerativeAiEmbeddingFunction(
            api_key=os.getenv("GEMINI_API_KEY"),
            model_name="models/embedding-001"
        )
    )

    # Retrieve top 3 products
    results = collection.query(query_texts=[user_text], n_results=3)
    top_products = results["metadatas"][0]

    # Prepare prompt
    context_text = ""
    for i, p in enumerate(top_products, 1):
        context_text += f"{i}. {p['product_name']} | Category: {p['category']} | Brand: {p['brand']} | " \
                        f"Price: {p['price']} | Features: {p['features']} | Highlights: {p['highlights']} | " \
                        f"Stock: {p['stock_status']}\n"

    prompt = f"""
    You are a helpful shopping assistant. Here are some products:

    {context_text}

    Answer the user's query in a friendly way, recommending products if suitable.

    User query: "{user_text}"
    """

    # Call Gemini
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text

# ---------------- Real-time STT ----------------
# In your existing real-time STT loop, just replace:
# print(f'\nFinal: {transcript}')
# with:
# response = gemini_response(transcript)
# speak_malayalam(response)
