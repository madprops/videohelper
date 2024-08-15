import os
import sys
import subprocess

# Get video duration
def get_duration(path: str) -> int:
  d = subprocess.check_output(['ffprobe', '-i', path, '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=%s' % ("p=0")])
  d = d.decode("utf-8").strip()
  return int(float(d))  

# Main function
def main() -> None:
  # Arguments
  path = sys.argv[1]
  seconds = float(sys.argv[2])

  d = get_duration(path)
  os.popen(f"ffmpeg -y -ss 0 -t {d - seconds} -i {path} -c copy trimmed_{path}").read()

# Program starts here
if __name__ == "__main__": main()