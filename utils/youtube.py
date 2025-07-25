"""
YouTube URL parsing utilities.
Handles extraction of video IDs and timestamps from various YouTube URL formats.
"""

import re
from urllib.parse import urlparse, parse_qs

def parse_youtube_url(url):
    """
    Parse YouTube URL to extract video ID and timestamp.
    Supports various YouTube URL formats.
    
    Args:
        url (str): YouTube URL to parse
        
    Returns:
        tuple: (video_id, timestamp) where timestamp is in seconds
        
    Raises:
        ValueError: If video ID cannot be extracted from URL
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
