import ffmpeg

input_file = "ajnas_voice.opus"
output_file = "ajnas_voice.mp3"

try:
    # Run FFmpeg conversion
    stream = ffmpeg.input(input_file)
    stream = ffmpeg.output(stream, output_file)
    ffmpeg.run(stream)
    print(f"Conversion complete! File saved as {output_file}")
except ffmpeg.Error as e:
    print('An error occurred:', e.stderr.decode())