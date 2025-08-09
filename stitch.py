"""
YouTube Clip Stitcher - Main Application
Create video compilations from YouTube timestamps.

Features:
- Beautiful terminal interface with real-time progress bars
- Download and process YouTube clips from timestamped URLs
- Stitch clips together with optional blend transitions
- Automatic quality optimization and format standardization

Configuration options in config.yaml:
- use_transitions: Enable/disable blend transitions between clips
- transition_duration: Duration of transition effect in seconds
- clip_duration: Length of each clip in seconds
"""

import sys
from utils.config import Config, read_input_file
from utils.video_processor import check_dependencies


def main():
    """Main function to process YouTube URLs and create video compilation."""
    
    # Load configuration
    config = Config()
    
    # Check if we should use the old UI (for compatibility)
    use_old_ui = "--legacy" in sys.argv
    
    if use_old_ui:
        # Use the original UI
        from utils.legacy_processor import process_with_legacy_ui
        process_with_legacy_ui(config)
        return
    
    # Read input file
    urls = read_input_file(config)
    if urls is None:
        print("❌ Could not read input file. Please check your input.txt file.")
        return
    
    # Check dependencies before starting UI
    if not check_dependencies():
        print("❌ Dependencies check failed. Please install required dependencies.")
        return
    
    try:
        # Run the beautiful Textual UI
        from utils.textual_ui import run_textual_ui
        run_textual_ui(config, urls)
    except ImportError:
        print("❌ Textual not installed. Install with: pip install textual")
        print("   Or use legacy mode with: python stitch.py --legacy")
        return
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error running UI: {e}")
        print("   Try legacy mode with: python stitch.py --legacy")


if __name__ == "__main__":
    main()
