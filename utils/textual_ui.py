"""
Textual-based UI for YouTube Clip Stitcher.
Provides a beautiful terminal interface with progress bars and real-time updates.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, ProgressBar, Log, Button
from textual.binding import Binding
import threading
import queue
import os


class ClipStitcherApp(App):
    """Main Textual application for the YouTube Clip Stitcher."""
    
    CSS = """
    .title {
        text-align: center;
        background: $primary;
        color: $text;
        padding: 1;
        margin-bottom: 1;
    }
    
    .stats {
        background: $surface;
        border: solid $primary;
        padding: 1;
        margin: 1;
    }
    
    .progress-container {
        background: $surface;
        border: solid $secondary;
        padding: 1;
        margin: 1;
    }
    
    .log-container {
        border: solid $accent;
        height: 15;
        margin: 1;
    }
    
    .buttons {
        align: center middle;
        margin: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("c", "clear_log", "Clear Log"),
    ]
    
    def __init__(self, config, urls):
        super().__init__()
        self.config = config
        self.urls = urls
        self.current_clip = 0
        self.total_clips = len(urls)
        self.successful_clips = 0
        self.processing_complete = False
        
        # Queue for communication between processing thread and UI
        self.message_queue = queue.Queue()
        
    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        yield Header()
        
        with Container():
            yield Static("🎬 YOUTUBE CLIP STITCHER 🎬", classes="title")
            
            with Horizontal():
                with Vertical():
                    # Stats panel
                    with Container(classes="stats"):
                        yield Static(f"📋 Total Clips: {self.total_clips}", id="total_clips")
                        yield Static("✅ Successful: 0", id="successful_clips")
                        yield Static("❌ Failed: 0", id="failed_clips")
                        yield Static(f"⏱️  Duration per clip: {self.config.clip_duration}s", id="clip_duration")
                        yield Static(f"🔀 Transitions: {'Yes' if self.config.use_transitions else 'No'}", id="transitions")
                    
                    # Progress bars
                    with Container(classes="progress-container"):
                        yield Static("Overall Progress", id="overall_label")
                        yield ProgressBar(total=self.total_clips, id="overall_progress")
                        yield Static("Current Clip: Initializing...", id="current_label")
                        yield ProgressBar(total=100, id="current_progress")
                        yield Static("Final Processing: Waiting...", id="final_label")
                        yield ProgressBar(total=100, id="final_progress")
            
            # Log panel
            with Container(classes="log-container"):
                yield Log(id="log", auto_scroll=True)
            
            # Control buttons
            with Horizontal(classes="buttons"):
                yield Button("Start Processing", id="start_btn", variant="primary")
                yield Button("Clear Log", id="clear_btn")
                yield Button("Quit", id="quit_btn", variant="error")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the app when mounted."""
        self.log_message("🎬 YouTube Clip Stitcher initialized")
        self.log_message(f"📋 Found {self.total_clips} URLs to process")
        
        # Display URLs
        for i, url in enumerate(self.urls, 1):
            try:
                from .youtube import parse_youtube_url
                video_id, start_time = parse_youtube_url(url)
                self.log_message(f"   {i}. Video: {video_id} (starting at {start_time}s)")
            except Exception:
                self.log_message(f"   {i}. {url} (⚠️  may have parsing issues)")
        
        # Start message queue checker
        self.set_interval(0.1, self.check_message_queue)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "start_btn":
            self.start_processing()
        elif event.button.id == "clear_btn":
            self.action_clear_log()
        elif event.button.id == "quit_btn":
            self.action_quit()
    
    def start_processing(self) -> None:
        """Start the video processing in a separate thread."""
        start_btn = self.query_one("#start_btn", Button)
        start_btn.disabled = True
        start_btn.label = "Processing..."
        
        # Start processing thread
        processing_thread = threading.Thread(target=self.process_videos, daemon=True)
        processing_thread.start()
    
    def process_videos(self):
        """Process all videos (runs in separate thread)."""
        try:
            from .video_processor import process_video_clip
            from .video_stitcher import stitch_videos
            from .youtube import parse_youtube_url
            import tempfile
            import shutil
            
            # Check dependencies
            self.queue_message("info", "Checking dependencies...")
            
            # Create temp directory
            temp_dir = tempfile.mkdtemp(prefix="clip_stitcher_")
            self.queue_message("info", f"Working directory: {temp_dir}")
            
            try:
                clip_paths = []
                
                # Process each clip
                for i, url in enumerate(self.urls, 1):
                    try:
                        self.queue_message("current_clip", f"Processing clip {i}/{self.total_clips}")
                        self.queue_message("current_progress", 0)
                        
                        # Parse URL
                        video_id, start_time = parse_youtube_url(url)
                        
                        # Download phase
                        self.queue_message("current_progress", 20)
                        self.queue_message("info", f"📥 Downloading clip {i}: {video_id}")
                        
                        # Extract phase
                        self.queue_message("current_progress", 60)
                        
                        # Process clip
                        clip_filename = f"clip_{i:03d}_{video_id}.mp4"
                        clip_path = os.path.join(temp_dir, clip_filename)
                        
                        if process_video_clip(video_id, start_time, self.config.clip_duration, 
                                            clip_path, temp_dir, i, len(self.urls)):
                            clip_paths.append(clip_path)
                            self.queue_message("success", f"✅ Clip {i} processed successfully")
                            self.queue_message("clip_success", i)
                        else:
                            self.queue_message("warning", f"⚠️  Skipped clip {i} due to error")
                            self.queue_message("clip_failed", i)
                        
                        self.queue_message("current_progress", 100)
                        self.queue_message("overall_progress", i)
                        
                    except Exception as e:
                        self.queue_message("error", f"❌ Error processing clip {i}: {str(e)}")
                        self.queue_message("clip_failed", i)
                        continue
                
                # Final stitching
                if clip_paths:
                    self.queue_message("final_label", "Creating final video...")
                    self.queue_message("final_progress", 20)
                    
                    if stitch_videos(clip_paths, self.config.output_file, temp_dir, 
                                   self.config.use_transitions, self.config.transition_duration, 
                                   self.config.clip_duration):
                        self.queue_message("final_progress", 100)
                        
                        # Get file info
                        try:
                            file_size = os.path.getsize(self.config.output_file) / (1024 * 1024)
                            self.queue_message("final_success", {
                                "filename": self.config.output_file,
                                "size": file_size,
                                "clips": len(clip_paths)
                            })
                        except Exception:
                            self.queue_message("success", "🎉 Video compilation created successfully!")
                    else:
                        self.queue_message("error", "❌ Failed to create final video")
                else:
                    self.queue_message("error", "❌ No clips were successfully processed")
            
            finally:
                # Cleanup
                try:
                    shutil.rmtree(temp_dir)
                    self.queue_message("info", "🧹 Cleanup complete")
                except Exception as e:
                    self.queue_message("warning", f"⚠️  Cleanup warning: {str(e)}")
                
                self.queue_message("processing_complete", True)
        
        except Exception as e:
            self.queue_message("error", f"❌ Unexpected error: {str(e)}")
            self.queue_message("processing_complete", True)
    
    def queue_message(self, msg_type, data):
        """Queue a message for the UI thread."""
        self.message_queue.put((msg_type, data))
    
    def check_message_queue(self):
        """Check for messages from the processing thread."""
        try:
            while True:
                msg_type, data = self.message_queue.get_nowait()
                self.handle_message(msg_type, data)
        except queue.Empty:
            pass
    
    def handle_message(self, msg_type, data):
        """Handle messages from the processing thread."""
        if msg_type == "info":
            self.log_message(f"ℹ️  {data}")
        elif msg_type == "success":
            self.log_message(f"✅ {data}")
        elif msg_type == "warning":
            self.log_message(f"⚠️  {data}")
        elif msg_type == "error":
            self.log_message(f"❌ {data}")
        elif msg_type == "current_clip":
            self.query_one("#current_label", Static).update(data)
        elif msg_type == "current_progress":
            self.query_one("#current_progress", ProgressBar).progress = data
        elif msg_type == "overall_progress":
            self.query_one("#overall_progress", ProgressBar).progress = data
        elif msg_type == "final_label":
            self.query_one("#final_label", Static).update(data)
        elif msg_type == "final_progress":
            self.query_one("#final_progress", ProgressBar).progress = data
        elif msg_type == "clip_success":
            self.successful_clips += 1
            self.query_one("#successful_clips", Static).update(f"✅ Successful: {self.successful_clips}")
        elif msg_type == "clip_failed":
            failed = data - self.successful_clips
            self.query_one("#failed_clips", Static).update(f"❌ Failed: {failed}")
        elif msg_type == "final_success":
            info = data
            self.log_message("🎉 SUCCESS! Video compilation ready!")
            self.log_message(f"📁 File: {info['filename']}")
            self.log_message(f"📏 Size: {info['size']:.1f} MB")
            self.log_message(f"🎬 Clips: {info['clips']} clips")
            self.log_message(f"⏱️  Total duration: ~{info['clips'] * self.config.clip_duration} seconds")
        elif msg_type == "processing_complete":
            start_btn = self.query_one("#start_btn", Button)
            start_btn.disabled = False
            start_btn.label = "Start Processing"
            self.processing_complete = True
    
    def log_message(self, message):
        """Add a message to the log."""
        log = self.query_one("#log", Log)
        log.write_line(message)
    
    def action_clear_log(self) -> None:
        """Clear the log."""
        log = self.query_one("#log", Log)
        log.clear()
    
    def action_quit(self) -> None:
        """Quit the application."""
        if not self.processing_complete and hasattr(self, 'processing_thread'):
            self.log_message("⚠️  Processing in progress. Are you sure you want to quit?")
        self.exit()


def run_textual_ui(config, urls):
    """Run the Textual UI application."""
    app = ClipStitcherApp(config, urls)
    app.run()
