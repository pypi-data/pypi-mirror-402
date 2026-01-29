"""Base TTS backend interface."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from ..discourse import Post
    from ..voices import VoiceAssignment

# Maximum characters per chunk
MAX_CHUNK_CHARS = 250

# Pronunciation fixes: word -> phonetic spelling
# Case-insensitive matching, preserves surrounding context
PRONUNCIATIONS = {
    # Python-specific
    "GIL": "gill",
    "PyPI": "pie pea eye",
    "PyPy": "pie pie",
    "NumPy": "num pie",
    "SciPy": "sigh pie",
    "pytest": "pie test",
    "async": "a-sink",
    "asyncio": "a-sink ee oh",
    "await": "a-wait",
    "kwargs": "keyword args",
    "tuple": "toople",
    "deque": "deck",
    "pygame": "pie game",
    "cpython": "see python",
    "cython": "sigh-thon",
    "ipython": "eye python",
    "jupyter": "jupiter",
    "matplotlib": "mat plot lib",
    "scikit": "sigh kit",
    "sklearn": "sigh kit learn",
    "pytorch": "pie torch",
    "fastapi": "fast A P I",
    "django": "jango",
    "sqlalchemy": "sequel alchemy",
    "pydantic": "pie dantic",
    "mypy": "my pie",
    "pylint": "pie lint",
    "pyenv": "pie env",
    "virtualenv": "virtual env",
    "venv": "v env",
    "pipenv": "pip env",
    "uvicorn": "you vee corn",
    "gunicorn": "green unicorn",
    "aiohttp": "A I O H T T P",
    "httpx": "H T T P X",
    "websockets": "web sockets",
    # Dunder methods
    "__init__": "dunder init",
    "__main__": "dunder main",
    "__name__": "dunder name",
    "__str__": "dunder string",
    "__repr__": "dunder repper",
    "__eq__": "dunder equals",
    "__lt__": "dunder less than",
    "__gt__": "dunder greater than",
    "__len__": "dunder len",
    "__iter__": "dunder iter",
    "__next__": "dunder next",
    "__call__": "dunder call",
    "__enter__": "dunder enter",
    "__exit__": "dunder exit",
    "__getattr__": "dunder get attribute",
    "__setattr__": "dunder set attribute",
    # Unix/shell
    "stdin": "standard in",
    "stdout": "standard out",
    "stderr": "standard error",
    "sudo": "sue doo",
    "chmod": "ch mod",
    "chown": "ch own",
    "mkdir": "make dir",
    "rmdir": "remove dir",
    "grep": "grep",
    "awk": "awk",
    "sed": "sed",
    "xargs": "ex args",
    "cron": "kron",
    "crontab": "kron tab",
    "systemd": "system d",
    "systemctl": "system control",
    "journalctl": "journal control",
    # Web/servers
    "nginx": "engine x",
    "apache": "a patch ee",
    "wsgi": "whiskey",
    "asgi": "az gee",
    "CORS": "cores",
    "REST": "rest",
    "GraphQL": "graph Q L",
    "gRPC": "gee R P C",
    "OAuth": "oh auth",
    "JWT": "jot",
    # Data formats
    "JSON": "jason",
    "YAML": "yammel",
    "TOML": "tom el",
    "XML": "X M L",
    "HTML": "H T M L",
    "CSS": "C S S",
    "SQL": "sequel",
    "MySQL": "my sequel",
    "PostgreSQL": "post gres",
    "SQLite": "sequel lite",
    "NoSQL": "no sequel",
    "MongoDB": "mongo D B",
    "Redis": "reddis",
    # JavaScript/Node ecosystem
    "npm": "N P M",
    "npx": "N P X",
    "pnpm": "P N P M",
    "deno": "dee no",
    "jsx": "J S X",
    "tsx": "T S X",
    "vite": "veet",
    "webpack": "web pack",
    "esbuild": "E S build",
    "eslint": "E S lint",
    "nextjs": "next J S",
    "nodejs": "node J S",
    "vuejs": "view J S",
    "reactjs": "react J S",
    "svelte": "svelt",
    # DevOps/Cloud
    "kubectl": "kube control",
    "k8s": "kubernetes",
    "CI/CD": "C I C D",
    "DevOps": "dev ops",
    "GitOps": "git ops",
    "terraform": "terra form",
    "ansible": "ansi-ble",
    "dockerfile": "docker file",
    "docker-compose": "docker compose",
    "AWS": "A W S",
    "GCP": "G C P",
    "S3": "S three",
    "EC2": "E C two",
    "IAM": "I am",
    "VPC": "V P C",
    "ECS": "E C S",
    "EKS": "E K S",
    "RDS": "R D S",
    "SQS": "S Q S",
    "SNS": "S N S",
    "CDN": "C D N",
    # Networking
    "TCP": "T C P",
    "UDP": "U D P",
    "HTTP": "H T T P",
    "HTTPS": "H T T P S",
    "SSH": "S S H",
    "SSL": "S S L",
    "TLS": "T L S",
    "DNS": "D N S",
    "IP": "I P",
    "IPv4": "I P version four",
    "IPv6": "I P version six",
    "localhost": "local host",
    # General programming
    "CLI": "command line",
    "API": "A P I",
    "GUI": "gooey",
    "URL": "U R L",
    "URI": "U R I",
    "UUID": "you id",
    "GUID": "gwid",
    "IDE": "I D E",
    "regex": "redge ex",
    "segfault": "seg fault",
    "malloc": "mal ock",
    "realloc": "re al ock",
    "sizeof": "size of",
    "typedef": "type def",
    "ifdef": "if def",
    "ifndef": "if not def",
    "endif": "end if",
    "elif": "else if",
    "REPL": "repple",
    "LLVM": "L L V M",
    "WASM": "waz em",
    "WebAssembly": "web assembly",
    "FFI": "F F I",
    "ABI": "A B I",
    "ORM": "O R M",
    "MVC": "M V C",
    "MVVM": "M V V M",
    "CRUD": "crud",
    "FIFO": "fife oh",
    "LIFO": "life oh",
    # Git
    "GitHub": "git hub",
    "GitLab": "git lab",
    "gitignore": "git ignore",
    "gitconfig": "git config",
    "rebase": "re-base",
    "reflog": "ref log",
    # Discourse/forum
    "OP": "original poster",
    "TL;DR": "too long didn't read",
    "TLDR": "too long didn't read",
    "IMHO": "in my humble opinion",
    "IIRC": "if I recall correctly",
    "AFAIK": "as far as I know",
    "FWIW": "for what it's worth",
    "LGTM": "looks good to me",
    "WIP": "work in progress",
    "RFC": "R F C",
    "PEP": "pep",
    "PR": "pull request",
    "MR": "merge request",
    "RTFM": "read the manual",
    # Working groups and governance
    "WG": "working group",
    "SC": "steering council",
    "PSF": "P S F",
    "PC": "packaging council",
    "PyPA": "pie P A",
    "SIG": "sig",
}


def fix_pronunciations(text: str) -> str:
    """Apply pronunciation fixes to text before TTS."""
    result = text
    for word, phonetic in PRONUNCIATIONS.items():
        # Case-insensitive word boundary match
        pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
        result = pattern.sub(phonetic, result)
    return result


def split_into_chunks(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split text into chunks suitable for TTS."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    current = ""

    sentences = re.split(r"(?<=[.!?])\s+", text)

    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_chars:
            current = f"{current} {sentence}".strip() if current else sentence
        else:
            if current:
                chunks.append(current)
            if len(sentence) > max_chars:
                parts = re.split(r"(?<=[,;:])\s+", sentence)
                for part in parts:
                    if len(part) <= max_chars:
                        chunks.append(part)
                    else:
                        words = part.split()
                        chunk = ""
                        for word in words:
                            if len(chunk) + len(word) + 1 <= max_chars:
                                chunk = f"{chunk} {word}".strip() if chunk else word
                            else:
                                if chunk:
                                    chunks.append(chunk)
                                chunk = word
                        if chunk:
                            chunks.append(chunk)
            else:
                current = sentence

    if current:
        chunks.append(current)

    return chunks


class TTSBackend(ABC):
    """Abstract base class for TTS backends."""

    name: str = "base"
    sample_rate: int = 24000
    narrator_voice: str = "default"  # Default narrator voice for this backend

    @abstractmethod
    def get_voices(self) -> list[str]:
        """Return list of available voice IDs."""
        ...

    @abstractmethod
    def synthesize(self, text: str, voice: str) -> np.ndarray:
        """Synthesize text to audio.

        Args:
            text: Text to synthesize
            voice: Voice ID to use

        Returns:
            Audio as float32 numpy array
        """
        ...

    def generate_silence(self, duration_seconds: float) -> np.ndarray:
        """Generate silence of specified duration."""
        return np.zeros(int(self.sample_rate * duration_seconds), dtype=np.float32)


class TTSGenerator:
    """High-level TTS generator with caching and progress tracking."""

    def __init__(
        self,
        backend: TTSBackend,
        voice_assignment: VoiceAssignment,
        cache_dir: Path | None = None,
        include_attribution: bool = True,
        pause_between_posts: float = 1.5,
        narrator_voice: str | None = None,
    ):
        self.backend = backend
        self.voice_assignment = voice_assignment
        self.cache_dir = cache_dir
        self.include_attribution = include_attribution
        self.pause_between_posts = pause_between_posts
        self.narrator_voice = narrator_voice or backend.narrator_voice

        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cached_path(self, post_id: int) -> Path | None:
        if not self.cache_dir:
            return None
        return self.cache_dir / f"post_{post_id}_{self.backend.name}.npy"

    def generate_post(self, post: Post) -> tuple[np.ndarray, int]:
        """Generate audio for a post, using cache if available.

        Uses narrator voice for attribution ("Author says:") and
        the author's assigned voice for actual content.

        Returns:
            Tuple of (audio_array, attribution_samples) where attribution_samples
            is the number of samples used for the "Author says:" portion.
        """
        cache_path = self._get_cached_path(post.id)

        if cache_path and cache_path.exists():
            # For cached, we don't have attribution length - estimate it
            audio = np.load(cache_path)
            return audio, 0

        user_voice = self.voice_assignment.get_voice(post.username)
        audio_parts = []
        attribution_samples = 0

        # Attribution with narrator voice
        if self.include_attribution:
            attribution = f"{post.author} says:"
            attribution_audio = self.backend.synthesize(attribution, self.narrator_voice)
            silence = self.backend.generate_silence(0.4)
            attribution_samples = len(attribution_audio) + len(silence)
            audio_parts.append(attribution_audio)
            audio_parts.append(silence)

        # Content with user's assigned voice (with pronunciation fixes)
        chunks = split_into_chunks(fix_pronunciations(post.content))
        for chunk in chunks:
            audio = self.backend.synthesize(chunk, user_voice)
            audio_parts.append(audio)
            audio_parts.append(self.backend.generate_silence(0.3))

        result = np.concatenate(audio_parts)

        if cache_path:
            np.save(cache_path, result)

        return result, attribution_samples

    def generate_all(
        self,
        posts: list[Post],
        progress_callback: Callable[..., Any] | None = None,
        return_segments: bool = False,
    ) -> np.ndarray | tuple[np.ndarray, list[dict]]:
        """Generate audio for all posts.

        Args:
            posts: List of posts to convert
            progress_callback: Optional callback(current, total, post)
            return_segments: If True, return (audio, segments) where segments
                            contains start/end sample positions for each post

        Returns:
            Audio array, or tuple of (audio, segments) if return_segments=True
        """
        audio_parts = []
        segments = []
        pause = self.backend.generate_silence(self.pause_between_posts)
        current_sample = 0

        for i, post in enumerate(posts):
            if progress_callback:
                progress_callback(i + 1, len(posts), post)

            audio, attribution_samples = self.generate_post(post)
            start_sample = current_sample
            audio_parts.append(audio)
            current_sample += len(audio)

            # Track segment info including attribution length for sync
            segments.append(
                {
                    "post_number": post.number,
                    "author": post.author,
                    "username": post.username,
                    "start_sample": start_sample,
                    "end_sample": current_sample,
                    "content_preview": post.content[:100],
                    "content": post.content,
                    "attribution_samples": attribution_samples,
                }
            )

            audio_parts.append(pause)
            current_sample += len(pause)

        result = np.concatenate(audio_parts)
        if return_segments:
            return result, segments
        return result

    def generate_streaming(
        self,
        posts: list[Post],
        progress_callback: Callable[..., Any] | None = None,
    ):
        """Generate audio segments one at a time (yields as generated).

        Yields:
            Tuple of (audio_chunk, segment_info, post_index, total_posts)
        """
        pause = self.backend.generate_silence(self.pause_between_posts)
        current_sample = 0

        for i, post in enumerate(posts):
            if progress_callback:
                progress_callback(i + 1, len(posts), post)

            audio, attribution_samples = self.generate_post(post)
            start_sample = current_sample
            current_sample += len(audio)

            segment_info = {
                "post_number": post.number,
                "author": post.author,
                "username": post.username,
                "start_sample": start_sample,
                "end_sample": current_sample,
                "content_preview": post.content[:100],
                "content": post.content,
                "attribution_samples": attribution_samples,
            }

            # Yield the audio with pause appended
            audio_with_pause = np.concatenate([audio, pause])
            current_sample += len(pause)

            yield audio_with_pause, segment_info, i, len(posts)
