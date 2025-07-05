import subprocess
import os

# 入力ファイル名取得（テロップ用）
input_path = os.environ['VIDEO_IN']
filename = os.path.splitext(os.path.basename(input_path))[0]
output_path = os.environ['VIDEO_OUT']

# filter_complex の構築: 各ステップを適切にチェイン
filter_complex = (
    # インサイド・フィードバック: input twice -> fb1
    f"[0:v][0:v]tblend=all_mode=addition[fb1];"
    # アウトサイド・フィードバック: original + fb1 -> fb2
    f"[fb1][0:v]tblend=all_mode=difference[fb2];"
    # クロマキー: remove green
    f"[fb2]chromakey=0x00FF00:0.3:0.2,format=yuva420p[ck];"
    # スーパーインポーズ: overlay original onto ck
    f"[ck][0:v]overlay=10:10[ov];"
    # コマ撮り: 1フレームおきで表示
    f"[ov]select='not(mod(n,5))',setpts='N/FRAME_RATE/TB'[sm];"
    # テロップ: 動画名を表示
    f"[sm]drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='{filename}':"
    f"x=(w-text_w)/2:y=h-50:fontsize=24:fontcolor=white[out]"
)

cmd = [
    'ffmpeg', '-y',
    '-i', input_path,
    '-filter_complex', filter_complex,
    '-map', '[out]',
    '-an', output_path
]

print('Running:', ' '.join(cmd))
subprocess.run(cmd, check=True)
