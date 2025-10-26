"""
Speech Handler Module
Handles Text-to-Speech (pyttsx3) and Speech-to-Text (Google Cloud)
"""

import pyttsx3
import pyaudio
import wave
import os
from google.cloud import speech
import time

class SpeechHandler:
    def __init__(self, google_credentials_path):
        """Initialize TTS and STT clients"""
        
        # Set up Google Cloud credentials
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = google_credentials_path
        
        # Initialize Text-to-Speech (pyttsx3)
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 150)  # Speed of speech
        self.tts_engine.setProperty('volume', 1.0)  # Volume
        
        # Get available voices
        voices = self.tts_engine.getProperty('voices')
        if len(voices) > 0:
            self.tts_engine.setProperty('voice', voices[0].id)  # Default voice
        
        # Initialize Speech-to-Text client
        self.stt_client = speech.SpeechClient()
        
        # Audio recording settings
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        
        print("✓ Speech Handler initialized")
    
    
    def speak(self, text):
        """
        Convert text to speech and play it
        """
        print(f"\nBot: {text}")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()
    
    
    def listen(self, timeout=120):
        """
        Record audio from microphone with timeout
        Returns transcribed text or None if timeout
        
        Args:
            timeout: Maximum seconds to wait for speech (default 120 = 2 minutes)
        """
        print("\nUser: ", end="", flush=True)
        
        audio = pyaudio.PyAudio()
        
        # Open microphone stream
        stream = audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        
        print("Listening...", end="", flush=True)
        
        frames = []
        silence_threshold = 500  # Amplitude threshold for silence
        silence_duration = 0
        max_silence = 3  # 3 seconds of silence = end of speech
        recording = False
        start_time = time.time()
        
        try:
            while True:
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    print("\n[Timeout - 2 minutes of silence]")
                    return None
                
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                frames.append(data)
                
                # Calculate audio level
                audio_level = sum(abs(int.from_bytes(data[i:i+2], 'little', signed=True)) 
                                for i in range(0, len(data), 2)) / len(data) * 2
                
                # Detect speech start
                if audio_level > silence_threshold:
                    recording = True
                    silence_duration = 0
                    print(".", end="", flush=True)
                else:
                    if recording:
                        silence_duration += 1
                
                # End recording after silence
                if recording and silence_duration > max_silence * (self.RATE / self.CHUNK):
                    break
                
        except KeyboardInterrupt:
            print("\n[Recording stopped by user]")
            return None
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()
        
        if not recording:
            print("\n[No speech detected]")
            return None
        
        # Save audio to temporary file
        temp_audio = "temp_audio.wav"
        wf = wave.open(temp_audio, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(audio.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        # Transcribe using Google Cloud STT
        try:
            with open(temp_audio, 'rb') as audio_file:
                content = audio_file.read()
            
            audio_data = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=self.RATE,
                language_code='en-IN',  # English (India)
            )
            
            response = self.stt_client.recognize(config=config, audio=audio_data)
            
            # Get transcription
            if response.results:
                transcript = response.results[0].alternatives[0].transcript
                print(f"\r{transcript}")
                return transcript
            else:
                print("\n[Could not understand audio]")
                return None
                
        except Exception as e:
            print(f"\n[Error transcribing: {e}]")
            return None
        finally:
            # Clean up temp file
            if os.path.exists(temp_audio):
                os.remove(temp_audio)
    
    
    def test_tts(self):
        """Test text-to-speech"""
        self.speak("Hello! This is a test of the text to speech system.")
    
    
    def test_stt(self):
        """Test speech-to-text"""
        print("Testing Speech-to-Text...")
        print("Please speak something...")
        result = self.listen(timeout=10)
        if result:
            print(f"You said: {result}")
        else:
            print("No speech detected or timeout")


# Test the module
if __name__ == "__main__":
    print("Testing Speech Handler Module")
    print("="*60)
    
    # Initialize (update path to your credentials)
    handler = SpeechHandler('./malayalamspeechtest-080e845e78d0.json')
    
    # Test TTS
    print("\n1. Testing Text-to-Speech...")
    handler.test_tts()
    
    # Test STT
    print("\n2. Testing Speech-to-Text...")
    handler.test_stt()
    
    print("\n" + "="*60)
    print("Speech Handler test complete!")
