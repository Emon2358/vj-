import subprocess
import os
import sys
import shlex
from datetime import datetime
import multiprocessing

def download_video(url, base_filename):
    """
    Download the video from the provided Nico Nico URL using yt-dlp.
    """
    url = url.strip()
    if not url:
        sys.exit("No video URL provided.")
    output_file = f"videos/input_{base_filename}.mp4"
    cmd = f"yt-dlp -o {output_file} {shlex.quote(url)}"
    print(f"Downloading video: {url}")
    subprocess.run(cmd, shell=True, check=True)
    return output_file

def process_video(input_file, output_path):
    """
    Process the video with optimized performance settings.
    """
    # Get number of CPU cores for optimal threading
    cpu_count = multiprocessing.cpu_count()
    
    filter_complex = (
        "[0:v]edgedetect=low=0.1:high=0.4,format=rgba,"
        "lut=a='if(gt(val,128),255,0)'[lines];"
        "color=c=green:s=320x240,format=rgba[bg];"
        "[bg][lines]overlay=format=auto,format=rgba[combined];"
        "[combined]tmix=frames=3:weights='1 1 1'[final];"
        "[0:a]anull[aout]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        # Input file with thread optimization
        "-threads", str(cpu_count),
        "-i", input_file,
        # Filter complex
        "-filter_complex", filter_complex,
        # Output options optimized for speed
        "-map", "[final]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "ultrafast",     # Fastest encoding
        "-tune", "fastdecode",      # Optimize for fast decoding
        "-crf", "23",              # Slightly reduced quality for better speed
        "-c:a", "aac",
        "-b:a", "128k",            # Reduced audio bitrate
        "-movflags", "+faststart",  # Optimize for web playback
        "-g", "30",                # Keyframe interval
        "-bf", "2",                # Maximum 2 B-frames
        "-maxrate", "2M",          # Maximum bitrate
        "-bufsize", "2M",          # Buffer size
        "-row-mt", "1",            # Enable row-based multithreading
        "-threads", str(cpu_count), # Use all CPU cores
        output_path
    ]
    
    print("Running ffmpeg command with performance optimization:")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)

def main():
    video_link = os.environ.get("VIDEO_LINK", "")
    if not video_link:
        sys.exit("Error: VIDEO_LINK environment variable must be set with a Nico Nico video URL.")
    
    now = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    os.makedirs("videos", exist_ok=True)
    
    downloaded_file = download_video(video_link, now)
    output_file = f"videos/processed_{now}.mp4"
    
    # Record start time
    start_time = datetime.utcnow()
    print(f"Processing started at: {start_time}")
    
    process_video(downloaded_file, output_file)
    
    # Record end time and calculate duration
    end_time = datetime.utcnow()
    duration = end_time - start_time
    print(f"Processing completed at: {end_time}")
    print(f"Total processing time: {duration}")
    print(f"Output video: {output_file}")

if __name__ == "__main__":
    main()
