#!/usr/bin/env python3
"""
Media Pitcher - Changes the pitch of video or audio files by adjusting playback speed using ffmpeg
Usage: python pitcher.py <input_file> <percentage> <output_file>
Examples:
  python pitcher.py input.mp4 70 output.mp4
  python pitcher.py song.mp3 80 slow_song.mp3
"""

import sys
import subprocess
import os
from pathlib import Path


def validate_percentage(percentage_str):
    """Validate and convert percentage string to float"""
    try:
        percentage = float(percentage_str)
        if percentage <= 0:
            raise ValueError("Percentage must be greater than 0")
        return percentage
    except ValueError as e:
        print(f"Error: Invalid percentage '{percentage_str}'. {e}")
        sys.exit(1)


def check_file_exists(file_path):
    """Check if input file exists"""
    if not os.path.isfile(file_path):
        print(f"Error: Input file '{file_path}' does not exist")
        sys.exit(1)


def check_ffmpeg():
    """Check if ffmpeg is available"""
    try:
        subprocess.run(['ffmpeg', '-version'],
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL,
                      check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: ffmpeg is not installed or not found in PATH")
        print("Please install ffmpeg: https://ffmpeg.org/download.html")
        sys.exit(1)


def check_has_video_stream(input_file):
    """Check if input file has a video stream"""
    try:
        cmd = ['ffprobe', '-v', 'quiet', '-select_streams', 'v:0', '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', input_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0 and 'video' in result.stdout.lower()
    except:
        # If ffprobe fails, assume it's audio-only
        return False


def pitch_media(input_file, percentage, output_file):
    """
    Pitch video or audio by changing playback speed using ffmpeg (mimics Firefox behavior)

    Args:
        input_file (str): Path to input video or audio file
        percentage (float): Speed percentage (e.g., 70 for 70% speed)
        output_file (str): Path to output video or audio file
    """
    # Convert percentage to speed factor (70% = 0.7)
    speed_factor = percentage / 100.0

    # Check if input has video stream
    has_video = check_has_video_stream(input_file)

    # Force audio-only processing if output is MP3 (MP3 can't contain video)
    output_is_mp3 = output_file.lower().endswith('.mp3')
    process_as_video = has_video and not output_is_mp3

    if process_as_video:
        # Video file processing
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-filter_complex', f'[0:v]setpts={1/speed_factor}*PTS[v];[0:a]asetrate=44100*{speed_factor},aresample=44100[a]',
            '-map', '[v]',
            '-map', '[a]',
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-y',  # Overwrite output file if it exists
            output_file
        ]
    else:
        # Audio-only file processing (or video input with MP3 output)
        if output_is_mp3:
            cmd = [
                'ffmpeg',
                '-i', input_file,
                '-filter:a', f'asetrate=44100*{speed_factor},aresample=44100',
                '-c:a', 'libmp3lame',
                '-b:a', '192k',  # Set bitrate for MP3
                '-y',  # Overwrite output file if it exists
                output_file
            ]
        else:
            cmd = [
                'ffmpeg',
                '-i', input_file,
                '-filter:a', f'asetrate=44100*{speed_factor},aresample=44100',
                '-c:a', 'aac',
                '-y',  # Overwrite output file if it exists
                output_file
            ]

    print(f"Processing {'video' if process_as_video else 'audio'}: {input_file}")
    if has_video and output_is_mp3:
        print("Note: Extracting audio only (MP3 output cannot contain video)")
    print(f"Speed: {percentage}% (pitch will be {'lower' if percentage < 100 else 'higher' if percentage > 100 else 'unchanged'})")
    print(f"Output: {output_file}")
    print("Running ffmpeg...")

    try:
        # Run ffmpeg with progress output
        result = subprocess.run(cmd, check=True, text=True, capture_output=False)
        print(f"\nSuccess! {'Video' if process_as_video else 'Audio'} processed and saved to: {output_file}")

    except subprocess.CalledProcessError as e:
        print(f"\nError: ffmpeg failed with return code {e.returncode}")
        print("This could be due to:")
        print("- Unsupported video format")
        print("- Corrupted input file")
        print("- Insufficient disk space")
        print("- Invalid output path")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        # Clean up incomplete output file
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
                print(f"Cleaned up incomplete file: {output_file}")
            except:
                pass
        sys.exit(1)


def main():
    """Main function to handle command line arguments and execute media processing"""
    if len(sys.argv) != 4:
        print("Usage: python pitcher.py <input_file> <percentage> <output_file>")
        print("\nArguments:")
        print("  input_file  - Path to the input video or audio file (supports MP4, AVI, MKV, MP3, WAV, etc.)")
        print("  percentage  - Speed percentage (e.g., 70 for 70% speed, lower pitch)")
        print("  output_file - Path to the output video or audio file")
        print("\nExamples:")
        print("  python pitcher.py video.mp4 70 slow_video.mp4")
        print("  python pitcher.py input.avi 50 half_speed.mp4")
        print("  python pitcher.py movie.mkv 130 fast_movie.mp4")
        print("  python pitcher.py song.mp3 80 slow_song.mp3")
        print("  python pitcher.py audio.wav 120 fast_audio.mp3")
        sys.exit(1)

    input_file = sys.argv[1]
    percentage_str = sys.argv[2]
    output_file = sys.argv[3]

    # Validate inputs
    check_file_exists(input_file)
    percentage = validate_percentage(percentage_str)
    check_ffmpeg()

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        except OSError as e:
            print(f"Error: Could not create output directory '{output_dir}': {e}")
            sys.exit(1)

    # Process the media file
    pitch_media(input_file, percentage, output_file)


if __name__ == "__main__":
    main()