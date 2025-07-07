import subprocess
import os
import sys
import shlex
from datetime import datetime

def download_videos(video_links, base_filename):
    """
    Download each video from the comma-separated video_links list using yt-dlp.
    Returns a list of downloaded filenames.
    """
    downloaded_files = []
    for idx, link in enumerate(video_links):
        link = link.strip()
        if not link:
            continue
        output_file = f"videos/input_{idx}_{base_filename}.mp4"
        cmd = f"yt-dlp -o {output_file} {shlex.quote(link)}"
        print(f"Downloading video {idx+1}: {link}")
        subprocess.run(cmd, shell=True, check=True)
        downloaded_files.append(output_file)
    return downloaded_files

def build_filter_complex(num_inputs):
    """
    Constructs a filter_complex chain that:
      - For each input video [i:v]:
          * Splits into two streams.
          * Applies inside feedback via tmix with maximum intensity.
          * Applies outside feedback via a setpts delay.
          * Blends both using addition.
          * Applies a stop-motion effect (frame dropping) and warm tone enhancement.
          * Result is labeled as [proc{i}].
      - If multiple processed videos exist, they are blended together using addition.
      - For audio, all [i:a] streams are mixed using amix.
    """
    filter_parts = []

    # Process each input video
    for i in range(num_inputs):
        # Split into two paths: one for inside feedback and one for delay (outside feedback)
        filter_parts.append(f"[{i}:v]split=2[v{i}a][v{i}b];")
        # Inside feedback: tmix with maximum intensity (heavy blending)
        filter_parts.append(f"[v{i}a]tmix=frames=10:weights='1 1 1 1 1 1 1 1 1 1'[v{i}ifb];")
        # Outside feedback: delay the video signal
        filter_parts.append(f"[v{i}b]setpts=PTS+1/TB[v{i}ofb];")
        # Blend the two feedbacks for a superimposed effect
        filter_parts.append(f"[v{i}ifb][v{i}ofb]blend=all_mode=addition[v{i}blend];")
        # Apply stop-motion effect (drop half the frames) and add warmth via eq filter
        # Warm effect: slight brightness up, contrast and saturation increased
        filter_parts.append(
            f"[v{i}blend]select='not(mod(n,2))',setpts=N/FRAME_RATE/TB,eq=brightness=0.05:contrast=1.5:saturation=1.5[proc{i}];"
        )

    # Combine all processed videos if more than one exists
    if num_inputs == 0:
        sys.exit("No input videos were downloaded. Exiting.")
    elif num_inputs == 1:
        final_video = "[proc0]"
    else:
        # Start blending from the first processed video
        final_label = "[proc0]"
        for i in range(1, num_inputs):
            new_label = f"[proc_comb{i}]"
            # Blend accumulative result with the next processed video using addition
            filter_parts.append(f"{final_label}[proc{i}]blend=all_mode=addition{new_label};")
            final_label = new_label
        final_video = final_label

    # Construct audio mixing part: mix all audio streams from inputs
    # If an input might not have audio, this can fail; assume they do.
    audio_inputs = "".join(f"[{i}:a]" for i in range(num_inputs))
    filter_parts.append(f"{audio_inputs}amix=inputs={num_inputs}[aout]")

    # Concatenate the filter_complex parts
    filter_complex = "".join(filter_parts)
    return filter_complex, final_video

def process_video(input_files, output_path):
    num_inputs = len(input_files)
    filter_complex, final_video = build_filter_complex(num_inputs)

    print("Using filter_complex:")
    print(filter_complex)

    cmd = ["ffmpeg", "-y"]
    # Add all input files
    for file in input_files:
        cmd.extend(["-i", file])
    # Add the filter_complex chain
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", final_video,
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-c:a", "aac",
        output_path
    ])

    print("Running ffmpeg command:")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)

def main():
    # Expect environment variable VIDEO_LINKS as comma separated URLs
    video_links_env = os.environ.get("VIDEO_LINKS", "")
    if not video_links_env:
        sys.exit("Error: VIDEO_LINKS environment variable must be set with comma-separated video URLs")
    
    # Get a base filename based on current datetime
    now = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    video_links = video_links_env.split(",")
    # Create videos directory if it doesn't exist
    os.makedirs("videos", exist_ok=True)
    
    # Download all videos and get local file names
    downloaded_files = download_videos(video_links, now)
    
    # Define output file name, e.g., processed_{datetime}.mp4
    output_file = f"videos/processed_{now}.mp4"
    
    process_video(downloaded_files, output_file)
    
    print(f"Processing complete. Output video: {output_file}")
    # Optionally, cleanup input videos if desired:
    # for f in downloaded_files:
    #     os.remove(f)

if __name__ == "__main__":
    main()
