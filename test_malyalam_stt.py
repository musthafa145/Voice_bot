import os
import pyaudio
from dotenv import load_dotenv
from google.cloud import speech

# Load environment variables
load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

RATE = 16000
CHUNK = int(RATE / 10)

def stream_generator(mic_stream):
    while True:
        yield mic_stream.read(CHUNK, exception_on_overflow=False)

def main():
    client = speech.SpeechClient()

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="ml-IN",
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True
    )

    mic = pyaudio.PyAudio()
    mic_stream = mic.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )

    print("🎤 Listening... (Ctrl+C to stop)")

    audio_generator = stream_generator(mic_stream)
    requests = (
        speech.StreamingRecognizeRequest(audio_content=chunk)
        for chunk in audio_generator
    )

    try:
        responses = client.streaming_recognize(streaming_config, requests)
        for response in responses:
            for result in response.results:
                if result.is_final:  # Only final transcript
                    print("🗣️", result.alternatives[0].transcript)
    except KeyboardInterrupt:
        print("\n🛑 Stopped listening.")
    finally:
        mic_stream.stop_stream()
        mic_stream.close()
        mic.terminate()

if __name__ == "__main__":
    main()
