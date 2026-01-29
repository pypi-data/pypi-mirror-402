"""Bark TTS backend - highest quality, GPU recommended for speed."""

from __future__ import annotations

import os

import numpy as np

from .base import TTSBackend

# Enable MPS (Apple Silicon GPU) support if available
os.environ.setdefault("SUNO_ENABLE_MPS", "True")
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

BARK_VOICES = [f"v2/en_speaker_{i}" for i in range(10)]


def _patch_torch_load():
    """Patch torch.load for PyTorch 2.6+ compatibility with Bark models.

    PyTorch 2.6+ defaults weights_only=True which blocks numpy types used by Bark.
    We patch torch.load to default weights_only=False for Bark model loading.
    """
    try:
        import functools

        import torch

        _original_load = torch.load

        @functools.wraps(_original_load)
        def _patched_load(*args, **kwargs):
            if "weights_only" not in kwargs:
                kwargs["weights_only"] = False
            return _original_load(*args, **kwargs)

        torch.load = _patched_load  # type: ignore[assignment]
    except ImportError:
        pass


class BarkBackend(TTSBackend):
    """Bark TTS backend."""

    name = "bark"
    sample_rate = 24000
    narrator_voice = "v2/en_speaker_0"  # Neutral narrator voice for attribution
    _models_loaded = False

    def __init__(self):
        self._ensure_models()

    def _ensure_models(self):
        if not BarkBackend._models_loaded:
            # Fix PyTorch 2.6+ weights_only compatibility
            _patch_torch_load()

            from bark import preload_models

            preload_models()
            BarkBackend._models_loaded = True

    def get_voices(self) -> list[str]:
        return BARK_VOICES

    def synthesize(self, text: str, voice: str) -> np.ndarray:
        from bark import generate_audio

        return generate_audio(text, history_prompt=voice)
