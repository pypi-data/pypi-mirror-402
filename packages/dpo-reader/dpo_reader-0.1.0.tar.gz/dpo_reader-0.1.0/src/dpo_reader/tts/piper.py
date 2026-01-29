"""Piper TTS backend - fast, good quality, works on CPU."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .base import TTSBackend

# Piper voice models - these are downloaded on first use
# Using only medium/high quality voices for better audio
# Format: (model_name, sample_rate)
PIPER_VOICES = {
    "lessac": ("en_US-lessac-high", 22050),  # Best quality, neutral
    "libritts": ("en_US-libritts-high", 22050),  # High quality, clear
    "ljspeech": ("en_US-ljspeech-high", 22050),  # High quality, female
    "amy": ("en_US-amy-medium", 22050),  # Medium quality, female
    "joe": ("en_US-joe-medium", 22050),  # Medium quality, male
    "kusal": ("en_US-kusal-medium", 22050),  # Medium quality, male
    "arctic": ("en_US-arctic-medium", 22050),  # Medium quality, varied
    "ryan": ("en_US-ryan-high", 22050),  # High quality, male
    "kristin": ("en_US-kristin-medium", 22050),  # Medium quality, female
    "jenny": ("en_GB-jenny_dioco-medium", 22050),  # British, female
}

# Map our generic voice IDs to piper voices (best voices first)
VOICE_MAPPING = {
    "voice_0": "lessac",
    "voice_1": "libritts",
    "voice_2": "ljspeech",
    "voice_3": "amy",
    "voice_4": "joe",
    "voice_5": "kusal",
    "voice_6": "ryan",
    "voice_7": "kristin",
    "voice_8": "arctic",
    "voice_9": "jenny",
}


class PiperBackend(TTSBackend):
    """Piper TTS backend using piper-tts package."""

    name = "piper"
    sample_rate = 22050
    narrator_voice = "libritts"  # High quality narrator for attribution

    def __init__(self, model_dir: Path | None = None):
        """Initialize Piper backend.

        Args:
            model_dir: Directory to store/load models. Defaults to ~/.local/share/piper
        """
        self.model_dir = model_dir or Path.home() / ".local" / "share" / "piper"
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self._voices: dict = {}

    def get_voices(self) -> list[str]:
        return list(VOICE_MAPPING.keys())

    def _get_voice(self, voice_name: str):
        """Get or load a Piper voice.

        Args:
            voice_name: Voice name like "amy", "arctic", "lessac", etc.
        """
        if voice_name in self._voices:
            return self._voices[voice_name]

        try:
            from piper import PiperVoice  # type: ignore[import-not-found]
        except ImportError:
            raise ImportError("piper-tts not installed. Install with: pip install piper-tts")

        # voice_name is already the piper voice name (amy, arctic, etc.)
        # Look up the model name directly
        model_name, _ = PIPER_VOICES.get(voice_name, ("en_US-lessac-medium", 22050))

        # Download model if needed
        model_path = self.model_dir / f"{model_name}.onnx"
        if not model_path.exists():
            self._download_model(model_name)

        voice = PiperVoice.load(str(model_path))
        self._voices[voice_name] = voice
        return voice

    def _download_model(self, model_name: str):
        """Download a Piper model."""
        import urllib.request

        base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
        # Parse model name: en_US-lessac-medium -> en/en_US/lessac/medium/en_US-lessac-medium
        parts = model_name.split("-")
        lang_region = parts[0]  # e.g., "en_US"
        lang = lang_region.split("_")[0]  # e.g., "en"
        voice_name = parts[1]  # e.g., "lessac"
        quality = parts[2]  # e.g., "medium"

        for ext in [".onnx", ".onnx.json"]:
            url = f"{base_url}/{lang}/{lang_region}/{voice_name}/{quality}/{model_name}{ext}"
            dest = self.model_dir / f"{model_name}{ext}"

            if not dest.exists():
                print(f"Downloading {model_name}{ext}...")
                urllib.request.urlretrieve(url, dest)

    def synthesize(self, text: str, voice: str) -> np.ndarray:
        """Synthesize text using Piper."""
        piper_voice = self._get_voice(voice)

        # Piper returns AudioChunk objects with audio_float_array (already float32)
        audio_parts = [chunk.audio_float_array for chunk in piper_voice.synthesize(text)]

        if not audio_parts:
            return np.zeros(0, dtype=np.float32)

        return np.concatenate(audio_parts)
