import subprocess
import os
import sys
import shlex
from datetime import datetime

def download_video(url, base_filename):
    """
    Download the video from the provided URL using yt-dlp.
    Returns the downloaded filename.
    """
    url = url.strip()
    if not url:
        sys.exit("No video URL provided.")
    output_file = f"videos/input_{base_filename}.mp4"
    # Using yt-dlp (which supports Nico Nico video URLs) to download the video
    cmd = f"yt-dlp -o {output_file} {shlex.quote(url)}"
    print(f"Downloading video: {url}")
    subprocess.run(cmd, shell=True, check=True)
    return output_file

def process_video(input_file, output_path):
    """
    Apply a chain of super-strong glitch effects on a single video.
    
    Effects applied concurrently:
      - インサイド・フィードバック: using tmix.
      - アウトサイド・フィードバック: using setpts delay.
      - クロマキー: using colorkey (removes green components).
      - スーパーインポーズ: blending multiple processed streams.
      - コマ撮り: stop-motion effect via frame skipping.
      - テロップとしての映像読み込み: scaling down the video overlay.
      - オーディオ信号とビデオ信号の混合: mixing original audio with a delayed copy.
      
    The final filter_complex chain splits the input video into five branches:
      [v0] -> for inside feedback,
      [v1] -> for outside feedback,
      [v2] -> for chroma key effect,
      [v3] -> for stop-motion effect,
      [v4] -> for teletext overlay.
      
    They are then blended together in the following order:
      1. Blend inside and outside feedback ([v0] and [v1]) into [feedback].
      2. Blend [feedback] with stop-motion [v3] into [combined].
      3. Overlay the chroma keyed stream [v2] atop [combined] to yield [with_chroma].
      4. Overlay the teletext stream [v4] (scaled down) into the bottom-right, resulting in [final].
      
    For audio, a delayed copy of the audio stream is created and mixed with the original.
    """
    # Build filter_complex chain
    filter_complex = (
        # Split the input video into 5 copies and scale each to 320x240 for consistency.
        "[0:v]split=5[v0][v1][v2][v3][v4];"
        # インサイド・フィードバック: apply heavy tmix on [v0]
        "[v0]tmix=frames=10:weights='1 1 1 1 1 1 1 1 1 1'[inside];"
        # アウトサイド・フィードバック: delay [v1]
        "[v1]setpts=PTS+1/TB[outside];"
        # Blend inside and outside feedback to create a combined feedback effect.
        "[inside][outside]blend=all_mode=addition[feedback];"
        # クロマキー: apply colorkey on [v2] to remove green (0x00FF00)
        "[v2]colorkey=0x00FF00:0.3:0.2[chroma];"
        # コマ撮り: apply stop-motion effect on [v3] (drop every other frame)
        "[v3]select='not(mod(n,2))',setpts=N/FRAME_RATE/TB[stopmo];"
        # スーパーインポーズ: blend feedback and stop-motion streams
        "[feedback][stopmo]blend=all_mode=addition[combined];"
        # テロップ: scale down [v4] for overlay as teletext (e.g., 1/4 size)
        "[v4]scale=iw/4:ih/4[tele];"
        # Overlay chroma keyed video over the combined result (position at top-left)
        "[combined][chroma]overlay=0:0[with_chroma];"
        # Finally, overlay the teletext video at the bottom-right (10 pixels margin)
        "[with_chroma][tele]overlay=W-w-10:H-h-10[final];"
        # Audio: create a delayed copy of the audio and mix with original.
        "[0:a]adelay=500|500[a_delay];"
        "[0:a][a_delay]amix=inputs=2[aout]"
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
    # Use environment variable VIDEO_LINK for the Nico Nico video URL.
    video_link = os.environ.get("VIDEO_LINK", "")
    if not video_link:
        sys.exit("Error: VIDEO_LINK environment variable must be set to a Nico Nico video URL.")
    
    now = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    # Ensure videos directory exists
    os.makedirs("videos", exist_ok=True)
    
    # Download the video using yt-dlp (which supports Nico Nico)
    downloaded_file = download_video(video_link, now)
    
    # Define the output file name
    output_file = f"videos/processed_{now}.mp4"
    
    # Process the downloaded video with all effects applied concurrently.
    process_video(downloaded_file, output_file)
    
    print(f"Processing complete. Output video: {output_file}")
    # Optionally, cleanup input file:
    # os.remove(downloaded_file)

if __name__ == "__main__":
    main()
