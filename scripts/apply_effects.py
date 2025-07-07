import subprocess
import os

def process_video(input_path, output_path):
    # Build a filter chain that applies:
    # 1. Split the video into four copies:
    #    - [v1]: For inside feedback via tmix.
    #    - [v2]: For outside feedback (delayed version via setpts).
    #    - [v3]: For stop-motion effect (frame dropping via select).
    #    - [tele0]: For a scaled down overlay ("teletext" style).
    # 2. Process [v1] with tmix for inside feedback.
    # 3. Process [v2] with setpts to produce a slight delay (outside feedback).
    # 4. Overlay the results of (2) and (3) as the superimposition.
    # 5. Process [v3] with a select filter to simulate stop-motion, then blend it.
    # 6. Scale [tele0] down and overlay it in the bottom right.
    # 7. For audio, delay one copy and mix it with the original.
    filter_complex = (
        "[0:v]split=4[v1][v2][v3][tele0];"
        "[v1]tmix=frames=5:weights='1 1 1 1 1'[ifb];"
        "[v2]setpts=PTS+0.5/TB[ofb];"
        "[ifb][ofb]overlay=10:10[sup];"
        "[v3]select='not(mod(n,2))',setpts=N/FRAME_RATE/TB[stop];"
        "[sup][stop]blend=all_mode=addition[glitched];"
        "[tele0]scale=iw/4:ih/4[tele];"
        "[glitched][tele]overlay=W-w-10:H-h-10[final];"
        "[0:a]adelay=500|500[a_delay];"
        "[0:a][a_delay]amix=inputs=2[aout]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-filter_complex", filter_complex,
        "-map", "[final]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        output_path
    ]
    
    print("Running command:", " ".join(cmd))
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    input_path = os.environ.get("VIDEO_IN")
    output_path = os.environ.get("VIDEO_OUT")
    
    if not input_path or not output_path:
        raise ValueError("VIDEO_IN and VIDEO_OUT environment variables must be set")
    
    process_video(input_path, output_path)
