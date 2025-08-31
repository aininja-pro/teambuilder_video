from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from rq import Queue
from redis import Redis
from redis.asyncio import Redis as AsyncRedis
import asyncio
import json
import os

# ChatGPT's exact setup - sync Redis for RQ, async for WebSocket
redis = Redis(host="localhost", port=6379, decode_responses=True)
redis_async = AsyncRedis.from_url("redis://localhost:6379/0", decode_responses=True)
q = Queue("uploads", connection=redis)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

# Minimal chunked upload storage
upload_sessions = {}

from fastapi import UploadFile, File, Form

@router.post("/api/upload/chunk")
async def upload_chunk(
    chunk: UploadFile = File(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    filename: str = Form(...),
    session_id: str = Form(None)
):
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())
    
    if session_id not in upload_sessions:
        import tempfile
        upload_sessions[session_id] = {
            "filename": filename,
            "total_chunks": total_chunks,
            "received_chunks": 0,
            "chunks": [],
            "temp_dir": tempfile.mkdtemp()
        }
    
    # Save chunk
    import os
    chunk_path = os.path.join(upload_sessions[session_id]["temp_dir"], f"chunk_{chunk_index}")
    content = await chunk.read()
    with open(chunk_path, "wb") as f:
        f.write(content)
    
    upload_sessions[session_id]["received_chunks"] += 1
    
    progress = int((upload_sessions[session_id]["received_chunks"] / total_chunks) * 100)
    
    return {
        "session_id": session_id,
        "chunk_index": chunk_index,
        "received_chunks": upload_sessions[session_id]["received_chunks"],
        "total_chunks": total_chunks,
        "progress": progress,
        "complete": upload_sessions[session_id]["received_chunks"] == total_chunks
    }

# ChatGPT's EXACT API pattern
@router.post("/api/upload/complete/{session_id}")
def complete(session_id: str):
    import logging
    logging.warning(f"DEBUG MAIN: Complete called for session {session_id}")
    logging.warning(f"DEBUG MAIN: Available sessions: {list(upload_sessions.keys())}")
    
    # Assemble chunks first
    if session_id not in upload_sessions:
        logging.error(f"DEBUG MAIN: Session {session_id} NOT FOUND!")
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = upload_sessions[session_id]
    import os
    final_path = os.path.join(session["temp_dir"], session["filename"])
    
    with open(final_path, "wb") as final_file:
        for i in range(session["total_chunks"]):
            chunk_path = os.path.join(session["temp_dir"], f"chunk_{i}")
            with open(chunk_path, "rb") as chunk_file:
                final_file.write(chunk_file.read())
    
    # Store file path for worker
    logging.warning(f"DEBUG MAIN: Storing file path in Redis: {final_path}")
    redis.hset(f"jobs:{session_id}", mapping={"file_path": final_path})
    logging.warning(f"DEBUG MAIN: Stored successfully for session {session_id}")
    
    job = q.enqueue("workers.process_session", session_id)
    return {"job_id": job.get_id()}

# ChatGPT's EXACT robust WebSocket pattern
@router.websocket("/ws/{session_id}")
async def ws_progress(ws: WebSocket, session_id: str):
    await ws.accept()

    # 1) send latest known state immediately
    state = await redis_async.hgetall(f"jobs:{session_id}")
    if state:
        await ws.send_json({"type": "snapshot", **state})

    # 2) subscribe to pub/sub channel
    channel = f"progress:{session_id}"
    pubsub = redis_async.pubsub(ignore_subscribe_messages=True)
    await pubsub.subscribe(channel)

    # 3) robust receive loop with heartbeat
    async def heartbeat():
        while True:
            await asyncio.sleep(20)
            try:
                await ws.send_json({"type": "ping"})
            except Exception:
                break

    try:
        hb_task = asyncio.create_task(heartbeat())
        while True:
            msg = await pubsub.get_message(timeout=1.0)
            if msg:
                await ws.send_text(msg["data"])  # already JSON string
            await asyncio.sleep(0.01)
    except asyncio.CancelledError:
        pass
    except WebSocketDisconnect:
        pass
    finally:
        try:
            hb_task.cancel()
        except Exception:
            pass
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()

# Fallback endpoint as ChatGPT suggested
@router.get("/api/jobs/{session_id}")
def get_job_status(session_id: str):
    job_data = redis.hgetall(f"jobs:{session_id}")
    if not job_data:
        return {"status": "not_found"}
    return job_data

# ChatGPT's debug endpoint for testing
@router.post("/api/debug/publish/{session_id}/{pct}")
async def dbg(session_id: str, pct: int):
    from workers import publish
    publish(session_id, pct, f"dbg {pct}", status="debug")
    return {"ok": True}

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)