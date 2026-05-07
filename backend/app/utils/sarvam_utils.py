from sarvamai import AsyncSarvamAI
from app.core.configs import configs
from loguru import logger


async def transcribe_audio(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    try:
        client = AsyncSarvamAI(api_subscription_key=configs.SARVAM_API_KEY)
        response = await client.speech_to_text.transcribe(
            file=("audio.wav", audio_bytes, "audio/wav"),
            model="saaras:v3",
            mode="transcribe",
            language_code="en-IN",
        )
        transcript = getattr(response, "transcript", "") or ""
        logger.info(f"Transcription result: {transcript[:100]}")
        return transcript
    except Exception:
        logger.exception("Error while transcribing audio")
        raise
