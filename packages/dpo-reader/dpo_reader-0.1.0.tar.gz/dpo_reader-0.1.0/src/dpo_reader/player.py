"""Textual TUI audio player with playback controls."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

import numpy as np
import sounddevice as sd
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Footer, Header, ProgressBar, Static

if TYPE_CHECKING:
    from .discourse import Thread


@dataclass
class PostSegment:
    """Audio segment for a single post."""

    post_number: int
    author: str
    username: str
    start_sample: int
    end_sample: int
    content_preview: str
    content: str = ""  # Full content for read-along display
    attribution_samples: int = 0  # Samples used for "Author says:" portion


class AudioBuffer:
    """Thread-safe audio buffer that supports appending while playing."""

    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self._chunks: list[np.ndarray] = []
        self._total_samples = 0
        self._lock = threading.Lock()
        self.generation_complete = False

    def append(self, audio: np.ndarray) -> None:
        """Append audio chunk to buffer."""
        with self._lock:
            self._chunks.append(audio)
            self._total_samples += len(audio)

    def get_samples(self, start: int, length: int) -> np.ndarray | None:
        """Get samples from buffer. Returns None if not enough data."""
        with self._lock:
            if start + length > self._total_samples:
                return None  # Not enough buffered

            # Find which chunks contain our range
            result = np.zeros(length, dtype=np.float32)
            chunk_start = 0
            result_pos = 0

            for chunk in self._chunks:
                chunk_end = chunk_start + len(chunk)

                if chunk_end <= start:
                    chunk_start = chunk_end
                    continue

                if chunk_start >= start + length:
                    break

                # Calculate overlap
                src_start = max(0, start - chunk_start)
                src_end = min(len(chunk), start + length - chunk_start)
                dst_start = max(0, chunk_start - start)
                copy_len = src_end - src_start

                result[dst_start : dst_start + copy_len] = chunk[src_start:src_end]
                result_pos += copy_len
                chunk_start = chunk_end

            return result

    @property
    def total_samples(self) -> int:
        with self._lock:
            return self._total_samples

    @property
    def duration(self) -> float:
        return self.total_samples / self.sample_rate


class AudioPlayer:
    """Audio player with speed control and seeking, supports streaming buffer."""

    def __init__(self, audio: np.ndarray | None = None, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self.position = 0  # Current sample position
        self.speed = 1.0
        self.playing = False
        self.stream: sd.OutputStream | None = None
        self._lock = threading.Lock()
        self.buffering = False  # True when waiting for more data

        # Support both static audio and streaming buffer
        if audio is not None:
            self.audio = audio
            self.buffer: AudioBuffer | None = None
        else:
            self.audio = np.zeros(0, dtype=np.float32)
            self.buffer = AudioBuffer(sample_rate)

    @property
    def duration(self) -> float:
        """Total duration in seconds."""
        if self.buffer:
            return self.buffer.duration
        return len(self.audio) / self.sample_rate

    @property
    def total_samples(self) -> int:
        """Total samples available."""
        if self.buffer:
            return self.buffer.total_samples
        return len(self.audio)

    @property
    def current_time(self) -> float:
        """Current position in seconds."""
        return self.position / self.sample_rate

    @property
    def progress(self) -> float:
        """Progress as 0-1."""
        total = self.total_samples
        if total == 0:
            return 0
        return self.position / total

    @property
    def buffer_progress(self) -> float:
        """How much is buffered as 0-1 (for streaming mode)."""
        if not self.buffer or self.buffer.generation_complete:
            return 1.0
        # This would need total expected samples - for now return based on position
        return 1.0

    def append_audio(self, audio: np.ndarray) -> None:
        """Append audio to streaming buffer."""
        if self.buffer:
            self.buffer.append(audio)

    def _audio_callback(self, outdata, frames, _time_info, _status):
        """Sounddevice callback for audio output."""
        with self._lock:
            if not self.playing:
                outdata.fill(0)
                return

            # Calculate how many source samples we need based on speed
            source_frames = int(frames * self.speed)

            # Get audio data (from buffer or static array)
            if self.buffer:
                chunk = self.buffer.get_samples(self.position, source_frames)
                if chunk is None:
                    # Buffer underrun - not enough data
                    outdata.fill(0)
                    self.buffering = True
                    if self.buffer.generation_complete:
                        self.playing = False  # Reached end
                    return
                self.buffering = False
            else:
                end_pos = min(self.position + source_frames, len(self.audio))
                chunk = self.audio[self.position : end_pos]
                if len(chunk) == 0:
                    outdata.fill(0)
                    self.playing = False
                    return

            # Resample for speed change
            if self.speed != 1.0 and len(chunk) > 0:
                indices = np.linspace(0, len(chunk) - 1, frames).astype(int)
                indices = np.clip(indices, 0, len(chunk) - 1)
                resampled = chunk[indices]
            else:
                resampled = chunk
                if len(resampled) < frames:
                    resampled = np.pad(resampled, (0, frames - len(resampled)))

            outdata[:, 0] = resampled[:frames]
            self.position += len(chunk)

    def play(self):
        """Start playback."""
        if self.stream is None:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=1,
                callback=self._audio_callback,
                blocksize=2048,
            )
            self.stream.start()
        self.playing = True

    def pause(self):
        """Pause playback."""
        self.playing = False

    def toggle(self):
        """Toggle play/pause."""
        if self.playing:
            self.pause()
        else:
            self.play()

    def seek(self, seconds: float):
        """Seek to position in seconds."""
        with self._lock:
            self.position = int(seconds * self.sample_rate)
            max_pos = self.total_samples - 1 if self.total_samples > 0 else 0
            self.position = max(0, min(self.position, max_pos))

    def skip(self, seconds: float):
        """Skip forward/backward by seconds."""
        with self._lock:
            self.position += int(seconds * self.sample_rate)
            max_pos = self.total_samples - 1 if self.total_samples > 0 else 0
            self.position = max(0, min(self.position, max_pos))

    def set_speed(self, speed: float):
        """Set playback speed (0.5 to 2.0)."""
        self.speed = max(0.5, min(2.0, speed))

    def stop(self):
        """Stop and cleanup."""
        self.playing = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None


class PostList(Static):
    """Widget showing list of posts with current highlight."""

    def __init__(self, thread: Thread, segments: list[PostSegment]):
        super().__init__("")
        self.thread = thread
        self.segments = segments
        self.current_index = 0
        self._last_index: int | None = None
        self._last_segment_count = 0

    def update_current(self, index: int):
        """Update which post is currently playing."""
        segments_changed = len(self.segments) != self._last_segment_count
        index_changed = self.current_index != index

        self.current_index = index
        self._last_segment_count = len(self.segments)

        if segments_changed or index_changed:
            self._last_index = index
            self.update(self._build_content())
        else:
            self.refresh()

    def _build_content(self) -> str:
        """Generate the content string."""
        lines = [f"[bold]{self.thread.title}[/bold]"]
        lines.append(f"[dim]{len(self.thread.posts)} posts • {len(self.thread.authors)} authors[/dim]\n")

        for i, seg in enumerate(self.segments):
            prefix = "[cyan]▶[/cyan] " if i == self.current_index else "  "
            style = "bold cyan" if i == self.current_index else "dim"
            lines.append(f"{prefix}[{style}]#{seg.post_number} {seg.author}[/{style}]")

        return "\n".join(lines)

    def render(self) -> str:
        return self._build_content()


class ReadAlongText(Static):
    """Widget showing current post text with section highlighting."""

    def __init__(self):
        super().__init__("")
        self.segment: PostSegment | None = None
        self.in_attribution: bool = True  # True = narrator speaking, False = content
        self._last_post_number: int | None = None

    def update_segment(self, segment: PostSegment, samples_into_segment: int):
        """Update the displayed segment and which section is playing."""
        changed = self.segment is None or self.segment.post_number != segment.post_number
        self.segment = segment
        # Determine if we're in attribution or content portion
        self.in_attribution = samples_into_segment < segment.attribution_samples

        if changed:
            # Force full re-render on post change
            self._last_post_number = segment.post_number
            content = self._build_content()
            self.update(content)
        else:
            self.refresh()

    def _build_content(self) -> str:
        """Generate the content string."""
        if not self.segment:
            return "[dim]Waiting for audio...[/dim]"

        # Header with post number
        header = f"[bold cyan]#{self.segment.post_number}[/bold cyan]\n"
        header += "─" * 60 + "\n\n"

        content = self.segment.content or self.segment.content_preview
        attribution = f"{self.segment.author} says:"

        if self.in_attribution:
            return header + f"[bold yellow]{attribution}[/bold yellow] [dim]{content}[/dim]"
        return header + f"[cyan]{attribution}[/cyan] {content}"

    def render(self) -> str:
        return self._build_content()


class PlayerControls(Static):
    """Widget showing playback controls and status."""

    def __init__(self, player: AudioPlayer):
        super().__init__()
        self.player = player

    def render(self) -> str:
        # Determine status based on state
        if self.player.buffer and self.player.total_samples == 0:
            # No audio yet - still generating first post
            status = "[bold cyan]Generating first post...[/bold cyan]"
        elif self.player.buffering:
            status = "[bold yellow]Buffering...[/bold yellow]"
        elif self.player.playing:
            status = "[green]Playing[/green]"
        else:
            status = "[yellow]Paused[/yellow]"

        time_str = self._format_time(self.player.current_time)
        duration_str = self._format_time(self.player.duration)
        speed_str = f"{self.player.speed:.1f}x"

        # Show generation progress if streaming
        gen_status = ""
        if self.player.buffer and not self.player.buffer.generation_complete:
            gen_status = "  [dim](generating more...)[/dim]"

        return f"""
{status}  {time_str} / {duration_str}  Speed: {speed_str}{gen_status}

