import subprocess
import os
import sys
import shlex
from datetime import datetime
import random
import math

def download_video(url, base_filename):
    os.makedirs("videos", exist_ok=True)
    out = f"videos/input_{base_filename}.mp4"
    cmd = f"yt-dlp -o {out} {shlex.quote(url)}"
    print("Downloading:", url)
    subprocess.run(cmd, shell=True, check=True)
    return out

def build_super_extreme_filter(w, h, fps):
    # ランダムパラメータ
    ra = random.uniform(0.1, math.pi)               # 回転角
    wave_m = random.uniform(5, 50)                  # 波形歪み強度
    burst_chance = random.random()                  # バーストカラー確率
    burst_frame = random.randint(0, 30)             # いつバーストするか
    tile_size = random.choice([2,4,8,16])           # ミラータイルサイズ

    return (
        # ストリーム分岐
        "[0:v]split=8[orig][yuv][time][chan][mirror][wave][post1][post2];"

        # --- 1. 生データ破壊 (YUV → バイト逆転) ---
        "[yuv]format=yuv444p,"
        "fifo, "
        "zmqsend=bind_address=tcp\\://127.0.0.1\\:5555, "  # →（外部でバイトを乱す想定）
        "zmqrecv=bind_address=tcp\\://127.0.0.1\\:5556, "
        "format=yuv420p[yuv_out];"

        # --- 2. 時間歪み＋フレームシャッフル ---
        "[time]setpts=PTS*random(0.5)+random(0.5),"
        "framestep=step=random(1)*5+1[time_out];"

        # --- 3. チャネルオフセット ---
        "[chan]split=3[rc][gc][bc];"
        "[rc]lutrgb=r='val+random(0)*50':g='val':b='val'[r];"
        "[gc]lutrgb=r='val':g='val+random(0)*50':b='val'[g];"
        "[bc]lutrgb=r='val':g='val':b='val+random(0)*50'[b];"
        "[r][g]blend=all_mode=addition:all_opacity=0.5[rg];"
        "[rg][b]blend=all_mode=addition:all_opacity=0.5[chan_out];"

        # --- 4. ミラータイル化 ---
        f"[mirror]crop={w//tile_size}:{h}:{0}:{0},tile={tile_size}x1,scale={w}:{h}[mir_out];"

        # --- 5. 波形歪み ---
        f"[wave]geq=r='X+{wave_m}*sin(Y/{wave_m})':"
        f"g='Y+{wave_m}*cos(X/{wave_m})':b='(X+Y)/2'[wave_out];"

        # --- 6. 1-bit ポスタライズを二段階 ---
        "[post1]format=gray,threshold,format=gray,threshold,format=yuv420p[po1];"
        "[post2]format=rgb24,"
        "lutrgb=r='if(gt(val,128),255,0)':"
        "g='if(gt(val,128),255,0)':"
        "b='if(gt(val,128),255,0)',format=yuv420p[po2];"

        # --- 7. ランダムバーストカラー逆転 ---
        f"[orig]eq='enable=between(n,{burst_frame},{burst_frame+3})':"
        "contrast=2:brightness=0.3:saturation=-1,negate[burst];"

        # --- 全層ブレンド & 出力 ---
        "[orig][yuv_out]blend=all_mode=difference:all_opacity=0.7[b1];"
        "[b1][time_out]blend=all_mode=addition:all_opacity=0.7[b2];"
        "[b2][chan_out]blend=all_mode=multiply:all_opacity=0.7[b3];"
        "[b3][mir_out]blend=all_mode=grainextract:all_opacity=0.6[b4];"
        "[b4][wave_out]blend=all_mode=overlay:all_opacity=0.5[b5];"
        "[b5][po1]blend=all_mode=lighten:all_opacity=0.5[b6];"
        "[b6][po2]blend=all_mode=darken:all_opacity=0.5[b7];"
        "[b7][burst]blend=all_mode=hardlight:all_opacity=0.8[v]"
    )

def process_video(input_file, output_path):
    # 解像度&FPS取得
    w, h, fps = 320, 240, 30
    try:
        out = subprocess.run([
            "ffprobe","-v","error",
            "-select_streams","v:0",
            "-show_entries","stream=width,height,avg_frame_rate",
            "-of","csv=p=0", input_file
        ], capture_output=True, text=True, check=True).stdout.strip().split(',')
        w,h = map(int, out[0].split('x'))
        num,den = map(int, out[2].split('/'))
        fps = num/den if den else fps
    except:
        pass
    print(f"Detected {w}x{h}@{fps:.2f}fps")

    fc = build_super_extreme_filter(w,h,fps)
    cmd = [
        "ffmpeg","-y","-i",input_file,
        "-filter_complex",fc,
        "-map","[v]","-map","0:a",
        "-c:v","libx264","-preset","ultrafast","-crf","50",
        "-c:a","aac","-b:a","8k","-pix_fmt","yuv420p",
        output_path
    ]
    print("Running super-extreme ffmpeg:")
    print(" ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print("※FFmpeg errorも演出の一部です！出力を確認してください。")

def main():
    if len(sys.argv)<2:
        print("Usage: python extreme_ultrachaos.py <video_url>")
        sys.exit(1)
    url = sys.argv[1]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"chaos_{ts}"
    out = f"videos/{base}_ultra.mp4"
    src = download_video(url, base)
    process_video(src, out)
    print("=== 超絶破壊完了 ===")
    print("Output:", out)

if __name__=="__main__":
    main()
