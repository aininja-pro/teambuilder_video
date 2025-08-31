# ChatGPT's EXACT worker pattern
from redis import Redis
import time, json
import logging
import traceback
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

redis = Redis(host="localhost", port=6379, decode_responses=True)
log = logging.getLogger("processing")

# ChatGPT's EXACT publish pattern with payload
def publish(session_id, pct, msg, **extra):
    payload = {"type": "progress", "pct": pct, "msg": msg, **extra}
    redis.hset(f"jobs:{session_id}", mapping={"pct": pct, "msg": msg, "status": extra.get("status", "processing")})
    redis.publish(f"progress:{session_id}", json.dumps(payload))
    redis.expire(f"jobs:{session_id}", 60 * 60)  # 1 hour TTL

# ChatGPT's logging wrapper
def run_with_logging(fn, *args, **kwargs):
    try:
        logging.info("TASK START %s", args or "")
        return fn(*args, **kwargs)
    except Exception:
        logging.exception("TASK FAILED")
        raise
    finally:
        logging.info("TASK END")

# ChatGPT's EXACT worker pattern with your progress semantics
def process_session(session_id: str):
    publish(session_id, 0, "Queued")
    
    # Progress semantics: Upload (0-20%) → MOV Convert (20-40%) → Transcribe (40-70%) → Parse (70-90%) → Docs (90-100%)
    
    # validate files exist, assemble chunks, etc.
    publish(session_id, 10, "Assembling chunks")
    time.sleep(1)
    
    # MOV Convert (20-40%)
    publish(session_id, 25, "Converting MOV to MP4...")
    time.sleep(2)
    publish(session_id, 40, "MOV conversion complete")
    
    # Transcribe (40-70%)
    publish(session_id, 45, "Starting audio transcription...")
    
    # Initialize OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Mock transcription for now - replace with real call
    time.sleep(3)
    transcript = "Sample transcript from video processing..."
    
    publish(session_id, 70, f"Transcription complete ({len(transcript)} characters)")
    
    # Parse (70-90%)
    publish(session_id, 75, "Analyzing transcript for scope items...")
    time.sleep(2)
    publish(session_id, 90, "Extracted 5 scope items")
    
    # Docs (90-100%)
    publish(session_id, 95, "Generating documents...")
    time.sleep(1)
    publish(session_id, 100, "Done", status="completed")
    
    # Store final result
    result = {
        "transcript": transcript,
        "scope_items": [],
        "project_summary": {},
        "documents": {"docx": "/static/test.docx", "pdf": "/static/test.pdf"}
    }
    redis.hset(f"jobs:{session_id}", mapping={
        "status": "completed",
        "result": json.dumps(result)
    })