Space Play/Pause  ←/→ Skip  ↑/↓ Speed  n/p Post  q Quit
"""

    @staticmethod
    def _format_time(seconds: float) -> str:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}:{secs:02d}"


class StreamingPlayerControls(Static):
    """Widget showing playback controls and generation progress."""

    def __init__(self, app_ref):
        super().__init__()
        self.app_ref = app_ref

    def render(self) -> str:
        player = self.app_ref.player

        # Determine status based on state
        if player.buffer and player.total_samples == 0:
            # No audio yet - still generating first post
            author = self.app_ref.generating_post_author or "..."
            status = f"[bold cyan]Generating: {author}[/bold cyan]"
        elif player.buffering:
            status = "[bold yellow]Buffering...[/bold yellow]"
        elif player.playing:
            status = "[green]Playing[/green]"
        else:
            status = "[yellow]Paused[/yellow]"

        time_str = self._format_time(player.current_time)
        duration_str = self._format_time(player.duration)
        speed_str = f"{player.speed:.1f}x"

        # Show generation progress
        gen_status = ""
        if not self.app_ref.generation_complete:
            gen_status = f"  [cyan]Gen: {self.app_ref.posts_generated}/{self.app_ref.total_posts}[/cyan]"

        return f"""
{status}  {time_str} / {duration_str}  Speed: {speed_str}{gen_status}

