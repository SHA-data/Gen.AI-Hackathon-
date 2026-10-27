"""Speech-to-Text API endpoint (Could tier, Part B2)."""
from fastapi import APIRouter, Depends, File, UploadFile
from packages.contracts.stt import FakeSttProvider, SttResult
from services.api.app.core.auth import AuthContext, get_auth_context

router = APIRouter(prefix="/stt", tags=["stt"])
_stt_provider = FakeSttProvider()

@router.post("/transcribe", response_model=SttResult)
async def transcribe_audio(
    file: UploadFile = File(...),
    auth: AuthContext = Depends(get_auth_context),
):
    audio_bytes = await file.read()
    return await _stt_provider.transcribe(audio_bytes, file.filename or "audio.wav")
