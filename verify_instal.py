import sys

def check_imports():
    packages = {
        'google.genai': 'Google GenAI SDK',
        'google.cloud.speech': 'Google Cloud Speech-to-Text',
        'fastmcp': 'FastMCP',
        'gtts': 'gTTS',
        'pyttsx3': 'pyttsx3 (Offline TTS)',
        'pyaudio': 'PyAudio',
        'webrtcvad': 'WebRTC VAD',
        'dotenv': 'Python-dotenv',
        'pydub': 'Pydub'
    }
    
    print("Checking installed packages...\n")
    for package, name in packages.items():
        try:
            __import__(package)
            print(f"✓ {name}: Installed")
        except ImportError:
            print(f"✗ {name}: NOT INSTALLED")
    
    print("\n" + "="*50)
    print("Python Version:", sys.version)
    
    # Check credentials file
    import os
    creds_path = './malayalamspeechtest-080e845e78d0.json'
    if os.path.exists(creds_path):
        print(f"✓ Google Cloud credentials file found: {creds_path}")
    else:
        print(f"✗ Google Cloud credentials file NOT FOUND: {creds_path}")

if __name__ == "__main__":
    check_imports()
