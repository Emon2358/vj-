import subprocess
import os

# 各エフェクトを順に適用し、最終ストリームを[out]としてマッピング
filter_complex = (
    # インサイド・フィードバック（自己ブレンド）
    '[0:v][0:v]tblend=all_mode=addition[fb1];'
    # アウトサイド・フィードバック（二重ブレンド）
    '[fb1][fb1]tblend=all_mode=difference[fb2];'
    # クロマキー
    '[fb2]chromakey=0x00FF00:0.3:0.2[ck];'
    # スーパーインポーズ（微小オフセット）
    '[ck][ck]overlay=10:10[ov];'
    # コマ撮り（フレーム間セレクト）
    '[ov]select=not(mod(n\,5)),setpts=N/FRAME_RATE/TB[sm];'
    # テロップ表示
    "[sm]drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='${{FILENAME}}':x=(w-text_w)/2:y=h-50:fontsize=24:fontcolor=white[out]"
)

cmd = [
    'ffmpeg', '-y',
    '-i', os.environ['VIDEO_IN'],
    '-filter_complex', filter_complex,
    '-map', '[out]',
    '-an', os.environ['VIDEO_OUT']
]
print('Running:', ' '.join(cmd))
subprocess.run(cmd, shell=False, check=True)
