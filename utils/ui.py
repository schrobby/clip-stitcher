"""
UI utilities for YouTube Clip Stitcher.
Provides beautiful terminal output with emojis and consistent formatting.
"""

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

def print_final_success(output_file, clip_count, clip_duration):
    """Print the final success summary."""
    try:
        import os
        file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
        
        print("\n" + "="*60)
        print("🎉 SUCCESS! Your video compilation is ready!")
        print("="*60)
        print(f"📁 File: {output_file}")
        print(f"📏 Size: {file_size:.1f} MB")
        print(f"🎬 Clips: {clip_count} clips")
        print(f"⏱️  Duration: ~{clip_count * clip_duration} seconds")
        print("="*60)
        
        # Check video properties
        try:
            import subprocess
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
