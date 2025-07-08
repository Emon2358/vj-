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
    Process video with optimized effects and compression for GitHub's 100MB limit
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
    
    # Calculate new dimensions to reduce file size
    # Maintain aspect ratio but reduce resolution
    new_width = 480
    new_height = int((new_width/width) * height)
    new_height = new_height - (new_height % 2)  # Make sure height is even

    filter_complex = (
        # Start with format conversion, scaling, and splitting
        f"[0:v]format=yuv420p,scale={new_width}:{new_height},"
        "split=4[base][distort][glitch][noise];"
        
        # 残像エフェクト
        "[base]tmix=frames=6:weights='1 1 1 1 1 1'[fb];"
        
        # VHS風グリッチ
        "[distort]rgbashift=rh=-2:bv=2,"
        "curves=r='0/0 0.5/0.4 1/1':g='0/0 0.5/0.6 1/1':b='0/0 0.5/0.5 1/1'[vhs];"
        
        # フレーム抜きグリッチ
        "[glitch]select='if(mod(n,3),1,0)',"
        "setpts=N/FRAME_RATE/TB[gli];"
        
        # ノイズエフェクト
        "[noise]noise=alls=20:allf=t[noi];"
        
        # エフェクトの合成
        "[fb][vhs]blend=all_mode=overlay[tmp1];"
        "[tmp1][gli]blend=all_mode=addition[tmp2];"
        "[tmp2][noi]blend=all_mode=overlay,format=yuv420p[final_video];"
        
        # オーディオエフェクト - より低いビットレート
        "[0:a]aecho=0.8:0.88:60:0.4,tremolo=f=10:d=0.7,volume=0.8[final_audio]"
    )

    # Two-pass encoding for better compression
    pass1_cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-filter_complex", filter_complex,
        "-map", "[final_video]",
        "-map", "[final_audio]",
        "-c:v", "libx264",
        "-preset", "slow",     # より効率的な圧縮のためにpresetを変更
        "-tune", "grain",
        "-b:v", "800k",       # ビデオビットレートを制限
        "-pass", "1",
        "-f", "null",
        "/dev/null"
    ]

    pass2_cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-filter_complex", filter_complex,
        "-map", "[final_video]",
        "-map", "[final_audio]",
        "-c:v", "libx264",
        "-preset", "slow",
        "-tune", "grain",
        "-b:v", "800k",
        "-pass", "2",
        "-c:a", "aac",
        "-b:a", "96k",        # オーディオビットレートを低く設定
        "-ac", "2",           # ステレオ
        "-ar", "44100",       # サンプルレートを標準的な値に
        "-pix_fmt", "yuv420p",
        output_path
    ]

    print("Running first pass...")
    subprocess.run(pass1_cmd, check=True)
    
    print("Running second pass...")
    subprocess.run(pass2_cmd, check=True)

    # Check final file size
    file_size = os.path.getsize(output_path)
    if file_size > 95 * 1024 * 1024:  # If still over 95MB
        print("Warning: File still too large, applying emergency compression...")
        emergency_output = output_path.replace('.mp4', '_compressed.mp4')
        emergency_cmd = [
            "ffmpeg", "-y",
            "-i", output_path,
            "-c:v", "libx264",
            "-preset", "veryslow",
            "-crf", "28",
            "-c:a", "aac",
            "-b:a", "64k",
            emergency_output
        ]
        subprocess.run(emergency_cmd, check=True)
        os.replace(emergency_output, output_path)

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
    
    # 最終確認
    final_size = os.path.getsize(output_file)
    print(f"Final file size: {final_size / 1024 / 1024:.2f}MB")

if __name__ == "__main__":
    main()
