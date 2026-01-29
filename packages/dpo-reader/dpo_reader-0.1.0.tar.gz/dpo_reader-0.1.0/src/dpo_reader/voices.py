"""Voice assignment for TTS backends."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TTSEngine(Enum):
    """Available TTS engines."""

    BARK = "bark"
    PIPER = "piper"


# Generic voice IDs (mapped to specific backend voices)
VOICES = [f"voice_{i}" for i in range(10)]

# Voice descriptions (neutral, tonal qualities)
VOICE_DESCRIPTIONS = {
    "voice_0": "Voice A (deeper tone)",
    "voice_1": "Voice B (mid-range)",
    "voice_2": "Voice C (higher pitch)",
    "voice_3": "Voice D (energetic)",
    "voice_4": "Voice E (calm)",
    "voice_5": "Voice F (gravelly)",
    "voice_6": "Voice G (brighter)",
    "voice_7": "Voice H (neutral)",
    "voice_8": "Voice I (clear)",
    "voice_9": "Voice J (relaxed)",
}

# Backend-specific voice mappings
BARK_VOICES = {f"voice_{i}": f"v2/en_speaker_{i}" for i in range(10)}
PIPER_VOICES = {
    "voice_0": "amy",
    "voice_1": "arctic",
    "voice_2": "danny",
    "voice_3": "joe",
    "voice_4": "kathleen",
    "voice_5": "kusal",
    "voice_6": "l2arctic",
    "voice_7": "lessac",
    "voice_8": "libritts",
    "voice_9": "ljspeech",
}


def get_backend_voice(voice_id: str, engine: TTSEngine) -> str:
    """Map generic voice ID to backend-specific voice."""
    if engine == TTSEngine.BARK:
        return BARK_VOICES.get(voice_id, "v2/en_speaker_0")
    if engine == TTSEngine.PIPER:
        return PIPER_VOICES.get(voice_id, "lessac")
    return voice_id


@dataclass
class VoiceAssignment:
    """Maps authors to voice IDs."""

    assignments: dict[str, str] = field(default_factory=dict)
    engine: TTSEngine = TTSEngine.BARK
    _next_idx: int = 0

    def assign(self, username: str) -> str:
        """Get or assign a voice for an author."""
        if username not in self.assignments:
            voice = VOICES[self._next_idx % len(VOICES)]
            self.assignments[username] = voice
            self._next_idx += 1
        return self.assignments[username]

    def get_voice(self, username: str) -> str:
        """Get the assigned backend-specific voice for an author."""
        generic_voice = self.assignments.get(username, VOICES[0])
        return get_backend_voice(generic_voice, self.engine)

    def get_generic_voice(self, username: str) -> str:
        """Get the generic voice ID for an author."""
        return self.assignments.get(username, VOICES[0])

    @classmethod
    def from_author_counts(
        cls,
        author_counts: dict[str, int],
        engine: TTSEngine = TTSEngine.BARK,
        prioritize_active: bool = True,
    ) -> VoiceAssignment:
        """Create voice assignments from author post counts."""
        va = cls(engine=engine)

        if prioritize_active:
            sorted_authors = sorted(author_counts.keys(), key=lambda x: -author_counts[x])
        else:
            sorted_authors = sorted(author_counts.keys())

        for username in sorted_authors:
            va.assign(username)

        return va

    def summary(self) -> list[tuple[str, str, str]]:
        """Get a summary of voice assignments."""
        return [
            (username, voice, VOICE_DESCRIPTIONS.get(voice, "Unknown")) for username, voice in self.assignments.items()
        ]
