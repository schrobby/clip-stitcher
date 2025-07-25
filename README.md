# YouTube Clip Stitcher

A Python script that takes YouTube timestamp links and creates a compilation video with 30-second clips from each link.

## Prerequisites

1. **Python 3.7+** - Make sure Python is installed and in your PATH
2. **ffmpeg** - Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html) and add to your PATH
3. **yt-dlp** - Will be installed via pip (see installation steps below)

## Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure ffmpeg is installed and accessible from command line:
   ```bash
   ffmpeg -version
   ```

## Usage

1. **Create input file**: Add your YouTube URLs with timestamps to `input.txt`, one URL per line. The script supports various YouTube URL formats:
   ```
   https://youtu.be/pPoYQPcBUQ4?si=gyaSIZT2We27H7D5&t=35
   https://youtu.be/8W5TWR74Mms?si=56q7sv8pDpOi8oz8&t=49
   https://youtu.be/Sv2MLXAT8Bw?t=55
   https://www.youtube.com/watch?v=VIDEO_ID&t=120
   ```

2. **Run the script**:
   ```bash
   python stitch.py
   ```

3. **Output**: The script will create `final_output.mp4` containing all the 30-second clips stitched together.

## How it works

1. **Parse URLs**: Extracts video IDs and timestamps from YouTube URLs
2. **Download**: Uses yt-dlp to download each video (up to 1080p quality with best audio)
3. **Extract clips**: Uses ffmpeg to extract 30-second segments with high-quality re-encoding
4. **Concatenate**: Combines all clips into a single video file with consistent quality
5. **Cleanup**: Removes all temporary files

## Features

- ✅ Supports multiple YouTube URL formats
- ✅ Downloads videos in up to 1080p quality with best available audio
- ✅ High-quality video encoding (H.264 with CRF 18 - visually lossless)
- ✅ High-quality audio encoding (AAC at 192kbps)
- ✅ Extracts precise 30-second clips from specified timestamps
- ✅ Automatic cleanup of temporary files
- ✅ Progress tracking and error handling
- ✅ Dependency checking before execution

## Troubleshooting

- **ffmpeg not found**: Make sure ffmpeg is installed and in your system PATH
- **yt-dlp errors**: Some videos may be unavailable or have download restrictions
- **Permission errors**: Make sure you have write permissions in the script directory
- **Long processing times**: Downloading videos can take time depending on your internet connection

## Configuration

You can modify these settings in the `main()` function:
- `clip_duration`: Length of each clip in seconds (default: 30)
- `output_file`: Name of the final output video (default: "final_output.mp4")

For advanced users, you can adjust quality settings in the code:
- Video quality: Modify the `-crf` parameter (lower = better quality, 18 = visually lossless)
- Audio quality: Modify the `-b:a` parameter (higher = better quality, 192k = high quality)
- Video resolution: Modify the `-f` parameter in yt-dlp command

## License

This project is licensed under the MIT License - see the LICENSE file for details.
