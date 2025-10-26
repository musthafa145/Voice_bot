import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

# MCP Settings
MCP_HOST = os.getenv('MCP_HOST', 'localhost')
MCP_PORT = int(os.getenv('MCP_PORT', 8080))

# Audio Settings
SAMPLE_RATE = int(os.getenv('SAMPLE_RATE', 16000))
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1024))
SILENCE_TIMEOUT = int(os.getenv('SILENCE_TIMEOUT', 120))

# TTS Settings
USE_OFFLINE_TTS = True  # Set to True to use pyttsx3, False for gTTS
TTS_RATE = 150  # Speech rate for pyttsx3
TTS_VOLUME = 1.0  # Volume for pyttsx3

# Conversation Settings
BOT_NAME = "MYG Sales Assistant"
WELCOME_MESSAGE = "Hello! Welcome to MYG Kerala. I'm your sales assistant. How can I help you today?"
