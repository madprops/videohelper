#!/usr/bin/env python3
"""
Media Pitcher - Changes the pitch of video or audio files by adjusting playback speed using ffmpeg
Usage: python pitcher.py <input_file> <percentage> <output_file> [--reverb]
Examples:
  python pitcher.py input.mp4 70 output.mp4
  python pitcher.py song.mp3 80 slow_song.mp3 --reverb
"""

import sys
import subprocess
import os
import argparse
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


def create_impulse_response_file():
    """Create a temporary impulse response file for convolution reverb"""
    import tempfile
    import wave
    import numpy as np

    try:
        # Create a temporary WAV file for the impulse response
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_file.close()

        # Parameters matching the JavaScript implementation
        sample_rate = 44100
        duration = 3.0  # 3 seconds
        length = int(sample_rate * duration)

        # Create stereo impulse response
        impulse_data = np.zeros((length, 2), dtype=np.float32)

        # Early reflections (matching JS implementation)
        early_times = [0.007, 0.013, 0.021, 0.033]
        early_gains = [0.6, 0.45, 0.32, 0.22]

        for channel in range(2):
            for j, (time, gain) in enumerate(zip(early_times, early_gains)):
                # Add slight stereo delay difference
                t = time + (0.0 if channel == 0 else 0.0015)
                idx = int(t * sample_rate)

                if idx < length:
                    # Apply windowed early reflection
                    for k in range(-8, 9):
                        p = idx + k
                        if 0 <= p < length:
                            window = 1 - abs(k) / 8
                            impulse_data[p, channel] += gain * window * 0.04

            # Add diffuse reverb tail with exponential decay
            decay = 3.5
            for i in range(length):
                t = i / length
                env = (1 - t) ** decay
                noise = (np.random.random() * 2 - 1) * env * 0.6
                impulse_data[i, channel] += noise

            # Fade out the tail
            fade_start = int(length * 0.85)
            for i in range(fade_start, length):
                fade = (length - i) / (length * 0.15)
                impulse_data[i, channel] *= fade

        # Normalize to prevent clipping
        max_val = np.max(np.abs(impulse_data))
        if max_val > 0:
            impulse_data = impulse_data / max_val * 0.8

        # Convert to 16-bit PCM
        impulse_data_int = (impulse_data * 32767).astype(np.int16)

        # Write WAV file
        with wave.open(temp_file.name, 'w') as wav_file:
            wav_file.setnchannels(2)  # Stereo
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(impulse_data_int.tobytes())

        return temp_file.name

    except ImportError:
        # If numpy is not available, return None to fall back to simple echo
        return None
    except Exception:
        return None


