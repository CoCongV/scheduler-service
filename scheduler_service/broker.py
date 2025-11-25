import os
import urllib.parse
import dramatiq
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore
from dramatiq.brokers.redis import RedisBroker
from dramatiq.brokers.stub import StubBroker
from dramatiq.middleware import AsyncIO

from scheduler_service.config import Config

# --- Dramatiq Configuration ---
if os.getenv("UNIT_TESTS") == "1":
    broker = StubBroker()
    broker.emit_after("process_boot")
else:
    broker = RedisBroker(url=Config.REDIS_URL)

broker.add_middleware(AsyncIO())
dramatiq.set_broker(broker)


# --- APScheduler Configuration ---
def _get_redis_job_store(redis_url: str) -> RedisJobStore:
    """
    Parses a Redis URL and returns a configured RedisJobStore.
    Handles redis://[:password@]host[:port][/db] format.
    """
    try:
        url_parts = urllib.parse.urlparse(redis_url)

        return RedisJobStore(
            jobs_key='apscheduler.jobs',
            run_times_key='apscheduler.run_times',
            host=url_parts.hostname or 'localhost',
            port=url_parts.port or 6379,
            db=int(url_parts.path.lstrip('/')) if url_parts.path else 0,
            password=url_parts.password
        )
    except Exception:
        # Fallback or re-raise depending on strictness requirements.
        # For now, we assume a valid URL or fallback to defaults if parsing fails drastically.
        # But using 'from_url' style init is safer if the lib supported it directly.
        # Since RedisJobStore doesn't take a URL, we parse manually.
        return RedisJobStore(host='localhost', port=6379)


jobstores = {
    'default': _get_redis_job_store(Config.REDIS_URL)
}

scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="Asia/Shanghai")
