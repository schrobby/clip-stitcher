# YouTube Clip Stitcher

A Python script that creates video compilations from YouTube timestamp links with optional blend transitions between clips.

## Features

- Download and process clips from YouTube URLs with timestamps
- Optional smooth blend transitions between clips
- Large clip number overlay in the bottom-left of each clip
- Automatic video quality normalization (1080p, 30fps)
- Clean modular codebase for easy customization

## Prerequisites

1. **Python 3.7+**
2. **ffmpeg** - Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
3. **yt-dlp** - Installed automatically via requirements.txt

## Installation

```bash
pip install -r requirements.txt
```

## Usage

1. **Add URLs to input.txt** (one per line):
   ```
   https://youtu.be/pPoYQPcBUQ4?t=35
   https://youtu.be/8W5TWR74Mms?t=49
   https://youtu.be/Sv2MLXAT8Bw?t=55
   ```

2. **Run the script**:
   ```bash
   python stitch.py
   ```

3. **Get your video**: `final_output.mp4` will be created with all clips stitched together.

## Configuration

Edit settings in `utils/config.py`:

```python
class Config:
    def __init__(self):
        self.clip_duration = 30          # Clip length in seconds
        self.use_transitions = True      # Enable blend transitions
        self.transition_duration = 1.0   # Transition length in seconds
        self.output_file = "final_output.mp4"
```

## How it Works

1. **Parse** YouTube URLs and extract video IDs + timestamps
2. **Download** videos using yt-dlp (up to 1080p)
3. **Process** clips with ffmpeg (normalize to 1080p@30fps)
4. **Stitch** clips together with optional blend transitions
5. **Cleanup** temporary files automatically


## Troubleshooting

- **ffmpeg not found**: Make sure ffmpeg is in your system PATH
- **yt-dlp errors**: Some videos may be restricted or unavailable
- **Slow processing**: Video download and processing takes time

## License

MIT License - see LICENSE file for details.
