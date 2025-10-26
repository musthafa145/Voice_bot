# server/main_proxy.py
import os
import threading
from flask import Flask
from flask_sock import Sock
from dotenv import load_dotenv
from .gemini_service import GeminiLiveService # നിങ്ങളുടെ സർവീസ് ഫയലിൽ നിന്ന് ക്ലാസ് ഇമ്പോർട്ട് ചെയ്യുന്നു

# .env ഫയലിൽ നിന്ന് പരിസ്ഥിതി വേരിയബിളുകൾ ലോഡ് ചെയ്യുന്നു
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file. Please set your key.")

app = Flask(__name__)
sock = Sock(app)

# ക്ലയിൻ്റ് കണക്ട് ചെയ്യേണ്ട WebSocket endpoint
@sock.route('/connect')
def live_proxy_session(ws):
    """
    പ്രാദേശിക Python ക്ലയിൻ്റിൽ നിന്നുള്ള (terminal_client.py) WebSocket കണക്ഷൻ കൈകാര്യം ചെയ്യുന്നു.
    ഓഡിയോ ജെമിനി സർവീസിലേക്ക് കൈമാറുകയും പ്രതികരണം തിരികെ ക്ലയിൻ്റിലേക്ക് അയയ്ക്കുകയും ചെയ്യുന്നു.
    """
    
    print("\n--- Client Connected! Starting Gemini Live Session ---")
    
    # 1. Gemini Live Service ആരംഭിക്കുന്നു
    service = GeminiLiveService(client_ws=ws, api_key=GEMINI_API_KEY)
    
    # 2. Gemini API-യിലേക്കുള്ള കണക്ഷൻ ഒരു ബാക്ക്ഗ്രൗണ്ട് ത്രെഡിൽ ആരംഭിക്കുന്നു
    # ഇത് പ്രധാന ത്രെഡിന് ക്ലയിൻ്റിൽ നിന്ന് ലൈവ് ഓഡിയോ സ്വീകരിക്കുന്നത് തുടരാൻ അനുവദിക്കുന്നു
    service_thread = threading.Thread(target=service.run_session)
    service_thread.start()
    
    # 3. പ്രധാന ലൂപ്പ്: ക്ലയിൻ്റിൽ നിന്ന് ബൈനറി ഓഡിയോ chunk-കൾ സ്വീകരിക്കുന്നു
    while not ws.closed:
        try:
            # WebSocket-ൽ നിന്ന് ഓഡിയോ ഡാറ്റ സ്വീകരിക്കുന്നു
            audio_data = ws.receive()
            
            if audio_data is None:
                # കണക്ഷൻ ക്ലോസ് ചെയ്താൽ അല്ലെങ്കിൽ ഡാറ്റ ഇല്ലെങ്കിൽ ബ്രേക്ക് ചെയ്യുക
                break
            
            if isinstance(audio_data, bytes):
                # ലഭിച്ച ഓഡിയോ chunk Gemini സർവീസിലേക്ക് കൈമാറുന്നു
                service.send_audio_to_gemini(audio_data)
            else:
                 # ടെക്സ്റ്റ് ഡാറ്റ വന്നാൽ (ഉദാഹരണത്തിന് സ്റ്റോപ്പ് കമാൻഡ്)
                print(f"Received non-audio data: {audio_data}")
                

        except Exception as e:
            # പിഴവുകൾ കൈകാര്യം ചെയ്യുക
            print(f"Error receiving client audio: {e}")
            break

    # 4. ക്ലയിൻ്റ് ഡിസ്കണക്ട് ചെയ്യുമ്പോൾ ക്ലീനപ്പ്
    service.close_session() # Gemini സർവീസിനോട് സ്ട്രീമിംഗ് നിർത്താൻ പറയുന്നു
    service_thread.join()   # Gemini ത്രെഡ് പൂർത്തിയാക്കാൻ കാത്തിരിക്കുന്നു
    print("--- Client Disconnected. Session Ended ---")


if __name__ == '__main__':
    print(f"Proxy Server running on ws://127.0.0.1:5000/connect")
    # Flask-Sock പ്രവർത്തിക്കാൻ gevent അല്ലെങ്കിൽ eventlet ആവശ്യമാണ്.
    # ലളിതമായ ഡെമോയ്ക്ക് സ്റ്റാൻഡേർഡ് ഫ്ലാസ്ക് സെർവർ ഉപയോഗിക്കുന്നു.
    # വലിയ ട്രാഫിക്കിനായി gevent ഉപയോഗിക്കുന്നതാണ് നല്ലത്.
    app.run(port=5000, debug=False)