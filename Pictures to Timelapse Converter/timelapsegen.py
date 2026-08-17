import os
import re
import subprocess

# Folder containing images
input_folder = input("Enter folder with JPEG files: ").strip()

# Output file
output_video = "timelapse.mp4"

# Regex for filenames like: 20251102_00_13_14.jpg
pattern = re.compile(r"(\d{8})_(\d{2})_(\d{2})_(\d{2})\.jpg$")

# Collect files + extract timestamps
files = []
for f in os.listdir(input_folder):
    match = pattern.match(f)
    if match:
        date, hh, mm, ss = match.groups()
        timestamp = f"{date}{hh}{mm}{ss}"
        files.append((timestamp, f))

# Sort by numeric timestamp
files.sort(key=lambda x: x[0])

if not files:
    print("No matching files found.")
    exit()

# Create temporary ffmpeg list file
list_path = os.path.join(input_folder, "frames.txt")
with open(list_path, "w") as list_file:
    for _, filename in files:
        full_path = os.path.abspath(os.path.join(input_folder, filename))
        safe_path = full_path.replace("\\", "/")
        list_file.write(f"file '{safe_path}'\n")

# Build command
cmd = [
    "ffmpeg",
    "-y",
    "-r", "25",                     # Input FPS
    "-f", "concat",
    "-safe", "0",
    "-i", list_path,
    "-vf", "format=yuv420p",
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    output_video
]

# Run ffmpeg
print("Building timelapse video...")
subprocess.run(cmd)

print(f"Timelapse created: {output_video}")
