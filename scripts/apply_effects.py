import subprocess
import os
import sys
import shlex
from datetime import datetime

def download_video(url, base_filename):
    """ニコニコ動画からダウンロード"""
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
    アナログビデオミキサーのフィードバック効果をエミュレート:
    1. インプット1からの映像をアウトプット1へ
    2. アウトプット1からインプット2へフィードバック(右/斜めにずれを入れる)
    3. インプット1とインプット2の映像を合成
    4. 上記プロセスを繰り返してフィードバックループを生成
    """
    filter_complex = (
        # オリジナル映像をsplitで2つに分ける
        "[0:v]split=2[original][feedback];"
        
        # フィードバック映像に遅延とずれを適用
        "[feedback]tpad=start=0.1:stop=3," # 100ms遅延
        "crop=iw:ih:0:0," # 映像の一部を切り取り (このcropは意味がないかもしれません)
        "rotate=0.5:ow=rotw(0.5):oh=roth(0.5)," # 0.5度の回転で斜めずれを表現
        "scale=320:240," # ★ここを修正: 元の解像度に戻す (320x240はログから取得)
        "settb=AVTB," # タイムベース設定
        "setpts=PTS+0.1/TB[delayed];" # さらなる遅延効果
        
        # オリジナルとフィードバック映像をブレンド
        "[original][delayed]blend=all_mode=overlay:all_opacity=0.7[v];"
        
        # オーディオはそのまま通過
        "[0:a]acopy[a]"
    )

    # エンコード設定
    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-pix_fmt", "yuv420p",
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
    
    # ファイルサイズの確認
    final_size = os.path.getsize(output_file)
    print(f"Final file size: {final_size / 1024 / 1024:.2f}MB")

if __name__ == "__main__":
    main()
