import os
import queue
import pyaudio
from google.cloud import speech
from gtts import gTTS
from playsound import playsound
from google import genai
import chromadb
from chromadb.utils import embedding_functions

# ------------------ TTS ------------------
def speak_malayalam(text):
    tts = gTTS(text=text, lang='ml')
    filename = "response.mp3"
    tts.save(filename)
    playsound(filename)
    os.remove(filename)

# ------------------ Gemini + RAG ------------------
def gemini_response(user_text):
    # Load Chroma collection
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

    # Prepare context for Gemini
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

# ------------------ Real-time STT ------------------
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

class MicrophoneStream:
    """Opens a recording stream as a generator yielding audio chunks."""
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
    """Iterates through server responses and sends final transcript to Gemini + TTS"""
    for response in responses:
        if not response.results:
            continue
        result = response.results[0]
        if not result.alternatives:
            continue
        transcript = result.alternatives[0].transcript
        if not result.is_final:
            print(f'\r📝 Interim: {transcript}', end='', flush=True)
        else:
            print(f'\n🎯 Final (Malayalam): {transcript}')
            # Send to Gemini and speak back
            answer = gemini_response(transcript)
            print(f'💬 Gemini says: {answer}')
            speak_malayalam(answer)
            print("\n🎤 Speak your next query...")

def main():
    # Ensure Google credentials loaded
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("❌ Set GOOGLE_APPLICATION_CREDENTIALS environment variable to your credentials.json")
        return

    print("🎤 Starting real-time Malayalam voice assistant...")
    print("Press Ctrl+C to exit\n")

    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="ml-IN",
        alternative_language_codes=["en-IN"],
        max_alternatives=1,
    )
    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True
    )

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (speech.StreamingRecognizeRequest(audio_content=content) for content in audio_generator)
        responses = client.streaming_recognize(streaming_config, requests)
        listen_print_loop(responses)

if __name__ == "__main__":
    main()
