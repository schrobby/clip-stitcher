"""
Video processing utilities for the YouTube Clip Stitcher.
Handles video downloading, extraction, and processing.
"""

import os
import subprocess
from pathlib import Path
from .ui import print_success, print_error, print_warning, print_info


def process_video_clip(video_id, start_time, clip_duration, clip_path, temp_dir, clip_num, total_clips):
    """
    Process a single video clip: download, extract, and prepare for stitching.
    
    Args:
        video_id (str): YouTube video ID
        start_time (int): Start timestamp in seconds
        clip_duration (int): Duration of clip in seconds
        clip_path (str): Output path for the processed clip
        temp_dir (str): Temporary directory for processing
        clip_num (int): Current clip number
        total_clips (int): Total number of clips
        
    Returns:
        bool: True if successful, False otherwise
    """
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    temp_video_path = os.path.join(temp_dir, f"{video_id}_full.%(ext)s")
    
    print(f"\n📥 Downloading clip {clip_num}/{total_clips}: {video_id}")
    
    # Download the full video first with high quality settings
    cmd = [
        'yt-dlp',
        '-f', 'bestvideo[height<=1080]+bestaudio/bestvideo[height<=720]+bestaudio/best[height<=1080]/best[height<=720]/best',
        '--merge-output-format', 'mp4',
        '--concurrent-fragments', '4',
        '--no-playlist',
        '-o', temp_video_path,
        video_url
    ]
    
    try:
        print("   Downloading...")
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        print_success("Download complete")
        
        # Find the actual downloaded file
        downloaded_files = list(Path(temp_dir).glob(f"{video_id}_full.*"))
        if not downloaded_files:
            raise FileNotFoundError(f"Downloaded video file not found for {video_id}")
        
        full_video_path = str(downloaded_files[0])
        
        # Check source video properties
        try:
            probe_cmd = ['ffprobe', '-v', 'quiet', '-select_streams', 'v:0', 
                        '-show_entries', 'stream=width,height,r_frame_rate', 
                        '-of', 'csv=s=x:p=0', full_video_path]
            result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
            source_info = result.stdout.strip()
            print_info(f"Source quality: {source_info}")
        except Exception:
            print_warning("Could not detect source video properties")
        
        print(f"✂️  Extracting {clip_duration}s clip from {start_time}s...")
        
        # Software encoding command
        cmd_extract = [
            'ffmpeg', '-i', full_video_path,
            '-ss', str(start_time), '-t', str(clip_duration),
            '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23',
            '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30',
            '-c:a', 'copy', '-avoid_negative_ts', 'make_zero',
            '-threads', '0', clip_path, '-y'
        ]
        
        # Process with software encoding
        print("   Processing video...")
        subprocess.run(cmd_extract, capture_output=True, check=True)
        print_success("Video processing complete")
        
        # Remove the full video file to save space
        os.remove(full_video_path)
        
        print_success(f"Clip {clip_num}/{total_clips} saved successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to process video {video_id}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"   Error details: {e.stderr}")
        return False
    except Exception as e:
        print_error(f"Unexpected error processing {video_id}: {str(e)}")
        return False


def check_dependencies():
    """Check if required dependencies (yt-dlp and ffmpeg) are available."""
    print_info("Checking dependencies...")
    
    dependencies_ok = True
    
    # Check yt-dlp
    try:
        subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
        print_success("yt-dlp is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("yt-dlp is not installed or not in PATH")
        print("   Install with: pip install yt-dlp")
        dependencies_ok = False
    
    # Check ffmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print_success("ffmpeg is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("ffmpeg is not installed or not in PATH")
        print("   Download from: https://ffmpeg.org/download.html")
        dependencies_ok = False
    
    if dependencies_ok:
        print_success("All dependencies are ready!")
    else:
        print_error("Please install missing dependencies before continuing.")
    
    print()  # Add spacing
    return dependencies_ok
