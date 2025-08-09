import os
import subprocess
import tempfile
import shutil

# Import our custom modules
from utils.ui import (
    print_header, print_step, print_success, print_error, 
    print_warning, print_info, print_final_success
)
from utils.youtube import parse_youtube_url
from utils.video_processor import process_video_clip, check_dependencies
from utils.video_stitcher import stitch_videos
from utils.config import Config, read_input_file, display_processing_info


def main():
    """Main function to process YouTube URLs and create video compilation."""
    
    # Load configuration
    config = Config()
    
    print_header()
    
    # Step 1: Check dependencies
    print_step(1, 4, "Checking dependencies")
    if not check_dependencies():
        return
    
    # Step 2: Read input file
    print_step(2, 4, "Reading input file")
    urls = read_input_file(config)
    if urls is None:
        return
    
    # Display processing information
    display_processing_info(config, urls)
    
    # Step 3: Process each clip
    print_step(3, 4, f"Processing {len(urls)} video clips")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="clip_stitcher_")
    print_info(f"Working directory: {temp_dir}")
    
    try:
        clip_paths = []
        successful_clips = 0
        
        # Process each URL
        for i, url in enumerate(urls, 1):
            try:
                # Parse URL
                video_id, start_time = parse_youtube_url(url)
                
                # Process clip
                clip_filename = f"clip_{i:03d}_{video_id}.mp4"
                clip_path = os.path.join(temp_dir, clip_filename)
                
                if process_video_clip(video_id, start_time, config.clip_duration, clip_path, temp_dir, i, len(urls)):
                    clip_paths.append(clip_path)
                    successful_clips += 1
                else:
                    print_warning(f"Skipped clip {i} due to processing error")
                    
            except Exception as e:
                print_error(f"Error processing URL {i}: {str(e)}")
                continue
        
        print(f"\n📊 Processing complete: {successful_clips}/{len(urls)} clips successful")
        
        # Step 4: Create final video
        if clip_paths:
            print_step(4, 4, "Creating final video")
            if stitch_videos(clip_paths, config.output_file, temp_dir, config.use_transitions, config.transition_duration, config.clip_duration):
                # Get final video info and display success message
                try:
                    file_size = os.path.getsize(config.output_file) / (1024 * 1024)  # MB
                    
                    # Check video properties
                    video_info = ""
                    try:
                        result = subprocess.run(['ffprobe', '-v', 'quiet', '-select_streams', 'v:0', 
                                               '-show_entries', 'stream=width,height,r_frame_rate', 
                                               '-of', 'csv=s=x:p=0', config.output_file], 
                                               capture_output=True, text=True, check=True)
                        video_info = result.stdout.strip()
                    except Exception:
                        video_info = "Unknown"
                    
                    print_final_success(
                        filename=config.output_file,
                        file_size=file_size,
                        clip_count=len(clip_paths),
                        duration=len(clip_paths) * config.clip_duration,
                        quality=video_info
                    )
                    
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
