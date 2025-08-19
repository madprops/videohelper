#!/usr/bin/env python
"""
GIF Background Cropper

This script processes GIF images to remove black/empty spaces from the left and right sides
by cropping each frame at specified coordinates, then saves the result as a new GIF.
All frames are cropped to the same size for consistency.

Usage:
    python bgcrop.py input.gif output.gif --left 50 --right 200
    python bgcrop.py input.gif output.gif -l 50 -r 200
"""

import argparse
import sys
from pathlib import Path
from PIL import Image, ImageSequence


def crop_gif(input_path, output_path, left_crop, right_crop):
    """
    Crop a GIF by removing specified pixels from left and right sides.

    Args:
        input_path (str): Path to input GIF file
        output_path (str): Path to output GIF file
        left_crop (int): Number of pixels to crop from the left
        right_crop (int): Number of pixels to crop from the right
    """
    try:
        # Open the input GIF
        with Image.open(input_path) as img:
            if not getattr(img, "is_animated", False):
                print("Warning: Input file is not an animated GIF")

            # Get original dimensions
            original_width, original_height = img.size
            print(f"Original dimensions: {original_width}x{original_height}")

            # Calculate new dimensions
            new_width = original_width - left_crop - right_crop
            if new_width <= 0:
                raise ValueError(f"Crop values too large: {left_crop} + {right_crop} >= {original_width}")

            print(f"Cropping {left_crop} pixels from left, {right_crop} pixels from right")
            print(f"New dimensions: {new_width}x{original_height}")

            # Process each frame
            frames = []
            durations = []

            for frame_num, frame in enumerate(ImageSequence.Iterator(img)):
                print(f"Processing frame {frame_num + 1}...", end="\r")

                # Convert frame to RGBA if necessary
                if frame.mode != 'RGBA':
                    frame = frame.convert('RGBA')

                # Crop the frame: (left, top, right, bottom)
                cropped_frame = frame.crop((left_crop, 0, original_width - right_crop, original_height))
                frames.append(cropped_frame)

                # Get frame duration (default to 100ms if not available)
                duration = frame.info.get('duration', 100)
                durations.append(duration)

            print(f"\nProcessed {len(frames)} frames")

            # Save the new GIF
            if frames:
                frames[0].save(
                    output_path,
                    save_all=True,
                    append_images=frames[1:],
                    duration=durations,
                    loop=img.info.get('loop', 0),  # Preserve loop setting
                    optimize=True
                )
                print(f"Saved cropped GIF to: {output_path}")
            else:
                raise ValueError("No frames found in the input GIF")

    except Exception as e:
        print(f"Error processing GIF: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Crop GIF images by removing black/empty spaces from left and right sides",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.gif output.gif --left 50 --right 100
  %(prog)s animation.gif cropped.gif -l 25 -r 25
        """
    )

    parser.add_argument("input", help="Input GIF file path")
    parser.add_argument("output", help="Output GIF file path")
    parser.add_argument("-l", "--left", type=int, required=True,
                       help="Number of pixels to crop from the left side")
    parser.add_argument("-r", "--right", type=int, required=True,
                       help="Number of pixels to crop from the right side")

    args = parser.parse_args()

    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file '{args.input}' not found")
        sys.exit(1)

    if not input_path.suffix.lower() in ['.gif']:
        print(f"Warning: Input file '{args.input}' may not be a GIF file")

    # Validate crop values
    if args.left < 0 or args.right < 0:
        print("Error: Crop values must be non-negative")
        sys.exit(1)

    # Create output directory if it doesn't exist
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Input: {args.input}")
    print(f"Output: {args.output}")

    # Process the GIF
    crop_gif(args.input, args.output, args.left, args.right)


if __name__ == "__main__":
    main()