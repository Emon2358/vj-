import subprocess
import os
import sys
import shlex
from datetime import datetime
import random # ランダムな値を生成するために追加

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
    革新的な方法で、視認できないほど高威力なグリッチ効果を適用します。
    """
    # FFprobeを使って実際の解像度とフレームレートを取得する
    input_width = 320
    input_height = 240
    input_fps = 30 # デフォルト値
    try:
        probe_cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height,avg_frame_rate", "-of", "csv=p=0:s=x",
            input_file
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        parts = result.stdout.strip().split(',')
        if len(parts) >= 2:
            width_height = parts[0].split('x')
            input_width = int(width_height[0])
            input_height = int(width_height[1])
        if len(parts) >= 3:
            try:
                num, den = map(int, parts[2].split('/'))
                input_fps = num / den
            except ValueError:
                pass # フレームレート取得失敗時はデフォルト値を使用
        print(f"Detected input resolution: {input_width}x{input_height}, FPS: {input_fps:.2f}")
    except Exception as e:
        print(f"Could not detect video resolution/FPS, using default {input_width}x{input_height}, {input_fps:.2f}fps. Error: {e}")

    # ランダムなグリッチ値を生成
    random_rotate_angle = round(random.uniform(1.0, 5.0), 2) # より大きなランダム回転
    random_geq_factor = random.randint(100, 300) # geqの強度を上げる
    random_opacity = round(random.uniform(0.7, 0.99), 2) # blendの不透明度をランダムに高くする
    glitch_fps = random.choice([5, 10, 15, 60, 120]) # 意図的に異なるフレームレートを混ぜる
    
    # タイムライン破壊のためのダミー字幕ファイルを作成 (FFmpegがファイルを探す場所に適当なファイル)
    # 実際の字幕は表示されないが、フィルターチェーンの複雑性を増し、エラーを誘発する可能性を高める
    dummy_ass_file = "dummy_glitch.ass"
    with open(dummy_ass_file, "w") as f:
        f.write("[Script Info]\n")
        f.write("ScriptType: v4.00+\n")
        f.write("\n[V4+ Styles]\n")
        f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        f.write("Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1\n")
        f.write("\n[Events]\n")
        f.write(f"Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        f.write(f"Dialogue: 0,0:00:00.00,0:00:00.01,Default,,0,0,0,,{{\\blur10}}Random Glitch Text {random.randint(0, 1000)}\n")


    filter_complex = (
        # オリジナル映像をsplitで2つに分ける
        "[0:v]split=2[original][feedback];"
        
        # フィードバック映像に遅延とずれ、様々なグリッチ効果を適用
        f"[feedback]fps={glitch_fps}," # フレームレートを意図的に変更して時間的な歪みを加える
        f"scale={input_width}:{input_height}," # サイズを揃える
        "tpad=start=0.1:stop=3," # 100ms遅延
        f"rotate={random_rotate_angle}:ow=rotw({random_rotate_angle}):oh=roth({random_rotate_angle})," # より大きなランダムな角度で回転
        f"scale={input_width}:{input_height}," # 回転によってサイズが変わるので、再度元のサイズにスケール
        "colorchannelmixer="
            "1.5:0.5:0.5:0.5:0.5:1.5:0.5:0.5:0.5:0.5:0.5:1.5," # 各チャンネルを極端に混ぜる (より破壊的な値)
        f"geq=random(1)*{random_geq_factor}:random(1)*{random_geq_factor}:random(1)*{random_geq_factor}," # ピクセル値をランダムに、より強く変化
        "gblur=sigma=5:steps=2," # ぼかし強度とステップを上げる
        f"scale=iw/{random.uniform(5, 20)}:ih/{random.uniform(5, 20)},"  # ランダムな粒度でスケールダウン
        f"scale={input_width}:{input_height}:flags=neighbor," # ニアレストネイバーでピクセル効果を出す
        "negate," # 色を反転させることでさらに視覚的な混乱を招く
        "setpts=PTS+random(0)*0.5/TB[delayed];" # setptsでランダムな遅延を付加し、時間的な破壊を強調

        # オリジナルとフィードバック映像をブレンド
        f"[original][delayed]blend=all_mode=difference:all_opacity={random_opacity}[v];" # blendモードをdifferenceに、不透明度を上げる
        
        # オーディオはそのまま通過（ここにはグリッチを適用しない）
        "[0:a]acopy[a]"
    )

    # エンコード設定
    # スライス数を増やすことでエンコード時のデータ破損を誘発し、グリッチを強化する
    # これはFFmpegの内部的な動作に依存するため、すべての環境で同じ効果が得られるわけではない
    # また、`-sub_charenc` のような存在しないオプションを意図的に入れることでエラーを誘発する可能性もあるが、
    # FFmpegがすぐに停止する可能性があるため、ここでは採用しない。
    
    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-filter_complex", filter_complex,
        # `-vf` を使用して `ass` フィルターを追加し、存在しないファイルを指定することでエラーを誘発
        # この方法はFFmpegがフィルターチェーンでエラーを出すため、通常は勧められないが、グリッチ目的では有効な場合がある
        # しかし、ここでは`filter_complex`内に直接含める方が安全性が高い
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "28", # 画質を意図的に下げて、圧縮アーティファクトをグリッチとして利用
        "-c:a", "aac",
        "-b:a", "64k", # 音声ビットレートも下げて、音声の劣化も促す
        "-pix_fmt", "yuv420p",
        "-flags", "+cgop+ilme+ildct", # 不安定なエンコードフラグ
        "-sc_threshold", "0", # シーンチェンジ検出を無効にし、Iフレーム挿入を減らす (グリッチに貢献)
        "-g", "1", # GOPサイズを最小にすることで、フレーム間予測のエラーを広げやすくする
        "-slices", str(random.randint(4, 16)), # ランダムなスライス数でエンコードを試み、データ破損を誘発
        output_path
    ]

    print("Running ffmpeg command:")
    print(" ".join(cmd))
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg command failed with exit code {e.returncode}. This might be intentional for extreme glitches!")
        print(f"Command: {e.cmd}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        # 極端なグリッチを狙うため、FFmpegのエラーを無視して続行するか、特定のコードで終了するか選択
        # ここでは、エラーが出てもメッセージを表示し、スクリプト自体は終了しないようにする
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print("Partial output file generated. It might still contain glitches!")
        else:
            sys.exit("FFmpeg failed to produce any output file. Try reducing the intensity of some filters.")

    finally:
        # ダミー字幕ファイルを削除
        if os.path.exists(dummy_ass_file):
            os.remove(dummy_ass_file)


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
