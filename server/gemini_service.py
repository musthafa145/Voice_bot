# server/gemini_service.py
import asyncio
import threading
from google import genai
from google.genai import types

class GeminiLiveService:
    def __init__(self, client_ws, api_key: str):
        """
        Gemini Live API സെഷൻ ആരംഭിക്കുന്നു.
        :param client_ws: പ്രാദേശിക പൈത്തൺ ക്ലയിൻ്റുമായുള്ള WebSocket കണക്ഷൻ (Flask-Sock).
        :param api_key: നിങ്ങളുടെ Gemini API കീ.
        """
        self.client_ws = client_ws
        self.client = genai.Client(api_key=api_key)
        # ലൈവ് വോയിസ് ഇന്ററാക്ഷൻ പിന്തുണയ്ക്കുന്ന മോഡൽ
        self.model = "gemini-live-2.5-flash-preview" 
        self.loop = asyncio.new_event_loop()
        self.audio_queue = asyncio.Queue()
        self.is_streaming = True

    def send_audio_to_gemini(self, audio_data: bytes):
        """മൈക്രോഫോണിൽ നിന്നുള്ള ലൈവ് ഓഡിയോ ഡാറ്റ ക്യൂവിലേക്ക് ചേർക്കുന്നു."""
        if self.is_streaming:
            # ത്രെഡ്-സേഫ് ആയി ഓഡിയോ ഡാറ്റ അസിൻക്രണസ് ക്യൂവിലേക്ക് ചേർക്കുന്നു
            self.loop.call_soon_threadsafe(self.audio_queue.put_nowait, audio_data)

    def close_session(self):
        """ഓഡിയോ സ്ട്രീമിംഗ് അവസാനിപ്പിക്കാൻ സിഗ്നൽ നൽകുന്നു."""
        self.is_streaming = False
        # ക്യൂവിലേക്ക് None എന്നൊരു sentinel value നൽകി ഓഡിയോ പ്രൊഡ്യൂസറിനെ നിർത്തുന്നു
        self.loop.call_soon_threadsafe(self.audio_queue.put_nowait, None)

    async def _audio_generator(self):
        """ജെമിനി API-യിലേക്ക് അയക്കാനുള്ള ഓഡിയോ chunk-കൾ അസിൻക്രണസ് ആയി നൽകുന്നു."""
        while self.is_streaming or not self.audio_queue.empty():
            chunk = await self.audio_queue.get()
            if chunk is None:
                break 

            # ഓഡിയോ ഡാറ്റ 16-bit PCM, 16kHz, mono ഫോർമാറ്റിൽ സജ്ജീകരിക്കുന്നു
            yield types.RealtimeInput(
                audio=types.Audio(
                    data=chunk,
                    mime_type="audio/pcm;rate=16000",
                )
            )

    async def _handle_response(self, session):
        """ജെമിനി API-യിൽ നിന്നുള്ള പ്രതികരണങ്ങൾ (ഓഡിയോയും ടെക്സ്റ്റും) കൈകാര്യം ചെയ്യുന്നു."""
        async for message in session:
            # 1. ടെക്സ്റ്റ് ട്രാൻസ്ക്രിപ്റ്റും പ്രതികരണവും കൈകാര്യം ചെയ്യുക
            if message.text:
                # ജെമിനി ഓഡിയോ ഇൻപുട്ട് ട്രാൻസ്ക്രൈബ് ചെയ്തത് ഇവിടെ ലഭിക്കും
                transcript = f"[Transcript]: {message.text}"
                print(transcript) # Terminal 1-ൽ പ്രിൻ്റ് ചെയ്യുന്നു
                
                # പ്രാദേശിക ക്ലയിൻ്റിലേക്ക് ടെക്സ്റ്റ് ട്രാൻസ്ക്രിപ്റ്റ് അയയ്ക്കുന്നു
                try:
                    # WebSocket വഴി സ്ട്രിംഗ് ഡാറ്റ അയയ്ക്കുന്നു
                    self.client_ws.send(transcript.encode('utf-8')) 
                except Exception as e:
                    print(f"Error sending text to client: {e}")
                    break
            
            # 2. ജെമിനിയുടെ സംസാരം (ബൈനറി ഓഡിയോ ഡാറ്റ) കൈകാര്യം ചെയ്യുക
            if message.audio and message.audio.data:
                audio_chunk = message.audio.data
                # ലഭിക്കുന്ന ഓഡിയോ ബൈറ്റുകൾ ക്ലയിൻ്റിൻ്റെ പ്ലേബാക്കിനായി നേരിട്ട് അയയ്ക്കുന്നു
                try:
                    # WebSocket വഴി ബൈനറി ഡാറ്റ അയയ്ക്കുന്നു
                    self.client_ws.send(audio_chunk, binary=True)
                except Exception as e:
                    print(f"Error sending audio to client: {e}")
                    break

            # ഒരു സംഭാഷണത്തിൻ്റെ പ്രതികരണം പൂർത്തിയാകുമ്പോൾ
            if message.turn_complete:
                print("--- Turn Complete ---")

    async def _main_live_session(self):
        """ജെമിനി ലൈവ് API-യിലേക്ക് WebSocket കണക്ഷൻ സ്ഥാപിക്കുന്നു."""
        try:
            # പ്രധാന കോൺഫിഗറേഷൻ: വോയിസ് റെസ്പോൺസ്, മലയാളം ഭാഷ
            config = types.LiveConnectConfig(
                # ഓഡിയോ, ടെക്സ്റ്റ് പ്രതികരണങ്ങൾ ആവശ്യപ്പെടുന്നു
                response_modalities=[types.Modality.AUDIO, types.Modality.TEXT], 
                
                # സംഭാഷണത്തെ കൂടുതൽ സ്വാഭാവികമാക്കാൻ VAD (വോയിസ് ആക്ടിവിറ്റി ഡിറ്റക്ഷൻ) ഓൺ ചെയ്യുന്നു
                input_audio_transcription=types.InputAudioTranscriptionConfig(),
                
                # മലയാളം ഭാഷാ കോൺഫിഗറേഷൻ
                speech_config=types.SpeechConfig(
                    language_code="ml-IN", # മലയാളം (ഇന്ത്യ)
                    # ഒരു പ്രത്യേക വോയിസ് വേണമെങ്കിൽ uncomment ചെയ്യുക (PrebuiltVoiceConfig ലഭ്യമാണെങ്കിൽ)
                    # voice_config=types.VoiceConfig(
                    #     prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    #         voice_name="Aoede" # ഉദാഹരണത്തിന്
                    #     )
                    # )
                ),
                # സംഭാഷണ ശൈലി സജ്ജീകരിക്കുന്നതിനുള്ള സിസ്റ്റം ഇൻസ്ട്രക്ഷൻ
                system_instruction=types.Content(
                    parts=[types.Part.from_text("നിങ്ങൾ ഒരു ലാപ്‌ടോപ്പ് വിൽപ്പനക്കാരനാണ്. ഉപഭോക്താവുമായി സ്നേഹത്തോടെയും ശ്രദ്ധയോടെയും മലയാളത്തിൽ സംസാരിക്കുക. കൂടുതൽ വിവരങ്ങൾ ചോദിച്ചുകൊണ്ട് സംഭാഷണം മുന്നോട്ട് കൊണ്ടുപോകുക.")]
                )
            )

            async with self.client.aio.live.connect(model=self.model, config=config) as session:
                print("Gemini Live API connected. Starting bidirectional streaming...")
                
                # പ്രതികരണങ്ങൾ കൈകാര്യം ചെയ്യാൻ ഒരു ടാസ്ക് തുടങ്ങുന്നു
                response_task = asyncio.create_task(self._handle_response(session))
                
                # ഓഡിയോ ജനറേറ്ററിൽ നിന്ന് ഡാറ്റ അയയ്ക്കുന്നു
                async for input_msg in self._audio_generator():
                    await session.send_realtime_input(input_msg)
                
                # ഓഡിയോ സ്ട്രീമിംഗ് നിർത്തുമ്പോൾ, പ്രതികരണ ടാസ്ക് പൂർത്തിയാക്കാൻ കാത്തിരിക്കുന്നു
                await response_task

        except Exception as e:
            print(f"Fatal error in Gemini session: {e}")
        finally:
            print("Gemini Live Session closed.")

    def run_session(self):
        """ബാക്ക്ഗ്രൗണ്ട് ത്രെഡിനായുള്ള എൻട്രി പോയിൻ്റ്."""
        try:
            # അസിൻക്രണസ് ലൂപ്പ് ആരംഭിക്കുന്നു
            self.loop.run_until_complete(self._main_live_session())
        finally:
            # ലൂപ്പ് ക്ലീൻ അപ്പ് ചെയ്യുന്നു
            self.loop.close()

if __name__ == '__main__':
    # ഈ ഫയൽ നേരിട്ട് പ്രവർത്തിപ്പിക്കാൻ സാധ്യമല്ല.
    # ഇത് main_proxy.py വഴി മാത്രമേ പ്രവർത്തിപ്പിക്കാൻ പാടുള്ളൂ.
    print("This file must be run via main_proxy.py")