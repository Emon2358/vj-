import subprocess
import os
import sys
import shlex
from datetime import datetime
import random
import math # mathモジュールをインポート

def download_video(url, base_filename):
    """ニコニコ動画からダウンロード"""
    url = url.strip()
    if not url:
        sys.exit("No video URL provided")
    
    # videosディレクトリがなければ作成
    os.makedirs("videos", exist_ok=True)
    
    output_file = f"videos/input_{base_filename}.mp4"
    cmd = f"yt-dlp -o {output_file} {shlex.quote(url)}"
    print(f"Downloading video: {url}")
    
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(f"Failed to download video: {url}. Error: {e}")
        
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
        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True, encoding='utf-8')
        parts = result.stdout.strip().split(',')
        if len(parts) >= 2:
            width_height = parts[0].split('x')
            input_width = int(width_height[0])
            input_height = int(width_height[1])
        if len(parts) >= 3:
            try:
                num, den = map(int, parts[2].split('/'))
                input_fps = num / den if den != 0 else 30 # ZeroDivisionError対策
            except ValueError:
                pass 
        print(f"Detected input resolution: {input_width}x{input_height}, FPS: {input_fps:.2f}")
    except Exception as e:
        print(f"Could not detect video resolution/FPS, using default {input_width}x{input_height}, {input_fps:.2f}fps. Error: {e}")

    # ランダムなグリッチ値を生成
    random_rotate_angle_degrees = round(random.uniform(0.5, 10.0), 2) # 度数法で生成
    random_rotate_angle_radians = random_rotate_angle_degrees * math.pi / 180 # ラジアンに変換
    random_geq_factor = random.randint(300, 800) # geqの強度をさらに上げる
    glitch_fps = random.choice([0.5, 1, 2, 3, 5, 10, 60, 120]) # 極端なフレームレートを混ぜる (0.5を追加)
    pixel_block_size = random.randint(4, 48) # ピクセル化ブロックのサイズをランダムに (さらに極端に)
    noise_strength = random.randint(20, 50) # ノイズフィルターの強度をさらに上げる
    distortion_factor = round(random.uniform(0.01, 0.1), 3) # ディストーションの強度
    random_chroma_shift = random.randint(10, 50) # 色ずれの強度
    # random_vignette_darkness = round(random.uniform(0.3, 0.8), 2) # ビニエットの暗さ (0.0 - 1.0) -> この行は使用しないためコメントアウトまたは削除
    
    # 意図的にエラーを誘発するためのパラメータ
    deadzone = round(random.uniform(0.01, 0.2), 2) # 量子化時のデッドゾーンをランダムに (floatのまま)

    filter_complex = (
        # ====== 映像ストリーム1: オリジナルをベースにした破壊的なフィードバック ======
        "[0:v]split=2[original][feedback_raw];"
        
        # feedback_raw に極端なグリッチを適用
        "[feedback_raw]"
        f"fps={glitch_fps}," # フレームレートを意図的に変更
        f"scale={input_width}:{input_height}," # サイズを揃える
        "tpad=start=0.05:stop=2," # 短い遅延
        f"rotate={random_rotate_angle_radians}:ow=rotw({random_rotate_angle_radians}):oh=roth({random_rotate_angle_radians})," # 大角度回転 (radiansを使用)
        f"scale={input_width}:{input_height}," # 回転後のサイズ調整
        "colorchannelmixer="
            "2.0:-0.5:-0.5:0: " # 赤チャンネルを強調し、他を打ち消す
            "-0.5:2.0:-0.5:0: " # 緑チャンネルを強調
            "-0.5:-0.5:2.0:0: " # 青チャンネルを強調
            "0:0:0:1," # アルファチャンネルはそのまま (全体的に強調・ネガティブ効果)
        f"geq=r='random(1)*{random_geq_factor}':g='random(1)*{random_geq_factor}':b='random(1)*{random_geq_factor}'," # 強力なランダムノイズ
        "gblur=sigma=10:steps=5," # ぼかし強度をさらに上げる
        f"scale=iw/{pixel_block_size}:ih/{pixel_block_size}," # ランダムな粒度でスケールダウン
        f"scale={input_width}:{input_height}:flags=neighbor," # ニアレストネイバーでピクセル効果
        "negate," # 色を反転
        "loop=loop=30:size=1:start=0," # 短いループで映像をスタック (回数を増やす)
        "curves=preset=strong_contrast," # コントラストを強調し、色の破壊を促進
        # 新しい破壊フィルターの追加
        f"lenscorrection=k1={distortion_factor}:k2={distortion_factor}," # レンズディストーション
        f"chromakey=0x00FF00:0.1:0.0," # 特定の色を透過（予期せぬ部分が透過する）
        # f"vignette=angle=PI/4:d={random_vignette_darkness}," # <<<< この行を完全に削除
        f"edgedetect=mode=canny:low=0.1:high=0.4:intensity=5," # エッジ検出を強調
        f"mpdecimate=hi=64*60:lo=64*10:frac=0.3," # フレームを間引くことで時間的な破壊
        "setpts=PTS+random(0)*2/TB[glitch_feedback];" # setptsでランダムな遅延を付加 (遅延をさらに増やす)

        # ====== 映像ストリーム2: ノイズとカラーフォーマット破壊を組み合わせたレイヤー ======
        # 純粋なノイズと色空間変換による破壊
        f"color=c=black:s={input_width}x{input_height}:d=10," # 黒の背景
        f"format=yuv444p," # 高品質なYUV形式に変換（次に劣化させるため）
        f"noise={noise_strength}," # ノイズ強度
        f"format=rgb24," # RGBに変換（情報損失と色空間の破壊）
        f"format=yuv420p," # 再度YUVに戻す（さらなる情報損失）
        "geq=r='(r(X,Y)+random(0)*150)':g='(g(X,Y)+random(0)*150)':b='(b(X,Y)+random(0)*150)'," # カラーチャンネルをさらにランダムにシフト (強度アップ)
        f"lutrgb=r='clip(r+random(1)*{random_chroma_shift},0,255)':g='clip(g+random(1)*{random_chroma_shift},0,255)':b='clip(b+random(1)*{random_chroma_shift},0,255)'," # ランダムなRGBシフト
        f"crop={input_width/2}:{input_height/2}:{int(random.randint(0, int(input_width/4)))}:{int(random.randint(0, int(input_height/4)))},scale={input_width}:{input_height}:flags=neighbor," # ランダムな部分を切り取り拡大
        f"shufflepixels=direction=horizontal:width={random.randint(1,4)}:height={random.randint(1,4)}," # ランダムなピクセルシャッフル
        "setpts=PTS+random(0)*1.5/TB[noise_layer];" # ランダムな遅延 (遅延をさらに増やす)

        # ====== 映像ストリーム3: オーディオからの視覚グリッチフィードバック (実験的) ======
        # オーディオから得られる情報を視覚効果に変換する試み
        "[0:a]showvolume=f=0:s=0:o=v:c=0xFFAABBCC," # 音量を視覚化（目に見えないが内部で処理）
        f"format=yuv420p," # showvolumeの出力フォーマットを調整
        f"scale={input_width}:{input_height}," # サイズを合わせる
        "geq=g='st(1, gt(abs(st(0, (T*2*PI*0.5)+sin(T*3*PI*0.1))) , 0.5)*255)'," # サイン波ノイズを映像に重ねる (適当な数式)
        f"setpts=PTS+random(0)*2.0/TB[audio_glitch];" # ランダムな遅延 (さらに増やす)

        # ====== 最終ブレンド ======
        # 3つのグリッチ映像ストリームを重ねる
        "[original][glitch_feedback]blend=all_mode=difference:all_opacity=1.0[blend1];" # 差分ブレンド
        "[blend1][noise_layer]blend=all_mode=addition:all_opacity=1.0[blend2];" # 加算ブレンドでノイズを強調
        "[blend2][audio_glitch]blend=all_mode=grainmerge:all_opacity=1.0[v_out];" # さらにオーディオグリッチをマージ

        # ====== オーディオの破壊 ======
        # オーディオにもグリッチ効果を適用
        "[0:a]acrusher=level_in=8:level_out=4:bits=random(1)*8+1:mode=log:aa=1:samples=random(1)*500+1:mix=0.8," # ビットクラッシュとサンプルレート破壊
        "atempo=0.5," # テンポをランダムに変化
        "compand=attacks=0:decays=0:points=-80/-80|-15/-15|0/0:soft-knee=0," # コンパンディングで音声を歪ませる
        f"channelmap=channel_map=random(1)>0.5?FL-FL|FR-FR:FL-FR|FR-FL," # チャンネルをランダムに入れ替える
        "adelay=delays=100|200:all=1," # ランダムな遅延
        "afade=t=out:st=3:d=1," # 不規則なフェード
        "aselect='random(0)*0.8', asetpts=N/SR/TB[a]" # ランダムに一部をスキップ

    )

    # エンコード設定
    g_value = str(random.randint(int(input_fps * 5), int(input_fps * 20))) if input_fps > 0 else "150" # input_fpsが0の場合のFallback

    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-filter_complex", filter_complex,
        "-map", "[v_out]", # 最終的な映像ストリーム名を変更
        "-map", "[a]", # 最終的な音声ストリーム名を変更
        "-c:v", "libx264",
        "-preset", "ultrafast", # 最速プリセットで、エンコード品質を犠牲にしてグリッチを誘発
        "-crf", "51", # CRF値を最大に上げて、圧縮による破壊を最大化 (最大値51)
        "-profile:v", "baseline", # プロファイルを下げ、デコードを難しくする
        "-level", "3.0", # レベルを下げ、制限をかける
        "-g", g_value, # Iフレーム間隔を大きくし、Pフレームのエラー伝播を助長
        "-keyint_min", "1", # キーフレームの最小間隔 (あまり影響しないかも)
        "-sc_threshold", "0", # シーンチェンジ検出を無効に
        "-b:v", "10k", # 意図的に極端に低いビデオビットレートを設定し、データ不足による破損を誘発 (さらに下げる)
        "-slices", str(random.randint(1, 64)), # ランダムなスライス数でエンコード時のデータ破損を誘発 (さらに広く)
        f"-x264-params", 
        f"me=dia:subme=0:trellis=0:no-fast-pskip=1:no-dct-decimate=1:nr=10000:deadzone-inter={int(deadzone*100)}:deadzone-intra={int(deadzone*100)}:qcomp=0.0", # x264のエンコードパラメータを調整し、品質を落とす。deadzoneを追加
        "-c:a", "aac",
        "-b:a", "16k", # 音声ビットレートをさらに下げ、音声の劣化を最大化 (さらに下げる)
        "-pix_fmt", "yuv420p",
        output_path
    ]

    print("Running ffmpeg command:")
    print(" ".join(cmd))
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg command failed with exit code {e.returncode}. This might be an intended part of the extreme glitch process!")
        print(f"Command: {e.cmd}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print("Partial output file generated. It might still contain extreme glitches!")
        else:
            sys.exit("FFmpeg failed to produce any output file. The glitch settings might be too extreme for this input/FFmpeg version. Try slightly reducing random ranges or filter intensities.")

def main():
    # コマンドライン引数からURLを取得
    if len(sys.argv) > 1:
        video_url = sys.argv[1]
    else:
        # GitHub Actionsからの実行を想定しているため、引数がない場合はエラーで終了
        print("Usage: python scripts/apply_effects.py <NicoNicoDouga_Video_URL>")
        sys.exit("Error: No video URL provided as a command-line argument. This script is intended to be run via GitHub Actions workflow_dispatch.")

    # Generate a unique filename for the output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"glitch_{timestamp}"
    output_filename = f"videos/{base_filename}_output.mp4"

    # Download the video
    downloaded_file = download_video(video_url, base_filename)

    # Process the video
    process_video(downloaded_file, output_filename)
    print(f"Video processing complete. Output saved to: {output_filename}")

if __name__ == "__main__":
    main()
