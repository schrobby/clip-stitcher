import os
import subprocess
from urllib.parse import urlparse, parse_qs
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import shutil
import platform

# === SETTINGS ===
INPUT_LINKS_FILE = "input.txt"
OUTPUT_DIR = "clips"
FINAL_OUTPUT = "final_output.mp4"
DURATION_SECONDS = 30
MAX_PARALLEL_DOWNLOADS = 4
RETRY_COUNT = 3
IS_WINDOWS = platform.system() == "Windows"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def normalize(path):
    return os.path.normpath(path)


def seconds_to_hhmmss(seconds):
    return str(timedelta(seconds=int(seconds))).zfill(8)


def parse_link(link):
    link = link.strip()
    parsed = urlparse(link)
    query = parse_qs(parsed.query)

    # Get video ID
    if "youtube.com" in parsed.netloc:
        video_id = query.get("v", [None])[0]
    elif "youtu.be" in parsed.netloc:
        video_id = parsed.path.lstrip("/")
    else:
        raise ValueError(f"Unsupported YouTube domain: {link}")

    if not video_id:
        raise ValueError(f"Could not extract video ID from: {link}")

    # Get timestamp
    timestamp_sec = None
    if "t" in query:
        timestamp_sec = int(query["t"][0])
    elif parsed.fragment.startswith("t="):  # e.g., #t=123
        timestamp_sec = int(parsed.fragment.split("=")[-1])
    else:
        raise ValueError(f"No timestamp found in: {link}")

    timestamp_hhmmss = seconds_to_hhmmss(timestamp_sec)
    full_url = f"https://www.youtube.com/watch?v={video_id}"
    return full_url, timestamp_hhmmss


def download_full_video(video_id, output_path):
    if os.path.exists(output_path):
        return  # Skip if already downloaded
    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = [
        "yt-dlp",
        "--quiet",
        "--no-warnings",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
        "-o", output_path,
        url
    ]
    subprocess.run(cmd, check=True, shell=IS_WINDOWS)

def cut_segment(index, input_path, start_time_hhmmss):
    output_path = normalize(os.path.join(OUTPUT_DIR, f"clip_{index}.mp4"))
    
    # Check if input has audio stream
    probe_cmd = [
        "ffprobe", "-v", "quiet", "-select_streams", "a", 
        "-show_entries", "stream=index", "-of", "csv=p=0", input_path
    ]
    result = subprocess.run(probe_cmd, capture_output=True, text=True, shell=IS_WINDOWS)
    has_audio = bool(result.stdout.strip())
    
    cmd = [
        "ffmpeg", "-y",
        "-ss", start_time_hhmmss,
        "-i", input_path,
        "-t", str(DURATION_SECONDS),
        "-c:v", "libx264", "-preset", "ultrafast",
        "-map", "0:v:0",
        "-movflags", "+faststart"
    ]
    
    # Only add audio options if audio stream exists
    if has_audio:
        cmd.extend(["-c:a", "aac", "-b:a", "128k", "-map", "0:a:0"])
    
    cmd.append(output_path)
    subprocess.run(cmd, check=True, shell=IS_WINDOWS)
    return output_path

def process_clip(index, video_id, timestamp_hhmmss):
    full_video_path = normalize(os.path.join(OUTPUT_DIR, f"full_{video_id}.mp4"))
    download_full_video(video_id, full_video_path)
    return cut_segment(index, full_video_path, timestamp_hhmmss)



def convert_to_safe_mp4(index, input_path):
    safe_path = normalize(os.path.join(OUTPUT_DIR, f"clip_{index}.mp4"))
    
    # Check if input has audio stream
    probe_cmd = [
        "ffprobe", "-v", "quiet", "-select_streams", "a", 
        "-show_entries", "stream=index", "-of", "csv=p=0", normalize(input_path)
    ]
    result = subprocess.run(probe_cmd, capture_output=True, text=True, shell=IS_WINDOWS)
    has_audio = bool(result.stdout.strip())
    
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        normalize(input_path),
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-map", "0:v:0",
        "-movflags",
        "+faststart"
    ]
    
    # Only add audio options if audio stream exists
    if has_audio:
        cmd.extend(["-c:a", "aac", "-b:a", "128k", "-map", "0:a:0"])
    
    cmd.append(safe_path)
    subprocess.run(cmd, check=True, shell=IS_WINDOWS)
    return safe_path


def main():
    with open(INPUT_LINKS_FILE, "r") as f:
        raw_links = [line.strip() for line in f if line.strip()]

    links = [parse_link(link) for link in raw_links]

    safe_clips = []

    print("📥 Downloading full videos and cutting clips...")
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_DOWNLOADS) as executor:
        futures = [
            executor.submit(process_clip, i, video_id, timestamp)
            for i, (url, timestamp) in enumerate(links)
            for video_id in [url.split("v=")[-1]]
        ]
        for future in tqdm(as_completed(futures), total=len(futures)):
            safe_clips.append(future.result())


    print("🔗 Concatenating...")
    with open("inputs.txt", "w", encoding="utf-8") as f:
        for path in safe_clips:
            abs_path = normalize(os.path.abspath(path)).replace("\\", "/")
            f.write(f"file '{abs_path}'\n")

    # Check if any of the clips have audio
    has_audio_clips = False
    for clip_path in safe_clips:
        probe_cmd = [
            "ffprobe", "-v", "quiet", "-select_streams", "a", 
            "-show_entries", "stream=index", "-of", "csv=p=0", clip_path
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True, shell=IS_WINDOWS)
        if result.stdout.strip():
            has_audio_clips = True
            break

    concat_cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        "inputs.txt",
        "-c:v",
        "copy"
    ]
    
    # Only add audio codec if clips have audio
    if has_audio_clips:
        concat_cmd.extend(["-c:a", "aac", "-b:a", "128k"])
    
    concat_cmd.append(FINAL_OUTPUT)

    subprocess.run(
        concat_cmd,
        check=True,
        shell=IS_WINDOWS,
    )

    print(f"✅ Done. Final video created: {FINAL_OUTPUT}")

    print("🧹 Cleaning up temporary files...")
    shutil.rmtree(OUTPUT_DIR)
    if os.path.exists("inputs.txt"):
        os.remove("inputs.txt")

    print("🏁 Finished cleanly.")


if __name__ == "__main__":
    main()