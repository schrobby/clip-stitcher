"""
Configuration and file handling utilities.
"""

import os
from .ui import print_success, print_error, print_info
from .youtube import parse_youtube_url


class Config:
    """Configuration class for the YouTube Clip Stitcher."""
    
    def __init__(self):
        self.input_file = "input.txt"
        self.output_file = "final_output.mp4"
        self.clip_duration = 30  # seconds
        self.use_transitions = True  # Set to False for faster processing without transitions
        self.transition_duration = 1.0  # Duration of blend transition in seconds
        self.fonts_dir = "assets/fonts"


def read_input_file(config):
    """
    Read and parse the input file containing YouTube URLs.
    
    Args:
        config (Config): Configuration object
        
    Returns:
        list: List of URLs, or None if error
    """
    if not os.path.exists(config.input_file):
        print_error(f"Input file '{config.input_file}' not found")
        print("   Please create an input.txt file with YouTube URLs (one per line)")
        return None
    
    urls = []
    try:
        with open(config.input_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print_error(f"Error reading input file: {str(e)}")
        return None
    
    if not urls:
        print_error("No URLs found in input file")
        print("   Please add YouTube URLs to input.txt (one per line)")
        return None
    
    print_success(f"Found {len(urls)} URLs to process")
    return urls


def display_processing_info(config, urls):
    """Display information about the processing configuration and URLs."""
    # Display transition settings
    if config.use_transitions and len(urls) > 1:
        print_info(f"Blend transitions enabled ({config.transition_duration}s duration)")
    elif len(urls) > 1:
        print_info("Transitions disabled (faster processing)")
    else:
        print_info("Single clip - no transitions needed")
    
    # Display the URLs to be processed
    print("\n📋 URLs to process:")
    for i, url in enumerate(urls, 1):
        try:
            video_id, start_time = parse_youtube_url(url)
            print(f"   {i}. Video: {video_id} (starting at {start_time}s)")
        except Exception:
            print(f"   {i}. {url} (⚠️  may have parsing issues)")
    
    print()
