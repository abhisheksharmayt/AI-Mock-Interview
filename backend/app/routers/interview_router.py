import asyncio
import base64
import json
from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_ws
from app.db.database import get_db_session
from app.common.enums import InterviewStatus
from app.repositories.interview import InterviewRepository
from app.schemas.interview import InterviewSessionCreate, InterviewSessionStartResponse
from app.services.interveiw import InterviewService
from app.utils.cartesia_utils import CartesiaSessionManager
from app.utils.openai_utils import stream_interview_question
from app.utils.sarvam_utils import transcribe_audio
from app.core.configs import configs

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/start")
async def create_interview_session(
    request: InterviewSessionCreate,
    interview_service: InterviewService = Depends(InterviewService),
) -> InterviewSessionStartResponse:
    session = await interview_service.create_interview_session(request)
    return session


@router.websocket("/ws/{session_id}")
async def interview_websocket(
    websocket: WebSocket,
    session_id: UUID,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db_session),
):
    user = await get_current_user_ws(token, db)
    await websocket.accept()

    interview_repo = InterviewRepository(db)
    session = await interview_repo.get_interview_session(session_id)

    if not session or str(session.user_id) != str(user.id):
        await websocket.close(code=4004)
        return

    system_prompt: str = session.interview_context_json["prompt"]
    question_count: int = session.question_count
    turns: list[dict] = []
    audio_chunks: list[bytes] = []

    session_id_str = str(session_id)
    cartesia = CartesiaSessionManager()

    cartesia.get_or_create(session_id_str)

    sequence_no = 1  # 0 was the opening question from /start

    try:
        while True:
            raw = await websocket.receive_text()
            message = json.loads(raw)
            msg_type = message.get("type")

            if msg_type == "audio_chunk":
                chunk = base64.b64decode(message["data"])
                audio_chunks.append(chunk)

            elif msg_type == "end_utterance":
                if not audio_chunks:
                    continue

                answer_text = await transcribe_audio(b"".join(audio_chunks))
                audio_chunks.clear()

                if not answer_text:
                    await websocket.send_text(json.dumps({
                        "type": "no_speech_detected",
                        "message": "No speech detected, please try again.",
                    }))
                    continue

                await websocket.send_text(json.dumps({
                    "type": "transcript",
                    "text": answer_text,
                }))

                turns.append({"role": "user", "content": answer_text})
                sequence_no += 1

                completed_turns = len([t for t in turns if t["role"] == "user"])
                if completed_turns >= question_count:
                    await interview_repo.update_session_status(session_id, InterviewStatus.completed)
                    await websocket.send_text(json.dumps({"type": "session_completed"}))
                    break

                logger.info(f"Streaming next question, turn {sequence_no}")
                full_question = ""
                async for sentence in stream_interview_question(system_prompt, turns[-6:]):
                    logger.info(f"Sentence: {sentence[:60]}")
                    full_question += sentence + " "
                    audio_bytes = await asyncio.to_thread(
                        cartesia.text_to_speech, session_id_str, sentence
                    )
                    await websocket.send_text(json.dumps({
                        "type": "ai_audio_chunk",
                        "text": sentence,
                        "data": base64.b64encode(audio_bytes).decode(),
                    }))

                full_question = full_question.strip()
                turns.append({"role": "assistant", "content": full_question})
                sequence_no += 1

                await websocket.send_text(json.dumps({"type": "ai_audio_done"}))

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id_str}")
    except Exception:
        logger.exception(f"Error in interview WebSocket for session {session_id_str}")
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": "Internal server error"}))
        except Exception:
            pass
    finally:
        await interview_repo.update_session_status(session_id, InterviewStatus.completed)
        cartesia.close(session_id_str)
