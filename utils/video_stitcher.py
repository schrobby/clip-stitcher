"""
Video stitching utilities for combining clips with or without transitions.
"""

import os
import subprocess
from .ui import print_success, print_error, print_info


def create_video_list_file(clip_paths, temp_dir):
    """Create a text file listing all video clips for ffmpeg concatenation."""
    list_file_path = os.path.join(temp_dir, "video_list.txt")
    
    with open(list_file_path, 'w') as f:
        for clip_path in clip_paths:
            # Use forward slashes for ffmpeg, even on Windows
            normalized_path = clip_path.replace('\\', '/')
            f.write(f"file '{normalized_path}'\n")
    
    return list_file_path


def stitch_videos_with_transitions(clip_paths, output_path, temp_dir, transition_duration=1.0, clip_duration=30):
    """Concatenate video clips with blend transitions between them."""
    if not clip_paths:
        print_error("No clips to concatenate")
        return False
    
    if len(clip_paths) == 1:
        # Single clip, no transitions needed - just copy
        print("\n🔗 Single clip detected, copying to output...")
        try:
            subprocess.run(['ffmpeg', '-i', clip_paths[0], '-c', 'copy', output_path, '-y'], 
                         capture_output=True, check=True)
            print_success(f"Single clip copied: {output_path}")
            return True
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to copy single clip: {str(e)}")
            return False
    
    print(f"\n🔗 Combining {len(clip_paths)} clips with {transition_duration}s blend transitions...")
    
    # For transitions, we'll use a different approach with overlay filters
    inputs = []
    filter_complex = []
    
    # Add all input files
    for i, clip_path in enumerate(clip_paths):
        inputs.extend(['-i', clip_path])
    
    # Create fade in/out effects and overlay them
    video_filters = []
    audio_filters = []
    
    for i, clip_path in enumerate(clip_paths):
        if i == 0:
            # First clip: fade out at the end
            video_filters.append(f"[{i}:v]fade=t=out:st={clip_duration-transition_duration}:d={transition_duration}[v{i}]")
            audio_filters.append(f"[{i}:a]afade=t=out:st={clip_duration-transition_duration}:d={transition_duration}[a{i}]")
        elif i == len(clip_paths) - 1:
            # Last clip: fade in at the beginning  
            video_filters.append(f"[{i}:v]fade=t=in:st=0:d={transition_duration}[v{i}]")
            audio_filters.append(f"[{i}:a]afade=t=in:st=0:d={transition_duration}[a{i}]")
        else:
            # Middle clips: fade in and out
            video_filters.append(f"[{i}:v]fade=t=in:st=0:d={transition_duration},fade=t=out:st={clip_duration-transition_duration}:d={transition_duration}[v{i}]")
            audio_filters.append(f"[{i}:a]afade=t=in:st=0:d={transition_duration},afade=t=out:st={clip_duration-transition_duration}:d={transition_duration}[a{i}]")
    
    # Concatenate the faded clips
    video_concat = "".join(f"[v{i}]" for i in range(len(clip_paths))) + f"concat=n={len(clip_paths)}:v=1:a=0[vout]"
    audio_concat = "".join(f"[a{i}]" for i in range(len(clip_paths))) + f"concat=n={len(clip_paths)}:v=0:a=1[aout]"
    
    filter_complex = video_filters + audio_filters + [video_concat, audio_concat]
    
    # Build ffmpeg command
    cmd = ['ffmpeg'] + inputs + [
        '-filter_complex', '; '.join(filter_complex),
        '-map', '[vout]', '-map', '[aout]',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
        '-c:a', 'aac', '-b:a', '128k',
        output_path, '-y'
    ]
    
    try:
        print("   Creating transitions...")
        subprocess.run(cmd, capture_output=True, check=True)
        print_success(f"Final video with transitions created: {output_path}")
        return True
        
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to create video with transitions: {str(e)}")
        print_info("Falling back to simple concatenation...")
        return stitch_videos_simple(clip_paths, output_path, temp_dir)


def stitch_videos_simple(clip_paths, output_path, temp_dir):
    """Concatenate all video clips into a single video without transitions (faster)."""
    if not clip_paths:
        print_error("No clips to concatenate")
        return False
    
    print(f"\n🔗 Combining {len(clip_paths)} clips into final video...")
    
    # Create video list file
    list_file_path = create_video_list_file(clip_paths, temp_dir)
    
    # Use ffmpeg to concatenate with stream copy for speed
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


def stitch_videos(clip_paths, output_path, temp_dir, use_transitions=False, transition_duration=1.0, clip_duration=30):
    """Concatenate video clips with optional blend transitions."""
    if use_transitions:
        return stitch_videos_with_transitions(clip_paths, output_path, temp_dir, transition_duration, clip_duration)
    else:
        return stitch_videos_simple(clip_paths, output_path, temp_dir)
