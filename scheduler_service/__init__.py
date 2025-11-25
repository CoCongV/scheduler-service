import dramatiq
from dramatiq.brokers.redis import RedisBroker
from tortoise import Tortoise

from scheduler_service.broker import broker


def setup_dramatiq(config):
    """初始化Dramatiq消息队列"""
    redis_url = config.get("REDIS_URL")

    if redis_url:
        new_broker = RedisBroker(url=redis_url)
        dramatiq.set_broker(new_broker)
    else:
        dramatiq.set_broker(broker)


def close_dramatiq():
    """关闭Dramatiq连接"""
    current_broker = dramatiq.get_broker()
    if current_broker:
        current_broker.close()


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