Space Play/Pause  ←/→ Skip  ↑/↓ Speed  n/p Post  l Logs  q Quit
"""

    @staticmethod
    def _format_time(seconds: float) -> str:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}:{secs:02d}"


class DPOPlayerApp(App):
    """Textual app for playing DPO audio with controls."""

    CSS = """
    Screen {
        layout: vertical;
        background: $background;
    }
    #main {
        layout: horizontal;
        height: 1fr;
        background: $background;
    }
    #posts {
        width: 30%;
        border: solid $primary;
        padding: 1;
        overflow-y: auto;
        background: $surface;
    }
    #read-along {
        width: 70%;
        border: solid $secondary;
        padding: 1 2;
        overflow-y: auto;
        background: $surface;
    }
    ReadAlongText {
        background: $surface;
        width: 100%;
        height: auto;
    }
    PostList {
        background: $surface;
        width: 100%;
        height: auto;
    }
    #progress-container {
        height: 5;
        padding: 1 2;
        width: 100%;
        background: $background;
    }
    #controls {
        height: 5;
        padding: 1;
        background: $surface;
    }
    PlayerControls {
        background: $surface;
        width: 100%;
    }
    ProgressBar {
        width: 100%;
        height: 3;
    }
    Bar {
        width: 100%;
    }
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("space", "toggle_play", "Play/Pause"),
        Binding("left", "skip_back", "Back 5s"),
        Binding("right", "skip_forward", "Forward 5s"),
        Binding("up", "speed_up", "Speed Up"),
        Binding("down", "speed_down", "Speed Down"),
        Binding("n", "next_post", "Next Post"),
        Binding("p", "prev_post", "Prev Post"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        audio: np.ndarray,
        sample_rate: int,
        thread: Thread,
        segments: list[PostSegment],
    ):
        super().__init__()
        self.audio = audio
        self.sample_rate = sample_rate
        self.thread = thread
        self.segments = segments
        self.player = AudioPlayer(audio, sample_rate)
        self.current_segment_index = 0

    def compose(self) -> ComposeResult:
        from textual.containers import Horizontal

        yield Header()
        yield Horizontal(
            Container(PostList(self.thread, self.segments), id="posts"),
            Container(ReadAlongText(), id="read-along"),
            id="main",
        )
        yield Container(
            ProgressBar(total=100, show_eta=False),
            id="progress-container",
        )
        yield PlayerControls(self.player)
        yield Footer()

    def on_mount(self) -> None:
        """Start playback and update loop when mounted."""
        self.player.play()
        self.update_loop()

    @work(exclusive=True)
    async def update_loop(self) -> None:
        """Update UI periodically."""
        import asyncio

        while True:
            # Update progress bar
            progress_bar = self.query_one(ProgressBar)
            progress_bar.progress = self.player.progress * 100

            # Update current segment
            self._update_current_segment()

            # Update controls display
            controls = self.query_one(PlayerControls)
            controls.refresh()

            # Update post list
            posts = self.query_one(PostList)
            posts.update_current(self.current_segment_index)

            # Update read-along text with position within current segment
            read_along = self.query_one(ReadAlongText)
            if self.segments:
                seg = self.segments[self.current_segment_index]
                # Calculate samples into this segment
                samples_into_segment = self.player.position - seg.start_sample
                read_along.update_segment(seg, samples_into_segment)

            await asyncio.sleep(0.1)

    def _update_current_segment(self) -> None:
        """Update which segment is currently playing."""
        self.current_segment_index = self._get_segment_index()

    def _get_segment_index(self) -> int:
        """Get current segment index based on playback position."""
        if not self.segments:
            return 0

        pos = self.player.position

        # Check each segment
        for i, seg in enumerate(self.segments):
            if seg.start_sample <= pos < seg.end_sample:
                return i

        # Position is in pause between segments or beyond - find closest
        # If before first segment, return 0
        if pos < self.segments[0].start_sample:
            return 0

        # If after last segment ends, return last
        if pos >= self.segments[-1].end_sample:
            return len(self.segments) - 1

        # Must be in a pause between segments - find which one we're closer to
        for i in range(len(self.segments) - 1):
            if self.segments[i].end_sample <= pos < self.segments[i + 1].start_sample:
                return i  # Still on the segment we just finished

        return 0

    def action_toggle_play(self) -> None:
        """Toggle play/pause."""
        self.player.toggle()

    def action_skip_back(self) -> None:
        """Skip back 5 seconds."""
        self.player.skip(-5)

    def action_skip_forward(self) -> None:
        """Skip forward 5 seconds."""
        self.player.skip(5)

    def action_speed_up(self) -> None:
        """Increase playback speed."""
        self.player.set_speed(self.player.speed + 0.1)

    def action_speed_down(self) -> None:
        """Decrease playback speed."""
        self.player.set_speed(self.player.speed - 0.1)

    def action_next_post(self) -> None:
        """Jump to next post."""
        idx = self._get_segment_index()
        if idx < len(self.segments) - 1:
            next_seg = self.segments[idx + 1]
            self.player.seek(next_seg.start_sample / self.sample_rate)

    def action_prev_post(self) -> None:
        """Jump to previous post."""
        idx = self._get_segment_index()
        if idx > 0:
            prev_seg = self.segments[idx - 1]
            self.player.seek(prev_seg.start_sample / self.sample_rate)

    async def action_quit(self) -> None:
        """Quit the app."""
        self.player.stop()
        self.exit()


