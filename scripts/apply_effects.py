import subprocess
import random

# 定義: 各エフェクトのフィルター文字列
EFFECTS = {
    'inside_feedback': 'tblend=all_mode=addition',
    'outside_feedback': 'tblend=all_mode=difference',
    'chromakey': 'chromakey=0x00FF00:0.3:0.2',
    'superimpose': '[0:v][0:v]overlay=10:10',
    'stop_motion': 'select=not(mod(n\\,5)),setpts=N/FRAME_RATE/TB',
    'telop': "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='%{filename}':x=(w-text_w)/2:y=h-50:fontsize=24:fontcolor=white"
}

# ランダムにパラメータを調整 (例)
def randomize_filter(filter_str):
    # 必要に応じてパラメータを変化させる
    return filter_str

# 全てのエフェクトを同時に適用するフィルターコンプレックスを構築
filters = []
for name, f in EFFECTS.items():
    filters.append(randomize_filter(f))

filter_complex = ';'.join(filters)

cmd = [
    'ffmpeg', '-y', '-i', subprocess.os.environ['VIDEO_IN'],
    '-filter_complex', filter_complex,
    '-an', subprocess.os.environ['VIDEO_OUT']
]

print('Running:', ' '.join(cmd))
subprocess.run(cmd, check=True)
