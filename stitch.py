import os
import subprocess
import time
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


def download_clip(url, start_time, output_path):
    end_time = seconds_to_hhmmss(
        sum(int(x) * 60**i for i, x in enumerate(reversed(start_time.split(":"))))
        + DURATION_SECONDS
    )
    section = f"*{start_time}-{end_time}"

    cmd = [
        "yt-dlp",
        "--quiet",
        "--no-warnings",
        "--download-sections",
        section,
        "-f",
        "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
        "-o",
        normalize(output_path),
        url,
    ]
    subprocess.run(cmd, check=True, shell=IS_WINDOWS)


def download_clip_retry(index, url, start_time):
    temp_path = normalize(os.path.join(OUTPUT_DIR, f"raw_{index}.mp4"))
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            download_clip(url, start_time, temp_path)
            return temp_path
        except subprocess.CalledProcessError:
            print(f"[{index}] Retry {attempt}/{RETRY_COUNT} failed for {url}")
            time.sleep(2)
    raise RuntimeError(f"[{index}] Failed after {RETRY_COUNT} retries: {url}")


def convert_to_safe_mp4(index, input_path):
    safe_path = normalize(os.path.join(OUTPUT_DIR, f"clip_{index}.mp4"))
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        normalize(input_path),
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        safe_path,
    ]
    subprocess.run(cmd, check=True, shell=IS_WINDOWS)
    return safe_path


def main():
    with open(INPUT_LINKS_FILE, "r") as f:
        raw_links = [line.strip() for line in f if line.strip()]

    links = [parse_link(link) for link in raw_links]

    downloaded = []

    print("📥 Downloading clips in parallel...")
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_DOWNLOADS) as executor:
        futures = [
            executor.submit(download_clip_retry, i, url, timestamp)
            for i, (url, timestamp) in enumerate(links)
        ]
        for future in tqdm(as_completed(futures), total=len(futures)):
            downloaded.append(future.result())

    print("🎞️ Re-encoding all clips...")
    safe_clips = []
    for i, path in tqdm(enumerate(downloaded), total=len(downloaded)):
        safe_clips.append(convert_to_safe_mp4(i, path))

    print("🔗 Concatenating...")
    with open("inputs.txt", "w", encoding="utf-8") as f:
        for path in safe_clips:
            abs_path = normalize(os.path.abspath(path)).replace("\\", "/")
            f.write(f"file '{abs_path}'\n")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            "inputs.txt",
            "-c",
            "copy",
            FINAL_OUTPUT,
        ],
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
