# client/terminal_client.py
import pyaudio
import websocket
import threading
import time
import sys

# --- ഓഡിയോ കോൺഫിഗറേഷനുകൾ (Audio Configurations) ---
# PyAudio ഇൻപുട്ടിനുള്ള സ്ഥിരമായ കോൺഫിഗറേഷനുകൾ
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000 # Gemini API പ്രതീക്ഷിക്കുന്ന ഓഡിയോ ഇൻപുട്ട് Sample Rate

# Gemini API-യിൽ നിന്ന് ലഭിക്കുന്ന ഓഡിയോ ഔട്ട്പുട്ടിനുള്ള Sample Rate
# (ഇത് സാധാരണയായി 24000Hz ആണ്)
GEMINI_OUTPUT_RATE = 24000 

# --- WebSocket കോൺഫിഗറേഷൻ ---
WS_URL = "ws://127.0.0.1:5000/connect"

# PyAudio ഇൻസ്റ്റൻസ്
p = pyaudio.PyAudio()

# ഗ്ലോബൽ സ്റ്റേറ്റുകൾ
ws_connected = threading.Event()

# --------------------------
# 1. ഓഡിയോ സ്ട്രീമുകൾ സജ്ജമാക്കുന്നു
# --------------------------

try:
    # PyAudio ഇൻപുട്ട് സ്ട്രീം (മൈക്രോഫോൺ)
    stream_in = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK,
                        input_device_index=None) # ഓട്ടോമാറ്റിക് ആയി ഡിഫോൾട്ട് ഇൻപുട്ട് ഉപകരണം തിരഞ്ഞെടുക്കുന്നു
    
    # PyAudio ഔട്ട്പുട്ട് സ്ട്രീം (സ്പീക്കർ പ്ലേബാക്ക്)
    stream_out = p.open(format=FORMAT,
                         channels=CHANNELS,
                         rate=GEMINI_OUTPUT_RATE, 
                         output=True,
                         frames_per_buffer=CHUNK,
                         output_device_index=None) # ഓട്ടോമാറ്റിക് ആയി ഡിഫോൾട്ട് ഔട്ട്പുട്ട് ഉപകരണം തിരഞ്ഞെടുക്കുന്നു

    print(f"--- ഓഡിയോ സ്ട്രീമുകൾ സജ്ജമാക്കി (Mic: {RATE}Hz, Speaker: {GEMINI_OUTPUT_RATE}Hz) ---")

except Exception as e:
    print(f"\n[ERROR]: PyAudio സ്ട്രീം തുറക്കുന്നതിൽ പിശക്: {e}")
    print("നിങ്ങൾക്ക് PyAudio, PortAudio ലൈബ്രറികൾ ഇൻസ്റ്റാൾ ചെയ്തിട്ടുണ്ടെന്ന് ഉറപ്പാക്കുക.")
    sys.exit(1)


# --------------------------
# 2. മൈക്രോഫോൺ ഓഡിയോ അയക്കുന്ന ത്രെഡ്
# --------------------------

def audio_thread_function(ws):
    """മൈക്രോഫോണിൽ നിന്ന് ഓഡിയോ റീഡ് ചെയ്യുകയും WebSocket വഴി അയയ്ക്കുകയും ചെയ്യുന്നു."""
    print("🎤 ഓഡിയോ സ്ട്രീമിംഗ് ആരംഭിക്കുന്നു. സംസാരിക്കുക...")
    
    while ws_connected.is_set():
        try:
            # മൈക്രോഫോണിൽ നിന്ന് ഓഡിയോ ഡാറ്റ റീഡ് ചെയ്യുന്നു
            audio_data = stream_in.read(CHUNK, exception_on_overflow=False)
            
            # WebSocket വഴി സെർവറിലേക്ക് അയക്കുന്നു
            if ws.connected:
                ws.send(audio_data, opcode=websocket.ABNF.OPCODE_BINARY)
            
        except IOError as e:
            # ഓഡിയോ ഓവർഫ്ലോ പോലുള്ള പിശകുകൾ സാധാരണമാണ്, അവ ഒഴിവാക്കുന്നു
            if 'Input overflowed' in str(e):
                continue
            print(f"ഓഡിയോ ത്രെഡ് പിശക്: {e}")
            break
        except Exception as e:
            print(f"ഓഡിയോ ത്രെഡ് പിശക്: {e}")
            break
            
    print("🎤 ഓഡിയോ ഇൻപുട്ട് സ്ട്രീം നിർത്തുന്നു.")


