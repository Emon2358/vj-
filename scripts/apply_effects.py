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
    Apply extreme glitch effects with simplified but more stable filter chain
    """
    filter_complex = (
        # Split input into 5 streams for different effects
        "[0:v]split=5[base][vhs][kalei][glitch][noise];"
        
        # Base effect: heavy feedback with color distortion
        "[base]tmix=frames=30:weights='1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1',"
        "hue=h=2*PI*t:s=sin(t)+2[fb];"
        
        # VHS style tracking errors
        "[vhs]rgbashift=rh=-2:bv=2,"
        "curves=r='0/0 0.5/0.4 1/1':g='0/0 0.5/0.6 1/1':b='0/0 0.5/0.5 1/1'[track];"
        
        # Kaleidoscope effect
        "[kalei]rotate=PI/3:ow=rotw(PI/3):oh=roth(PI/3),"
        "split=2[k1][k2];"
        "[k1][k2]blend=all_mode=screen[kal];"
        
        # Random glitch effect
        "[glitch]select='if(mod(n,5),1,0)',"
        "setpts=N/FRAME_RATE/TB[gli];"
        
        # Noise and interference
        "[noise]noise=alls=20:allf=t,"
        "format=rgb24[noi];"
        
        # Combine all effects
        "[fb][track]blend=all_mode=overlay[tmp1];"
        "[tmp1][kal]blend=all_mode=screen[tmp2];"
        "[tmp2][gli]blend=all_mode=addition[tmp3];"
        "[tmp3][noi]blend=all_mode=overlay[final_video];"
        
        # Audio effects
        "[0:a]aecho=0.8:0.88:60:0.4,"
        "flanger,"
        "aphaser[final_audio]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-filter_complex", filter_complex,
        "-map", "[final_video]",
        "-map", "[final_audio]",
        "-c:v", "libx264",
        "-preset", "ultrafast",  # 処理速度を上げるため ultrafast に変更
        "-tune", "grain",        # ノイズや粗さを強調
        "-crf", "23",           # 画質と圧縮率のバランスを調整
        "-c:a", "aac",
        "-b:a", "192k",
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
