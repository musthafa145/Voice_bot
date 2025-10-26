# myg_voicebot_combined.py
import os
import queue
import pyaudio
import requests
from gtts import gTTS
from playsound import playsound
from google.cloud import speech
from google import genai
from dotenv import load_dotenv
import time

# ------------------ Load Environment ------------------
load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
API_URL = "http://127.0.0.1:8000"  # Synthetic MCP API

# ------------------ Config ------------------
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms
SILENCE_THRESHOLD = 2.0  # seconds to wait before processing

# ------------------ TTS ------------------
def speak_malayalam(text):
    tts = gTTS(text=text, lang='ml')
    filename = "response.mp3"
    tts.save(filename)
    playsound(filename)
    os.remove(filename)

# ------------------ MCP API ------------------
def fetch_products(query=None, category=None, max_price=None, limit=3):
    params = {}
    if query:
        params["q"] = query
    if category:
        params["category"] = category
    if max_price:
        params["max_price"] = max_price
    params["limit"] = limit
    
    try:
        response = requests.get(f"{API_URL}/search", params=params, timeout=5)
        print(f"🔍 API Request: {API_URL}/search with params: {params}")
        print(f"📡 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Products found: {len(data)}")
            return data
        else:
            print(f"❌ API returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ API request failed: {e}")
    return []

# ------------------ Gemini ------------------
def gemini_response(user_text):
    # Check if greeting or casual conversation
    greetings = ["നമസ്കാരം", "ഹലോ", "ഹായ്", "സുഖമല്ലേ", "എങ്ങനെയുണ്ട്"]
    is_greeting = any(greeting in user_text for greeting in greetings)
    
    # Extract product keywords
    product_keywords = ["ലാപ്ടോപ്പ്", "ലാപ്ടോപ്", "laptop", "മൊബൈൽ", "ഫോൺ", "mobile", "phone", "കമ്പ്യൂട്ടർ", "computer"]
    has_product_intent = any(keyword in user_text.lower() for keyword in product_keywords)
    
    if is_greeting and not has_product_intent:
        prompt = f"""
You are a friendly Malayalam-speaking shopping assistant. The user greeted you.

User said: "{user_text}"

Respond warmly in Malayalam and ask how you can help them today. Keep it friendly and conversational.
"""
        client = genai.Client(api_key=GEMINI_KEY)
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt
        )
        return response.text
    
    # Fetch products
    top_products = fetch_products(query=user_text, limit=5)
    
    if not top_products:
        # Try broader search
        if "ലാപ്ടോപ്" in user_text or "laptop" in user_text.lower():
            top_products = fetch_products(category="Electronics", limit=5)
        elif "മൊബൈൽ" in user_text or "ഫോൺ" in user_text or "mobile" in user_text.lower() or "phone" in user_text.lower():
            top_products = fetch_products(category="Electronics", limit=5)
    
    if not top_products:
        return """നമസ്കാരം! ഞാൻ നിങ്ങളെ സഹായിക്കാൻ ഇവിടെയുണ്ട്. നിങ്ങൾക്ക് ഏത് തരം ഉൽപ്പന്നമാണ് വേണ്ടത്? Electronics, Home Appliances, Clothing, അതോ മറ്റെന്തെങ്കിലുമോ?"""

    # Prepare context for Gemini
    context_text = ""
    for i, p in enumerate(top_products, 1):
        context_text += f"{i}. {p.get('product_name', 'N/A')} | Category: {p.get('category', 'N/A')} | Brand: {p.get('brand', 'N/A')} | " \
                        f"Price: ₹{p.get('price', 'N/A')} | Features: {p.get('features', 'N/A')} | " \
                        f"Highlights: {p.get('highlights', 'N/A')} | Stock: {p.get('stock_status', 'Available')}\n"

    prompt = f"""
You are a helpful and friendly shopping assistant speaking Malayalam. Your role is to help users find the right products.

Available products:
{context_text}

User query: "{user_text}"

Instructions:
1. Be warm and conversational
2. Recommend the most relevant products from the list above
3. Ask clarifying questions to understand their needs better (budget, preferred brand, specific features)
4. Mention key features and prices
5. If multiple options exist, ask what matters most to them
6. Always respond in natural, friendly Malayalam

Keep your response concise and engaging.
"""
    
    client = genai.Client(api_key=GEMINI_KEY)
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=prompt
    )
    return response.text

# ------------------ Real-time STT ------------------
class MicrophoneStream:
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break
            yield b''.join(data)

def listen_print_loop(responses):
    last_transcript_time = None
    pending_transcript = ""
    
    for response in responses:
        if not response.results:
            continue
            
        result = response.results[0]
        
        if not result.alternatives:
            continue
        
        transcript = result.alternatives[0].transcript
        
        if result.is_final:
            pending_transcript = transcript
            last_transcript_time = time.time()
            print(f"🗣️ You said: {transcript}")
        else:
            # Check if user paused
            if pending_transcript and last_transcript_time:
                elapsed = time.time() - last_transcript_time
                if elapsed >= SILENCE_THRESHOLD:
                    # Process the pending transcript
                    user_text = pending_transcript
                    print(f"\n💭 Processing: {user_text}")
                    
                    answer = gemini_response(user_text)
                    print(f"🤖 Gemini: {answer}\n")
                    speak_malayalam(answer)
                    
                    # Reset
                    pending_transcript = ""
                    last_transcript_time = None
                    print("🎤 Listening...")
        
        # Also process immediately on final if no new speech for threshold time
        if result.is_final and pending_transcript:
            time.sleep(SILENCE_THRESHOLD)
            if pending_transcript:  # Still no new speech
                user_text = pending_transcript
                print(f"\n💭 Processing: {user_text}")
                
                answer = gemini_response(user_text)
                print(f"🤖 Gemini: {answer}\n")
                speak_malayalam(answer)
                
                pending_transcript = ""
                last_transcript_time = None
                print("🎤 Listening...")

# ------------------ Main ------------------
def main():
    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="ml-IN",
        enable_automatic_punctuation=True,
    )
    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True,
        single_utterance=False
    )

    print("🎤 നമസ്കാരം! Speak Malayalam now... (Ctrl+C to stop)")

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests_stream = (speech.StreamingRecognizeRequest(audio_content=chunk) for chunk in audio_generator)
        responses = client.streaming_recognize(streaming_config, requests_stream)
        listen_print_loop(responses)

if __name__ == "__main__":
    main()
