"""
Video processing utilities for the YouTube Clip Stitcher.
Handles video downloading, extraction, and processing.
"""

import os
import shutil
import subprocess
from pathlib import Path
from .ui import print_success, print_error, print_warning, print_info
from .config import Config


def find_font_file():
    """
    Find a font file in the assets/fonts directory.
    
    Returns:
        str: Path to font file, or None if not found
    """
    try:
        # Get project root directory from script location
        root_dir = Path(__file__).parent.parent
        config = Config()
        cfg_path = Path(config.fonts_dir)
        fonts_dir = cfg_path if cfg_path.is_absolute() else (root_dir / cfg_path)
        
        if not fonts_dir.exists():
            print_error(f"Fonts directory not found: {fonts_dir}")
            return None
        
        # Find font files
        candidates = []
        for ext in ("*.ttf", "*.otf", "*.ttc"):
            candidates.extend(list(fonts_dir.rglob(ext)))
        
        if not candidates:
            print_error(f"No font files found in {fonts_dir}")
            return None
        
        # Return first font found
        font_file = candidates[0]
        print_info(f"Using font: {font_file.name}")
        return str(font_file.absolute())
        
    except Exception as e:
        print_error(f"Error finding font: {e}")
        return None


def prepare_font_for_overlay(font_path, temp_dir):
    """
    Copy font to temp directory for reliable path handling.
    
    Args:
        font_path (str): Path to original font file
        temp_dir (str): Temporary directory for processing
        
    Returns:
        str: Simple font filename for use in temp directory
    """
    font_name = os.path.basename(font_path)
    temp_font_path = os.path.join(temp_dir, font_name)
    shutil.copy2(font_path, temp_font_path)
    return font_name


def create_drawtext_filter(font_filename, clip_num):
    """
    Create FFmpeg drawtext filter for clip number overlay.
    
    Args:
        font_filename (str): Font filename (simple name, no path)
        clip_num (int): Clip number to display
        
    Returns:
        str: FFmpeg drawtext filter string
    """
    options = [
        f"fontfile={font_filename}",
        f"text={clip_num}",
        "x=24",
        "y=24", 
        "fontsize=96",
        "fontcolor=white",
        "box=1",
        "boxcolor=black@0.5",
        "boxborderw=10"
    ]
    return "drawtext=" + ":".join(options)


def process_video_with_overlay(full_video_path, start_time, clip_duration, clip_path, temp_dir, clip_num):
    """
    Process video with clip number overlay.
    
    Returns:
        bool: True if successful, False if overlay failed
    """
    # Base video processing filters
    base_vf = (
        "scale=1920:1080:force_original_aspect_ratio=decrease,"
        "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30"
    )
    
    # Find and prepare font
    font_path = find_font_file()
    if not font_path:
        return False
    
    font_filename = prepare_font_for_overlay(font_path, temp_dir)
    drawtext = create_drawtext_filter(font_filename, clip_num)
    
    # Create complete filter chain
    vf_chain = f"{base_vf},{drawtext}"
    
    # Build FFmpeg command
    cmd = [
        'ffmpeg', '-i', full_video_path,
        '-ss', str(start_time), '-t', str(clip_duration),
        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23',
        '-vf', vf_chain,
        '-c:a', 'copy', '-avoid_negative_ts', 'make_zero',
        '-threads', '0', clip_path, '-y'
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=temp_dir)
        return True
    except subprocess.CalledProcessError:
        return False


def process_video_without_overlay(full_video_path, start_time, clip_duration, clip_path, temp_dir):
    """
    Process video without overlay (fallback when overlay fails).
    """
    base_vf = (
        "scale=1920:1080:force_original_aspect_ratio=decrease,"
        "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30"
    )
    
    cmd = [
        'ffmpeg', '-i', full_video_path,
        '-ss', str(start_time), '-t', str(clip_duration),
        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23',
        '-vf', base_vf,
        '-c:a', 'copy', '-avoid_negative_ts', 'make_zero',
        '-threads', '0', clip_path, '-y'
    ]
    
    subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=temp_dir)


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
    try:
        # Download video
        if not _download_video(video_id, temp_dir, clip_num, total_clips):
            return False
        
        # Find downloaded file
        full_video_path = _find_downloaded_file(video_id, temp_dir)
        if not full_video_path:
            return False
        
        # Show source info
        _show_source_info(full_video_path)
        
        # Process video
        print(f"✂️  Extracting {clip_duration}s clip from {start_time}s...")
        print("   Processing video...")
        
        # Try with overlay first, fallback to no overlay if it fails
        success = process_video_with_overlay(
            full_video_path, start_time, clip_duration, clip_path, temp_dir, clip_num
        )
        
        if not success:
            print_warning("Overlay failed, processing without clip number...")
            process_video_without_overlay(
                full_video_path, start_time, clip_duration, clip_path, temp_dir
            )
        
        # Cleanup
        os.remove(full_video_path)
        
        print_success("Video processing complete")
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


def _download_video(video_id, temp_dir, clip_num, total_clips):
    """Download video from YouTube."""
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    temp_video_path = os.path.join(temp_dir, f"{video_id}_full.%(ext)s")
    
    print(f"\n📥 Downloading clip {clip_num}/{total_clips}: {video_id}")
    
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
        return True
    except subprocess.CalledProcessError:
        print_error("Download failed")
        return False


def _find_downloaded_file(video_id, temp_dir):
    """Find the downloaded video file."""
    downloaded_files = list(Path(temp_dir).glob(f"{video_id}_full.*"))
    if not downloaded_files:
        print_error(f"Downloaded video file not found for {video_id}")
        return None
    return str(downloaded_files[0])


def _show_source_info(full_video_path):
    """Show source video information."""
    try:
        probe_cmd = [
            'ffprobe', '-v', 'quiet', '-select_streams', 'v:0', 
            '-show_entries', 'stream=width,height,r_frame_rate', 
            '-of', 'csv=s=x:p=0', full_video_path
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        source_info = result.stdout.strip()
        print_info(f"Source quality: {source_info}")
    except Exception:
        pass  # Not critical if this fails


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
