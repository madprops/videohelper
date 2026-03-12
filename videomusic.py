#!/usr/bin/env python3
"""
Video Audio Muxer

Replaces or adds an audio track to a video file.

Usage:
    python addaudio.py <input_video> <input_audio> <output_video>

Arguments:
    input_video: Path to the input video file
    input_audio: Path to the input audio file
    output_video: Path to the output video file

Example:
    python addaudio.py video.mp4 background_music.mp3 final_output.mp4
"""

import sys
import subprocess
import os
from pathlib import Path


def add_audio_to_video(video_file, audio_file, output_file):
    """Muxes an audio file into a video file."""

    if not os.path.exists(video_file):
        print(f"Error: Video file '{video_file}' does not exist.")
        return False

    if not os.path.exists(audio_file):
        print(f"Error: Audio file '{audio_file}' does not exist.")
        return False

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # ffmpeg command breakdown:
    # -c:v copy    : Copies the video stream without re-encoding (fast)
    # -c:a aac     : Encodes audio to aac (standard for mp4)
    # -map 0:v:0   : Takes the first video stream from the first input (video_file)
    # -map 1:a:0   : Takes the first audio stream from the second input (audio_file)
    # -shortest    : Trims the output to the length of the shortest input stream
    cmd = [
        'ffmpeg',
        '-i', video_file,
        '-i', audio_file,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-shortest',
        '-y',
        output_file
    ]

    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True)
        print(f"Successfully added audio to video: {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error processing video: {e}")
        return False
    except FileNotFoundError:
        print("Error: ffmpeg not found. Please install FFmpeg.")
        return False


def main():

    if len(sys.argv) != 4:
        print("Usage: python addaudio.py <input_video> <input_audio> <output_video>")
        sys.exit(1)

    video_file = sys.argv[1]
    audio_file = sys.argv[2]
    output_file = sys.argv[3]

    success = add_audio_to_video(video_file, audio_file, output_file)

    if success:
        print("Audio added successfully!")
        sys.exit(0)
    else:
        print("Failed to add audio!")
        sys.exit(1)


if __name__ == "__main__":
    main()