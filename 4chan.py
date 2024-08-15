import os
import sys
from pathlib import Path

path = sys.argv[1]

if (len(sys.argv)) > 2:
  bitrate = float(sys.argv[2])
else:
  bitrate = 500

new_file = str(Path(path).parent / Path(path).stem) + "_4c.webm"
os.popen(f"ffmpeg -i '{path}' -c:v libvpx-vp9 -b:v {bitrate}K -an {new_file}")