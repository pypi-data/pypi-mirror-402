"""OpenAI TTS backend - high quality cloud voices."""

from __future__ import annotations

import os

import numpy as np

from .base import TTSBackend

# Available OpenAI TTS voices
OPENAI_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]


class OpenAIBackend(TTSBackend):
    """OpenAI TTS backend using their API.

    Requires OPENAI_API_KEY environment variable.
    """

    name = "openai"
    sample_rate = 24000
    narrator_voice = "onyx"  # Deep, neutral voice for narration

    def __init__(self, model: str = "tts-1"):
        """Initialize OpenAI TTS backend.

        Args:
            model: Model to use - "tts-1" (faster) or "tts-1-hd" (higher quality)
        """
        self.model = model
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable required for OpenAI TTS. "
                "Get one at https://platform.openai.com/api-keys"
            )

        # Lazy import
        try:
            import httpx

            self._client = httpx.Client(
                base_url="https://api.openai.com/v1",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=60.0,
            )
        except ImportError as e:
            raise ImportError("httpx required for OpenAI backend") from e

    def get_voices(self) -> list[str]:
        """Return list of available voice IDs."""
        return OPENAI_VOICES

    def synthesize(self, text: str, voice: str) -> np.ndarray:
        """Synthesize text to audio using OpenAI TTS API.

        Args:
            text: Text to synthesize
            voice: Voice ID to use (alloy, echo, fable, onyx, nova, shimmer)

        Returns:
            Audio as float32 numpy array
        """
        import time

        import httpx

        if voice not in OPENAI_VOICES:
            voice = OPENAI_VOICES[hash(voice) % len(OPENAI_VOICES)]

        # Retry with exponential backoff for rate limits
        max_retries = 8
        base_delay = 2.0

        for attempt in range(max_retries):
            try:
                response = self._client.post(
                    "/audio/speech",
                    json={
                        "model": self.model,
                        "input": text,
                        "voice": voice,
                        "response_format": "pcm",  # Raw 24kHz 16-bit mono PCM
                    },
                )
                response.raise_for_status()

                # Convert PCM bytes to float32 numpy array
                audio_bytes = response.content
                audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
                audio_float32 = audio_int16.astype(np.float32) / 32768.0

                return audio_float32

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    # Rate limited - wait and retry with exponential backoff
                    delay = base_delay * (2**attempt)
                    print(f"Rate limited, waiting {delay:.0f}s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(delay)
                    continue
                raise
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    delay = base_delay * (2**attempt)
                    print(f"Rate limited, waiting {delay:.0f}s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(delay)
                    continue
                raise

        raise RuntimeError(f"Failed to synthesize after {max_retries} retries")

    def __del__(self):
        """Cleanup HTTP client."""
        if hasattr(self, "_client"):
            self._client.close()
