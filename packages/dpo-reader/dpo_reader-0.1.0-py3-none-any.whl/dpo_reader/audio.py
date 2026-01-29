"""Audio output utilities."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.io import wavfile

SAMPLE_RATE = 24000


def save_wav(audio: np.ndarray, path: Path, sample_rate: int = SAMPLE_RATE) -> None:
    """Save audio array to WAV file.

    Args:
        audio: Audio data as float32 numpy array
        path: Output file path
        sample_rate: Sample rate in Hz
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # Clip to valid range and convert to int16
    audio_clipped = np.clip(audio, -1.0, 1.0)
    audio_int16 = (audio_clipped * 32767).astype(np.int16)

    wavfile.write(str(path), sample_rate, audio_int16)


def load_wav(path: Path) -> tuple[int, np.ndarray]:
    """Load WAV file.

    Returns:
        Tuple of (sample_rate, audio_data)
    """
    sample_rate, audio = wavfile.read(str(path))

    # Convert to float32 if needed
    if audio.dtype == np.int16:
        audio = audio.astype(np.float32) / 32767.0

    return sample_rate, audio


def concatenate_with_crossfade(
    audio_parts: list[np.ndarray],
    crossfade_duration: float = 0.1,
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """Concatenate audio parts with crossfade transitions.

    Args:
        audio_parts: List of audio arrays
        crossfade_duration: Crossfade duration in seconds
        sample_rate: Sample rate in Hz

    Returns:
        Concatenated audio array
    """
    if not audio_parts:
        return np.array([], dtype=np.float32)

    if len(audio_parts) == 1:
        return audio_parts[0]

    crossfade_samples = int(crossfade_duration * sample_rate)
    result = audio_parts[0].copy()

    for part in audio_parts[1:]:
        if len(result) < crossfade_samples or len(part) < crossfade_samples:
            # Not enough samples for crossfade, just concatenate
            result = np.concatenate([result, part])
        else:
            # Apply crossfade
            fade_out = np.linspace(1.0, 0.0, crossfade_samples)
            fade_in = np.linspace(0.0, 1.0, crossfade_samples)

            # Apply fades
            result[-crossfade_samples:] *= fade_out
            part_copy = part.copy()
            part_copy[:crossfade_samples] *= fade_in

            # Overlap-add
            result[-crossfade_samples:] += part_copy[:crossfade_samples]
            result = np.concatenate([result, part_copy[crossfade_samples:]])

    return result


def get_duration(audio: np.ndarray, sample_rate: int = SAMPLE_RATE) -> float:
    """Get audio duration in seconds."""
    return len(audio) / sample_rate


def format_duration(seconds: float) -> str:
    """Format duration as HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
