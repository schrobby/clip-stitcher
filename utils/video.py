"""
Video processing utilities using ffmpeg.
Handles video downloading, processing, and concatenation.
"""

import subprocess
import tempfile
from pathlib import Path
from utils.ui import print_error, print_info

def download_video_segment(video_id, timestamp, output_path, duration=30):
    """
    Download a video segment using yt-dlp.
    
    Args:
        video_id (str): YouTube video ID
        timestamp (int): Start timestamp in seconds
        output_path (str): Path to save the downloaded video
        duration (int): Duration of the segment to download
        
    Returns:
        bool: True if successful, False otherwise
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = [
        "yt-dlp",
        "--format", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "--external-downloader", "ffmpeg",
        "--external-downloader-args", f"ffmpeg_i:-ss {timestamp} -t {duration}",
        "--output", output_path,
        url
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Error downloading video segment: {e}")
        return False

def concatenate_videos(video_files, output_path):
    """
    Concatenate multiple video files into one using ffmpeg.
    
    Args:
        video_files (list): List of video file paths to concatenate
        output_path (str): Path for the output video file
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Create a temporary file list for ffmpeg
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for video_file in video_files:
            f.write(f"file '{video_file}'\n")
        file_list_path = f.name

    # First, try hardware acceleration
    cmd_hw = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", file_list_path,
        "-c:v", "h264_nvenc", "-preset", "fast",
        "-c:a", "copy",
        output_path
    ]

    cmd_sw = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", file_list_path,
        "-c:v", "libx264", "-preset", "ultrafast",
        "-c:a", "copy",
        output_path
    ]

    try:
        # Try hardware acceleration first
        try:
            subprocess.run(cmd_hw, check=True, capture_output=True)
            print_info("✨ Hardware acceleration successful!")
        except subprocess.CalledProcessError:
            # Fallback to software encoding
            print_info("🔄 Hardware acceleration not available, using software encoding...")
            subprocess.run(cmd_sw, check=True, capture_output=True)
        
        # Clean up temporary file list
        Path(file_list_path).unlink()
        return True
        
    except subprocess.CalledProcessError as e:
        print_error(f"Error concatenating videos: {e}")
        Path(file_list_path).unlink()  # Clean up even on error
        return False
