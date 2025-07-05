# scripts/apply_effects.py
import subprocess
import os

input_path = os.environ['VIDEO_IN']
output_path = os.environ['VIDEO_OUT']
filename = os.path.splitext(os.path.basename(input_path))[0]

# 1入力で直列に全エフェクトを通す
filter_complex = (
    f"[0:v] "
    f"chromakey=0x00FF00:0.3:0.2, "
    f"format=yuva420p, "
    f"overlay=10:10, "
    f"select='not(mod(n\\,5))', "
    f"setpts='N/FRAME_RATE/TB', "
    f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
    f"text='{filename}':x=(w-text_w)/2:y=h-50:fontsize=24:fontcolor=white"
    f" [out]"
)

cmd = [
    "ffmpeg", "-y",
    "-i", input_path,
    "-filter_complex", filter_complex,
    "-map", "[out]",
    "-an", output_path
]

print("Running:", " ".join(cmd))
subprocess.run(cmd, check=True)
