"""CLI entrypoint for DPO Reader."""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from urllib.parse import urlparse

import typer


def _load_dotenv():
    """Load .env file if present (simple implementation, no dependency)."""
    env_file = Path.cwd() / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("\"'")  # Remove quotes
        if key and key not in os.environ:  # Don't override existing
            os.environ[key] = value


_load_dotenv()
import json
import re

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from .audio import format_duration, get_duration, save_wav
from .discourse import Post, Thread, fetch_thread_sync
from .voices import TTSEngine, VoiceAssignment


def _load_thread_from_file(file_path: Path, max_posts: int | None = None) -> Thread:
    """Load a thread from a local JSON file (Discourse format)."""
    data = json.loads(file_path.read_text())

    posts = []
    for p in data["post_stream"]["posts"]:
        # Strip HTML tags
        content = p.get("cooked", "")
        content = re.sub(r"<[^>]+>", "", content).strip()

        posts.append(
            Post(
                id=p["id"],
                number=p["post_number"],
                author=p.get("name") or p["username"],
                username=p["username"],
                content=content,
                created_at=p.get("created_at", ""),
            )
        )

    if max_posts:
        posts = posts[:max_posts]

    return Thread(
        id=data["id"],
        title=data["title"],
        url=data.get("url", "file://local"),
        posts=posts,
    )


app = typer.Typer(
    name="dpo-reader",
    help="Convert Discourse threads to multi-voice audio.\n\nUsage: dpo-reader listen URL [-o output.wav]",
    no_args_is_help=True,
)
console = Console()