def pitch_media(input_file, percentage, output_file, add_reverb=False):
    """
    Pitch video or audio by changing playback speed using ffmpeg (mimics Firefox behavior)

    Args:
        input_file (str): Path to input video or audio file
        percentage (float): Speed percentage (e.g., 70 for 70% speed)
        output_file (str): Path to output video or audio file
        add_reverb (bool): Whether to add reverb effect to audio
    """
    # Convert percentage to speed factor (70% = 0.7)
    speed_factor = percentage / 100.0

    # Check if input has video stream
    has_video = check_has_video_stream(input_file)

    # Force audio-only processing if output is MP3 or FLAC (these formats can't contain video)
    output_is_audio_only = output_file.lower().endswith(('.mp3', '.flac'))
    process_as_video = has_video and not output_is_audio_only

    # Base (simple) audio speed/pitch change chain
    base_audio_chain = f'asetrate=44100*{speed_factor},aresample=44100'

    # Track whether we need a complex (multi-pad) graph
    complex_audio_graph = None  # Will hold only the audio portion if needed
    impulse_file = None

    if add_reverb:
        print("Adding reverb effect...")
        impulse_file = create_impulse_response_file()
        if impulse_file:
            # Build complex graph with dry/wet mix using convolution reverb using afir (load IR via amovie)
            # Graph explanation:
            # 1. [0:a] speed change then split -> [prewet][dry]
            # 2. Load impulse file with amovie -> [ir]
            # 3. Convolve: [prewet][ir] afir -> [wetraw]
            # 4. Apply pre-delay + filtering + compression + level -> [wet]
            # 5. Mix dry & wet -> [a]
            complex_audio_graph = (
                f"[0:a]{base_audio_chain},asplit=2[prewet][dry];"
                f"amovie={impulse_file}[ir];"
                f"[prewet][ir]afir=dry=0:wet=1[wetraw];"
                f"[wetraw]adelay=30|30,lowpass=f=6500:width_type=h:width=0.707,"
                f"acompressor=threshold=-18dB:ratio=2:attack=3:release=250,volume=0.55[wet];"
                f"[dry][wet]amix=inputs=2:weights=0.45|0.55[a]"
            )
        else:
            # Fallback to simple echo chain (can stay linear)
            base_audio_chain += ',aecho=0.8:0.9:30:0.3,aecho=0.6:0.7:60:0.2,lowpass=f=6500'
    # If no reverb requested, base_audio_chain is sufficient

    # Build command
    if process_as_video:
        # Always use -filter_complex for video so we can integrate either simple or complex audio graph uniformly
        if complex_audio_graph:
            filter_complex = f"[0:v]setpts={1/speed_factor}*PTS[v];" + complex_audio_graph
        else:
            # Simple case: append audio chain and label output [a]
            filter_complex = f"[0:v]setpts={1/speed_factor}*PTS[v];[0:a]{base_audio_chain}[a]"
        # Optional debug output
        if os.environ.get('PITCHER_DEBUG'):
            print('Filter complex:', filter_complex)
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-filter_complex', filter_complex,
            '-map', '[v]',
            '-map', '[a]',
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-y',
            output_file
        ]
    else:
        # Audio-only output
        if complex_audio_graph:
            # Need -filter_complex and map [a]
            if os.environ.get('PITCHER_DEBUG'):
                print('Filter complex:', complex_audio_graph)
            cmd = [
                'ffmpeg',
                '-i', input_file,
                '-filter_complex', complex_audio_graph,
                '-map', '[a]',
            ]
        else:
            # Simple linear chain can use -filter:a
            if os.environ.get('PITCHER_DEBUG'):
                print('Filter a:', base_audio_chain)
            cmd = [
                'ffmpeg',
                '-i', input_file,
                '-filter:a', base_audio_chain,
            ]
        # Append codec options based on output extension
        if output_file.lower().endswith('.mp3'):
            cmd += ['-c:a', 'libmp3lame', '-b:a', '192k']
        elif output_file.lower().endswith('.flac'):
            cmd += ['-c:a', 'flac', '-compression_level', '5']
        else:
            cmd += ['-c:a', 'aac']
        cmd += ['-y', output_file]

    print(f"Processing {'video' if process_as_video else 'audio'}: {input_file}")
    if has_video and output_is_audio_only:
        print(f"Note: Extracting audio only ({output_file.split('.')[-1].upper()} output cannot contain video)")
    print(f"Speed: {percentage}% (pitch will be {'lower' if percentage < 100 else 'higher' if percentage > 100 else 'unchanged'})")
    if add_reverb:
        print(f"Reverb: {'Enabled (convolution)' if impulse_file else 'Enabled (echo fallback)'}")
    print(f"Output: {output_file}")
    print("Running ffmpeg...")

    try:
        subprocess.run(cmd, check=True, text=True, capture_output=False)
        effects_text = " with reverb" if add_reverb else ""
        print(f"\nSuccess! {'Video' if process_as_video else 'Audio'} processed{effects_text} and saved to: {output_file}")

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
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
                print(f"Cleaned up incomplete file: {output_file}")
            except:
                pass
        sys.exit(1)
    finally:
        if impulse_file and os.path.exists(impulse_file):
            try:
                os.unlink(impulse_file)
            except:
                pass


def main():
    """Main function to handle command line arguments and execute media processing"""
    parser = argparse.ArgumentParser(
        description='Changes the pitch of video or audio files by adjusting playback speed using ffmpeg',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python pitcher.py video.mp4 70 slow_video.mp4
  python pitcher.py input.avi 50 half_speed.mp4
  python pitcher.py movie.mkv 130 fast_movie.mp4
  python pitcher.py song.mp3 80 slow_song.mp3 --reverb
  python pitcher.py audio.wav 120 fast_audio.flac --reverb
  python pitcher.py music.flac 90 slower_music.flac"""
    )

    parser.add_argument('input_file',
                       help='Path to the input video or audio file (supports MP4, AVI, MKV, MP3, WAV, FLAC, etc.)')
    parser.add_argument('percentage', type=str,
                       help='Speed percentage (e.g., 70 for 70%% speed, lower pitch)')
    parser.add_argument('output_file',
                       help='Path to the output video or audio file')
    parser.add_argument('--reverb', action='store_true',
                       help='Add reverb effect to the audio track')

    args = parser.parse_args()

    # Validate inputs
    check_file_exists(args.input_file)
    percentage = validate_percentage(args.percentage)
    check_ffmpeg()

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output_file)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        except OSError as e:
            print(f"Error: Could not create output directory '{output_dir}': {e}")
            sys.exit(1)

    # Process the media file
    pitch_media(args.input_file, percentage, args.output_file, args.reverb)


if __name__ == "__main__":
    main()