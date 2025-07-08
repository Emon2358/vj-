import subprocess
import os
import sys
import shlex
from datetime import datetime

def download_video(url, base_filename):
    """
    Download the video from the provided URL using yt-dlp.
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
    Apply multiple video effects simultaneously:
    - インサイド・フィードバック (Inside Feedback)
    - アウトサイド・フィードバック (Outside Feedback) 
    - クロマキー (Chroma Key)
    - スーパーインポーズ (Superimpose)
    - コマ撮り (Stop Motion)
    - テロップ映像 (Telop Video)
    - オーディオ/ビデオ信号ミックス (Audio/Video Signal Mix)
    """
    filter_complex = (
        # Split input into multiple streams
        "[0:v]split=6[base][fb1][fb2][chroma][motion][telop];"
        
        # インサイド・フィードバック: Heavy feedback effect with tmix
        "[fb1]tmix=frames=30:weights='1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1'[inside_fb];"
        
        # アウトサイド・フィードバック: Delayed feedback with setpts
        "[fb2]setpts=PTS+0.5/TB[outside_fb];"
        
        # クロマキー: Apply chroma key effect (green screen)
        "[chroma]colorkey=0x00FF00:0.3:0.2[keyed];"
        
        # コマ撮り: Stop motion effect
        "[motion]select='not(mod(n,4))',setpts=N/FRAME_RATE/TB[stop_motion];"
        
        # テロップ: Scale down for telop overlay
        "[telop]scale=iw/3:ih/3[small_telop];"
        
        # スーパーインポーズ: Blend all effects together
        "[base][inside_fb]blend=all_mode=addition[tmp1];"
        "[tmp1][outside_fb]blend=all_mode=lighten[tmp2];"
        "[tmp2][keyed]overlay[tmp3];"
        "[tmp3][stop_motion]blend=all_mode=screen[tmp4];"
        "[tmp4][small_telop]overlay=W-w-10:H-h-10[final_video];"
        
        # オーディオミックス: Mix original and delayed audio
        "[0:a]asplit=2[a1][a2];"
        "[a2]adelay=1000|1000[delayed];"
        "[a1][delayed]amix=inputs=2:weights=1 1[final_audio]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-filter_complex", filter_complex,
        "-map", "[final_video]",
        "-map", "[final_audio]",
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
        sys.exit("Error: VIDEO_LINK environment variable must be set with a video URL")
    
    now = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    os.makedirs("videos", exist_ok=True)
    
    downloaded_file = download_video(video_link, now)
    output_file = f"videos/processed_{now}.mp4"
    
    process_video(downloaded_file, output_file)
    print(f"Processing complete. Output video: {output_file}")

if __name__ == "__main__":
    main()
