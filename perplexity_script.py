import queue
import sys
import pyaudio
from google.cloud import speech

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms chunks

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
        """Continuously collect data from the audio stream."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        """Stream audio from microphone to API."""
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]
            
            # Consume buffered data
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
    """Iterates through server responses and prints them in real-time."""
    
    for response in responses:
        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript

        # Display interim results (overwrites previous line)
        if not result.is_final:
            print(f'\rInterim: {transcript}', end='', flush=True)
        else:
            # Display final results on new line
            print(f'\nFinal: {transcript}')


def main():
    """Start real-time speech recognition from microphone."""
    
    # Initialize Speech client
    client = speech.SpeechClient()

    # Configuration for Malayalam and English
    # Option 1: Auto-detect language
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="ml-IN",  # Primary language: Malayalam
        alternative_language_codes=["en-IN"],  # Alternative: English
        max_alternatives=1,
    )
    
    # Option 2: Explicit multi-language support
    # For automatic language detection, use:
    # language_code="ml-IN"
    # alternative_language_codes=["en-IN", "en-US"]

    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True  # Enable real-time interim results
    )

    print("🎤 Starting real-time speech recognition...")
    print("Supported languages: Malayalam (മലയാളം) and English")
    print("Speak now! (Press Ctrl+C to stop)\n")

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )

        responses = client.streaming_recognize(streaming_config, requests)
        
        # Process responses and print in real-time
        listen_print_loop(responses)


if __name__ == '__main__':
    main()
