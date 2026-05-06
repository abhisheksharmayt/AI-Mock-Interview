from dataclasses import dataclass
from io import BytesIO
import wave
from cartesia import Cartesia
from app.core.configs import configs
from loguru import logger
from threading import Lock


@dataclass
class CartesiaSessionState:
    connection: object
    ctx: object


class CartesiaSessionManager:
    def __init__(self):
        self.client = Cartesia(api_key=configs.CARTESIA_API_KEY)
        self._sessions: dict[str, CartesiaSessionState] = {}
        self._lock = Lock()

    def get_or_create(self, session_id: str) -> CartesiaSessionState:
        with self._lock:
            existing = self._sessions.get(session_id)
            if existing:
                return existing
            connection = self.client.tts.websocket_connect().enter()
            ctx = connection.context(
                model_id="sonic-3",
                voice={"mode": "id", "id": "3a8e6fea-81e5-4d4d-8755-86093146cdb8"},
                output_format={
                    "container": "raw",
                    "encoding": "pcm_s16le",
                    "sample_rate": 44100,
                },
            )
            state = CartesiaSessionState(connection=connection, ctx=ctx)
            self._sessions[session_id] = state
            return state

    def close(self, session_id: str):
        with self._lock:
            state = self._sessions.pop(session_id, None)
            if state:
                state.connection.close()
                return True
            return False

    def text_to_speech(self, session_id: str, text: str) -> bytes:
        try:
            with self._lock:
                state = self._sessions.get(session_id)
                if not state:
                    raise ValueError(f"Session {session_id} not found")
                state.ctx.push(text)
                state.ctx.no_more_inputs()
                audio_chunks = []
                for response in state.ctx.receive():
                    if response.type == "chunk" and response.audio:
                        audio_chunks.append(response.audio)
                    elif response.type == "done":
                        break
                return self._pcm_s16le_to_wav(b"".join(audio_chunks), sample_rate=44100)
        except Exception:
            logger.exception("Error while generating audio")
            raise

    @staticmethod
    def _pcm_s16le_to_wav(audio_bytes: bytes, sample_rate: int) -> bytes:
        buffer = BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_bytes)
        return buffer.getvalue()
