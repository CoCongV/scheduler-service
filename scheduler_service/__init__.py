import os
import urllib.parse
import dramatiq
import redis
from dramatiq.brokers.redis import RedisBroker
from dramatiq.brokers.stub import StubBroker
from dramatiq.middleware import AsyncIO
from dramatiq_abort import Abortable, RedisBackend
from tortoise import Tortoise

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


def generate_broker(config):
    """
    根据配置生成并返回一个配置好的 Dramatiq Broker 实例。
    支持测试模式 (UNIT_TESTS=1) 使用 StubBroker。
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
        redis_url = getattr(config, "REDIS_URL", None) or (config.get("REDIS_URL") if isinstance(config, dict) else None)
        
        if not redis_url:
            # Fallback or error
            redis_url = "redis://localhost:6379/0"
        
        broker = RedisBroker(url=redis_url)
        
        # Add Middleware
        broker.add_middleware(AsyncIO())
        
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


# --- Setup Functions ---

def setup_dramatiq(config):
    """
    初始化Dramatiq消息队列和APScheduler。
    虽然全局 broker 已经在导入时设置了，但这里允许根据运行时 config 重新配置（如果需要）。
    主要用于初始化 APScheduler。
    """
    global scheduler, broker

    # --- 1. (Optional) Re-configure Dramatiq Broker ---
    # If we want to support changing REDIS_URL at runtime via `create_app(config=...)`,
    # we can regenerate the broker here.
    # However, for actors to pick up the new broker, they need to be aware of it.
    # Dramatiq actors bind to the broker at definition time by default.
    # So changing it here might not affect already-imported actors unless we use set_broker
    # AND the actors look up the global broker dynamically (they usually don't).
    # But let's update the global broker reference anyway.
    
    current_broker = generate_broker(config)
    dramatiq.set_broker(current_broker)
    broker = current_broker # Update module-level variable

    # --- 2. Configure APScheduler ---
    if os.getenv("UNIT_TESTS") == "1":
        # Test Mode: Memory JobStore
        jobstores = {'default': MemoryJobStore()}
        scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="Asia/Shanghai")
    else:
        # Production Mode: Redis JobStore
        redis_url = config.get("REDIS_URL")
        if redis_url:
            jobstores = {'default': _get_redis_job_store(redis_url)}
            scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="Asia/Shanghai")
        else:
            # Fallback
            scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


def close_dramatiq():
    """关闭Dramatiq连接"""
    current_broker = dramatiq.get_broker()
    if current_broker:
        current_broker.close()
    
    # Shut down APScheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()


async def setup_tortoise(config):
    """初始化Tortoise-ORM"""
    db_url = config.get('PG_URL') or config.get('POSTGRES_URL') or config.get('DB_URL')
    if not db_url:
        raise ValueError("数据库URL未配置，请设置PG_URL、POSTGRES_URL或DB_URL环境变量")

    await Tortoise.init(
        db_url=db_url,
        modules={'models': ['scheduler_service.models']}
    )


async def close_tortoise():
    """关闭Tortoise连接，不依赖Sanic应用"""
    await Tortoise.close_connections()
