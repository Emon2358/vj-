import subprocess
import os
import sys
import shlex
from datetime import datetime

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
    Process the video so that only the drawing/lines (edges) remain visible.
    The remaining areas are made transparent and then filled with a flat (chroma-key) solid color.
    Additionally, a clear afterimage (ghost trail) is applied on each frame.
    
    Processing steps:
      1. Extract edges using the 'edgedetect' filter.
         This retains only the outlines (the drawing and background lines) from the video.
      2. Use the LUT filter to force non-edge areas to become transparent.
      3. Create a solid-colored (green) background.
      4. Overlay the edge extraction (with transparency) onto the colored background.
      5. Apply a tmix filter to blend successive frames and produce a distinct afterimage effect.
      6. Pass through audio unchanged.
    """
    # Build the complex filter chain.
    # Note: The parameters (e.g., low/high thresholds, LUT threshold, tmix settings) are set for an aggressive effect.
    filter_complex = (
        # Step 1: Extract edges. 'edgedetect' produces white lines on a black background.
        "[0:v]edgedetect=low=0.1:high=0.4,format=rgba,"
        # Step 2: Use LUT to set alpha: if pixel value > 128 then opaque, else transparent.
        "lut=a='if(val>128,255,0)'[lines];"
        # Step 3: Create a solid green background, matching our target chroma-key color.
        "color=c=green:s=320x240,format=rgba[bg];"
        # Step 4: Overlay the edge image (with transparency) onto the background.
        "[bg][lines]overlay=format=auto,format=rgba[combined];"
        # Step 5: Apply a tmix filter to create a pronounced afterimage (ghost trail) effect.
        "[combined]tmix=frames=3:weights='1 1 1'[final];"
        # Step 6: Pass through the audio unchanged.
        "[0:a]anull[aout]"
    )
    
    cmd = [
        "ffmpeg", "-y", "-i", input_file,
        "-filter_complex", filter_complex,
        "-map", "[final]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-c:a", "aac",
        output_path
    ]
    
    print("Running ffmpeg command:")
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
    
    process_video(downloaded_file, output_file)
    print(f"Processing complete. Output video: {output_file}")

if __name__ == "__main__":
    main()
