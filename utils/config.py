"""
Configuration and file handling utilities.
"""

import os
import yaml
from pathlib import Path
from .ui import print_success, print_error, print_info
from .youtube import parse_youtube_url


class Config:
    """Configuration class for the YouTube Clip Stitcher."""
    
    def __init__(self):
        # Default values (fallback if config.yaml is missing or incomplete)
        self.input_file = "input.txt"
        self.output_file = "final_output.mp4"
        self.clip_duration = 30
        self.use_transitions = True
        self.transition_duration = 1.0
        self.fonts_dir = "assets/fonts"
        
        # Advanced settings with defaults
        self.video_quality = "1080p"
        self.encoding_preset = "ultrafast"
        self.crf_value = 23
        
        # Load settings from config.yaml if it exists
        self._load_from_yaml()
    
    def _load_from_yaml(self):
        """Load configuration from config.yaml file."""
        try:
            # Find config.yaml in the project root
            config_path = Path(__file__).parent.parent / "config.yaml"
            
            if not config_path.exists():
                # Only show this message once by checking if it's the first Config instance
                if not hasattr(Config, '_yaml_message_shown'):
                    print_info("No config.yaml found, using default settings")
                    Config._yaml_message_shown = True
                return
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if not config_data:
                return
            
            # Update settings from YAML
            for key, value in config_data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            # Only show this message once
            if not hasattr(Config, '_yaml_message_shown'):
                print_info("Configuration loaded from config.yaml")
                Config._yaml_message_shown = True
            
        except yaml.YAMLError as e:
            print_error(f"Error parsing config.yaml: {e}")
            print_info("Using default settings")
        except Exception as e:
            print_error(f"Error loading config.yaml: {e}")
            print_info("Using default settings")


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
