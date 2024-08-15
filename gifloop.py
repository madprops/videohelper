import subprocess
from sys import argv

def get_audio_duration(audio_file):
    result = subprocess.run(['ffmpeg', '-i', audio_file, '-hide_banner'], stderr=subprocess.PIPE, text=True)
    duration = None
    for line in result.stderr.split('\n'):
        if 'Duration' in line:
            duration = line.split(',')[0].split()[1]
            break
    if duration:
        hours, minutes, seconds = duration.split(':')
        total_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        return total_seconds
    return None

def create_video_from_gif_and_audio(gif_file, audio_file, output_file):
    audio_duration = get_audio_duration(audio_file)

    if audio_duration is None:
        print("Error: Could not determine the audio duration.")
        return

    # Create a video from the GIF with the duration of the audio
    command = [
        'ffmpeg',
        '-stream_loop', '-1',  # Loop the GIF indefinitely
        '-i', gif_file,        # Input GIF file
        '-i', audio_file,      # Input audio file
        '-t', str(audio_duration), # Set the duration to the audio file's duration
        '-c:v', 'libx264',     # Video codec
        '-c:a', 'aac',         # Audio codec
        '-strict', 'experimental', # Allow usage of experimental codecs
        '-pix_fmt', 'yuv420p', # Pixel format
        '-shortest',           # Match the shortest input duration
        output_file            # Output file
    ]

    subprocess.run(command)

# Define your input files and output file
gif_file = argv[1]
audio_file = argv[2]
output_file = argv[3]

# Create the video
create_video_from_gif_and_audio(gif_file, audio_file, output_file)