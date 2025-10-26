from google.cloud import speech
import pyaudio
import io

def record_audio(duration=5):
    import wave
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    WAVE_OUTPUT_FILENAME = "temp_audio.wav"

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True,
                    frames_per_buffer=CHUNK)

    print("🎙️ Speak now (recording for", duration, "seconds)...")
    frames = []
    for _ in range(int(RATE / CHUNK * duration)):
        frames.append(stream.read(CHUNK))
    print("✅ Recording complete.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    return WAVE_OUTPUT_FILENAME


def transcribe_malayalam():
    client = speech.SpeechClient()

    filename = record_audio(duration=5)

    with io.open(filename, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="ml-IN"
    )

    response = client.recognize(config=config, audio=audio)

    for result in response.results:
        print("🗣️ Recognized Malayalam text:", result.alternatives[0].transcript)
        return result.alternatives[0].transcript


if __name__ == "__main__":
    transcribe_malayalam()
