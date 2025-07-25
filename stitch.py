import os
import re
import subprocess
import tempfile
import shutil
from urllib.parse import urlparse, parse_qs
from pathlib import Path

def print_header():
    """Print a nice header for the application."""
    print("\n" + "="*60)
    print("           🎬 YOUTUBE CLIP STITCHER 🎬")
    print("="*60)
    print("   Create video compilations from YouTube timestamps")
    print("="*60 + "\n")

def print_step(step_num, total_steps, message):
    """Print a formatted step message."""
    print(f"[{step_num}/{total_steps}] {message}")

def print_success(message):
    """Print a success message."""
    print(f"✅ {message}")

def print_error(message):
    """Print an error message."""
    print(f"❌ {message}")

def print_warning(message):
    """Print a warning message."""
    print(f"⚠️  {message}")

def print_info(message):
    """Print an info message."""
    print(f"ℹ️  {message}")

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

def download_video_segment(video_id, start_time, duration, output_path, temp_dir, clip_num, total_clips):
    """
    Download a specific segment of a YouTube video.
    """
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    temp_video_path = os.path.join(temp_dir, f"{video_id}_full.%(ext)s")
    
    print(f"\n📥 Downloading clip {clip_num}/{total_clips}: {video_id}")
    
    # Download the full video first with high quality and faster settings
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
        # Simple download without complex progress tracking
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
        
        print(f"✂️  Extracting {duration}s clip from {start_time}s...")
        
        # Extract without complex progress simulation
        cmd_extract_hw = [
            'ffmpeg', '-hwaccel', 'auto', '-i', full_video_path,
            '-ss', str(start_time), '-t', str(duration),
            '-c:v', 'h264_nvenc', '-preset', 'fast', '-cq', '25',
            '-vf', 'scale_npp=1920:1080:force_original_aspect_ratio=decrease,pad_npp=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30',
            '-c:a', 'copy', '-avoid_negative_ts', 'make_zero',
            output_path, '-y'
        ]
        
        cmd_extract_sw = [
            'ffmpeg', '-i', full_video_path,
            '-ss', str(start_time), '-t', str(duration),
            '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23',
            '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30',
            '-c:a', 'copy', '-avoid_negative_ts', 'make_zero',
            '-threads', '0', output_path, '-y'
        ]
        
        # Try hardware acceleration first
        print("   Processing with hardware acceleration...")
        try:
            subprocess.run(cmd_extract_hw, capture_output=True, check=True)
            print_success("Used hardware acceleration")
        except subprocess.CalledProcessError:
            print_info("Hardware acceleration failed, using software encoding...")
            subprocess.run(cmd_extract_sw, capture_output=True, check=True)
            print_success("Software encoding complete")
        
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
        print_error("No clips to concatenate")
        return False
    
    print(f"\n🔗 Combining {len(clip_paths)} clips into final video...")
    
    # Create video list file
    list_file_path = create_video_list_file(clip_paths, temp_dir)
    
    # Use ffmpeg to concatenate with faster encoding settings
    cmd = [
        'ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_file_path,
        '-c', 'copy', '-avoid_negative_ts', 'make_zero', output_path, '-y'
    ]
    
    try:
        print("   Combining clips...")
        subprocess.run(cmd, capture_output=True, check=True)
        print_success(f"Final video created: {output_path}")
        return True
        
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to create final video: {str(e)}")
        return False

def main():
    """Main function to process YouTube URLs and create video compilation."""
    
    # Configuration
    input_file = "input.txt"
    output_file = "final_output.mp4"
    clip_duration = 30  # seconds
    
    print_header()
    
    # Step 1: Check dependencies
    print_step(1, 4, "Checking dependencies")
    if not check_dependencies():
        return
    
    # Step 2: Read input file
    print_step(2, 4, "Reading input file")
    if not os.path.exists(input_file):
        print_error(f"Input file '{input_file}' not found")
        print("   Please create an input.txt file with YouTube URLs (one per line)")
        return
    
    urls = []
    try:
        with open(input_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print_error(f"Error reading input file: {str(e)}")
        return
    
    if not urls:
        print_error("No URLs found in input file")
        print("   Please add YouTube URLs to input.txt (one per line)")
        return
    
    print_success(f"Found {len(urls)} URLs to process")
    
    # Display the URLs to be processed
    print("\n📋 URLs to process:")
    for i, url in enumerate(urls, 1):
        try:
            video_id, start_time = parse_youtube_url(url)
            print(f"   {i}. Video: {video_id} (starting at {start_time}s)")
        except Exception:
            print(f"   {i}. {url} (⚠️  may have parsing issues)")
    
    print()
    
    # Step 3: Process each clip
    print_step(3, 4, f"Processing {len(urls)} video clips")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="clip_stitcher_")
    print_info(f"Working directory: {temp_dir}")
    
    try:
        clip_paths = []
        successful_clips = 0
        
        # Process each URL with overall progress
        for i, url in enumerate(urls, 1):
            try:
                # Parse URL
                video_id, start_time = parse_youtube_url(url)
                
                # Download and extract clip
                clip_filename = f"clip_{i:03d}_{video_id}.mp4"
                clip_path = os.path.join(temp_dir, clip_filename)
                
                if download_video_segment(video_id, start_time, clip_duration, clip_path, temp_dir, i, len(urls)):
                    clip_paths.append(clip_path)
                    successful_clips += 1
                else:
                    print_warning(f"Skipped clip {i} due to download error")
                    
            except Exception as e:
                print_error(f"Error processing URL {i}: {str(e)}")
                continue
        
        print(f"\n📊 Processing complete: {successful_clips}/{len(urls)} clips successful")
        
        # Step 4: Create final video
        if clip_paths:
            print_step(4, 4, "Creating final video")
            if concatenate_videos(clip_paths, output_file, temp_dir):
                # Get final video info
                try:
                    file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
                    
                    print("\n" + "="*60)
                    print("🎉 SUCCESS! Your video compilation is ready!")
                    print("="*60)
                    print(f"📁 File: {output_file}")
                    print(f"📏 Size: {file_size:.1f} MB")
                    print(f"🎬 Clips: {len(clip_paths)} clips")
                    print(f"⏱️  Duration: ~{len(clip_paths) * clip_duration} seconds")
                    print("="*60)
                    
                    # Check video properties
                    try:
                        result = subprocess.run(['ffprobe', '-v', 'quiet', '-select_streams', 'v:0', 
                                               '-show_entries', 'stream=width,height,r_frame_rate', 
                                               '-of', 'csv=s=x:p=0', output_file], 
                                               capture_output=True, text=True, check=True)
                        info = result.stdout.strip()
                        print(f"🎥 Quality: {info}")
                    except Exception:
                        pass
                    
                    print("\n✨ Enjoy your video compilation! ✨\n")
                    
                except Exception:
                    print_success("Video compilation created successfully!")
            else:
                print_error("Failed to create final video")
        else:
            print_error("No clips were successfully processed")
            print("   Please check your URLs and try again")
    
    finally:
        # Cleanup temporary files
        print_info("Cleaning up temporary files...")
        try:
            shutil.rmtree(temp_dir)
            print_success("Cleanup complete")
        except Exception as e:
            print_warning(f"Could not clean up temporary directory: {str(e)}")
            print(f"   Manual cleanup may be needed: {temp_dir}")

if __name__ == "__main__":
    main()