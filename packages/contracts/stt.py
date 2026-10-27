"""Speech-to-Text Provider protocol and Fake implementation."""
from typing import List, Optional, Protocol
from pydantic import BaseModel, Field

class HighlightToken(BaseModel):
    token: str
    category: str  # 'currency' | 'number' | 'date'
    start_char: int
    end_char: int

class SttResult(BaseModel):
    raw_transcript: str
    edited_transcript: Optional[str] = None
    duration_seconds: float = 0.0
    highlights: List[HighlightToken] = Field(default_factory=list)

class SttProvider(Protocol):
    """Protocol for transcribing user voice input."""
    async def transcribe(self, audio_bytes: bytes, filename: str) -> SttResult:
        ...

class FakeSttProvider:
    """Fake STT provider for push-to-talk voice testing."""
    async def transcribe(self, audio_bytes: bytes, filename: str) -> SttResult:
        text = "Can we hire two developers if client Alpha pays thirty days late?"
        return SttResult(
            raw_transcript=text,
            edited_transcript=text,
            duration_seconds=4.2,
            highlights=[
                HighlightToken(token="two", category="number", start_char=12, end_char=15),
                HighlightToken(token="thirty days", category="date", start_char=44, end_char=55),
            ],
        )
