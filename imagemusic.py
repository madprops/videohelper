import os
import sys
from pathlib import Path

def main() -> None:
  image = sys.argv[1]
  audio = sys.argv[2]
  output = sys.argv[3]

  os.popen(f"ffmpeg -loop 1 -i {image} -i {audio} -c:v libx264 -tune stillimage -c:a aac -b:a 320k -pix_fmt yuv420p -shortest {output}.mp4")

if __name__ == "__main__": main()