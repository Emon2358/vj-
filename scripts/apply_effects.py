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
    映像を視認できないほどにグリッチ効果を適用します。
    """
    # FFprobeを使って実際の解像度を取得する
    input_width = 320
    input_height = 240
    try:
        probe_cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x",
            input_file
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        width_height = result.stdout.strip().split('x')
        input_width = int(width_height[0])
        input_height = int(width_height[1])
        print(f"Detected input resolution: {input_width}x{input_height}")
    except Exception as e:
        print(f"Could not detect video resolution, using default {input_width}x{input_height}. Error: {e}")


    filter_complex = (
        # オリジナル映像をsplitで2つに分ける
        "[0:v]split=2[original][feedback];"
        
        # フィードバック映像に遅延とずれ、そして様々なグリッチ効果を適用
        "[feedback]"
        f"scale={input_width}:{input_height}," # まず元のサイズに揃える
        "tpad=start=0.1:stop=3," # 100ms遅延
        "rotate=1.0:ow=rotw(1.0):oh=roth(1.0)," # より大きな角度で回転（1.0ラジアン = 約57度）
        f"scale={input_width}:{input_height}," # 回転によってサイズが変わる可能性があるので、再度元のサイズにスケール
        "colorchannelmixer=0.5:0.5:0.5:0.5:0.5:0.5:0.5:0.5:0.5," # 各チャンネルを強く混ぜる
        "geq=random(1)*100:random(1)*100:random(1)*100," # ピクセル値をランダムに変化させノイズを加える
        "gblur=sigma=3:steps=1," # boxblurの代わりにgblurを使用
        # ★ここを修正: pixelizeの代わりにscaleとsetsarを組み合わせてピクセレート効果を再現
        f"scale=iw/{16}:ih/{16},"  # 小さな解像度にスケールダウン (例: 16x16ブロック)
        f"scale={input_width}:{input_height}:flags=neighbor," # 元の解像度に戻す際にニアレストネイバーで補間し、ピクセル効果を出す
        "settb=AVTB," # タイムベース設定
        "setpts=PTS+0.1/TB[delayed];" # さらなる遅延効果
        
        # オリジナルとフィードバック映像をブレンド
        "[original][delayed]blend=all_mode=overlay:all_opacity=0.9[v];" # 不透明度を上げてフィードバックの影響を強める
        
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
