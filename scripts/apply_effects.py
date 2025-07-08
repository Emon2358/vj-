import subprocess
import os
import sys
import shlex
from datetime import datetime

def download_video(url, base_filename):
    """
    Download video from the provided URL using yt-dlp.
    """
    url = url.strip()
    if not url:
        sys.exit("No video URL provided")
    output_file = f"videos/input_{base_filename}.mp4"
    cmd = f"yt-dlp -o {output_file} {shlex.quote(url)}"
    print(f"Downloading video: {url}")
    subprocess.run(cmd, shell=True, check=True)
    return output_file

def process_video(input_file, output_path):
    """
    Apply extreme glitch effects with fixed dimensions and format conversions
    """
    filter_complex = (
        # Initialize with format conversion to ensure compatibility
        "[0:v]format=yuv420p,"
        # Split into 4 streams
        "split=4[base][distort][glitch][noise];"
        
        # Base effect with feedback and color distortion
        "[base]tmix=frames=15:weights='1 1 1 1 1 1 1 1 1 1 1 1 1 1 1',"
        "hue=h=2*PI*t:s=sin(t)+2[fb];"
        
        # VHS style distortion
        "[distort]rgbashift=rh=-2:bv=2,"
        "scale=320:240,"  # Force consistent dimensions
        "curves=r='0/0 0.5/0.4 1/1':g='0/0 0.5/0.6 1/1':b='0/0 0.5/0.5 1/1'[vhs];"
        
        # Random glitch effect with consistent dimensions
        "[glitch]select='if(mod(n,3),1,0)',"
        "scale=320:240,"  # Force consistent dimensions
        "setpts=N/FRAME_RATE/TB[gli];"
        
        # Noise effect with consistent dimensions
        "[noise]noise=alls=20:allf=t,"
        "scale=320:240[noi];"  # Force consistent dimensions
        
        # Combine all effects ensuring same dimensions for blend operations
        "[fb][vhs]blend=all_mode=overlay[tmp1];"
        "[tmp1][gli]blend=all_mode=addition[tmp2];"
        "[tmp2][noi]blend=all_mode=overlay,"
        # Final format conversion
        "format=yuv420p[final_video];"
        
        # Audio effects
        "[0:a]aecho=0.8:0.88:60:0.4,"
        "tremolo=f=10:d=0.7[final_audio]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-filter_complex", filter_complex,
        "-map", "[final_video]",
        "-map", "[final_audio]",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "grain",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",  # Explicitly set output pixel format
        output_path
    ]

    print("Running ffmpeg command:")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)

def main():
    video_link = os.environ.get("VIDEO_LINK", "")
    if not video_link:
        sys.exit("Error: VIDEO_LINK environment variable must be set with a video URL")
    
    now = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    os.makedirs("videos", exist_ok=True)
    
    downloaded_file = download_video(video_link, now)
    output_file = f"videos/processed_{now}.mp4"
    
    process_video(downloaded_file, output_file)
    print(f"Processing complete. Output video: {output_file}")

if __name__ == "__main__":
    main()
