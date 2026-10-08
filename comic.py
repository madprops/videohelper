import argparse
import glob
import os
import random
import subprocess

def get_audio_duration(audio_path):
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Error getting audio duration: {result.stderr}")

    return float(result.stdout.strip())

def parse_overrides(override_str):
    overrides = {}

    if not override_str:
        return overrides

    # We expect pairs split by commas, and keys/values split by colons e.g., "2:500, 3:1200"
    pairs = override_str.split(",")

    for pair in pairs:
        parts = pair.split(":")

        if len(parts) == 2:
            frame_idx = int(parts[0].strip())
            duration_ms = int(parts[1].strip())
            overrides[frame_idx] = duration_ms

    return overrides

def create_video(image_dir, base_ms, audio_path, override_str, output_path="output.mp4"):
    images = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp", "*.JPG", "*.JPEG", "*.PNG", "*.WEBP"):
        images.extend(glob.glob(os.path.join(image_dir, ext)))
    images = sorted(images)

    if not images:
        print("No images found in the specified directory.")
        return

    overrides = parse_overrides(override_str)
    concat_file = "concat_inputs.txt"
    total_video_duration = 0.0

    with open(concat_file, "w") as f:
        for i, img_path in enumerate(images):
            safe_path = os.path.abspath(img_path).replace("'", "'\\''")

            if i in overrides:
                duration_sec = overrides[i] / 1000.0
            else:
                duration_sec = base_ms / 1000.0

            f.write(f"file '{safe_path}'\n")
            f.write(f"duration {duration_sec}\n")
            total_video_duration += duration_sec

        last_safe_path = os.path.abspath(images[-1]).replace("'", "'\\''")
        f.write(f"file '{last_safe_path}'\n")

    audio_duration = get_audio_duration(audio_path)
    max_start = audio_duration - total_video_duration

    if max_start > 0:
        start_time = random.uniform(0, max_start)
    else:
        start_time = 0.0

    print(f"Total video duration: {total_video_duration}s")
    print(f"Audio duration: {audio_duration}s")
    print(f"Random audio start time: {start_time}s")

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        concat_file,
        "-ss",
        str(start_time),
        "-i",
        audio_path,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-t",
        str(total_video_duration),
        "-shortest",
        output_path
    ]
    subprocess.run(ffmpeg_cmd)

    if os.path.exists(concat_file):
        os.remove(concat_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Join images into a video with random audio start.")
    parser.add_argument("image_dir", help="Directory containing images")
    parser.add_argument("base_ms", type=int, help="Base duration per image in milliseconds (e.g. 5000)")
    parser.add_argument("audio_path", help="Path to the audio file")
    parser.add_argument("--overrides", type=str, default="", help="Format: 'frame:ms, frame:ms' e.g. '2:500, 3:1200' (0-indexed)")
    parser.add_argument("--output", type=str, default="output.mp4", help="Output video file path")

    args = parser.parse_args()
    create_video(args.image_dir, args.base_ms, args.audio_path, args.overrides, args.output)