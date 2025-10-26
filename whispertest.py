from faster_whisper import WhisperModel

model_size = "small.en"

# Run on CPU with FP32 (standard floating point)
model = WhisperModel(model_size, device="cpu", compute_type="float32")

# or run on GPU with INT8
# model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
# or run on CPU with INT8
# model = WhisperModel(model_size, device="cpu", compute_type="int8")

segments, _ = model.transcribe("ajnas_voice.mp3", language="malayalam", beam_size=5)


for segment in segments:
    print(segment.text)