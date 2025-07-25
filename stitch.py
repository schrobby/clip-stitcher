import os
import re
import subprocess
import tempfile
import shutil
from urllib.parse import urlparse, parse_qs
from pathlib import Path

def parse_youtube_url(url):
    """
    Parse YouTube URL to extract video ID and timestamp.
    Supports various YouTube URL formats.
    """
    # Regular expressions for different YouTube URL formats
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)',
        r'youtube\.com/embed/([a-zA-Z0-9_-]+)',
        r'youtube\.com/v/([a-zA-Z0-9_-]+)'
    ]
    
    video_id = None
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            break
    
    if not video_id:
        raise ValueError(f"Could not extract video ID from URL: {url}")
    
    # Extract timestamp
    timestamp = 0
    if 't=' in url:
        # Parse t parameter
        parsed_url = urlparse(url)
        if parsed_url.query:
            params = parse_qs(parsed_url.query)
            if 't' in params:
                timestamp = int(params['t'][0])
    
    return video_id, timestamp

def check_dependencies():
    """Check if required dependencies (yt-dlp and ffmpeg) are available."""
    try:
        subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
        print("✓ yt-dlp is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ yt-dlp is not installed or not in PATH")
        print("Install with: pip install yt-dlp")
        return False
    
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✓ ffmpeg is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ffmpeg is not installed or not in PATH")
        print("Download from: https://ffmpeg.org/download.html")
        return False
    
    return True

def download_video_segment(video_id, start_time, duration, output_path, temp_dir):
    """
    Download a specific segment of a YouTube video.
    """
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    temp_video_path = os.path.join(temp_dir, f"{video_id}_full.%(ext)s")
    
    print(f"Downloading video {video_id}...")
    
    # Download the full video first
    cmd = [
        'yt-dlp',
        '-f', 'best[height<=720]',  # Limit quality to 720p for faster download
        '-o', temp_video_path,
        video_url
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Find the actual downloaded file
        downloaded_files = list(Path(temp_dir).glob(f"{video_id}_full.*"))
        if not downloaded_files:
            raise FileNotFoundError(f"Downloaded video file not found for {video_id}")
        
        full_video_path = str(downloaded_files[0])
        
        print(f"Extracting {duration}s clip starting at {start_time}s...")
        
        # Extract the specific segment using ffmpeg
        cmd_extract = [
            'ffmpeg',
            '-i', full_video_path,
            '-ss', str(start_time),
            '-t', str(duration),
            '-c', 'copy',  # Copy without re-encoding for speed
            '-avoid_negative_ts', 'make_zero',
            output_path,
            '-y'  # Overwrite output file if it exists
        ]
        
        subprocess.run(cmd_extract, capture_output=True, check=True)
        
        # Remove the full video file to save space
        os.remove(full_video_path)
        
        print(f"✓ Clip saved: {output_path}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error processing video {video_id}: {e}")
        print(f"Command output: {e.stderr}")
        return False

def create_video_list_file(clip_paths, temp_dir):
    """Create a text file listing all video clips for ffmpeg concatenation."""
    list_file_path = os.path.join(temp_dir, "video_list.txt")
    
    with open(list_file_path, 'w') as f:
        for clip_path in clip_paths:
            # Use forward slashes for ffmpeg, even on Windows
            normalized_path = clip_path.replace('\\', '/')
            f.write(f"file '{normalized_path}'\n")
    
    return list_file_path

def concatenate_videos(clip_paths, output_path, temp_dir):
    """Concatenate all video clips into a single video."""
    if not clip_paths:
        print("❌ No clips to concatenate")
        return False
    
    print(f"Concatenating {len(clip_paths)} clips...")
    
    # Create video list file
    list_file_path = create_video_list_file(clip_paths, temp_dir)
    
    # Use ffmpeg to concatenate
    cmd = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', list_file_path,
        '-c', 'copy',
        output_path,
        '-y'
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        print(f"✓ Final video created: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error concatenating videos: {e}")
        return False

def main():
    """Main function to process YouTube URLs and create video compilation."""
    
    # Configuration
    input_file = "input.txt"
    output_file = "final_output.mp4"
    clip_duration = 30  # seconds
    
    print("🎬 YouTube Clip Stitcher")
    print("=" * 30)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"❌ Input file '{input_file}' not found")
        return
    
    # Read URLs from input file
    print(f"Reading URLs from {input_file}...")
    urls = []
    try:
        with open(input_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"❌ Error reading input file: {e}")
        return
    
    if not urls:
        print("❌ No URLs found in input file")
        return
    
    print(f"Found {len(urls)} URLs to process")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="clip_stitcher_")
    print(f"Working directory: {temp_dir}")
    
    try:
        clip_paths = []
        
        # Process each URL
        for i, url in enumerate(urls, 1):
            print(f"\n--- Processing clip {i}/{len(urls)} ---")
            print(f"URL: {url}")
            
            try:
                # Parse URL
                video_id, start_time = parse_youtube_url(url)
                print(f"Video ID: {video_id}, Start time: {start_time}s")
                
                # Download and extract clip
                clip_filename = f"clip_{i:03d}_{video_id}.mp4"
                clip_path = os.path.join(temp_dir, clip_filename)
                
                if download_video_segment(video_id, start_time, clip_duration, clip_path, temp_dir):
                    clip_paths.append(clip_path)
                else:
                    print(f"⚠️  Skipping clip {i} due to download error")
                    
            except Exception as e:
                print(f"❌ Error processing URL {i}: {e}")
                continue
        
        # Concatenate all clips
        if clip_paths:
            print("\n--- Creating final video ---")
            if concatenate_videos(clip_paths, output_file, temp_dir):
                print(f"\n🎉 Success! Final video saved as: {output_file}")
                print(f"📊 Total clips processed: {len(clip_paths)}")
                print(f"⏱️  Total duration: ~{len(clip_paths) * clip_duration} seconds")
            else:
                print("❌ Failed to create final video")
        else:
            print("❌ No clips were successfully downloaded")
    
    finally:
        # Cleanup temporary files
        print("\n--- Cleaning up ---")
        try:
            shutil.rmtree(temp_dir)
            print("✓ Temporary files cleaned up")
        except Exception as e:
            print(f"⚠️  Warning: Could not clean up temporary directory: {e}")
            print(f"Manual cleanup may be needed: {temp_dir}")

if __name__ == "__main__":
    main()