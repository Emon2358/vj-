import subprocess
import os
import random

def create_filter_complex():
    # 利用可能なエフェクトのリスト
    effects = [
        # 色反転
        "negate",
        # カラーチャンネルの入れ替え
        "colorchannelmixer=rr=0:rg=1:rb=0:gr=1:gg=0:gb=0:br=0:bg=0:bb=1",
        # グリッチ的なブレンドモード
        "colorbalance=rs=0.5:gs=0.5:bs=0.5:rm=0.5:gm=0.5:bm=0.5:rh=0.5:gh=0.5:bh=0.5",
        # ピクセルのソート
        "shufflepixels=2:10:100",
        # 時間遅延エフェクト
        "setpts=0.5*PTS",
        # 色相回転
        "hue=h=t*90:s=cos(t*0.5)",
        # ノイズ付加
        "noise=alls=20:allf=t",
        # クロマキー的なエフェクト
        "colorkey=0x00FF00:0.3:0.2",
        # ピクセル化
        "pixelize=50:50",
        # 波形歪み
        "wave=0.1:10:10",
        # スライス効果
        "vignette=PI/4",
        # カラーシフト
        "colorshift=rh=0.5:bv=0.5",
        # フレーム間引き
        "select='not(mod(n,2))',setpts=N/FRAME_RATE/TB"
    ]
    
    # ランダムにエフェクトを3-5個選択
    selected_effects = random.sample(effects, random.randint(3, 5))
    
    # エフェクトを組み合わせる
    return ','.join(selected_effects)

def process_video(input_path, output_path):
    filter_complex = create_filter_complex()
    
    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-filter_complex', f"[0:v] {filter_complex} [out]",
        '-map', '[out]',
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-an',  # 音声を除去
        output_path
    ]
    
    print("Applying effects:", filter_complex)
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    input_path = os.environ['VIDEO_IN']
    output_path = os.environ['VIDEO_OUT']
    process_video(input_path, output_path)