# --------------------------
# 3. WebSocket സ്വീകരിക്കുന്ന ഫംഗ്ഷനുകൾ
# --------------------------

def on_message(ws, message):
    """സെർവറിൽ നിന്ന് ഡാറ്റ സ്വീകരിക്കുമ്പോൾ പ്രവർത്തിക്കുന്നു."""
    if isinstance(message, bytes):
        # ജെമിനിയുടെ ഓഡിയോ പ്രതികരണം (Binary data)
        try:
            stream_out.write(message)
        except IOError as e:
            # പ്ലേബാക്ക് പിശകുകൾ ഒഴിവാക്കുന്നു
            if 'Output overflowed' in str(e):
                return
            print(f"ഓഡിയോ പ്ലേബാക്ക് പിശക്: {e}")
            
    else:
        # ടെക്സ്റ്റ് ഡാറ്റ (ട്രാൻസ്ക്രിപ്റ്റ് അല്ലെങ്കിൽ സ്ട്രിംഗ് പ്രതികരണം)
        try:
            text = message.decode('utf-8')
            print(f"\n{text}", end="", flush=True) # ലൈവ് ആയി പ്രിൻ്റ് ചെയ്യുന്നു
        except Exception:
            # ഡീകോഡിംഗിൽ പിശകുണ്ടായാൽ
            print(f"\n[Received]: {message}")


def on_error(ws, error):
    """WebSocket പിശകുകൾ കൈകാര്യം ചെയ്യുന്നു."""
    print(f"\n[ERROR]: WebSocket പിശക്: {error}")
    ws_connected.clear()


def on_close(ws, close_code, reason):
    """WebSocket അടയ്ക്കുമ്പോൾ പ്രവർത്തിക്കുന്നു."""
    print(f"\n--- കണക്ഷൻ ക്ലോസ് ചെയ്തു (Code: {close_code}, Reason: {reason}) ---")
    ws_connected.clear()


def on_open(ws):
    """WebSocket തുറക്കുമ്പോൾ പ്രവർത്തിക്കുന്നു."""
    print(f"--- WebSocket കണക്ഷൻ വിജയകരം: {WS_URL} ---")
    ws_connected.set()
    
    # കണക്ഷൻ തുറന്ന ശേഷം ഓഡിയോ അയയ്ക്കുന്ന ത്രെഡ് ആരംഭിക്കുന്നു
    audio_thread = threading.Thread(target=audio_thread_function, args=(ws,))
    audio_thread.start()


# --------------------------
# 4. പ്രധാന പ്രവർത്തനങ്ങൾ
# --------------------------

if __name__ == "__main__":
    print(f"Gemini Live കൺസോൾ ക്ലയിൻ്റ്: {WS_URL}-ലേക്ക് കണക്ട് ചെയ്യാൻ ശ്രമിക്കുന്നു...")
    
    # WebSocket ക്ലയിൻ്റ് ഇൻസ്റ്റൻസ് ഉണ്ടാക്കുന്നു
    ws = websocket.WebSocketApp(WS_URL,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    
    # WebSocket റണ്ണിംഗ് ആരംഭിക്കുന്നു (ഒരു ബാക്ക്ഗ്രൗണ്ട് ത്രെഡിൽ റൺ ചെയ്യുന്നു)
    ws_thread = threading.Thread(target=ws.run_forever)
    ws_thread.daemon = True
    ws_thread.start()

    try:
        # മെയിൻ ത്രെഡ് WebSocket ക്ലോസ് ചെയ്യുന്നത് വരെ പ്രവർത്തിക്കുന്നു
        while ws_connected.is_set() or ws_thread.is_alive():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nനിങ്ങൾ ക്ലയിൻ്റ് നിർത്താൻ ആവശ്യപ്പെട്ടു (Ctrl+C).")
    
    finally:
        # ക്ലീനപ്പ്
        print("ക്ലീനപ്പ്...")
        ws_connected.clear()
        stream_in.stop_stream()
        stream_in.close()
        stream_out.stop_stream()
        stream_out.close()
        p.terminate()
        ws.close()
        print("ക്ലയിൻ്റ് വിജയകരമായി അടച്ചു.")