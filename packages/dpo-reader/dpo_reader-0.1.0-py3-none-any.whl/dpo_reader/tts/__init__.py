"""TTS backends for DPO Reader."""

from .bark import BarkBackend
from .base import TTSBackend, TTSGenerator
from .openai import OpenAIBackend
from .piper import PiperBackend

__all__ = ["BarkBackend", "OpenAIBackend", "PiperBackend", "TTSBackend", "TTSGenerator"]
