"""
Redis client configuration for job queue
"""
import redis
from rq import Queue
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


# Redis connection
redis_conn = redis.from_url(settings.REDIS_URL, decode_responses=True)

# Job queue for background processing
job_queue = Queue("scope_processing", connection=redis_conn)


def get_redis():
    """Get Redis connection"""
    return redis_conn


def get_job_queue():
    """Get RQ job queue"""
    return job_queue


def publish_progress(session_id: str, progress: int, message: str):
    """
    Publish progress update to Redis pub/sub channel

    Args:
        session_id: Unique session/job identifier
        progress: Progress percentage (0-100)
        message: Status message
    """
    try:
        channel = f"progress:{session_id}"
        data = {
            "type": "progress",
            "pct": progress,
            "msg": message
        }
        redis_conn.publish(channel, str(data))
        logger.debug(f"Published progress: {session_id} - {progress}% - {message}")

    except Exception as e:
        logger.error(f"Error publishing progress: {e}")
