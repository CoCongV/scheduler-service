import os
import urllib.parse
import asyncio
import dramatiq
import redis
from dramatiq.brokers.redis import RedisBroker
from dramatiq.brokers.stub import StubBroker
from dramatiq.brokers.stub import StubBroker
from dramatiq.middleware import AsyncIO, Middleware
from dramatiq.asyncio import get_event_loop_thread
from dramatiq_abort import Abortable
from dramatiq_abort.backends.redis import RedisBackend
from tortoise import Tortoise
from tortoise.exceptions import ConfigurationError


from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.jobstores.memory import MemoryJobStore
from scheduler_service.utils.logger import logger
from scheduler_service.config import Config


# --- Helper Functions ---
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
        return RedisJobStore(host='localhost', port=6379)


class TortoiseMiddleware(Middleware):
    """
    Dramatiq Middleware to initialize Tortoise ORM in worker threads.
    """

    def after_worker_boot(self, broker, worker):
        try:
            event_loop_thread = get_event_loop_thread()
            if not event_loop_thread:
                logger.error("AsyncIO event loop thread not found.")
                return

            loop = event_loop_thread.loop
            if not loop:
                logger.error("AsyncIO event loop not initialized.")
                return

            # Initialize Tortoise on the AsyncIO loop
            future = asyncio.run_coroutine_threadsafe(
                setup_tortoise(Config.to_dict()), loop)
            future.result(timeout=10)
            logger.info("Tortoise ORM initialized on AsyncIO loop.")

        except Exception as e:
            logger.error("Failed to initialize Tortoise ORM: %s", e)

    def before_worker_shutdown(self, broker, worker):
        try:
            event_loop_thread = get_event_loop_thread()
            if event_loop_thread and event_loop_thread.loop:
                loop = event_loop_thread.loop
                if loop.is_running():
                    future = asyncio.run_coroutine_threadsafe(
                        close_tortoise(), loop)
                    future.result(timeout=5)
            logger.info("Tortoise ORM connections closed.")
        except Exception as e:
            logger.warning("Error closing Tortoise ORM connections: %s", e)


def generate_broker(config):
    """
    Generate and return a configured Dramatiq Broker instance based on config.
    Supports test mode (UNIT_TESTS=1) using StubBroker.
    """
    if os.getenv("UNIT_TESTS") == "1":
        # [Test Mode]
        # Use StubBroker for in-memory testing
        broker = StubBroker()
        broker.emit_after("process_boot")
        # Add AsyncIO middleware (needed for async actors)
        broker.add_middleware(AsyncIO())
        # Test mode typically doesn't need Abortable unless mocking backend
        return broker
    else:
        # [Production Mode]
        # Config.REDIS_URL is populated from env vars or config file
        # Note: `config` here can be the Config class or a dict/object with .REDIS_URL or .get("REDIS_URL")
        # We handle both for robustness
        redis_url = getattr(config, "REDIS_URL", None) or (
            config.get("REDIS_URL") if isinstance(config, dict) else None)

        if not redis_url:
            # Fallback or error
            redis_url = "redis://localhost:6379/0"

        broker = RedisBroker(url=redis_url)

        # Add Middleware
        broker.add_middleware(AsyncIO())
        broker.add_middleware(TortoiseMiddleware())

        # Abortable Middleware
        try:
            redis_client = redis.Redis.from_url(redis_url)
            abort_backend = RedisBackend(client=redis_client)
            broker.add_middleware(Abortable(backend=abort_backend))
        except Exception as e:
            logger.warning("Failed to configure Abortable middleware: %s", e)

        return broker


# --- Global Initialization ---
# Initialize the global broker using the default Config immediately on import.
# This ensures that any actors defined in other modules will register against this broker.
broker = generate_broker(Config)
dramatiq.set_broker(broker)

# Global scheduler instance (placeholder, fully configured in setup_dramatiq or via default logic)
scheduler: AsyncIOScheduler = None


def get_scheduler() -> AsyncIOScheduler:
    """Get APScheduler instance, raise error if not initialized"""
    if scheduler is None:
        raise RuntimeError(
            "APScheduler has not been initialized. Call setup_dramatiq first.")
    return scheduler


# --- Setup Functions ---
def setup_dramatiq(config):
    """
    Initialize Dramatiq message queue and APScheduler (do not start).
    Start and shutdown are managed by application lifecycle or test fixtures.
    """
    global scheduler, broker

    if os.getenv("UNIT_TESTS") == "1":
        # --- [Test Mode] ---
        jobstores = {'default': MemoryJobStore()}
        scheduler = AsyncIOScheduler(
            jobstores=jobstores, timezone="Asia/Shanghai")

    else:
        # --- [Production Mode] ---
        current_broker = generate_broker(config)
        dramatiq.set_broker(current_broker)
        broker = current_broker  # Update module-level variable

        redis_url = config.get("REDIS_URL")
        if redis_url:
            jobstores = {'default': _get_redis_job_store(redis_url)}
            scheduler = AsyncIOScheduler(
                jobstores=jobstores, timezone="Asia/Shanghai")
        else:
            scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


def close_dramatiq():
    """Close Dramatiq connection"""
    current_broker = dramatiq.get_broker()
    if current_broker:
        current_broker.close()

    # Shut down APScheduler (only if it was started and is running)
    # Shut down APScheduler (only if it was started and is running)
    if scheduler and scheduler.running:
        scheduler.shutdown()


async def setup_tortoise(config):
    """Initialize Tortoise-ORM"""
    db_url = config.get('PG_URL') or config.get(
        'POSTGRES_URL') or config.get('DB_URL')
    if not db_url:
        raise ValueError(
            "Database URL not configured, please set PG_URL, POSTGRES_URL or DB_URL environment variable")

    await Tortoise.init(
        db_url=db_url,
        modules={'models': ['scheduler_service.models']}
    )


async def close_tortoise():
    """Close Tortoise connection, independent of Sanic app"""
    try:
        await Tortoise.close_connections()
    except ConfigurationError:
        # Ignore error if not initialized
        pass
