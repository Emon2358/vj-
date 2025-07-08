import subprocess
import os
import sys
import shlex
from datetime import datetime

def download_video(url, base_filename):
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
    Process video with optimized effects chain:
    - VHS風のグリッチ効果
    - 残像エフェクト
    - ノイズ効果
    スケーリングの問題を修正し、パフォーマンスを改善
    """
    # Get input video dimensions
    probe_cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0",
        input_file
    ]
    dimensions = subprocess.check_output(probe_cmd).decode().strip().split(',')
    width, height = map(int, dimensions)

    filter_complex = (
        # Start with format conversion and splitting
        "[0:v]format=yuv420p,split=4[base][distort][glitch][noise];"
        
        # 残像エフェクト
        "[base]tmix=frames=8:weights='1 1 1 1 1 1 1 1',"
        f"scale={width}:{height}[fb];"
        
        # VHS風グリッチ
        "[distort]rgbashift=rh=-2:bv=2,"
        f"scale={width}:{height},"
        "curves=r='0/0 0.5/0.4 1/1':g='0/0 0.5/0.6 1/1':b='0/0 0.5/0.5 1/1'[vhs];"
        
        # フレーム抜きグリッチ
        "[glitch]select='if(mod(n,3),1,0)',"
        f"scale={width}:{height},"
        "setpts=N/FRAME_RATE/TB[gli];"
        
        # ノイズエフェクト
        "[noise]noise=alls=20:allf=t,"
        f"scale={width}:{height}[noi];"
        
        # エフェクトの合成
        "[fb][vhs]blend=all_mode=overlay[tmp1];"
        "[tmp1][gli]blend=all_mode=addition[tmp2];"
        "[tmp2][noi]blend=all_mode=overlay,format=yuv420p[final_video];"
        
        # オーディオエフェクト
        "[0:a]aecho=0.8:0.88:60:0.4,tremolo=f=10:d=0.7[final_audio]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-filter_complex", filter_complex,
        "-map", "[final_video]",
        "-map", "[final_audio]",
        "-c:v", "libx264",
        "-preset", "ultrafast",  # 最速の処理速度
        "-tune", "grain",        # ノイズ/グレイン効果に最適化
        "-crf", "23",           # 画質と圧縮率のバランス
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",  # 互換性の高いピクセルフォーマット
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