def get_base_url(url: str) -> str:
    """Extract base URL from thread URL."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def parse_post_number_from_url(url: str) -> int | None:
    """Extract post number from Discourse URL if present.

    URLs like /t/topic-slug/12345/17 have post number 17.
    URLs like /t/topic-slug/12345 have no post number.
    """
    parsed = urlparse(url)
    parts = parsed.path.rstrip("/").split("/")

    # Format: /t/slug/topic_id[/post_number]
    # Minimum parts: ['', 't', 'slug', 'topic_id']
    if len(parts) >= 5 and parts[1] == "t":
        try:
            return int(parts[4])
        except ValueError:
            pass
    return None


def user_link(base_url: str, username: str, display: str | None = None) -> str:
    """Create Rich markup for a clickable user link."""
    display = display or f"@{username}"
    return f"[link={base_url}/u/{username}]{display}[/link]"


def post_link(base_url: str, topic_id: int, post_number: int, display: str | None = None) -> str:
    """Create Rich markup for a clickable post link."""
    display = display or f"#{post_number}"
    return f"[link={base_url}/t/{topic_id}/{post_number}]{display}[/link]"


def title_link(url: str, title: str) -> str:
    """Create Rich markup for a clickable title link."""
    return f"[link={url}]{title}[/link]"


class Engine(str, Enum):
    """TTS engine choices."""

    bark = "bark"
    openai = "openai"
    piper = "piper"


def get_backend(engine: Engine):
    """Get TTS backend instance."""
    if engine == Engine.openai:
        try:
            from .tts import OpenAIBackend

            return OpenAIBackend()
        except ValueError as e:
            # Missing API key
            console.print(f"[red]Error:[/red] {e}")
            raise SystemExit(1) from e

    if engine == Engine.bark:
        try:
            from .tts import BarkBackend

            return BarkBackend()
        except ModuleNotFoundError as e:
            if "bark" in str(e):
                console.print(
                    "[red]Error:[/red] Bark TTS not installed.\n"
                    "Install with: [cyan]uv pip install dpo-reader[bark][/cyan]\n"
                    "Or use OpenAI: [cyan]dpo-reader listen URL -e openai[/cyan]"
                )
                raise SystemExit(1) from e
            raise

    # Default: piper
    try:
        from .tts import PiperBackend

        return PiperBackend()
    except ModuleNotFoundError as e:
        if "piper" in str(e):
            console.print(
                "[red]Error:[/red] Piper TTS not installed.\n"
                "Install with: [cyan]uv pip install dpo-reader[piper][/cyan]\n"
                "Or use Bark: [cyan]dpo-reader listen URL -e bark[/cyan]"
            )
            raise SystemExit(1) from e
        raise


@app.command()
def listen(
    url: str = typer.Argument("", help="Discourse thread URL (not needed with --file)"),
    output: Path = typer.Option(
        Path("output.wav"),
        "--output",
        "-o",
        help="Output audio file path",
    ),
    engine: Engine = typer.Option(
        Engine.bark,
        "--engine",
        "-e",
        help="TTS engine: openai (best, needs API key), bark (good, local), piper (fast, CPU)",
    ),
    max_posts: int | None = typer.Option(
        None,
        "--max-posts",
        "-n",
        help="Maximum number of posts to convert (default: all)",
    ),
    no_attribution: bool = typer.Option(
        False,
        "--no-attribution",
        help="Don't include 'Author says:' prefix",
    ),
    cache_dir: Path | None = typer.Option(
        None,
        "--cache-dir",
        "-c",
        help="Directory to cache generated audio chunks",
    ),
    pause: float = typer.Option(
        1.5,
        "--pause",
        "-p",
        help="Pause duration between posts (seconds)",
    ),
    no_play: bool = typer.Option(
        False,
        "--no-play",
        help="Don't auto-play after generating",
    ),
    ui: bool = typer.Option(
        False,
        "--ui",
        help="Launch interactive Textual TUI player with controls",
    ),
    file: Path | None = typer.Option(
        None,
        "--file",
        "-f",
        help="Load thread from local JSON file instead of URL (for testing)",
    ),
    start_post: int | None = typer.Option(
        None,
        "--start-post",
        "-s",
        help="Start from this post number (auto-detected from URL if present)",
    ),
) -> None:
    """Convert a Discourse thread to audio and play it."""
    # Validate inputs
    if not file and not url:
        console.print("[red]Error:[/red] Provide a URL or use --file to load from JSON")
        raise typer.Exit(1)

    # Auto-detect post number from URL if not explicitly provided
    if url and start_post is None:
        start_post = parse_post_number_from_url(url)

    console.print("\n[bold blue]DPO Reader[/bold blue] - Discourse to Audio\n")

    # Fetch thread (from file or URL)
    if file:
        with console.status("[bold green]Loading from file..."):
            try:
                thread = _load_thread_from_file(file, max_posts=max_posts)
            except Exception as e:
                console.print(f"[bold red]Error loading file:[/bold red] {e}")
                raise typer.Exit(1)
        base_url = "https://example.com"
    else:
        with console.status("[bold green]Fetching thread..."):
            try:
                thread = fetch_thread_sync(url, max_posts=max_posts)
            except Exception as e:
                console.print(f"[bold red]Error fetching thread:[/bold red] {e}")
                raise typer.Exit(1)
        base_url = get_base_url(url)

    # Filter posts by start_post if specified
    original_count = len(thread.posts)
    if start_post is not None:
        thread.posts = [p for p in thread.posts if p.number >= start_post]
        if not thread.posts:
            console.print(f"[red]Error:[/red] No posts found starting from #{start_post}")
            raise typer.Exit(1)

    display_title = title_link(url, thread.title) if url else thread.title
    console.print(f"[green]✓[/green] Loaded: [bold]{display_title}[/bold]")

    # Show post range info
    if start_post is not None:
        console.print(
            f"  Posts: {len(thread.posts)} (#{start_post}→#{thread.posts[-1].number} of {original_count}) | Authors: {len(thread.authors)}"
        )
    else:
        console.print(f"  Posts: {len(thread.posts)} | Authors: {len(thread.authors)}")
    console.print(f"  Engine: [cyan]{engine.value}[/cyan]\n")

    # Map engine enum to TTSEngine
    tts_engine = TTSEngine.BARK if engine == Engine.bark else TTSEngine.PIPER

    # Create voice assignments
    voice_assignment = VoiceAssignment.from_author_counts(
        thread.author_post_counts,
        engine=tts_engine,
    )

    # Show voice assignments table
    table = Table(title="Voice Assignments", show_header=True)
    table.add_column("Author", style="cyan")
    table.add_column("Posts", justify="right", style="green")
    table.add_column("Voice", style="yellow")

    for username, voice_id, desc in voice_assignment.summary():
        posts_count = thread.author_post_counts.get(username, 0)
        table.add_row(user_link(base_url, username, username), str(posts_count), desc)

    console.print(table)
    console.print()

    # Initialize TTS backend
    with console.status(f"[bold green]Loading {engine.value} models..."):
        backend = get_backend(engine)

    # Create generator
    from .tts import TTSGenerator

    generator = TTSGenerator(
        backend=backend,
        voice_assignment=voice_assignment,
        cache_dir=cache_dir,
        include_attribution=not no_attribution,
        pause_between_posts=pause,
    )

    # Launch streaming TUI player if requested (generates in background)
    if ui:
        from .player import run_streaming_player

        console.print("[cyan]Launching player (generating audio in background)...[/cyan]\n")
        run_streaming_player(thread, generator, backend.sample_rate)
        return

    # Otherwise, generate all audio first
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Generating audio...", total=len(thread.posts))

        def on_progress(current: int, total: int, post):
            progress.update(task, completed=current, description=f"[cyan]Post {current}/{total} by {post.username}")

        result = generator.generate_all(thread.posts, progress_callback=on_progress, return_segments=False)
        audio = result[0] if isinstance(result, tuple) else result

    # Save output
    save_wav(audio, output, sample_rate=backend.sample_rate)

    duration = get_duration(audio, backend.sample_rate)
    console.print(f"\n[green]✓[/green] Saved: [bold]{output}[/bold]")
    console.print(f"  Duration: {format_duration(duration)}")
    console.print(f"  Size: {output.stat().st_size / (1024 * 1024):.1f} MB\n")

    # Auto-play unless disabled
    if not no_play:
        import platform
        import subprocess

        console.print("[cyan]Playing audio...[/cyan] (Ctrl+C to stop)\n")
        try:
            system = platform.system()
            if system == "Darwin":
                subprocess.run(["afplay", str(output)], check=True)
            elif system == "Linux":
                # Try paplay first (PulseAudio), fall back to aplay
                try:
                    subprocess.run(["paplay", str(output)], check=True)
                except FileNotFoundError:
                    subprocess.run(["aplay", str(output)], check=True)
            elif system == "Windows":
                subprocess.run(
                    ["powershell", "-c", f"(New-Object Media.SoundPlayer '{output}').PlaySync()"],
                    check=True,
                )
        except KeyboardInterrupt:
            console.print("\n[yellow]Playback stopped.[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Could not auto-play:[/yellow] {e}")
            console.print(f"  Play manually: [bold]afplay {output}[/bold]")


@app.command(name="export")
def export_audio(
    url: str = typer.Argument(..., help="Discourse thread URL"),
    output: Path = typer.Option(
        Path("output.wav"),
        "--output",
        "-o",
        help="Output audio file path",
    ),
    engine: Engine = typer.Option(
        Engine.bark,
        "--engine",
        "-e",
        help="TTS engine: openai (best, needs API key), bark (good, local), piper (fast, CPU)",
    ),
    max_posts: int | None = typer.Option(
        None,
        "--max-posts",
        "-n",
        help="Maximum number of posts to convert (default: all)",
    ),
    no_attribution: bool = typer.Option(
        False,
        "--no-attribution",
        help="Don't include 'Author says:' prefix",
    ),
    cache_dir: Path | None = typer.Option(
        None,
        "--cache-dir",
        "-c",
        help="Directory to cache generated audio chunks",
    ),
    pause: float = typer.Option(
        1.5,
        "--pause",
        "-p",
        help="Pause duration between posts (seconds)",
    ),
) -> None:
    """Export a Discourse thread to audio file (no auto-play)."""
    # Call listen with no_play=True
    listen(
        url=url,
        output=output,
        engine=engine,
        max_posts=max_posts,
        no_attribution=no_attribution,
        cache_dir=cache_dir,
        pause=pause,
        no_play=True,
    )


@app.command()
def info(
    url: str = typer.Argument(..., help="Discourse thread URL"),
    max_posts: int | None = typer.Option(
        None,
        "--max-posts",
        "-n",
        help="Maximum number of posts to analyze",
    ),
) -> None:
    """Show information about a Discourse thread without generating audio."""
    console.print("\n[bold blue]DPO Reader[/bold blue] - Thread Info\n")

    with console.status("[bold green]Fetching thread..."):
        try:
            thread = fetch_thread_sync(url, max_posts=max_posts)
        except Exception as e:
            console.print(f"[bold red]Error fetching thread:[/bold red] {e}")
            raise typer.Exit(1)

    base_url = get_base_url(url)
    console.print(f"[bold]Title:[/bold] {title_link(url, thread.title)}")
    console.print(f"[bold]URL:[/bold] [link={thread.url}]{thread.url}[/link]")
    console.print(f"[bold]Posts:[/bold] {len(thread.posts)}")
    console.print(f"[bold]Unique Authors:[/bold] {len(thread.authors)}\n")

    # Author stats
    table = Table(title="Authors by Activity", show_header=True)
    table.add_column("Author", style="cyan")
    table.add_column("Username", style="dim")
    table.add_column("Posts", justify="right", style="green")
    table.add_column("% of Thread", justify="right", style="yellow")

    author_names = {}
    for post in thread.posts:
        author_names[post.username] = post.author

    total_posts = len(thread.posts)
    for username, count in list(thread.author_post_counts.items())[:20]:
        name = author_names.get(username, username)
        pct = (count / total_posts) * 100
        table.add_row(name, user_link(base_url, username), str(count), f"{pct:.1f}%")

    console.print(table)

    if len(thread.authors) > 20:
        console.print(f"\n[dim]...and {len(thread.authors) - 20} more authors[/dim]")

    total_chars = sum(len(p.content) for p in thread.posts)
    est_words = total_chars / 5
    est_minutes = est_words / 150
    console.print(f"\n[bold]Estimated Duration:[/bold] ~{format_duration(est_minutes * 60)}")
    console.print("[dim](Based on ~150 words/minute speech rate)[/dim]\n")


@app.command()
def preview(
    url: str = typer.Argument(..., help="Discourse thread URL"),
    posts: int = typer.Option(
        3,
        "--posts",
        "-n",
        help="Number of posts to preview",
    ),
) -> None:
    """Preview the first few posts of a thread."""
    console.print("\n[bold blue]DPO Reader[/bold blue] - Thread Preview\n")

    with console.status("[bold green]Fetching thread..."):
        try:
            thread = fetch_thread_sync(url, max_posts=posts)
        except Exception as e:
            console.print(f"[bold red]Error fetching thread:[/bold red] {e}")
            raise typer.Exit(1)

    base_url = get_base_url(url)
    console.print(f"[bold]{title_link(url, thread.title)}[/bold]\n")

    for post in thread.posts:
        post_num = post_link(base_url, thread.id, post.number)
        author = user_link(base_url, post.username, post.author)
        username = user_link(base_url, post.username)
        console.print(f"[cyan]{post_num}[/cyan] [bold]{author}[/bold] ({username})")
        content = post.content
        if len(content) > 500:
            content = content[:500] + "..."
        console.print(f"  {content}\n")


if __name__ == "__main__":
    app()
