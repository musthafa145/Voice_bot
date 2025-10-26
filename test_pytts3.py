import pyttsx3

# Initialize TTS engine
engine = pyttsx3.init()

# Set properties
engine.setProperty('rate', 150)    # Speed of speech
engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)

# Get available voices
voices = engine.getProperty('voices')
# engine.setProperty('voice', voices[0].id)  # Male voice
# engine.setProperty('voice', voices[1].id)  # Female voice (if available)

# Test speech
engine.say("Hello! Welcome to MYG Kerala. I'm your sales assistant. How can I help you today?")
engine.runAndWait()

print("pyttsx3 test successful!")
