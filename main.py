from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
import base64
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from asr import transcribe_audio
from brain import get_reply
from tts import generate_full_tts
from lipsync import generate_visemes, estimate_word_timing

app = FastAPI()

# Add CORS middleware - must be before any routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Serve frontend static files

@app.post("/chat")
async def chat_handler(request: dict):
    """Simple chat endpoint - accepts { message: "text" } returns { text: "reply", audio: "base64", lip_sync: {...} }"""
    try:
        text = request.get("message", "")
        
        if not text:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing message"},
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
        # Get AI response
        reply = get_reply(text)
        
        # Generate TTS
        audio_bytes = await generate_full_tts(reply) if generate_full_tts else b""
        
        # Lip sync
        audio_duration_ms = len(audio_bytes) * 1000 // 24000 if audio_bytes else 1000
        viseme_sequence = []
        word_timing = []
        if generate_visemes and estimate_word_timing and audio_bytes:
            viseme_sequence = generate_visemes(audio_bytes)
            word_timing = estimate_word_timing(reply, audio_duration_ms)
        
        # Convert audio to base64
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8') if audio_bytes else ""
        
        return JSONResponse(
            content={
                "text": reply,
                "audio": audio_base64,
                "lip_sync": {
                    "visemes": viseme_sequence,
                    "words": word_timing,
                    "duration": audio_duration_ms
                }
            },
            headers={"Access-Control-Allow-Origin": "*"}
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
            headers={"Access-Control-Allow-Origin": "*"}
        )

@app.post("/api")
async def api_handler(request: dict):
    """REST API handler for text and audio processing"""
    cors_headers = {"Access-Control-Allow-Origin": "*"}
    
    try:
        text = request.get("text", "")
        audio_data = request.get("audio", "")
        
        # If audio is provided, transcribe it first
        if audio_data:
            try:
                audio_bytes = base64.b64decode(audio_data)
                text = transcribe_audio(audio_bytes)
                logger.info(f"Transcribed audio to text: {text}")
            except Exception as e:
                logger.error(f"ASR transcription error: {e}")
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Audio transcription failed: {str(e)}"},
                    headers=cors_headers
                )
        
        if not text:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing text or audio"},
                headers=cors_headers
            )
        
        # Get AI response
        reply = get_reply(text)
        
        # Generate TTS
        audio_bytes = await generate_full_tts(reply) if generate_full_tts else b""
        
        # Lip sync
        audio_duration_ms = len(audio_bytes) * 1000 // 24000 if audio_bytes else 1000
        viseme_sequence = []
        word_timing = []
        if generate_visemes and estimate_word_timing and audio_bytes:
            viseme_sequence = generate_visemes(audio_bytes)
            word_timing = estimate_word_timing(reply, audio_duration_ms)
        
        # Convert audio to base64
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8') if audio_bytes else ""
        
        return JSONResponse(
            content={
                "text": reply,
                "audio": audio_base64,
                "lip_sync": {
                    "visemes": viseme_sequence,
                    "words": word_timing,
                    "duration": audio_duration_ms
                }
            },
            headers=cors_headers
        )
        
    except Exception as e:
        logger.error(f"API error: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
            headers=cors_headers
        )

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()

    while True:
        data = await ws.receive_bytes()

        # 1. Speech → Text (Vietnamese)
        text = transcribe_audio(data)

        # 2. AI Response
        reply = get_reply(text)

        # 3. Send text first (for subtitles)
        await ws.send_json({"type": "text", "data": reply})

        # 4. Generate full TTS audio first
        full_audio = await generate_full_tts(reply)
        
        if full_audio:
            # Send audio as single message
            await ws.send_bytes(full_audio)
            
            # Generate viseme sequence
            viseme_sequence = generate_visemes(full_audio)
            
            # Estimate word timing
            audio_duration_ms = len(full_audio) * 1000 // 24000  # Approximate
            word_timing = estimate_word_timing(reply, audio_duration_ms)
            
            # Send combined lip sync data
            await ws.send_json({
                "type": "lip_sync_data",
                "data": {
                    "visemes": viseme_sequence,
                    "words": word_timing,
                    "duration": audio_duration_ms
                }
            })
