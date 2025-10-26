from gtts import gTTS
import os

# Test TTS
tts = gTTS('Hello, this is a test', lang='en')
tts.save('test_output.mp3')
print("gTTS test successful! Check test_output.mp3")

# Play audio (platform-specific)
os.system('start test_output.mp3')  # Windows
# os.system('afplay test_output.mp3')  # macOS
# os.system('mpg123 test_output.mp3')  # Linux
