import subprocess, os, sys, shlex, random, math
from datetime import datetime

def download_video(url, base):
    os.makedirs("videos", exist_ok=True)
    out = f"videos/input_{base}.mp4"
    subprocess.run(f"yt-dlp -o {out} {shlex.quote(url)}", shell=True, check=True)
    return out

def build_super_extreme_filter(w, h, fps):
    # ランダムパラメータ
    ra    = random.uniform(0.2, math.pi)     # 回転
    wave  = random.uniform(10, 80)           # 波形歪み
    tile  = random.choice([2,4,8,16])        # タイルサイズ
    burst = random.randint(0, int(fps))      # バースト発生フレーム

    return (
        "[0:v]split=8[orig][bs][time][chan][mir][wav][postA][postB];"

        # ビットストリーム可視化＆歪み
        "[bs]codecview=mv=pf+bf+bb,"
        "split=2[bs1][bs2];"
        "[bs1]negate[bs_n];"
        "[bs2]curves=preset=invert[bs_c];"
        "[bs_n][bs_c]blend=all_mode=difference:all_opacity=0.8[bit_crush];"

        # 時間歪み＋フレームステップ
        "[time]setpts='(PTS-STARTPTS)*(0.5+random(0))',"
        "framestep=step='1+floor(random(1)*5)'[time_crush];"

        # RGB チャネル独立ノイズ
        "[chan]split=3[r][g][b];"
        "[r]lutrgb=r='val+random(1)*60':g='val':b='val'[R];"
        "[g]lutrgb=r='val':g='val+random(1)*60':b='val'[G];"
        "[b]lutrgb=r='val':g='val':b='val+random(1)*60'[B];"
        "[R][G]blend=addition:all_opacity=0.5[RG];"
        "[RG][B]blend=addition:all_opacity=0.5[chan_crush];"

        # ミラータイル化
        f"[mir]crop={w//tile}:{h}:0:0,tile={tile}x1,scale={w}:{h}[mir_crush];"

        # 波形ジッター
        f"[wav]geq=r='X+{wave}*sin(Y/{wave})':"
        f"g='Y+{wave}*cos(X/{wave})':b='(X+Y)/2'[wav_crush];"

        # ポスタライズ 1-bit ×2 段階
        "[postA]format=gray,threshold=128,threshold=64,format=yuv420p[postA_crush];"
        "[postB]format=rgb24,"
        "lutrgb=r='if(gt(val,64),255,0)':"
        "g='if(gt(val,64),255,0)':"
        "b='if(gt(val,64),255,0)',format=yuv420p[postB_crush];"

        # 短時間バースト反転
        f"[orig]eq='enable=between(n,{burst},{burst+2})':"
        "contrast=3:brightness=0.2:saturation=-2,negate[burst_crush];"

        # tblend + cellauto (セルオートマトン風)
        "[orig][orig]tblend=all_mode=lighten:all_opacity=0.5[t_bl];"
        "[t_bl]cellauto=strength=1.0:mode=invert[cell_crush];"

        # 最終ブレンド（全10レイヤーを複合）
        "[orig][bit_crush]blend=difference:all_opacity=0.6[b1];"
        "[b1][time_crush]blend=addition:all_opacity=0.6[b2];"
        "[b2][chan_crush]blend=multiply:all_opacity=0.6[b3];"
        "[b3][mir_crush]blend=grainextract:all_opacity=0.6[b4];"
        "[b4][wav_crush]blend=overlay:all_opacity=0.5[b5];"
        "[b5][postA_crush]blend=darken:all_opacity=0.5[b6];"
        "[b6][postB_crush]blend=lighten:all_opacity=0.5[b7];"
        "[b7][burst_crush]blend=hardlight:all_opacity=0.8[b8];"
        "[b8][cell_crush]blend=addition:all_opacity=0.5[v]"
    )

def process_video(src, dst):
    # 解像度・FPS 検出
    w,h,fps = 320,240,30
    try:
        out = subprocess.run([
            "ffprobe","-v","error","-select_streams","v:0",
            "-show_entries","stream=width,height,avg_frame_rate",
            "-of","csv=p=0", src
        ], capture_output=True, text=True, check=True).stdout.split(',')
        w,h = map(int, out[0].split('x'))
        num,den = map(int, out[2].split('/'))
        fps = num/den if den else fps
    except:
        pass

    fc = build_super_extreme_filter(w,h,fps)
    cmd = [
        "ffmpeg","-y","-i",src,
        "-filter_complex",fc,
        "-map","[v]","-map","0:a",
        "-c:v","libx264","-preset","ultrafast","-crf","50",
        "-c:a","aac","-b:a","8k","-pix_fmt","yuv420p", dst
    ]
    print("Running super-extreme ffmpeg:")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)

def main():
    if len(sys.argv)<2:
        print("Usage: python ultra_chaos.py <video_url>"); sys.exit(1)
    url = sys.argv[1]
    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    base= f"chaos2_{ts}"
    out = f"videos/{base}_ultra.mp4"
    src = download_video(url, base)
    process_video(src, out)
    print("=== 超絶破壊完了 ===\nOutput:", out)

if __name__=="__main__":
    main()
