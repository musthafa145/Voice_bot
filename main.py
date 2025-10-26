"""
MYG Kerala AI Voice Sales Bot
Main application that integrates Speech, Gemini LLM, and Database
"""

import os
import sys
from dotenv import load_dotenv

# Add modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from modules.speech_handler import SpeechHandler
from modules.gemini_llm import GeminiHandler

# Load environment variables
load_dotenv()

def main():
    """Main application loop"""
    
    print("="*70)
    print("MYG KERALA - AI VOICE SALES BOT")
    print("="*70)
    
    # Get API keys from environment
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GOOGLE_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', './malayalamspeechtest-080e845e78d0.json')
    
    if not GEMINI_API_KEY:
        print("\n✗ Error: GEMINI_API_KEY not found in .env file")
        print("Please add your Gemini API key to the .env file")
        return
    
    # Initialize handlers
    print("\nInitializing systems...")
    try:
        speech = SpeechHandler(GOOGLE_CREDENTIALS)
        gemini = GeminiHandler(GEMINI_API_KEY, database_path='data/products.json')
    except Exception as e:
        print(f"\n✗ Error initializing handlers: {e}")
        return
    
    print("\n" + "="*70)
    print("SYSTEM READY - Starting conversation...")
    print("="*70)
    
    # Welcome message - Bot speaks first
    welcome_msg = gemini.get_welcome_message()
    speech.speak(welcome_msg)
    
    # Main conversation loop
    conversation_count = 0
    max_conversations = 20  # Limit to prevent infinite loop
    
    while conversation_count < max_conversations:
        conversation_count += 1
        
        # User's turn to speak
        user_input = speech.listen(timeout=120)  # 2 minutes timeout
        
        # Check if timeout or no input
        if user_input is None:
            print("\n" + "="*70)
            print("SESSION ENDED - 2 minutes of silence detected")
            print("="*70)
            speech.speak("Thank you for visiting MYG Kerala. Have a great day!")
            break
        
        # Check for exit keywords
        if any(word in user_input.lower() for word in ['bye', 'goodbye', 'exit', 'quit', 'thank you bye']):
            print("\n" + "="*70)
            print("SESSION ENDED - Customer said goodbye")
            print("="*70)
            speech.speak("Thank you for visiting MYG Kerala. Have a great day!")
            break
        
        # Generate response from Gemini
        print("\nBot: ", end="", flush=True)
        bot_response = gemini.generate_response(user_input)
        
        # Bot speaks the response
        speech.speak(bot_response)
    
    # End of conversation
    if conversation_count >= max_conversations:
        print("\n" + "="*70)
        print("SESSION ENDED - Maximum conversation limit reached")
        print("="*70)
    
    print("\nConversation Summary:")
    print(f"Total exchanges: {conversation_count}")
    print("\nThank you for using MYG Kerala AI Voice Sales Bot!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("SESSION ENDED - Interrupted by user")
        print("="*70)
    except Exception as e:
        print(f"\n\n✗ Fatal Error: {e}")
        import traceback
        traceback.print_exc()
