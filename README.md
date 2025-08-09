# 🎬 YouTube Clip Stitcher

**Create amazing video compilations from your favorite YouTube moments!**

Turn a list of timestamped YouTube links into a single polished video compilation with smooth transitions and clip numbers. Perfect for creating highlight reels, funny moments compilations, or educational content mashups.

## ✨ What This Tool Does

- 📥 **Automatically downloads** clips from YouTube URLs with timestamps
- ✂️ **Extracts precise segments** from each video 
- 🔀 **Combines everything** into one seamless compilation
- 🎨 **Adds clip numbers** so viewers know which video they're watching
- 🌊 **Smooth transitions** between clips (optional)
- 📐 **Standardizes quality** to 1080p for consistency

## 🚀 Quick Start

### 1. **Install Requirements**
You'll need these on your computer:
- **Python 3.7 or newer** - [Download here](https://www.python.org/downloads/)
- **FFmpeg** - [Download here](https://ffmpeg.org/download.html) (video processing tool)

### 2. **Download This Project**
Download or clone this project to your computer.

### 3. **Install Python Dependencies**
Open a terminal/command prompt in the project folder and run:
```bash
pip install -r requirements.txt
```

### 4. **Add Your YouTube Links**
Edit the `input.txt` file and add your YouTube URLs (one per line):
```
https://youtu.be/pPoYQPcBUQ4?t=35
https://youtu.be/8W5TWR74Mms?t=49
https://youtu.be/Sv2MLXAT8Bw?t=55
```
💡 **Tip**: Make sure your URLs include the `?t=` timestamp part!

### 5. **Run the Magic** ✨
```bash
python stitch.py
```

### 6. **Enjoy Your Video!**
Your compilation will be saved as `compilation.mp4` (or whatever you named it in the config).

## ⚙️ Customize Your Settings

Want to change how long each clip is? Different output filename? Easy! Just edit the `config.yaml` file:

```yaml
# Basic settings you'll probably want to change
clip_duration: 30                # How long each clip should be (seconds)
output_file: "my_awesome_compilation.mp4"  # Your video's filename
use_transitions: true            # Smooth blending between clips
transition_duration: 1          # How long transitions last (seconds)

# You probably don't need to change these
input_file: "input.txt"          # File with your YouTube URLs
fonts_dir: "assets/fonts"        # Where the overlay fonts are stored
```

## 🔧 Troubleshooting

**"ffmpeg not found" error?**
- Make sure you installed FFmpeg and it's in your system PATH
- On Windows: Add FFmpeg to your environment variables
- On Mac: Try `brew install ffmpeg`

**Some videos won't download?**
- Some YouTube videos are restricted or private
- Age-restricted content might not work
- Try a different video if one fails

**Processing is slow?**
- This is normal! Downloading and processing video takes time
- Longer clips = more processing time
- Be patient, it's worth the wait! ☕

**Video quality issues?**
- All videos are automatically converted to 1080p for consistency
- If source video is lower quality, it won't be upscaled beyond original

## 🎨 Advanced Features

### Custom Fonts
Want different looking clip numbers? Drop any `.ttf` or `.otf` font file into the `assets/fonts` folder!

### No Transitions Mode
For faster processing, set `use_transitions: false` in `config.yaml`.

### Quality Settings
Uncomment the advanced settings in `config.yaml` to fine-tune video quality and processing speed.

## 📁 What You'll See

```
clip-stitcher/
├── stitch.py              # Main script - run this!
├── config.yaml            # Your settings - edit this!
├── input.txt              # Your YouTube URLs - edit this!
├── requirements.txt       # Python dependencies
├── assets/fonts/          # Font files for clip numbers
└── utils/                 # Internal code (don't touch)
```

## ❓ Need Help?

1. **Check this README** - Most answers are here!
2. **Look at the example files** - `input.txt` and `config.yaml` have examples
3. **File an issue** - If something's broken, let us know!

## 📜 License

MIT License - Use this however you want! See `LICENSE` file for details.