def run_player(
    audio: np.ndarray,
    sample_rate: int,
    thread: Thread,
    segments: list[PostSegment],
) -> None:
    """Run the Textual player app."""
    app = DPOPlayerApp(audio, sample_rate, thread, segments)
    app.run()


class LogPanel(Static):
    """Widget showing log messages."""

    def __init__(self):
        super().__init__()
        self.logs: list[str] = []

    def add_log(self, message: str):
        """Add a log message."""
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[dim]{timestamp}[/dim] {message}")
        if len(self.logs) > 100:  # Keep last 100 logs
            self.logs = self.logs[-100:]
        self.refresh()

    def render(self) -> str:
        if not self.logs:
            return "[dim]No logs yet. Press 'l' to hide.[/dim]"
        return "\n".join(self.logs[-20:])  # Show last 20


class StreamingPlayerApp(App):
    """Textual app that generates audio in background and starts playing early."""

    CSS = """
    Screen {
        layout: vertical;
        background: #1e1e2e;
    }
    #main {
        layout: horizontal;
        height: 1fr;
        background: #1e1e2e;
    }
    #posts {
        width: 30%;
        border: solid $primary;
        padding: 1;
        overflow: hidden auto;
        background: #313244;
    }
    #read-along {
        width: 70%;
        border: solid $secondary;
        padding: 1 2;
        overflow: hidden auto;
        background: #313244;
    }
    ReadAlongText {
        background: #313244;
        width: 100%;
        height: auto;
        overflow: hidden;
    }
    PostList {
        background: #313244;
        width: 100%;
        height: auto;
        overflow: hidden;
    }
    #log-panel {
        height: 12;
        border: solid $error;
        padding: 1;
        overflow: hidden auto;
        display: none;
        background: #313244;
    }
    #log-panel.visible {
        display: block;
    }
    LogPanel {
        background: #313244;
        overflow: hidden;
    }
    #progress-container {
        height: 5;
        padding: 1 2;
        width: 100%;
        background: #1e1e2e;
    }
    StreamingPlayerControls {
        background: #313244;
        width: 100%;
        height: auto;
        overflow: hidden;
    }
    ProgressBar {
        width: 100%;
        height: 3;
    }
    Bar {
        width: 100%;
    }
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("space", "toggle_play", "Play/Pause"),
        Binding("left", "skip_back", "Back 5s"),
        Binding("right", "skip_forward", "Forward 5s"),
        Binding("up", "speed_up", "Speed Up"),
        Binding("down", "speed_down", "Speed Down"),
        Binding("n", "next_post", "Next Post"),
        Binding("p", "prev_post", "Prev Post"),
        Binding("l", "toggle_logs", "Logs"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        thread: Thread,
        generator,  # TTSGenerator
        sample_rate: int,
    ):
        super().__init__()
        self.thread = thread
        self.generator = generator
        self.sample_rate = sample_rate
        self.player = AudioPlayer(audio=None, sample_rate=sample_rate)  # Streaming mode
        self.segments: list[PostSegment] = []
        self.current_segment_index = 0
        self.generation_complete = False
        self.posts_generated = 0
        self.total_posts = len(thread.posts)
        self.generating_post_author = ""  # Currently generating author
        self._gen_thread: threading.Thread | None = None
        self.show_logs = False

    def compose(self) -> ComposeResult:
        from textual.containers import Horizontal

        yield Header()
        yield Horizontal(
            Container(PostList(self.thread, self.segments), id="posts"),
            Container(ReadAlongText(), id="read-along"),
            id="main",
        )
        yield Container(LogPanel(), id="log-panel")
        yield Container(
            ProgressBar(total=100, show_eta=False),
            id="progress-container",
        )
        yield StreamingPlayerControls(self)
        yield Footer()

    def on_mount(self) -> None:
        """Start generation thread and update loop."""
        # Set initial generating author
        if self.thread.posts:
            self.generating_post_author = self.thread.posts[0].author
        self._gen_thread = threading.Thread(target=self._generate_audio, daemon=True)
        self._gen_thread.start()
        self.update_loop()

    def _log_msg(self, message: str):
        """Add log message (thread-safe call to UI)."""
        self.call_from_thread(self._add_log_message, message)

    def _add_log_message(self, message: str):
        """Add message to log panel."""
        try:
            log_panel = self.query_one("#log-panel LogPanel", LogPanel)
            log_panel.add_log(message)
        except Exception:
            pass

    def _generate_audio(self) -> None:
        """Generate audio in background thread."""
        try:
            # Log what we're about to generate
            self._log_msg(f"Starting generation of {self.total_posts} posts...")

            for audio_chunk, seg_info, idx, total in self.generator.generate_streaming(self.thread.posts):
                # Update status for next post (if not last)
                if idx + 1 < total:
                    next_post = self.thread.posts[idx + 1]
                    self.generating_post_author = next_post.author
                else:
                    self.generating_post_author = ""

                # Log completion
                self._log_msg(f"[green]✓[/green] Post {idx + 1}/{total}: {seg_info['author']}")

                # Add audio to buffer
                self.player.append_audio(audio_chunk)

                # Create segment and add to list
                segment = PostSegment(
                    post_number=seg_info["post_number"],
                    author=seg_info["author"],
                    username=seg_info["username"],
                    start_sample=seg_info["start_sample"],
                    end_sample=seg_info["end_sample"],
                    content_preview=seg_info["content_preview"],
                    content=seg_info["content"],
                    attribution_samples=seg_info["attribution_samples"],
                )
                self.segments.append(segment)
                self.posts_generated = idx + 1

                # Auto-start playback once first post is ready
                if idx == 0:
                    self.player.play()
                    self._log_msg("[green]▶ Playback started[/green]")

            # Mark generation complete
            self.generation_complete = True
            if self.player.buffer:
                self.player.buffer.generation_complete = True
            self._log_msg("[bold green]✓ All posts generated![/bold green]")

        except Exception as e:
            self._log_msg(f"[bold red]✗ Error:[/bold red] {e}")
            import traceback

            self._log_msg(f"[dim]{traceback.format_exc()[:200]}[/dim]")
            self.generation_complete = True

    @work(exclusive=True)
    async def update_loop(self) -> None:
        """Update UI periodically."""
        import asyncio

        while True:
            # Update progress bar (generation progress)
            progress_bar = self.query_one(ProgressBar)
            if self.total_posts > 0:
                gen_pct = (self.posts_generated / self.total_posts) * 100
                progress_bar.progress = gen_pct

            # Update current segment
            if self.segments:
                self._update_current_segment()

            # Update controls display
            try:
                controls = self.query_one(StreamingPlayerControls)
                controls.refresh()
            except Exception:
                pass

            # Update post list (may not be mounted yet during startup)
            try:
                posts_widget = self.query_one(PostList)
                posts_widget.segments = self.segments
                posts_widget.update_current(self.current_segment_index)
            except Exception:
                pass

            # Update read-along text
            try:
                read_along = self.query_one(ReadAlongText)
                if self.segments and self.current_segment_index < len(self.segments):
                    seg = self.segments[self.current_segment_index]
                    samples_into_segment = self.player.position - seg.start_sample
                    read_along.update_segment(seg, samples_into_segment)
            except Exception:
                pass

            await asyncio.sleep(0.1)

    def _update_current_segment(self) -> None:
        """Update which segment is currently playing."""
        if not self.segments:
            return
        pos = self.player.position
        for i, seg in enumerate(self.segments):
            if seg.start_sample <= pos < seg.end_sample:
                self.current_segment_index = i
                return
        # If past all segments, stay on last
        if pos >= self.segments[-1].end_sample:
            self.current_segment_index = len(self.segments) - 1

    def action_toggle_play(self) -> None:
        self.player.toggle()

    def action_toggle_logs(self) -> None:
        """Toggle log panel visibility."""
        log_panel = self.query_one("#log-panel")
        self.show_logs = not self.show_logs
        if self.show_logs:
            log_panel.add_class("visible")
        else:
            log_panel.remove_class("visible")

    def action_skip_back(self) -> None:
        self.player.skip(-5)

    def action_skip_forward(self) -> None:
        self.player.skip(5)

    def action_speed_up(self) -> None:
        self.player.set_speed(self.player.speed + 0.1)

    def action_speed_down(self) -> None:
        self.player.set_speed(self.player.speed - 0.1)

    def action_next_post(self) -> None:
        if self.segments and self.current_segment_index < len(self.segments) - 1:
            next_seg = self.segments[self.current_segment_index + 1]
            self.player.seek(next_seg.start_sample / self.sample_rate)

    def action_prev_post(self) -> None:
        if self.segments and self.current_segment_index > 0:
            prev_seg = self.segments[self.current_segment_index - 1]
            self.player.seek(prev_seg.start_sample / self.sample_rate)

    async def action_quit(self) -> None:
        self.player.stop()
        self.exit()


def run_streaming_player(
    thread: Thread,
    generator,  # TTSGenerator
    sample_rate: int,
) -> None:
    """Run the streaming Textual player app."""
    app = StreamingPlayerApp(thread, generator, sample_rate)
    app.run()
