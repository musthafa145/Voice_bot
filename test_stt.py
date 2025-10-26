from google.cloud import speech
import os

# Test STT connection
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'malayalamspeechtest-080e845e78d0.json'
client = speech.SpeechClient()
print("Google Cloud STT Client initialized successfully!")
