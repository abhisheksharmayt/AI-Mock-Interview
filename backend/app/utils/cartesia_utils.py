from io import BytesIO
import wave
from cartesia import Cartesia
from app.core.configs import configs
from loguru import logger
from threading import Lock


class CartesiaSessionManager:
    def __init__(self):
        self.client = Cartesia(api_key=configs.CARTESIA_API_KEY)
        self._connections: dict[str, object] = {}
        self._lock = Lock()

    def get_or_create(self, session_id: str) -> object:
        with self._lock:
            if session_id not in self._connections:
                self._connections[session_id] = self.client.tts.websocket_connect().enter()
            return self._connections[session_id]

    def close(self, session_id: str):
        with self._lock:
            connection = self._connections.pop(session_id, None)
            if connection:
                connection.close()
                return True
            return False

    def text_to_speech(self, session_id: str, text: str) -> bytes:
        try:
            with self._lock:
                connection = self._connections.get(session_id)
                if not connection:
                    raise ValueError(f"Session {session_id} not found")
                ctx = connection.context(
                    model_id="sonic-3",
                    voice={"mode": "id", "id": "3a8e6fea-81e5-4d4d-8755-86093146cdb8"},
                    output_format={
                        "container": "raw",
                        "encoding": "pcm_s16le",
                        "sample_rate": 44100,
                    },
                )
                ctx.push(text)
                ctx.no_more_inputs()
                audio_chunks = []
                for response in ctx.receive():
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
