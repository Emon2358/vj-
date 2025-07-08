import subprocess
import os
import sys
import shlex
from datetime import datetime

def download_video(url, base_filename):
    """
    Download video from the provided URL using yt-dlp.
    """
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
    Apply extreme glitch effects including:
    - Analog-style distortions
    - Kaleidoscope effect
    - Heavy feedback effects
    - Color glitches
    - Random noise and interference
    - VHS-style tracking errors
    """
    filter_complex = (
        # Split input into multiple streams for different effects
        "[0:v]split=8[in1][in2][in3][in4][in5][in6][in7][in8];"
        
        # Heavy feedback with random color shifts
        "[in1]tmix=frames=60:weights='1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1',"
        "colorbalance=rs=.3:gs=-.3:bs=.3:rm=.1:gm=-.1:bm=.1:rh=.1:gh=-.1:bh=.1[fb1];"
        
        # VHS tracking errors and noise
        "[in2]noise=alls=20:allf=t,"
        "rgbashift=rh=-2:bv=2,"
        "curves=r='0/0 0.5/0.4 1/1':g='0/0 0.5/0.6 1/1':b='0/0 0.5/0.5 1/1'[vhs];"
        
        # Kaleidoscope effect (randomly applied)
        "[in3]split[k1][k2];"
        "[k1]rotate=PI/3:ow=rotw(PI/3):oh=roth(PI/3)[r1];"
        "[k2]rotate=-PI/3:ow=rotw(PI/3):oh=roth(PI/3)[r2];"
        "[r1][r2]blend=all_mode=screen[kalei];"
        
        # Extreme color glitches and wave distortions
        "[in4]hue=h=2*PI*t:s=sin(t)+2,"
        "waves=period=20:amplitude=20[wave];"
        
        # Random signal interference
        "[in5]format=rgb24,datascope=mode=color2,"
        "rotate=PI/6:ow=rotw(PI/6):oh=roth(PI/6)[interf];"
        
        # Heavy chromatic aberration
        "[in6]split=3[r][g][b];"
        "[r]lutrgb=r=val:g=0:b=0,crop=iw/1.01:ih/1.01:0:0[r1];"
        "[g]lutrgb=r=0:g=val:b=0[g1];"
        "[b]lutrgb=r=0:g=0:b=val,crop=iw/1.02:ih/1.02:0:0[b1];"
        "[g1][r1]overlay=0:0[g1r1];"
        "[g1r1][b1]overlay=0:0[chroma];"
        
        # Random scanlines and flickering
        "[in7]geq='lum=128+(128-lum(X,Y))*sin(t*10):cb=128:cr=128',"
        "curves=all='0/0 0.5/0.8 1/1'[scan];"
        
        # Time displacement glitch
        "[in8]select='if(lt(random(0), 0.2), 1, 0)',setpts=N/FRAME_RATE/TB[glitch];"
        
        # Combine all effects
        "[fb1][vhs]blend=all_mode=overlay[tmp1];"
        "[tmp1][kalei]blend=all_mode=screen:shortest=1[tmp2];"
        "[tmp2][wave]blend=all_mode=lighten[tmp3];"
        "[tmp3][interf]blend=all_mode=addition[tmp4];"
        "[tmp4][chroma]blend=all_mode=screen[tmp5];"
        "[tmp5][scan]blend=all_mode=overlay[tmp6];"
        "[tmp6][glitch]blend=all_mode=addition[final_video];"
        
        # Create heavily distorted audio
        "[0:a]aecho=0.8:0.88:60:0.4,"
        "flanger=delay=20:depth=2,"
        "vibrato=f=7:d=0.5,"
        "aphaser=type=t:speed=2:decay=0.6[final_audio]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-filter_complex", filter_complex,
        "-map", "[final_video]",
        "-map", "[final_audio]",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        output_path
    ]

    print("Running ffmpeg command:")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)

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

if __name__ == "__main__":
    main()
