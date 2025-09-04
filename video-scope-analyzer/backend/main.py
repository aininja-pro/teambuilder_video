from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from rq import Queue
from redis import Redis
from redis.asyncio import Redis as AsyncRedis
import asyncio
import json
import os
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

# Redis setup with fallback for deployment
import os
redis = None
redis_async = None
q = None

try:
    if os.getenv('USE_REDIS', 'true').lower() != 'false':
        redis = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)
        redis_async = AsyncRedis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)
        q = Queue("uploads", connection=redis)
        print("✅ Redis connected successfully")
    else:
        print("⚠️ Running without Redis persistence")
except Exception as e:
    print(f"⚠️ Redis not available, running in simple mode: {e}")
    redis = None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(FileNotFoundError)
async def not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"detail": "Frontend build not found"})

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
    
    if redis and q:
        # Store file path for worker
        logging.warning(f"DEBUG MAIN: Storing file path in Redis: {final_path}")
        redis.hset(f"jobs:{session_id}", mapping={"file_path": final_path})
        logging.warning(f"DEBUG MAIN: Stored successfully for session {session_id}")
        
        job = q.enqueue("workers.process_session", session_id)
        return {"job_id": job.get_id()}
    else:
        # Simple mode - return mock result for now
        return {"job_id": "simple-mode", "message": "Redis not available - using simple mode"}

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

# Persistence Models
class SavedAnalysis(BaseModel):
    id: str
    filename: str
    created_at: str
    transcript: str
    scope_items: List[dict]
    project_summary: dict
    file_size_mb: Optional[float] = None
    documents: Optional[dict] = None

class AnalysisListItem(BaseModel):
    id: str
    filename: str
    created_at: str
    file_size_mb: Optional[float] = None
    scope_count: int

# Persistence API Endpoints
@router.get("/api/analyses", response_model=List[AnalysisListItem])
def get_analyses():
    """Get list of all saved analyses"""
    try:
        analysis_keys = redis.keys("analysis:*")
        analyses = []
        
        for key in analysis_keys:
            analysis_id = key.replace("analysis:", "")
            data = redis.hgetall(key)
            if data:
                scope_items = json.loads(data.get('scope_items', '[]'))
                analyses.append(AnalysisListItem(
                    id=analysis_id,
                    filename=data.get('filename', 'Unknown'),
                    created_at=data.get('created_at', ''),
                    file_size_mb=float(data.get('file_size_mb', 0)) if data.get('file_size_mb') else None,
                    scope_count=len(scope_items)
                ))
        
        # Sort by creation date (newest first)
        analyses.sort(key=lambda x: x.created_at, reverse=True)
        return analyses
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/analyses/{analysis_id}", response_model=SavedAnalysis)
def get_analysis(analysis_id: str):
    """Get a specific analysis by ID"""
    data = redis.hgetall(f"analysis:{analysis_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return SavedAnalysis(
        id=analysis_id,
        filename=data.get('filename', 'Unknown'),
        created_at=data.get('created_at', ''),
        transcript=data.get('transcript', ''),
        scope_items=json.loads(data.get('scope_items', '[]')),
        project_summary=json.loads(data.get('project_summary', '{}')),
        file_size_mb=float(data.get('file_size_mb', 0)) if data.get('file_size_mb') else None,
        documents=json.loads(data.get('documents', '{}')) if data.get('documents') else None
    )

@router.delete("/api/analyses/{analysis_id}")
def delete_analysis(analysis_id: str):
    """Delete a specific analysis"""
    if not redis.exists(f"analysis:{analysis_id}"):
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    redis.delete(f"analysis:{analysis_id}")
    return {"message": "Analysis deleted successfully"}

from fastapi.responses import FileResponse

# Mount the React build output - this serves CSS, JS, and other assets
if os.path.exists("static/_next"):
    app.mount("/_next", StaticFiles(directory="static/_next"), name="nextjs_assets")

if os.path.exists("static/static"):
    app.mount("/static", StaticFiles(directory="static/static"), name="static_assets")

if os.path.exists("static"):
    app.mount("/documents", StaticFiles(directory="static"), name="documents")

# Mount API routes
app.include_router(router)

# Serve frontend index.html at root
@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")

# Catch-all for React router
@app.get("/{full_path:path}")
def serve_react_app(full_path: str):
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    print(f"🌐 Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)